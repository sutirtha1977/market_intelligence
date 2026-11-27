from database.connection import get_engine, get_db_connection_cm
from config.logger import log

import pandas as pd
import numpy as np
import talib

# --------------------------------------------------------------------------
def compute_vix_features_talib():

    log("========== VIX FEATURE (TA-LIB) START ==========")

    try:
        # ----------------------------------------------------------
        # Step 1: Load data
        # ----------------------------------------------------------
        engine = get_engine()

        df = pd.read_sql("""
            SELECT date, vix
            FROM nse_vix_features
            ORDER BY date
        """, engine)

        if df.empty:
            log("No VIX data found")
            return

        log(f"Loaded {len(df)} rows")

        # Ensure sorted
        df = df.sort_values("date")

        # ----------------------------------------------------------
        # Step 2: TA-Lib Indicators (vectorized)
        # ----------------------------------------------------------
        # df["vix_ma_5"] = talib.SMA(df["vix"], timeperiod=5)
        # df["vix_ma_10"] = talib.SMA(df["vix"], timeperiod=10)
        import numpy as np
        from numpy.typing import NDArray
        # Explicitly type the array as NDArray[float64]
        vix_array: NDArray[np.float64] = df["vix"].to_numpy(dtype=np.float64)

        df["vix_ma_5"] = talib.SMA(vix_array, timeperiod=5)
        df["vix_ma_10"] = talib.SMA(vix_array, timeperiod=10)

        # Change (absolute)
        df["vix_change"] = df["vix"].diff()

        # ----------------------------------------------------------
        # Step 3: Percentile (vectorized)
        # ----------------------------------------------------------
        df["vix_percentile"] = df["vix"].rank(pct=True)

        # ----------------------------------------------------------
        # Step 4: Regime classification
        # ----------------------------------------------------------
        conditions = [
            df["vix_percentile"] < 0.2,
            df["vix_percentile"] < 0.6,
            df["vix_percentile"] < 0.8
        ]

        regimes = ["LOW", "NORMAL", "HIGH"]

        df["vix_regime"] = np.select(conditions, regimes, default="EXTREME")

        # ----------------------------------------------------------
        # Step 5: Signal mapping
        # ----------------------------------------------------------
        signal_map = {
            "LOW": "OPTION-BUY",
            "NORMAL": "SPREAD",
            "HIGH": "OPTION-SELL",
            "EXTREME": "HEDGE"
        }

        df["vix_signal"] = df["vix_regime"].map(signal_map)

        # ----------------------------------------------------------
        # Step 6: Update DB (bulk)
        # ----------------------------------------------------------
        update_query = """
            UPDATE nse_vix_features
            SET 
                vix_ma_5 = %s,
                vix_ma_10 = %s,
                vix_change = %s,
                vix_percentile = %s,
                vix_regime = %s,
                vix_signal = %s
            WHERE date = %s
        """

        data = list(zip(
            df["vix_ma_5"],
            df["vix_ma_10"],
            df["vix_change"],
            df["vix_percentile"],
            df["vix_regime"],
            df["vix_signal"],
            df["date"]
        ))

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                log("Updating VIX features (bulk)...")
                cur.executemany(update_query, data)

        log("========== VIX FEATURE (TA-LIB) COMPLETE ==========")

    except Exception as e:
        log(f"❌ VIX FEATURE (TA-LIB) FAILED: {e}")
        raise
# --------------------------------------------------------------------------
def update_vix_daily_data():
    log("========== VIX UPDATE START ==========")

    query = """
    WITH vix_symbol AS (
        SELECT symbol_id
        FROM nse_india_index_symbols
        WHERE UPPER(symbol) = 'INDIA VIX'
    )
    INSERT INTO nse_vix_features (date, vix)
    SELECT 
        p.date,
        ROUND(p.close::numeric, 2)
    FROM nse_india_index_price p
    JOIN vix_symbol v
        ON p.symbol_id = v.symbol_id
    WHERE p.timeframe = '1d'
    ON CONFLICT (date) DO UPDATE
    SET vix = EXCLUDED.vix;
    """
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                log("Executing VIX upsert query...")
                cur.execute(query)

                rows = cur.rowcount  # rows affected
                log(f"VIX rows processed: {rows}")

        log("========== VIX UPDATE SUCCESS ==========")

    except Exception as e:
        log(f"❌ VIX UPDATE FAILED: {e}")
        raise
# --------------------------------------------------------------------------
def get_vix_last_n_days(n_days: int = 10) -> pd.DataFrame:

    log(f"Fetching last {n_days} days of VIX data")

    try:
        engine = get_engine()

        query = f"""
            SELECT 
                date,
                vix,
                vix_ma_5,
                vix_ma_10,
                vix_change,
                vix_percentile,
                vix_regime,
                vix_signal
            FROM nse_vix_features
            ORDER BY date DESC
            LIMIT {n_days}
        """

        df = pd.read_sql(query, engine)

        if df.empty:
            log("No VIX data found")
            return df

        # Optional: sort ascending for charts
        df = df.sort_values("date")

        log(f"Fetched {len(df)} rows")

        return df

    except Exception as e:
        log(f"❌ FAILED to fetch VIX data: {e}")
        raise
# --------------------------------------------------------------------------
def get_vix_last_n_days_new(cur, n_days: int = 10) -> pd.DataFrame:

    log(f"Fetching last {n_days} days of VIX data")

    try:
        query = """
            SELECT 
                date,
                vix,
                vix_ma_5,
                vix_ma_10,
                vix_change,
                vix_percentile,
                vix_regime,
                vix_signal
            FROM nse_vix_features
            ORDER BY date DESC
            LIMIT %s
        """

        cur.execute(query, (n_days,))
        rows = cur.fetchall()

        if not rows:
            log("No VIX data found")
            return pd.DataFrame()

        # Convert to DataFrame
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)

        # Optional: sort ascending for charts
        df = df.sort_values("date")

        log(f"Fetched {len(df)} rows")

        return df

    except Exception as e:
        log(f"❌ FAILED to fetch VIX data: {e}")
        raise
# --------------------------------------------------------------------------