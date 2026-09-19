"""
Test Fitur Baru v0.5: Web Server, Automation, Developer Tools
==================================================================
Menguji:
- for item in daftar { ... } -- for-loop untuk List/string
- route "/path" { return ... } + HTTP_SERVER_START(port) -- HTTP server
  multi-route sungguhan (diuji dengan HTTP request nyata)
- html { title/heading/text } -- gula sintaks generate HTML
- Map (map_new/get/set/has/keys)
- JSON (json_stringify/json_parse), termasuk untuk custom type
- timer_after (blocking, diverifikasi dengan pengukuran waktu nyata)
- KASUS KRITIS: 'html' tetap bisa dipakai sebagai nama variabel biasa
  (regresi kompatibilitas mundur terhadap contoh v0.4)

Cara jalankan:
    python3 tests/test_v0_5_features.py
"""

import sys
import os
import io
import contextlib
import threading
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import parse_source, ParserError
from interpreter import Interpreter
from runtime import AstraRuntimeError

PASSED = 0
FAILED = 0


def check(name, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [OK] {name}")
    else:
        FAILED += 1
        print(f"  [GAGAL] {name}")


def run_and_capture(source):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(parse_source(source))
    return buf.getvalue()


# --- for-loop ---

def test_for_loop_list():
    print("Test: for-loop List angka")
    out = run_and_capture("for x in [1, 2, 3] { print x }")
    check("iterasi list angka benar", out.strip().splitlines() == ["1", "2", "3"])


def test_for_loop_string():
    print("Test: for-loop string (iterasi karakter)")
    out = run_and_capture('for c in "abc" { print c }')
    check("iterasi karakter benar", out.strip().splitlines() == ["a", "b", "c"])


def test_for_loop_custom_type():
    print("Test: for-loop List custom type + akumulasi")
    src = '''
type Pemain {
    nama
    skor
}
let daftar = [Pemain { nama: "A", skor: 10 }, Pemain { nama: "B", skor: 20 }]
let total = 0
for p in daftar {
    total = total + p.skor
}
print total
'''
    out = run_and_capture(src)
    check("akumulasi via for-loop benar", out.strip() == "30")


def test_for_loop_variable_scope():
    print("Test: variabel loop for tidak bocor ke luar scope")
    try:
        run_and_capture('for x in [1, 2, 3] { print x }\nprint x\n')
        check("variabel loop tidak bocor", False)
    except AstraRuntimeError:
        check("variabel loop tidak bocor", True)


def test_for_loop_invalid_iterable():
    print("Test: for-loop menolak iterasi non-List/string")
    try:
        run_and_capture("for x in 5 { print x }")
        check("iterasi angka ditolak", False)
    except AstraRuntimeError as e:
        check("iterasi angka ditolak", True)
        check("hint diberikan", e.hint is not None)


# --- html block sebagai ekspresi ---

def test_html_block_expression():
    print("Test: html { } menghasilkan dokumen HTML lengkap")
    out = run_and_capture('let h = html { title "Judul" heading "Halo" text "isi" }\nprint h\n')
    result = out.strip()
    check("ada DOCTYPE", "<!DOCTYPE html>" in result)
    check("title benar", "<title>Judul</title>" in result)
    check("heading benar", "<h1>Halo</h1>" in result)
    check("text benar", "<p>isi</p>" in result)


def test_html_variable_name_still_works():
    print("Test: KASUS KRITIS - 'html' tetap bisa dipakai sebagai nama variabel biasa")
    out = run_and_capture('let html = "<p>halo</p>"\nprint html\n')
    check("html sebagai variabel tetap jalan (kompatibilitas v0.4)", out.strip() == "<p>halo</p>")


def test_html_block_invalid_field():
    print("Test: html { } menolak field selain title/heading/text")
    try:
        parse_source('let h = html { foo "bar" }')
        check("field tidak dikenal ditolak", False)
    except ParserError as e:
        check("field tidak dikenal ditolak", True)


# --- route + HTTP server ---

def test_route_registration_and_lookup():
    print("Test: route terdaftar dan bisa dijalankan lewat _run_route")
    src = '''
route "/" {
    return "Hello AstraLang"
}
route "/tentang" {
    return "Halaman tentang"
}
'''
    interp = Interpreter()
    interp.run(parse_source(src))
    check("route / terdaftar", "/" in interp._routes)
    check("route /tentang terdaftar", "/tentang" in interp._routes)
    result_root = interp._run_route("/")
    result_about = interp._run_route("/tentang")
    result_missing = interp._run_route("/tidak-ada")
    check("isi route / benar", result_root == "Hello AstraLang")
    check("isi route /tentang benar", result_about == "Halaman tentang")
    check("route tidak terdaftar mengembalikan None", result_missing is None)


def test_route_rejects_invalid_path():
    print("Test: route menolak path yang tidak diawali '/'")
    try:
        run_and_capture('route "tanpa-slash" { return "x" }')
        check("path tanpa slash ditolak", False)
    except AstraRuntimeError as e:
        check("path tanpa slash ditolak", True)


def test_http_server_real_requests():
    print("Test: HTTP_SERVER_START -- server NYATA, diuji dengan HTTP request sungguhan")
    port = 48801
    src = f'''
route "/" {{
    return "Hello AstraLang"
}}
route "/tentang" {{
    return html {{ title "Tentang" heading "Tentang Kami" text "Dibuat dengan AstraLang" }}
}}
HTTP_SERVER_START({port})
'''
    interp = Interpreter()
    t = threading.Thread(target=lambda: interp.run(parse_source(src)), daemon=True)
    t.start()
    time.sleep(0.6)

    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3)
        body = resp.read().decode("utf-8")
        check("GET / status 200", resp.status == 200)
        check("GET / isi benar", "Hello AstraLang" in body)

        resp2 = urllib.request.urlopen(f"http://127.0.0.1:{port}/tentang", timeout=3)
        body2 = resp2.read().decode("utf-8")
        check("GET /tentang status 200", resp2.status == 200)
        check("GET /tentang berisi html lengkap", "<html" in body2.lower() and "Tentang Kami" in body2)

        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/tidak-ada", timeout=3)
            check("GET /tidak-ada mengembalikan 404", False)
        except urllib.error.HTTPError as e:
            check("GET /tidak-ada mengembalikan 404", e.code == 404)
    except Exception as e:
        check(f"HTTP server test gagal total: {e}", False)


