# AstraLang

**AstraLang** adalah bahasa pemrograman baru yang sedang dikembangkan dengan visi:

- 🐍 Sintaks sederhana, mudah dipelajari pemula (terinspirasi Python)
- ⚡ Performa tinggi di masa depan (terinspirasi C++ dan Go)
- 🛡️ Keamanan memory di masa depan (terinspirasi Rust)
- 📟 Ringan untuk perangkat IoT
- 🤖 Dukungan AI/Machine Learning sebagai fitur masa depan
- 🌍 Berkembang menjadi bahasa pemrograman internasional

> **Status saat ini: v0.5.0 — Web Server, Automation, Developer Tools & Performance**
> AstraLang adalah tree-walking interpreter yang ditulis murni dengan Python
> (tanpa dependency eksternal). v0.5.0 menambahkan **`for` loop**, **HTTP
> server multi-route** (`route`/`HTTP_SERVER_START`), **blok `html { }`**,
> **Map & JSON**, **file module** (`file_read`/`file_write`), **string
> functions** (`upper`/`lower`/`split`/dst), **`timer_after`** (blocking),
> **mode `--debug`**, **package manager lokal** (`astra_pkg.py`), dan
> **optimisasi dispatch interpreter** (menghilangkan `getattr` berulang dari
> hot path eksekusi). Lihat `CHANGELOG.md` untuk riwayat lengkap termasuk
> keputusan pencabutan fitur "Astra Device Bridge" dan batasan jujur soal
> APK (belum bisa dibuat dari lingkungan pengembangan ini).

---

## Ekstensi File

Semua kode AstraLang menggunakan ekstensi **`.as`**

Contoh: `main.as`

---

## Struktur Project

```
AstraLang/
│
├── compiler.py       # Entry point CLI: menjalankan file .as
├── build_exe.py       # script build jadi executable (.exe)
├── astra_pkg.py        # (BARU v0.5) package manager lokal (install/remove/list)
├── lexer.py             # Tahap 1: source code -> token
├── parser.py            # Tahap 2: token -> AST (Abstract Syntax Tree)
├── interpreter.py       # Tahap 3: menjalankan AST
├── runtime.py             # Environment, error handling, List, Type, Map
├── i18n.py                 # sistem terjemahan pesan error ID/EN
│
├── examples/
│   ├── hello.as
│   ├── advanced.as
│   ├── list_demo.as             # contoh Type System: List, indexing, null
│   ├── custom_type_demo.as      # contoh Custom Type
│   ├── web_demo.as              # contoh generate file HTML
│   ├── pemula_demo.as           # contoh let opsional, input, randint
│   ├── game_bgk.as              # game terminal: batu gunting kertas
│   ├── web_game.as              # game web interaktif (HTML+JS via serve_html)
│   ├── leaderboard_demo.as      # generate halaman leaderboard statis
│   ├── for_loop_demo.as         # (BARU v0.5) contoh for-loop
│   └── route_server_demo.as     # (BARU v0.5) HTTP server multi-route
│
├── tests/
│   ├── test_v0_1_regression.py       # test fitur inti bahasa (wajib selalu lulus)
│   ├── test_v0_3_features.py         # test List & Error System (v0.3)
│   ├── test_v0_3_custom_type.py      # test Custom Type (v0.3)
│   ├── test_v0_4_web.py               # test File I/O & web server (v0.4)
│   ├── test_v0_4_beginner_friendly.py  # test let opsional, i18n, built-in pemula
│   ├── test_v0_4_list_ops.py           # test sort, sort_by, contains, join, slice
│   ├── test_v0_5_features.py           # (BARU) test for-loop, route, HTTP server, Map, JSON, timer
│   └── run_all.py                      # runner semua test
│
├── README.md
├── BUILD.md             # panduan build .exe
└── CHANGELOG.md
```

### Arsitektur

```
file.as
   │
   ▼
[ lexer.py ]   -> mengubah teks menjadi Token (NUMBER, STRING, IDENT, IF, ...)
   │
   ▼
[ parser.py ]  -> mengubah Token menjadi AST (Program, IfStatement, BinaryExpr, ...)
   │
   ▼
[interpreter.py] -> berjalan di atas AST, mengeksekusi statement demi statement
   │
   ▼
[ runtime.py ]  -> menyediakan Environment (variable scope), Function, error class
```

