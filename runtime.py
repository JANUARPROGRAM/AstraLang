"""
AstraLang Runtime (v0.1, diperluas di v0.3)
==============================================
Berisi komponen-komponen yang dipakai saat program AstraLang benar-benar
dieksekusi:
- Environment: manajemen variable & scope (mendukung nested scope untuk
  function call, if-block, while-block).
- RuntimeError khusus AstraLang (AstraRuntimeError) supaya error dari
  program pengguna bisa dibedakan dari bug internal interpreter. v0.3
  menambahkan field `hint` opsional untuk saran perbaikan konkret.
- Representasi nilai fungsi (AstraFunction) dan sinyal kontrol alur
  (ReturnSignal) yang dipakai interpreter untuk implementasi 'return'.
- v0.3: AstraList, wrapper tipis di atas Python list untuk tipe data List.
"""


class AstraRuntimeError(Exception):
    """
    Error yang terjadi saat eksekusi program AstraLang (bukan bug internal).

    v0.3: menambahkan field `hint` opsional berisi saran perbaikan konkret,
    supaya pesan error tidak cuma menyatakan apa yang salah, tapi juga
    mengarahkan bagaimana cara memperbaikinya.
    """

    def __init__(self, message, line=None, hint=None):
        self.message = message
        self.line = line
        self.hint = hint
        if line is not None:
            text = f"[Runtime Error] Baris {line}: {message}"
        else:
            text = f"[Runtime Error] {message}"
        if hint:
            text += f"\n  Saran: {hint}"
        super().__init__(text)


class ReturnSignal(Exception):
    """Dipakai secara internal untuk 'melompat' keluar dari body fungsi saat 'return'."""

    def __init__(self, value):
        self.value = value


class Environment:
    """
    Menyimpan variable dalam satu scope, dengan pointer ke parent scope
    untuk mendukung lexical scoping (mis. variable global terlihat dari
    dalam function, tapi variable lokal function tidak bocor keluar).
    """

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        """Mendefinisikan variable baru di scope SAAT INI (dipakai oleh 'let')."""
        self.vars[name] = value

    def get(self, name, line=None):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise AstraRuntimeError(
            f"Variabel '{name}' tidak ditemukan",
            line,
            hint=f"Deklarasikan dulu dengan 'let {name} = ...' sebelum dipakai, atau cek kemungkinan salah ketik nama variabel",
        )

    def set(self, name, value, line=None, auto_declare=True):
        """
        Mengubah nilai variable yang SUDAH ADA (assignment tanpa 'let'
        sebelumnya, atau assignment setelah 'let').

        v0.4: kalau variabel belum ada di scope manapun (rantai parent),
        dan auto_declare=True, variabel baru otomatis DIDEKLARASIKAN di
        scope SAAT INI (bukan scope terluar/global) -- ini membuat 'let'
        jadi opsional untuk assignment sederhana (mis. `nama = "Budi"`
        langsung jalan seperti Python), sambil tetap menjaga perilaku
        assignment ke variabel yang SUDAH ada di scope luar (mis. closure
        di dalam function yang mengubah variabel scope luar) tidak berubah
        sama sekali -- itu tetap mengubah variabel yang sudah ada, bukan
        membuat variabel lokal baru.
        """
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        if auto_declare:
            self.vars[name] = value
            return
        raise AstraRuntimeError(
            f"Tidak bisa assign ke variabel '{name}' yang belum dideklarasikan",
            line,
            hint=f"Gunakan 'let {name} = ...' untuk mendeklarasikan variabel baru sebelum diberi nilai",
        )


class AstraFunction:
    """Representasi runtime dari fungsi yang dideklarasikan dengan 'function'."""

    def __init__(self, declaration, closure_env):
        self.declaration = declaration  # FunctionDecl node
        self.closure_env = closure_env  # Environment saat fungsi didefinisikan

    @property
    def name(self):
        return self.declaration.name

    @property
    def arity(self):
        return len(self.declaration.params)

    def __repr__(self):
        return f"<function {self.name}>"


class AstraBuiltinFunction:
    """Wrapper untuk fungsi bawaan (built-in) yang diimplementasikan di Python."""

    def __init__(self, name, arity, py_func):
        self.name = name
        self.arity = arity  # -1 berarti argumen bebas
        self.py_func = py_func

    def __repr__(self):
        return f"<builtin function {self.name}>"


# -- Ditambahkan v0.3: Type System (List) ---------------------------------
def _runtime_type_name(value):
    """
    Helper penamaan tipe level-runtime, dipakai oleh AstraList supaya pesan
    errornya konsisten dengan Interpreter._type_name tanpa perlu circular
    import (runtime.py tidak boleh mengimpor interpreter.py).
    """
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
    if isinstance(value, AstraInstance):
        return value.type_def.name
    if isinstance(value, AstraMap):
        return "map"
    return type(value).__name__


