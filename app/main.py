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
from components.transport_card import render_transport_card, get_transport_cost
from core.itinerary_builder import build_itinerary
from services.openai_service import generate_narrative, generate_transport_recommendation

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="RENCANAIN — Perencanaan Wisata Cerdas",
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
st.markdown(
    '<div style="text-align:center;padding:40px 20px 30px;">'
    '<h1 style="font-size:3rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;line-height:1.2;">Rencanain</h1>'
    '<div style="display:inline-flex;align-items:center;gap:6px;background:rgba(251,191,36,0.12);border:1px solid rgba(251,191,36,0.35);color:#fbbf24;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:500;margin-top:10px;">'
    '⚠️ Demo AI · Hanya untuk keperluan demonstrasi'
    '</div>'
    '<p style="color:#94a3b8;font-size:1.15rem;margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto;">Rencanakan perjalanan wisata dengan kecerdasan buatan. Itinerary lengkap dalam hitungan detik.</p>'
    '<div style="display:flex;justify-content:center;gap:24px;margin-top:20px;flex-wrap:wrap;">'
    '<span style="color:#60a5fa;font-size:0.9rem;">🤖 AI-Powered</span>'
    '<span style="color:#a78bfa;font-size:0.9rem;">🗺️ Rute Optimal</span>'
    '<span style="color:#f472b6;font-size:0.9rem;">💰 Budget Smart</span>'
    '<span style="color:#34d399;font-size:0.9rem;">📍 30+ Destinasi</span>'
    '</div></div>',
    unsafe_allow_html=True,
)


# ── Session State Init ───────────────────────────────────────
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "narrative" not in st.session_state:
    st.session_state.narrative = None
if "transport_rec" not in st.session_state:
    st.session_state.transport_rec = None
if "transport_selected" not in st.session_state:
    st.session_state.transport_selected = 0
if "form_data" not in st.session_state:
    st.session_state.form_data = None

# ── Form Input ───────────────────────────────────────────────
form_data = render_form()


# ── Process: hanya saat form di-submit ───────────────────────
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
            st.session_state.itinerary = itinerary
            st.session_state.form_data = form_data

            # Generate transport recommendation (LLM)
            transport_rec = generate_transport_recommendation(
                kota_asal=form_data["kota_asal"],
                jumlah_orang=form_data["jumlah_orang"],
                budget=form_data["budget"],
            )
            st.session_state.transport_rec = transport_rec

            # Generate narrative
            narrative = generate_narrative(itinerary)
            st.session_state.narrative = narrative

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")
            st.exception(e)


# ── Render Results: selalu tampil selama ada data ────────────
if st.session_state.itinerary:
    itinerary = st.session_state.itinerary

    st.markdown("<hr>", unsafe_allow_html=True)

    # Tabs untuk hasil
    tab1, tab2, tab3 = st.tabs([
        "📋 Itinerary",
        "🗺️ Peta Rute",
        "💰 Budget",
    ])

    with tab1:
        # Transport card (di awal)
        if st.session_state.transport_rec:
            transport_options = st.session_state.transport_rec
            fd = st.session_state.form_data or {}
            jumlah_orang = fd.get("jumlah_orang", 2)
            kota_asal = fd.get("kota_asal", "")

            # Selectbox untuk pilih moda
            option_labels = [
                f"{opt.get('emoji', '')} {opt.get('moda', '')} — {opt.get('durasi', '')}"
                for opt in transport_options
            ]
            selected = st.selectbox(
                "🚆 Pilih Moda Transportasi",
                options=range(len(option_labels)),
                format_func=lambda x: option_labels[x],
                index=st.session_state.transport_selected,
                key="transport_select",
            )
            st.session_state.transport_selected = selected

            render_transport_card(kota_asal, transport_options, jumlah_orang, selected)
            st.markdown('<hr style="border-color:rgba(255,255,255,0.06);margin:24px 0;">', unsafe_allow_html=True)

        render_itinerary(itinerary)

        # Narrative
        if st.session_state.narrative:
            with st.expander("📝 Narasi Perjalanan (AI Generated)", expanded=False):
                st.markdown(st.session_state.narrative)

    with tab2:
        render_map(itinerary)

    with tab3:
        # Hitung transport cost dari opsi yang dipilih
        transport_cost = 0
        if st.session_state.transport_rec and st.session_state.form_data:
            transport_cost = get_transport_cost(
                st.session_state.transport_rec,
                st.session_state.transport_selected,
                st.session_state.form_data.get("jumlah_orang", 2),
            )

        # Update estimasi biaya dengan transport cost
        estimasi = dict(itinerary["estimasi_biaya"])
        estimasi["transport"] = transport_cost
        estimasi["total"] = estimasi["hotel"] + estimasi["wisata"] + estimasi["kuliner"] + transport_cost
        estimasi["sisa_budget"] = itinerary["alokasi_budget"]["total"] - estimasi["total"]

        render_budget_summary(estimasi, itinerary["alokasi_budget"])


# ── Footer ───────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:40px 20px;margin-top:60px;border-top:1px solid rgba(255,255,255,0.06);">'
    '<p style="color:#475569;font-size:0.85rem;margin:0;">BandungTrip AI v1.0 · Microsoft Elevate Hackathon 2025</p>'
    '<p style="color:#334155;font-size:0.75rem;margin-top:4px;">Powered by Azure OpenAI · Azure AI Search · Azure Maps</p>'
    '</div>',
    unsafe_allow_html=True,
)
