# Halaman Leaderboard Statis (v0.4)
#
# Contoh AstraLang murni menghasilkan halaman HTML dari data (custom type +
# List) -- cocok untuk laporan hasil game, leaderboard, ringkasan skor, dll.
# Beda dari web_game.as: di sini AstraLang yang menyusun SEMUA kontennya
# (tidak ada logic interaktif JavaScript), hasilnya halaman statis.
#
# Memakai sort_by() (built-in v0.4 lanjutan) untuk mengurutkan List custom
# type berdasarkan sebuah field, tanpa perlu menulis algoritma sort manual.

type Pemain {
    nama
    skor
}

let pemain_list = [
    Pemain { nama: "Astra", skor: 87 },
    Pemain { nama: "Budi", skor: 95 },
    Pemain { nama: "Citra", skor: 72 },
    Pemain { nama: "Dedi", skor: 60 }
]

function ambil_skor(p) {
    return p.skor
}

let terurut_naik = sort_by(pemain_list, ambil_skor)
pemain_list = reverse(terurut_naik)

let baris_html = ""
let peringkat = 1
let i = 0
while i < len(pemain_list) {
    let p = pemain_list[i]
    baris_html = baris_html +
        "<tr><td>" + str(peringkat) + "</td><td>" + p.nama + "</td><td>" + str(p.skor) + "</td></tr>"
    peringkat = peringkat + 1
    i = i + 1
}

let html = "<!DOCTYPE html><html lang=\"id\"><head><meta charset=\"utf-8\">" +
    "<title>Leaderboard - AstraLang</title>" +
    "<style>" +
    "body { font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }" +
    "h1 { color: #38bdf8; }" +
    "table { border-collapse: collapse; width: 100%; max-width: 500px; }" +
    "th, td { border: 1px solid #334155; padding: 0.6rem 1rem; text-align: left; }" +
    "th { background: #1e293b; }" +
    "tr:nth-child(2) td { color: #facc15; font-weight: bold; }" +
    "</style></head><body>" +
    "<h1>Leaderboard</h1>" +
    "<table><tr><th>Peringkat</th><th>Nama</th><th>Skor</th></tr>" +
    baris_html +
    "</table></body></html>"

write_file("leaderboard.html", html)
print "Leaderboard berhasil dibuat: leaderboard.html"
print ""
print "Urutan akhir:"
let k = 0
while k < len(pemain_list) {
    print str(k + 1) + ". " + pemain_list[k].nama + " - " + str(pemain_list[k].skor)
    k = k + 1
}
