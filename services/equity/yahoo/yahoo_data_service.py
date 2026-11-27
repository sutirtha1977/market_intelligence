# services/equity/yahoo/yahoo_data_service.py

from typing import Dict, Optional, List, Union
from config.logger import log
from datetime import datetime, timedelta, date
from database.connection import get_db_connection_cm, get_engine
from config.db_config import ASSET_TABLE_CONFIG
import pandas as pd
from pprint import pprint

# --------------------------------------------------------------------------
def get_latest_date(cur, price_table: str, timeframe: str):
    try:
        cur.execute(
            f"""
            SELECT MAX(date)
            FROM {price_table}
            WHERE timeframe = %s
            """,
            (timeframe,)
        )
        return cur.fetchone()[0]
    except Exception as e:
        log(f"❌ Error in get_latest_date for {price_table}, {timeframe}: {e}")
        return None
# --------------------------------------------------------------------------
def fetch_next_nse_holiday(cur) -> Optional[Dict]:
    try:
        holidays_table = ASSET_TABLE_CONFIG["reference"]["nse_holidays"]
        cur.execute(
            f"""
            SELECT holiday_date, day_name, holiday_name
            FROM {holidays_table}
            WHERE holiday_date >= CURRENT_DATE
            ORDER BY holiday_date
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row:
            holiday_date, day_name, holiday_name = row
            return {
                "date": holiday_date.strftime("%d %b %Y"),
                "day": day_name,
                "name": holiday_name,
            }
        return None
    except Exception as e:
        log(f"❌ Error in fetch_next_nse_holiday: {e}")
        return None
# --------------------------------------------------------------------------
def fetch_sma_breadth_ratio_range(
    cur,
    price_table: str,
    indicator_table: str,
    symbol_table: str,
    latest_date
) -> dict:
    try:
        current_year = datetime.now().year
        start_date = f"{current_year}-01-01"
        query = f"""
            SELECT
                p.date,
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(p.adj_close, 0), p.close) > i.ema_10
                ) AS ema10,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(p.adj_close, 0), p.close) > i.sma_20
                ) AS sma20,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(p.adj_close, 0), p.close) > i.sma_50
                ) AS sma50,
                COUNT(*) FILTER (
                    WHERE COALESCE(NULLIF(p.adj_close, 0), p.close) > i.sma_200
                ) AS sma200
            FROM {price_table} p
            JOIN {indicator_table} i
                ON p.symbol_id = i.symbol_id
                AND p.timeframe = i.timeframe
                AND p.date = i.date
            JOIN {symbol_table} s
                ON s.symbol_id = p.symbol_id
            WHERE
                p.timeframe = '1d'
                AND s.is_active = TRUE
                AND p.date BETWEEN %s AND %s
            GROUP BY p.date
            ORDER BY p.date DESC
        """
        cur.execute(query, (start_date, latest_date))
        rows = cur.fetchall()
        if not rows:
            return {}
        data = []
        for r in rows:
            total = r[1]
            if not total:
                continue
            data.append({
                "date": r[0],
                "ema10": round(r[2] / total * 100, 2),
                "sma20": round(r[3] / total * 100, 2),
                "sma50": round(r[4] / total * 100, 2),
                "sma200": round(r[5] / total * 100, 2),
            })
        return {"breadth": data}
    except Exception:
        return {}
# --------------------------------------------------------------------------
def fetch_gap_stocks(
    cur,
    price_table: str,
    symbol_table: str,
    latest_date,
    timeframe: str
) -> Dict:
    try:
        query = f"""
            SELECT
                s.symbol_id,
                s.symbol,
                p.open AS today_open,
                p.high AS today_high,
                p.low AS today_low,
                prev.adj_close AS prev_close,
                prev.high AS prev_high,
                prev.low AS prev_low,
                ROUND((((p.open - prev.adj_close) / prev.adj_close) * 100)::numeric, 2) AS gap_pct,
                p.adj_close AS today_adj_close
            FROM {price_table} p
            JOIN {price_table} prev
                ON prev.symbol_id = p.symbol_id
                AND prev.timeframe = p.timeframe
                AND prev.date = (
                    SELECT MAX(date)
                    FROM {price_table}
                    WHERE symbol_id = p.symbol_id
                      AND date < p.date
                      AND timeframe = %s
                )
            JOIN {symbol_table} s
                ON s.symbol_id = p.symbol_id
            WHERE p.timeframe = %s
              AND p.date = %s
              AND p.adj_close >= 100
              AND s.is_active = TRUE
        """
        cur.execute(query, (timeframe, timeframe, latest_date))
        rows = cur.fetchall()
        gap_up, gap_down = [], []
        for symbol_id, symbol, today_open, today_high, today_low, prev_close, prev_high, prev_low, gap_pct, today_adj_close in rows:
            if today_low > prev_high:
                gap_up.append({"symbol_id": symbol_id, "Symbol": symbol, "Gap %": float(gap_pct)})
            elif today_high < prev_low:
                gap_down.append({"symbol_id": symbol_id, "Symbol": symbol, "Gap %": float(gap_pct)})
        gap_up = sorted(gap_up, key=lambda x: x["Gap %"], reverse=True)[:10]
        gap_down = sorted(gap_down, key=lambda x: x["Gap %"])[:10]
        return {"gap_up": gap_up, "gap_down": gap_down}
    except Exception as e:
        log(f"❌ Error in fetch_gap_stocks for {price_table}: {e}")
        return {"gap_up": [], "gap_down": []}
# --------------------------------------------------------------------------
def fetch_rsi_crossovers(
    cur,
    price_table: str,
    indicator_table: str,
    symbol_table: str,
    latest_date,
    timeframe: str,
    wma_min: float = 30,
    wma_max: float = 50
) -> Dict:
    try:
        query = f"""
            SELECT
                s.symbol_id,
                s.symbol,
                ind.rsi_9,
                ind.wma_rsi_9_21,
                p.adj_close
            FROM {indicator_table} ind
            JOIN {indicator_table} prev
                ON prev.symbol_id = ind.symbol_id
                AND prev.timeframe = ind.timeframe
                AND prev.date = (
                    SELECT MAX(date)
                    FROM {indicator_table}
                    WHERE symbol_id = ind.symbol_id
                      AND date < ind.date
                      AND timeframe = %s
                )
            JOIN {price_table} p
                ON p.symbol_id = ind.symbol_id
                AND p.timeframe = ind.timeframe
                AND p.date = ind.date
            JOIN {symbol_table} s
                ON s.symbol_id = ind.symbol_id
            WHERE ind.timeframe = %s
              AND ind.date = %s
              AND s.is_active = TRUE
              AND p.adj_close >= 100
              AND ind.wma_rsi_9_21 > %s
              AND ind.wma_rsi_9_21 < %s
              AND prev.rsi_9 <= prev.wma_rsi_9_21
              AND ind.rsi_9 > ind.wma_rsi_9_21
        """
        cur.execute(query, (timeframe, timeframe, latest_date, wma_min, wma_max))
        rows = cur.fetchall()
        signals = []
        for symbol_id, symbol, rsi_9, wma_rsi_9_21, adj_close in rows:
            signals.append({
                "symbol_id": symbol_id,
                "Symbol": symbol,
                "RSI_9": float(rsi_9),
                "WMA_RSI_9_21": float(wma_rsi_9_21),
                "Adj_Close": float(adj_close)
            })
        signals = sorted(signals, key=lambda x: x["RSI_9"], reverse=True)
        return {"rsi_crossovers": signals}
    except Exception as e:
        log(f"❌ Error in fetch_rsi_crossovers for {indicator_table}: {e}")
        return {"rsi_crossovers": []}
# --------------------------------------------------------------------------
def get_yahoo_equity_data(
    asset_key: str = "yahoo_india_equity",
    timeframe: str = "1d"
) -> Dict:
    tables = ASSET_TABLE_CONFIG[asset_key]
    symbol_table = tables["symbol"]
    price_table = tables["price"]
    dashboard: Dict = {}
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                latest = get_latest_date(cur, price_table, timeframe)
                dashboard["gap"] = fetch_gap_stocks(
                    cur,
                    price_table,
                    symbol_table,
                    latest,
                    timeframe
                )
                log(f"✅ Dashboard data fetched for {asset_key}")
                return dashboard
    except Exception as e:
        log(f"❌ Error fetching dashboard data for {asset_key}: {e}")
        return {}
# --------------------------------------------------------------------------
def get_equity_dashboard_data(
    asset_key: str = "yahoo_india_equity",
    timeframe: str = "1d"
) -> Dict:
    tables = ASSET_TABLE_CONFIG[asset_key]
    symbol_table = tables["symbol"]
    price_table = tables["price"]
    indicator_table = tables["indicator"]
    dashboard: Dict = {}
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                latest = get_latest_date(cur, price_table, timeframe)
                dashboard["gap"] = fetch_gap_stocks(
                    cur,
                    price_table,
                    symbol_table,
                    latest,
                    timeframe
                )
                dashboard["rsi_crossovers_30_50"] = fetch_rsi_crossovers(
                    cur,
                    price_table,
                    indicator_table,
                    symbol_table,
                    latest,
                    timeframe,
                    wma_min=30,
                    wma_max=50
                ).get("rsi_crossovers", [])
                dashboard["rsi_crossovers_50_80"] = fetch_rsi_crossovers(
                    cur,
                    price_table,
                    indicator_table,
                    symbol_table,
                    latest,
                    timeframe,
                    wma_min=50,
                    wma_max=80
                ).get("rsi_crossovers", [])
                log(f"✅ Dashboard data fetched for {asset_key}")
                return dashboard
    except Exception as e:
        log(f"❌ Error fetching dashboard data for {asset_key}: {e}")
        return {}
# --------------------------------------------------------------------------
def get_market_data() -> Dict:
    from services.index.vix_service import get_vix_last_n_days_new

    dashboard: Dict = {}
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                tables_india = ASSET_TABLE_CONFIG["yahoo_india_equity"]
                india_symbol = tables_india["symbol"]
                india_price = tables_india["price"]
                india_indicator = tables_india["indicator"]
                india_latest = get_latest_date(cur, india_price, "1d")
                india_data = fetch_sma_breadth_ratio_range(
                    cur,
                    india_price,
                    india_indicator,
                    india_symbol,
                    india_latest
                )
                dashboard["india_sma_breadth"] = india_data
                tables_usa = ASSET_TABLE_CONFIG["yahoo_usa_equity"]
                usa_symbol = tables_usa["symbol"]
                usa_price = tables_usa["price"]
                usa_indicator = tables_usa["indicator"]
                usa_latest = get_latest_date(cur, usa_price, "1d")
                usa_data = fetch_sma_breadth_ratio_range(
                    cur,
                    usa_price,
                    usa_indicator,
                    usa_symbol,
                    usa_latest
                )
                dashboard["usa_sma_breadth"] = usa_data
                dashboard["vix_data"] = get_vix_last_n_days_new(cur, 1)
                dashboard["next_holiday"] = fetch_next_nse_holiday(cur)
                # print("\n========== MARKET DASHBOARD DATA ==========")
                # pprint(dashboard, sort_dicts=False, width=120)
                # print("============================================\n")
                return dashboard
    except Exception as e:
        log(f"❌ Error fetching market data: {e}")
        return {}
# --------------------------------------------------------------------------
def fetch_asset_data(
    symbol_id: int,
    asset_key: str,
    days: int = 90,
    timeframe: str = "1d"
) -> pd.DataFrame:
    try:
        tables = ASSET_TABLE_CONFIG[asset_key]
        symbol_table = tables["symbol"]
        price_table = tables["price"]
        indicator_table = tables["indicator"]
        engine = get_engine()
        query = f"""
            SELECT *
            FROM (
                SELECT 
                    p.date, p.open, p.high, p.low,
                    COALESCE(NULLIF(p.adj_close, 0), p.close) AS close,
                    i.ema_rsi_9_3, 
                    i.wma_rsi_9_21, 
                    i.rsi_9,
                    i.rsi_3,
                    i.ema_9,
                    i.bb_upper, i.bb_middle, i.bb_lower,
                    i.rs, i.rs_ma
                FROM {price_table} p
                LEFT JOIN {indicator_table} i
                    ON p.symbol_id = i.symbol_id
                    AND p.timeframe = i.timeframe
                    AND p.date = i.date
                WHERE p.symbol_id = %(symbol_id)s
                  AND p.timeframe = %(timeframe)s
                ORDER BY p.date DESC
                LIMIT %(days)s
            ) sub
            ORDER BY date ASC
        """
        df = pd.read_sql(
            query,
            engine,
            params={"symbol_id": int(symbol_id), "timeframe": timeframe, "days": days}
        )
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        log(f"❌ Error fetching stock data for symbol_id {symbol_id}, asset_key {asset_key}: {e}")
        return pd.DataFrame()
# --------------------------------------------------------------------------
def fetch_asset_data_all(
    symbol_id: int,
    asset_key: str,
    timeframe: str = "1d"
) -> pd.DataFrame:
    try:
        tables = ASSET_TABLE_CONFIG[asset_key]
        symbol_table = tables["symbol"]
        price_table = tables["price"]
        indicator_table = tables["indicator"]

        engine = get_engine()

        query = f"""
            SELECT *
            FROM (
                SELECT 
                    p.date, p.open, p.high, p.low,
                    COALESCE(NULLIF(p.adj_close, 0), p.close) AS close,
                    i.ema_9,
                    i.sma_50,
                    i.sma_100,
                    i.sma_200,
                    i.rsi_3,
                    i.rsi_9,
                    i.rsi_14,
                    i.ema_rsi_9_3, 
                    i.wma_rsi_9_21, 
                    i.bb_upper, 
                    i.bb_middle, 
                    i.bb_lower,
                    i.rs, 
                    i.rs_ma,
                    i.rs_slope,
                    i.rs_ma_rising,
                    i.rs_ma_falling
                FROM {price_table} p
                LEFT JOIN {indicator_table} i
                    ON p.symbol_id = i.symbol_id
                    AND p.timeframe = i.timeframe
                    AND p.date = i.date
                WHERE p.symbol_id = %(symbol_id)s
                  AND p.timeframe = %(timeframe)s
                ORDER BY p.date DESC
            ) sub
            ORDER BY date ASC
        """

        df = pd.read_sql(
            query,
            engine,
            params={
                "symbol_id": int(symbol_id),
                "timeframe": timeframe
            }
        )

        df["date"] = pd.to_datetime(df["date"])

        return df

    except Exception as e:
        log(f"❌ Error fetching stock data for symbol_id {symbol_id}, asset_key {asset_key}: {e}")
        return pd.DataFrame()
# --------------------------------------------------------------------------
def fetch_asset_data_from_signal_date(
    symbol_id: int,
    asset_key: str,
    start_date: Union[str, datetime, date, pd.Timestamp],
    days: int = 90,
    timeframe: str = "1d"
) -> pd.DataFrame:
    try:
        if symbol_id is None or asset_key is None or start_date is None:
            log("❌ Missing symbol_id / asset_key / start_date")
            return pd.DataFrame()
        symbol_id = int(symbol_id)
        asset_key = str(asset_key)
        tables = ASSET_TABLE_CONFIG.get(asset_key)
        if not tables:
            log(f"❌ Invalid asset_key: {asset_key}")
            return pd.DataFrame()
        price_table = tables["price"]
        indicator_table = tables["indicator"]
        engine = get_engine()
        start_date = pd.to_datetime(start_date)
        end_date = start_date + timedelta(days=int(days))

        query = f"""
            SELECT 
                p.date,
                p.open,
                p.high,
                p.low,
                COALESCE(NULLIF(p.adj_close, 0), p.close) AS close,
                i.ema_9,
                i.ema_rsi_9_3,
                i.wma_rsi_9_21,
                i.rsi_3,
                i.rsi_9,
                i.bb_upper,
                i.bb_middle,
                i.bb_lower,
                i.rs, 
                i.rs_ma
            FROM {price_table} p
            LEFT JOIN {indicator_table} i
                ON p.symbol_id = i.symbol_id
                AND p.timeframe = i.timeframe
                AND p.date = i.date
            WHERE p.symbol_id = %(symbol_id)s
              AND p.timeframe = %(timeframe)s
              AND p.date BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY p.date ASC
        """
        df = pd.read_sql(
            query,
            engine,
            params={
                "symbol_id": symbol_id,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        log(f"❌ Error fetching window stock data for symbol_id {symbol_id}, asset_key {asset_key}: {e}")
        return pd.DataFrame()
# --------------------------------------------------------------------------
def fetch_asset_data_by_year(
    symbol_id: int,
    asset_key: str,
    year: int,
    timeframe: str = "1d"
) -> pd.DataFrame:
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        tables = ASSET_TABLE_CONFIG[asset_key]
        price_table = tables["price"]
        indicator_table = tables["indicator"]
        engine = get_engine()
        query = f"""
            SELECT 
                p.date,
                p.open,
                p.high,
                p.low,
                COALESCE(NULLIF(p.adj_close, 0), p.close) AS close,
                p.volume,
                i.rsi_3,
                i.rsi_9,
                i.ema_rsi_9_3,
                i.wma_rsi_9_21,
                i.bb_upper,
                i.bb_middle,
                i.bb_lower
            FROM {price_table} p
            LEFT JOIN {indicator_table} i
                ON p.symbol_id = i.symbol_id
                AND p.timeframe = i.timeframe
                AND p.date = i.date
            WHERE p.symbol_id = %(symbol_id)s
              AND p.timeframe = %(timeframe)s
              AND p.date BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY p.date ASC
        """
        df = pd.read_sql(
            query,
            engine,
            params={
                "symbol_id": int(symbol_id),
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        indicator_cols = [
            "rsi_9", "ema_rsi_9_3", "wma_rsi_9_21",
            "bb_upper", "bb_middle", "bb_lower",
            "rs", "rs_ma"
        ]
        existing_cols = [c for c in indicator_cols if c in df.columns]
        df[existing_cols] = df[existing_cols].ffill()
        return df
    except Exception as e:
        log(f"❌ Error fetching stock data for symbol_id {symbol_id}: {e}")
        return pd.DataFrame()
# --------------------------------------------------------------------------
def get_yahoo_data_snapshot(asset_key: str) -> List[Dict]:
    try:
        tables = ASSET_TABLE_CONFIG[asset_key]
        symbol_table = tables["symbol"]
        price_table = tables["price"]
        indicator_table = tables["indicator"]

        query = f"""
            SELECT DISTINCT ON (s.symbol_id, p.timeframe)
                s.symbol_id,
                s.name,
                s.symbol,
                p.date,
                p.timeframe,

                p.open,
                p.high,
                p.low,
                p.close,
                p.adj_close,
                p.volume,

                i.ema_3,
                i.ema_5,
                i.ema_7,
                i.ema_9,
                i.ema_10,

                i.sma_20,
                i.sma_50,
                i.sma_100,
                i.sma_200,

                i.sma_10_vol,
                i.sma_20_vol,

                i.rsi_3,
                i.rsi_9,
                i.rsi_14,
                i.ema_rsi_9_3,
                i.ema_rsi_9_5,
                i.wma_rsi_9_21,

                i.macd,
                i.macd_signal,

                i.bb_upper,
                i.bb_middle,
                i.bb_lower,

                i.rs,
                i.rs_ma,
                i.rs_slope,
                i.rs_ma_rising,
                i.rs_ma_falling

            FROM {symbol_table} s
            JOIN {price_table} p
                ON s.symbol_id = p.symbol_id
            LEFT JOIN {indicator_table} i
                ON p.symbol_id = i.symbol_id
                AND p.date = i.date
                AND p.timeframe = i.timeframe
            WHERE s.is_active = TRUE
              AND p.timeframe IN ('1d','1wk','1mo')
            ORDER BY s.symbol_id, p.timeframe, p.date DESC
        """

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                if not rows:
                    return []

                columns = [desc[0] for desc in cur.description]

                return [dict(zip(columns, r)) for r in rows]

    except Exception as e:
        log(f"❌ Error in get_yahoo_data_snapshot({asset_key}): {e}")
        return []
# --------------------------------------------------------------------------
