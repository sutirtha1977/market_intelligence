import os
import requests
import traceback
import pandas as pd
from datetime import date, timedelta
import json
import re
from typing import Callable, Optional
from tqdm import tqdm

from config.constants import (
    NIFTY_INDEX_URLS,
    NSE_IDX_API_URL,
    NSE_DAILY_URL,
    NSE_IDX_HEADERS,
    NSE_IDX_CONS_HEADERS,
)
from config.db_config import ASSET_TABLE_CONFIG
from config.paths import NSE_DIR
from config.logger import log
from services.equity.cleanup_service import delete_files_in_folder
from database.connection import get_db_connection_cm, get_db_connection, get_engine

# --------------------------------------------------------------------------
TIMEFRAME = "1d"
FALLBACK_START_DATE = date(2018, 1, 1)
START_DATE = "01-Jan-2000"
END_DATE = "31-Dec-2017"
SMA_PERIOD = 124
# --------------------------------------------------------------------------
def upsert_nifty_index_constituents():
    log("Starting NSE Index Constituents Update")
    os.makedirs(NSE_DIR, exist_ok=True)
    delete_files_in_folder(str(NSE_DIR))
    try:
        tables = ASSET_TABLE_CONFIG["nse_india_index"]
        symbols_table = tables["symbol"]
        constituents_table = tables["constituents"]

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                for index_name, url in NIFTY_INDEX_URLS.items():
                    log(f"Processing index: {index_name}")

                    cur.execute(
                        f"""
                        SELECT symbol_id
                        FROM {symbols_table}
                        WHERE name = %s
                        AND UPPER(symbol) != 'INDIA VIX'
                        """,
                        (index_name,),
                    )
                    row = cur.fetchone()
                    if not row:
                        log(f"Index not found in DB: {index_name}")
                        continue

                    index_id = int(row[0])
                    log(f"{index_name} index_id: {index_id}")

                    response = requests.get(url, headers=NSE_IDX_CONS_HEADERS, timeout=15)
                    if response.status_code != 200:
                        log(f"HTTP {response.status_code} for {index_name}")
                        continue

                    csv_text = response.content.decode("utf-8", errors="ignore")
                    if "Symbol" not in csv_text:
                        log(f"Invalid CSV received for {index_name}")
                        continue

                    csv_path = os.path.join(NSE_DIR, f"{index_name.replace(' ', '_').lower()}.csv")
                    with open(csv_path, "w", encoding="utf-8") as f:
                        f.write(csv_text)

                    df = pd.read_csv(csv_path)
                    if "Symbol" not in df.columns:
                        log(f"CSV structure invalid for {index_name}")
                        continue

                    csv_symbols = df["Symbol"].dropna().astype(str).str.strip().unique()
                    inserted = 0
                    skipped_symbols = []

                    for symbol in csv_symbols:
                        cur.execute("SELECT symbol_id FROM yahoo_india_equity_symbols WHERE symbol = %s", (symbol,))
                        stock_row = cur.fetchone()
                        if not stock_row:
                            skipped_symbols.append(symbol)
                            continue

                        cur.execute(
                            f"""
                            INSERT INTO {constituents_table} (index_id, symbol_id)
                            VALUES (%s, %s)
                            ON CONFLICT (index_id, symbol_id) DO NOTHING
                            """,
                            (index_id, stock_row[0]),
                        )
                        if cur.rowcount > 0:
                            inserted += 1

                    log(f"{index_name}: inserted={inserted}, skipped={len(skipped_symbols)}")
                    if skipped_symbols:
                        log(f"Skipped symbols ({len(skipped_symbols)}): {', '.join(sorted(skipped_symbols))}")

        delete_files_in_folder(str(NSE_DIR))
        log("✅ NSE Index Constituents Update Completed")
    except Exception as e:
        log(f"❌ Fatal error in NSE Index Constituents: {e}")
        raise
