# operations/home_dashboard/home_ops/home_styles.py
# Home screen CSS - all colors / fonts / shadows come from core/styles.py

import re

import streamlit as st

from core.styles import (
    COLOR_MAP,
    FONT_FAMILY,
    FONT_SIZE,
    CARD_SHADOW,
    CARD_SHADOW_HOVER,
)

# Tokens: {{color-key}} -> COLOR_MAP value, plus {{font}}, {{font-size}}, {{shadow}}, {{shadow-hover}}
_CSS = """
<style>
    .card, .card * {font-family:{{font}};}
    .card {
        background:{{bg-card}}; border:1px solid {{card-border}}; border-radius:12px;
        padding:14px 18px; box-shadow:{{shadow}}; color:{{text-primary}}; font-size:{{font-size}};
    }

    /* hero */
    .hero {background:linear-gradient(90deg,{{bg-surface}},{{hover-blue}}); padding:16px 20px;}
    .hero h1 {margin:0; padding:0; font-size:1.45rem; font-weight:700; color:{{text-primary}}; display:flex; align-items:center; gap:12px;}
    .hero h1:before {content:""; width:6px; height:24px; border-radius:4px; background:{{primary}}; display:inline-block;}

    /* rows: event / vix */
    .row {display:flex; justify-content:space-between; align-items:center;}
    .event {font-weight:600; color:{{text-primary}}; font-size:.9rem;}
    .vix {font-size:1.2rem; font-weight:700; color:{{blue-70}};}
    .vix .chg {font-size:.85rem; margin-left:8px;}
    .neg {color:{{bearish}};} .pos {color:{{bullish}};}
    .regime {font-weight:700; font-size:.8rem; letter-spacing:.04em; color:{{text-primary}};}

    /* index cards */
    .idx {border-left:5px solid; padding:12px 16px; transition:box-shadow .15s ease;}
    .idx:hover {box-shadow:{{shadow-hover}};}
    .idx.BULLISH {border-left-color:{{bullish}};}
    .idx.NEUTRAL {border-left-color:{{signal-hold}};}
    .idx.BEARISH {border-left-color:{{bearish}};}
    .idx .name {color:{{blue-70}}; font-weight:700; font-size:.95rem;}
    .badge {color:{{text-inverse}}; font-weight:700; padding:3px 10px; border-radius:5px; font-size:.7rem; letter-spacing:.03em;}
    .badge.BULLISH {background:{{bullish}};}
    .badge.NEUTRAL {background:{{signal-hold}};}
    .badge.BEARISH {background:{{bearish}};}
    .metrics {display:flex; justify-content:space-between; margin:10px 0 6px; font-size:.9rem; color:{{text-primary}};}
    .expiry {color:{{text-secondary}}; font-size:.72rem;}

    /* SMA breadth */
    .sma-title {text-align:center; color:{{blue-70}}; font-weight:700; font-size:.9rem; margin-bottom:10px;}
    .pills {display:grid; grid-template-columns:repeat(4,1fr); gap:10px;}
    .pill {background:{{bullish-bg}}; border:2px solid {{green-40}}; border-radius:10px; text-align:center; padding:8px 4px;}
    .pill .l {font-size:.78rem; font-weight:700; color:{{text-primary}};}
    .pill .v {font-weight:700; font-size:1.05rem; color:{{bullish}}; margin:1px 0;}
    .pill .s {color:{{bullish}}; font-weight:600; font-size:.72rem;}
    .pill.bear {background:{{bearish-bg}}; border-color:{{red-30}};}
    .pill.bear .v, .pill.bear .s {color:{{bearish}};}

    /* news */
    .news-head {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid {{border-light}}; padding-bottom:12px; margin-bottom:6px;}
    .news-head h2 {margin:0; padding:0; color:{{blue-80}}; font-size:1.1rem; font-weight:700;}
    .news-head span {font-size:.8rem; font-weight:600; color:{{text-primary}};}
    .news-scroll {max-height:340px; overflow-y:auto; padding-right:8px;}
    .news-item {display:flex; justify-content:space-between; gap:24px; padding:9px 8px; border-bottom:1px solid {{table-border}}; color:{{text-primary}}; font-size:.82rem;}
    .news-item:hover {background:{{hover-bg}};}
    .news-item .t {color:{{text-muted}}; white-space:nowrap; font-size:.72rem;}
</style>
"""


def _build_css() -> str:
    extra = {
        "font": FONT_FAMILY,
        "font-size": FONT_SIZE,
        "shadow": CARD_SHADOW,
        "shadow-hover": CARD_SHADOW_HOVER,
    }

    def sub(m):
        key = m.group(1)
        return extra[key] if key in extra else COLOR_MAP[key]

    return re.sub(r"\{\{([\w-]+)\}\}", sub, _CSS)


def inject_home_styles():
    st.markdown(_build_css(), unsafe_allow_html=True)