def test_http_server_requires_routes():
    print("Test: HTTP_SERVER_START menolak jika belum ada route terdaftar")
    try:
        run_and_capture("HTTP_SERVER_START(48802)")
        check("HTTP_SERVER_START tanpa route ditolak", False)
    except AstraRuntimeError as e:
        check("HTTP_SERVER_START tanpa route ditolak", True)


# --- Map ---

def test_map_basic_operations():
    print("Test: Map dasar (new/set/get/has/keys)")
    src = '''
let m = map_new()
map_set(m, "nama", "Astra")
map_set(m, "umur", 5)
print map_get(m, "nama")
print map_has(m, "umur")
print map_has(m, "tidak_ada")
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("map_get benar", lines[0] == "Astra")
    check("map_has true untuk key ada", lines[1] == "true")
    check("map_has false untuk key tidak ada", lines[2] == "false")


def test_map_get_missing_key_error():
    print("Test: map_get() untuk key yang tidak ada melempar error dengan hint")
    try:
        run_and_capture('let m = map_new()\nprint map_get(m, "x")\n')
        check("key tidak ada ditolak", False)
    except AstraRuntimeError as e:
        check("key tidak ada ditolak", True)
        check("hint menyebutkan map_has", "map_has" in e.hint)


def test_map_keys():
    print("Test: map_keys() mengembalikan List semua key")
    src = '''
