"""
transport_card.py — Tampilan card rekomendasi transportasi.
"""

import streamlit as st
from utils.formatter import format_rupiah


def render_transport_card(kota_asal: str, transport_options: list[dict],
                          jumlah_orang: int, selected_idx: int = 0):
    """
    Render card rekomendasi transportasi dengan opsi yang bisa dipilih.

    Args:
        kota_asal: kota asal perjalanan
        transport_options: list of dict dari generate_transport_recommendation
        jumlah_orang: jumlah orang (untuk kalkulasi total)
        selected_idx: index opsi yang dipilih saat ini
    """
    if not transport_options:
        return

    # Header
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f4c75 0%,#1b262c 100%);border-radius:12px 12px 0 0;padding:20px 24px;margin-top:16px;">'
        f'<h3 style="color:white;margin:0;font-size:1.2rem;">🚆 Transportasi: {kota_asal} → Bandung</h3>'
        f'<p style="color:rgba(255,255,255,0.7);margin:4px 0 0;font-size:0.85rem;">Pilih moda transportasi untuk perhitungan budget</p></div>',
        unsafe_allow_html=True,
    )

    # Transport options container
    st.markdown(
        '<div style="background:#1e293b;border-radius:0 0 12px 12px;padding:20px 24px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.05);border-top:none;">',
        unsafe_allow_html=True,
    )

    # Render each option as a card
    for i, opt in enumerate(transport_options):
        emoji = opt.get("emoji", "🚌")
        moda = opt.get("moda", "")
        harga_min = opt.get("harga_min", 0)
        harga_max = opt.get("harga_max", 0)
        durasi = opt.get("durasi", "")
        keterangan = opt.get("keterangan", "")
        tujuan = opt.get("tujuan_bandung", "")

        harga_avg = (harga_min + harga_max) // 2
        total_est = harga_avg * jumlah_orang

        is_selected = (i == selected_idx)
        border_color = "#3b82f6" if is_selected else "rgba(255,255,255,0.08)"
        bg_selected = "rgba(59,130,246,0.1)" if is_selected else "rgba(255,255,255,0.03)"
        check = "✅ " if is_selected else ""

        card = (
            f'<div style="background:{bg_selected};border:2px solid {border_color};border-radius:10px;padding:16px;margin:8px 0;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<span style="font-size:1.8rem;">{emoji}</span>'
            f'<div>'
            f'<h4 style="color:#e2e8f0;margin:0;font-size:1.05rem;">{check}{moda}</h4>'
            f'<p style="color:#94a3b8;margin:2px 0 0;font-size:0.8rem;">{keterangan}</p>'
            f'</div></div>'
            f'<div style="text-align:right;">'
            f'<p style="color:#fbbf24;margin:0;font-size:0.85rem;">{format_rupiah(harga_min)} - {format_rupiah(harga_max)}/orang</p>'
            f'<p style="color:#f472b6;margin:2px 0 0;font-size:0.8rem;">Est. total: {format_rupiah(total_est)} ({jumlah_orang} orang)</p>'
            f'</div></div>'
            f'<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">'
            f'<span style="background:rgba(59,130,246,0.15);color:#93c5fd;padding:2px 8px;border-radius:10px;font-size:0.75rem;">⏱️ {durasi}</span>'
            f'<span style="background:rgba(16,185,129,0.15);color:#6ee7b7;padding:2px 8px;border-radius:10px;font-size:0.75rem;">📍 {tujuan}</span>'
            f'</div></div>'
        )
        st.markdown(card, unsafe_allow_html=True)

    # Close container
    st.markdown('</div>', unsafe_allow_html=True)


def get_transport_cost(transport_options: list[dict], selected_idx: int,
                       jumlah_orang: int) -> int:
    """
    Hitung estimasi biaya transport berdasarkan opsi yang dipilih.

    Returns biaya total (rata-rata harga min dan max × jumlah orang).
    """
    if not transport_options or selected_idx >= len(transport_options):
        return 0

    opt = transport_options[selected_idx]
    harga_avg = (opt.get("harga_min", 0) + opt.get("harga_max", 0)) // 2
    return harga_avg * jumlah_orang
