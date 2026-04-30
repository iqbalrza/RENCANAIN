"""
grounding.py — RAG pipeline: Retrieve context → build grounded system prompt.

Peran dalam pipeline:
  1. Terima itinerary_data (hasil build_itinerary)
  2. Gunakan Azure AI Search untuk retrieve dokumen relevan
  3. Format context documents
  4. Build system prompt dengan grounding strategy anti-halusinasi

Dipakai oleh openai_service.generate_narrative() agar GPT-4o
hanya berhalusinasi berdasarkan data yang sudah diambil dari Azure Search,
bukan dari training knowledge yang mungkin sudah outdated.
"""

from services.search_service import search_wisata, search_hotel, search_kuliner
from utils.logger import get_logger

logger = get_logger(__name__)


def build_context_from_itinerary(itinerary_data: dict) -> str:
    """
    Build context documents dari itinerary yang sudah terbentuk.

    Strategi: retrieve dokumen dari Azure Search menggunakan nama-nama
    destinasi, hotel, dan kuliner yang sudah dipilih oleh itinerary_builder.
    Ini memastikan LLM mendapat informasi detail (deskripsi, fasilitas, dll)
    yang mungkin tidak tersimpan penuh di itinerary_data.

    Args:
        itinerary_data: output dari build_itinerary()

    Returns:
        string context documents siap di-inject ke system prompt
    """
    ringkasan = itinerary_data.get("ringkasan", {})
    hotel_data = itinerary_data.get("hotel", {})
    days = itinerary_data.get("itinerary_per_hari", [])
    preferensi = ringkasan.get("preferensi", ["Alam"])

    context_parts = []

    # ── Section 1: Destinasi wisata yang terpilih ────────────
    dest_names = []
    for day in days:
        for dest in day.get("destinasi", []):
            dest_names.append(dest.get("nama", ""))

    if dest_names:
        # Query ke Azure Search dengan nama destinasi yang terpilih
        wisata_query = " ".join(preferensi) + " " + " ".join(dest_names[:3])
        wisata_docs = search_wisata(wisata_query, top=len(dest_names) + 5)

        # Index by nama untuk lookup cepat
        wisata_index = {w.get("nama", "").lower(): w for w in wisata_docs}

        context_parts.append("=== DESTINASI WISATA TERPILIH ===")
        for day in days:
            context_parts.append(f"\n[Hari {day.get('hari', 1)}]")
            for dest in day.get("destinasi", []):
                nama = dest.get("nama", "")
                # Cari detail lengkap dari Azure Search
                detail = wisata_index.get(nama.lower(), dest)
                context_parts.append(
                    f"• {nama} ({detail.get('kategori', '-')})\n"
                    f"  {detail.get('deskripsi', '')}\n"
                    f"  📍 {detail.get('alamat', '-')}\n"
                    f"  🎫 Rp {int(detail.get('harga_tiket', 0)):,}/orang  "
                    f"⏰ {detail.get('jam_operasional', '-')}  "
                    f"⭐ {detail.get('rating', 0)}\n"
                    f"  ⏱️ Estimasi kunjungan: {detail.get('durasi_kunjungan_menit', 60)} menit"
                )

    # ── Section 2: Hotel yang terpilih ───────────────────────
    if hotel_data:
        nama_hotel = hotel_data.get("nama", "")
        hotel_docs = search_hotel(nama_hotel, top=3, max_harga_malam=hotel_data.get("harga_per_malam", 9999999))
        hotel_detail = next(
            (h for h in hotel_docs if h.get("nama", "").lower() == nama_hotel.lower()),
            hotel_data,
        )

        durasi = ringkasan.get("durasi", 1)
        total_hotel = hotel_detail.get("harga_per_malam", 0) * durasi
        fasilitas = " · ".join(hotel_detail.get("fasilitas", []))

        context_parts.append("\n=== HOTEL / AKOMODASI ===")
        context_parts.append(
            f"• {nama_hotel} ({hotel_detail.get('kategori', '-')})\n"
            f"  {hotel_detail.get('deskripsi', '')}\n"
            f"  📍 {hotel_detail.get('alamat', '-')}\n"
            f"  💰 Rp {int(hotel_detail.get('harga_per_malam', 0)):,}/malam  "
            f"(Total {durasi} malam: Rp {int(total_hotel):,})\n"
            f"  ⭐ {hotel_detail.get('rating', 0)}\n"
            f"  🏷️ Fasilitas: {fasilitas}"
        )

    # ── Section 3: Kuliner yang terpilih ─────────────────────
    kuliner_names = []
    for day in days:
        for meal in day.get("kuliner", []):
            kuliner_names.append(meal.get("nama", ""))

    if kuliner_names:
        kuliner_query = "bandung kuliner " + " ".join(preferensi).lower()
        kuliner_docs = search_kuliner(kuliner_query, top=len(kuliner_names) + 5)
        kuliner_index = {k.get("nama", "").lower(): k for k in kuliner_docs}

        context_parts.append("\n=== REKOMENDASI KULINER ===")
        for day in days:
            context_parts.append(f"\n[Hari {day.get('hari', 1)}]")
            for meal in day.get("kuliner", []):
                nama = meal.get("nama", "")
                detail = kuliner_index.get(nama.lower(), meal)
                context_parts.append(
                    f"• {meal.get('waktu_makan', '')} — {nama} ({detail.get('kategori', '-')})\n"
                    f"  {detail.get('deskripsi', '')}\n"
                    f"  📍 {detail.get('alamat', '-')}\n"
                    f"  💰 Rp {int(detail.get('harga_per_orang', 0)):,}/orang  "
                    f"⏰ {detail.get('jam_operasional', '-')}"
                )

    # ── Section 4: Info perjalanan ───────────────────────────
    estimasi = itinerary_data.get("estimasi_biaya", {})
    context_parts.append("\n=== RINGKASAN PERJALANAN ===")
    context_parts.append(
        f"Dari: {ringkasan.get('kota_asal', '-')} → Bandung\n"
        f"Durasi: {ringkasan.get('durasi', 1)} hari\n"
        f"Rombongan: {ringkasan.get('jumlah_orang', 1)} orang\n"
        f"Total Budget: Rp {int(ringkasan.get('budget', 0)):,}\n"
        f"Estimasi Pengeluaran: Rp {int(estimasi.get('total', 0)):,}\n"
        f"Sisa: Rp {int(estimasi.get('sisa_budget', 0)):,}\n"
        f"Preferensi: {', '.join(preferensi)}"
    )

    context = "\n".join(context_parts)
    logger.debug(f"Grounding context: {len(context)} chars")
    return context


