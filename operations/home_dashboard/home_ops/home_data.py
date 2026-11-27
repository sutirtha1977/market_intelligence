# operations/home_dashboard/home_ops/home_data.py
# Static data for now - replace each getter with a DB / API call later.

from datetime import date, datetime

import numpy as np

from core.styles import COLOR_MAP

TODAY = date(2026, 11, 27)


def get_next_event():
    return {"name": "Christmas", "date": date(2026, 12, 25)}


def get_vix():
    return {"value": 17.70, "change": -0.38, "regime": "HIGH • OPTION-SELL"}


def get_index_cards():
    return [
        {"name": "NIFTY",      "bias": "BULLISH", "oi": 1.65, "vol": 0.85, "doi": 1.15, "expiry": "Mon, 09 Nov 2026 00:00:00 GMT"},
        {"name": "BANKNIFTY",  "bias": "BULLISH", "oi": 1.24, "vol": 0.69, "doi": 1.15, "expiry": "Mon, 23 Nov 2026 00:00:00 GMT"},
        {"name": "FINNIFTY",   "bias": "NEUTRAL", "oi": 1.04, "vol": 0.81, "doi": 1.00, "expiry": "Mon, 23 Nov 2026 00:00:00 GMT"},
        {"name": "MIDCPNIFTY", "bias": "NEUTRAL", "oi": 1.07, "vol": 0.46, "doi": 0.71, "expiry": "Mon, 23 Nov 2026 00:00:00 GMT"},
        {"name": "NIFTYNXT50", "bias": "BEARISH", "oi": 0.31, "vol": 0.21, "doi": 0.75, "expiry": "Mon, 23 Nov 2026 00:00:00 GMT"},
        {"name": "NIFTYFPI",   "bias": "BEARISH", "oi": 0.48, "vol": 0.87, "doi": 2.33, "expiry": "Mon, 23 Nov 2026 00:00:00 GMT"},
    ]


SERIES_COLORS = {
    "EMA 10": COLOR_MAP["blue-60"],
    "SMA 20": COLOR_MAP["orange-70"],
    "SMA 50": COLOR_MAP["green-70"],
    "SMA 200": COLOR_MAP["red-70"],
}

_SMOOTHNESS = {"EMA 10": 0.0, "SMA 20": 0.5, "SMA 50": 0.8, "SMA 200": 0.92}


def get_breadth(market: str, days: int = 30):
    """Returns {'flag', 'latest': {...}, 'series': {'dates': [...], name: [...]}}"""
    cfg = {
        "IN": {"flag": "🇮🇳", "seed": 7,
               "latest": {"EMA 10": 99.8, "SMA 20": 99.9, "SMA 50": 99.9, "SMA 200": 99.9}},
        "US": {"flag": "🇺🇸", "seed": 21,
               "latest": {"EMA 10": 100.0, "SMA 20": 100.0, "SMA 50": 100.0, "SMA 200": 100.0}},
    }[market]

    rng = np.random.default_rng(cfg["seed"])
    series = {"dates": [
        datetime.fromordinal(TODAY.toordinal() - (days - 1 - i)).strftime("%a, %d %b")
        for i in range(days)
    ]}
    for name, last in cfg["latest"].items():
        s = _SMOOTHNESS[name]
        keep = 0.4 + 0.6 * s
        x, vals = 45.0, []
        for _ in range(days - 1):
            x = float(np.clip(x * keep + (1 - keep) * 50 + rng.normal(0, 14 * (1 - s) + 2), 5, 90))
            vals.append(x)
        vals.append(last)
        series[name] = vals

    return {"flag": cfg["flag"], "latest": cfg["latest"], "series": series}
