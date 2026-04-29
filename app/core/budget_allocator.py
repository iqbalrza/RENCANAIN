"""
budget_allocator.py — Hitung alokasi budget 40/25/25/10.
"""

from config import (
    BUDGET_RATIO_HOTEL,
    BUDGET_RATIO_WISATA,
    BUDGET_RATIO_KULINER,
    BUDGET_RATIO_TRANSPORT,
)


def allocate_budget(total_budget: int) -> dict:
    """
    Alokasi budget ke 4 kategori berdasarkan rasio yang ditentukan.

    Returns dict:
        hotel, wisata, kuliner, transport (masing-masing dalam Rp)
    """
    return {
        "hotel": int(total_budget * BUDGET_RATIO_HOTEL),
        "wisata": int(total_budget * BUDGET_RATIO_WISATA),
        "kuliner": int(total_budget * BUDGET_RATIO_KULINER),
        "transport": int(total_budget * BUDGET_RATIO_TRANSPORT),
        "total": total_budget,
    }


def get_budget_per_day(allocation: dict, durasi: int) -> dict:
    """Hitung budget per hari untuk setiap kategori."""
    if durasi <= 0:
        durasi = 1
    return {
        "hotel_per_malam": allocation["hotel"] // durasi,
        "wisata_per_hari": allocation["wisata"] // durasi,
        "kuliner_per_hari": allocation["kuliner"] // durasi,
        "transport_per_hari": allocation["transport"] // durasi,
    }


def check_budget_fit(allocation: dict, actual_costs: dict) -> dict:
    """
    Bandingkan alokasi dengan biaya aktual.

    Returns dict dengan sisa/lebih per kategori.
    """
    result = {}
    for key in ["hotel", "wisata", "kuliner", "transport"]:
        allocated = allocation.get(key, 0)
        actual = actual_costs.get(key, 0)
        result[key] = {
            "allocated": allocated,
            "actual": actual,
            "sisa": allocated - actual,
            "over_budget": actual > allocated,
        }

    total_actual = sum(actual_costs.get(k, 0) for k in ["hotel", "wisata", "kuliner", "transport"])
    result["total"] = {
        "allocated": allocation["total"],
        "actual": total_actual,
        "sisa": allocation["total"] - total_actual,
        "over_budget": total_actual > allocation["total"],
    }

    return result