# --------------------------------------------------------------------------
def upsert_nse_index_history():
    log("Starting NSE historical index upsert")
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT symbol_id, symbol FROM nse_india_index_symbols WHERE is_active = TRUE")
                symbol_map = {r[1]: r[0] for r in cur.fetchall()}
                session = requests.Session()
                for i, (symbol, symbol_id) in enumerate(symbol_map.items(), 1):
                    try:
                        payload = {
                            "cinfo": str(
                                {"name": symbol, "startDate": START_DATE, "endDate": END_DATE, "indexName": symbol}
                            ).replace('"', "'")
                        }
                        r = session.post(NSE_IDX_API_URL, headers=NSE_IDX_HEADERS, json=payload, timeout=30)
                        r.raise_for_status()
                        outer = r.json()
                        raw = outer.get("d", "")

                        if not raw:
                            log(f"No data returned for {symbol}, skipping")
                            continue
                        raw_fixed = re.sub(r"}\s*{", "},{", raw.replace("\t", ","))
                        records = json.loads(raw_fixed)
                        df = pd.DataFrame(records)
                        if "HistoricalDate" not in df.columns:
                            log(f"{symbol} missing HistoricalDate column, skipping")
                            continue
                        df.rename(columns={
                            "HistoricalDate": "date",
                            "OPEN": "open",
                            "HIGH": "high",
                            "LOW": "low",
                            "CLOSE": "close",
                        }, inplace=True)
                        df["date"] = pd.to_datetime(df["date"], format="%d %b %Y", errors="coerce").dt.date
                        df = df[(df["date"].notna()) & (df["date"] <= pd.to_datetime(END_DATE).date())]
                        if df.empty:
                            log(f"No valid data after filtering for {symbol}, skipping")
                            continue
                        for c in ["open", "high", "low", "close"]:
                            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
                        df["volume"] = 0
                        df = df.sort_values("date")
                        df["pct_price_change"] = df["close"].pct_change().replace([float("inf"), float("-inf")], 0.0)\
                            .fillna(0.0).mul(100).round(2).astype("float32")
                        for _, row in df.iterrows():
                            cur.execute(
                                """
                                INSERT INTO nse_india_index_price (
                                    symbol_id, timeframe, date, open, high, low, close, volume, pct_price_change
                                )
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                ON CONFLICT (symbol_id, timeframe, date) DO UPDATE
                                SET open = EXCLUDED.open,
                                    high = EXCLUDED.high,
                                    low = EXCLUDED.low,
                                    close = EXCLUDED.close,
                                    volume = EXCLUDED.volume,
                                    pct_price_change = EXCLUDED.pct_price_change
                                """,
                                (
                                    symbol_id, TIMEFRAME, row["date"], row["open"], row["high"],
                                    row["low"], row["close"], row["volume"], row["pct_price_change"]
                                )
                            )
                    except Exception as e:
                        log(f"❌ Failed {symbol}: {type(e).__name__} - {e}")
                        log(traceback.format_exc())
    except Exception as e:
        log(f"❌ General error in NSE index history upsert: {e}")
    log("✅ NSE historical index upsert completed (check error logs for issues)")
