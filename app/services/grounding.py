"""
grounding.py — RAG pipeline: Inject context documents, build system prompt.
"""

import json
from services.search_service import search_wisata, search_hotel, search_kuliner
from utils.logger import get_logger

logger = get_logger(__name__)


def build_context_documents(intent: dict, form_data: dict) -> str:
    """
    Bangun context documents dari hasil retrieval untuk di-inject ke system prompt.

    Args:
        intent: hasil extract_intent (search_queries, budget_category, etc.)
        form_data: data form asli (budget, preferensi, etc.)
    """
    context_parts = []

    # Retrieve wisata
    queries = intent.get("search_queries", form_data.get("preferensi", ["wisata"]))
    wisata_results = []
    for q in queries:
        results = search_wisata(q, top=5)
        wisata_results.extend(results)

    # Deduplicate by id
    seen_ids = set()
    unique_wisata = []
    for w in wisata_results:
        wid = w.get("id", w.get("nama"))
        if wid not in seen_ids:
            seen_ids.add(wid)
            unique_wisata.append(w)

    if unique_wisata:
        context_parts.append("=== DESTINASI WISATA BANDUNG ===")
        for w in unique_wisata[:10]:
            context_parts.append(
                f"- {w['nama']} ({w.get('kategori', '-')}): "
                f"{w.get('deskripsi', '')} | "
                f"Tiket: Rp {w.get('harga_tiket', 0):,} | "
                f"Jam: {w.get('jam_operasional', '-')} | "
                f"Rating: {w.get('rating', 0)}"
            )

    # Retrieve hotel
    budget_cat = intent.get("budget_category", "budget")
    hotel_results = search_hotel(budget_cat, top=5)
    if hotel_results:
        context_parts.append("\n=== HOTEL & AKOMODASI ===")
        for h in hotel_results:
            context_parts.append(
                f"- {h['nama']} ({h.get('kategori', '-')}): "
                f"{h.get('deskripsi', '')} | "
                f"Harga: Rp {h.get('harga_per_malam', 0):,}/malam | "
                f"Rating: {h.get('rating', 0)}"
            )

    # Retrieve kuliner
    kuliner_results = search_kuliner("bandung", top=5)
    if kuliner_results:
        context_parts.append("\n=== KULINER LOKAL ===")
        for k in kuliner_results:
            context_parts.append(
                f"- {k['nama']} ({k.get('kategori', '-')}): "
                f"{k.get('deskripsi', '')} | "
                f"Harga: Rp {k.get('harga_per_orang', 0):,}/orang | "
                f"Rating: {k.get('rating', 0)}"
            )

    context = "\n".join(context_parts)
    logger.debug(f"Built context documents: {len(context)} chars, "
                 f"{len(unique_wisata)} wisata, {len(hotel_results)} hotel, "
                 f"{len(kuliner_results)} kuliner")
    return context


def build_system_prompt(context_docs: str) -> str:
    """
    Build system prompt dengan grounding strategy anti-halusinasi.
    """
    return f"""Kamu adalah BandungTrip AI — asisten perencanaan wisata Bandung yang akurat.

ATURAN KETAT:
1. Kamu HANYA boleh merekomendasikan tempat yang ada di CONTEXT DOCUMENTS di bawah
2. JANGAN PERNAH menambahkan tempat, hotel, atau restoran dari pengetahuan umummu
3. Jika data tidak cukup, katakan "data terbatas" — JANGAN mengarang
4. Semua harga harus sesuai data — JANGAN menebak harga
5. Gunakan bahasa Indonesia yang ramah dan informatif

CONTEXT DOCUMENTS:
{context_docs}

FORMAT OUTPUT:
- Ringkasan perjalanan
- Rekomendasi hotel (nama, harga, fasilitas)
- Itinerary per hari (jadwal, destinasi, durasi, biaya)
- Rekomendasi kuliner per waktu makan
- Estimasi total biaya"""
