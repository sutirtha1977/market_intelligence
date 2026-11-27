# operations/home_dashboard/home_ops/home_styles.py
# Home screen CSS - all colors / fonts come from core/styles.py

import re

import streamlit as st

from core.styles import (
    COLOR_MAP,
    FONT_FAMILY,
)

SERIES_COLORS = {
    "EMA 10": COLOR_MAP["blue-60"],
    "SMA 20": COLOR_MAP["orange-70"],
    "SMA 50": COLOR_MAP["green-70"],
    "SMA 200": COLOR_MAP["red-70"],
}

# Tokens: {{color-key}} -> COLOR_MAP value, plus {{font}}
# Type scale: 10.5 / 11 / 12 / 13px. Cards are flat (border, no shadow).
_CSS = """
<style>
    .card, .card * {font-family:{{font}}; font-variant-numeric:tabular-nums;}
    .card {
        background:{{bg-card}}; border:1px solid {{card-border}}; border-radius:8px;
        padding:10px 14px; color:{{text-primary}}; font-size:12px; line-height:1.35;
    }

    /* ---------- summary strip: VIX + next holiday ---------- */
    .strip {display:flex; align-items:center; gap:18px; flex-wrap:wrap;}
    .strip .grp {display:flex; align-items:baseline; gap:8px;}
    .strip .grow {margin-left:auto;}
    .strip .sep {width:1px; align-self:stretch; background:{{border-light}};}
    .strip .lbl {font-size:11px; color:{{text-secondary}};}
    .strip .val {font-size:15px; font-weight:700; color:{{text-primary}};}
    .strip .chg {font-size:11px; font-weight:600;}
    .strip .txt {font-size:12px; font-weight:500; color:{{text-primary}};}
    .strip .muted {color:{{text-secondary}};}
    .tag {font-size:10.5px; font-weight:600; letter-spacing:.02em; color:{{text-secondary}};
          background:{{gray-10}}; border:1px solid {{border-light}}; border-radius:4px; padding:1px 7px;}
    .neg {color:{{bearish}};} .pos {color:{{bullish}};}
    .expiry {color:{{text-secondary}}; font-size:11px;}

    /* ---------- SMA breadth header: title + inline chips ---------- */
    .bh {display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;}
    .bh-title {font-size:12px; font-weight:600; color:{{text-primary}};}
    .bh-title .sub {font-weight:400; color:{{text-secondary}}; margin-left:6px;}
    .chips {display:flex; gap:6px; flex-wrap:wrap;}
    .chip {display:inline-flex; align-items:baseline; gap:5px; font-size:11px;
           border:1px solid {{border-light}}; border-radius:4px; padding:2px 8px; background:{{bg-surface}};}
    .chip .k {color:{{text-secondary}};}
    .chip .n {font-weight:700;}
    .chip.up {border-color:{{green-40}};}   .chip.up .n {color:{{bullish}};}
    .chip.down {border-color:{{red-30}};}   .chip.down .n {color:{{bearish}};}

    /* ---------- news ---------- */
    .news-head {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid {{border-light}}; padding-bottom:8px; margin-bottom:2px;}
    .news-head h2 {margin:0; padding:0; color:{{text-primary}}; font-size:13px; font-weight:700;}
    .news-head span {font-size:11px; color:{{text-secondary}};}
    .news-scroll {max-height:300px; overflow-y:auto; padding-right:6px;}
    .news-item {display:flex; justify-content:space-between; gap:20px; padding:6px 4px; border-bottom:1px solid {{table-border}}; color:{{text-primary}}; font-size:12px;}
    .news-item:last-child {border-bottom:none;}
    .news-item:hover {background:{{hover-bg}};}
    .news-item .t {color:{{text-muted}}; white-space:nowrap; font-size:11px;}
</style>
"""


def _build_css() -> str:
    extra = {"font": FONT_FAMILY}

    def sub(m):
        key = m.group(1)
        return extra[key] if key in extra else COLOR_MAP[key]

    return re.sub(r"\{\{([\w-]+)\}\}", sub, _CSS)


def inject_home_styles():
    st.markdown(_build_css(), unsafe_allow_html=True)