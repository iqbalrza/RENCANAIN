"""
precompute_jarak.py — Hitung & simpan jarak_matrix.json.

Pre-compute jarak Haversine antara semua pasangan destinasi
untuk mempercepat query saat runtime.

Usage:
    python scripts/precompute_jarak.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.haversine import haversine

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_all_locations() -> list[dict]:
    """Load semua lokasi dari wisata, hotel, dan kuliner."""
    locations = []
    for filename in ["wisata.json", "hotel.json", "kuliner.json"]:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                locations.append({
                    "id": item.get("id", item.get("nama")),
                    "nama": item.get("nama", ""),
                    "lat": item.get("lat", 0),
                    "lng": item.get("lng", 0),
                    "tipe": filename.replace(".json", ""),
                })
    return locations


def compute_matrix(locations: list[dict]) -> dict:
    """Compute pairwise distance matrix."""
    matrix = {}
    total = len(locations)

    for i, loc_a in enumerate(locations):
        id_a = loc_a["id"]
        matrix[id_a] = {}
        for j, loc_b in enumerate(locations):
            if i == j:
                continue
            id_b = loc_b["id"]
            dist = haversine(loc_a["lat"], loc_a["lng"], loc_b["lat"], loc_b["lng"])
            matrix[id_a][id_b] = round(dist, 3)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{total} locations...")

    return matrix


def main():
    print("📐 Pre-computing distance matrix...\n")

    locations = load_all_locations()
    print(f"📍 Found {len(locations)} locations\n")

    matrix = compute_matrix(locations)

    output_path = os.path.join(DATA_DIR, "jarak_matrix.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Distance matrix saved to {output_path}")
    print(f"   Total pairs: {sum(len(v) for v in matrix.values())}")


if __name__ == "__main__":
    main()
