import yfinance as yf
import pandas as pd
from typing import Callable, List, Optional, Tuple
import traceback

from psycopg2.extras import execute_values

from config.logger import log
from config.constants import FREQUENCIES
from config.db_config import ASSET_TABLE_CONFIG
from database.connection import get_db_connection_cm

# --------------------------------------------------------------------------
def _fetch_symbols_from_db(cur, symbol_table: str, symbols: str) -> List[Tuple[int, str]]:
    log(f"▶ FETCH SYMBOLS START | table={symbol_table} | symbols={symbols}")
    try:
        query = f"""
        SELECT symbol_id, symbol
        FROM {symbol_table}
        WHERE is_active = TRUE
        """
        params = []
        requested_symbols = symbols.strip().upper() if symbols else "ALL"
        if requested_symbols != "ALL":
            symbol_list = [s.strip().upper() for s in requested_symbols.split(",") if s.strip()]
            placeholders = ",".join(["%s"] * len(symbol_list))
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbol_list)
        if requested_symbols != "ALL" and not params:
            return []
        query += " ORDER BY symbol_id"
        cur.execute(query, params)
        rows = cur.fetchall()
        log(f"✅ FETCH SYMBOLS END | loaded={len(rows)}")
        return rows
    except Exception:
        log(f"❌ FETCH SYMBOLS FAILED\n{traceback.format_exc()}")
        raise
# --------------------------------------------------------------------------
def _download_symbol_data(symbol: str, asset_type: str, timeframe: str, start_date: str) -> Tuple[pd.DataFrame, str, str]:
    symbol_clean = symbol.strip().upper()
    original_symbol = symbol_clean
    download_symbol = f"{symbol_clean}.NS" if "india_equity" in asset_type and not symbol_clean.endswith(".NS") else symbol_clean
    try:
        # end_date = pd.Timestamp.today()
        end_date = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        df = yf.download(
            download_symbol,
            start=start_date,
            end=end_date,
            interval=timeframe,
            auto_adjust=False,
            progress=False,
        )
        if df is None or df.empty:
            return pd.DataFrame(), download_symbol, original_symbol
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]
        df = df.sort_values("Date")
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
        price_cols = ["Open", "High", "Low", "Close", "Adj Close"]
        for col in price_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype("int64")
        df["price_final"] = df["Adj Close"]
        df.loc[df["price_final"].isna() | (df["price_final"] <= 0), "price_final"] = df["Close"]
        df["pct_price_change"] = (
            df["price_final"]
            .pct_change(fill_method=None)
            .replace([float("inf"), float("-inf")], 0.0)
            .fillna(0.0)
            .mul(100)
            .round(2)
        )
        return df, download_symbol, original_symbol
    except Exception:
        log(f"❌ DOWNLOAD FAILED | {symbol_clean} | {timeframe}\n{traceback.format_exc()}")
        return pd.DataFrame(), download_symbol, original_symbol
# --------------------------------------------------------------------------
def _build_rows(symbol_id: int, timeframe: str, df: pd.DataFrame):
    try:
        values = df[
            ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "pct_price_change"]
        ].itertuples(index=False, name=None)
        return [
            (symbol_id, timeframe, *row)
            for row in values
        ]
    except Exception:
        log(f"❌ BUILD ROWS FAILED | symbol_id={symbol_id} | tf={timeframe}\n{traceback.format_exc()}")
        raise
# --------------------------------------------------------------------------
def _upsert_rows(conn, price_table: str, rows: list, silent: bool = False):
    if not rows:
        return
    if not silent:
        log(f"▶ UPSERT START | table={price_table} | rows={len(rows)}")
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                f"""
                INSERT INTO {price_table} (
                    symbol_id, timeframe, date,
                    open, high, low, close, adj_close,
                    volume, pct_price_change
                )
                VALUES %s
                ON CONFLICT (symbol_id, timeframe, date)
                DO UPDATE SET
                    open=EXCLUDED.open,
                    high=EXCLUDED.high,
                    low=EXCLUDED.low,
                    close=EXCLUDED.close,
                    adj_close=EXCLUDED.adj_close,
                    volume=EXCLUDED.volume,
                    pct_price_change=EXCLUDED.pct_price_change
                """,
                rows,
                page_size=1000,
            )
        if not silent:
            log("✅ UPSERT END")
    except Exception:
        log(f"❌ UPSERT FAILED | table={price_table}\n{traceback.format_exc()}")
        raise
# --------------------------------------------------------------------------
def insert_yahoo_price_data(
    asset_type: str,
    symbols: str = "ALL",
    start_date: str = "1999-01-01",
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> List[str]:
    log(f"✅ PIPELINE START | asset_type={asset_type} | symbols={symbols}")
    failed_symbols: List[str] = []
    tables = ASSET_TABLE_CONFIG[asset_type]
    symbol_table = tables["symbol"]
    price_table = tables["price"]

    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                symbol_rows = _fetch_symbols_from_db(cur, symbol_table, symbols)
            for tf in FREQUENCIES:
                log(f"▶ TIMEFRAME START | {tf}")
                timeframe_rows = []
                total_symbols = len(symbol_rows)
                if progress_callback:
                    progress_callback(tf, 0, total_symbols)
                for completed, (symbol_id, symbol) in enumerate(symbol_rows, start=1):
                    original_symbol = symbol
                    try:
                        df, download_symbol, original_symbol = _download_symbol_data(symbol, asset_type, tf, start_date)
                        if df is None or df.empty:
                            failed_symbols.append(original_symbol)
                        else:
                            timeframe_rows.extend(_build_rows(symbol_id, tf, df))
                    except Exception:
                        failed_symbols.append(original_symbol)
                        log(f"❌ SYMBOL FAILED | {symbol} | {tf}\n{traceback.format_exc()}")
                    if progress_callback:
                        progress_callback(tf, completed, total_symbols)
                _upsert_rows(conn, price_table, timeframe_rows, silent=True)
                conn.commit()
                log(f"✅ TIMEFRAME END | {tf}")
    except Exception:
        log(f"❌ PIPELINE FAILED\n{traceback.format_exc()}")
    failed_symbols = sorted(set(failed_symbols))
    log(f"✅ PIPELINE END | failed={len(failed_symbols)}")
    return failed_symbols
# --------------------------------------------------------------------------