import pandas as pd
from database.connection import get_db_connection_cm
from config.logger import log
from config.db_table import ASSET_TABLE_CONFIG

# --------------------------------------------------------------------------
def get_index_overview() -> pd.DataFrame:
    
    tables = ASSET_TABLE_CONFIG["nse_india_index"]
    symbols_table = tables["symbol"]
    price_table = tables["price"]
    srt_table = tables["srt"]

    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                query = f"""
                    WITH latest_price_date AS (
                        SELECT MAX(date) AS max_date
                        FROM {price_table}
                        WHERE timeframe = '1d'
                    ),

                    latest_price AS (
                        SELECT
                            p.symbol_id,
                            p.close
                        FROM {price_table} p
                        JOIN latest_price_date d
                          ON p.date = d.max_date
                        WHERE p.timeframe = '1d'
                    ),

                    latest_srt AS (
                        SELECT
                            m.index_id,
                            m.srt
                        FROM {srt_table} m
                        JOIN latest_price_date d
                          ON m.date = d.max_date
                    ),

                    hist AS (
                        SELECT
                            m.index_id,
                            MIN(m.srt) AS min_srt,
                            MAX(m.srt) AS max_srt
                        FROM {srt_table} m
                        GROUP BY m.index_id
                    ),

                    ath AS (
                        SELECT
                            p.symbol_id,
                            COALESCE(MAX(p.high), 0) AS ath
                        FROM {price_table} p
                        WHERE p.timeframe = '1d'
                        GROUP BY p.symbol_id
                    ),

                    high_52w AS (
                        SELECT
                            p.symbol_id,
                            COALESCE(MAX(p.high), 0) AS high_52w
                        FROM {price_table} p
                        JOIN latest_price_date d
                          ON p.date >= d.max_date - INTERVAL '365 days'
                        WHERE p.timeframe = '1d'
                        GROUP BY p.symbol_id
                    )

                    SELECT
                        s.symbol_id AS symbol_id,
                        s.symbol AS symbol,
                        s.exchange AS type,
                        latest_srt.srt AS srt,
                        hist.min_srt AS min_srt,
                        hist.max_srt AS max_srt,
                        COALESCE(lp.close, 0) AS close,
                        COALESCE(ath.ath, 0) AS ath,
                        COALESCE(h52.high_52w, 0) AS high_52w,
                        (SELECT max_date FROM latest_price_date) AS date

                    FROM {symbols_table} s
                    LEFT JOIN latest_srt ON latest_srt.index_id = s.symbol_id
                    LEFT JOIN hist ON hist.index_id = s.symbol_id
                    LEFT JOIN latest_price lp ON lp.symbol_id = s.symbol_id
                    LEFT JOIN ath ON ath.symbol_id = s.symbol_id
                    LEFT JOIN high_52w h52 ON h52.symbol_id = s.symbol_id

                    WHERE s.symbol <> 'India VIX'
                      AND lp.close IS NOT NULL

                    ORDER BY latest_srt.srt ASC;
                """

                cur.execute(query)
                rows = cur.fetchall()

        if not rows:
            log("ℹ No SRT data found")
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=[
            "symbol_id", "Symbol", "Type", "SRT", "Min SRT", "Max SRT",
            "Close", "ATH", "52W High", "Date"
        ])

        # ================= CLEAN =================
        df["Symbol"] = df["Symbol"].astype(str)

        df[["SRT", "Min SRT", "Max SRT"]] = df[
            ["SRT", "Min SRT", "Max SRT"]
        ].apply(pd.to_numeric, errors="coerce").round(2)

        # ===== INTEGER FIELDS =====
        for col in ["Close", "ATH", "52W High"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).round(0).astype("Int64")

        # ===== DATE FORMAT =====
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d-%b-%Y")

        return df

    except Exception as e:
        log(f"❌ Error fetching SRT data: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------  
def fetch_index_rsi_crossovers(
    range_min,
    range_max,
    asset_key="nse_india_index",
    timeframe="1d"
) -> pd.DataFrame:

    try:
        tables = ASSET_TABLE_CONFIG[asset_key]
        symbols_table = tables["symbol"]
        price_table = tables["price"]
        indicators_table = tables["indicator"]

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                query = f"""
                WITH latest_date AS (
                    SELECT MAX(date) AS max_date
                    FROM {price_table}
                    WHERE timeframe = %s
                ),

                ranked AS (
                    SELECT 
                        i.symbol_id,
                        i.date,
                        i.rsi_9,
                        i.wma_rsi_9_21,
                        ROW_NUMBER() OVER (
                            PARTITION BY i.symbol_id 
                            ORDER BY i.date DESC
                        ) AS rn
                    FROM {indicators_table} i
                    JOIN latest_date d
                      ON i.date <= d.max_date
                    WHERE i.timeframe = %s
                ),

                pivot AS (
                    SELECT
                        t1.symbol_id,
                        t1.rsi_9  AS rsi_today,
                        t1.wma_rsi_9_21 AS wma_today,
                        t1.date AS latest_date,
                        t2.rsi_9  AS rsi_prev,
                        t2.wma_rsi_9_21 AS wma_prev
                    FROM ranked t1
                    JOIN ranked t2 
                        ON t1.symbol_id = t2.symbol_id
                       AND t1.rn = 1
                       AND t2.rn = 2
                )

                SELECT 
                    s.name AS symbol,
                    p.latest_date,
                    ROUND(p.rsi_today::numeric, 2) AS rsi_9,
                    ROUND(p.wma_today::numeric, 2) AS wma_rsi_9_21

                FROM pivot p
                JOIN {symbols_table} s 
                    ON s.symbol_id = p.symbol_id

                WHERE 
                    p.rsi_today > p.wma_today
                    AND p.rsi_prev <= p.wma_prev
                    AND p.wma_today > %s
                    AND p.wma_today < %s

                ORDER BY p.rsi_today DESC;
                """

                cur.execute(
                    query,
                    (timeframe, timeframe, range_min, range_max)
                )

                rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=[
            "Symbol", "Date", "RSI_9", "WMA_RSI_9_21"
        ])

        # ✅ Format date
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d-%b-%Y")

        return df

    except Exception as e:
        log(f"❌ Error fetching RSI crossover data: {e}")
        return pd.DataFrame()  
    
