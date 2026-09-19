# Contoh v0.4: AstraLang untuk pemula
# Menunjukkan fitur yang bikin AstraLang lebih gampang dari Python:
# - variabel BOLEH tanpa 'let' (langsung nama = nilai)
# - input(), random(), randint() siap pakai
# - pesan error otomatis punya saran perbaikan (coba salahin kodenya!)

print "=== Program Tebak Angka ==="

jawaban = randint(1, 10)
tebakan = 0
percobaan = 0

print "Aku memikirkan angka antara 1 sampai 10."

while tebakan != jawaban {
    let teks_tebakan = input("Tebak angkanya: ")
    tebakan = int(teks_tebakan)
    percobaan = percobaan + 1

    if tebakan < jawaban {
        print "Terlalu kecil!"
    } else {
        if tebakan > jawaban {
            print "Terlalu besar!"
        }
    }
}

print "Benar! Jawabannya " + str(jawaban)
print "Kamu menebak sebanyak " + str(percobaan) + " kali."
