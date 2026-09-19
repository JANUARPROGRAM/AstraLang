# Contoh lebih kompleks: loop, rekursi, operasi matematika, logika

# --- Loop sederhana ---
let i = 1
while i <= 5 {
    print i
    i = i + 1
}

# --- Operasi matematika ---
let a = 10
let b = 3
print a + b
print a - b
print a * b
print a / b
print a % b

# --- Fungsi rekursif: faktorial ---
function faktorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * faktorial(n - 1)
    }
}
print faktorial(5)

# --- Logika and/or/not ---
let x = 7
if x > 5 and x < 10 {
    print "x di antara 5 dan 10"
}

if not (x > 100) {
    print "x tidak lebih dari 100"
}

# --- String concat & len() ---
let greeting = "Halo" + " " + "AstraLang"
print greeting
print len(greeting)
