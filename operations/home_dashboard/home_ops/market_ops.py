# operations/home_dashboard/home_ops/market_ops.py
# Header (holiday + VIX), index cards and SMA breadth - all fed by ONE get_market_data() call.

from datetime import date, datetime

import streamlit as st

from core.styles import COLOR_MAP
from operations.home_dashboard.home_ops.home_data import (
    SERIES_COLORS,
    get_index_cards,
)

BREADTH_DAYS = 30

# DB keys -> display labels
_BREADTH_KEYS = {"ema10": "EMA 10", "sma20": "SMA 20", "sma50": "SMA 50", "sma200": "SMA 200"}


# ----------------------------------------------------------
# SINGLE DATA LOADER (shared by header + breadth)
# ----------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)   # EOD data, so 15 minutes is plenty
def _load_market_data() -> dict:
    # IMPORTANT: lazy import
    from services.equity.yahoo.yahoo_data_service import get_market_data

    data = get_market_data()
    if not data:
        # get_market_data() returns {} on failure; raising keeps that out of the cache
        raise ValueError("Market data unavailable")
    return data


def _get_market_data() -> dict:
    try:
        return _load_market_data()
    except Exception:
        return {}


# ----------------------------------------------------------
# VIX
# ----------------------------------------------------------
def _parse_vix(raw):
    """vix_data is a DataFrame: date, vix, vix_change, vix_regime, vix_signal, ...
    Returns {'value', 'change', 'regime'} for the latest row, or None."""
    # IMPORTANT: lazy import
    import pandas as pd

    if not isinstance(raw, pd.DataFrame) or raw.empty:
        return None
    df = raw.sort_values("date") if "date" in raw.columns else raw
    row = df.iloc[-1]
    try:
        value = float(row["vix"])
    except (KeyError, TypeError, ValueError):
        return None

    change = row.get("vix_change")
    regime = row.get("vix_regime")
    signal = row.get("vix_signal")
    parts = [str(x) for x in (regime, signal) if pd.notna(x) and str(x).strip()]

    return {
        "value": value,
        "change": float(change) if pd.notna(change) else None,
        "regime": " • ".join(parts),
    }


# ----------------------------------------------------------
# HOLIDAY
# ----------------------------------------------------------
def _countdown_text(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%d %b %Y").date()
    except (TypeError, ValueError):
        return ""
    days = (d - date.today()).days
    if days <= 0:
        return "Today"
    return f"{days} day{'s' if days != 1 else ''} left"


# ----------------------------------------------------------
# HEADER SECTION
# ----------------------------------------------------------
def handle_header_section():
    data = _get_market_data()

    # Next NSE holiday
    hol = data.get("next_holiday")
    if hol:
        left_txt = _countdown_text(hol["date"])
        left_html = f'{hol["name"]} &nbsp;·&nbsp; {hol["day"]}'
        right_html = f'{left_txt} ({hol["date"]})' if left_txt else hol["date"]
    else:
        left_html, right_html = "No upcoming NSE holiday found", ""

    st.markdown(
        f"""
<div class="card row">
  <div class="event">🗓️&nbsp; NSE Holiday: {left_html}</div>
  <div class="event" style="font-weight:500">{right_html}</div>
</div>""",
        unsafe_allow_html=True,
    )
    st.write("")

    # VIX
    vix = _parse_vix(data.get("vix_data"))
    if vix:
        chg = vix["change"]
        chg_html = ""
        if chg is not None:
            cls = "neg" if chg < 0 else "pos"
            chg_html = f'<span class="chg {cls}">({chg:+.2f})</span>'
        left = f'🇮🇳 VIX {vix["value"]:.2f}{chg_html}'
        right = vix["regime"]
    else:
        left, right = "🇮🇳 VIX unavailable", ""

    st.markdown(
        f"""
<div class="card row">
  <div class="vix">{left}</div>
  <div class="regime">{right}</div>
</div>""",
        unsafe_allow_html=True,
    )
    st.write("")


# ----------------------------------------------------------
# INDEX CARDS (still static)
# ----------------------------------------------------------
def _index_card(i: dict) -> str:
    return f"""
<div class="card idx {i['bias']}">
  <div class="row"><div class="name">{i['name']}</div><div class="badge {i['bias']}">{i['bias']}</div></div>
  <div class="metrics">
    <span>OI <b>{i['oi']:.2f}</b></span>
    <span>VOL <b>{i['vol']:.2f}</b></span>
    <span>ΔOI <b>{i['doi']:.2f}</b></span>
  </div>
  <div class="expiry">Expiry: {i['expiry']}</div>
</div>"""


def handle_index_section():
    cards = get_index_cards()
    for start in range(0, len(cards), 4):
        cols = st.columns(4)
        for col, c in zip(cols, cards[start:start + 4]):
            col.markdown(_index_card(c), unsafe_allow_html=True)
        st.write("")


# ----------------------------------------------------------
# SMA BREADTH SECTION
# ----------------------------------------------------------
def _build_chart(rows: list):
    # IMPORTANT: lazy import - plotly is heavy
    import plotly.graph_objects as go

    rows = list(reversed(rows[:BREADTH_DAYS]))        # DB is newest-first -> oldest-first
    dates = [r["date"].strftime("%a, %d %b") if hasattr(r["date"], "strftime") else str(r["date"]) for r in rows]

    fig = go.Figure()
    for key, label in _BREADTH_KEYS.items():
        fig.add_trace(go.Scatter(
            x=dates, y=[r[key] for r in rows], name=label, mode="lines",
            line=dict(color=SERIES_COLORS[label], width=2),
        ))
    fig.update_layout(
        height=330, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="v", x=1.01, y=1),
        xaxis=dict(showgrid=True, gridcolor=COLOR_MAP["gray-10"], tickangle=-30, nticks=7),
        yaxis=dict(showgrid=True, gridcolor=COLOR_MAP["gray-10"], range=[0, 100]),
    )
    return fig


def _render_panel(col, flag: str, payload: dict, key: str):
    rows = (payload or {}).get("breadth") or []
    with col:
        if not rows:
            st.markdown(
                f'<div class="card"><div class="sma-title">{flag} SMA Breadth</div>'
                f'<div class="expiry" style="text-align:center">No breadth data available.</div></div>',
                unsafe_allow_html=True,
            )
            return

        latest = rows[0]
        pills = "".join(
            f'<div class="pill {"" if latest[k] >= 50 else "bear"}"><div class="l">{label}</div>'
            f'<div class="v">{latest[k]:.1f}%</div>'
            f'<div class="s">{"Bullish" if latest[k] >= 50 else "Bearish"}</div></div>'
            for k, label in _BREADTH_KEYS.items()
        )
        st.markdown(
            f'<div class="card"><div class="sma-title">{flag} SMA Breadth (Last {BREADTH_DAYS} days)</div>'
            f'<div class="pills">{pills}</div></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(_build_chart(rows), width="stretch",
                        config={"displayModeBar": False}, key=key)


def handle_breadth_section():
    data = _get_market_data()
    left, right = st.columns(2)
    _render_panel(left, "🇮🇳", data.get("india_sma_breadth") or {}, "breadth_IN")
    _render_panel(right, "🇺🇸", data.get("usa_sma_breadth") or {}, "breadth_US")