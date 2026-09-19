# Contoh for-loop (v0.5)
#
# Sebelumnya (v0.1-v0.4) iterasi List harus manual:
#   let i = 0
#   while i < len(daftar) { ... i = i + 1 }
#
# Sekarang bisa langsung:
#   for item in daftar { ... }

print "=== Iterasi List angka ==="
for angka in [10, 20, 30] {
    print angka
}

print "=== Iterasi List string ==="
let buah = ["apel", "jeruk", "mangga"]
for nama in buah {
    print upper(nama)
}

print "=== Iterasi karakter dalam string ==="
for huruf in "Astra" {
    print huruf
}

print "=== Iterasi List custom type ==="
type Pemain {
    nama
    skor
}
let pemain_list = [
    Pemain { nama: "A", skor: 80 },
    Pemain { nama: "B", skor: 95 }
]
let total = 0
for p in pemain_list {
    print p.nama + ": " + str(p.skor)
    total = total + p.skor
}
print "Total skor: " + str(total)
