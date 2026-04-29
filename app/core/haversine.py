"""
haversine.py — Pre-filter jarak koordinat menggunakan formula Haversine.
"""

import math


EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Hitung jarak antara dua titik koordinat menggunakan formula Haversine.

    Returns jarak dalam kilometer.
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def sort_by_distance(origin_lat: float, origin_lng: float,
                     destinations: list[dict]) -> list[dict]:
    """
    Urutkan destinasi berdasarkan jarak dari titik origin.

    Setiap item di destinations harus memiliki key 'lat' dan 'lng'.
    """
    for dest in destinations:
        dest["_jarak_km"] = haversine(
            origin_lat, origin_lng, dest["lat"], dest["lng"]
        )

    return sorted(destinations, key=lambda d: d["_jarak_km"])


def nearest_neighbor_route(destinations: list[dict],
                            start_lat: float, start_lng: float) -> list[dict]:
    """
    Optimasi urutan kunjungan menggunakan Nearest Neighbor Algorithm.

    Dimulai dari koordinat start, lalu setiap langkah mengunjungi
    destinasi terdekat yang belum dikunjungi.
    """
    if not destinations:
        return []

    remaining = list(destinations)
    route = []
    current_lat, current_lng = start_lat, start_lng

    while remaining:
        nearest = min(
            remaining,
            key=lambda d: haversine(current_lat, current_lng, d["lat"], d["lng"])
        )
        nearest["_jarak_dari_sebelumnya"] = haversine(
            current_lat, current_lng, nearest["lat"], nearest["lng"]
        )
        route.append(nearest)
        current_lat, current_lng = nearest["lat"], nearest["lng"]
        remaining.remove(nearest)

    return route


def total_route_distance(route: list[dict]) -> float:
    """Hitung total jarak rute dalam km."""
    return sum(d.get("_jarak_dari_sebelumnya", 0) for d in route)
