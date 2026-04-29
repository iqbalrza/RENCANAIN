"""
main.py — BandungTrip AI: Entry point Streamlit app.
Render form input & tampilan hasil itinerary.
"""

import sys
import os
import streamlit as st

# Pastikan app/ ada di sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.form_input import render_form
from components.itinerary_card import render_itinerary
from components.budget_summary import render_budget_summary
from components.map_view import render_map
from core.itinerary_builder import build_itinerary
from services.openai_service import generate_narrative

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="BandungTrip AI — Perencanaan Wisata Cerdas",
    page_icon="🌄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        background: linear-gradient(180deg, #0a0a1a 0%, #0f172a 30%, #1a1a2e 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Header area */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Main container */
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Form styling */
    .stForm {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
    }

    /* Button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 32px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }

    /* Labels */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stMultiSelect label {
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94a3b8;
        border-radius: 8px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)


# ── Hero Section ─────────────────────────────────────────────
st.markdown("""
<div style="
    text-align: center;
    padding: 40px 20px 30px;
">
    <h1 style="
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    ">
        🌄 BandungTrip AI
    </h1>
    <p style="
        color: #94a3b8;
        font-size: 1.15rem;
        margin-top: 12px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    ">
        Rencanakan perjalanan wisata ke Bandung dengan kecerdasan buatan.
        Itinerary lengkap dalam hitungan detik.
    </p>
    <div style="
        display: flex;
        justify-content: center;
        gap: 24px;
        margin-top: 20px;
        flex-wrap: wrap;
    ">
        <span style="color: #60a5fa; font-size: 0.9rem;">🤖 AI-Powered</span>
        <span style="color: #a78bfa; font-size: 0.9rem;">🗺️ Rute Optimal</span>
        <span style="color: #f472b6; font-size: 0.9rem;">💰 Budget Smart</span>
        <span style="color: #34d399; font-size: 0.9rem;">📍 30+ Destinasi</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Form Input ───────────────────────────────────────────────
form_data = render_form()


# ── Process & Render Results ─────────────────────────────────
if form_data:
    with st.spinner("🤖 Memproses itinerary..."):
        try:
            # Build itinerary
            itinerary = build_itinerary(
                kota_asal=form_data["kota_asal"],
                durasi=form_data["durasi"],
                jumlah_orang=form_data["jumlah_orang"],
                budget=form_data["budget"],
                preferensi=form_data["preferensi"],
            )

            st.markdown("<hr>", unsafe_allow_html=True)

            # Tabs untuk hasil
            tab1, tab2, tab3 = st.tabs([
                "📋 Itinerary",
                "🗺️ Peta Rute",
                "💰 Budget",
            ])

            with tab1:
                render_itinerary(itinerary)

                # Narrative (if OpenAI available)
                narrative = generate_narrative(itinerary)
                if narrative:
                    with st.expander("📝 Narasi Perjalanan (AI Generated)", expanded=False):
                        st.markdown(narrative)

            with tab2:
                render_map(itinerary)

            with tab3:
                render_budget_summary(
                    itinerary["estimasi_biaya"],
                    itinerary["alokasi_budget"],
                )

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")
            st.exception(e)


# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<div style="
    text-align: center;
    padding: 40px 20px;
    margin-top: 60px;
    border-top: 1px solid rgba(255,255,255,0.06);
">
    <p style="color: #475569; font-size: 0.85rem; margin: 0;">
        BandungTrip AI v1.0 · Microsoft Elevate Hackathon 2025
    </p>
    <p style="color: #334155; font-size: 0.75rem; margin-top: 4px;">
        Powered by Azure OpenAI · Azure AI Search · Azure Maps
    </p>
</div>
""", unsafe_allow_html=True)
