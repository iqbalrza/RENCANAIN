"""
search_service.py — Azure AI Search: Query 3 index (wisata, hotel, kuliner).

Saat Azure AI Search belum dikonfigurasi, module ini menggunakan
pencarian lokal pada file JSON sebagai fallback.
"""

import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ── Coba import Azure AI Search ──────────────────────────────
_search_clients = {}

try:
    from azure.search.documents import SearchClient
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
        logger.warning("Azure AI Search credentials not set or placeholder — using local fallback.")
except Exception as e:
    logger.warning(f"Azure AI Search not available: {e} — using local fallback.")


def _load_local_data(category: str) -> list[dict]:
    """Load data lokal dari file JSON."""
    filepath = os.path.join(DATA_DIR, f"{category}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []


def _local_search(data: list[dict], query: str, top: int = 5) -> list[dict]:
    """Pencarian sederhana berdasarkan keyword matching."""
    query_lower = query.lower()
    scored = []

    for item in data:
        score = 0
        # Cek nama
        if query_lower in item.get("nama", "").lower():
            score += 10
        # Cek deskripsi
        if query_lower in item.get("deskripsi", "").lower():
            score += 5
        # Cek kategori
        if query_lower in item.get("kategori", "").lower():
            score += 8
        # Cek tags
        for tag in item.get("tags", []):
            if query_lower in tag.lower():
                score += 3

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top]]


def search_wisata(query: str, top: int = 5, filters: dict | None = None) -> list[dict]:
    """
    Cari destinasi wisata berdasarkan query.

    Args:
        query: kata kunci pencarian
        top: jumlah hasil maksimal
        filters: filter tambahan (e.g., kategori, max_harga)
    """
    if "wisata" in _search_clients:
        try:
            results = _search_clients["wisata"].search(
                search_text=query, top=top
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Azure Search wisata failed: {e}")

    # Fallback lokal
    data = _load_local_data("wisata")
    if filters:
        if "kategori" in filters:
            data = [d for d in data if d.get("kategori", "").lower() == filters["kategori"].lower()]
        if "max_harga" in filters:
            data = [d for d in data if d.get("harga_tiket", 0) <= filters["max_harga"]]

    if query:
        return _local_search(data, query, top)
    return data[:top]


def search_hotel(query: str, top: int = 5, filters: dict | None = None) -> list[dict]:
    """Cari hotel berdasarkan query."""
    if "hotel" in _search_clients:
        try:
            results = _search_clients["hotel"].search(
                search_text=query, top=top
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Azure Search hotel failed: {e}")

    data = _load_local_data("hotel")
    if filters:
        if "max_harga" in filters:
            data = [d for d in data if d.get("harga_per_malam", 0) <= filters["max_harga"]]
        if "kategori" in filters:
            data = [d for d in data if d.get("kategori", "").lower() == filters["kategori"].lower()]

    if query:
        return _local_search(data, query, top)
    return data[:top]


def search_kuliner(query: str, top: int = 5, filters: dict | None = None) -> list[dict]:
    """Cari kuliner berdasarkan query."""
    if "kuliner" in _search_clients:
        try:
            results = _search_clients["kuliner"].search(
                search_text=query, top=top
            )
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Azure Search kuliner failed: {e}")

    data = _load_local_data("kuliner")
    if filters:
        if "max_harga" in filters:
            data = [d for d in data if d.get("harga_per_orang", 0) <= filters["max_harga"]]

    if query:
        return _local_search(data, query, top)
    return data[:top]


def search_all(query: str, top_per_category: int = 3) -> dict:
    """Cari di semua 3 index secara paralel (atau sequential di fallback)."""
    return {
        "wisata": search_wisata(query, top_per_category),
        "hotel": search_hotel(query, top_per_category),
        "kuliner": search_kuliner(query, top_per_category),
    }
