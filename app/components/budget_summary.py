"""
budget_summary.py — Breakdown & progress bar budget.
"""

import streamlit as st
from utils.formatter import format_rupiah


def render_budget_summary(estimasi: dict, alokasi: dict):
    """Render ringkasan dan breakdown budget."""
    total_budget = alokasi.get("total", 0)
    total_actual = estimasi.get("total", 0)
    sisa = estimasi.get("sisa_budget", 0)
    pct_used = (total_actual / total_budget * 100) if total_budget > 0 else 0

    if sisa >= 0:
        status_color = "#10b981"
        status_text = f"Sisa Budget: {format_rupiah(sisa)}"
        status_icon = "✅"
    else:
        status_color = "#ef4444"
        status_text = f"Over Budget: {format_rupiah(abs(sisa))}"
        status_icon = "⚠️"

    # Header & Progress
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:16px;padding:28px;margin:24px 0;border:1px solid rgba(255,255,255,0.08);">'
        f'<h3 style="color:#e2e8f0;margin:0 0 20px 0;font-size:1.4rem;">💰 Ringkasan Budget</h3>'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
        f'<span style="color:#94a3b8;font-size:0.85rem;">Terpakai</span>'
        f'<span style="color:#e2e8f0;font-size:0.85rem;font-weight:600;">{format_rupiah(total_actual)} / {format_rupiah(total_budget)}</span></div>'
        f'<div style="background:rgba(255,255,255,0.08);border-radius:10px;height:12px;overflow:hidden;">'
        f'<div style="background:linear-gradient(90deg,#3b82f6,{status_color});height:100%;width:{min(pct_used,100):.1f}%;border-radius:10px;"></div></div>'
        f'<p style="color:#64748b;text-align:right;margin:4px 0 0;font-size:0.8rem;">{pct_used:.1f}% terpakai</p>'
        f'<div style="background:rgba(255,255,255,0.05);border:1px solid {status_color}40;border-radius:8px;padding:12px;margin:16px 0;text-align:center;">'
        f'<span style="color:{status_color};font-weight:600;">{status_icon} {status_text}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Category breakdown
    categories = [
        ("🏨 Hotel", estimasi.get("hotel", 0), alokasi.get("hotel", 0), "#3b82f6"),
        ("🏛️ Wisata", estimasi.get("wisata", 0), alokasi.get("wisata", 0), "#8b5cf6"),
        ("🍽️ Kuliner", estimasi.get("kuliner", 0), alokasi.get("kuliner", 0), "#f59e0b"),
        ("🚗 Transport", estimasi.get("transport", 0), alokasi.get("transport", 0), "#10b981"),
    ]

    cols = st.columns(4)
    for i, (label, actual, allocated, color) in enumerate(categories):
        cat_pct = (actual / allocated * 100) if allocated > 0 else 0
        with cols[i]:
            st.markdown(
                f'<div style="background:#1e293b;border-radius:10px;padding:16px;border:1px solid rgba(255,255,255,0.06);text-align:center;">'
                f'<p style="color:#94a3b8;margin:0;font-size:0.85rem;">{label}</p>'
                f'<p style="color:{color};margin:4px 0;font-weight:700;font-size:1.1rem;">{format_rupiah(actual)}</p>'
                f'<div style="background:rgba(255,255,255,0.08);border-radius:6px;height:6px;overflow:hidden;margin:8px 0 4px;">'
                f'<div style="background:{color};height:100%;width:{min(cat_pct,100):.1f}%;border-radius:6px;"></div></div>'
                f'<p style="color:#64748b;margin:0;font-size:0.75rem;">dari {format_rupiah(allocated)}</p></div>',
                unsafe_allow_html=True,
            )