Pendekatan ini disebut **tree-walking interpreter**: source dijalankan langsung
dari AST tanpa dikompilasi ke bytecode/native code terlebih dahulu. Ini dipilih
karena mudah dikembangkan dan di-debug. Versi lebih cepat (compile ke bytecode
atau native) direncanakan di roadmap v0.4+.

---

## Instalasi di Termux (Android)

1. Install Termux dari F-Droid (disarankan) atau Play Store.
2. Update paket dan install Python:

```bash
pkg update && pkg upgrade -y
pkg install python -y
```

3. Verifikasi Python terpasang:

```bash
python3 --version
```

4. Salin/clone folder project `AstraLang/` ke perangkat, misalnya via `git clone`
   (jika sudah di-push ke repository) atau dengan menyalin file secara manual:

```bash
# Jika menggunakan git
pkg install git -y
git clone https://github.con/JANUARPROGRAM/AstraLang
cd AstraLang
```

5. Tidak ada dependency eksternal (hanya Python standard library), jadi tidak
   perlu `pip install` apa pun.

---

## Cara Menjalankan File `.as`

```bash
python3 compiler.py examples/hello.as
```

Menampilkan bantuan:

```bash
python3 compiler.py --help
```

Menampilkan versi:

```bash
python3 compiler.py --version
```

### (Opsional) Membuat alias `astra` di Termux

Agar bisa menjalankan seperti `astra main.as`, tambahkan alias ini ke `~/.bashrc`:

```bash
echo 'alias astra="python3 $HOME/AstraLang/compiler.py"' >> ~/.bashrc
source ~/.bashrc
```

Lalu jalankan:

```bash
astra examples/hello.as
```

---

## Contoh Program AstraLang

### 1. Hello World

```
print "Hello World"
```

### 2. Variabel

```
let nama = "Astra"
let angka = 10
print nama
print angka
```

### 3. Kondisi (if / else)

```
let angka = 10
if angka > 5 {
    print "besar"
} else {
    print "kecil"
}
```

### 4. Loop (while)

```
let i = 1
while i <= 5 {
    print i
    i = i + 1
}
```

### 5. Fungsi

```
function halo(nama) {
    print "Halo, " + nama
}

halo("Dunia")
```

### 6. Fungsi Rekursif

```
function faktorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * faktorial(n - 1)
    }
}

print faktorial(5)   # hasil: 120
```

Lihat `examples/hello.as` dan `examples/advanced.as` untuk contoh lebih lengkap.

---

## Type System: List (Baru di v0.3)

### 7. Membuat & Mengakses List

```
let angka = [10, 20, 30]
print angka          # [10, 20, 30]
print angka[0]        # 10
angka[1] = 99          # ubah elemen lewat index
print angka           # [10, 99, 30]
```

### 8. List Bersarang (Nested List)

```
let matrix = [[1, 2], [3, 4]]
print matrix[0][1]   # 2
print matrix[1][0]   # 3
```

### 9. Fungsi Bawaan untuk List

Karena AstraLang belum punya syntax method-call (`.push()`), operasi List
memakai fungsi biasa untuk saat ini:

```
let a = [1, 2]
push(a, 3)          # a menjadi [1, 2, 3]
let x = pop(a)       # x = 3, a menjadi [1, 2]
print get(a, 0)      # 1 (setara a[0])
print len(a)          # panjang list
```

### 10. Nilai `null`

```
let kosong = null
if kosong == null {
    print "belum diisi"
}
```

Lihat `examples/list_demo.as` untuk contoh lengkap.

### Operasi List Tambahan (Baru di v0.4)

| Function | Kegunaan |
|---|---|
| `sort(daftar)` | Urutkan angka/string menaik, hasil List baru (tidak mengubah aslinya) |
| `sort_by(daftar, fungsi_kunci)` | Urutkan List berisi custom type berdasarkan sebuah field |
| `reverse(daftar)` | Balik urutan, hasil List baru |
| `contains(daftar, nilai)` | `true`/`false` apakah nilai ada di dalam List |
| `join(daftar, pemisah)` | Gabungkan isi List jadi satu string |
| `slice(daftar, mulai, akhir)` | Ambil sebagian List (mirip Python) |

