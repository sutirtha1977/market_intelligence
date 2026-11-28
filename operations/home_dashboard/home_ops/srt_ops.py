# operations/home_dashboard/home_ops/srt_ops.py
# Index SRT heatmap: grouped tiles, tinted by distance from the reference level (1.00),
# plus a summary line and leaders / laggards. Reads data["all_index_srt"].

import html
import re
import statistics
from datetime import date
from typing import List, Optional

import streamlit as st

from core.styles import COLOR_MAP
from operations.home_dashboard.home_ops.market_ops import _get_market_data

# ----------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------
SRT_NEUTRAL = 1.00        # reference level: above = green tint, below = red tint
SRT_FULL_SCALE = 0.12     # |SRT - 1.00| at which the tint is strongest
LEADERS_N = 5

# Group membership (exact index names). Anything not listed falls into "Thematic".
_GROUPS = [
    ("Broad market", [
        "Nifty 50", "Nifty Next 50", "Nifty 100", "Nifty 200",
        "Nifty Total Market", "Nifty 500",
    ]),
    ("Market-cap segments", [
        "Nifty Midcap 50", "Nifty Midcap Select", "Nifty Midcap 100",
        "Nifty Smallcap 50", "Nifty Smallcap 100", "Nifty Smallcap 250", "Nifty Smallcap 500",
        "Nifty Microcap 250", "Nifty LargeMidcap 250", "Nifty MidSmallcap 400",
    ]),
    ("Sectoral", [
        "Nifty Auto", "Nifty Bank", "Nifty Cement", "Nifty Chemicals",
        "Nifty Financial Services", "Nifty FMCG", "Nifty IT", "Nifty Media",
        "Nifty Metal", "Nifty Pharma", "Nifty Private Bank", "Nifty PSU Bank",
        "Nifty Realty", "Nifty Consumer Durables", "Nifty Oil and Gas",
        "Nifty500 Healthcare", "Nifty Capital Markets",
    ]),
]
_THEMATIC = "Thematic"
_FULL_NAME_GROUPS = {"Broad market", "Market-cap segments"}   # keep the "Nifty " prefix here


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha:.2f})"


def _clean(rows) -> List[dict]:
    """Keep rows with a usable name + numeric SRT."""
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        try:
            srt = float(r["srt"])
        except (KeyError, TypeError, ValueError):
            continue
        name = str(r.get("index_name") or "").strip()
        if not name:
            continue
        d = r.get("date")
        out.append({"name": name, "srt": srt, "date": d if isinstance(d, date) else None})
    return out


def _group_of(name: str) -> str:
    for group, names in _GROUPS:
        if name in names:
            return group
    return _THEMATIC


def _short(name: str, group: str) -> str:
    return name if group in _FULL_NAME_GROUPS else (re.sub(r"^Nifty\s*", "", name) or name)


def _state(v: float) -> str:
    d = round(v, 2) - SRT_NEUTRAL
    if abs(d) < 1e-9:
        return "flat"
    return "up" if d > 0 else "down"


def _tile_bg(v: float) -> str:
    d = round(v, 2) - SRT_NEUTRAL
    if abs(d) < 1e-9:
        return COLOR_MAP["bg-surface"]
    base = COLOR_MAP["bullish"] if d > 0 else COLOR_MAP["bearish"]
    return _rgba(base, 0.10 + 0.40 * min(abs(d) / SRT_FULL_SCALE, 1.0))


def _tile(row: dict, group: str, stale: bool) -> str:
    full = html.escape(row["name"])
    when = row["date"].strftime("%d %b %Y") if row["date"] else "n/a"
    tip = f'{full} · SRT {row["srt"]:.2f} · {when}' + (" · stale" if stale else "")
    style = "" if stale else f'style="background:{_tile_bg(row["srt"])}"'
    cls = "srt-tile stale" if stale else "srt-tile"
    return (
        f'<div class="{cls}" {style} title="{tip}">'
        f'<span class="n">{html.escape(_short(row["name"], group))}</span>'
        f'<span class="v">{row["srt"]:.2f}</span></div>'
    )


