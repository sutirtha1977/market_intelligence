# operations/home_dashboard/home_ops/market_ops.py
# Header (holiday + VIX + USD/INR + Gold) - fed by ONE get_market_data() call.

import math
from datetime import date, datetime
from typing import Optional

import streamlit as st

# Quote tiles on line 2 after VIX: (key in market data, label, value prefix)
_QUOTES = [
    ("USD/INR", "USD/INR", ""),
    ("GOLD", "Gold", "$"),
]


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
# PRICE QUOTES (USD/INR, Gold)
# ----------------------------------------------------------
def _num(x) -> Optional[float]:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _parse_quote(raw: Optional[dict]):
    """raw = one price row (adj_close, close, pct_price_change, ...) -> {'value','pct'} or None."""
    if not isinstance(raw, dict):
        return None
    value = _num(raw.get("adj_close")) or _num(raw.get("close"))   # adj_close 0 / missing -> close
    if value is None:
        return None
    return {"value": value, "pct": _num(raw.get("pct_price_change"))}


def _quote_group(label: str, prefix: str, q: Optional[dict]) -> str:
    if not q:
        return (
            f'<div class="grp"><span class="lbl">{label}</span>'
            f'<span class="txt muted">unavailable</span></div>'
        )
    pct_html = ""
    if q["pct"] is not None:
        cls = "neg" if q["pct"] < 0 else "pos"
        pct_html = f'<span class="chg {cls}">{q["pct"]:+.2f}%</span>'
    return (
        f'<div class="grp"><span class="lbl">{label}</span>'
        f'<span class="val">{prefix}{q["value"]:,.2f}</span>{pct_html}</div>'
    )


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
#   line 2: India VIX | USD/INR | Gold (equal-width columns)
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

    # ---------- Line 2: India VIX | USD/INR | Gold ----------
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

    quotes_html = "".join(
        _quote_group(label, prefix, _parse_quote(data.get(key)))
        for key, label, prefix in _QUOTES
    )

    st.markdown(
        f'<div class="card strip split c3">{vix_html}{quotes_html}</div>',
        unsafe_allow_html=True,
    )
    st.write("")