"""Shared Streamlit theme styles and layout helpers."""

from __future__ import annotations

APP_CSS = """
<style>
  /* ── Layout ───────────────────────────────────────────────── */
  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1180px; }

  /* ── Hero banner ──────────────────────────────────────────── */
  .diag-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0f766e 100%);
    color: #f8fafc; padding: 1.25rem 1.5rem; border-radius: 14px;
    margin-bottom: 1rem; box-shadow: 0 8px 24px rgba(15,23,42,.18);
  }
  .diag-hero h1 { color: #fff !important; font-size: 1.55rem !important; margin: 0 0 .35rem 0 !important; }
  .diag-hero p  { color: #cbd5e1 !important; margin: 0; font-size: .92rem; line-height: 1.45; }
  .diag-pill-row { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .85rem; }
  .diag-pill {
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
    border-radius: 999px; padding: .25rem .7rem; font-size: .75rem; color: #e2e8f0;
  }

  /* ── "How it works" step cards ───────────────────────────── */
  .diag-step-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: .75rem .9rem; min-height: 88px;
  }
  .diag-step-card strong { display: block; font-size: .72rem; text-transform: uppercase;
    letter-spacing: .04em; color: #64748b; margin-bottom: .2rem; }
  .diag-step-card span { font-size: .86rem; color: #0f172a; line-height: 1.35; }

  /* ── Sidebar ─────────────────────────────────────────────── */
  div[data-testid="stSidebar"] { background: #f8fafc; }
  div[data-testid="stSidebar"] .stRadio label { font-weight: 500; }

  /* ── Tabs ────────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] { height: 42px; padding: 0 18px; border-radius: 8px 8px 0 0; }

  /* ── Status badges ───────────────────────────────────────── */
  .badge {
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    font-size: .72rem; font-weight: 600; letter-spacing: .03em;
  }
  .badge-submitted  { background: #dbeafe; color: #1d4ed8; }
  .badge-approved   { background: #d1fae5; color: #065f46; }
  .badge-denied     { background: #fee2e2; color: #991b1b; }
  .badge-closed     { background: #e2e8f0; color: #475569; }
  .badge-open       { background: #fef9c3; color: #854d0e; }
  .badge-in-progress{ background: #e0f2fe; color: #0369a1; }
  .badge-resolved   { background: #d1fae5; color: #065f46; }
  .badge-high       { background: #fee2e2; color: #991b1b; }
  .badge-medium     { background: #fef3c7; color: #92400e; }
  .badge-low        { background: #d1fae5; color: #065f46; }

  /* ── Claim / case cards ──────────────────────────────────── */
  .card {
    border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px;
    margin-bottom: 6px; background: #fff;
  }
  .card-header {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 8px; margin-bottom: 8px;
  }
  .card-title { font-size: .92rem; font-weight: 600; color: #0f172a; }
  .card-sub   { font-size: .78rem; color: #64748b; margin-top: 2px; }
  .card-meta-row {
    display: flex; flex-wrap: wrap; gap: 6px 14px;
    font-size: .78rem; color: #475569; margin-top: 6px;
  }
  .card-meta-row strong { color: #0f172a; }

  /* ── Agent priority row ──────────────────────────────────── */
  .priority-critical { border-left: 4px solid #dc2626 !important; }
  .priority-high     { border-left: 4px solid #ea580c !important; }

  /* ── Section header accent ───────────────────────────────── */
  .section-header {
    font-size: .78rem; text-transform: uppercase; letter-spacing: .06em;
    color: #64748b; padding-bottom: 4px; border-bottom: 1px solid #e2e8f0;
    margin-bottom: 10px;
  }

  /* ── Metrics row ─────────────────────────────────────────── */
  .metric-pill {
    display: inline-flex; flex-direction: column; align-items: center;
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 10px 18px; min-width: 90px;
  }
  .metric-pill .mval { font-size: 1.4rem; font-weight: 700; color: #0f172a; }
  .metric-pill .mlbl { font-size: .7rem; text-transform: uppercase; color: #64748b;
    letter-spacing: .04em; margin-top: 2px; }

  /* ── Mermaid iframe safety ───────────────────────────────── */
  iframe { border: none !important; }
</style>
"""


def inject_theme() -> None:
    import streamlit as st

    st.markdown(APP_CSS, unsafe_allow_html=True)
