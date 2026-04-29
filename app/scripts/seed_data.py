"""
seed_data.py — Populate dataset awal.

Script ini memvalidasi dan menampilkan statistik dataset
yang sudah ada di folder data/.

Usage:
    python scripts/seed_data.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def validate_dataset(filename: str, required_fields: list[str]):
    """Validate dataset dan tampilkan statistik."""
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n📁 {filename}")
    print(f"   Total entries: {len(data)}")

    # Check required fields
    missing = []
    for i, item in enumerate(data):
        for field in required_fields:
            if field not in item:
                missing.append(f"   ⚠️  Entry {i}: missing '{field}'")

    if missing:
        for m in missing[:5]:
            print(m)
        if len(missing) > 5:
            print(f"   ... and {len(missing) - 5} more")
    else:
        print("   ✅ All required fields present")

    # Statistik
    if "rating" in required_fields:
        ratings = [item.get("rating", 0) for item in data]
        print(f"   Rating: min={min(ratings)}, max={max(ratings)}, avg={sum(ratings)/len(ratings):.2f}")

    # Kategori breakdown
    categories = {}
    for item in data:
        cat = item.get("kategori", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    if categories:
        print(f"   Kategori: {dict(sorted(categories.items()))}")


def main():
    print("🌱 Validating datasets...\n")

    validate_dataset("wisata.json", ["id", "nama", "kategori", "harga_tiket", "lat", "lng", "rating"])
    validate_dataset("hotel.json", ["id", "nama", "kategori", "harga_per_malam", "lat", "lng", "rating"])
    validate_dataset("kuliner.json", ["id", "nama", "kategori", "harga_per_orang", "rating"])

    print("\n🎉 Validation complete!")


if __name__ == "__main__":
    main()