class AstraList:
    """
    Representasi runtime tipe data List di AstraLang. Wrapper tipis di atas
    Python list (bukan langsung memakai `list` Python mentah) supaya:
    - Interpreter bisa membedakan "List AstraLang" dari list Python internal
      secara eksplisit lewat isinstance(), tanpa ambigu dengan struktur data
      internal lain yang mungkin ditambahkan nanti.
    - Mutasi (push/pop/set index) terjadi in-place dan konsisten dengan
      semantik pass-by-reference untuk List (sama seperti kebanyakan bahasa
      modern: menetapkan List ke variabel lain berbagi referensi yang sama).
    """

    def __init__(self, items=None):
        self.items = list(items) if items is not None else []

    def get(self, index, line=None):
        if not isinstance(index, int) or isinstance(index, bool):
            raise AstraRuntimeError(
                f"Index list harus berupa integer, dapat '{_runtime_type_name(index)}'",
                line,
                hint="Gunakan angka bulat untuk index, mis. daftar[0], bukan daftar[\"0\"]",
            )
        if index < 0 or index >= len(self.items):
            raise AstraRuntimeError(
                f"Index {index} di luar jangkauan (list berisi {len(self.items)} elemen)",
                line,
                hint=f"Index yang valid untuk list ini adalah 0 sampai {len(self.items) - 1}" if self.items else "List ini masih kosong, tidak ada index yang valid",
            )
        return self.items[index]

    def set(self, index, value, line=None):
        if not isinstance(index, int) or isinstance(index, bool):
            raise AstraRuntimeError(
                f"Index list harus berupa integer, dapat '{_runtime_type_name(index)}'",
                line,
                hint="Gunakan angka bulat untuk index, mis. daftar[0] = nilai",
            )
        if index < 0 or index >= len(self.items):
            raise AstraRuntimeError(
                f"Index {index} di luar jangkauan (list berisi {len(self.items)} elemen)",
                line,
                hint=f"Index yang valid untuk list ini adalah 0 sampai {len(self.items) - 1}" if self.items else "List ini masih kosong, tidak ada index yang valid",
            )
        self.items[index] = value

    def push(self, value):
        self.items.append(value)

    def pop(self, line=None):
        if not self.items:
            raise AstraRuntimeError(
                "Tidak bisa pop() dari list yang kosong",
                line,
                hint="Cek dulu len(daftar) > 0 sebelum memanggil pop()",
            )
        return self.items.pop()

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        if isinstance(other, AstraList):
            return self.items == other.items
        return NotImplemented

    def __repr__(self):
        return f"AstraList({self.items!r})"


# -- Ditambahkan v0.3 lanjutan: Custom Type --------------------------------
class AstraTypeDef:
    """
    Representasi runtime dari deklarasi 'type Point { x y }'. Ini adalah
    "blueprint"-nya, bukan instance-nya sendiri — dipakai untuk memvalidasi
    field apa saja yang sah dipakai saat membuat instance (mis. Point { x: 10 }).
    """

    def __init__(self, name, fields):
        self.name = name      # mis. 'Point'
        self.fields = fields  # list nama field, mis. ['x', 'y']

    def __repr__(self):
        return f"<type {self.name} {{{', '.join(self.fields)}}}>"


class AstraInstance:
    """
    Representasi runtime dari sebuah instance custom type, mis. hasil dari
    `Point { x: 10, y: 20 }`. Field disimpan di dict biasa (bukan wrapper
    tipis kayak AstraList) karena instance memang sekumpulan
    nama-field -> nilai, mirip Environment tapi tanpa nested scope.
    """

    def __init__(self, type_def: AstraTypeDef, values: dict):
        self.type_def = type_def
        self.values = values  # dict: nama_field -> nilai

    def get_field(self, field_name, line=None):
        if field_name not in self.values:
            raise AstraRuntimeError(
                f"Type '{self.type_def.name}' tidak punya field '{field_name}'",
                line,
                hint=f"Field yang tersedia pada '{self.type_def.name}': {', '.join(self.type_def.fields)}",
            )
        return self.values[field_name]

    def set_field(self, field_name, value, line=None):
        if field_name not in self.type_def.fields:
            raise AstraRuntimeError(
                f"Type '{self.type_def.name}' tidak punya field '{field_name}'",
                line,
                hint=f"Field yang tersedia pada '{self.type_def.name}': {', '.join(self.type_def.fields)}",
            )
        self.values[field_name] = value

    def __eq__(self, other):
        if isinstance(other, AstraInstance):
            return self.type_def is other.type_def and self.values == other.values
        return NotImplemented

    def __repr__(self):
        field_str = ", ".join(f"{k}: {v!r}" for k, v in self.values.items())
        return f"{self.type_def.name} {{{field_str}}}"


# -- Ditambahkan v0.5: Map (dictionary sederhana) --------------------------
class AstraMap:
    """
    Representasi runtime tipe data Map (key-value, mirip dict Python) di
    AstraLang. Ditambahkan terutama sebagai basis representasi JSON object
    (JSON object -> AstraMap, JSON array -> AstraList), tapi juga berguna
    umum sebagai struktur data key-value.

    Diakses lewat built-in function map_get/map_set/map_keys (bukan syntax
    indexing [key]), karena IndexExpr sekarang secara semantik khusus untuk
    integer index pada List/string -- memakainya juga untuk Map akan
    membingungkan (index [0] pada List vs key ["nama"] pada Map terlihat
    sama tapi artinya beda total).
    """

    def __init__(self, items=None):
        self.items = dict(items) if items is not None else {}

    def get(self, key, line=None):
        if key not in self.items:
            raise AstraRuntimeError(
                f"Key '{key}' tidak ditemukan di dalam map",
                line,
                hint="Cek dulu dengan map_has(peta, key) sebelum mengambil nilainya",
            )
        return self.items[key]

    def set(self, key, value):
        self.items[key] = value

    def has(self, key):
        return key in self.items

    def keys(self):
        return list(self.items.keys())

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        if isinstance(other, AstraMap):
            return self.items == other.items
        return NotImplemented

    def __repr__(self):
        return f"AstraMap({self.items!r})"
