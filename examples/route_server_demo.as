# Contoh HTTP Server Multi-Route (v0.5)
#
# Berbeda dari serve_html() (v0.4) yang cuma sajikan 1 halaman statis,
# HTTP_SERVER_START() mendukung banyak route sekaligus, masing-masing
# didaftarkan dengan 'route "path" { ... return isi }'.
#
# Jalankan: python3 compiler.py examples/route_server_demo.as
# Lalu buka di browser:
#   http://localhost:8080/
#   http://localhost:8080/tentang
#   http://localhost:8080/data

route "/" {
    return "Hello AstraLang! Coba buka /tentang atau /data juga."
}

route "/tentang" {
    return html {
        title "Tentang"
        heading "Tentang Server Ini"
        text "Server ini dibuat sepenuhnya dengan AstraLang v0.5, memakai HTTP_SERVER_START() dan route."
    }
}

route "/data" {
    let m = map_new()
    map_set(m, "bahasa", "AstraLang")
    map_set(m, "versi", "0.5.0")
    map_set(m, "fitur", ["route", "html block", "json", "map"])
    return json_stringify(m)
}

print "Mendaftarkan route selesai. Menjalankan server..."
HTTP_SERVER_START(8080)