# --------------------------------------------------------------------------
def get_index_yearly_heatmap(
    symbol: str,
    asset_key: str = "nse_india_index"
) -> pd.DataFrame:

    tables = ASSET_TABLE_CONFIG[asset_key]
    symbols_table = tables["symbol"]
    price_table = tables["price"]

    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                query = f"""
                    WITH base AS (
                        SELECT
                            EXTRACT(YEAR FROM p.date)::int AS year,
                            EXTRACT(MONTH FROM p.date)::int AS month,
                            p.close,
                            LAG(p.close) OVER (ORDER BY p.date) AS prev_close
                        FROM {price_table} p
                        JOIN {symbols_table} s
                            ON p.symbol_id = s.symbol_id
                        WHERE s.symbol = %s
                          AND p.timeframe = '1mo'
                    )

                    SELECT
                        year,
                        month,
                        ROUND(
                            CASE
                                WHEN prev_close IS NULL OR prev_close = 0 THEN 0
                                ELSE ((close - prev_close) / prev_close * 100)::numeric
                            END, 2
                        ) AS pct_return

                    FROM base
                    ORDER BY year, month;
                """

                cur.execute(query, (symbol,))
                rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["Year", "Month", "Return"])

        # --------------------------------------------------
        # Month mapping
        # --------------------------------------------------
        month_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        df["Month_Name"] = df["Month"].map(month_map)

        # --------------------------------------------------
        # Fill missing months (important for heatmap)
        # --------------------------------------------------
        all_years = sorted(df["Year"].unique(), reverse=True)
        all_months = list(month_map.values())

        full_index = pd.MultiIndex.from_product(
            [all_years, all_months],
            names=["Year", "Month_Name"]
        )

        df = (
            df.set_index(["Year", "Month_Name"])
              .reindex(full_index, fill_value=0)
              .reset_index()
        )

        # --------------------------------------------------
        # Pivot (READY for heatmap directly)
        # --------------------------------------------------
        heatmap_df = df.pivot(
            index="Year",
            columns="Month_Name",
            values="Return"
        )[all_months]

        return heatmap_df

    except Exception as e:
        log(f"❌ Error in get_index_yearly_heatmap({symbol}): {e}")
        return pd.DataFrame()