# --------------------------------------------------------------------------
def upsert_nse_index_incremental():
    log("Starting NSE Index Price Data Update")
    os.makedirs(NSE_DIR, exist_ok=True)
    delete_files_in_folder(str(NSE_DIR))
    session = requests.Session()
    downloaded_files = 0
    latest_date = None
    tables = ASSET_TABLE_CONFIG["nse_india_index"]
    symbols_table = tables["symbol"]
    price_table = tables["price"]

    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT MAX(date) FROM {price_table} WHERE timeframe = %s",
                    (TIMEFRAME,)
                )
                row = cur.fetchone()
                latest_date = row[0] if row and row[0] else None
    except Exception as e:
        log(f"Failed to get latest date: {e}")
    current_date = latest_date + timedelta(days=1) if latest_date else FALLBACK_START_DATE
    end_date = date.today()
    if latest_date and latest_date >= end_date:
        log(f"NSE Index data already up-to-date | Latest date in DB: {latest_date}")
        return
    log(f"NSE Index sync window | From {current_date} → To {end_date}")
    while current_date <= end_date:
        date_str = current_date.strftime("%d%m%Y")
        url = NSE_DAILY_URL.format(date=date_str)
        try:
            response = session.get(url, headers=NSE_IDX_CONS_HEADERS, timeout=30)
            if response.status_code != 200:
                log(f"HTTP {response.status_code} | {url}")
                current_date += timedelta(days=1)
                continue
            csv_text = response.content.decode("utf-8", errors="ignore")
            if "Index Name" not in csv_text:
                log(f"No index data for {date_str} (likely holiday)")
                current_date += timedelta(days=1)
                continue
            file_path = os.path.join(NSE_DIR, f"nifty_index_{date_str}.csv")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_text)
            downloaded_files += 1
        except Exception as e:
            log(f"Request failed | {url} | {e}")
        current_date += timedelta(days=1)
    if downloaded_files == 0:
        log("No new NSE index files downloaded")
        return
    csv_files = sorted(f for f in os.listdir(NSE_DIR) if f.endswith(".csv"))
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT symbol_id, name FROM {symbols_table}")
                symbol_map = {name.strip().upper(): symbol_id for symbol_id, name in cur.fetchall()}
                total_inserted = 0
                all_skipped = set()
                for file_name in csv_files:
                    file_path = os.path.join(NSE_DIR, file_name)
                    df = pd.read_csv(file_path)
                    df.columns = df.columns.str.strip()
                    df["Index Date"] = pd.to_datetime(df["Index Date"], dayfirst=True, errors="coerce").dt.date
                    df = df[df["Index Date"].notna()]
                    if df.empty:
                        continue
                    df["Index Name"] = df["Index Name"].astype(str).str.strip().str.upper()
                    numeric_cols = [
                        "Open Index Value", "High Index Value", "Low Index Value",
                        "Closing Index Value", "Change(%)", "Volume",
                    ]
                    for col in numeric_cols:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).round(2)
                    inserted = 0
                    skipped = set()
                    for _, r in df.iterrows():
                        idx_name = r["Index Name"]
                        if idx_name not in symbol_map:
                            skipped.add(idx_name)
                            continue
                        cur.execute(
                            f"""
                            INSERT INTO {price_table} (
                                symbol_id, timeframe, date, open, high, low, close, volume, pct_price_change
                            )
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (symbol_id, timeframe, date)
                            DO UPDATE SET
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume,
                                pct_price_change = EXCLUDED.pct_price_change
                            """,
                            (
                                symbol_map[idx_name], TIMEFRAME, r["Index Date"],
                                r["Open Index Value"], r["High Index Value"], r["Low Index Value"],
                                r["Closing Index Value"], r["Volume"], r["Change(%)"]
                            )
                        )
                        inserted += 1
                    total_inserted += inserted
                    all_skipped.update(skipped)
                cur.execute(f"SELECT COUNT(*) FROM {price_table}")
                total_rows = (cur.fetchone() or [0])[0]
        log(f"NSE Index Price Data Update Completed | Inserted this run: {total_inserted} | Total rows: {total_rows}")
        if all_skipped:
            log(f"Skipped index names ({len(all_skipped)}): {', '.join(sorted(all_skipped))}")
        delete_files_in_folder(str(NSE_DIR))
    except Exception as e:
        log(f"❌ Fatal Error during NSE index incremental upsert: {e}")
        raise