```
type Pemain {
    nama
    skor
}
function ambil_skor(p) {
    return p.skor
}

let daftar = [Pemain { nama: "A", skor: 50 }, Pemain { nama: "B", skor: 90 }]
let terurut = sort_by(daftar, ambil_skor)   # urut naik berdasarkan skor
let terbalik = reverse(terurut)              # urut turun (tertinggi dulu)
```

---

## Custom Type (Baru di v0.3)

### 11. Deklarasi Type

```
type Point {
    x
    y
}
```

Nama type **harus diawali huruf besar** (mis. `Point`, `Player`, `Item`) —
ini membedakan `Nama { ... }` sebagai instance literal dari blok kode biasa
seperti `if kondisi { ... }`.

### 12. Membuat & Menggunakan Instance

```
let p = Point { x: 10, y: 20 }
print p           # Point {x: 10, y: 20}
print p.x         # 10
p.y = 99          # ubah field
print p           # Point {x: 10, y: 99}
```

Semua field wajib diisi saat membuat instance; field yang tidak dikenal atau
field yang belum diisi akan ditolak dengan error yang jelas.

### 13. Kombinasi dengan List

```
type Item {
    nama
    harga
}

let keranjang = [
    Item { nama: "Buku", harga: 50000 },
    Item { nama: "Pensil", harga: 5000 }
]

let total = 0
let i = 0
while i < len(keranjang) {
    total = total + keranjang[i].harga
    i = i + 1
}
print total   # 55000
```

Field sebuah instance juga boleh berisi List, dan sebaliknya — List boleh
berisi banyak instance, seperti contoh di atas.

Lihat `examples/custom_type_demo.as` untuk contoh lengkap.

---

## Web & File I/O (Baru di v0.4)

### 14. Menulis & Membaca File

```
write_file("catatan.txt", "isi filenya")
let isi = read_file("catatan.txt")
print isi
```

`write_file()` menerima nilai apa pun sebagai isi (bukan cuma string) — nilai
non-string otomatis dikonversi lewat aturan yang sama seperti `print`.

### 15. Membuat File HTML (Generate Website)

Karena AstraLang belum punya templating HTML khusus, HTML disusun sebagai
string biasa (bisa digabung multi-baris dengan `+` di akhir baris), lalu
ditulis ke file:

```
let daftar = ["List", "Custom Type", "Web server"]
let item_html = ""
let i = 0
while i < len(daftar) {
    item_html = item_html + "<li>" + daftar[i] + "</li>"
    i = i + 1
}

let html = "<html><body>" +
    "<h1>Fitur AstraLang</h1>" +
    "<ul>" + item_html + "</ul>" +
    "</body></html>"

write_file("index.html", html)
```

> **Catatan path:** `write_file`/`read_file` memakai path **relatif terhadap
> folder tempat perintah `python3 compiler.py` dijalankan** (working
> directory), bukan relatif terhadap lokasi file `.as` itu sendiri. Gunakan
> path absolut kalau perlu kepastian lokasi file.

Lihat `examples/web_demo.as` untuk contoh lengkap.

### 16. Web Server Bawaan

AstraLang bisa langsung menjalankan web server dari kode `.as`, tanpa
dependency eksternal (memakai `http.server` bawaan Python):

```
let html = "<html><body><h1>Halo dari AstraLang!</h1></body></html>"
serve_html(html, 8080)
```

Setelah dijalankan, buka `http://localhost:8080/` di browser. Server ini
melayani **satu halaman HTML statis** untuk semua request `GET` — cocok
untuk demo atau halaman status sederhana. Tekan `Ctrl+C` untuk menghentikan.

---

## Membuat Game dengan AstraLang

Ada tiga cara membuat game dengan AstraLang, tergantung kebutuhan:

### A. Game Terminal (Teks)

Cocok untuk game berbasis giliran seperti tebak angka atau batu-gunting-kertas.
Memakai `input()`, custom type untuk skor, dan List untuk aturan/pilihan:

```
type Skor {
    menang
    kalah
}
let skor = Skor { menang: 0, kalah: 0 }
```

Lihat `examples/game_bgk.as` (Batu Gunting Kertas) — mendemonstrasikan
custom type, List sebagai daftar pilihan valid, validasi input, dan loop
permainan sampai pemain memilih keluar.

### B. Game Web Interaktif (Klik/Keyboard di Browser)

