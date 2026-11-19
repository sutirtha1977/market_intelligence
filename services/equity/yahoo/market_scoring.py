from typing import Dict, Any, List
from config.logger import log


# =========================================================
# PRICE HELPER
# =========================================================
def get_price(row: Dict[str, Any]):
    return row.get("adj_close") if row.get("adj_close") is not None else row.get("close")


# =========================================================
# RSI SCORING
# =========================================================
def get_rsi_score(rsi_3, rsi_9, ema_rsi_9_3, wma_rsi_9_21):

    if None in (rsi_3, rsi_9, ema_rsi_9_3, wma_rsi_9_21):
        return 0, "NO DATA"

    bull_stack = rsi_3 > rsi_9 > ema_rsi_9_3 > wma_rsi_9_21
    bear_stack = rsi_3 < rsi_9 < ema_rsi_9_3 < wma_rsi_9_21

    wma = wma_rsi_9_21

    # ---------------- BULLISH ----------------
    if bull_stack:
        if wma > 80:
            return -2, "OVERBOUGHT REVERSAL"
        elif 50 < wma <= 80:
            return 3, "STRONG BULL"
        elif 30 < wma <= 50:
            return 2, "BULL"
        else:
            return 1, "WEAK BULL"

    # ---------------- BEARISH ----------------
    if bear_stack:
        if wma > 80:
            return -3, "STRONG BEAR"
        elif 50 < wma <= 80:
            return -2, "BEAR"
        elif 30 < wma <= 50:
            return -1, "WEAK BEAR"
        else:
            return 1, "REVERSAL BULLISH"

    return 0, "SIDEWAYS"


# =========================================================
# SMA SCORING
# =========================================================
def get_sma_score(price, sma20, sma50, sma200):

    if price is None:
        return 0

    score = 0

    if sma20 is not None:
        score += 1 if price > sma20 else -1

    if sma50 is not None:
        score += 1 if price > sma50 else -1

    if sma200 is not None:
        score += 1 if price > sma200 else -1

    return score


# =========================================================
# TOTAL SCORE
# =========================================================
def get_total_score(sma_score, rsi_score):
    return sma_score + rsi_score


# =========================================================
# RECOMMENDATION ENGINE (FINAL CLEAN OUTPUT)
# =========================================================
def get_recommendation(total_score: int, rsi_state: str) -> str:

    # --- risk first ---
    if "OVERBOUGHT REVERSAL" in rsi_state:
        return "TAKE PROFIT"

    if "REVERSAL" in rsi_state:
        return "WATCH REVERSAL"

    # --- trend logic ---
    if total_score >= 4:
        return "STRONG BUY"

    if 2 <= total_score < 4:
        return "BUY"

    if total_score <= -4:
        return "STRONG SELL"

    if -4 < total_score <= -2:
        return "SELL"

    return "HOLD"


# =========================================================
# SYMBOL SCORING
# =========================================================
def build_symbol_score(row: Dict[str, Any]):

    price = get_price(row)

    sma_score = get_sma_score(
        price,
        row.get("sma_20"),
        row.get("sma_50"),
        row.get("sma_200")
    )

    rsi_score, rsi_state = get_rsi_score(
        row.get("rsi_3"),
        row.get("rsi_9"),
        row.get("ema_rsi_9_3"),
        row.get("wma_rsi_9_21")
    )

    total_score = get_total_score(sma_score, rsi_score)

    return {
        "symbol_id": row.get("symbol_id"),
        "name": row.get("name"),
        "symbol": row.get("symbol"),
        "timeframe": row.get("timeframe"),

        "close": price,

        "sma_score": sma_score,
        "rsi_score": rsi_score,
        "rsi_state": rsi_state,

        "total_score": total_score,
        "recommendation": get_recommendation(total_score, rsi_state)
    }


# =========================================================
# BATCH SCORING
# =========================================================
def score_snapshot(data: List[Dict]):

    log(f"📊 SNAPSHOT INPUT ({len(data)}) rows")

    return [build_symbol_score(row) for row in data]