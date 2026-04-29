"""
map_view.py — Render peta rute per hari (1 peta per hari).
Menggunakan OSRM API untuk rute jalan sebenarnya.
"""

import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
from config import BANDUNG_LAT, BANDUNG_LNG


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


def _build_day_route(day_data: dict) -> list[dict]:
    """Bangun urutan: Sarapan → Dest1 → Makan Siang → Dest2 → Makan Malam → Dest3"""
    destinasi = day_data.get("destinasi", [])
    kuliner = day_data.get("kuliner", [])
    route = []

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


def _get_osrm_route(coords: list[list[float]]) -> list[list[float]] | None:
    """Ambil rute jalan sebenarnya dari OSRM API."""
    if len(coords) < 2:
        return None

    coord_str = f"{coords[0][1]},{coords[0][0]};{coords[1][1]},{coords[1][0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                return [[c[1], c[0]] for c in geojson_coords]
    except Exception:
        pass
    return None


def _render_single_day_map(day_data: dict, hotel: dict, hari: int):
    """Render 1 peta untuk 1 hari."""
    color = DAY_COLORS[(hari - 1) % len(DAY_COLORS)]
    hex_color = DAY_HEX_COLORS[(hari - 1) % len(DAY_HEX_COLORS)]

    m = folium.Map(
        location=[BANDUNG_LAT, BANDUNG_LNG],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    all_coords = []
    day_coords = []

    # Hotel marker + start point
    hotel_coord = None
    if hotel and hotel.get("lat") and hotel.get("lng"):
        hotel_coord = [hotel["lat"], hotel["lng"]]
        day_coords.append(hotel_coord)
        all_coords.append(hotel_coord)
        folium.Marker(
            location=hotel_coord,
            popup=folium.Popup(
                f"<b>🏨 {hotel['nama']}</b><br>"
                f"{hotel.get('alamat', '')}<br>"
                f"Rp {hotel.get('harga_per_malam', 0):,}/malam",
                max_width=250,
            ),
            tooltip=hotel["nama"],
            icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        ).add_to(m)

    # Bangun rute
    route = _build_day_route(day_data)
    stop_number = 1

    for stop in route:
        item = stop["data"]
        lat, lng = item.get("lat"), item.get("lng")
        if not lat or not lng:
            continue

        coord = [lat, lng]
        day_coords.append(coord)
        all_coords.append(coord)

        if stop["type"] == "destinasi":
            kategori = item.get("kategori", "Alam")
            icon_name = CATEGORY_ICONS.get(kategori, "info-sign")
            folium.Marker(
                location=coord,
                popup=folium.Popup(
                    f"<b>#{stop_number} {item['nama']}</b><br>"
                    f"{item.get('deskripsi', '')}<br>"
                    f"🎫 Rp {item.get('harga_tiket', 0):,}<br>"
                    f"⏰ {item.get('jam_operasional', '')}<br>"
                    f"⭐ {item.get('rating', '')}",
                    max_width=250,
                ),
                tooltip=f"#{stop_number} {item['nama']}",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
            ).add_to(m)
        else:
            meal_label = stop.get("label", "Makan")
            meal_emoji = MEAL_ICONS.get(meal_label, "🍴")
            folium.Marker(
                location=coord,
                popup=folium.Popup(
                    f"<b>{meal_emoji} #{stop_number} {meal_label}</b><br>"
                    f"<b>{item['nama']}</b><br>"
                    f"{item.get('kategori', '')} · {item.get('jam_operasional', '')}<br>"
                    f"💰 Rp {item.get('harga_per_orang', 0):,}/orang",
                    max_width=250,
                ),
                tooltip=f"#{stop_number} {meal_label}: {item['nama']}",
                icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
            ).add_to(m)

        stop_number += 1

    # Gambar rute jalan — segment per segment (A→B, B→C, C→D)
    for i in range(len(day_coords) - 1):
        segment_start = day_coords[i]
        segment_end = day_coords[i + 1]
        road_segment = _get_osrm_route([segment_start, segment_end])
        if road_segment:
            folium.PolyLine(
                road_segment, weight=4, color=hex_color, opacity=0.85,
            ).add_to(m)
        else:
            # Fallback: garis lurus untuk segment ini
            folium.PolyLine(
                [segment_start, segment_end], weight=3, color=hex_color,
                opacity=0.6, dash_array="8",
            ).add_to(m)

    # Fit bounds
    if all_coords:
        m.fit_bounds(all_coords, padding=(40, 40))

    st_folium(m, width=None, height=380, use_container_width=True,
              key=f"map_hari_{hari}")


def render_map(itinerary_data: dict):
    """Render peta terpisah per hari."""
    days = itinerary_data.get("itinerary_per_hari", [])
    hotel = itinerary_data.get("hotel", {})

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:12px;padding:20px 24px;margin:24px 0 12px;">'
        '<h3 style="color:#e2e8f0;margin:0;font-size:1.3rem;">🗺️ Peta Rute Perjalanan</h3>'
        '<p style="color:#94a3b8;margin:4px 0 0;font-size:0.9rem;">Rute jalan per hari · Klik marker untuk detail</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    for day in days:
        hari = day.get("hari", 1)
        hex_color = DAY_HEX_COLORS[(hari - 1) % len(DAY_HEX_COLORS)]

        # Header per hari
        dest_names = ", ".join(d["nama"] for d in day.get("destinasi", [])[:3])
        st.markdown(
            f'<div style="background:{hex_color}22;border-left:4px solid {hex_color};'
            f'border-radius:0 8px 8px 0;padding:12px 16px;margin:16px 0 8px;">'
            f'<span style="color:{hex_color};font-weight:700;font-size:1.05rem;">📅 Hari {hari}</span>'
            f'<span style="color:#94a3b8;font-size:0.85rem;margin-left:12px;">{dest_names}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        _render_single_day_map(day, hotel, hari)
