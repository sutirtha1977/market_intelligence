# services/news_service.py
import feedparser
import pandas as pd

RSS_URL = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

def get_news(limit=10):
    feed = feedparser.parse(RSS_URL)

    news = []
    for entry in feed.entries[:limit]:
        news.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "")
        })

    df = pd.DataFrame(news)
    return df