def _chip(label: str, value: str, kind: str = "") -> str:
    return f'<span class="chip {kind}"><span class="k">{label}</span><span class="n">{value}</span></span>'


def _rank_row(label: str, rows: List[dict]) -> str:
    chips = "".join(
        _chip(html.escape(_short(r["name"], _group_of(r["name"]))), f'{r["srt"]:.2f}', _state(r["srt"]))
        for r in rows
    )
    return f'<div class="srt-rank"><span class="rl">{label}</span><div class="chips">{chips}</div></div>'


# ----------------------------------------------------------
# SECTION
# ----------------------------------------------------------
def handle_srt_section():
    data = _get_market_data()
    rows = _clean(data.get("all_index_srt"))

    if not rows:
        st.markdown(
            '<div class="card"><div class="srt-title">Index SRT</div>'
            '<div class="expiry">No SRT data available.</div></div>',
            unsafe_allow_html=True,
        )
        st.write("")
        return

    # Freshness: anything older than the newest date is shown dimmed and left out of the stats
    dates = [r["date"] for r in rows if r["date"]]
    latest = max(dates) if dates else None
    for r in rows:
        r["stale"] = latest is not None and (r["date"] is None or r["date"] < latest)
    fresh = [r for r in rows if not r["stale"]]
    stale = [r for r in rows if r["stale"]]

    # Summary
    vals = [r["srt"] for r in fresh]
    above = sum(1 for v in vals if _state(v) == "up")
    below = sum(1 for v in vals if _state(v) == "down")
    flat = len(vals) - above - below
    median = statistics.median(vals) if vals else None

    summary = (
        _chip("Above 1.00", str(above), "up")
        + _chip("At 1.00", str(flat), "flat")
        + _chip("Below 1.00", str(below), "down")
        + (_chip("Median", f"{median:.2f}") if median is not None else "")
    )
    as_of = f'as of {latest.strftime("%d %b")}' if latest else ""

    ranked = sorted(fresh, key=lambda r: r["srt"], reverse=True)
    leaders = _rank_row("Leaders", ranked[:LEADERS_N])
    laggards = _rank_row("Laggards", list(reversed(ranked[-LEADERS_N:])))

    # Groups, each sorted high -> low (stale tiles sink to the end)
    buckets = {g: [] for g, _ in _GROUPS}
    buckets[_THEMATIC] = []
    for r in rows:
        buckets[_group_of(r["name"])].append(r)

    blocks = []
    for group in [g for g, _ in _GROUPS] + [_THEMATIC]:
        items = sorted(buckets[group], key=lambda r: (r["stale"], -r["srt"]))
        if not items:
            continue
        tiles = "".join(_tile(r, group, r["stale"]) for r in items)
        blocks.append(
            f'<div class="srt-group"><div class="srt-gt">{group}<span class="cnt">{len(items)}</span></div>'
            f'<div class="srt-grid">{tiles}</div></div>'
        )

    note = (
        f'Tiles are tinted by distance from {SRT_NEUTRAL:.2f} (green above, red below). '
        f'Sorted high to low within each group.'
    )
    if stale:
        names = ", ".join(
            f'{html.escape(r["name"])} ({r["date"].strftime("%d %b %Y") if r["date"] else "no date"})'
            for r in stale
        )
        note += f' Excluded from the summary (stale data): {names}.'

    st.markdown(
        '<div class="card">'
        f'<div class="srt-head"><div class="srt-title">Index SRT<span class="sub">{as_of}</span></div>'
        f'<div class="chips">{summary}</div></div>'
        f'{leaders}{laggards}'
        f'<div class="srt-groups">{"".join(blocks)}</div>'
        f'<div class="srt-note">{note}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.write("")