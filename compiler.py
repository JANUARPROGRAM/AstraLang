#!/usr/bin/env python3
"""
AstraLang Compiler/Runner - Entry Point (v0.5.0)
==================================================
Ini adalah titik masuk (CLI) untuk menjalankan program AstraLang (.as).

"compiler.py" sebenarnya berperan sebagai INTERPRETER RUNNER (bukan compiler
ke native code) — source dibaca -> lexer -> parser -> interpreter dijalankan
langsung. Nama "compiler.py" dipertahankan sebagai entry point resmi karena
roadmap versi mendatang akan menambahkan tahap kompilasi sungguhan (mis. ke
bytecode) tanpa mengubah cara pemakaian dari sisi user.

Catatan versi:
v0.2.1 sempat menambahkan modul "Astra Device Bridge" (device naming,
discovery jaringan, dashboard web, kontrol device). Modul tersebut DIHAPUS
TOTAL atas permintaan eksplisit, dan project dikembalikan ke fondasi bahasa
v0.1 murni sebagai basis pengembangan v0.3 ke atas (type system, web, dst
— lihat CHANGELOG.md).

v0.4 menambahkan opsi --lang untuk menampilkan pesan error dalam Bahasa
Inggris (pesan tetap DITULIS dalam Bahasa Indonesia di source code sebagai
bahasa kanonik, lalu diterjemahkan saat ditampilkan lewat modul i18n.py).

v0.5 menambahkan opsi --debug: menampilkan waktu eksekusi tiap tahap
(lexer/parser/interpreter) dan traceback Python asli di bawah pesan error
normal (bukan menggantikannya) untuk membantu development AstraLang sendiri.

Cara pakai:
    python3 compiler.py <file.as>
    python3 compiler.py <file.as> --lang en
    python3 compiler.py <file.as> --debug
    python3 compiler.py --version
"""

import sys
import os
import time
import traceback

from lexer import Lexer, LexerError
from parser import Parser, ParserError
from interpreter import Interpreter
from runtime import AstraRuntimeError
from i18n import translate, normalize_lang

VERSION = "0.5.0"


def print_error_box(title, message, location=None, hint=None, lang="id"):
    """
    v0.3: format error terstruktur — judul, pesan, lokasi, dan saran perbaikan
    (hint) bila tersedia, supaya error message tidak cuma bilang "salah" tapi
    juga membantu penyebab & cara memperbaikinya.
    v0.4: menerima parameter `lang` ("id"/"en") untuk menerjemahkan tampilan
    lewat modul i18n.py. Pesan sumber selalu Bahasa Indonesia; terjemahan
    hanya diterapkan di titik tampilan ini.
    """
    print(f"\n{translate(title, lang)}", file=sys.stderr)
    print(f"  {translate(message, lang)}", file=sys.stderr)
    if location:
        print(f"  {translate('Lokasi:', lang)} {location}", file=sys.stderr)
    if hint:
        print(f"  {translate('Saran:', lang)} {translate(hint, lang)}", file=sys.stderr)