AstraLang **menyusun** halaman HTML + CSS + JavaScript sebagai satu string,
lalu menyajikannya lewat `serve_html()`. Logika interaksi (klik, cek jawaban,
skor real-time) berjalan di JavaScript pada sisi browser — AstraLang berperan
menyusun dan menyajikan halamannya:

```
let html = "<html><body>...<script>...</script></body></html>"
write_file("game.html", html)     # opsional, untuk pratinjau file
serve_html(html, 8080)             # sajikan sebagai web game
```

Lihat `examples/web_game.as` — game tebak angka interaktif lengkap dengan
tombol, input, dan pengecekan jawaban langsung di browser tanpa reload
halaman.

> **Batasan yang perlu diketahui:** `serve_html()` melayani halaman statis
> yang sama untuk semua request — AstraLang tidak (belum) punya cara
> menerima data balik dari browser ke server (mis. menyimpan skor tertinggi
> di server). Untuk game seperti ini, seluruh logic game harus berjalan di
> JavaScript pada sisi browser, seperti pada contoh.

### C. Generate Halaman Hasil/Laporan (Statis)

AstraLang murni menyusun halaman HTML dari data — cocok untuk leaderboard,
ringkasan skor, atau laporan hasil game, tanpa JavaScript sama sekali:

```
type Pemain {
    nama
    skor
}
function ambil_skor(p) {
    return p.skor
}
let terurut = reverse(sort_by(daftar_pemain, ambil_skor))
```

Lihat `examples/leaderboard_demo.as` — mengurutkan List berisi custom type
`Pemain` berdasarkan field `skor` memakai `sort_by()`, lalu menyusun tabel
HTML dari hasilnya.

---

## Membuat Executable (.exe)

AstraLang bisa dikemas jadi satu file executable yang bisa dijalankan tanpa
install Python, memakai `build_exe.py`:

```bash
pip install pyinstaller
python3 build_exe.py
```

Hasilnya ada di `dist/AstraLang` (Linux/Mac) atau `dist/AstraLang.exe`
(Windows). Lihat `BUILD.md` untuk panduan lengkap dan batasannya (build
harus dilakukan di platform target — tidak bisa cross-compile dari
Linux/Termux ke `.exe` Windows).

---

## Web Server, Automation & Developer Tools (Baru di v0.5)

### 20. `for` Loop

```
for item in [10, 20, 30] {
    print item
}
for huruf in "Astra" {
    print huruf
}
```

Bekerja untuk List maupun string (iterasi karakter). Variabel loop hanya
hidup di dalam blok `{ }`, tidak bocor ke luar.

### 21. HTTP Server Multi-Route

```
route "/" {
    return "Hello AstraLang"
}
route "/tentang" {
    return "Halaman tentang"
}
HTTP_SERVER_START(8080)
```

Beda dari `serve_html()` (v0.4, satu halaman statis), `HTTP_SERVER_START()`
mendukung banyak `route` sekaligus. Path yang tidak terdaftar otomatis
menjawab `404`. Path harus diawali `/`.

### 22. Blok `html { }`

Gula sintaks untuk menyusun HTML sederhana tanpa menulis tag manual:

```
route "/tentang" {
    return html {
        title "Tentang"
        heading "Tentang Kami"
        text "Dibuat dengan AstraLang"
    }
}
```

> **Catatan kompatibilitas:** `html` BUKAN keyword reserved — ini sengaja
> supaya `let html = "..."` (dipakai di beberapa contoh v0.4) tetap sah.
> `html { ... }` hanya dikenali sebagai blok HTML kalau langsung diikuti
> `{`; di konteks lain `html` tetap nama variabel biasa.

### 23. Map (Dictionary) & JSON

```
let m = map_new()
map_set(m, "nama", "Astra")
map_set(m, "skor", [10, 20, 30])
print map_get(m, "nama")
print map_has(m, "nama")
print map_keys(m)

let teks = json_stringify(m)   # -> JSON string valid
let parsed = json_parse(teks)  # -> Map lagi
```

`json_stringify()` juga bisa dipakai langsung pada custom type dan List.

### 24. File Module & String Functions

