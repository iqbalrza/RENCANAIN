"""
search_service.py — Azure AI Search: Query 3 index (wisata, hotel, kuliner).

Implementasi RAG pipeline:
- Full-text search dengan scoring profile
- Filter OData untuk budget, kategori, dan harga
- Semantic search (jika tier Standard ke atas)
- Fallback ke pencarian lokal JSON jika Azure tidak tersedia

Index schema yang dibutuhkan (lihat scripts/create_index.py):
  wisata:  id, nama, kategori, deskripsi, harga_tiket, rating, tags, lat, lng
  hotel:   id, nama, kategori, deskripsi, harga_per_malam, rating, tags, lat, lng
  kuliner: id, nama, kategori, deskripsi, harga_per_orang, rating, tags, lat, lng
"""

import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ── Coba inisialisasi Azure AI Search clients ────────────────
_search_clients = {}
_use_semantic = False  # Aktif jika tier Standard ke atas

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.models import QueryType
    from azure.core.credentials import AzureKeyCredential
    from config import (
        AZURE_SEARCH_ENDPOINT,
        AZURE_SEARCH_API_KEY,
        AZURE_SEARCH_INDEX_WISATA,
        AZURE_SEARCH_INDEX_HOTEL,
        AZURE_SEARCH_INDEX_KULINER,
    )

    _is_placeholder = (
        not AZURE_SEARCH_ENDPOINT
        or not AZURE_SEARCH_API_KEY
        or "your-" in AZURE_SEARCH_API_KEY
        or "your-" in AZURE_SEARCH_ENDPOINT
    )

    if not _is_placeholder:
        credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
        _search_clients = {
            "wisata": SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_WISATA, credential),
            "hotel": SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_HOTEL, credential),
            "kuliner": SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_KULINER, credential),
        }
        logger.info("Azure AI Search clients initialized.")
    else:
        logger.warning("Azure AI Search credentials not set — using local fallback.")
except Exception as e:
    logger.warning(f"Azure AI Search not available: {e} — using local fallback.")


# ─────────────────────────────────────────────────────────────
# LOCAL FALLBACK HELPERS
# ─────────────────────────────────────────────────────────────

def _load_local(category: str) -> list[dict]:
    """Load data lokal dari file JSON."""
    filepath = os.path.join(DATA_DIR, f"{category}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []


def _local_search(data: list[dict], query: str, top: int = 10) -> list[dict]:
    """
    Full-text search sederhana dengan keyword scoring.
    Mensimulasikan behavior Azure AI Search pada mode fallback.
    """
    if not query or query.strip() == "*":
        return data[:top]

    query_tokens = query.lower().split()
    scored = []

    for item in data:
        score = 0.0

        # Bobot field: nama > kategori > tags > deskripsi
        nama = item.get("nama", "").lower()
        kategori = item.get("kategori", "").lower()
        deskripsi = item.get("deskripsi", "").lower()
        tags = [t.lower() for t in item.get("tags", [])]

        for token in query_tokens:
            if token in nama:
                score += 10.0
            if token in kategori:
                score += 8.0
            for tag in tags:
                if token in tag:
                    score += 5.0
            if token in deskripsi:
                score += 2.0

        # Bonus rating (normalisasi 0-5 → 0-1 sebagai tiebreaker)
        score += item.get("rating", 0) * 0.1

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top]]


# ─────────────────────────────────────────────────────────────
# AZURE SEARCH HELPER
# ─────────────────────────────────────────────────────────────

