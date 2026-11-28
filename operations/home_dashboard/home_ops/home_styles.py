# operations/home_dashboard/home_ops/home_styles.py
# Home screen CSS - all colors / fonts come from core/styles.py

import re

import streamlit as st

from core.styles import (
    COLOR_MAP,
    FONT_FAMILY,
)

# Tokens: {{color-key}} -> COLOR_MAP value, plus {{font}}
# Type scale: 10.5 / 11 / 12 / 13px. Cards are flat (border, no shadow).
_CSS = """
<style>
    .card, .card * {font-family:{{font}}; font-variant-numeric:tabular-nums;}
    .card {
        background:{{bg-card}}; border:1px solid {{card-border}}; border-radius:8px;
        padding:10px 14px; color:{{text-primary}}; font-size:12px; line-height:1.35;
    }

    /* ---------- summary strip: holiday / VIX / USD-INR / Gold ---------- */
    .strip {display:flex; align-items:center; gap:18px; flex-wrap:wrap;}
    .strip .grp {display:flex; align-items:baseline; gap:8px;}
    .strip .grow {margin-left:auto;}
    .strip .sep {width:1px; align-self:stretch; background:{{border-light}};}
    .strip .lbl {font-size:11px; color:{{text-secondary}};}
    .strip .val {font-size:15px; font-weight:700; color:{{text-primary}};}
    .strip .chg {font-size:11px; font-weight:600;}
    .strip .txt {font-size:12px; font-weight:500; color:{{text-primary}};}
    .strip .muted {color:{{text-secondary}};}

    /* equal-width columns (VIX | USD/INR | Gold) */
    .strip.split {display:grid; grid-template-columns:1fr 1fr; gap:0; align-items:stretch;}
    .strip.split.c3 {grid-template-columns:repeat(3,minmax(0,1fr));}
    .strip.split .grp {padding:0 16px; flex-wrap:wrap; row-gap:2px;}
    .strip.split .grp:first-child {padding-left:0;}
    .strip.split .grp + .grp {border-left:1px solid {{border-light}};}

    .tag {font-size:10.5px; font-weight:600; letter-spacing:.02em; color:{{text-secondary}};
          background:{{gray-10}}; border:1px solid {{border-light}}; border-radius:4px; padding:1px 7px;}
    .neg {color:{{bearish}};} .pos {color:{{bullish}};}
    .expiry {color:{{text-secondary}}; font-size:11px;}

    /* ---------- chips (shared) ---------- */
    .chips {display:flex; gap:6px; flex-wrap:wrap;}
    .chip {display:inline-flex; align-items:baseline; gap:5px; font-size:11px;
           border:1px solid {{border-light}}; border-radius:4px; padding:2px 8px; background:{{bg-surface}};}
    .chip .k {color:{{text-secondary}};}
    .chip .n {font-weight:700;}
    .chip.up {border-color:{{green-40}};}   .chip.up .n {color:{{bullish}};}
    .chip.down {border-color:{{red-30}};}   .chip.down .n {color:{{bearish}};}

    /* ---------- index SRT heatmap ---------- */
    .srt-head {display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
               border-bottom:1px solid {{border-light}}; padding-bottom:8px; margin-bottom:8px;}
    .srt-title {font-size:13px; font-weight:700; color:{{text-primary}};}
    .srt-title .sub {font-size:11px; font-weight:400; color:{{text-secondary}}; margin-left:8px;}
    .srt-rank {display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:6px;}
    .srt-rank .rl {font-size:11px; color:{{text-secondary}}; min-width:56px;}
    .srt-groups {display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px 22px; margin-top:12px;}
    .srt-group.wide {grid-column:1 / -1;}
    .srt-gt {font-size:10.5px; font-weight:600; color:{{text-secondary}}; text-transform:uppercase;
             letter-spacing:.06em; margin-bottom:5px;}
    .srt-gt .cnt {font-weight:400; margin-left:6px; color:{{text-muted}};}
    .srt-grid {display:grid; grid-template-columns:repeat(auto-fill,minmax(128px,1fr)); gap:4px;}
    .srt-tile {display:flex; justify-content:space-between; align-items:baseline; gap:6px;
               padding:4px 7px; border-radius:4px; border:1px solid {{border-light}}; font-size:11px; line-height:1.25;}
    .srt-tile .n {overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:{{text-primary}};}
    .srt-tile .v {font-weight:700; color:{{text-primary}};}
    .srt-tile.stale {opacity:.45; border-style:dashed;}
    .srt-note {margin-top:12px; font-size:10.5px; color:{{text-muted}};}
    @media (max-width: 900px) {.srt-groups {grid-template-columns:1fr;}}

    /* ---------- news ---------- */
    .news-head {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid {{border-light}}; padding-bottom:8px; margin-bottom:2px;}
    .news-head h2 {margin:0; padding:0; color:{{text-primary}}; font-size:13px; font-weight:700;}
    .news-meta {font-size:11px; color:{{text-secondary}};}
    .news-scroll {max-height:320px; overflow-y:auto; padding-right:6px;}
    .news-day {position:sticky; top:0; z-index:1; background:{{bg-card}}; padding:8px 4px 4px;
               font-size:10.5px; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
               color:{{text-secondary}}; border-bottom:1px solid {{table-border}};}
    .news-row {display:grid; grid-template-columns:44px 1fr; gap:10px; padding:6px 4px;
               border-bottom:1px solid {{table-border}}; font-size:12px; line-height:1.4;}
    .news-row:last-child {border-bottom:none;}
    .news-row:hover {background:{{hover-bg}};}
    .news-row .tm {color:{{text-muted}}; font-size:11px; padding-top:1px;}
    .news-row a {color:{{text-primary}}; text-decoration:none;}
    .news-row a:hover {color:{{blue-70}}; text-decoration:underline;}
    .news-empty {padding:10px 4px; color:{{text-secondary}}; font-size:12px;}
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