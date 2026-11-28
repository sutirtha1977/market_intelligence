# operations/home_dashboard/home_ops/news_ops.py

import html

import pandas as pd
import streamlit as st

USE_LIVE_NEWS = True          # flip to False to hide the live feed
NEWS_LIMIT = 15
NEWS_SOURCE = "Economic Times"
NEWS_TZ = "Asia/Kolkata"


def _to_local(raw):
    """Parse a feed timestamp into NEWS_TZ. Returns a Timestamp or None."""
    try:
        dt = pd.to_datetime(raw, errors="coerce", utc=True)
    except Exception:
        return None
    if pd.isna(dt):
        return None
    return dt.tz_convert(NEWS_TZ)


@st.cache_data(ttl=300, show_spinner=False)   # refresh every 5 minutes
def _load_live_news(limit: int = NEWS_LIMIT) -> dict:
    # IMPORTANT: lazy import
    from services.news_service import fetch_news

    df = fetch_news("Markets", limit=limit)
    if df is None or df.empty:
        # raising keeps a failed fetch out of the cache, so the next rerun retries
        raise ValueError("No news returned")

    published = df["published"] if "published" in df.columns else [""] * len(df)
    items = [
        {"title": str(t), "link": str(l), "dt": _to_local(p)}
        for t, l, p in zip(df["title"], df["link"], published)
    ]
    return {
        "items": items,
        "fetched_at": pd.Timestamp.now(tz=NEWS_TZ).strftime("%H:%M"),
    }


def _get_news() -> dict:
    if USE_LIVE_NEWS:
        try:
            return _load_live_news()
        except Exception:
            pass
    return {"items": [], "fetched_at": ""}


def _day_label(dt) -> str:
    if dt is None:
        return "Earlier"
    today = pd.Timestamp.now(tz=NEWS_TZ).date()
    d = dt.date()
    if d == today:
        return "Today"
    if (today - d).days == 1:
        return "Yesterday"
    return dt.strftime("%a, %d %b")


def handle_news_section():
    news = _get_news()
    items = news["items"]

    rows = []
    last_day = None
    for it in items:
        dt = it["dt"]
        day = _day_label(dt)
        if day != last_day:
            rows.append(f'<div class="news-day">{html.escape(day)}</div>')
            last_day = day

        title = html.escape(it["title"])
        if it["link"]:
            title = (
                f'<a href="{html.escape(it["link"], quote=True)}" target="_blank" '
                f'rel="noopener noreferrer">{title}</a>'
            )
        tm = dt.strftime("%H:%M") if dt is not None else "–"
        rows.append(f'<div class="news-row"><span class="tm">{tm}</span><span>{title}</span></div>')

    if not rows:
        rows.append(
            '<div class="news-empty">News is unavailable right now. It will retry on the next refresh.</div>'
        )

    updated = f' · Updated {news["fetched_at"]} IST' if news["fetched_at"] else ""
    st.markdown(
        '<div class="card">'
        f'<div class="news-head"><h2>Market News</h2>'
        f'<span class="news-meta">{html.escape(NEWS_SOURCE)}{updated}</span></div>'
        f'<div class="news-scroll">{"".join(rows)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