def _azure_search(
    index_key: str,
    query: str,
    top: int,
    filter_expr: str | None = None,
    order_by: list[str] | None = None,
) -> list[dict] | None:
    """
    Jalankan query ke Azure AI Search.

    Args:
        index_key: "wisata" | "hotel" | "kuliner"
        query: full-text query string; gunakan "*" untuk match-all
        top: jumlah hasil
        filter_expr: OData filter expression (e.g., "harga_tiket le 50000")
        order_by: list field untuk sorting (e.g., ["rating desc"])

    Returns:
        list of dict hasil, atau None jika client tidak tersedia / error
    """
    client = _search_clients.get(index_key)
    if not client:
        return None

    try:
        search_kwargs = {
            "search_text": query or "*",
            "top": top,
            "include_total_count": False,
        }
        if filter_expr:
            search_kwargs["filter"] = filter_expr
        if order_by:
            search_kwargs["order_by"] = order_by

        results = client.search(**search_kwargs)
        docs = [dict(r) for r in results]
        logger.debug(f"Azure Search [{index_key}] '{query}' filter='{filter_expr}' → {len(docs)} docs")
        return docs

    except Exception as e:
        logger.error(f"Azure Search [{index_key}] failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def search_wisata(
    query: str,
    top: int = 10,
    max_harga_tiket: int | None = None,
    kategori: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    """
    Cari destinasi wisata dari Azure AI Search (atau fallback lokal).

    Args:
        query: kata kunci, e.g. "alam lembang" / "budaya sejarah"
        top: jumlah hasil maksimal
        max_harga_tiket: filter harga tiket maksimal (Rupiah)
        kategori: filter kategori exact, e.g. "Alam" / "Budaya"
        min_rating: filter rating minimal, e.g. 4.0

    Returns:
        list of dict destinasi wisata
    """
    # Build OData filter
    filters = []
    if max_harga_tiket is not None:
        filters.append(f"harga_tiket le {max_harga_tiket}")
    if kategori:
        filters.append(f"kategori eq '{kategori}'")
    if min_rating is not None:
        filters.append(f"rating ge {min_rating}")
    filter_expr = " and ".join(filters) if filters else None

    # Coba Azure Search
    results = _azure_search(
        "wisata", query, top,
        filter_expr=filter_expr,
        order_by=["rating desc"],
    )
    if results is not None:
        return results

    # Fallback lokal
    data = _load_local("wisata")
    if max_harga_tiket is not None:
        data = [d for d in data if d.get("harga_tiket", 0) <= max_harga_tiket]
    if kategori:
        data = [d for d in data if d.get("kategori", "").lower() == kategori.lower()]
    if min_rating is not None:
        data = [d for d in data if d.get("rating", 0) >= min_rating]

    return _local_search(data, query, top)


def search_hotel(
    query: str,
    top: int = 5,
    max_harga_malam: int | None = None,
    kategori: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    """
    Cari hotel dari Azure AI Search (atau fallback lokal).

    Args:
        query: kata kunci, e.g. "budget lembang" / "premium kolam renang"
        max_harga_malam: filter harga per malam maksimal
        kategori: "Budget" | "Mid-Range" | "Premium"
    """
    filters = []
    if max_harga_malam is not None:
        filters.append(f"harga_per_malam le {max_harga_malam}")
    if kategori:
        filters.append(f"kategori eq '{kategori}'")
    if min_rating is not None:
        filters.append(f"rating ge {min_rating}")
    filter_expr = " and ".join(filters) if filters else None

    results = _azure_search(
        "hotel", query, top,
        filter_expr=filter_expr,
        order_by=["rating desc", "harga_per_malam desc"],
    )
    if results is not None:
        return results

    # Fallback lokal
    data = _load_local("hotel")
    if max_harga_malam is not None:
        data = [d for d in data if d.get("harga_per_malam", 0) <= max_harga_malam]
    if kategori:
        data = [d for d in data if d.get("kategori", "").lower() == kategori.lower()]
    if min_rating is not None:
        data = [d for d in data if d.get("rating", 0) >= min_rating]

    return _local_search(data, query, top)


def search_kuliner(
    query: str,
    top: int = 10,
    max_harga_orang: int | None = None,
    kategori: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    """
    Cari kuliner dari Azure AI Search (atau fallback lokal).

    Args:
        query: kata kunci, e.g. "sunda tradisional" / "kafe aesthetic"
        max_harga_orang: filter harga per orang maksimal
    """
    filters = []
    if max_harga_orang is not None:
        filters.append(f"harga_per_orang le {max_harga_orang}")
    if kategori:
        filters.append(f"kategori eq '{kategori}'")
    if min_rating is not None:
        filters.append(f"rating ge {min_rating}")
    filter_expr = " and ".join(filters) if filters else None

    results = _azure_search(
        "kuliner", query, top,
        filter_expr=filter_expr,
        order_by=["rating desc"],
    )
    if results is not None:
        return results

    # Fallback lokal
    data = _load_local("kuliner")
    if max_harga_orang is not None:
        data = [d for d in data if d.get("harga_per_orang", 0) <= max_harga_orang]
    if kategori:
        data = [d for d in data if d.get("kategori", "").lower() == kategori.lower()]
    if min_rating is not None:
        data = [d for d in data if d.get("rating", 0) >= min_rating]

    return _local_search(data, query, top)


def search_all(query: str, top_per_category: int = 5) -> dict:
    """Cari di semua 3 index sekaligus."""
    return {
        "wisata": search_wisata(query, top_per_category),
        "hotel": search_hotel(query, top_per_category),
        "kuliner": search_kuliner(query, top_per_category),
    }


def retrieve_for_itinerary(
    preferensi: list[str],
    budget_wisata_per_orang: int,
    budget_kuliner_per_orang_per_meal: int,
    budget_hotel_per_malam: int,
    jumlah_hari: int,
    jumlah_wisata_needed: int,
) -> dict:
    """
    RAG retrieval khusus untuk itinerary builder.

    Fungsi ini adalah jembatan antara itinerary_builder.py dan Azure AI Search.
    Menggantikan load_json() + filter manual dengan query langsung ke Azure Search.

    Args:
        preferensi: list preferensi user, e.g. ["Alam", "Kuliner"]
        budget_wisata_per_orang: budget tiket wisata per orang (total)
        budget_kuliner_per_orang_per_meal: budget makan per orang per sekali makan
        budget_hotel_per_malam: budget hotel per malam
        jumlah_hari: durasi perjalanan
        jumlah_wisata_needed: total destinasi wisata yang dibutuhkan

    Returns:
        dict dengan keys: wisata, hotel, kuliner
    """
    # ── Retrieve wisata ──────────────────────────────────────
    # Query = join preferensi sebagai kata kunci
    # Filter = harga tiket sesuai budget wisata per orang
    wisata_query = " ".join(preferensi)  # e.g. "Alam Kuliner"

    # Ambil lebih banyak lalu filter duplikat, agar ada cukup pilihan
    wisata_candidates = search_wisata(
        query=wisata_query,
        top=jumlah_wisata_needed * 3,  # buffer 3x
        max_harga_tiket=budget_wisata_per_orang,
    )

    # Jika kurang (preferensi terlalu spesifik), fallback ke semua wisata
    if len(wisata_candidates) < jumlah_wisata_needed:
        logger.info(f"Wisata candidates kurang ({len(wisata_candidates)}), expand search...")
        wisata_candidates += search_wisata(
            query="bandung wisata",
            top=jumlah_wisata_needed * 2,
            max_harga_tiket=budget_wisata_per_orang,
        )
        # Deduplicate by id
        seen = set()
        deduped = []
        for w in wisata_candidates:
            wid = w.get("id", w.get("nama"))
            if wid not in seen:
                seen.add(wid)
                deduped.append(w)
        wisata_candidates = deduped

    # ── Retrieve hotel ───────────────────────────────────────
    # Query berdasarkan budget → kategori hotel
    if budget_hotel_per_malam >= 800000:
        hotel_query = "premium mewah spa kolam renang"
    elif budget_hotel_per_malam >= 400000:
        hotel_query = "mid-range nyaman restoran"
    else:
        hotel_query = "budget bersih wifi"

    hotel_candidates = search_hotel(
        query=hotel_query,
        top=10,
        max_harga_malam=budget_hotel_per_malam,
    )

    # Fallback: ambil semua hotel termurah jika tidak ada yang sesuai
    if not hotel_candidates:
        logger.warning("Tidak ada hotel yang sesuai budget, ambil semua hotel.")
        hotel_candidates = search_hotel(query="hotel bandung", top=10)

    # ── Retrieve kuliner ─────────────────────────────────────
    # Query gabungan preferensi + "bandung" untuk konteks lokal
    kuliner_query = "sunda bandung " + " ".join(preferensi).lower()

    # Harga per meal dengan margin 20%
    max_harga_meal = int(budget_kuliner_per_orang_per_meal * 1.2)

    kuliner_candidates = search_kuliner(
        query=kuliner_query,
        top=jumlah_hari * 3 * 3,  # 3 meal/hari × 3 opsi/meal × buffer
        max_harga_orang=max_harga_meal,
    )

    # Fallback kuliner murah
    if len(kuliner_candidates) < jumlah_hari * 3:
        logger.info("Kuliner candidates kurang, expand search...")
        extra = search_kuliner(
            query="kuliner bandung murah",
            top=jumlah_hari * 9,
        )
        seen = {k.get("id", k.get("nama")) for k in kuliner_candidates}
        kuliner_candidates += [k for k in extra if k.get("id", k.get("nama")) not in seen]

    logger.info(
        f"RAG retrieved: {len(wisata_candidates)} wisata, "
        f"{len(hotel_candidates)} hotel, {len(kuliner_candidates)} kuliner"
    )

    return {
        "wisata": wisata_candidates,
        "hotel": hotel_candidates,
        "kuliner": kuliner_candidates,
    }