```
file_write("catatan.txt", "isi")
print file_read("catatan.txt")

print upper("halo")           # HALO
print lower("HALO")           # halo
print trim("  spasi  ")        # spasi
print split("a,b,c", ",")      # [a, b, c]
print replace("halo dunia", "dunia", "AstraLang")
print starts_with("AstraLang", "Astra")   # true
print ends_with("AstraLang", "Lang")      # true
```

`file_read`/`file_write` adalah alias dari `read_file`/`write_file` (v0.4).

### 25. Timer

```
function selesai() {
    print "Done"
}
timer_after(1000, selesai)
```

> **Batasan yang perlu diketahui:** `timer_after()` bersifat **blocking**
> (program berhenti sejenak selama durasi timer, baru menjalankan
> callback). AstraLang belum punya event loop/concurrency sungguhan, jadi
> timer TIDAK berjalan "di latar belakang" sambil kode lain tetap jalan.

### 26. Mode Debug

```bash
python3 compiler.py program.as --debug
```

Menampilkan waktu eksekusi tiap tahap (lexer/parser/interpreter) saat
program berhasil jalan, dan traceback Python asli di bawah pesan error
normal saat terjadi error — untuk membantu development AstraLang sendiri.

### 27. Package Manager Lokal

```bash
python3 astra_pkg.py install <folder_atau_file.zip> [--name nama]
python3 astra_pkg.py list
python3 astra_pkg.py remove <nama>
```

> **Batasan yang perlu diketahui:** ini package manager **lokal** (install
> dari folder/zip di komputer sendiri) — tidak ada registry online seperti
> npm/PyPI. AstraLang juga belum punya sistem `import` otomatis; untuk
> memakai isi package yang terinstal, panggil `read_file()` secara manual
> ke path di dalam `astra_packages/`.

---

## Lebih Mudah dari Python (Baru di v0.4)

### 17. Variabel Tanpa `let` (Opsional)

`let` sekarang **opsional** untuk variabel baru — kalau belum pernah
dideklarasikan, assignment langsung membuatnya:

```
nama = "Budi"
umur = 20
print nama
```

`let` tetap bisa dipakai kapan saja (dan tetap wajib kalau ingin
mendeklarasikan variabel baru **di dalam** function yang namanya sama
dengan variabel di luar, supaya tidak tertukar). Assignment ke variabel
yang sudah ada di scope luar (misalnya di dalam function yang mengubah
variabel luar) **tetap bekerja seperti biasa**, tidak berubah:

```
let total = 0
function tambah() {
    total = total + 1   # ini tetap mengubah 'total' di luar, bukan bikin baru
}
tambah()
tambah()
print total   # 2
```

### 18. Pesan Error Dwibahasa (Indonesia / Inggris)

Semua pesan error bisa ditampilkan dalam Bahasa Inggris lewat opsi
`--lang en`:

```bash
python3 compiler.py program.as --lang en
```

```
An error occurred while running the program (Runtime Error):
  Can't divide by zero
  Location: program.as:3
  Suggestion: First check whether the divisor is zero before dividing
```

Tanpa opsi ini, pesan tetap Bahasa Indonesia (default).

### 19. Built-in Function Siap Pakai untuk Pemula

| Function | Kegunaan |
|---|---|
| `input(prompt)` | Membaca input dari pengguna |
| `random()` | Angka acak 0.0 sampai 1.0 |
| `randint(min, maks)` | Angka bulat acak antara min dan maks (inklusif) |
| `round(angka)` / `round(angka, n)` | Pembulatan |
| `int(nilai)` | Konversi ke integer |
| `float(nilai)` | Konversi ke float |

Contoh — program tebak angka dalam beberapa baris:

```
jawaban = randint(1, 10)
tebakan = 0
while tebakan != jawaban {
    tebakan = int(input("Tebak angkanya: "))
}
print "Benar!"
```

Lihat `examples/pemula_demo.as` untuk contoh lengkap.

---

## Fitur Bahasa

