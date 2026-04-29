"""
map_view.py — Render peta rute menggunakan Folium.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from config import BANDUNG_LAT, BANDUNG_LNG


# Warna untuk marker per hari
DAY_COLORS = ["blue", "red", "green", "purple", "orange", "darkred", "cadetblue"]

CATEGORY_ICONS = {
    "Alam": "tree",
    "Budaya": "university",
    "Hiburan": "gamepad",
    "Kota": "building",
    "Kuliner": "cutlery",
}


def render_map(itinerary_data: dict):
    """Render peta interaktif dengan marker destinasi dan rute."""
    days = itinerary_data.get("itinerary_per_hari", [])
    hotel = itinerary_data.get("hotel", {})

    # Buat peta base
    m = folium.Map(
        location=[BANDUNG_LAT, BANDUNG_LNG],
        zoom_start=11,
        tiles="CartoDB dark_matter",
    )

    # Marker hotel
    if hotel and hotel.get("lat") and hotel.get("lng"):
        folium.Marker(
            location=[hotel["lat"], hotel["lng"]],
            popup=folium.Popup(
                f"<b>🏨 {hotel['nama']}</b><br>"
                f"{hotel.get('alamat', '')}<br>"
                f"Rp {hotel.get('harga_per_malam', 0):,}/malam",
                max_width=250,
            ),
            tooltip=hotel["nama"],
            icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        ).add_to(m)

    # Marker destinasi per hari
    all_coords = []
    for day in days:
        hari = day.get("hari", 1)
        color = DAY_COLORS[(hari - 1) % len(DAY_COLORS)]
        day_coords = []

        for dest in day.get("destinasi", []):
            lat, lng = dest.get("lat"), dest.get("lng")
            if lat and lng:
                kategori = dest.get("kategori", "Alam")
                icon_name = CATEGORY_ICONS.get(kategori, "info-sign")

                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(
                        f"<b>Hari {hari}: {dest['nama']}</b><br>"
                        f"{dest.get('deskripsi', '')}<br>"
                        f"🎫 Rp {dest.get('harga_tiket', 0):,}<br>"
                        f"⏰ {dest.get('jam_operasional', '')}<br>"
                        f"⭐ {dest.get('rating', '')}",
                        max_width=250,
                    ),
                    tooltip=f"Hari {hari}: {dest['nama']}",
                    icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
                ).add_to(m)

                day_coords.append([lat, lng])
                all_coords.append([lat, lng])

        # Garis rute per hari
        if len(day_coords) >= 2:
            folium.PolyLine(
                day_coords,
                weight=3,
                color=color,
                opacity=0.7,
                dash_array="10",
                tooltip=f"Rute Hari {hari}",
            ).add_to(m)

    # Fit bounds
    if all_coords:
        m.fit_bounds(all_coords, padding=(30, 30))

    # Header
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:12px;
    padding:20px 24px;margin:24px 0 12px;">
        <h3 style="color:#e2e8f0;margin:0;font-size:1.3rem;">🗺️ Peta Rute Perjalanan</h3>
        <p style="color:#94a3b8;margin:4px 0 0;font-size:0.9rem;">
            Klik marker untuk detail destinasi
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Render map
    st_folium(m, width=None, height=480, use_container_width=True)

    # Legend
    legend_html = ""
    for i, day in enumerate(days):
        color = DAY_COLORS[i % len(DAY_COLORS)]
        legend_html += f'<span style="color:{color};margin-right:16px;font-size:0.85rem;">● Hari {day["hari"]}</span>'

    st.markdown(f"""
    <div style="text-align:center;padding:8px;color:#94a3b8;font-size:0.85rem;">
        🏨 Hotel &nbsp;&nbsp; {legend_html}
    </div>
    """, unsafe_allow_html=True)