# --------------------------------------------------------------------------
def update_nse_index_srt():
    log("Starting NSE Index SRT update")
    try:
        tables = ASSET_TABLE_CONFIG["nse_india_index"]
        symbols_table = tables["symbol"]
        price_table = tables["price"]
        srt_table = tables["srt"]
        
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT symbol_id, name
                    FROM {symbols_table}
                    WHERE is_active = TRUE AND UPPER(symbol) != 'INDIA VIX'
                """)
                indices = cur.fetchall()
                if not indices:
                    log("No active indices found")
                    return
                for idx, (index_id, index_name) in enumerate(indices, 1):
                    log(f"[{idx}/{len(indices)}] Processing {index_name}")
                    cur.execute(f"""
                        SELECT date, close
                        FROM {price_table}
                        WHERE symbol_id = %s AND timeframe = %s
                        ORDER BY date
                    """, (index_id, TIMEFRAME))
                    rows = cur.fetchall()
                    if not rows:
                        log(f"No price data for {index_name}, skipping")
                        continue
                    df = pd.DataFrame(rows, columns=["date", "close"])
                    df["sma_124"] = df["close"].rolling(SMA_PERIOD).mean()
                    df["srt"] = df["close"] / df["sma_124"]
                    df = df.dropna(subset=["srt"])
                    upserted = 0
                    for _, row in df.iterrows():
                        cur.execute(f"""
                            INSERT INTO {srt_table} (index_id, timeframe, date, srt)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (index_id, timeframe, date)
                            DO UPDATE SET srt = EXCLUDED.srt
                        """, (index_id, TIMEFRAME, row["date"], round(row["srt"], 2)))
                        upserted += 1
                    log(f"{index_name}: SRT updated for {upserted} dates")
        log("✅ NSE Index SRT update completed")
    except Exception as e:
        log(f"❌ Error updating SRT: {e}")
        raise
# --------------------------------------------------------------------------
def upsert_weekly_monthly_ohlc(
    price_table: str,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
):
    try:
        log(f"START OHLC UPSERT | table={price_table}")
        engine = get_engine()
        with get_db_connection() as conn:
            symbol_ids = pd.read_sql(
                f"SELECT DISTINCT symbol_id FROM {price_table} WHERE timeframe='1d'", engine
            )["symbol_id"].tolist()
            log(f"TOTAL SYMBOLS: {len(symbol_ids)}")
            if progress_callback:
                progress_callback("OHLC aggregation", 0, len(symbol_ids))
            for completed, symbol_id in enumerate(
                tqdm(
                    symbol_ids,
                    desc="Symbols",
                    ncols=100,
                    disable=progress_callback is not None,
                ),
                start=1,
            ):
                df = pd.read_sql(
                    f"""
                    SELECT date, open, high, low, close, volume
                    FROM {price_table}
                    WHERE symbol_id=%s AND timeframe='1d'
                    ORDER BY date
                    """,
                    engine,
                    params=(symbol_id,)
                )
                if df.empty:
                    log(f"SKIP SYMBOL {symbol_id} (no data)")
                    if progress_callback:
                        progress_callback("OHLC aggregation", completed, len(symbol_ids))
                    continue
                df["date"] = pd.to_datetime(df["date"])
                df["volume"] = df["volume"].fillna(0)
                def agg_ohlc(g):
                    if g.empty:
                        return pd.Series({'open':0,'high':0,'low':0,'close':0,'volume':0})
                    return pd.Series({
                        'open': g['open'].iloc[0] if 'open' in g else 0,
                        'high': g['high'].max() if 'high' in g else 0,
                        'low': g['low'].min() if 'low' in g else 0,
                        'close': g['close'].iloc[-1] if 'close' in g else 0,
                        'volume': g['volume'].sum() if 'volume' in g else 0
                    })
                df_w = df.resample('W-MON', on='date', label='left', closed='left').apply(agg_ohlc).reset_index()
                df_w["symbol_id"] = symbol_id
                df_w["timeframe"] = "1wk"
                df_m = df.resample('MS', on='date').apply(agg_ohlc).reset_index()
                df_m["symbol_id"] = symbol_id
                df_m["timeframe"] = "1mo"
                df_all = pd.concat([df_w, df_m])
                with conn.cursor() as cur:
                    for _, r in df_all.iterrows():
                        try:
                            cur.execute(f"""
                                INSERT INTO {price_table}
                                (symbol_id, timeframe, date, open, high, low, close, volume)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                                ON CONFLICT (symbol_id, timeframe, date)
                                DO UPDATE SET
                                    open=EXCLUDED.open,
                                    high=EXCLUDED.high,
                                    low=EXCLUDED.low,
                                    close=EXCLUDED.close,
                                    volume=EXCLUDED.volume
                            """, (
                                r["symbol_id"], r["timeframe"], r["date"],
                                r["open"], r["high"], r["low"], r["close"], r["volume"]
                            ))
                        except Exception:
                            log(f"UPSERT ERROR | symbol={symbol_id} date={r['date']}")
                            log(traceback.format_exc())
                    conn.commit()
                if progress_callback:
                    progress_callback("OHLC aggregation", completed, len(symbol_ids))
        log("✅ OHLC UPSERT COMPLETED")
    except Exception:
        log("❌ OHLC UPSERT FAILED")
        log(traceback.format_exc())
# --------------------------------------------------------------------------
def update_pct_price_change(price_table: str):
    try:
        log(f"✅ START pct_price_change UPDATE | table={price_table}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                log("RUNNING SQL UPDATE...")
                cur.execute(f"""
                    WITH ranked AS (
                        SELECT 
                            symbol_id,
                            timeframe,
                            date,
                            close,
                            LAG(close) OVER (
                                PARTITION BY symbol_id, timeframe 
                                ORDER BY date
                            ) AS prev_close
                        FROM {price_table}
                        WHERE timeframe IN ('1wk','1mo')
                    )
                    UPDATE {price_table} t
                    SET pct_price_change = COALESCE(
                        ROUND(
                            (
                                (r.close::numeric - r.prev_close::numeric)
                                / NULLIF(r.prev_close::numeric,0)
                            ) * 100
                        , 2),
                        0
                    )
                    FROM ranked r
                    WHERE t.symbol_id = r.symbol_id
                      AND t.timeframe = r.timeframe
                      AND t.date = r.date
                """)
                log(f"ROWS UPDATED: {cur.rowcount}")
                conn.commit()
        log("✅ pct_price_change UPDATE COMPLETED")
    except Exception:
        log("❌ pct_price_change UPDATE FAILED")
        log(traceback.format_exc())
# --------------------------------------------------------------------------
def update_weekly_monthly_for_all_symbols(
    asset_type: str,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
):
    log("START FULL PIPELINE")
    tables = ASSET_TABLE_CONFIG[asset_type]
    price_table = tables["price"]
    upsert_weekly_monthly_ohlc(price_table, progress_callback=progress_callback)
    if progress_callback:
        progress_callback("Price changes", 0, 1)
    update_pct_price_change(price_table)
    if progress_callback:
        progress_callback("Price changes", 1, 1)

    log("PIPELINE COMPLETED")
# --------------------------------------------------------------------------
def get_index_srt(index_name, timeframe=TIMEFRAME):
    """
    Retrieve the latest SRT value for the specified index.

    Args:
        index_name: Index name from nse_india_index_symbols.
        timeframe: Data timeframe (default: 1d).

    Returns:
        Dictionary containing index name, date and SRT.
    """

    try:
        tables = ASSET_TABLE_CONFIG["nse_india_index"]

        symbols_table = tables["symbol"]
        srt_table = tables["srt"]

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    f"""
                    SELECT
                        s.name AS index_name,
                        srt.date,
                        srt.srt
                    FROM {srt_table} srt
                    JOIN {symbols_table} s
                        ON s.symbol_id = srt.index_id
                    WHERE UPPER(TRIM(s.name)) = UPPER(TRIM(%s))
                      AND srt.timeframe = %s
                    ORDER BY srt.date DESC
                    LIMIT 1
                    """,
                    (index_name, timeframe)
                )

                row = cur.fetchone()

                if not row:
                    log(f"No SRT data found for index: {index_name}")
                    return None

                return {
                    "index_name": row[0],
                    "date": row[1],
                    "srt": row[2]
                }

    except Exception as e:
        log(f"❌ Error fetching SRT for {index_name}: {e}")
        return None
# --------------------------------------------------------------------------
def get_all_index_srt(timeframe=TIMEFRAME):
    """
    Retrieve the latest SRT value for all indices,
    excluding India VIX.

    Args:
        timeframe: Data timeframe (default: 1d).

    Returns:
        List of dictionaries containing index_name, date and srt.
    """

    try:
        tables = ASSET_TABLE_CONFIG["nse_india_index"]

        symbols_table = tables["symbol"]
        srt_table = tables["srt"]

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    f"""
                    SELECT DISTINCT ON (srt.index_id)
                        s.name AS index_name,
                        srt.date,
                        srt.srt
                    FROM {srt_table} srt
                    JOIN {symbols_table} s
                        ON s.symbol_id = srt.index_id
                    WHERE srt.timeframe = %s
                      AND UPPER(TRIM(s.name)) <> 'INDIA VIX'
                    ORDER BY
                        srt.index_id,
                        srt.date DESC
                    """,
                    (timeframe,)
                )

                rows = cur.fetchall()

                if not rows:
                    log(f"No index SRT data found for timeframe: {timeframe}")
                    return []

                return [
                    {
                        "index_name": row[0],
                        "date": row[1],
                        "srt": row[2]
                    }
                    for row in rows
                ]

    except Exception as e:
        log(f"❌ Error fetching all index SRT: {e}")
        return []
# --------------------------------------------------------------------------