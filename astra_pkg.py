#!/usr/bin/env python3
"""
AstraLang Package Manager (v0.5) — astra_pkg.py
==================================================
Package manager LOKAL untuk AstraLang. Tidak ada registry online (tidak ada
server pusat seperti npm/PyPI) — package diinstal dari:
- folder lokal berisi file .as, atau
- file .zip lokal berisi file .as

Package yang terinstal disalin ke folder `astra_packages/<nama>/` di
direktori kerja saat ini. Untuk memakai isi package, program .as memanggil
read_file() secara manual ke path di dalam astra_packages/ -- AstraLang
BELUM punya sistem `import` sungguhan (baru direncanakan roadmap
mendatang), jadi package manager ini murni mengelola PENYIMPANAN & METADATA
package, bukan mengintegrasikannya otomatis ke bahasa.

Cara pakai:
    python3 astra_pkg.py install <path_ke_folder_atau_zip> [--name nama_package]
    python3 astra_pkg.py remove <nama_package>
    python3 astra_pkg.py list
"""

import sys
import os
import shutil
import zipfile
import json

PACKAGES_DIR = "astra_packages"
MANIFEST_FILE = "astra_packages.json"


def _load_manifest():
    if not os.path.isfile(MANIFEST_FILE):
        return {"packages": {}}
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(manifest):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def _infer_package_name(source_path):
    base = os.path.basename(source_path.rstrip("/\\"))
    if base.endswith(".zip"):
        base = base[:-4]
    return base


def install(source_path, name=None):
    if not os.path.exists(source_path):
        print(f"Error: sumber package tidak ditemukan: {source_path}", file=sys.stderr)
        return 1

    package_name = name or _infer_package_name(source_path)
    os.makedirs(PACKAGES_DIR, exist_ok=True)
    dest_path = os.path.join(PACKAGES_DIR, package_name)

    if os.path.exists(dest_path):
        print(f"Error: package '{package_name}' sudah terinstal. Jalankan 'remove' dulu untuk menimpa.", file=sys.stderr)
        return 1

    file_count = 0
    if os.path.isdir(source_path):
        shutil.copytree(source_path, dest_path)
        file_count = sum(len(files) for _, _, files in os.walk(dest_path))
    elif source_path.endswith(".zip") and zipfile.is_zipfile(source_path):
        os.makedirs(dest_path)
        with zipfile.ZipFile(source_path, "r") as zf:
            zf.extractall(dest_path)
            file_count = len(zf.namelist())
    else:
        print(f"Error: sumber package harus berupa folder atau file .zip, dapat: {source_path}", file=sys.stderr)
        return 1

    as_files = []
    for root, _, files in os.walk(dest_path):
        for fname in files:
            if fname.endswith(".as"):
                rel = os.path.relpath(os.path.join(root, fname), dest_path)
                as_files.append(rel)

    manifest = _load_manifest()
    manifest["packages"][package_name] = {
        "source": source_path,
        "path": dest_path,
        "as_files": as_files,
    }
    _save_manifest(manifest)

    print(f"Package '{package_name}' terinstal di {dest_path}")
    print(f"  {file_count} file disalin, {len(as_files)} di antaranya file .as:")
    for f in as_files:
        print(f"    - {f}")
    print()
    print("Catatan: AstraLang belum punya sistem 'import' otomatis.")
    print(f"Untuk memakai isi package, panggil read_file() ke path di dalam '{dest_path}/' secara manual dari script .as kamu.")
    return 0


def remove(package_name):
    manifest = _load_manifest()
    if package_name not in manifest["packages"]:
        print(f"Error: package '{package_name}' tidak terinstal.", file=sys.stderr)
        return 1

    dest_path = manifest["packages"][package_name]["path"]
    if os.path.isdir(dest_path):
        shutil.rmtree(dest_path)

    del manifest["packages"][package_name]
    _save_manifest(manifest)

    print(f"Package '{package_name}' telah dihapus.")
    return 0


def list_packages():
    manifest = _load_manifest()
    packages = manifest["packages"]
    if not packages:
        print("Belum ada package yang terinstal.")
        return 0

    print(f"Package terinstal ({len(packages)}):")
    for name, info in packages.items():
        print(f"  - {name}  (dari: {info['source']}, {len(info['as_files'])} file .as)")
    return 0


def print_usage():
    print("AstraLang Package Manager (astra_pkg.py)")
    print()
    print("Cara pakai:")
    print("  python3 astra_pkg.py install <path_folder_atau_zip> [--name nama]")
    print("  python3 astra_pkg.py remove <nama_package>")
    print("  python3 astra_pkg.py list")
    print()
    print("Catatan: ini package manager LOKAL (install dari folder/zip di")
    print("komputer sendiri). Tidak ada registry online seperti npm/PyPI.")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print_usage()
        return 0

    command = args[0]
    if command == "install":
        if len(args) < 2:
            print("Error: 'install' membutuhkan path ke folder atau file .zip", file=sys.stderr)
            return 1
        source_path = args[1]
        name = None
        if "--name" in args:
            idx = args.index("--name")
            if idx + 1 >= len(args):
                print("Error: --name membutuhkan sebuah nilai", file=sys.stderr)
                return 1
            name = args[idx + 1]
        return install(source_path, name=name)
    elif command == "remove":
        if len(args) < 2:
            print("Error: 'remove' membutuhkan nama package", file=sys.stderr)
            return 1
        return remove(args[1])
    elif command == "list":
        return list_packages()
    else:
        print(f"Error: perintah tidak dikenal: {command}", file=sys.stderr)
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
