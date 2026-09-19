"""
Test Runner Utama AstraLang
==============================
Menjalankan semua file test di folder tests/ secara berurutan.

Cara jalankan:
    python3 tests/run_all.py
"""

import sys
import os
import subprocess

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_FILES = [
    "test_v0_1_regression.py",
    "test_v0_3_features.py",
    "test_v0_3_custom_type.py",
    "test_v0_4_web.py",
    "test_v0_4_beginner_friendly.py",
    "test_v0_4_list_ops.py",
    "test_v0_5_features.py",
]


def main():
    overall_failed = False
    for test_file in TEST_FILES:
        path = os.path.join(TESTS_DIR, test_file)
        print(f"\n>>> Menjalankan {test_file} ...\n")
        result = subprocess.run([sys.executable, path])
        if result.returncode != 0:
            overall_failed = True
            print(f"\n!!! {test_file} GAGAL (exit code {result.returncode}) !!!\n")

    print("\n" + "=" * 60)
    if overall_failed:
        print("RINGKASAN: ADA TEST YANG GAGAL")
        print("=" * 60)
        return 1
    else:
        print("RINGKASAN: SEMUA TEST LULUS")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
