# operations/home_dashboard/home_ops/news_ops.py

import html

import pandas as pd
import streamlit as st

# from operations.home_dashboard.home_ops.home_data import get_news as get_static_news

USE_LIVE_NEWS = True   # flip to False to fall back to static data
NEWS_LIMIT = 15


def _fmt_time(raw) -> str:
    """Short display time; falls back to the raw string if it can't be parsed."""
    try:
        dt = pd.to_datetime(raw, errors="coerce")
        return str(raw) if pd.isna(dt) else dt.strftime("%a, %d %b %H:%M")
    except Exception:
        return str(raw)


@st.cache_data(ttl=300, show_spinner=False)   # refresh every 5 minutes
def _load_live_news(limit: int = NEWS_LIMIT):
    # IMPORTANT: lazy import
    from services.news_service import fetch_news

    df = fetch_news("Markets", limit=limit)
    if df is None or df.empty:
        # raising keeps a failed fetch out of the cache, so the next rerun retries
        raise ValueError("No news returned")

    published = df["published"] if "published" in df.columns else [""] * len(df)
    return [
        (str(t), str(l), _fmt_time(p))
        for t, l, p in zip(df["title"], df["link"], published)
    ]


def _get_items():
    if USE_LIVE_NEWS:
        try:
            return _load_live_news()
        except Exception:
            pass
    return []


def handle_news_section():
    rows = []
    for title, link, ts in _get_items():
        t = html.escape(title)
        if link:
            t = (
                f'<a href="{html.escape(link, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer" style="color:inherit;text-decoration:none">{t}</a>'
            )
        rows.append(
            f'<div class="news-item"><div>{t}</div>'
            f'<div class="t">{html.escape(ts)}</div></div>'
        )

    if not rows:
        rows.append(
            '<div class="news-item"><div>News is unavailable right now. '
            'It will retry on the next refresh.</div></div>'
        )

    st.markdown(
        f"""
<div class="card">
  <div class="news-head"><h2>📰&nbsp; Market News</h2><span>Live Feed</span></div>
  <div class="news-scroll">{"".join(rows)}</div>
</div>""",
        unsafe_allow_html=True,
    )