"""
map_view.py — Render peta rute per hari (1 peta per hari).
Menggunakan Azure Maps Route API untuk rute jalan sebenarnya.
Fallback ke OSRM jika Azure Maps tidak tersedia.
"""

from html import escape

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

from config import AZURE_MAPS_API_KEY, BANDUNG_LAT, BANDUNG_LNG
from utils.logger import get_logger

logger = get_logger(__name__)

DAY_COLORS = ["blue", "red", "green", "purple", "orange", "darkred", "cadetblue"]
DAY_HEX_COLORS = ["#3388ff", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12", "#c0392b", "#1abc9c"]

CATEGORY_ICONS = {
    "Alam": "tree",
    "Budaya": "university",
    "Hiburan": "gamepad",
    "Kota": "building",
}

MEAL_ICONS = {
    "Sarapan": "☀️",
    "Makan Siang": "🍽️",
    "Makan Malam": "🌙",
}

REQUEST_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_coord(lat, lng) -> bool:
    """Validasi koordinat: harus angka, bukan None, dan dalam range bumi."""
    if lat is None or lng is None:
        return False
    try:
        lat_f, lng_f = float(lat), float(lng)
    except (TypeError, ValueError):
        return False
    return -90 <= lat_f <= 90 and -180 <= lng_f <= 180


def _safe(text) -> str:
    """Escape HTML untuk konten popup."""
    return escape(str(text)) if text is not None else ""


def _build_day_route(day_data: dict) -> list[dict]:
    """Bangun urutan: Sarapan → Dest1 → Makan Siang → Dest2 → Makan Malam → Dest3 → sisa destinasi."""
    destinasi = day_data.get("destinasi", []) or []
    kuliner = day_data.get("kuliner", []) or []
    route: list[dict] = []

    sarapan = next((k for k in kuliner if k.get("waktu_makan") == "Sarapan"), None)
    makan_siang = next((k for k in kuliner if k.get("waktu_makan") == "Makan Siang"), None)
    makan_malam = next((k for k in kuliner if k.get("waktu_makan") == "Makan Malam"), None)

    if sarapan:
        route.append({"type": "kuliner", "data": sarapan, "label": "Sarapan"})
    if len(destinasi) > 0:
        route.append({"type": "destinasi", "data": destinasi[0]})
    if makan_siang:
        route.append({"type": "kuliner", "data": makan_siang, "label": "Makan Siang"})
    if len(destinasi) > 1:
        route.append({"type": "destinasi", "data": destinasi[1]})
    if makan_malam:
        route.append({"type": "kuliner", "data": makan_malam, "label": "Makan Malam"})
    if len(destinasi) > 2:
        route.append({"type": "destinasi", "data": destinasi[2]})
    for d in destinasi[3:]:
        route.append({"type": "destinasi", "data": d})

    return route


# ---------------------------------------------------------------------------
# Routing API (dengan caching)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def _get_azure_maps_route_multi(coords_tuple: tuple) -> list[list[float]] | None:
    """
    Ambil rute jalan untuk multi-waypoint dalam 1 request.
    coords_tuple: tuple of (lat, lng) — minimal 2 titik.
    Returns: list of [lat, lng] sepanjang jalan, atau None.

    Pakai tuple supaya hashable untuk @st.cache_data.
    """
    if len(coords_tuple) < 2 or not AZURE_MAPS_API_KEY:
        return None

    # Build query: "lat1,lng1:lat2,lng2:lat3,lng3"
    query = ":".join(f"{lat},{lng}" for lat, lng in coords_tuple)
    url = "https://atlas.microsoft.com/route/directions/json"
    params = {
        "api-version": "1.0",
        "subscription-key": AZURE_MAPS_API_KEY,
        "query": query,
        "travelMode": "car",
        "routeType": "shortest",
    }

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning(f"Azure Maps HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        if not data.get("routes"):
            return None

        points: list[list[float]] = []
        for leg in data["routes"][0].get("legs", []):
            for point in leg.get("points", []):
                points.append([point["latitude"], point["longitude"]])

        if points:
            logger.debug(f"Azure Maps route: {len(points)} points for {len(coords_tuple)} waypoints")
            return points
    except Exception as e:
        logger.warning(f"Azure Maps route failed: {e}")

    return None


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def _get_osrm_route(coords_tuple: tuple) -> list[list[float]] | None:
    """Fallback: OSRM multi-waypoint."""
    if len(coords_tuple) < 2:
        return None

    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords_tuple)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                return [[c[1], c[0]] for c in geojson_coords]
    except Exception as e:
        logger.warning(f"OSRM route failed: {e}")

    return None


def _get_route(coords: list[list[float]]) -> list[list[float]] | None:
    """Ambil rute jalan: Azure Maps (primary) → OSRM (fallback)."""
    coords_tuple = tuple((c[0], c[1]) for c in coords)

    route = _get_azure_maps_route_multi(coords_tuple)
    if route:
        return route

    return _get_osrm_route(coords_tuple)


# ---------------------------------------------------------------------------
# Map rendering
# ---------------------------------------------------------------------------

def _render_single_day_map(day_data: dict, hotel: dict, hari: int):
    """Render 1 peta untuk 1 hari."""
    color = DAY_COLORS[(hari - 1) % len(DAY_COLORS)]
    hex_color = DAY_HEX_COLORS[(hari - 1) % len(DAY_HEX_COLORS)]

    m = folium.Map(
        location=[BANDUNG_LAT, BANDUNG_LNG],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    day_coords: list[list[float]] = []

    # Hotel marker + start point
    if hotel and _is_valid_coord(hotel.get("lat"), hotel.get("lng")):
        hotel_coord = [float(hotel["lat"]), float(hotel["lng"])]
        day_coords.append(hotel_coord)
        folium.Marker(
            location=hotel_coord,
            popup=folium.Popup(
                f"<b>🏨 {_safe(hotel.get('nama', ''))}</b><br>"
                f"{_safe(hotel.get('alamat', ''))}<br>"
                f"Rp {int(hotel.get('harga_per_malam', 0)):,}/malam",
                max_width=250,
            ),
            tooltip=_safe(hotel.get("nama", "Hotel")),
            icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        ).add_to(m)

    # Bangun rute & marker
    route = _build_day_route(day_data)
    stop_number = 1

    for stop in route:
        item = stop["data"]
        lat, lng = item.get("lat"), item.get("lng")
        if not _is_valid_coord(lat, lng):
            continue

        coord = [float(lat), float(lng)]
        day_coords.append(coord)

        nama = _safe(item.get("nama", ""))

        if stop["type"] == "destinasi":
            kategori = item.get("kategori", "Alam")
            icon_name = CATEGORY_ICONS.get(kategori, "info-sign")
            popup_html = (
                f"<b>#{stop_number} {nama}</b><br>"
                f"{_safe(item.get('deskripsi', ''))}<br>"
                f"🎫 Rp {int(item.get('harga_tiket', 0)):,}<br>"
                f"⏰ {_safe(item.get('jam_operasional', ''))}<br>"
                f"⭐ {_safe(item.get('rating', ''))}"
            )
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"#{stop_number} {nama}",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
            ).add_to(m)
        else:
            meal_label = stop.get("label", "Makan")
            meal_emoji = MEAL_ICONS.get(meal_label, "🍴")
            popup_html = (
                f"<b>{meal_emoji} #{stop_number} {_safe(meal_label)}</b><br>"
                f"<b>{nama}</b><br>"
                f"{_safe(item.get('kategori', ''))} · {_safe(item.get('jam_operasional', ''))}<br>"
                f"💰 Rp {int(item.get('harga_per_orang', 0)):,}/orang"
            )
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"#{stop_number} {_safe(meal_label)}: {nama}",
                icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
            ).add_to(m)

        stop_number += 1

    # Gambar rute jalan — 1 request multi-waypoint untuk seluruh hari
    if len(day_coords) >= 2:
        full_route = _get_route(day_coords)
        if full_route:
            folium.PolyLine(
                full_route, weight=4, color=hex_color, opacity=0.85,
            ).add_to(m)
        else:
            # Fallback: garis lurus penuh
            folium.PolyLine(
                day_coords, weight=3, color=hex_color,
                opacity=0.6, dash_array="8",
            ).add_to(m)

    # Fit bounds — folium butuh [[sw_lat, sw_lng], [ne_lat, ne_lng]]
    if day_coords:
        lats = [c[0] for c in day_coords]
        lngs = [c[1] for c in day_coords]
        bounds = [[min(lats), min(lngs)], [max(lats), max(lngs)]]
        m.fit_bounds(bounds, padding=(40, 40))

    st_folium(
        m,
        height=380,
        use_container_width=True,
        returned_objects=[],  # disable rerun on map interaction
        key=f"map_hari_{hari}",
    )


