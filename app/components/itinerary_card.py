"""
itinerary_card.py — Tampilan itinerary per hari.
"""

import streamlit as st
from utils.formatter import format_rupiah, format_durasi


def render_itinerary(itinerary_data: dict):
    """Render itinerary lengkap dengan card per hari."""
    ringkasan = itinerary_data.get("ringkasan", {})
    hotel = itinerary_data.get("hotel", {})
    days = itinerary_data.get("itinerary_per_hari", [])

    # ── Header Ringkasan ─────────────────────────────────────
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0f3460 0%, #533483 50%, #e94560 100%);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        text-align: center;
    ">
        <h2 style="color: white; margin: 0 0 12px 0; font-size: 1.8rem;">
            🗺️ Itinerary Wisata Bandung
        </h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.1rem;">
            {ringkasan.get('kota_asal', '')} → Bandung · 
            {ringkasan.get('durasi', 1)} Hari · 
            {ringkasan.get('jumlah_orang', 1)} Orang · 
            {format_rupiah(ringkasan.get('budget', 0))}
        </p>
        <div style="margin-top: 12px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
    """, unsafe_allow_html=True)

    pref_html = ""
    for p in ringkasan.get("preferensi", []):
        pref_html += f"""<span style="
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        ">{p}</span>"""

    st.markdown(f"""
        {pref_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hotel Card ───────────────────────────────────────────
    if hotel:
        _render_hotel_card(hotel, ringkasan.get("durasi", 1))

    # ── Itinerary Per Hari ───────────────────────────────────
    for day in days:
        _render_day_card(day, ringkasan.get("jumlah_orang", 1))


def _render_hotel_card(hotel: dict, durasi: int):
    """Render card hotel terpilih."""
    total = hotel.get("harga_per_malam", 0) * durasi
    fasilitas_str = " · ".join(hotel.get("fasilitas", []))

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 2rem;">🏨</span>
            <div>
                <h3 style="color: #e2e8f0; margin: 0; font-size: 1.3rem;">{hotel.get('nama', '')}</h3>
                <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 0.9rem;">
                    📍 {hotel.get('alamat', '')}
                </p>
            </div>
        </div>
        <p style="color: #cbd5e1; margin: 0 0 12px 0; font-size: 0.95rem;">
            {hotel.get('deskripsi', '')}
        </p>
        <div style="display: flex; gap: 24px; flex-wrap: wrap;">
            <div>
                <span style="color: #94a3b8; font-size: 0.8rem;">PER MALAM</span>
                <p style="color: #60a5fa; margin: 2px 0; font-weight: 600; font-size: 1.1rem;">
                    {format_rupiah(hotel.get('harga_per_malam', 0))}
                </p>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 0.8rem;">TOTAL ({durasi} MALAM)</span>
                <p style="color: #f472b6; margin: 2px 0; font-weight: 600; font-size: 1.1rem;">
                    {format_rupiah(total)}
                </p>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 0.8rem;">RATING</span>
                <p style="color: #fbbf24; margin: 2px 0; font-weight: 600; font-size: 1.1rem;">
                    ⭐ {hotel.get('rating', 0)}
                </p>
            </div>
        </div>
        <p style="color: #64748b; margin: 12px 0 0 0; font-size: 0.85rem;">
            🏷️ {fasilitas_str}
        </p>
    </div>
    """, unsafe_allow_html=True)


