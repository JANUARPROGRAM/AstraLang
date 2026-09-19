"""
Test Fitur Baru v0.4 Lanjutan: Operasi List Tambahan
========================================================
Menguji built-in List yang ditambahkan untuk mendukung skenario nyata
(leaderboard, game) yang ditemukan saat membuat contoh game AstraLang:
- sort(daftar) -- urutkan angka/string
- sort_by(daftar, fungsi_kunci) -- urutkan List custom type berdasarkan field
- reverse(daftar)
- contains(daftar, nilai)
- join(daftar, pemisah)
- slice(daftar, mulai, akhir)

Juga menguji refactor _call_astra_function (dipakai ulang oleh sort_by)
tidak mengubah perilaku pemanggilan function biasa.

Cara jalankan:
    python3 tests/test_v0_4_list_ops.py
"""

import sys
import os
import io
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import parse_source
from interpreter import Interpreter
from runtime import AstraRuntimeError

PASSED = 0
FAILED = 0


def check(name, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [OK] {name}")
    else:
        FAILED += 1
        print(f"  [GAGAL] {name}")


def run_and_capture(source):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        Interpreter().run(parse_source(source))
    return buf.getvalue()


def test_sort_numbers():
    print("Test: sort() angka")
    out = run_and_capture("print sort([5, 2, 8, 1, 9])")
    check("urutan angka benar", out.strip() == "[1, 2, 5, 8, 9]")


def test_sort_strings():
    print("Test: sort() string")
    out = run_and_capture('print sort(["banana", "apple", "cherry"])')
    check("urutan string benar (alfabetis)", out.strip() == "[apple, banana, cherry]")


def test_sort_does_not_mutate_original():
    print("Test: sort() tidak mengubah List asli (mengembalikan List baru)")
    out = run_and_capture('let a = [3, 1, 2]\nlet b = sort(a)\nprint a\nprint b\n')
    lines = out.strip().splitlines()
    check("list asli tidak berubah", lines[0] == "[3, 1, 2]")
    check("list hasil sort benar", lines[1] == "[1, 2, 3]")


def test_sort_mixed_types_rejected():
    print("Test: sort() menolak List dengan tipe campuran")
    try:
        run_and_capture('print sort([1, "a", 2])')
        check("tipe campuran ditolak", False)
    except AstraRuntimeError as e:
        check("tipe campuran ditolak", True)


def test_reverse():
    print("Test: reverse()")
    out = run_and_capture("print reverse([1, 2, 3])")
    check("urutan terbalik benar", out.strip() == "[3, 2, 1]")


def test_contains():
    print("Test: contains()")
    out = run_and_capture('print contains([1, 2, 3], 2)\nprint contains([1, 2, 3], 99)\n')
    lines = out.strip().splitlines()
    check("contains true untuk elemen yang ada", lines[0] == "true")
    check("contains false untuk elemen yang tidak ada", lines[1] == "false")


def test_join():
    print("Test: join()")
    out = run_and_capture('print join(["a", "b", "c"], "-")\nprint join([1, 2, 3], ", ")\n')
    lines = out.strip().splitlines()
    check("join string benar", lines[0] == "a-b-c")
    check("join angka (auto stringify) benar", lines[1] == "1, 2, 3")


def test_slice():
    print("Test: slice()")
    out = run_and_capture("print slice([1,2,3,4,5], 1, 3)")
    check("slice benar (index 1 sampai sebelum 3)", out.strip() == "[2, 3]")


def test_sort_by_with_custom_type():
    print("Test: sort_by() mengurutkan List custom type berdasarkan field")
    src = '''
type Pemain {
    nama
    skor
}
function ambil_skor(p) {
    return p.skor
}
let daftar = [
    Pemain { nama: "A", skor: 50 },
    Pemain { nama: "B", skor: 90 },
    Pemain { nama: "C", skor: 20 }
]
let terurut = sort_by(daftar, ambil_skor)
let i = 0
while i < len(terurut) {
    print terurut[i].nama
    i = i + 1
}
'''
    out = run_and_capture(src)
    check("urutan sort_by benar (naik berdasarkan skor)", out.strip().splitlines() == ["C", "A", "B"])


def test_sort_by_rejects_non_function():
    print("Test: sort_by() menolak argumen kedua yang bukan function")
    try:
        run_and_capture("print sort_by([1,2,3], 5)")
        check("sort_by menolak non-function", False)
    except AstraRuntimeError as e:
        check("sort_by menolak non-function", True)
        check("hint memberi contoh pemakaian", "sort_by" in e.hint)


def test_sort_by_rejects_wrong_arity():
    print("Test: sort_by() menolak fungsi kunci dengan jumlah parameter salah")
    try:
        run_and_capture('function dua_param(a, b) { return a }\nprint sort_by([1,2,3], dua_param)\n')
        check("sort_by menolak arity salah", False)
    except AstraRuntimeError as e:
        check("sort_by menolak arity salah", True)


def test_leaderboard_scenario_end_to_end():
    print("Test: skenario leaderboard lengkap (sort_by + reverse untuk urutan turun)")
    src = '''
type Pemain {
    nama
    skor
}
function ambil_skor(p) {
    return p.skor
}
let daftar = [
    Pemain { nama: "Astra", skor: 87 },
    Pemain { nama: "Budi", skor: 95 },
    Pemain { nama: "Citra", skor: 72 }
]
let terurut_naik = sort_by(daftar, ambil_skor)
let terurut_turun = reverse(terurut_naik)
let i = 0
while i < len(terurut_turun) {
    print str(i + 1) + ". " + terurut_turun[i].nama + " - " + str(terurut_turun[i].skor)
    i = i + 1
}
'''
    out = run_and_capture(src)
    expected = ["1. Budi - 95", "2. Astra - 87", "3. Citra - 72"]
    check("leaderboard terurut turun benar", out.strip().splitlines() == expected)


def test_regular_function_calls_still_work_after_refactor():
    print("Test: pemanggilan function biasa tetap benar setelah refactor _call_astra_function")
    src = '''
function faktorial(n) {
    if n <= 1 {
        return 1
    } else {
        return n * faktorial(n - 1)
    }
}
function tanpa_return() {
    let x = 1
}
print faktorial(6)
print tanpa_return()
'''
    out = run_and_capture(src)
    lines = out.strip().splitlines()
    check("rekursi tetap benar setelah refactor", lines[0] == "720")
    check("function tanpa return tetap null", lines[1] == "null")


def test_regression_full():
    print("Test: regresi total v0.1/v0.3/v0.4 tetap benar")
    src = '''
let daftar = [3, 1, 2]
let terurut = sort(daftar)
print terurut
print faktorial_helper(5)
'''
    src_full = '''
function faktorial_helper(n) {
    if n <= 1 {
        return 1
    } else {
        return n * faktorial_helper(n - 1)
    }
}
''' + src
    out = run_and_capture(src_full)
    lines = out.strip().splitlines()
    check("list sort tetap benar", lines[0] == "[1, 2, 3]")
    check("faktorial tetap benar", lines[1] == "120")


def main():
    print("=" * 60)
    print("MENJALANKAN TEST: OPERASI LIST TAMBAHAN (v0.4 lanjutan)")
    print("=" * 60)

    test_sort_numbers()
    test_sort_strings()
    test_sort_does_not_mutate_original()
    test_sort_mixed_types_rejected()
    test_reverse()
    test_contains()
    test_join()
    test_slice()
    test_sort_by_with_custom_type()
    test_sort_by_rejects_non_function()
    test_sort_by_rejects_wrong_arity()
    test_leaderboard_scenario_end_to_end()
    test_regular_function_calls_still_work_after_refactor()
    test_regression_full()

    print("=" * 60)
    print(f"HASIL: {PASSED} lulus, {FAILED} gagal")
    print("=" * 60)
    return 1 if FAILED > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