let m = map_new()
map_set(m, "a", 1)
map_set(m, "b", 2)
let keys = map_keys(m)
print len(keys)
print contains(keys, "a")
print contains(keys, "b")
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("jumlah keys benar", lines[0] == "2")
    check("keys berisi a", lines[1] == "true")
    check("keys berisi b", lines[2] == "true")


# --- JSON ---

def test_json_stringify_and_parse_roundtrip():
    print("Test: json_stringify() dan json_parse() roundtrip")
    src = '''
let m = map_new()
map_set(m, "nama", "Astra")
map_set(m, "skor", [10, 20, 30])
let teks = json_stringify(m)
let parsed = json_parse(teks)
print map_get(parsed, "nama")
print map_get(parsed, "skor")
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("nama setelah roundtrip benar", lines[0] == "Astra")
    check("list setelah roundtrip benar", lines[1] == "[10, 20, 30]")


def test_json_stringify_custom_type():
    print("Test: json_stringify() untuk custom type")
    src = '''
type Point {
    x
    y
}
let p = Point { x: 1, y: 2 }
print json_stringify(p)
'''
    out = run_and_capture(src)
    check("json custom type valid", out.strip() == '{"x": 1, "y": 2}')


def test_json_parse_invalid_string():
    print("Test: json_parse() menolak string bukan JSON valid")
    try:
        run_and_capture('print json_parse("bukan json {{{")')
        check("json tidak valid ditolak", False)
    except AstraRuntimeError as e:
        check("json tidak valid ditolak", True)
        check("hint diberikan", e.hint is not None)


def test_json_produces_valid_json_syntax():
    print("Test: hasil json_stringify() benar-benar valid secara sintaks JSON (pakai json.loads Python)")
    import json as py_json
    src = '''
let m = map_new()
map_set(m, "aktif", true)
map_set(m, "kosong", null)
print json_stringify(m)
'''
    out = run_and_capture(src)
    parsed = py_json.loads(out.strip())  # akan melempar exception kalau tidak valid
    check("hasil json_stringify valid JSON murni (bisa diparse json.loads)", parsed == {"aktif": True, "kosong": None})


# --- file module alias ---

def test_file_read_write_alias(tmp_path):
    print("Test: file_read()/file_write() sebagai alias read_file/write_file")
    src = f'''
file_write("{tmp_path}", "isi dari file module")
print file_read("{tmp_path}")
'''
    out = run_and_capture(src)
    check("file_write/file_read bekerja", out.strip() == "isi dari file module")


# --- timer_after ---

def test_timer_after_blocking_delay():
    print("Test: timer_after() benar-benar menunda eksekusi (diverifikasi dengan waktu nyata)")
    src = '''
function selesai() {
    print "Done"
}
timer_after(150, selesai)
'''
    start = time.time()
    out = run_and_capture(src)
    elapsed = time.time() - start
    check("callback dijalankan", out.strip() == "Done")
    check("waktu tunda minimal 150ms benar-benar terjadi", elapsed >= 0.14)


def test_timer_after_rejects_function_with_params():
    print("Test: timer_after() menolak fungsi callback yang punya parameter")
    try:
        run_and_capture('function f(x) { print x }\ntimer_after(10, f)\n')
        check("callback dengan parameter ditolak", False)
    except AstraRuntimeError as e:
        check("callback dengan parameter ditolak", True)


# --- string functions ---

def test_string_functions_basic():
    print("Test: string functions dasar (upper/lower/trim)")
    src = '''
print upper("halo dunia")
print lower("HALO DUNIA")
print trim("   spasi   ")
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("upper benar", lines[0] == "HALO DUNIA")
    check("lower benar", lines[1] == "halo dunia")
    check("trim benar", lines[2] == "spasi")


def test_string_split():
    print("Test: split()")
    out = run_and_capture('print split("a,b,c", ",")')
    check("split benar", out.strip() == "[a, b, c]")


