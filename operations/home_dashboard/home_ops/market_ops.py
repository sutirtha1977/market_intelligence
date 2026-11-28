# operations/home_dashboard/home_ops/market_ops.py
# Header (holiday + VIX + SRT) - fed by ONE get_market_data() call.

import html
from datetime import date, datetime
from typing import Optional

import streamlit as st


# ----------------------------------------------------------
# SINGLE DATA LOADER
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


def _get_market_data(progress_placeholder=None) -> dict:
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
# NIFTY 50 SRT
# ----------------------------------------------------------
def _parse_srt(raw: Optional[dict]):
    if not isinstance(raw, dict) or raw.get("srt") is None:
        return None
    try:
        value = float(raw["srt"])
    except (TypeError, ValueError):
        return None

    d = raw.get("date")
    as_of = d.strftime("%d %b") if isinstance(d, date) else (str(d) if d else "")

    return {
        "name": str(raw.get("index_name") or "Nifty 50"),
        "value": value,
        "as_of": as_of,
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
#   line 1: next NSE holiday
#   line 2: India VIX | Nifty 50 SRT (equal-width columns)
# ----------------------------------------------------------
def handle_header_section(progress_placeholder=None):
    data = _get_market_data(progress_placeholder)

    # ---------- Line 1: next NSE holiday ----------
    hol = data.get("next_holiday")
    if hol:
        left_txt = _countdown_text(hol["date"])
        when = f'{left_txt} · {hol["date"]}' if left_txt else hol["date"]
        hol_html = (
            f'<div class="grp"><span class="lbl">Next NSE holiday</span>'
            f'<span class="txt">{hol["name"]} <span class="muted">({hol["day"]})</span></span></div>'
            f'<div class="grp grow"><span class="txt muted">{when}</span></div>'
        )
    else:
        hol_html = (
            '<div class="grp"><span class="lbl">Next NSE holiday</span>'
            '<span class="txt muted">none found</span></div>'
        )

    st.markdown(f'<div class="card strip">{hol_html}</div>', unsafe_allow_html=True)
    st.write("")

    # ---------- Line 2: India VIX | Nifty 50 SRT ----------
    vix = _parse_vix(data.get("vix_data"))
    if vix:
        chg = vix["change"]
        chg_html = ""
        if chg is not None:
            cls = "neg" if chg < 0 else "pos"
            chg_html = f'<span class="chg {cls}">{chg:+.2f}</span>'
        tag_html = f'<span class="tag">{vix["regime"]}</span>' if vix["regime"] else ""
        vix_html = (
            f'<div class="grp"><span class="lbl">India VIX</span>'
            f'<span class="val">{vix["value"]:.2f}</span>{chg_html}{tag_html}</div>'
        )
    else:
        vix_html = '<div class="grp"><span class="lbl">India VIX</span><span class="txt muted">unavailable</span></div>'

    srt = _parse_srt(data.get("nifty50_srt"))
    if srt:
        as_of = f'<span class="lbl">as of {srt["as_of"]}</span>' if srt["as_of"] else ""
        srt_html = (
            f'<div class="grp"><span class="lbl">{html.escape(srt["name"])} SRT</span>'
            f'<span class="val">{srt["value"]:.2f}</span>{as_of}</div>'
        )
    else:
        srt_html = '<div class="grp"><span class="lbl">Nifty 50 SRT</span><span class="txt muted">unavailable</span></div>'

    st.markdown(
        f'<div class="card strip split">{vix_html}{srt_html}</div>',
        unsafe_allow_html=True,
    )
    st.write("")