# Contoh: AstraLang membuat file HTML (v0.4)
#
# AstraLang belum punya templating HTML khusus -- HTML disusun sebagai
# string biasa, lalu ditulis ke file pakai write_file().

let judul = "Halo dari AstraLang"

let daftar_fitur = ["List", "Custom Type", "Error dengan hint", "Web server bawaan"]

let item_html = ""
let i = 0
while i < len(daftar_fitur) {
    item_html = item_html + "<li>" + daftar_fitur[i] + "</li>"
    i = i + 1
}

let html = "<!DOCTYPE html><html><head><title>" + judul + "</title></head><body>" +
    "<h1>" + judul + "</h1>" +
    "<p>Halaman ini dibuat oleh program AstraLang (.as).</p>" +
    "<h2>Fitur AstraLang:</h2><ul>" + item_html + "</ul>" +
    "</body></html>"

write_file("output.html", html)
print "File output.html berhasil dibuat!"