def _render_day_card(day: dict, jumlah_orang: int):
    """Render card untuk satu hari perjalanan."""
    hari = day.get("hari", 1)

    # Day header
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 12px 12px 0 0;
        padding: 16px 24px;
        margin-top: 16px;
    ">
        <h3 style="color: white; margin: 0; font-size: 1.2rem;">
            📅 Hari {hari}
        </h3>
    </div>
    """, unsafe_allow_html=True)

    # Destinations
    destinasi_html = ""
    waktu = 8  # Mulai jam 8 pagi

    for dest in day.get("destinasi", []):
        durasi_jam = dest.get("durasi_kunjungan_menit", 60)
        waktu_mulai = f"{waktu:02d}:00"
        waktu_selesai_h = waktu + durasi_jam // 60
        waktu_selesai_m = durasi_jam % 60
        waktu_selesai = f"{waktu_selesai_h:02d}:{waktu_selesai_m:02d}"

        tiket_str = "Gratis" if dest.get("harga_tiket", 0) == 0 else f"{format_rupiah(dest['harga_tiket'])}/orang"
        total_tiket = dest.get("harga_tiket", 0) * jumlah_orang

        jarak_info = dest.get("jarak_info", "")
        jarak_badge = ""
        if jarak_info:
            jarak_badge = f'<span style="background: rgba(59,130,246,0.2); color: #93c5fd; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem;">📏 {jarak_info}</span>'

        destinasi_html += f"""
        <div style="
            background: rgba(255,255,255,0.03);
            border-left: 3px solid #3b82f6;
            padding: 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                <div>
                    <p style="color: #60a5fa; margin: 0; font-size: 0.8rem; font-weight: 600;">
                        ⏰ {waktu_mulai} - {waktu_selesai}
                    </p>
                    <h4 style="color: #e2e8f0; margin: 4px 0; font-size: 1.1rem;">
                        📍 {dest.get('nama', '')}
                    </h4>
                    <p style="color: #94a3b8; margin: 0; font-size: 0.85rem;">
                        {dest.get('deskripsi', '')}
                    </p>
                </div>
                <div style="text-align: right;">
                    <p style="color: #fbbf24; margin: 0; font-size: 0.85rem;">🎫 {tiket_str}</p>
                    {'<p style="color: #f472b6; margin: 2px 0; font-size: 0.8rem;">Total: ' + format_rupiah(total_tiket) + '</p>' if total_tiket > 0 else ''}
                </div>
            </div>
            <div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span style="background: rgba(251,191,36,0.15); color: #fbbf24; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem;">
                    ⭐ {dest.get('rating', 0)}
                </span>
                <span style="background: rgba(16,185,129,0.15); color: #6ee7b7; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem;">
                    ⏱️ {format_durasi(dest.get('durasi_kunjungan_menit', 60))}
                </span>
                {jarak_badge}
            </div>
        </div>
        """
        waktu = waktu_selesai_h + 1  # 1 jam perjalanan antar destinasi

    # Kuliner
    kuliner_html = ""
    for meal in day.get("kuliner", []):
        emoji = {"Sarapan": "🌅", "Makan Siang": "☀️", "Makan Malam": "🌙"}.get(meal.get("waktu_makan", ""), "🍽️")
        kuliner_html += f"""
        <div style="
            background: rgba(255,255,255,0.03);
            border-left: 3px solid #f59e0b;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="color: #fbbf24; font-size: 0.8rem; font-weight: 600;">
                        {emoji} {meal.get('waktu_makan', '')}
                    </span>
                    <p style="color: #e2e8f0; margin: 4px 0 0 0; font-size: 1rem; font-weight: 500;">
                        {meal.get('nama', '')}
                    </p>
                    <p style="color: #94a3b8; margin: 2px 0 0 0; font-size: 0.8rem;">
                        {meal.get('kategori', '')} · {meal.get('jam_operasional', '')}
                    </p>
                </div>
                <div style="text-align: right;">
                    <p style="color: #fbbf24; margin: 0; font-size: 0.85rem;">
                        {format_rupiah(meal.get('harga_per_orang', 0))}/orang
                    </p>
                    <p style="color: #f472b6; margin: 2px 0 0 0; font-size: 0.8rem;">
                        Total: {format_rupiah(meal.get('total_biaya', 0))}
                    </p>
                </div>
            </div>
        </div>
        """

    st.markdown(f"""
    <div style="
        background: #1e293b;
        border-radius: 0 0 12px 12px;
        padding: 20px 24px;
        margin-bottom: 4px;
        border: 1px solid rgba(255,255,255,0.05);
        border-top: none;
    ">
        <h4 style="color: #93c5fd; margin: 0 0 12px 0; font-size: 1rem;">🏛️ Destinasi</h4>
        {destinasi_html}
        <h4 style="color: #fcd34d; margin: 20px 0 12px 0; font-size: 1rem;">🍽️ Kuliner</h4>
        {kuliner_html}
    </div>
    """, unsafe_allow_html=True)
