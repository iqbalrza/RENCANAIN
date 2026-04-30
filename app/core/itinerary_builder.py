"""
itinerary_builder.py — Susun slot waktu per hari.

PERUBAHAN UTAMA (RAG Integration):
- Sebelumnya: load_json() langsung dari file
- Sekarang:   retrieve_for_itinerary() → Azure AI Search (atau fallback lokal)

Alur RAG:
  1. retrieve_for_itinerary() query Azure Search dengan filter budget + preferensi
  2. Hasil retrieval dipakai sebagai kandidat wisata, hotel, kuliner
  3. Core algorithm (Nearest Neighbor, budget check) tetap berjalan di atas hasil retrieval
"""

from core.budget_allocator import allocate_budget, get_budget_per_day
from core.haversine import nearest_neighbor_route, haversine
from config import BANDUNG_LAT, BANDUNG_LNG

# Import fungsi RAG retrieval dari search_service
from services.search_service import retrieve_for_itinerary


def filter_wisata_by_preferensi(wisata_list: list[dict],
                                 preferensi: list[str]) -> list[dict]:
    """
    Post-filter wisata berdasarkan preferensi user.
    Dipakai sebagai second-pass filter setelah retrieval dari Azure Search.
    Jika hasil terlalu sedikit, kembalikan semua tanpa filter.
    """
    pref_lower = [p.lower() for p in preferensi]
    filtered = [
        w for w in wisata_list
        if w.get("kategori", "").lower() in pref_lower
        or any(t.lower() in pref_lower for t in w.get("tags", []))
    ]
    # Jika terlalu sedikit, kembalikan semua hasil retrieval
    return filtered if len(filtered) >= 3 else wisata_list


def select_hotel(hotel_list: list[dict], budget_per_malam: int,
                 center_lat: float = None, center_lng: float = None) -> dict | None:
    """
    Pilih hotel terbaik dari hasil retrieval.
    Prioritas: dekat centroid destinasi → harga mendekati budget → rating.
    """
    if not hotel_list:
        return None

    # Hotel sudah difilter budget oleh Azure Search,
    # tapi kita post-filter lagi untuk keamanan
    affordable = [h for h in hotel_list if h.get("harga_per_malam", 0) <= budget_per_malam]
    if not affordable:
        affordable = sorted(hotel_list, key=lambda h: h.get("harga_per_malam", 0))[:5]

    if center_lat is not None and center_lng is not None:
        return min(
            affordable,
            key=lambda h: (
                haversine(center_lat, center_lng,
                          h.get("lat", BANDUNG_LAT), h.get("lng", BANDUNG_LNG)),
                -(h.get("harga_per_malam", 0) / max(budget_per_malam, 1)),
                -h.get("rating", 0),
            ),
        )

    return max(affordable, key=lambda h: (h.get("harga_per_malam", 0), h.get("rating", 0)))


