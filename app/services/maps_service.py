"""
maps_service.py — Azure Maps: Optimasi rute & ETA.

Saat Azure Maps belum dikonfigurasi, module ini menggunakan
perhitungan Haversine lokal sebagai fallback.
"""

import requests
from core.haversine import haversine, nearest_neighbor_route, total_route_distance
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Azure Maps config ────────────────────────────────────────
_maps_key = None

try:
    from config import AZURE_MAPS_API_KEY
    if AZURE_MAPS_API_KEY and "your-" not in AZURE_MAPS_API_KEY:
        _maps_key = AZURE_MAPS_API_KEY
        logger.info("Azure Maps API key loaded.")
    else:
        logger.warning("Azure Maps API key not set or placeholder — using Haversine fallback.")
except Exception as e:
    logger.warning(f"Azure Maps not available: {e} — using Haversine fallback.")


AZURE_MAPS_ROUTE_URL = "https://atlas.microsoft.com/route/directions/json"


def get_route_azure(waypoints: list[dict]) -> dict | None:
    """
    Dapatkan rute dari Azure Maps Route API.

    Args:
        waypoints: list dict dengan key 'lat' dan 'lng'

    Returns:
        dict dengan route info atau None jika gagal
    """
    if not _maps_key or len(waypoints) < 2:
        return None

    try:
        # Format waypoints untuk Azure Maps
        coordinates = ":".join(
            f"{wp['lat']},{wp['lng']}" for wp in waypoints
        )

        params = {
            "api-version": "1.0",
            "subscription-key": _maps_key,
            "query": coordinates,
            "travelMode": "car",
            "routeType": "shortest",
        }

        response = requests.get(AZURE_MAPS_ROUTE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("routes"):
            route = data["routes"][0]
            summary = route.get("summary", {})
            return {
                "distance_km": summary.get("lengthInMeters", 0) / 1000,
                "duration_minutes": summary.get("travelTimeInSeconds", 0) / 60,
                "legs": route.get("legs", []),
            }
    except Exception as e:
        logger.error(f"Azure Maps route failed: {e}")

    return None


def optimize_route(destinations: list[dict],
                    start_lat: float, start_lng: float) -> dict:
    """
    Optimasi rute menggunakan Azure Maps atau fallback Haversine.

    Returns dict:
        ordered_destinations, total_distance_km, segments
    """
    # Pertama, coba Nearest Neighbor lokal untuk ordering
    ordered = nearest_neighbor_route(list(destinations), start_lat, start_lng)

    # Coba Azure Maps untuk jarak sebenarnya
    azure_route = get_route_azure(
        [{"lat": start_lat, "lng": start_lng}] + ordered
    )

    if azure_route:
        return {
            "ordered_destinations": ordered,
            "total_distance_km": azure_route["distance_km"],
            "total_duration_minutes": azure_route["duration_minutes"],
            "source": "azure_maps",
        }

    # Fallback: gunakan jarak Haversine
    total_km = total_route_distance(ordered)

    # Estimasi durasi: rata-rata 30 km/jam di kota Bandung
    est_duration = (total_km / 30) * 60

    return {
        "ordered_destinations": ordered,
        "total_distance_km": round(total_km, 2),
        "total_duration_minutes": round(est_duration, 1),
        "source": "haversine_estimate",
    }


def get_distance_between(lat1: float, lng1: float,
                          lat2: float, lng2: float) -> dict:
    """Dapatkan jarak antara dua titik."""
    if _maps_key:
        route = get_route_azure([
            {"lat": lat1, "lng": lng1},
            {"lat": lat2, "lng": lng2},
        ])
        if route:
            return {
                "distance_km": route["distance_km"],
                "duration_minutes": route["duration_minutes"],
                "source": "azure_maps",
            }

    # Fallback
    dist = haversine(lat1, lng1, lat2, lng2)
    return {
        "distance_km": round(dist, 2),
        "duration_minutes": round((dist / 30) * 60, 1),
        "source": "haversine_estimate",
    }