| Fitur                     | Status | Keterangan                                  |
|----------------------------|:------:|----------------------------------------------|
| `print`                    | ✅     | Mencetak nilai ke layar                       |
| `let` (deklarasi variabel) | ✅     | Deklarasi variabel baru                       |
| Assignment (`x = ...`)     | ✅     | Mengubah nilai variabel yang sudah ada         |
| Tipe data: integer          | ✅     | Bilangan bulat                                |
| Tipe data: float            | ✅     | Bilangan desimal                              |
| Tipe data: string            | ✅     | Diapit tanda kutip ganda `"..."`             |
| Tipe data: boolean          | ✅     | `true` / `false`                              |
| Tipe data: null              | ✅ **(v0.3)** | Literal `null`, bisa dibandingkan dengan `==` |
| Tipe data: List              | ✅ **(v0.3)** | Literal `[1,2,3]`, indexing, index assignment, nested list |
| Operasi matematika          | ✅     | `+ - * / %`                                   |
| Operasi perbandingan         | ✅     | `== != < > <= >=`                             |
| Operasi logika               | ✅     | `and or not`                                  |
| `if / else`                 | ✅     | Termasuk `else if` berantai                   |
| `while`                     | ✅     | Loop dengan batas pengaman anti infinite loop |
| `function`                  | ✅     | Deklarasi & pemanggilan fungsi, `return`      |
| Rekursi                     | ✅     | Fungsi bisa memanggil dirinya sendiri          |
| Komentar (`#`)              | ✅     | Komentar satu baris                           |
| Built-in `len()`            | ✅     | String & List                                 |
| Built-in `push/pop/get`      | ✅ **(v0.3)** | Operasi dasar List                           |
| Error dengan hint            | ✅ **(v0.3)** | Lokasi + penyebab + saran perbaikan          |
| Custom type sederhana        | ✅ **(v0.3)** | `type Nama { field }`, instance, field access & assignment |
| File I/O (`write_file`/`read_file`) | ✅ **(v0.4)** | Baca/tulis file apa pun termasuk HTML |
| Web server bawaan (`serve_html`) | ✅ **(v0.4)** | HTTP server 1 halaman, stdlib saja, teruji dengan request nyata |
| Build ke executable (`.exe`) | ✅ **(v0.4)** | Lewat `build_exe.py` + PyInstaller (build manual, butuh internet) |
| APK (Android)                | ❌     | Belum bisa dibuat dari lingkungan pengembangan ini            |
| Variabel tanpa `let`          | ✅ **(v0.4)** | Auto-declare, tanpa merusak closure/scope         |
| Pesan error dwibahasa (ID/EN) | ✅ **(v0.4)** | Opsi `--lang en`                                   |
| Built-in pemula (`input`, `random`, dst) | ✅ **(v0.4)** | Lihat tabel di section "Lebih Mudah dari Python" |
| Operasi List lanjutan (`sort`, `sort_by`, dst) | ✅ **(v0.4)** | Lihat tabel di section Type System: List |
| Contoh game (terminal, web, leaderboard) | ✅ **(v0.4)** | Lihat section "Membuat Game dengan AstraLang" |
| `for` loop                   | ✅ **(v0.5)** | `for item in daftar { }`, List & string          |
| HTTP server multi-route (`route`, `HTTP_SERVER_START`) | ✅ **(v0.5)** | 404 otomatis untuk path tak terdaftar |
| Blok `html { }`               | ✅ **(v0.5)** | `title`/`heading`/`text`, `html` tetap bisa jadi nama variabel |
| Map & JSON                    | ✅ **(v0.5)** | `map_new/get/set/has/keys`, `json_stringify/parse` |
| File module (`file_read/write`) | ✅ **(v0.5)** | Alias dari `read_file`/`write_file`             |
| String functions              | ✅ **(v0.5)** | `upper/lower/trim/split/replace/starts_with/ends_with` |
| Timer (`timer_after`)          | ✅ **(v0.5)** | Blocking, bukan async — lihat batasan di dokumentasi |
| Mode debug (`--debug`)          | ✅ **(v0.5)** | Waktu eksekusi + traceback Python                |
| Package manager lokal (`astra_pkg.py`) | ✅ **(v0.5)** | Install dari folder/zip lokal, bukan registry online |
| Module/import               | ❌     | Direncanakan roadmap lanjutan (package manager belum terintegrasi otomatis) |
| Standard library              | ❌     | Direncanakan roadmap lanjutan                 |
| Memory safety (ala Rust)     | ❌     | Direncanakan roadmap lanjutan                 |
| AI/ML module                 | ❌     | Direncanakan roadmap lanjutan                 |

---

## Pesan Error

AstraLang memiliki 3 lapis error handling yang jelas:

