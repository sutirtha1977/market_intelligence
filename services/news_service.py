# operations/services/news_service.py
# Pure data service - no Streamlit imports, so it can be reused by jobs / APIs.

from email.utils import parsedate_to_datetime

import feedparser
import pandas as pd
import requests

FEEDS = {
    "Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
}

_HEADERS = {"User-Agent": "Mozilla/5.0 (MarketAnalytics)"}
_COLUMNS = ["title", "link", "published", "published_dt", "source"]


def _parse_dt(value: str):
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def fetch_news(feed: str = "Markets", limit: int = 10, timeout: int = 8) -> pd.DataFrame:
    """Fetch latest headlines. Always returns a DataFrame (empty on failure)."""
    url = FEEDS[feed]
    try:
        # feedparser has no timeout of its own, so download with requests first
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception:
        return pd.DataFrame(columns=_COLUMNS)

    rows = []
    for e in parsed.entries:
        published = e.get("published", "")
        rows.append({
            "title": e.get("title", "").strip(),
            "link": e.get("link", ""),
            "published": published,
            "published_dt": _parse_dt(published),
            "source": feed,
        })

    df = pd.DataFrame(rows, columns=_COLUMNS)
    if df.empty:
        return df
    return (df.dropna(subset=["title"])
              .drop_duplicates(subset="link")
              .sort_values("published_dt", ascending=False, na_position="last")
              .head(limit)
              .reset_index(drop=True))