def render_map(itinerary_data: dict):
    """Render peta terpisah per hari."""
    days = itinerary_data.get("itinerary_per_hari", []) or []
    hotel = itinerary_data.get("hotel", {}) or {}

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1e293b,#334155);'
        'border-radius:12px;padding:20px 24px;margin:24px 0 12px;">'
        '<h3 style="color:#e2e8f0;margin:0;font-size:1.3rem;">🗺️ Peta Rute Perjalanan</h3>'
        '<p style="color:#94a3b8;margin:4px 0 0;font-size:0.9rem;">'
        'Rute jalan per hari · Klik marker untuk detail</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    for day in days:
        hari = day.get("hari", 1)
        hex_color = DAY_HEX_COLORS[(hari - 1) % len(DAY_HEX_COLORS)]

        dest_names = ", ".join(
            _safe(d.get("nama", "")) for d in (day.get("destinasi", []) or [])[:3]
        )
        st.markdown(
            f'<div style="background:{hex_color}22;border-left:4px solid {hex_color};'
            f'border-radius:0 8px 8px 0;padding:12px 16px;margin:16px 0 8px;">'
            f'<span style="color:{hex_color};font-weight:700;font-size:1.05rem;">📅 Hari {hari}</span>'
            f'<span style="color:#94a3b8;font-size:0.85rem;margin-left:12px;">{dest_names}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        _render_single_day_map(day, hotel, hari)