1. **Lexer Error** — karakter tidak dikenal, string tidak ditutup, dll.
2. **Parser Error** — struktur kode salah (kurung tidak ditutup, statement tidak valid, dll.)
3. **Runtime Error** — error saat program dijalankan (variabel tidak ada, pembagian dengan nol, tipe data tidak cocok, index di luar jangkauan, dll.)

Setiap error menyertakan **lokasi baris (dan kolom bila relevan)**, dan sejak
v0.3 sebagian besar juga menyertakan **saran perbaikan (hint)** — bukan cuma
memberi tahu apa yang salah, tapi juga bagaimana cara memperbaikinya.

Contoh:

```
Terjadi error saat program berjalan (Runtime Error):
  Index 10 di luar jangkauan (list berisi 3 elemen)
  Lokasi: examples/list_demo.as:5
  Saran: Index yang valid untuk list ini adalah 0 sampai 2
```

```
Terjadi error saat program berjalan (Runtime Error):
  Variabel 'xxx' tidak ditemukan
  Lokasi: examples/hello.as:3
  Saran: Deklarasikan dulu dengan 'let xxx = ...' sebelum dipakai, atau cek kemungkinan salah ketik nama variabel
```

---

## Roadmap Pengembangan

| Versi | Fokus                                             |
|-------|----------------------------------------------------|
| v0.1  | Prototype dasar (lexer, parser, interpreter) ✅ |
| ~~v0.2.1~~ | ~~Astra Device Bridge~~ — **dicabut**, lihat `CHANGELOG.md` |
| v0.3  | Type System (List ✅, custom type ✅) + Error System lebih detail ✅ **(selesai)** |
| v0.4.0 | Web (file I/O ✅, web server ✅), Build .exe ✅, lebih mudah dari Python ✅ **(selesai)** |
| v0.4.1 | Operasi List lanjutan ✅, contoh game (terminal/web/leaderboard) ✅ **(selesai)** |
| v0.5.0 | HTTP server multi-route ✅, Map/JSON ✅, timer ✅, `--debug` ✅, package manager lokal ✅, optimisasi dispatch ✅ **(selesai)** |
| v0.6  | Module system (`import` sungguhan), standard library, Serial Hardware ⏳ **(berikutnya)** |
| v0.7  | Compiler/eksekusi lebih cepat (bytecode)             |
| v0.8  | Dukungan IoT, ARM support                           |
| v0.9  | Sistem memory safety                                |
| v0.10 | Modul AI/Machine Learning                            |
| v1.0  | Release publik                                       |

Lihat `CHANGELOG.md` untuk rincian setiap perubahan per versi, termasuk fitur
yang pernah ditambahkan lalu dicabut.

---

## Menjalankan Test

```bash
python3 tests/run_all.py
```

Atau jalankan satu per satu:

```bash
python3 tests/test_v0_1_regression.py   # test fitur inti bahasa (wajib selalu lulus)
python3 tests/test_v0_3_features.py     # test List & Error System (v0.3)
python3 tests/test_v0_3_custom_type.py  # test Custom Type (v0.3)
python3 tests/test_v0_4_web.py           # test File I/O & web server (v0.4)
python3 tests/test_v0_4_beginner_friendly.py  # test let opsional, i18n, built-in pemula (v0.4)
python3 tests/test_v0_4_list_ops.py       # test sort, sort_by, contains, join, slice (v0.4)
python3 tests/test_v0_5_features.py       # test for-loop, HTTP server, Map, JSON, timer, string functions (v0.5)
```

Test regresi **wajib tetap lulus 100%** di setiap versi berikutnya — jika ada
yang gagal, berarti sebuah fitur lama rusak dan harus diperbaiki sebelum lanjut.

---

## Kontribusi

AstraLang dirancang sebagai proyek open source. Prinsip pengembangan yang dipegang:

- Setiap kode yang ditambahkan harus benar-benar bisa dijalankan (tidak ada kode palsu/placeholder tanpa implementasi).
- Fitur lama tidak dihapus saat memperbaiki bug, kecuali memang direncanakan sebagai breaking change dan didokumentasikan dengan jelas (lihat `CHANGELOG.md`).
- Setiap perubahan memakai versioning yang jelas (lihat Roadmap di atas).

---

## Lisensi

Belum ditentukan (rencana: lisensi open source seperti MIT/Apache-2.0 sebelum rilis v1.0 publik).