def run_file(path: str, lang: str = "id", debug: bool = False) -> int:
    lang = normalize_lang(lang)

    if not os.path.isfile(path):
        not_found_msg = translate("File tidak ditemukan", lang)
        print(f"Error: {not_found_msg}: {path}", file=sys.stderr)
        return 1

    if not path.endswith(".as"):
        warning = translate(
            f"Peringatan: File '{path}' tidak memakai ekstensi '.as'. "
            "Melanjutkan tetap mencoba menjalankan...",
            lang,
        )
        print(warning, file=sys.stderr)

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    # --- Tahap 1: Lexing ---
    t0 = time.perf_counter()
    try:
        tokens = Lexer(source).tokenize()
    except LexerError as e:
        print_error_box(
            "Gagal membaca kode (Lexer Error):", e.message,
            location=f"{path}:{e.line}:{e.column}",
            lang=lang,
        )
        if debug:
            print("\n[DEBUG] Traceback Python asli:", file=sys.stderr)
            traceback.print_exc()
        return 1
    t1 = time.perf_counter()

    # --- Tahap 2: Parsing ---
    try:
        program = Parser(tokens).parse()
    except ParserError as e:
        print_error_box(
            "Struktur kode tidak valid (Parser Error):", e.message,
            location=f"{path}:{e.line}:{e.column}",
            hint=e.hint,
            lang=lang,
        )
        if debug:
            print("\n[DEBUG] Traceback Python asli:", file=sys.stderr)
            traceback.print_exc()
        return 1
    t2 = time.perf_counter()

    # --- Tahap 3: Interpretasi ---
    try:
        Interpreter().run(program)
    except AstraRuntimeError as e:
        line_info = f":{e.line}" if e.line is not None else ""
        print_error_box(
            "Terjadi error saat program berjalan (Runtime Error):", e.message,
            location=f"{path}{line_info}",
            hint=e.hint,
            lang=lang,
        )
        if debug:
            print("\n[DEBUG] Traceback Python asli:", file=sys.stderr)
            traceback.print_exc()
        return 1
    except RecursionError:
        print_error_box(
            "Runtime Error:",
            "Terlalu banyak pemanggilan fungsi bersarang (kemungkinan rekursi tak berhenti).",
            hint="Cek apakah ada fungsi rekursif yang tidak punya kondisi berhenti (base case)",
            lang=lang,
        )
        if debug:
            print("\n[DEBUG] Traceback Python asli:", file=sys.stderr)
            traceback.print_exc()
        return 1
    t3 = time.perf_counter()

    if debug:
        print("\n[DEBUG] Waktu eksekusi:", file=sys.stderr)
        print(f"  Lexer      : {(t1 - t0) * 1000:.3f} ms", file=sys.stderr)
        print(f"  Parser     : {(t2 - t1) * 1000:.3f} ms", file=sys.stderr)
        print(f"  Interpreter: {(t3 - t2) * 1000:.3f} ms", file=sys.stderr)
        print(f"  Total      : {(t3 - t0) * 1000:.3f} ms", file=sys.stderr)

    return 0


def print_usage():
    print("AstraLang - Bahasa Pemrograman Modern (Prototype)")
    print(f"Versi: {VERSION}")
    print()
    print("Cara pakai:")
    print("  python3 compiler.py <file.as>                Menjalankan file AstraLang")
    print("  python3 compiler.py <file.as> --lang en       Menjalankan dengan pesan error Bahasa Inggris")
    print("  python3 compiler.py <file.as> --debug         Menjalankan dengan mode debug (waktu eksekusi + traceback)")
    print("  python3 compiler.py --version                 Menampilkan versi")
    print("  python3 compiler.py --help                    Menampilkan bantuan ini")


def main():
    args = sys.argv[1:]

    if len(args) == 0 or args[0] in ("-h", "--help"):
        print_usage()
        return 0

    if args[0] in ("-v", "--version"):
        print(f"AstraLang v{VERSION}")
        return 0

    file_path = args[0]

    # -- Ditambahkan v0.4: parsing opsi --lang --
    # -- Ditambahkan v0.5: parsing opsi --debug --
    lang = "id"
    debug = False
    rest = args[1:]
    i = 0
    while i < len(rest):
        if rest[i] == "--lang":
            if i + 1 >= len(rest):
                print("Error: --lang membutuhkan sebuah nilai, mis. --lang en", file=sys.stderr)
                return 1
            lang = normalize_lang(rest[i + 1])
            i += 2
        elif rest[i] == "--debug":
            debug = True
            i += 1
        else:
            print(f"Peringatan: argumen tidak dikenal diabaikan: {rest[i]}", file=sys.stderr)
            i += 1

    return run_file(file_path, lang=lang, debug=debug)


if __name__ == "__main__":
    sys.exit(main())
