"""
form_input.py — Render 5 field form input wisata.
"""

import streamlit as st
from utils.validator import validate_form, PREFERENSI_OPTIONS


def render_form() -> dict | None:
    """
    Render form input dan return data form jika valid.
    Returns None jika form belum disubmit atau invalid.
    """
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        border: 1px solid rgba(255,255,255,0.08);
    ">
        <h2 style="
            color: #e2e8f0;
            margin: 0 0 8px 0;
            font-size: 1.5rem;
        ">📝 Rencanakan Perjalananmu</h2>
        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">
            Isi form di bawah untuk mendapatkan itinerary wisata Bandung yang teroptimasi.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("trip_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            kota_asal = st.text_input(
                "🏙️ Kota Asal",
                placeholder="contoh: Jakarta, Surabaya, Bekasi",
                help="Kota keberangkatan kamu",
            )

            durasi = st.selectbox(
                "📅 Durasi Perjalanan",
                options=[1, 2, 3, 4, 5, 6, 7],
                index=2,
                format_func=lambda x: f"{x} hari",
                help="Berapa lama kamu ingin berlibur?",
            )

            jumlah_orang = st.number_input(
                "👥 Jumlah Orang",
                min_value=1,
                max_value=20,
                value=2,
                step=1,
                help="Total rombongan termasuk kamu",
            )

        with col2:
            budget = st.number_input(
                "💰 Total Budget (Rp)",
                min_value=100_000,
                max_value=100_000_000,
                value=2_000_000,
                step=100_000,
                format="%d",
                help="Total keseluruhan perjalanan (bukan per orang)",
            )

            preferensi = st.multiselect(
                "🎯 Preferensi Wisata",
                options=PREFERENSI_OPTIONS,
                default=["Alam", "Kuliner"],
                help="Pilih minimal 1 preferensi",
            )

        # Budget info
        if budget and jumlah_orang and durasi:
            per_orang_per_hari = budget / jumlah_orang / durasi
            st.markdown(f"""
            <div style="
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 8px;
            ">
                <span style="color: #93c5fd; font-size: 0.9rem;">
                    💡 Budget per orang per hari: <strong>Rp {per_orang_per_hari:,.0f}</strong>
                </span>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🚀 Buat Itinerary!",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            is_valid, error_msg = validate_form(
                kota_asal, durasi, jumlah_orang, budget, preferensi
            )

            if not is_valid:
                st.error(f"⚠️ {error_msg}")
                return None

            return {
                "kota_asal": kota_asal.strip(),
                "durasi": durasi,
                "jumlah_orang": jumlah_orang,
                "budget": budget,
                "preferensi": preferensi,
            }

    return None
