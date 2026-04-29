"""
itinerary_builder.py — Susun slot waktu per hari.
"""

import json
import os
from core.budget_allocator import allocate_budget, get_budget_per_day
from core.haversine import nearest_neighbor_route, haversine
from config import BANDUNG_LAT, BANDUNG_LNG


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_json(filename: str) -> list[dict]:
    """Load JSON data dari folder data/."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_wisata_by_preferensi(wisata_list: list[dict],
                                 preferensi: list[str]) -> list[dict]:
    """Filter wisata berdasarkan preferensi user."""
    pref_lower = [p.lower() for p in preferensi]
    filtered = []
    for w in wisata_list:
        kategori = w.get("kategori", "").lower()
        tags = [t.lower() for t in w.get("tags", [])]
        if kategori in pref_lower or any(t in pref_lower for t in tags):
            filtered.append(w)
    return filtered


def filter_hotel_by_budget(hotel_list: list[dict],
                            budget_per_malam: int) -> list[dict]:
    """Filter hotel yang sesuai budget per malam."""
    return [h for h in hotel_list if h["harga_per_malam"] <= budget_per_malam]


def filter_kuliner_by_budget(kuliner_list: list[dict],
                              budget_per_orang_per_meal: int) -> list[dict]:
    """Filter kuliner yang sesuai budget per orang (dengan margin 20% agar budget lebih terpakai)."""
    margin = int(budget_per_orang_per_meal * 1.2)  # Beri margin 20%
    return [k for k in kuliner_list if k["harga_per_orang"] <= margin]


def select_hotel(hotel_list: list[dict], budget_per_malam: int,
                 center_lat: float = None, center_lng: float = None) -> dict | None:
    """
    Pilih hotel terbaik sesuai budget dan kedekatan dengan destinasi.

    Prioritas: budget → dekat centroid → harga mendekati budget (maksimalkan) → rating.
    """
    affordable = filter_hotel_by_budget(hotel_list, budget_per_malam)
    if not affordable:
        # Fallback: hotel termurah
        affordable = sorted(hotel_list, key=lambda h: h["harga_per_malam"])
        affordable = affordable[:5] if len(affordable) > 5 else affordable

    if not affordable:
        return None

    if center_lat is not None and center_lng is not None:
        # Pilih hotel: dekat destinasi + harga mendekati budget (agar sisa minim)
        return min(
            affordable,
            key=lambda h: (
                haversine(center_lat, center_lng, h["lat"], h["lng"]),
                -(h["harga_per_malam"] / budget_per_malam),  # Prefer harga mendekati budget
                -h["rating"],
            ),
        )

    # Tanpa lokasi: pilih harga tertinggi (mendekati budget) dengan rating terbaik
    return max(affordable, key=lambda h: (h["harga_per_malam"], h["rating"]))


def build_itinerary(kota_asal: str, durasi: int, jumlah_orang: int,
                     budget: int, preferensi: list[str]) -> dict:
    """
    Bangun itinerary lengkap dari input form.

    Returns dict berisi:
    - ringkasan, alokasi_budget, hotel, itinerary_per_hari, estimasi_biaya
    """
    # Load data
    wisata_all = load_json("wisata.json")
    hotel_all = load_json("hotel.json")
    kuliner_all = load_json("kuliner.json")

    # Budget allocation
    alokasi = allocate_budget(budget)
    per_hari = get_budget_per_day(alokasi, durasi)

    # Filter wisata by preferensi
    wisata_filtered = filter_wisata_by_preferensi(wisata_all, preferensi)
    if not wisata_filtered:
        wisata_filtered = wisata_all  # Fallback

    # Filter kuliner by budget (3 kali makan per hari)
    budget_per_meal = per_hari["kuliner_per_hari"] // (3 * jumlah_orang) if jumlah_orang > 0 else per_hari["kuliner_per_hari"] // 3
    kuliner_filtered = filter_kuliner_by_budget(kuliner_all, budget_per_meal)
    if not kuliner_filtered:
        kuliner_filtered = sorted(kuliner_all, key=lambda k: k["harga_per_orang"])[:10]

    # Optimasi rute wisata
    wisata_optimized = nearest_neighbor_route(
        list(wisata_filtered), BANDUNG_LAT, BANDUNG_LNG
    )

    # Batasi jumlah wisata per hari (2-3 per hari, tergantung durasi)
    wisata_per_hari = 3
    max_wisata = wisata_per_hari * durasi
    wisata_selected = wisata_optimized[:max_wisata]

    # Filter wisata yang terlalu mahal
    budget_wisata_total = alokasi["wisata"]
    total_tiket = 0
    wisata_final = []
    for w in wisata_selected:
        tiket = w["harga_tiket"] * jumlah_orang
        if total_tiket + tiket <= budget_wisata_total:
            wisata_final.append(w)
            total_tiket += tiket
        elif w["harga_tiket"] == 0:
            wisata_final.append(w)

    # Hitung centroid semua destinasi → pilih hotel terdekat
    if wisata_final:
        dest_center_lat = sum(w["lat"] for w in wisata_final) / len(wisata_final)
        dest_center_lng = sum(w["lng"] for w in wisata_final) / len(wisata_final)
    else:
        dest_center_lat, dest_center_lng = BANDUNG_LAT, BANDUNG_LNG

    hotel = select_hotel(hotel_all, per_hari["hotel_per_malam"],
                         dest_center_lat, dest_center_lng)

    # Susun itinerary per hari
    itinerary_per_hari = []
    wisata_idx = 0
    kuliner_used = set()  # Track kuliner yang sudah dipakai

    for day in range(1, durasi + 1):
        day_plan = {
            "hari": day,
            "destinasi": [],
            "kuliner": [],
        }

        # Alokasi wisata per hari
        day_destinations = []
        for _ in range(wisata_per_hari):
            if wisata_idx < len(wisata_final):
                dest = wisata_final[wisata_idx]
                jarak_info = ""
                if wisata_idx > 0:
                    prev = wisata_final[wisata_idx - 1]
                    jarak = haversine(prev["lat"], prev["lng"], dest["lat"], dest["lng"])
                    jarak_info = f"{jarak:.1f} km dari destinasi sebelumnya"
                day_plan["destinasi"].append({
                    **dest,
                    "jarak_info": jarak_info,
                })
                day_destinations.append(dest)
                wisata_idx += 1

        # Hitung centroid (titik tengah) destinasi hari ini
        if day_destinations:
            center_lat = sum(d["lat"] for d in day_destinations) / len(day_destinations)
            center_lng = sum(d["lng"] for d in day_destinations) / len(day_destinations)
        else:
            center_lat, center_lng = BANDUNG_LAT, BANDUNG_LNG

        # Alokasi kuliner: dekat destinasi + harga mendekati budget (maksimalkan)
        meals = ["Sarapan", "Makan Siang", "Makan Malam"]
        for meal_name in meals:
            available = [
                (i, k) for i, k in enumerate(kuliner_filtered)
                if i not in kuliner_used
            ]
            if not available:
                kuliner_used.clear()
                available = list(enumerate(kuliner_filtered))

            if available:
                # Prioritas: dekat destinasi, lalu harga tinggi (agar budget terpakai)
                available.sort(
                    key=lambda x: (
                        haversine(center_lat, center_lng, x[1]["lat"], x[1]["lng"]),
                        -x[1]["harga_per_orang"],  # Prefer harga lebih tinggi
                    )
                )
                # Ambil dari 3 terdekat, pilih yang paling mahal
                nearest_3 = available[:3]
                nearest_3.sort(key=lambda x: -x[1]["harga_per_orang"])
                idx, k = nearest_3[0]
                kuliner_used.add(idx)
                day_plan["kuliner"].append({
                    **k,
                    "waktu_makan": meal_name,
                    "total_biaya": k["harga_per_orang"] * jumlah_orang,
                })

        itinerary_per_hari.append(day_plan)

    # Hitung estimasi biaya
    total_hotel = (hotel["harga_per_malam"] * durasi) if hotel else 0
    total_wisata_biaya = sum(w["harga_tiket"] * jumlah_orang for w in wisata_final)
    total_kuliner_biaya = sum(
        meal.get("total_biaya", 0)
        for day in itinerary_per_hari
        for meal in day["kuliner"]
    )
    total_transport_est = alokasi["transport"]

    estimasi = {
        "hotel": total_hotel,
        "wisata": total_wisata_biaya,
        "kuliner": total_kuliner_biaya,
        "transport": total_transport_est,
        "total": total_hotel + total_wisata_biaya + total_kuliner_biaya + total_transport_est,
        "sisa_budget": budget - (total_hotel + total_wisata_biaya + total_kuliner_biaya + total_transport_est),
    }

    return {
        "ringkasan": {
            "kota_asal": kota_asal,
            "tujuan": "Bandung",
            "durasi": durasi,
            "jumlah_orang": jumlah_orang,
            "budget": budget,
            "preferensi": preferensi,
        },
        "alokasi_budget": alokasi,
        "hotel": hotel,
        "itinerary_per_hari": itinerary_per_hari,
        "wisata_terpilih": wisata_final,
        "estimasi_biaya": estimasi,
    }