def test_string_split_used_with_for_loop():
    print("Test: split() dikombinasikan dengan for-loop (skenario nyata)")
    src = '''
let kalimat = "AstraLang itu mudah"
let kata_kata = split(kalimat, " ")
for kata in kata_kata {
    print upper(kata)
}
'''
    out = run_and_capture(src)
    check("kombinasi split+for benar", out.strip().splitlines() == ["ASTRALANG", "ITU", "MUDAH"])


def test_string_replace():
    print("Test: replace()")
    out = run_and_capture('print replace("halo dunia", "dunia", "AstraLang")')
    check("replace benar", out.strip() == "halo AstraLang")


def test_string_starts_ends_with():
    print("Test: starts_with() dan ends_with()")
    src = '''
print starts_with("AstraLang", "Astra")
print ends_with("AstraLang", "Lang")
print starts_with("AstraLang", "Lang")
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("starts_with true benar", lines[0] == "true")
    check("ends_with true benar", lines[1] == "true")
    check("starts_with false benar", lines[2] == "false")


def test_string_function_rejects_non_string():
    print("Test: string function menolak argumen non-string")
    try:
        run_and_capture("print upper(123)")
        check("upper(angka) ditolak", False)
    except AstraRuntimeError as e:
        check("upper(angka) ditolak", True)


def test_split_rejects_empty_separator():
    print("Test: split() menolak pemisah kosong")
    try:
        run_and_capture('print split("a,b", "")')
        check("split pemisah kosong ditolak", False)
    except AstraRuntimeError as e:
        check("split pemisah kosong ditolak", True)
        check("hint diberikan", e.hint is not None)


# --- regresi total ---

def test_full_regression_v0_1_to_v0_4():
    print("Test: regresi total v0.1/v0.3/v0.4 tetap benar setelah semua fitur v0.5")
    src = '''
function faktorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * faktorial(n - 1)
    }
}
type Point {
    x
    y
}
let p = Point { x: 1, y: 2 }
let daftar = [3, 1, 2]
let terurut = sort(daftar)
print faktorial(5)
print p.x + p.y
print terurut
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("faktorial tetap benar", lines[0] == "120")
    check("custom type tetap benar", lines[1] == "3")
    check("sort tetap benar", lines[2] == "[1, 2, 3]")


def main():
    import tempfile
    tmp_file = tempfile.mktemp(prefix="astralang_v05_test_", suffix=".txt")

    print("=" * 60)
    print("MENJALANKAN TEST: WEB SERVER, AUTOMATION, DEV TOOLS (v0.5)")
    print("=" * 60)

    test_for_loop_list()
    test_for_loop_string()
    test_for_loop_custom_type()
    test_for_loop_variable_scope()
    test_for_loop_invalid_iterable()

    test_html_block_expression()
    test_html_variable_name_still_works()
    test_html_block_invalid_field()

    test_route_registration_and_lookup()
    test_route_rejects_invalid_path()
    test_http_server_real_requests()
    test_http_server_requires_routes()

    test_map_basic_operations()
    test_map_get_missing_key_error()
    test_map_keys()

    test_json_stringify_and_parse_roundtrip()
    test_json_stringify_custom_type()
    test_json_parse_invalid_string()
    test_json_produces_valid_json_syntax()

    test_file_read_write_alias(tmp_file)

    test_string_functions_basic()
    test_string_split()
    test_string_split_used_with_for_loop()
    test_string_replace()
    test_string_starts_ends_with()
    test_string_function_rejects_non_string()
    test_split_rejects_empty_separator()

    test_timer_after_blocking_delay()
    test_timer_after_rejects_function_with_params()

    test_full_regression_v0_1_to_v0_4()

    if os.path.isfile(tmp_file):
        os.remove(tmp_file)

    print("=" * 60)
    print(f"HASIL: {PASSED} lulus, {FAILED} gagal")
    print("=" * 60)
    return 1 if FAILED > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
