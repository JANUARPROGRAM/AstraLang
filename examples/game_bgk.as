# Game: Batu Gunting Kertas (v0.4)
# Contoh game sederhana yang jalan di terminal, memakai custom type,
# List, function, dan built-in input()/randint().

type Skor {
    menang
    kalah
    seri
}

let skor = Skor { menang: 0, kalah: 0, seri: 0 }
let pilihan_valid = ["batu", "gunting", "kertas"]

function pilihan_komputer() {
    let index = randint(0, 2)
    return pilihan_valid[index]
}

function menang_lawan(pemain, lawan) {
    if pemain == "batu" and lawan == "gunting" {
        return true
    }
    if pemain == "gunting" and lawan == "kertas" {
        return true
    }
    if pemain == "kertas" and lawan == "batu" {
        return true
    }
    return false
}

function is_pilihan_valid(pilihan) {
    let i = 0
    while i < len(pilihan_valid) {
        if pilihan_valid[i] == pilihan {
            return true
        }
        i = i + 1
    }
    return false
}

print "=== BATU GUNTING KERTAS ==="
print "Ketik: batu / gunting / kertas / selesai"
print ""

main = true
while main {
    let pemain = input("Pilihanmu: ")

    if pemain == "selesai" {
        main = false
    } else {
        if is_pilihan_valid(pemain) == false {
            print "Pilihan tidak dikenal. Coba lagi."
        } else {
            let komputer = pilihan_komputer()
            print "Komputer memilih: " + komputer

            if pemain == komputer {
                print "SERI!"
                skor.seri = skor.seri + 1
            } else {
                if menang_lawan(pemain, komputer) {
                    print "KAMU MENANG!"
                    skor.menang = skor.menang + 1
                } else {
                    print "KAMU KALAH!"
                    skor.kalah = skor.kalah + 1
                }
            }
            print ""
        }
    }
}

print "=== HASIL AKHIR ==="
print "Menang: " + str(skor.menang)
print "Kalah: " + str(skor.kalah)
print "Seri: " + str(skor.seri)
