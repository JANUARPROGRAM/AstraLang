# Web Game: Tebak Angka Interaktif (v0.4)
#
# AstraLang menyusun halaman HTML + CSS + JavaScript sebagai satu string,
# lalu menyajikannya lewat serve_html(). Logika interaksi (klik tombol,
# cek tebakan, update skor) berjalan di JavaScript di sisi browser --
# AstraLang berperan menyusun & menyajikan halamannya.
#
# Jalankan: python3 compiler.py examples/web_game.as
# Lalu buka http://localhost:8080/ di browser.

let judul = "Tebak Angka - AstraLang Web Game"

let html = "<!DOCTYPE html><html lang=\"id\"><head><meta charset=\"utf-8\">" +
    "<title>" + judul + "</title>" +
    "<style>" +
    "body { font-family: sans-serif; background: #0f172a; color: #e2e8f0; " +
    "display: flex; flex-direction: column; align-items: center; " +
    "justify-content: center; height: 100vh; margin: 0; }" +
    "h1 { color: #38bdf8; }" +
    "input { padding: 0.5rem; font-size: 1rem; border-radius: 6px; border: none; }" +
    "button { padding: 0.5rem 1rem; font-size: 1rem; margin-left: 0.5rem; " +
    "border-radius: 6px; border: none; background: #38bdf8; cursor: pointer; }" +
    "#pesan { margin-top: 1rem; font-size: 1.2rem; min-height: 2rem; }" +
    "#skor { margin-top: 2rem; color: #94a3b8; }" +
    "</style></head><body>" +
    "<h1>" + judul + "</h1>" +
    "<p>Aku memikirkan angka antara 1 sampai 20.</p>" +
    "<div>" +
    "<input type=\"number\" id=\"tebakan\" min=\"1\" max=\"20\" placeholder=\"Tebakanmu\">" +
    "<button onclick=\"cekTebakan()\">Tebak!</button>" +
    "</div>" +
    "<div id=\"pesan\"></div>" +
    "<div id=\"skor\">Percobaan: <span id=\"jumlah_percobaan\">0</span></div>" +
    "<script>" +
    "let jawaban = Math.floor(Math.random() * 20) + 1;" +
    "let percobaan = 0;" +
    "function cekTebakan() {" +
    "  const input = document.getElementById('tebakan');" +
    "  const pesan = document.getElementById('pesan');" +
    "  const tebakan = parseInt(input.value);" +
    "  if (isNaN(tebakan)) {" +
    "    pesan.textContent = 'Masukkan angka dulu ya!';" +
    "    return;" +
    "  }" +
    "  percobaan++;" +
    "  document.getElementById('jumlah_percobaan').textContent = percobaan;" +
    "  if (tebakan === jawaban) {" +
    "    pesan.textContent = 'Benar! Jawabannya ' + jawaban + ' (percobaan ke-' + percobaan + ')';" +
    "    pesan.style.color = '#4ade80';" +
    "  } else if (tebakan < jawaban) {" +
    "    pesan.textContent = 'Terlalu kecil, coba lagi!';" +
    "    pesan.style.color = '#facc15';" +
    "  } else {" +
    "    pesan.textContent = 'Terlalu besar, coba lagi!';" +
    "    pesan.style.color = '#facc15';" +
    "  }" +
    "  input.value = '';" +
    "  input.focus();" +
    "}" +
    "document.getElementById('tebakan').addEventListener('keyup', function(e) {" +
    "  if (e.key === 'Enter') cekTebakan();" +
    "});" +
    "</script>" +
    "</body></html>"

print "Menyimpan halaman game ke web_game_output.html untuk pratinjau..."
write_file("web_game_output.html", html)

print "Menjalankan web server di port 8080..."
serve_html(html, 8080)
