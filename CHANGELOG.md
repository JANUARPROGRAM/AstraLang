# Changelog AstraLang

Semua perubahan penting pada project ini didokumentasikan di file ini.
Format mengikuti gaya [Keep a Changelog](https://keepachangelog.com/), dan
project ini memakai skema versi `MAJOR.MINOR.PATCH` selama fase pra-1.0.

---

## [0.5.0] — Web Server, Automation, Developer Tools & Performance

Rilis ini dikerjakan berdasarkan permintaan fitur bertema "Web Server,
Automation, Developer Tools, dan Performance". Nomor versi awalnya diminta
sebagai "v0.2.1", tapi project ini **sudah pernah memiliki v0.2.1**
("Astra Device Bridge", dicabut di v0.3.0) — supaya penomoran versi tetap
runtut dan tidak bentrok dengan sejarah project, rilis ini diberi nomor
v0.5.0 (lanjutan wajar dari v0.4.1) atas persetujuan eksplisit.

### Catatan Pemulihan Project

Sebelum pengerjaan rilis ini dimulai, lingkungan kerja sempat ter-reset
(seluruh file kerja hilang dari filesystem sandbox). Project berhasil
dipulihkan **utuh dari file `AstraLang-v0.4.1.zip`** yang tersimpan di
folder output rilis sebelumnya — bukan ditulis ulang dari ingatan.
Dikonfirmasi 135/135 test v0.4.1 tetap lulus setelah pemulihan, sebelum
pengembangan v0.5.0 dimulai.

### Ditambahkan: `for` Loop

- `for item in daftar { ... }` — iterasi otomatis untuk List dan string
  (iterasi karakter). Variabel loop hanya hidup di dalam blok, tidak bocor
  ke scope luar (diverifikasi dengan test eksplisit).
- Token baru: `FOR`, `IN`. AST node baru: `ForStatement`.
- Diverifikasi untuk List angka, List string, List custom type (dengan
  akumulasi field), dan penolakan iterasi terhadap tipe yang bukan
  List/string dengan pesan error yang jelas.

### Ditambahkan: HTTP Server Multi-Route

- `route "/path" { ... return isi }` — mendaftarkan handler untuk path
  tertentu. Body route dieksekusi seperti body function (menangkap
  `ReturnSignal` untuk mendapatkan konten respons), dengan closure ke
  environment saat `route` dideklarasikan.
- `HTTP_SERVER_START(port)` — menjalankan HTTP server yang me-routing
  request berdasarkan path yang terdaftar. Path yang tidak dikenal otomatis
  dijawab `404`; error di dalam body route dijawab `500` (bukan meng-crash
  seluruh server). Menolak dijalankan kalau belum ada route terdaftar sama
  sekali, dengan pesan yang jelas.
- **Diverifikasi dengan HTTP request sungguhan** (bukan simulasi):
  `GET /`, `GET /tentang` (memakai blok `html { }`), dan `GET /path-tidak-ada`
  (mengonfirmasi kode status 404) semuanya diuji lewat `urllib.request`
  ke server yang benar-benar berjalan di thread terpisah.
- Beda dari `serve_html()` (v0.4): `serve_html()` melayani **satu** halaman
  statis untuk semua request; `HTTP_SERVER_START()` mendukung **banyak**
  route sekaligus.

### Ditambahkan: Blok `html { }`

- `html { title "..." heading "..." text "..." }` — gula sintaks untuk
  menyusun dokumen HTML lengkap (dengan `<!DOCTYPE html>`, `<title>`,
  `<h1>`, `<p>`) tanpa menulis tag manual. Nilai di dalamnya di-escape
  otomatis lewat modul `html` Python (mencegah HTML injection dari data
  yang mengandung karakter khusus).
- **Keputusan desain penting terkait kompatibilitas mundur:** `html`
  **SENGAJA TIDAK dijadikan keyword reserved**. Rencana awal menjadikannya
  keyword reserved **terbukti memecah 3 contoh v0.4 yang sudah ada**
  (`web_demo.as`, `web_game.as`, `leaderboard_demo.as` — semuanya memakai
  `let html = "..."` sebagai nama variabel biasa). Bug ini ditemukan lewat
  pengujian langsung (menjalankan ulang contoh lama), bukan diasumsikan
  aman dari membaca kode. Diperbaiki dengan mendeteksi `html { ... }`
  berdasarkan **posisi** (IDENT bernilai `"html"` di posisi ekspresi primer,
  diikuti `{`, dan `_allow_instance_literal` aktif) — pola yang sama seperti
  heuristik instance-literal custom type di v0.3. Diverifikasi dengan test
  eksplisit bahwa `let html = "..."` tetap sah SEKALIGUS `html { ... }`
  tetap dikenali sebagai blok, tergantung konteks pemakaian.

### Ditambahkan: Map & JSON

- **`AstraMap`** (di `runtime.py`) — tipe data dictionary/key-value
  sederhana. Diakses lewat built-in function (`map_new`, `map_get`,
  `map_set`, `map_has`, `map_keys`), bukan syntax indexing `[key]`, supaya
  tidak ambigu dengan semantik `IndexExpr` yang sudah khusus untuk integer
  index pada List/string.
- **`json_stringify(nilai)`** — mengonversi nilai AstraLang (angka, string,
  boolean, null, List, Map, custom type) menjadi string JSON. Tipe yang
  tidak didukung (function, dll) ditolak dengan pesan jelas alih-alih
  menghasilkan JSON yang salah.
- **`json_parse(teks)`** — mengonversi string JSON menjadi nilai AstraLang
  (object JSON → Map, array JSON → List). JSON yang tidak valid ditolak
  dengan pesan error dan hint contoh format yang benar.
- **Diverifikasi bahwa hasil `json_stringify()` adalah JSON yang benar-benar
  valid** dengan memparse-nya ulang memakai `json.loads()` Python asli
  (bukan hanya format yang "terlihat mirip" JSON), termasuk untuk nilai
  `true`/`null` yang representasi print AstraLang dan JSON berbeda secara
  sengaja dipisahkan (representasi `print` untuk Map TIDAK mengklaim JSON
  valid; `json_stringify()` yang menjamin itu).

### Ditambahkan: File Module & String Functions

- `file_read()`/`file_write()` — alias langsung dari `read_file()`/
  `write_file()` (v0.4), memenuhi permintaan penamaan gaya module tanpa
  duplikasi logic.
- String functions: `upper()`, `lower()`, `trim()`, `split()`, `replace()`,
  `starts_with()`, `ends_with()`. Semua memvalidasi tipe argumen dengan
  pesan error yang jelas. `split()` menolak pemisah kosong.
- **Catatan pemulihan:** fungsi-fungsi string ini sempat dikerjakan di
  sesi sebelum reset lingkungan, tapi belum sempat tersimpan ke zip
  terakhir — ditemukan hilang saat `examples/for_loop_demo.as` gagal
  dengan error "Variabel 'upper' tidak ditemukan" saat pengujian end-to-end,
  lalu dikerjakan ulang dan diverifikasi sebagai bagian resmi v0.5.0.

### Ditambahkan: Timer

- `timer_after(ms, nama_fungsi)` — menjalankan fungsi setelah durasi
  tertentu. Fungsi callback harus tidak menerima parameter.
- **Diverifikasi dengan pengukuran waktu nyata** (bukan asumsi) bahwa
  program benar-benar tertunda sesuai durasi yang diberikan.
- **Batasan yang dicatat jujur:** implementasi bersifat **blocking**
  (`time.sleep()`), bukan asynchronous. AstraLang belum punya event
  loop/concurrency sungguhan, jadi `timer_after()` menghentikan eksekusi
  program selama durasi timer — tidak bisa "berjalan di latar belakang"
  sambil kode lain tetap berjalan. Ini didokumentasikan eksplisit di
  README dan komentar kode, bukan disembunyikan.

### Ditambahkan: Mode Debug (`--debug`)

- `python3 compiler.py program.as --debug` menampilkan:
  - Traceback Python asli di bawah pesan error normal (untuk debugging
    interpreter AstraLang sendiri), di ketiga tahap (lexer/parser/runtime).
  - Waktu eksekusi tiap tahap (lexer, parser, interpreter) dalam
    milidetik saat program berhasil jalan tanpa error.
- Mode debug MENAMBAH informasi, tidak menggantikan pesan error normal
  yang sudah ada (pesan + lokasi + hint tetap tampil seperti biasa).

### Ditambahkan: Package Manager Lokal

- **`astra_pkg.py`** (script terpisah, dijalankan langsung: `python3
  astra_pkg.py ...`) — package manager LOKAL:
  - `install <folder_atau_zip> [--name nama]` — menyalin folder atau
    mengekstrak `.zip` ke `astra_packages/<nama>/`, mencatat metadata di
    `astra_packages.json`.
  - `remove <nama>` — menghapus package terinstal.
  - `list` — menampilkan semua package terinstal beserta sumbernya.
- **Diverifikasi dengan operasi file sungguhan**: install dari folder,
  install dari `.zip` (dengan `--name` kustom), list, remove, dan
  pembuktian bahwa file `.as` hasil instalasi benar-benar bisa dibaca dari
  script AstraLang lewat `read_file()`.
- **Batasan yang dicatat jujur dan disepakati eksplisit sebelum
  dikerjakan:** ini BUKAN package manager online seperti npm/PyPI — tidak
  ada registry server, hosting, atau unduh dari internet. Package harus
  sudah ada sebagai folder/zip lokal. AstraLang juga belum punya sistem
  `import` sungguhan, jadi package manager ini murni mengelola penyimpanan
  & metadata; memakai isi package masih perlu `read_file()` manual.

### Optimisasi Performa (Diukur, Bukan Diklaim)

- **Dispatch table di-cache** untuk `_exec_statement()` dan `_eval()` di
  `interpreter.py`. Sebelumnya, setiap eksekusi statement/ekspresi
  memanggil `getattr(self, f"_exec_{type(node).__name__}")` — resolve
  method lewat string formatting + attribute lookup berulang-ulang.
  **Diprofilkan dengan `cProfile`** pada while-loop 50.000 iterasi:
  `getattr()` dipanggil 650.008 kali sebagai kontributor waktu terbesar
  kedua sebelum optimisasi. Sekarang dispatch table `{NodeClass: method}`
  dibangun SEKALI di `Interpreter.__init__()` (lewat introspeksi otomatis
  yang mencocokkan nama method `_exec_*`/`_eval_*` ke class Node dari
  `parser.py`), dan lookup selanjutnya memakai `dict.get(type(node))` yang
  jauh lebih murah.
- **Hasil pengukuran yang jujur (bukan berlebihan):**
  - `getattr()` terkonfirmasi **hilang total** dari profil `cProfile`
    setelah optimisasi.
  - `for`-loop (push 10k + iterasi 10k): **70ms → 51ms** (~26% lebih
    cepat), perbaikan yang konsisten dan terukur jelas.
  - `while`-loop 100k iterasi dan rekursi `fib(20)`: hasil berada dalam
    **margin noise pengukuran sandbox** (variasi antar-run 386ms–512ms
    untuk kasus yang sama) — TIDAK diklaim sebagai peningkatan pasti untuk
    kasus ini, karena bottleneck yang tersisa (evaluasi `BinaryExpr`,
    pengecekan tipe) berada di luar scope optimisasi dispatch-table.
  - Startup time diukur terpisah: import semua modul ~12.5ms, inisialisasi
    `Interpreter()` (termasuk 38 built-in) ~0.05ms — bukan bottleneck yang
    signifikan untuk dioptimasi lebih lanjut pada rilis ini.
- Optimisasi arsitektural lebih besar (compile ke bytecode) tetap di
  roadmap versi mendatang, bukan dikerjakan di rilis ini.

### Testing

- `tests/test_v0_5_features.py` — 57 test baru: for-loop (List, string,
  custom type, scope, penolakan tipe salah), blok `html {}` (termasuk
  KASUS KRITIS variabel `html` tetap kompatibel), route (registrasi &
  lookup, path invalid), **HTTP server dengan request HTTP sungguhan**
  (200, 404, konten benar), Map, **JSON yang diverifikasi valid lewat
  `json.loads()` Python asli**, file module alias, string functions
  (termasuk kombinasi `split()` + `for`-loop), **timer dengan pengukuran
  waktu nyata**, dan regresi eksplisit v0.1/v0.3/v0.4.
- `tests/run_all.py` diperbarui memasukkan `test_v0_5_features.py`.
- Total setelah v0.5.0: **192/192 test lulus** (18 v0.1 + 25 List + 25
  Custom Type + 17 Web/File I/O + 30 Kemudahan Pemula + 20 List Ops
  Lanjutan + 57 Web Server/Automation/Dev Tools).

### Dokumentasi

- `examples/for_loop_demo.as`, `examples/route_server_demo.as` — contoh
  program untuk fitur baru, keduanya diverifikasi jalan end-to-end
  (termasuk `route_server_demo.as` diuji dengan HTTP request nyata ke 3
  route sekaligus).
- `README.md` diperbarui: struktur project, section "Web Server,
  Automation & Developer Tools", tabel fitur, roadmap.

### Diubah

- `compiler.py`: `VERSION` dinaikkan dari `0.4.1` ke `0.5.0`.

---

## [0.4.0] — Web, File I/O, dan Build Executable

### Ditambahkan: File I/O

- Built-in function `write_file(path, isi)` — menulis file apa pun ke disk.
  Menerima nilai apa pun sebagai isi (tidak harus string); nilai non-string
  dikonversi otomatis lewat aturan stringify yang sama seperti `print`.
- Built-in function `read_file(path)` — membaca isi file sebagai string.
  Melempar error dengan hint yang jelas kalau file tidak ditemukan.
- Built-in function `str(nilai)` — konversi eksplisit ke string, berguna
  saat menyusun konten file (mis. HTML) dari campuran tipe data.
- **Catatan penting:** path bersifat relatif terhadap *working directory*
  saat `compiler.py` dijalankan, bukan relatif terhadap lokasi file `.as`.
  Didokumentasikan eksplisit di README supaya tidak membingungkan.

### Ditambahkan: Web Server Bawaan

- Built-in function `serve_html(html, port)` — menjalankan HTTP server yang
  melayani satu halaman HTML statis untuk semua request `GET`. Memakai
  `http.server` dari Python standard library saja (tanpa dependency
  eksternal), konsisten dengan filosofi project ini.
- **Diverifikasi dengan HTTP request sungguhan** ke `127.0.0.1` memakai
  `urllib.request` di dalam test — bukan diklaim jalan tanpa dibuktikan.
  Test mengecek status code 200, isi body, dan header `Content-Type`.
- Validasi argumen: port harus integer, isi harus string, dengan pesan
  error yang menyebutkan hint contoh pemakaian.

### Ditambahkan: Build Executable (.exe)

- `build_exe.py` — script build yang membungkus seluruh AstraLang
  (`compiler.py` + `lexer.py` + `parser.py` + `interpreter.py` +
  `runtime.py`) jadi satu file executable memakai PyInstaller.
- Script memvalidasi environment sebelum build: mengecek semua file
  AstraLang ada, dan PyInstaller sudah terpasang — dengan pesan error yang
  actionable kalau belum (`pip install pyinstaller`).
- `BUILD.md` — panduan lengkap cara build di Windows/Linux/Termux/Mac.
- **Batasan yang dicatat jujur:**
  - Proses build **butuh akses internet** (untuk `pip install pyinstaller`)
    dan **tidak bisa dilakukan dari lingkungan pengembangan ini** (sandbox
    tanpa akses internet). Script sudah ditulis dan divalidasi logikanya
    (deteksi file & environment bekerja benar), tapi proses build
    sesungguhnya belum pernah dijalankan sampai selesai dari sesi
    pengembangan ini — perlu dijalankan manual oleh pengguna.
  - PyInstaller **tidak bisa cross-compile**: build di Linux/Termux hanya
    menghasilkan binary Linux, bukan `.exe` Windows. Untuk `.exe` Windows,
    build harus dilakukan di komputer Windows.

### Bug Ditemukan & Diperbaiki

- **Ekspresi `+`/`-` tidak mendukung penulisan multi-baris.** Ditemukan
  saat menjalankan `examples/web_demo.as` (bukan diasumsikan benar dari
  membaca kode) — menyusun string HTML panjang dengan `+` di akhir baris
  lalu lanjut ke baris berikutnya gagal di-parse karena `NEWLINE` dianggap
  pemisah statement. **Perbaikan:** `_term()` di parser sekarang memanggil
  `_skip_newlines()` setelah operator `+`/`-` dikonsumsi, sebelum membaca
  operand berikutnya. Diverifikasi dengan test
  `test_multiline_string_concat_with_plus`.

### Ditolak / Di Luar Cakupan (Dicatat Jujur)

- **Pembuatan APK (Android) ditolak untuk diklaim selesai.** Membuat APK
  butuh Android SDK, Gradle, toolchain Java/Kotlin — tidak tersedia di
  lingkungan pengembangan ini dan tidak bisa diinstall (tidak ada akses
  internet). Alih-alih membuat kerangka kosong yang diklaim "base APK"
  padahal tidak pernah ter-compile, fitur ini secara eksplisit TIDAK
  dikerjakan pada versi ini. Perlu didiskusikan ulang scope-nya (mis.
  menyiapkan struktur project Android yang di-build manual oleh pengguna
  di Android Studio) sebagai item roadmap terpisah.
- **"Cybersecurity" dalam artian tools penyerangan/exploit tidak
  dikerjakan** dan tidak akan dikerjakan — di luar batas yang bisa dibantu.
  Kalau yang dimaksud adalah konsep keamanan yang legal (enkripsi, hashing,
  validasi input) itu bisa dikerjakan sebagai bagian dari standard library
  di versi mendatang, tapi belum masuk di v0.4 ini.

### Testing

- `tests/test_v0_4_web.py` — 17 test baru: write_file/read_file (termasuk
  konversi non-string, file tidak ditemukan), str(), ekspresi multi-baris
  (bug fix di atas), generate HTML dari List lewat loop, **serve_html diuji
  dengan HTTP request sungguhan** (bukan mock), validasi port, dan regresi
  eksplisit v0.1/v0.3.
- `tests/run_all.py` diperbarui memasukkan `test_v0_4_web.py`.
- Total setelah v0.4: **85/85 test lulus** (18 v0.1 + 25 List + 25 Custom
  Type + 17 Web/File I/O).

### Dokumentasi

- `examples/web_demo.as` — contoh generate file HTML dari List lewat loop,
  memakai fitur multi-baris yang baru diperbaiki.
- `BUILD.md` (baru) — panduan build executable per platform.
- `README.md` diperbarui: struktur project, section Web & File I/O, section
  Membuat Executable, tabel fitur, roadmap.

### Ditambahkan: Lebih Mudah dari Python

Tiga perubahan ditambahkan atas permintaan eksplisit supaya AstraLang lebih
ringkas ditulis dibanding Python, bukan cuma "semudah" Python:

- **Variabel tanpa `let` (auto-declare).** `Environment.set()` di
  `runtime.py` sekarang menerima parameter `auto_declare` (default `True`):
  kalau assignment (`nama = "Budi"`) ditujukan ke variabel yang belum ada
  di scope manapun, variabel itu otomatis dideklarasikan di scope saat ini,
  alih-alih melempar error "belum dideklarasikan". `let` tetap bisa dipakai
  kapan saja dan tetap satu-satunya cara untuk sengaja membuat variabel
  lokal baru yang menaungi (shadow) nama yang sama di scope luar.
  - **Perhatian desain yang diverifikasi dengan test eksplisit:** perubahan
    ini SENGAJA tidak mengubah perilaku assignment ke variabel yang *sudah
    ada* di scope luar (mis. closure di dalam function yang mengubah
    variabel scope luar) — kasus itu tetap mengubah variabel yang sudah ada
    melalui rantai parent scope, bukan diam-diam membuat variabel lokal
    baru. Ini diverifikasi lewat `test_closure_assignment_not_broken`, yang
    memastikan `total = total + 1` di dalam function tetap mengakumulasi ke
    variabel `total` di luar (hasil `3` setelah 3x panggil), bukan reset
    tiap panggilan.
  - Typo nama variabel yang melibatkan *pembacaan* nilai (mis.
    `countr = countr + 1` padahal maksudnya `counter`) tetap tertangkap
    sebagai error, karena `Environment.get()` (dipakai untuk membaca) TIDAK
    diubah — tetap strict. Hanya assignment murni yang auto-declare.

- **Pesan error dwibahasa (Indonesia/Inggris).** Modul baru `i18n.py`
  menyediakan kamus terjemahan per-frasa dan fungsi `translate(text, lang)`.
  Pendekatan yang dipilih (dan disepakati eksplisit): pesan error tetap
  DITULIS dalam Bahasa Indonesia di source code sebagai bahasa kanonik;
  terjemahan diterapkan HANYA saat pesan ditampilkan ke pengguna, lewat CLI
  (`compiler.py --lang en`). Frasa yang belum masuk kamus dibiarkan apa
  adanya (Bahasa Indonesia) — bukan error atau crash, sesuai kesepakatan
  bahwa lebih baik sebagian pesan belum sempurna diterjemahkan daripada
  sistem yang rapuh.
  - `print_error_box()` di `compiler.py` diperluas menerima parameter
    `lang`, menerjemahkan judul, pesan, label "Lokasi:"/"Saran:", dan isi
    hint semuanya secara konsisten.
  - Diverifikasi dengan error runtime sungguhan (pembagian dengan nol)
    diterjemahkan penuh dari hulu ke hilir, bukan cuma pengujian kamus
    secara terisolasi.

- **Built-in function siap pakai untuk pemula:**
  - `input(prompt)` — membaca input pengguna dari stdin. Diverifikasi
    dengan stdin sungguhan (bukan mock), termasuk skenario penuh mirip
    game tebak angka dengan beberapa kali `input()` berurutan.
  - `random()` — angka acak 0.0–1.0.
  - `randint(min, maks)` — angka bulat acak inklusif; menolak `min > maks`
    dan argumen non-integer dengan pesan jelas.
  - `round(angka)` / `round(angka, n)` — pembulatan, dengan atau tanpa
    jumlah desimal.
  - `int(nilai)` / `float(nilai)` — konversi tipe eksplisit, menerima
    integer/float/string/boolean; string yang tidak valid (mis. `int("abc")`)
    ditolak dengan hint yang jelas, bukan crash Python mentah.
  - `examples/pemula_demo.as` — program tebak angka lengkap yang
    mengombinasikan `let` opsional, `input()`, `randint()`, `int()`, `str()`
    dalam skenario nyata; diuji end-to-end lewat CLI dengan stdin simulasi
    yang mencakup semua kemungkinan tebakan 1–10.

### Testing (lanjutan v0.4)

- `tests/test_v0_4_beginner_friendly.py` — 30 test baru: variabel tanpa
  `let` (termasuk KASUS KRITIS closure assignment yang wajib tidak rusak,
  dan typo yang tetap tertangkap), `let` tetap mendeklarasikan lokal,
  sistem terjemahan (frasa dikenal, frasa tak dikenal, passthrough
  Indonesia, normalisasi kode bahasa, error sungguhan diterjemahkan
  end-to-end), dan semua built-in pemula baru (termasuk validasi
  range/error masing-masing).
- Satu bug ditemukan & diperbaiki selama pengembangan test: helper test
  awalnya memakai `contextlib.redirect_stdin` yang **tidak ada** di
  `contextlib` Python (hanya ada `redirect_stdout`/`redirect_stderr`) —
  diperbaiki dengan mengganti `sys.stdin` secara manual di dalam
  try/finally.
- `tests/run_all.py` diperbarui memasukkan `test_v0_4_beginner_friendly.py`.
- Total setelah v0.4.0: **115/115 test lulus** (18 v0.1 + 25 List +
  25 Custom Type + 17 Web/File I/O + 30 Kemudahan Pemula).

---

## [0.4.1] — Contoh Game & Operasi List Lanjutan

Dikerjakan sebagai respons atas permintaan "web game format AstraLang" —
tiga pendekatan game dibuat dan masing-masing diverifikasi jalan nyata
sebelum diklaim selesai.

### Ditambahkan: Contoh Game

- **`examples/game_bgk.as`** — game terminal Batu Gunting Kertas. Memakai
  custom type `Skor` untuk menghitung menang/kalah/seri, List sebagai
  daftar pilihan valid, `input()` untuk giliran pemain, `randint()` untuk
  pilihan komputer, dan validasi input. Logika kemenangan diverifikasi
  terisolasi (semua 5 kombinasi pilihan diuji manual) sebelum diintegrasikan
  ke loop permainan penuh.
- **`examples/web_game.as`** — game tebak angka **interaktif di browser**.
  AstraLang menyusun HTML + CSS + JavaScript sebagai satu string (JS
  menangani klik tombol, cek jawaban, update skor secara real-time di sisi
  klien), lalu menyajikannya lewat `serve_html()`. Diverifikasi dengan HTTP
  request sungguhan yang mengonfirmasi seluruh konten game (fungsi JS,
  event listener, elemen form) benar-benar terkirim ke browser, bukan cuma
  diasumsikan dari membaca kode.
  - **Batasan yang dicatat jujur:** `serve_html()` melayani halaman statis
    yang sama untuk semua request — belum ada mekanisme AstraLang menerima
    data balik dari browser (mis. menyimpan skor tertinggi di sisi server).
    Untuk pola game seperti ini, seluruh logic interaktif harus berjalan di
    JavaScript sisi klien.
- **`examples/leaderboard_demo.as`** — AstraLang murni (tanpa JavaScript)
  menghasilkan halaman leaderboard statis dari List berisi custom type
  `Pemain`, diurutkan berdasarkan skor.

### Ditambahkan: Operasi List Lanjutan

Saat membuat `leaderboard_demo.as`, kebutuhan mengurutkan List custom type
memakai bubble sort manual (±15 baris) terasa jadi friksi yang tidak perlu
untuk kasus umum — mendorong penambahan built-in List berikut:

- **`sort(daftar)`** — urutkan List berisi angka atau string (menaik),
  mengembalikan List baru (tidak mengubah aslinya). Menolak List dengan
  tipe campuran dengan pesan jelas.
- **`sort_by(daftar, fungsi_kunci)`** — urutkan List berisi custom type
  berdasarkan sebuah field, dengan memanggil balik function AstraLang
  sebagai key pengurutan. Ini membutuhkan refactor kecil:
  `_call_astra_function()` diekstrak dari `_eval_CallExpr` di
  `interpreter.py` supaya logic pemanggilan `AstraFunction` bisa dipakai
  ulang dari built-in, tanpa duplikasi kode. Diverifikasi bahwa refactor
  ini tidak mengubah perilaku pemanggilan function biasa (termasuk rekursi
  dan function tanpa `return`) lewat test regresi eksplisit.
- **`reverse(daftar)`** — balik urutan List, dipakai bersama `sort_by()`
  untuk mengurutkan turun (leaderboard skor tertinggi dulu).
- **`contains(daftar, nilai)`**, **`join(daftar, pemisah)`**,
  **`slice(daftar, mulai, akhir)`** — operasi List umum lain yang sempat
  dicatat sebagai "belum ada" di CHANGELOG v0.3.
- `examples/leaderboard_demo.as` disederhanakan memakai `sort_by()` +
  `reverse()`, menggantikan bubble sort manual — hasil akhirnya
  diverifikasi identik dengan versi bubble sort sebelumnya.

### Diubah

- `compiler.py`: `VERSION` dinaikkan dari `0.4.0` ke `0.4.1`.

### Testing

- `tests/test_v0_4_list_ops.py` — 20 test baru: sort (angka, string, tidak
  mutasi original, menolak tipe campuran), reverse, contains, join, slice,
  sort_by (dengan custom type, menolak non-function, menolak arity salah),
  skenario leaderboard end-to-end, dan regresi eksplisit yang memastikan
  refactor `_call_astra_function` tidak mengubah pemanggilan function biasa.
- `tests/run_all.py` diperbarui memasukkan `test_v0_4_list_ops.py`.
- Total setelah v0.4.1: **135/135 test lulus** (18 v0.1 + 25 List + 25
  Custom Type + 17 Web/File I/O + 30 Kemudahan Pemula + 20 List Ops
  Lanjutan).

### Dokumentasi

- `README.md` diperbarui: section "Membuat Game dengan AstraLang" (3
  pendekatan), section "Operasi List Tambahan", struktur project, tabel
  fitur.

---

## [0.3.0] — Rollback ke Fondasi Bahasa Inti

### Dicabut (Reverted)

- **Seluruh modul "Astra Device Bridge" yang ditambahkan di v0.2.1 DICABUT
  TOTAL atas permintaan eksplisit.** Ini termasuk:
  - File `device_bridge.py` dihapus.
  - Statement `SET_TARGET`, `LIST_DEVICES`, `START_BROADCAST`,
    `STOP_BROADCAST`, `PAIR_REQUEST`, `PAIR_APPROVE` dihapus dari
    lexer & parser.
  - Ekspresi member access (`LIGHT.ON`, `device.vibrate`, dst) dan token
    `DOT` dihapus dari lexer & parser.
  - `Interpreter.__init__()` dikembalikan ke signature v0.1
    (`Interpreter()`, tanpa parameter `device_name`).
  - Opsi CLI `--device-name` dihapus dari `compiler.py`.
  - `examples/device_demo.as` dan `tests/test_device_bridge.py` dihapus.
- Alasan pencabutan: fitur device-to-device dinilai prematur untuk fase ini
  dan mengalihkan fokus dari penguatan fondasi bahasa (type system, error
  handling, module system) yang dibutuhkan lebih dulu sebelum fitur-fitur
  besar lanjutan dibangun di atasnya.
- Project dikembalikan ke kondisi setara v0.1 murni (diverifikasi ulang
  lewat `tests/test_v0_1_regression.py`, 18/18 lulus) sebagai basis bersih
  untuk pengembangan v0.3 ke atas.

### Ditambahkan (v0.3): Type System — List

- **Tipe data List**
  - Literal `[elemen, elemen, ...]`, termasuk list kosong `[]` dan trailing
    comma `[1, 2, 3,]`.
  - Indexing `daftar[i]` untuk baca, dan `daftar[i] = nilai` untuk tulis.
  - List bersarang (nested list) didukung penuh, mis. `matrix[0][1]`.
  - `AstraList` (di `runtime.py`): wrapper tipis di atas Python `list` dengan
    semantik pass-by-reference (menetapkan List ke variabel lain berbagi
    referensi yang sama, konsisten dengan kebanyakan bahasa modern).
  - Built-in function baru: `push(daftar, nilai)`, `pop(daftar)`,
    `get(daftar, index)`. Dipakai sebagai fungsi (bukan method `.push()`)
    karena AstraLang belum punya syntax method-call — ini akan disederhanakan
    di versi berikutnya begitu method syntax ditambahkan.
  - `len()` diperluas mendukung List selain string.
  - `print` pada List menghasilkan format `[1, 2, 3]`.

- **Nilai `null` sebagai literal eksplisit**
  - Sebelumnya `null` hanya representasi internal (`None` Python) yang tidak
    bisa ditulis langsung di kode `.as`. Sekarang `null` adalah keyword yang
    bisa dipakai langsung: `let x = null`, dan bisa dibandingkan `x == null`.

- **Lexer & Parser**
  - Token baru: `LBRACKET` (`[`), `RBRACKET` (`]`), `NULL`.
  - AST node baru: `ListExpr`, `IndexExpr`, `IndexAssignExpr`.
  - Grammar `_call()` diperluas mendukung indexing berantai (`matrix[0][1]`)
    dengan pola yang sama seperti pemanggilan fungsi berantai.
  - `_assignment()` diperluas mengenali `daftar[i] = nilai` sebagai
    `IndexAssignExpr`, terpisah dari assignment variabel biasa.

### Ditambahkan (v0.3): Error System

- **`AstraRuntimeError` dan `ParserError` sekarang punya field `hint`
  opsional** berisi saran perbaikan konkret, ditampilkan terpisah dari pesan
  utama baik saat exception di-print langsung maupun lewat CLI
  (`compiler.py` menampilkan baris `Saran: ...` setelah `Lokasi: ...`).
- Hint ditambahkan untuk error yang paling sering dialami pemula:
  - Variabel tidak ditemukan → saran deklarasi dengan `let` atau cek salah ketik.
  - Assignment ke variabel yang belum dideklarasikan → saran pakai `let`.
  - Index list di luar jangkauan → saran rentang index yang valid.
  - Index bukan integer → saran format index yang benar.
  - `pop()` dari list kosong → saran cek `len()` dulu.
  - Tipe data tidak sesuai untuk operator matematika/perbandingan → saran
    tipe yang diharapkan.
  - List literal tidak tertutup (`[1, 2` tanpa `]`) → saran pasangkan `[` dan `]`.
  - Target assignment tidak valid → saran bentuk assignment yang benar.
  - Token tak terduga saat parsing → hint kontekstual berdasarkan jenis
    token yang salah tempat (mis. `}` berlebih, `)` berlebih, `]` berlebih,
    EOF tiba-tiba, `=` tak terduga).

### Testing

- `tests/test_v0_3_features.py` — 25 test baru mencakup: List literal,
  indexing, index assignment, index out of range, push/pop/get, len() untuk
  List, nested list, List di dalam while loop, null literal & perbandingan,
  index bukan integer, pop dari list kosong, hint pada ParserError & 
  AstraRuntimeError, trailing comma, dan regresi eksplisit yang memverifikasi
  fitur v0.1 (rekursi faktorial) masih benar setelah List ditambahkan.
- `tests/run_all.py` diperbarui memasukkan `test_v0_3_features.py`.
- Total setelah v0.3: **43/43 test lulus** (18 regresi v0.1 + 25 fitur v0.3).

### Dokumentasi

### Ditambahkan (v0.3 lanjutan): Custom Type

- **Deklarasi custom type** dengan syntax `type Nama { field1 field2 ... }`.
  Nama type harus diawali huruf besar (konvensi wajib, bukan sekadar saran)
  — ini dipakai parser untuk membedakan instance literal dari blok kode
  biasa (lihat catatan kasus tepi di bawah).
- **Instance literal**: `Nama { field1: nilai1, field2: nilai2 }`. Semua
  field wajib diisi; field yang tidak dikenal oleh type-nya, atau field
  yang belum diisi, ditolak dengan error yang menyebutkan field mana saja
  yang tersedia/belum diisi.
- **Field access** (`p.x`) dan **field assignment** (`p.x = 99`) lewat
  operator titik (`.`).
- Field instance boleh berisi tipe data apa pun termasuk List, dan List
  boleh berisi banyak instance — keduanya saling berkombinasi bebas
  (dibuktikan lewat `examples/custom_type_demo.as`: keranjang belanja berupa
  List of Item, masing-masing Item instance dengan field harga).
- `AstraTypeDef` dan `AstraInstance` (di `runtime.py`): representasi
  runtime untuk blueprint type dan instance-nya. `AstraInstance.get_field`/
  `set_field` melempar error dengan hint yang menyebutkan daftar field yang
  sah pada type tersebut.

- **Lexer & Parser**
  - Token baru: `TYPE`, `DOT` (`.`), `COLON` (`:`).
  - AST node baru: `TypeDecl`, `InstanceExpr`, `FieldAccessExpr`,
    `FieldAssignExpr`.
  - Grammar `_call()` diperluas mendukung field access berantai (`a.b.c`)
    dengan pola yang sama seperti indexing berantai.
  - `_assignment()` diperluas mengenali `p.x = nilai` sebagai
    `FieldAssignExpr`.

- **Bug ditemukan & diperbaiki selama pengembangan (dicatat secara jujur):**
  1. **Kasus tepi ambiguitas instance literal vs blok kondisi.** Heuristik
     awal "`Nama` diikuti `{` = instance literal" ternyata salah mengenali
     `if Aktif { ... }` (variabel boolean berhuruf besar bernama `Aktif`)
     sebagai instance literal, membuat parser mencoba membaca isi blok `if`
     sebagai daftar field dan gagal dengan error yang membingungkan.
     **Perbaikan:** parser sekarang punya flag konteks
     `_allow_instance_literal` yang dimatikan sementara selama parsing
     kondisi `if`/`while`, dan dinyalakan lagi untuk sisa ekspresi lainnya.
     Diverifikasi dengan test eksplisit
     (`test_edge_case_uppercase_var_in_if_condition` dan versi `while`-nya).
  2. **List literal multi-baris tidak didukung.** Menulis list dengan
     elemen di baris terpisah (pola umum untuk list yang isinya instance,
     seperti contoh keranjang belanja) gagal di-parse karena parser
     sebelumnya tidak mengizinkan newline setelah `[`, setelah `,`, atau
     sebelum `]`. **Perbaikan:** `_primary()` untuk list literal sekarang
     memanggil `_skip_newlines()` di titik-titik tersebut, konsisten dengan
     cara `_block()` menangani newline. Diverifikasi dengan test
     `test_multiline_list_literal` dan `test_multiline_list_with_trailing_comma`.
  - Kedua bug ini ditemukan lewat pengujian end-to-end memakai
    `examples/custom_type_demo.as` sebelum diklaim selesai — bukan
    diasumsikan benar dari pembacaan kode saja.

### Testing

- `tests/test_v0_3_custom_type.py` — 25 test baru: deklarasi type & instance,
  field access & assignment, kombinasi dengan List (field berisi list, list
  berisi instance), instance sebagai parameter fungsi, validasi field tak
  dikenal/belum diisi, type tak dikenal, field access pada non-instance,
  type tanpa field ditolak di parser, KEDUA kasus tepi di atas (uppercase var
  di kondisi if/while), KEDUA bug list multi-baris di atas, dan regresi
  eksplisit yang memverifikasi v0.1 (rekursi) serta List v0.3 tetap benar.
- `tests/run_all.py` diperbarui memasukkan `test_v0_3_custom_type.py`.
- Total setelah v0.3 (lengkap): **68/68 test lulus** (18 regresi v0.1 + 25
  fitur List + 25 fitur Custom Type).

### Dokumentasi

- `examples/custom_type_demo.as` — contoh program mendemonstrasikan seluruh
  fitur Custom Type: deklarasi, instance, field access/assignment, field
  berisi List, List berisi instance, instance sebagai parameter fungsi.
- `README.md` diperbarui: struktur project, contoh kode Custom Type, tabel
  fitur (Custom Type kini berstatus selesai), roadmap.

### v0.3 Dinyatakan Selesai

Dengan Custom Type selesai dan teruji, fokus roadmap v0.3 (Type System +
Error System) dianggap tuntas. Operasi List lanjutan (`slice`, `contains`,
`remove_at`, penggabungan `+`) dan method-call syntax (`p.method()` alih-alih
`fungsi(p)`) belum ada — akan dievaluasi kembali kebutuhannya saat v0.4
(module system, standard library) mulai dikerjakan, karena keduanya lebih
relevan didesain bersamaan dengan standard library daripada berdiri sendiri.

---

## [0.2.1] — Astra Device Bridge *(DICABUT di v0.3.0, lihat di atas)*

> **Catatan:** Rilis ini kemudian ditarik seluruhnya di v0.3.0. Bagian di
> bawah dipertahankan sebagai catatan sejarah, bukan sebagai dokumentasi
> fitur yang masih aktif. Untuk kondisi project saat ini, lihat `README.md`
> dan entri [0.3.0] di atas.

### Ditambahkan (saat itu, sekarang sudah dicabut)

- **Device Naming System**
  - Statement `SET_TARGET "NAMA_DEVICE"` untuk menargetkan device Astra
    berdasarkan nama unik (bukan nomor telepon/IP manual).
  - Command kontrol tanpa `SET_TARGET` otomatis berlaku untuk device sendiri.

- **Local Network Discovery**
  - Statement `LIST_DEVICES` mencari device Astra aktif di jaringan WiFi lokal
    memakai UDP broadcast (`device_bridge.DiscoveryService`).
  - Device yang menjalankan `START_BROADCAST` akan otomatis membalas
    permintaan discovery dari device lain.

- **Astra Mini Web Server (Dashboard)**
  - Statement `START_BROADCAST` menjalankan dashboard HTTP ringan
    (`device_bridge.DashboardServer`, berbasis `http.server` bawaan Python,
    tanpa dependency eksternal) di `http://localhost:48292/` (default).
  - Dashboard menampilkan status koneksi, nama device, dan daftar
    pairing/approval. Bersifat **read-only** — tidak ada kontrol device dari
    halaman web, untuk mencegah celah keamanan.
  - Endpoint `GET /api/status` menyediakan status yang sama dalam format JSON.
  - Statement `STOP_BROADCAST` menghentikan discovery responder & dashboard.

- **Device API Framework** (`device_bridge.DeviceAPI`)
  - `LIGHT.ON` / `LIGHT.OFF` — kontrol lampu/senter.
  - `device.vibrate(durasi_ms)` — getar dengan durasi dalam milidetik.
  - `device.battery` — status baterai.
  - `device.info` — info umum device.
  - Dua provider implementasi:
    - `SimulatedDeviceProvider` (default, aman di semua platform, hasil
      ditandai jelas `"mode": "simulated"`).
    - `TermuxDeviceProvider` (memanggil `termux-torch`, `termux-vibrate`,
      `termux-battery-status` bila Termux:API terpasang; melempar error jelas
      jika binary tidak ditemukan, bukan pura-pura berhasil).

- **Security & Permission**
  - Statement `PAIR_REQUEST "NAMA_DEVICE"` menghasilkan kode pairing 4-digit.
  - Statement `PAIR_APPROVE "NAMA_DEVICE"` wajib dijalankan dengan kode yang
    cocok sebelum command kontrol ke device tersebut diizinkan.
  - Semua command kontrol ke device **selain diri sendiri** diblokir dengan
    `AstraPermissionError` (turunan `AstraRuntimeError`) sampai proses
    pairing & approval selesai. Tidak ada jalur bypass.
  - Kode pairing yang salah ditolak secara eksplisit.

- **Lexer & Parser**
  - Token baru: `SET_TARGET`, `LIST_DEVICES`, `START_BROADCAST`,
    `STOP_BROADCAST`, `PAIR_REQUEST`, `PAIR_APPROVE`, `DOT` (`.`).
  - AST node baru: `SetTargetStatement`, `ListDevicesStatement`,
    `StartBroadcastStatement`, `StopBroadcastStatement`,
    `PairRequestStatement`, `PairApproveStatement`, `MemberExpr`.
  - Grammar `_call()` diperluas mendukung member access berantai
    (`LIGHT.ON`, `device.light.on`) tanpa mengubah parsing pemanggilan
    fungsi yang sudah ada.

- **CLI (`compiler.py`)**
  - Opsi baru `--device-name "NAMA"` untuk menentukan nama device saat
    menjalankan script. Jika tidak diisi, nama device dibuat otomatis
    (`ASTRA-DEVICE-xxxx`) agar script lama tetap berjalan tanpa perubahan.
  - Penanganan `AstraPermissionError` menghasilkan pesan CLI khusus
    ("Command device ditolak (Permission Error)") sebelum jatuh ke
    penanganan `AstraRuntimeError` umum.

- **Testing**
  - `tests/test_v0_1_regression.py` — 18 test memastikan seluruh fitur v0.1
    (lexer, parser, variable, kondisi, loop, fungsi, rekursi, built-in)
    tidak berubah perilakunya.
  - `tests/test_device_bridge.py` — 13 test untuk fitur baru, termasuk
    3 test keamanan eksplisit (blokir tanpa pairing, blokir tanpa approval,
    tolak kode pairing salah) serta test discovery UDP dan dashboard HTTP
    nyata (bukan mock).
  - `tests/run_all.py` — runner gabungan.

- **Dokumentasi**
  - `README.md` diperbarui: struktur project, arsitektur, cara pakai
    `--device-name`, contoh kode Astra Device Bridge, tabel fitur, cara
    menjalankan test.
  - `examples/device_demo.as` — contoh program menunjukkan alur lengkap
    (kontrol device sendiri, `SET_TARGET`, pairing, kontrol device lain).

### Diubah

- `compiler.py`: `VERSION` dinaikkan dari `0.1.0` ke `0.2.1`.
- `interpreter.py`: `Interpreter.__init__()` menerima parameter opsional
  baru `device_name` (default `None`, backward compatible — kode lama yang
  memanggil `Interpreter()` tanpa argumen tetap berjalan).

### Tidak Diubah / Kompatibilitas

- Seluruh sintaks v0.1 (`let`, `print`, `if/else`, `while`, `function`,
  `return`, operator matematika/logika/perbandingan, komentar `#`, `len()`)
  berjalan identik seperti sebelumnya. Dibuktikan lewat
  `tests/test_v0_1_regression.py` (18/18 lulus).
- Tidak ada file lama yang dihapus atau ditulis ulang dari nol.

### Keterbatasan yang Diketahui (Dicatat Secara Jujur)

- `LIST_DEVICES` dan `START_BROADCAST` memakai UDP broadcast asli dan
  terbukti bekerja antar-proses di localhost (lihat test), tetapi discovery
  lintas-perangkat sungguhan di jaringan WiFi fisik **belum divalidasi** dari
  lingkungan pengembangan ini (tidak ada akses ke perangkat Android/Termux
  nyata pada tahap ini). Disarankan pengujian manual di 2 perangkat sebelum
  dianggap stabil untuk penggunaan produksi.
- `LIGHT.ON/OFF`, `device.vibrate`, `device.battery` menggunakan
  `SimulatedDeviceProvider` secara default di semua platform. Dukungan
  hardware asli via `TermuxDeviceProvider` sudah diimplementasikan tapi
  **belum diuji di perangkat Termux/Android sungguhan** — perlu validasi
  manual oleh pengguna yang memiliki paket `termux-api` terpasang.
- Proses `PAIR_APPROVE` saat ini memverifikasi kode pairing di dalam
  registry milik proses AstraLang yang sama. Channel persetujuan
  device-to-device yang independen antar dua proses AstraLang berbeda
  (mis. lewat request HTTP/UDP terautentikasi) belum diimplementasikan dan
  direncanakan sebagai peningkatan keamanan di versi berikutnya.
- Dashboard web tidak memakai HTTPS/autentikasi (murni HTTP lokal, cocok
  untuk jaringan rumah tepercaya). Ini akan menjadi pertimbangan sebelum
  fitur ini dianggap siap untuk jaringan yang tidak tepercaya.

---

## [0.1.0] — Prototype Awal

### Ditambahkan

- Lexer (`lexer.py`): tokenisasi source `.as` — angka (int/float), string
  (dengan escape), identifier/keyword, operator, simbol, komentar `#`, error
  karakter tidak dikenal & string tidak ditutup dengan lokasi baris/kolom.
- Parser (`parser.py`): recursive-descent parser menghasilkan AST
  (`Program`, `LetStatement`, `PrintStatement`, `IfStatement`,
  `WhileStatement`, `FunctionDecl`, `ReturnStatement`, ekspresi biner/unary,
  literal, variable, pemanggilan fungsi) dengan precedence climbing untuk
  ekspresi matematika/logika, plus `ParserError` dengan pesan jelas.
- Interpreter (`interpreter.py`): tree-walking interpreter mendukung
  `print`, `let`, assignment, tipe data (integer, float, string, boolean),
  operasi matematika (`+ - * / %`), perbandingan, logika (`and or not`),
  `if/else` (termasuk `else if` berantai), `while` (dengan batas iterasi
  pengaman), `function` + `return` + rekursi, dan built-in `len()`.
- Runtime (`runtime.py`): `Environment` dengan lexical scoping bertingkat,
  `AstraRuntimeError`, `ReturnSignal`, `AstraFunction`, `AstraBuiltinFunction`.
- CLI (`compiler.py`): entry point `python3 compiler.py <file.as>`, opsi
  `--help` dan `--version`, penanganan error 3 lapis (Lexer/Parser/Runtime)
  dengan pesan & lokasi baris yang jelas, exit code sesuai standar.
- Contoh program: `examples/hello.as`, `examples/advanced.as`.
- `README.md` awal: instalasi Termux, cara pakai, contoh kode, tabel fitur,
  roadmap v0.1–v1.0.

### Catatan Desain

- Pendekatan tree-walking interpreter dipilih untuk kemudahan pengembangan
  dan debugging di tahap awal; kompilasi ke bytecode/native direncanakan di
  roadmap v0.4+.
- Tidak ada dependency eksternal — hanya Python standard library — supaya
  bisa langsung dijalankan di Termux tanpa `pip install`.