def build_itinerary(kota_asal: str, durasi: int, jumlah_orang: int,
                     budget: int, preferensi: list[str]) -> dict:
    """
    Bangun itinerary lengkap dari input form.

    Pipeline:
        1. allocate_budget()            → hitung alokasi per kategori
        2. retrieve_for_itinerary()     → RAG: query Azure Search
        3. filter_wisata_by_preferensi()→ post-filter preferensi user
        4. nearest_neighbor_route()     → optimasi urutan kunjungan (TSP)
        5. select_hotel()               → pilih hotel terbaik dari kandidat
        6. susun kuliner per hari       → prioritas: dekat destinasi + budget
        7. hitung estimasi biaya        → ringkasan akhir

    Returns:
        dict berisi ringkasan, alokasi_budget, hotel,
        itinerary_per_hari, wisata_terpilih, estimasi_biaya
    """
    # ── 1. Budget allocation ─────────────────────────────────
    alokasi = allocate_budget(budget)
    per_hari = get_budget_per_day(alokasi, durasi)

    # Hitung budget per parameter untuk retrieval
    wisata_per_hari = 3
    jumlah_wisata_needed = wisata_per_hari * durasi

    # Budget tiket wisata per orang (total semua hari)
    budget_wisata_per_orang = alokasi["wisata"] // max(jumlah_orang, 1)

    # Budget kuliner per orang per sekali makan
    budget_kuliner_per_meal = (
        per_hari["kuliner_per_hari"] // (3 * max(jumlah_orang, 1))
    )

    budget_hotel_per_malam = per_hari["hotel_per_malam"]

    # ── 2. RAG: Retrieve dari Azure AI Search ────────────────
    retrieved = retrieve_for_itinerary(
        preferensi=preferensi,
        budget_wisata_per_orang=budget_wisata_per_orang,
        budget_kuliner_per_orang_per_meal=budget_kuliner_per_meal,
        budget_hotel_per_malam=budget_hotel_per_malam,
        jumlah_hari=durasi,
        jumlah_wisata_needed=jumlah_wisata_needed,
    )

    wisata_all = retrieved["wisata"]
    hotel_all  = retrieved["hotel"]
    kuliner_filtered = retrieved["kuliner"]

    # ── 3. Post-filter wisata by preferensi ──────────────────
    wisata_filtered = filter_wisata_by_preferensi(wisata_all, preferensi)

    # ── 4. Optimasi rute wisata (Nearest Neighbor TSP) ───────
    wisata_optimized = nearest_neighbor_route(
        list(wisata_filtered), BANDUNG_LAT, BANDUNG_LNG
    )

    # Batasi jumlah wisata & filter yang melebihi budget
    max_wisata = wisata_per_hari * durasi
    wisata_selected = wisata_optimized[:max_wisata]

    budget_wisata_total = alokasi["wisata"]
    total_tiket = 0
    wisata_final = []
    for w in wisata_selected:
        tiket = w.get("harga_tiket", 0) * jumlah_orang
        if total_tiket + tiket <= budget_wisata_total:
            wisata_final.append(w)
            total_tiket += tiket
        elif w.get("harga_tiket", 0) == 0:
            wisata_final.append(w)

    # ── 5. Pilih hotel ───────────────────────────────────────
    if wisata_final:
        dest_center_lat = sum(w.get("lat", BANDUNG_LAT) for w in wisata_final) / len(wisata_final)
        dest_center_lng = sum(w.get("lng", BANDUNG_LNG) for w in wisata_final) / len(wisata_final)
    else:
        dest_center_lat, dest_center_lng = BANDUNG_LAT, BANDUNG_LNG

    hotel = select_hotel(
        hotel_all,
        budget_hotel_per_malam,
        dest_center_lat,
        dest_center_lng,
    )

    # ── 6. Susun itinerary per hari ──────────────────────────
    itinerary_per_hari = []
    wisata_idx = 0
    kuliner_used = set()

    for day in range(1, durasi + 1):
        day_plan = {"hari": day, "destinasi": [], "kuliner": []}

        # Alokasi wisata per hari
        day_destinations = []
        for _ in range(wisata_per_hari):
            if wisata_idx < len(wisata_final):
                dest = wisata_final[wisata_idx]
                jarak_info = ""
                if wisata_idx > 0:
                    prev = wisata_final[wisata_idx - 1]
                    jarak = haversine(
                        prev.get("lat", BANDUNG_LAT), prev.get("lng", BANDUNG_LNG),
                        dest.get("lat", BANDUNG_LAT), dest.get("lng", BANDUNG_LNG),
                    )
                    jarak_info = f"{jarak:.1f} km dari destinasi sebelumnya"
                day_plan["destinasi"].append({**dest, "jarak_info": jarak_info})
                day_destinations.append(dest)
                wisata_idx += 1

        # Centroid destinasi hari ini → titik acuan kuliner terdekat
        if day_destinations:
            center_lat = sum(d.get("lat", BANDUNG_LAT) for d in day_destinations) / len(day_destinations)
            center_lng = sum(d.get("lng", BANDUNG_LNG) for d in day_destinations) / len(day_destinations)
        else:
            center_lat, center_lng = BANDUNG_LAT, BANDUNG_LNG

        # Alokasi kuliner: dekat destinasi + harga mendekati budget (maksimalkan utilisasi)
        for meal_name in ["Sarapan", "Makan Siang", "Makan Malam"]:
            available = [
                (i, k) for i, k in enumerate(kuliner_filtered)
                if i not in kuliner_used
            ]
            if not available:
                # Semua kuliner sudah dipakai, reset (rotasi)
                kuliner_used.clear()
                available = list(enumerate(kuliner_filtered))

            if available:
                available.sort(
                    key=lambda x: (
                        haversine(
                            center_lat, center_lng,
                            x[1].get("lat", BANDUNG_LAT), x[1].get("lng", BANDUNG_LNG),
                        ),
                        -x[1].get("harga_per_orang", 0),
                    )
                )
                nearest_3 = available[:3]
                nearest_3.sort(key=lambda x: -x[1].get("harga_per_orang", 0))
                idx, k = nearest_3[0]
                kuliner_used.add(idx)
                day_plan["kuliner"].append({
                    **k,
                    "waktu_makan": meal_name,
                    "total_biaya": k.get("harga_per_orang", 0) * jumlah_orang,
                })

        itinerary_per_hari.append(day_plan)

    # ── 7. Estimasi biaya ────────────────────────────────────
    total_hotel = (hotel.get("harga_per_malam", 0) * durasi) if hotel else 0
    total_wisata_biaya = sum(
        w.get("harga_tiket", 0) * jumlah_orang for w in wisata_final
    )
    total_kuliner_biaya = sum(
        meal.get("total_biaya", 0)
        for day in itinerary_per_hari
        for meal in day["kuliner"]
    )
    total_transport_est = alokasi["transport"]

    total_semua = total_hotel + total_wisata_biaya + total_kuliner_biaya + total_transport_est
    estimasi = {
        "hotel": total_hotel,
        "wisata": total_wisata_biaya,
        "kuliner": total_kuliner_biaya,
        "transport": total_transport_est,
        "total": total_semua,
        "sisa_budget": budget - total_semua,
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