def build_context_documents(intent: dict, form_data: dict) -> str:
    """
    (Backward-compatible) Build context dari intent + form_data.
    Dipakai saat itinerary belum terbentuk (pre-generation).
    """
    context_parts = []

    queries = intent.get("search_queries", form_data.get("preferensi", ["wisata"]))
    wisata_results = []
    seen_ids: set = set()

    for q in queries:
        for w in search_wisata(q, top=5):
            wid = w.get("id", w.get("nama"))
            if wid not in seen_ids:
                seen_ids.add(wid)
                wisata_results.append(w)

    if wisata_results:
        context_parts.append("=== DESTINASI WISATA BANDUNG ===")
        for w in wisata_results[:10]:
            context_parts.append(
                f"- {w['nama']} ({w.get('kategori', '-')}): "
                f"{w.get('deskripsi', '')} | "
                f"Tiket: Rp {int(w.get('harga_tiket', 0)):,} | "
                f"Jam: {w.get('jam_operasional', '-')} | "
                f"Rating: {w.get('rating', 0)}"
            )

    budget_cat = intent.get("budget_category", "budget")
    hotel_results = search_hotel(budget_cat, top=5)
    if hotel_results:
        context_parts.append("\n=== HOTEL & AKOMODASI ===")
        for h in hotel_results:
            context_parts.append(
                f"- {h['nama']} ({h.get('kategori', '-')}): "
                f"{h.get('deskripsi', '')} | "
                f"Harga: Rp {int(h.get('harga_per_malam', 0)):,}/malam | "
                f"Rating: {h.get('rating', 0)}"
            )

    kuliner_results = search_kuliner("bandung kuliner lokal", top=5)
    if kuliner_results:
        context_parts.append("\n=== KULINER LOKAL ===")
        for k in kuliner_results:
            context_parts.append(
                f"- {k['nama']} ({k.get('kategori', '-')}): "
                f"{k.get('deskripsi', '')} | "
                f"Harga: Rp {int(k.get('harga_per_orang', 0)):,}/orang | "
                f"Rating: {k.get('rating', 0)}"
            )

    return "\n".join(context_parts)


def build_system_prompt(context_docs: str) -> str:
    """
    Build system prompt dengan grounding strategy anti-halusinasi.
    """
    return f"""Kamu adalah BandungTrip AI — asisten perencanaan wisata Bandung yang akurat.

ATURAN KETAT:
1. Kamu HANYA boleh menyebutkan tempat, hotel, dan restoran yang ada di CONTEXT DOCUMENTS
2. JANGAN PERNAH menambahkan tempat dari pengetahuan umummu — hanya gunakan data yang diberikan
3. Jika data tidak cukup, katakan "data terbatas" — JANGAN mengarang informasi
4. Semua harga, jam operasional, dan fasilitas harus persis dari data — JANGAN menebak
5. Gunakan bahasa Indonesia yang ramah, informatif, dan mengundang

CONTEXT DOCUMENTS:
{context_docs}

INSTRUKSI OUTPUT:
- Tulis narasi perjalanan yang menarik dan informatif
- Sertakan tips praktis untuk setiap destinasi
- Sebutkan estimasi biaya dengan jelas
- Gunakan emoji yang relevan untuk keterbacaan
- Panjang narasi: 300-500 kata"""