"""
AstraLang Interpreter (v0.1, diperluas di v0.3)
==================================================
Tree-walking interpreter: berjalan langsung di atas AST hasil Parser.
Pendekatan tree-walking dipilih karena sederhana dan mudah dikembangkan
bertahap (compile ke bytecode/native direncanakan di roadmap lanjutan).

Fitur yang didukung:
- print
- variable (let, assignment)
- string, integer, float, boolean, null
- List (literal [1,2,3], indexing, index assignment) -- v0.3
- operasi matematika (+ - * / %) dan perbandingan
- kondisi (if / else)
- loop (while)
- function (deklarasi, pemanggilan, return, closure sederhana)
"""

from parser import (
    Program, LetStatement, PrintStatement, IfStatement, WhileStatement,
    FunctionDecl, ReturnStatement, ExpressionStatement,
    AssignExpr, BinaryExpr, UnaryExpr, LiteralExpr, VarExpr, CallExpr,
    # -- Ditambahkan v0.3: Type System (List) --
    ListExpr, IndexExpr, IndexAssignExpr,
    # -- Ditambahkan v0.3 lanjutan: Custom Type --
    TypeDecl, InstanceExpr, FieldAccessExpr, FieldAssignExpr,
    # -- Ditambahkan v0.5: for-loop, Web Route & HTML block --
    ForStatement, RouteStatement, HtmlBlockExpr,
)
from runtime import (
    Environment, AstraRuntimeError, ReturnSignal,
    AstraFunction, AstraBuiltinFunction,
    # -- Ditambahkan v0.3: Type System (List) --
    AstraList,
    # -- Ditambahkan v0.3 lanjutan: Custom Type --
    AstraTypeDef, AstraInstance,
    # -- Ditambahkan v0.5: Map --
    AstraMap,
)


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        # v0.5: registry route untuk HTTP_SERVER_START -- diisi oleh
        # _exec_RouteStatement, dibaca oleh built-in HTTP_SERVER_START.
        self._routes = {}  # path (str) -> (body_statements, closure_env)
        self._install_builtins()
        # v0.5 (optimisasi performa): dispatch table di-cache SEKALI di sini
        # (bukan di-resolve ulang lewat getattr()+f-string setiap kali
        # _exec_statement/_eval dipanggil). Diukur dengan cProfile pada while
        # loop 50.000 iterasi: sebelum optimisasi total 1.297s, getattr()
        # dipanggil 650.008 kali sebagai kontributor waktu terbesar kedua.
        # Key memakai class object langsung (type(node)), bukan nama string,
        # supaya lookup dict lebih cepat daripada string formatting berulang.
        self._exec_dispatch = self._build_dispatch_table("_exec_")
        self._eval_dispatch = self._build_dispatch_table("_eval_")

    def _build_dispatch_table(self, prefix):
        """
        Membangun {NamaClassNode: bound_method} dengan mencari semua method
        interpreter yang diawali prefix ("_exec_" atau "_eval_"), lalu
        mencocokkan sisa namanya ke class Node yang sudah diimpor dari
        parser.py (mis. method '_exec_LetStatement' -> class LetStatement).
        Class yang namanya tidak dikenal di parser.py dilewati (bukan error),
        supaya method helper internal yang kebetulan berawalan sama tidak
        ikut salah terdaftar.
        """
        import parser as parser_module
        table = {}
        for attr_name in dir(self):
            if not attr_name.startswith(prefix):
                continue
            node_class_name = attr_name[len(prefix):]
            node_class = getattr(parser_module, node_class_name, None)
            if node_class is not None and isinstance(node_class, type):
                table[node_class] = getattr(self, attr_name)
        return table

    # -- built-in functions ------------------------------------------------
    def _install_builtins(self):
        def _len(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("len() membutuhkan tepat 1 argumen", line)
            val = args[0]
            if isinstance(val, str):
                return len(val)
            if isinstance(val, AstraList):
                return len(val)
            raise AstraRuntimeError(
                f"len() tidak mendukung tipe '{self._type_name(val)}'",
                line,
                hint="len() hanya berlaku untuk string atau list",
            )

        # -- Ditambahkan v0.3: built-in function untuk operasi List --
        # (memakai fungsi, bukan method .push(), karena AstraLang belum
        # punya syntax method-call; ini akan disederhanakan lagi begitu
        # method syntax ditambahkan di versi berikutnya)
        def _push(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "push() membutuhkan tepat 2 argumen: push(daftar, nilai)", line,
                )
            target, value = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"push() argumen pertama harus List, dapat '{self._type_name(target)}'",
                    line,
                    hint="Contoh: push(daftar, 5)",
                )
            target.push(value)
            return None

        def _pop(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("pop() membutuhkan tepat 1 argumen: pop(daftar)", line)
            target = args[0]
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"pop() argumen pertama harus List, dapat '{self._type_name(target)}'",
                    line,
                    hint="Contoh: let terakhir = pop(daftar)",
                )
            return target.pop(line)

        def _get(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "get() membutuhkan tepat 2 argumen: get(daftar, index)", line,
                )
            target, index = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"get() argumen pertama harus List, dapat '{self._type_name(target)}'",
                    line,
                    hint="Contoh: get(daftar, 0), atau langsung pakai daftar[0]",
                )
            return target.get(index, line)

        # -- Ditambahkan v0.4: File I/O (fondasi untuk generate HTML/web) --
        def _write_file(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "write_file() membutuhkan tepat 2 argumen: write_file(path, isi)", line,
                )
            path, content = args
            if not isinstance(path, str):
                raise AstraRuntimeError(
                    f"write_file() argumen path harus string, dapat '{self._type_name(path)}'",
                    line,
                    hint='Contoh: write_file("index.html", "<h1>Halo</h1>")',
                )
            content_str = self._stringify(content) if not isinstance(content, str) else content
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content_str)
            except OSError as e:
                raise AstraRuntimeError(
                    f"Gagal menulis file '{path}': {e}",
                    line,
                    hint="Cek apakah folder tujuan ada dan bisa ditulis",
                )
            return None

        def _read_file(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("read_file() membutuhkan tepat 1 argumen: read_file(path)", line)
            path = args[0]
            if not isinstance(path, str):
                raise AstraRuntimeError(
                    f"read_file() argumen path harus string, dapat '{self._type_name(path)}'",
                    line,
                )
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                raise AstraRuntimeError(
                    f"File '{path}' tidak ditemukan",
                    line,
                    hint="Cek kembali path file, relatif terhadap folder tempat AstraLang dijalankan",
                )
            except OSError as e:
                raise AstraRuntimeError(f"Gagal membaca file '{path}': {e}", line)

        def _str(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("str() membutuhkan tepat 1 argumen", line)
            return self._stringify(args[0])

        # -- Ditambahkan v0.4: Web server sederhana bawaan (stdlib saja) --
        def _serve_html(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "serve_html() membutuhkan tepat 2 argumen: serve_html(html, port)", line,
                )
            html_content, port = args
            if not isinstance(html_content, str):
                raise AstraRuntimeError(
                    f"serve_html() argumen pertama harus string (isi HTML), dapat '{self._type_name(html_content)}'",
                    line,
                )
            if not isinstance(port, int) or isinstance(port, bool):
                raise AstraRuntimeError(
                    f"serve_html() argumen kedua harus integer (nomor port), dapat '{self._type_name(port)}'",
                    line,
                    hint="Contoh: serve_html(html, 8080)",
                )
            import http.server

            class _Handler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    body = html_content.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, fmt, *fmt_args):
                    pass  # bisukan log bawaan supaya tidak mengotori output CLI

            try:
                server = http.server.HTTPServer(("0.0.0.0", port), _Handler)
            except OSError as e:
                raise AstraRuntimeError(
                    f"Tidak bisa membuka port {port}: {e}",
                    line,
                    hint="Coba port lain, atau pastikan tidak ada program lain yang memakai port ini",
                )
            print(f"[AstraLang] Web server aktif di http://localhost:{port}/  (Ctrl+C untuk berhenti)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n[AstraLang] Web server dihentikan.")
            finally:
                server.server_close()
            return None

        # -- Ditambahkan v0.5: HTTP server multi-route bawaan --
        def _http_server_start(args, line):
            if len(args) != 1:
                raise AstraRuntimeError(
                    "HTTP_SERVER_START() membutuhkan tepat 1 argumen: HTTP_SERVER_START(port)", line,
                )
            port = args[0]
            if not isinstance(port, int) or isinstance(port, bool):
                raise AstraRuntimeError(
                    f"HTTP_SERVER_START() argumen harus integer (nomor port), dapat '{self._type_name(port)}'",
                    line,
                    hint="Contoh: HTTP_SERVER_START(8080)",
                )
            if not self._routes:
                raise AstraRuntimeError(
                    "Belum ada route yang didaftarkan sebelum HTTP_SERVER_START()",
                    line,
                    hint='Daftarkan minimal satu route dulu, mis. route "/" { return "Hello" }',
                )
            import http.server

            interpreter_self = self

            class _RouteHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    # Buang query string (?a=b) saat mencocokkan path route,
                    # supaya "/halo?x=1" tetap cocok dengan route "/halo".
                    path = self.path.split("?", 1)[0]
                    try:
                        result = interpreter_self._run_route(path, line)
                    except AstraRuntimeError as e:
                        body = f"<h1>500 Internal Error</h1><p>{e.message}</p>".encode("utf-8")
                        self.send_response(500)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return
                    if result is None:
                        body = f"<h1>404 Not Found</h1><p>Route '{path}' tidak terdaftar.</p>".encode("utf-8")
                        self.send_response(404)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return
                    # Kalau hasil route sudah berupa dokumen HTML lengkap
                    # (mis. dari blok html {...} atau string manual berisi
                    # <html>), kirim apa adanya. Kalau bukan, bungkus jadi
                    # teks polos sederhana supaya tetap tampil rapi di browser.
                    if "<html" in result.lower() or "<!doctype" in result.lower():
                        body = result.encode("utf-8")
                    else:
                        body = f"<pre>{result}</pre>".encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, fmt, *fmt_args):
                    pass

            try:
                server = http.server.HTTPServer(("0.0.0.0", port), _RouteHandler)
            except OSError as e:
                raise AstraRuntimeError(
                    f"Tidak bisa membuka port {port}: {e}",
                    line,
                    hint="Coba port lain, atau pastikan tidak ada program lain yang memakai port ini",
                )
            route_list = ", ".join(sorted(self._routes.keys()))
            print(f"[AstraLang] HTTP server aktif di http://localhost:{port}/  (Ctrl+C untuk berhenti)")
            print(f"[AstraLang] Route terdaftar: {route_list}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n[AstraLang] HTTP server dihentikan.")
            finally:
                server.server_close()
            return None

        # -- Ditambahkan v0.4: built-in siap pakai untuk pemula --
        def _input(args, line):
            if len(args) > 1:
                raise AstraRuntimeError(
                    "input() menerima paling banyak 1 argumen (teks prompt)", line,
                )
            prompt = args[0] if args else ""
            if args and not isinstance(prompt, str):
                raise AstraRuntimeError(
                    f"input() argumen prompt harus string, dapat '{self._type_name(prompt)}'",
                    line,
                )
            try:
                return input(prompt)
            except EOFError:
                raise AstraRuntimeError(
                    "Tidak ada input yang bisa dibaca (EOF)",
                    line,
                    hint="input() butuh program dijalankan secara interaktif di terminal",
                )

        def _random(args, line):
            if len(args) != 0:
                raise AstraRuntimeError("random() tidak menerima argumen, hasilnya selalu 0.0 sampai 1.0", line)
            import random as _random_module
            return _random_module.random()

        def _randint(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "randint() membutuhkan tepat 2 argumen: randint(min, maks)", line,
                )
            lo, hi = args
            if not isinstance(lo, int) or isinstance(lo, bool) or not isinstance(hi, int) or isinstance(hi, bool):
                raise AstraRuntimeError(
                    "randint() kedua argumen harus integer", line,
                    hint="Contoh: randint(1, 10) menghasilkan angka acak antara 1 sampai 10",
                )
            if lo > hi:
                raise AstraRuntimeError(
                    f"randint() argumen pertama ({lo}) tidak boleh lebih besar dari argumen kedua ({hi})",
                    line,
                )
            import random as _random_module
            return _random_module.randint(lo, hi)

        def _round(args, line):
            if len(args) not in (1, 2):
                raise AstraRuntimeError(
                    "round() membutuhkan 1 atau 2 argumen: round(angka) atau round(angka, jumlah_desimal)", line,
                )
            value = args[0]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise AstraRuntimeError(
                    f"round() argumen pertama harus angka, dapat '{self._type_name(value)}'", line,
                )
            digits = args[1] if len(args) == 2 else 0
            if not isinstance(digits, int) or isinstance(digits, bool):
                raise AstraRuntimeError("round() argumen kedua (jumlah desimal) harus integer", line)
            result = round(value, digits)
            if digits <= 0:
                return int(result)
            return result

        def _to_int(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("int() membutuhkan tepat 1 argumen", line)
            value = args[0]
            if isinstance(value, bool):
                return 1 if value else 0
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value.strip())
                except ValueError:
                    raise AstraRuntimeError(
                        f"Tidak bisa mengubah teks '{value}' menjadi integer",
                        line,
                        hint="Pastikan teksnya berupa angka bulat, mis. \"42\"",
                    )
            raise AstraRuntimeError(f"int() tidak mendukung tipe '{self._type_name(value)}'", line)

        def _to_float(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("float() membutuhkan tepat 1 argumen", line)
            value = args[0]
            if isinstance(value, bool):
                return 1.0 if value else 0.0
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.strip())
                except ValueError:
                    raise AstraRuntimeError(
                        f"Tidak bisa mengubah teks '{value}' menjadi float",
                        line,
                        hint="Pastikan teksnya berupa angka, mis. \"3.14\"",
                    )
            raise AstraRuntimeError(f"float() tidak mendukung tipe '{self._type_name(value)}'", line)

        # -- Ditambahkan v0.4 lanjutan: operasi List umum (sort, contains, dst) --
        def _sortable_key(value, line):
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise AstraRuntimeError(
                    f"sort() hanya bisa mengurutkan List berisi angka atau string, ketemu tipe '{self._type_name(value)}'",
                    line,
                    hint="Untuk mengurutkan List berisi custom type, gunakan sort_by(daftar, nama_fungsi)",
                )
            return value

        def _sort(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("sort() membutuhkan tepat 1 argumen: sort(daftar)", line)
            target = args[0]
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"sort() argumen harus List, dapat '{self._type_name(target)}'", line,
                )
            try:
                sorted_items = sorted(target.items, key=lambda v: _sortable_key(v, line))
            except TypeError:
                raise AstraRuntimeError(
                    "Semua elemen List harus bertipe sama (semuanya angka, atau semuanya string) untuk diurutkan",
                    line,
                )
            return AstraList(sorted_items)

        def _sort_by(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "sort_by() membutuhkan tepat 2 argumen: sort_by(daftar, nama_fungsi)", line,
                )
            target, key_func = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"sort_by() argumen pertama harus List, dapat '{self._type_name(target)}'", line,
                )
            if not isinstance(key_func, AstraFunction):
                raise AstraRuntimeError(
                    f"sort_by() argumen kedua harus nama fungsi, dapat '{self._type_name(key_func)}'",
                    line,
                    hint="Contoh: function ambil_skor(p) { return p.skor }\\nsort_by(daftar, ambil_skor)",
                )
            if key_func.arity != 1:
                raise AstraRuntimeError(
                    f"Fungsi kunci untuk sort_by() harus menerima tepat 1 parameter, '{key_func.name}' menerima {key_func.arity}",
                    line,
                )

            def _key_wrapper(item):
                return self._call_astra_function(key_func, [item], line)

            sorted_items = sorted(target.items, key=_key_wrapper)
            return AstraList(sorted_items)

        def _reverse(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("reverse() membutuhkan tepat 1 argumen: reverse(daftar)", line)
            target = args[0]
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"reverse() argumen harus List, dapat '{self._type_name(target)}'", line,
                )
            return AstraList(list(reversed(target.items)))

        def _contains(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "contains() membutuhkan tepat 2 argumen: contains(daftar, nilai)", line,
                )
            target, value = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"contains() argumen pertama harus List, dapat '{self._type_name(target)}'", line,
                )
            return value in target.items

        def _join(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "join() membutuhkan tepat 2 argumen: join(daftar, pemisah)", line,
                )
            target, sep = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"join() argumen pertama harus List, dapat '{self._type_name(target)}'", line,
                )
            if not isinstance(sep, str):
                raise AstraRuntimeError(
                    f"join() argumen kedua (pemisah) harus string, dapat '{self._type_name(sep)}'", line,
                )
            return sep.join(self._stringify(item) for item in target.items)

        def _slice(args, line):
            if len(args) != 3:
                raise AstraRuntimeError(
                    "slice() membutuhkan tepat 3 argumen: slice(daftar, mulai, akhir)", line,
                )
            target, start, end = args
            if not isinstance(target, AstraList):
                raise AstraRuntimeError(
                    f"slice() argumen pertama harus List, dapat '{self._type_name(target)}'", line,
                )
            for label, v in (("mulai", start), ("akhir", end)):
                if not isinstance(v, int) or isinstance(v, bool):
                    raise AstraRuntimeError(
                        f"slice() argumen '{label}' harus integer, dapat '{self._type_name(v)}'", line,
                    )
            return AstraList(target.items[start:end])

        # -- Ditambahkan v0.5: Map (dictionary sederhana) --
        def _map_new(args, line):
            if len(args) != 0:
                raise AstraRuntimeError("map_new() tidak menerima argumen", line)
            return AstraMap()

        def _map_get(args, line):
            if len(args) != 2:
                raise AstraRuntimeError("map_get() membutuhkan tepat 2 argumen: map_get(peta, key)", line)
            target, key = args
            if not isinstance(target, AstraMap):
                raise AstraRuntimeError(f"map_get() argumen pertama harus Map, dapat '{self._type_name(target)}'", line)
            if not isinstance(key, str):
                raise AstraRuntimeError(f"map_get() key harus string, dapat '{self._type_name(key)}'", line)
            return target.get(key, line)

        def _map_set(args, line):
            if len(args) != 3:
                raise AstraRuntimeError("map_set() membutuhkan tepat 3 argumen: map_set(peta, key, nilai)", line)
            target, key, value = args
            if not isinstance(target, AstraMap):
                raise AstraRuntimeError(f"map_set() argumen pertama harus Map, dapat '{self._type_name(target)}'", line)
            if not isinstance(key, str):
                raise AstraRuntimeError(f"map_set() key harus string, dapat '{self._type_name(key)}'", line)
            target.set(key, value)
            return None

        def _map_has(args, line):
            if len(args) != 2:
                raise AstraRuntimeError("map_has() membutuhkan tepat 2 argumen: map_has(peta, key)", line)
            target, key = args
            if not isinstance(target, AstraMap):
                raise AstraRuntimeError(f"map_has() argumen pertama harus Map, dapat '{self._type_name(target)}'", line)
            return target.has(key)

        def _map_keys(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("map_keys() membutuhkan tepat 1 argumen: map_keys(peta)", line)
            target = args[0]
            if not isinstance(target, AstraMap):
                raise AstraRuntimeError(f"map_keys() argumen harus Map, dapat '{self._type_name(target)}'", line)
            return AstraList(target.keys())

        # -- Ditambahkan v0.5: JSON support --
        def _astra_to_json_value(value, line):
            """Konversi nilai AstraLang -> struktur Python murni siap json.dumps()."""
            if value is None or isinstance(value, (bool, int, float, str)):
                return value
            if isinstance(value, AstraList):
                return [_astra_to_json_value(v, line) for v in value.items]
            if isinstance(value, AstraMap):
                return {k: _astra_to_json_value(v, line) for k, v in value.items.items()}
            if isinstance(value, AstraInstance):
                return {k: _astra_to_json_value(v, line) for k, v in value.values.items()}
            raise AstraRuntimeError(
                f"Tipe '{self._type_name(value)}' tidak bisa diubah menjadi JSON",
                line,
                hint="JSON hanya mendukung: angka, string, boolean, null, List, Map, dan custom type",
            )

        def _json_from_python_value(value):
            """Konversi struktur Python (hasil json.loads()) -> nilai AstraLang."""
            if isinstance(value, dict):
                return AstraMap({k: _json_from_python_value(v) for k, v in value.items()})
            if isinstance(value, list):
                return AstraList([_json_from_python_value(v) for v in value])
            return value  # None/bool/int/float/str sudah representasi AstraLang yang valid

        def _json_stringify(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("json_stringify() membutuhkan tepat 1 argumen", line)
            import json as _json_module
            py_value = _astra_to_json_value(args[0], line)
            return _json_module.dumps(py_value)

        def _json_parse(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("json_parse() membutuhkan tepat 1 argumen (string JSON)", line)
            text = args[0]
            if not isinstance(text, str):
                raise AstraRuntimeError(
                    f"json_parse() membutuhkan string, dapat '{self._type_name(text)}'", line,
                )
            import json as _json_module
            try:
                py_value = _json_module.loads(text)
            except _json_module.JSONDecodeError as e:
                raise AstraRuntimeError(
                    f"Teks bukan JSON yang valid: {e}",
                    line,
                    hint='Pastikan formatnya JSON yang benar, mis. \'{"nama": "Astra"}\'',
                )
            return _json_from_python_value(py_value)

        # -- Ditambahkan v0.5: timer (blocking, dijalankan di thread utama) --
        def _timer_after(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "timer_after() membutuhkan tepat 2 argumen: timer_after(ms, nama_fungsi)", line,
                )
            ms, callback = args
            if not isinstance(ms, (int, float)) or isinstance(ms, bool):
                raise AstraRuntimeError(f"timer_after() argumen pertama (ms) harus angka, dapat '{self._type_name(ms)}'", line)
            if not isinstance(callback, AstraFunction):
                raise AstraRuntimeError(
                    f"timer_after() argumen kedua harus nama fungsi, dapat '{self._type_name(callback)}'",
                    line,
                    hint='Contoh: function selesai() { print "Done" }\ntimer_after(1000, selesai)',
                )
            if callback.arity != 0:
                raise AstraRuntimeError(
                    f"Fungsi untuk timer_after() tidak boleh punya parameter, '{callback.name}' punya {callback.arity}",
                    line,
                )
            import time as _time_module
            # v0.5: implementasi BLOCKING (bukan async) -- program AstraLang
            # berhenti sejenak selama durasi timer, baru menjalankan callback.
            # Ini keterbatasan yang jujur dicatat: AstraLang belum punya event
            # loop/concurrency sungguhan, jadi timer_after() TIDAK bisa
            # berjalan "di latar belakang" sambil kode lain tetap jalan.
            _time_module.sleep(ms / 1000.0)
            return self._call_astra_function(callback, [], line)

        # -- Ditambahkan v0.5: string functions dasar --
        def _require_string(value, func_name, line):
            if not isinstance(value, str):
                raise AstraRuntimeError(
                    f"{func_name}() membutuhkan argumen string, dapat '{self._type_name(value)}'",
                    line,
                )

        def _upper(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("upper() membutuhkan tepat 1 argumen", line)
            _require_string(args[0], "upper", line)
            return args[0].upper()

        def _lower(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("lower() membutuhkan tepat 1 argumen", line)
            _require_string(args[0], "lower", line)
            return args[0].lower()

        def _trim(args, line):
            if len(args) != 1:
                raise AstraRuntimeError("trim() membutuhkan tepat 1 argumen", line)
            _require_string(args[0], "trim", line)
            return args[0].strip()

        def _split(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "split() membutuhkan tepat 2 argumen: split(teks, pemisah)", line,
                )
            text, sep = args
            _require_string(text, "split", line)
            if not isinstance(sep, str) or sep == "":
                raise AstraRuntimeError(
                    "split() argumen pemisah harus string yang tidak kosong", line,
                    hint='Contoh: split("a,b,c", ",")',
                )
            return AstraList(text.split(sep))

        def _replace(args, line):
            if len(args) != 3:
                raise AstraRuntimeError(
                    "replace() membutuhkan tepat 3 argumen: replace(teks, cari, ganti)", line,
                )
            text, old, new = args
            _require_string(text, "replace", line)
            if not isinstance(old, str) or not isinstance(new, str):
                raise AstraRuntimeError(
                    "replace() argumen 'cari' dan 'ganti' harus string", line,
                )
            return text.replace(old, new)

        def _starts_with(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "starts_with() membutuhkan tepat 2 argumen: starts_with(teks, awalan)", line,
                )
            text, prefix = args
            _require_string(text, "starts_with", line)
            if not isinstance(prefix, str):
                raise AstraRuntimeError("starts_with() argumen kedua harus string", line)
            return text.startswith(prefix)

        def _ends_with(args, line):
            if len(args) != 2:
                raise AstraRuntimeError(
                    "ends_with() membutuhkan tepat 2 argumen: ends_with(teks, akhiran)", line,
                )
            text, suffix = args
            _require_string(text, "ends_with", line)
            if not isinstance(suffix, str):
                raise AstraRuntimeError("ends_with() argumen kedua harus string", line)
            return text.endswith(suffix)

        self.global_env.define("upper", AstraBuiltinFunction("upper", 1, _upper))
        self.global_env.define("lower", AstraBuiltinFunction("lower", 1, _lower))
        self.global_env.define("trim", AstraBuiltinFunction("trim", 1, _trim))
        self.global_env.define("split", AstraBuiltinFunction("split", 2, _split))
        self.global_env.define("replace", AstraBuiltinFunction("replace", 3, _replace))
        self.global_env.define("starts_with", AstraBuiltinFunction("starts_with", 2, _starts_with))
        self.global_env.define("ends_with", AstraBuiltinFunction("ends_with", 2, _ends_with))

        self.global_env.define("len", AstraBuiltinFunction("len", 1, _len))
        self.global_env.define("push", AstraBuiltinFunction("push", 2, _push))
        self.global_env.define("pop", AstraBuiltinFunction("pop", 1, _pop))
        self.global_env.define("get", AstraBuiltinFunction("get", 2, _get))
        self.global_env.define("write_file", AstraBuiltinFunction("write_file", 2, _write_file))
        self.global_env.define("read_file", AstraBuiltinFunction("read_file", 1, _read_file))
        self.global_env.define("str", AstraBuiltinFunction("str", 1, _str))
        self.global_env.define("serve_html", AstraBuiltinFunction("serve_html", 2, _serve_html))
        self.global_env.define("HTTP_SERVER_START", AstraBuiltinFunction("HTTP_SERVER_START", 1, _http_server_start))
        self.global_env.define("map_new", AstraBuiltinFunction("map_new", 0, _map_new))
        self.global_env.define("map_get", AstraBuiltinFunction("map_get", 2, _map_get))
        self.global_env.define("map_set", AstraBuiltinFunction("map_set", 3, _map_set))
        self.global_env.define("map_has", AstraBuiltinFunction("map_has", 2, _map_has))
        self.global_env.define("map_keys", AstraBuiltinFunction("map_keys", 1, _map_keys))
        self.global_env.define("json_stringify", AstraBuiltinFunction("json_stringify", 1, _json_stringify))
        self.global_env.define("json_parse", AstraBuiltinFunction("json_parse", 1, _json_parse))
        self.global_env.define("file_read", AstraBuiltinFunction("file_read", 1, _read_file))
        self.global_env.define("file_write", AstraBuiltinFunction("file_write", 2, _write_file))
        self.global_env.define("timer_after", AstraBuiltinFunction("timer_after", 2, _timer_after))
        self.global_env.define("input", AstraBuiltinFunction("input", -1, _input))
        self.global_env.define("random", AstraBuiltinFunction("random", 0, _random))
        self.global_env.define("randint", AstraBuiltinFunction("randint", 2, _randint))
        self.global_env.define("round", AstraBuiltinFunction("round", -1, _round))
        self.global_env.define("int", AstraBuiltinFunction("int", 1, _to_int))
        self.global_env.define("float", AstraBuiltinFunction("float", 1, _to_float))
        self.global_env.define("sort", AstraBuiltinFunction("sort", 1, _sort))
        self.global_env.define("sort_by", AstraBuiltinFunction("sort_by", 2, _sort_by))
        self.global_env.define("reverse", AstraBuiltinFunction("reverse", 1, _reverse))
        self.global_env.define("contains", AstraBuiltinFunction("contains", 2, _contains))
        self.global_env.define("join", AstraBuiltinFunction("join", 2, _join))
        self.global_env.define("slice", AstraBuiltinFunction("slice", 3, _slice))

    # -- entry point ---------------------------------------------------------
    def run(self, program: Program):
        for stmt in program.statements:
            self._exec_statement(stmt, self.global_env)

    # -- statement execution ---------------------------------------------------
    def _exec_statement(self, stmt, env: Environment):
        method = self._exec_dispatch.get(type(stmt))
        if method is None:
            raise AstraRuntimeError(
                f"Statement tidak dikenal oleh interpreter: {type(stmt).__name__}"
            )
        return method(stmt, env)

    def _exec_LetStatement(self, stmt: LetStatement, env: Environment):
        value = self._eval(stmt.value, env)
        env.define(stmt.name, value)

    def _exec_PrintStatement(self, stmt: PrintStatement, env: Environment):
        value = self._eval(stmt.value, env)
        print(self._stringify(value))

    def _exec_IfStatement(self, stmt: IfStatement, env: Environment):
        condition = self._eval(stmt.condition, env)
        if self._is_truthy(condition):
            block_env = Environment(parent=env)
            for s in stmt.then_branch:
                self._exec_statement(s, block_env)
        elif stmt.else_branch is not None:
            block_env = Environment(parent=env)
            for s in stmt.else_branch:
                self._exec_statement(s, block_env)

    def _exec_WhileStatement(self, stmt: WhileStatement, env: Environment):
        # Batas iterasi pengaman untuk v0.1 supaya infinite loop tak sengaja
        # tidak membuat prototype hang selamanya di perangkat terbatas (mis. IoT/Termux).
        max_iterations = 10_000_000
        count = 0
        while self._is_truthy(self._eval(stmt.condition, env)):
            block_env = Environment(parent=env)
            for s in stmt.body:
                self._exec_statement(s, block_env)
            count += 1
            if count > max_iterations:
                raise AstraRuntimeError(
                    "Loop melebihi batas maksimum iterasi (kemungkinan infinite loop)",
                    stmt.line,
                )

    # -- Ditambahkan v0.5: for-loop -------------------------------------------
    def _exec_ForStatement(self, stmt: ForStatement, env: Environment):
        target = self._eval(stmt.iterable, env)
        if isinstance(target, AstraList):
            elements = target.items
        elif isinstance(target, str):
            elements = list(target)
        else:
            raise AstraRuntimeError(
                f"'for {stmt.var_name} in ...' membutuhkan List atau string, dapat '{self._type_name(target)}'",
                stmt.line,
                hint="Contoh: for item in [1, 2, 3] { print item }",
            )
        for item in elements:
            block_env = Environment(parent=env)
            block_env.define(stmt.var_name, item)
            for s in stmt.body:
                self._exec_statement(s, block_env)

    def _exec_FunctionDecl(self, stmt: FunctionDecl, env: Environment):
        func = AstraFunction(stmt, closure_env=env)
        env.define(stmt.name, func)

    # -- Ditambahkan v0.5: Web Route -----------------------------------------
    def _exec_RouteStatement(self, stmt: RouteStatement, env: Environment):
        path = self._eval(stmt.path_expr, env)
        if not isinstance(path, str):
            raise AstraRuntimeError(
                f"route membutuhkan path berupa string, dapat '{self._type_name(path)}'",
                stmt.line,
                hint='Contoh: route "/" { return "Hello" }',
            )
        if not path.startswith("/"):
            raise AstraRuntimeError(
                f"Path route harus diawali '/', dapat '{path}'",
                stmt.line,
                hint='Contoh: route "/tentang" { ... }',
            )
        # Route disimpan dengan closure_env = env saat 'route' dideklarasikan,
        # supaya body route bisa mengakses variabel/fungsi yang didefinisikan
        # sebelum route ini di source code (sama seperti closure function).
        self._routes[path] = (stmt.body, env)

    def _run_route(self, path, line=None):
        """
        v0.5: mengeksekusi body sebuah route yang sudah terdaftar, dipanggil
        dari handler HTTP_SERVER_START saat ada request masuk. Mengembalikan
        string hasil 'return' di dalam body route, atau None kalau route
        tidak ditemukan (caller menangani sebagai 404).
        """
        if path not in self._routes:
            return None
        body, closure_env = self._routes[path]
        call_env = Environment(parent=closure_env)
        try:
            for s in body:
                self._exec_statement(s, call_env)
        except ReturnSignal as r:
            return self._stringify(r.value) if r.value is not None else ""
        return ""  # route tanpa 'return' eksplisit -> halaman kosong, bukan error

    # -- Ditambahkan v0.3 lanjutan: Custom Type -----------------------------
    def _exec_TypeDecl(self, stmt: TypeDecl, env: Environment):
        type_def = AstraTypeDef(stmt.name, stmt.fields)
        # Type didaftarkan sebagai variabel biasa (nama Type -> AstraTypeDef)
        # supaya bisa dicari lewat env.get() saat membuat instance, sama
        # seperti fungsi dan variabel lain di AstraLang.
        env.define(stmt.name, type_def)

    def _exec_ReturnStatement(self, stmt: ReturnStatement, env: Environment):
        value = None
        if stmt.value is not None:
            value = self._eval(stmt.value, env)
        raise ReturnSignal(value)

    def _exec_ExpressionStatement(self, stmt: ExpressionStatement, env: Environment):
        self._eval(stmt.expr, env)

    # -- expression evaluation ---------------------------------------------------
    def _eval(self, node, env: Environment):
        method = self._eval_dispatch.get(type(node))
        if method is None:
            raise AstraRuntimeError(
                f"Ekspresi tidak dikenal oleh interpreter: {type(node).__name__}"
            )
        return method(node, env)

    def _eval_LiteralExpr(self, node: LiteralExpr, env: Environment):
        return node.value

    def _eval_VarExpr(self, node: VarExpr, env: Environment):
        return env.get(node.name, node.line)

    def _eval_AssignExpr(self, node: AssignExpr, env: Environment):
        value = self._eval(node.value, env)
        env.set(node.name, value, node.line)
        return value

    # -- Ditambahkan v0.5: HTML block (gula sintaks generate HTML) ----------
    def _eval_HtmlBlockExpr(self, node: HtmlBlockExpr, env: Environment):
        import html as _html_escape_module

        parts = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\">"]
        title_set = False
        body_parts = []
        for kind, value_node in node.entries:
            value = self._eval(value_node, env)
            text = self._stringify(value)
            escaped = _html_escape_module.escape(text)
            if kind == "title":
                parts.append(f"<title>{escaped}</title>")
                title_set = True
            elif kind == "heading":
                body_parts.append(f"<h1>{escaped}</h1>")
            elif kind == "text":
                body_parts.append(f"<p>{escaped}</p>")
        if not title_set:
            parts.append("<title>AstraLang</title>")
        parts.append("</head><body>")
        parts.extend(body_parts)
        parts.append("</body></html>")
        return "".join(parts)

    # -- Ditambahkan v0.3: Type System (List) -----------------------------
    def _eval_ListExpr(self, node: ListExpr, env: Environment):
        items = [self._eval(el, env) for el in node.elements]
        return AstraList(items)

    def _eval_IndexExpr(self, node: IndexExpr, env: Environment):
        collection = self._eval(node.collection, env)
        index = self._eval(node.index, env)
        if isinstance(collection, AstraList):
            return collection.get(index, node.line)
        if isinstance(collection, str):
            if not isinstance(index, int) or isinstance(index, bool):
                raise AstraRuntimeError(
                    f"Index string harus berupa integer, dapat '{self._type_name(index)}'",
                    node.line,
                )
            if index < 0 or index >= len(collection):
                raise AstraRuntimeError(
                    f"Index {index} di luar jangkauan (string ini panjangnya {len(collection)})",
                    node.line,
                    hint=f"Index yang valid adalah 0 sampai {len(collection) - 1}" if collection else "String ini kosong",
                )
            return collection[index]
        raise AstraRuntimeError(
            f"Tipe '{self._type_name(collection)}' tidak bisa diakses dengan index [ ]",
            node.line,
            hint="Indexing dengan [ ] hanya berlaku untuk List atau string",
        )

    def _eval_IndexAssignExpr(self, node: IndexAssignExpr, env: Environment):
        collection = self._eval(node.collection, env)
        index = self._eval(node.index, env)
        value = self._eval(node.value, env)
        if not isinstance(collection, AstraList):
            raise AstraRuntimeError(
                f"Tidak bisa assign ke index pada tipe '{self._type_name(collection)}'",
                node.line,
                hint="Assignment lewat index (mis. daftar[0] = nilai) hanya berlaku untuk List",
            )
        collection.set(index, value, node.line)
        return value

    # -- Ditambahkan v0.3 lanjutan: Custom Type -----------------------------
    def _eval_InstanceExpr(self, node: InstanceExpr, env: Environment):
        type_def = self._lookup_type(node.type_name, env, node.line)

        given_names = [name for name, _ in node.field_values]
        # Cek field yang diberikan tapi tidak dikenal oleh type-nya
        unknown = [name for name in given_names if name not in type_def.fields]
        if unknown:
            raise AstraRuntimeError(
                f"Field {unknown} tidak dikenal pada type '{type_def.name}'",
                node.line,
                hint=f"Field yang tersedia pada '{type_def.name}': {', '.join(type_def.fields)}",
            )
        # Cek field wajib yang belum diisi
        missing = [f for f in type_def.fields if f not in given_names]
        if missing:
            raise AstraRuntimeError(
                f"Field {missing} belum diisi saat membuat instance '{type_def.name}'",
                node.line,
                hint=f"Semua field wajib diisi saat membuat instance: {', '.join(type_def.fields)}",
            )

        values = {name: self._eval(value_node, env) for name, value_node in node.field_values}
        return AstraInstance(type_def, values)

    def _eval_FieldAccessExpr(self, node: FieldAccessExpr, env: Environment):
        obj = self._eval(node.obj, env)
        if not isinstance(obj, AstraInstance):
            raise AstraRuntimeError(
                f"Tidak bisa mengakses field '.{node.field_name}' pada tipe '{self._type_name(obj)}'",
                node.line,
                hint="Akses field dengan '.' hanya berlaku untuk instance custom type",
            )
        return obj.get_field(node.field_name, node.line)

    def _eval_FieldAssignExpr(self, node: FieldAssignExpr, env: Environment):
        obj = self._eval(node.obj, env)
        if not isinstance(obj, AstraInstance):
            raise AstraRuntimeError(
                f"Tidak bisa assign ke field '.{node.field_name}' pada tipe '{self._type_name(obj)}'",
                node.line,
                hint="Assignment field dengan '.' hanya berlaku untuk instance custom type",
            )
        value = self._eval(node.value, env)
        obj.set_field(node.field_name, value, node.line)
        return value

    def _eval_UnaryExpr(self, node: UnaryExpr, env: Environment):
        operand = self._eval(node.operand, env)
        if node.op == "-":
            self._check_number(operand, node.line, "operator '-' (negasi)")
            return -operand
        if node.op == "not":
            return not self._is_truthy(operand)
        raise AstraRuntimeError(f"Operator unary tidak dikenal: {node.op}", node.line)

    def _eval_BinaryExpr(self, node: BinaryExpr, env: Environment):
        op = node.op

        # short-circuit untuk and/or
        if op == "and":
            left = self._eval(node.left, env)
            if not self._is_truthy(left):
                return left
            return self._eval(node.right, env)
        if op == "or":
            left = self._eval(node.left, env)
            if self._is_truthy(left):
                return left
            return self._eval(node.right, env)

        left = self._eval(node.left, env)
        right = self._eval(node.right, env)

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            self._check_number(left, node.line, "operator '+'")
            self._check_number(right, node.line, "operator '+'")
            return left + right
        if op == "-":
            self._check_number(left, node.line, "operator '-'")
            self._check_number(right, node.line, "operator '-'")
            return left - right
        if op == "*":
            self._check_number(left, node.line, "operator '*'")
            self._check_number(right, node.line, "operator '*'")
            return left * right
        if op == "/":
            self._check_number(left, node.line, "operator '/'")
            self._check_number(right, node.line, "operator '/'")
            if right == 0:
                raise AstraRuntimeError(
                    "Nggak bisa membagi dengan angka nol",
                    node.line,
                    hint="Cek dulu apakah pembaginya nol sebelum membagi",
                )
            result = left / right
            if isinstance(left, int) and isinstance(right, int) and result.is_integer():
                return int(result)
            return result
        if op == "%":
            self._check_number(left, node.line, "operator '%'")
            self._check_number(right, node.line, "operator '%'")
            if right == 0:
                raise AstraRuntimeError(
                    "Nggak bisa menghitung sisa bagi (%) dengan angka nol",
                    node.line,
                    hint="Cek dulu apakah pembaginya nol sebelum memakai operator %",
                )
            return left % right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            self._check_comparable(left, right, node.line)
            return left < right
        if op == ">":
            self._check_comparable(left, right, node.line)
            return left > right
        if op == "<=":
            self._check_comparable(left, right, node.line)
            return left <= right
        if op == ">=":
            self._check_comparable(left, right, node.line)
            return left >= right

        raise AstraRuntimeError(f"Operator biner tidak dikenal: {op}", node.line)

    def _eval_CallExpr(self, node: CallExpr, env: Environment):
        if not isinstance(node.callee, VarExpr):
            raise AstraRuntimeError("Hanya nama fungsi yang bisa dipanggil di v0.1", node.line)
        callee_name = node.callee.name
        func = env.get(callee_name, node.line)
        args = [self._eval(arg, env) for arg in node.args]

        if isinstance(func, AstraBuiltinFunction):
            if func.arity != -1 and len(args) != func.arity:
                raise AstraRuntimeError(
                    f"Fungsi '{func.name}' membutuhkan {func.arity} argumen, diberikan {len(args)}",
                    node.line,
                )
            return func.py_func(args, node.line)

        if isinstance(func, AstraFunction):
            return self._call_astra_function(func, args, node.line)

        raise AstraRuntimeError(f"'{callee_name}' bukan fungsi yang bisa dipanggil", node.line)

    def _call_astra_function(self, func: AstraFunction, args, line):
        """
        v0.4: dipisah dari _eval_CallExpr supaya bisa dipanggil ulang dari
        tempat lain di interpreter (mis. built-in sort_by yang perlu
        memanggil balik function AstraLang sebagai key pengurutan), tanpa
        duplikasi logic pemanggilan function.
        """
        if len(args) != func.arity:
            raise AstraRuntimeError(
                f"Fungsi '{func.name}' membutuhkan {func.arity} argumen, diberikan {len(args)}",
                line,
            )
        call_env = Environment(parent=func.closure_env)
        for param_name, arg_value in zip(func.declaration.params, args):
            call_env.define(param_name, arg_value)
        try:
            for s in func.declaration.body:
                self._exec_statement(s, call_env)
        except ReturnSignal as r:
            return r.value
        return None  # fungsi tanpa return eksplisit

    # -- helper ----------------------------------------------------------------
    def _lookup_type(self, type_name, env, line):
        """
        v0.3 lanjutan: mencari AstraTypeDef berdasarkan nama, dengan pesan
        error yang spesifik untuk konteks custom type (bukan pesan generik
        'variabel tidak ditemukan' yang menyarankan 'let', yang membingungkan
        untuk kasus type yang belum dideklarasikan).
        """
        try:
            value = env.get(type_name, line)
        except AstraRuntimeError:
            raise AstraRuntimeError(
                f"Type '{type_name}' tidak dikenal",
                line,
                hint=f"Deklarasikan dulu dengan 'type {type_name} {{ field1 field2 }}' sebelum membuat instance-nya",
            )
        if not isinstance(value, AstraTypeDef):
            raise AstraRuntimeError(
                f"'{type_name}' bukan sebuah type, tidak bisa dibuat instance-nya",
                line,
                hint=f"'{type_name}' sudah dipakai untuk sesuatu yang lain (bukan type); pilih nama lain atau cek ulang deklarasinya",
            )
        return value

    def _is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def _check_number(self, value, line, context):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise AstraRuntimeError(
                f"Tipe data tidak sesuai untuk {context}: diharapkan angka, dapat '{self._type_name(value)}'",
                line,
                hint="Pastikan kedua operand bertipe integer atau float",
            )

    def _check_comparable(self, left, right, line):
        numeric = isinstance(left, (int, float)) and not isinstance(left, bool) and \
                  isinstance(right, (int, float)) and not isinstance(right, bool)
        both_str = isinstance(left, str) and isinstance(right, str)
        if not (numeric or both_str):
            raise AstraRuntimeError(
                f"Tidak bisa membandingkan '{self._type_name(left)}' dengan '{self._type_name(right)}'",
                line,
                hint="Operator <, >, <=, >= hanya berlaku antara dua angka atau dua string",
            )

    def _type_name(self, value):
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        if value is None:
            return "null"
        if isinstance(value, AstraList):
            return "list"
        if isinstance(value, AstraMap):
            return "map"
        if isinstance(value, AstraInstance):
            return value.type_def.name
        if isinstance(value, AstraTypeDef):
            return "type"
        if isinstance(value, (AstraFunction, AstraBuiltinFunction)):
            return "function"
        return type(value).__name__

    def _stringify(self, value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, AstraList):
            return "[" + ", ".join(self._stringify(item) for item in value.items) + "]"
        if isinstance(value, AstraMap):
            # Catatan: representasi print ini MIRIP JSON tapi bukan JSON
            # valid (String AstraLang lain tidak otomatis dikutip di sini,
            # konsisten dengan cara List/instance ditampilkan). Untuk JSON
            # yang benar-benar valid, gunakan json_stringify().
            entries_str = ", ".join(
                f"{k}: {self._stringify(v)}" for k, v in value.items.items()
            )
            return "{" + entries_str + "}"
        if isinstance(value, AstraInstance):
            fields_str = ", ".join(
                f"{k}: {self._stringify(v)}" for k, v in value.values.items()
            )
            return f"{value.type_def.name} {{{fields_str}}}"
        return str(value)
