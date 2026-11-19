from database.connection import get_db_connection, close_db_connection,get_engine
from config.logger import log
import pandas as pd
from config.db_table import FNO_TABLE_MAP

# --------------------------------------------------------------------------
def calculate_and_upsert_pcr():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        log("📊 Starting PCR calculation (STOCK + INDEX separately)")

        # =========================================================
        # 1. STOCK OPTIONS PCR
        # =========================================================
        stock_options_table = FNO_TABLE_MAP["stock"][0]
        stock_pcr_table = FNO_TABLE_MAP["stock"][3]

        log(f"📌 Processing STOCK options PCR | {stock_options_table} → {stock_pcr_table}")

        stock_query = f"""
        WITH aggregated AS (
            SELECT
                trade_date,
                symbol,
                expiry_date,

                SUM(CASE WHEN option_type = 'PE' THEN open_interest ELSE 0 END) AS put_oi,
                SUM(CASE WHEN option_type = 'CE' THEN open_interest ELSE 0 END) AS call_oi,

                SUM(CASE WHEN option_type = 'PE' THEN traded_volume ELSE 0 END) AS put_vol,
                SUM(CASE WHEN option_type = 'CE' THEN traded_volume ELSE 0 END) AS call_vol,

                SUM(CASE WHEN option_type = 'PE' THEN ABS(change_in_oi) ELSE 0 END) AS put_coi,
                SUM(CASE WHEN option_type = 'CE' THEN ABS(change_in_oi) ELSE 0 END) AS call_coi

            FROM {stock_options_table}
            GROUP BY trade_date, symbol, expiry_date
        )

        INSERT INTO {stock_pcr_table} (
            trade_date,
            symbol,
            expiry_date,
            pcr_open_interest,
            pcr_volume,
            pcr_change_in_oi,
            created_at
        )
        SELECT
            trade_date,
            symbol,
            expiry_date,

            ROUND(COALESCE(put_oi::NUMERIC / NULLIF(call_oi, 0), 0), 3),
            ROUND(COALESCE(put_vol::NUMERIC / NULLIF(call_vol, 0), 0), 3),
            ROUND(COALESCE(put_coi::NUMERIC / NULLIF(call_coi, 0), 0), 3),

            NOW()

        FROM aggregated

        ON CONFLICT (trade_date, symbol, expiry_date)
        DO UPDATE SET
            pcr_open_interest = EXCLUDED.pcr_open_interest,
            pcr_volume        = EXCLUDED.pcr_volume,
            pcr_change_in_oi  = EXCLUDED.pcr_change_in_oi,
            created_at        = NOW();
        """

        cur.execute(stock_query)
        conn.commit()
        log("✅ STOCK PCR updated")

        # =========================================================
        # 2. INDEX OPTIONS PCR
        # =========================================================
        index_options_table = FNO_TABLE_MAP["index"][0]
        index_pcr_table = FNO_TABLE_MAP["index"][3]

        log(f"📌 Processing INDEX options PCR | {index_options_table} → {index_pcr_table}")

        index_query = f"""
        WITH aggregated AS (
            SELECT
                trade_date,
                symbol,
                expiry_date,

                SUM(CASE WHEN option_type = 'PE' THEN open_interest ELSE 0 END) AS put_oi,
                SUM(CASE WHEN option_type = 'CE' THEN open_interest ELSE 0 END) AS call_oi,

                SUM(CASE WHEN option_type = 'PE' THEN traded_volume ELSE 0 END) AS put_vol,
                SUM(CASE WHEN option_type = 'CE' THEN traded_volume ELSE 0 END) AS call_vol,

                SUM(CASE WHEN option_type = 'PE' THEN ABS(change_in_oi) ELSE 0 END) AS put_coi,
                SUM(CASE WHEN option_type = 'CE' THEN ABS(change_in_oi) ELSE 0 END) AS call_coi

            FROM {index_options_table}
            GROUP BY trade_date, symbol, expiry_date
        )

        INSERT INTO {index_pcr_table} (
            trade_date,
            symbol,
            expiry_date,
            pcr_open_interest,
            pcr_volume,
            pcr_change_in_oi,
            created_at
        )
        SELECT
            trade_date,
            symbol,
            expiry_date,

            ROUND(COALESCE(put_oi::NUMERIC / NULLIF(call_oi, 0), 0), 3),
            ROUND(COALESCE(put_vol::NUMERIC / NULLIF(call_vol, 0), 0), 3),
            ROUND(COALESCE(put_coi::NUMERIC / NULLIF(call_coi, 0), 0), 3),

            NOW()

        FROM aggregated

        ON CONFLICT (trade_date, symbol, expiry_date)
        DO UPDATE SET
            pcr_open_interest = EXCLUDED.pcr_open_interest,
            pcr_volume        = EXCLUDED.pcr_volume,
            pcr_change_in_oi  = EXCLUDED.pcr_change_in_oi,
            created_at        = NOW();
        """

        cur.execute(index_query)
        conn.commit()
        log("✅ INDEX PCR updated")

        log("🎉 PCR calculation completed for STOCK + INDEX")

    except Exception as e:
        conn.rollback()
        log(f"❌ PCR calculation failed: {e}")
        raise

    finally:
        close_db_connection(conn)
        
# --------------------------------------------------------------------------
def get_pcr_data(asset_type="index"):
    engine = get_engine()

    # get correct PCR table from map
    pcr_table = FNO_TABLE_MAP[asset_type][3]

    query = f"""
        WITH latest_date AS (
            SELECT 
                symbol,
                MAX(trade_date) AS max_date
            FROM {pcr_table}
            GROUP BY symbol
        ),

        base AS (
            SELECT 
                p.symbol,
                p.trade_date,
                p.expiry_date,
                p.pcr_open_interest,
                p.pcr_volume,
                p.pcr_change_in_oi,
                DATE_TRUNC('month', p.expiry_date) AS expiry_month
            FROM {pcr_table} p
            INNER JOIN latest_date l
              ON p.symbol = l.symbol
             AND p.trade_date = l.max_date
        ),

        month_ranked AS (
            SELECT DISTINCT
                symbol,
                trade_date,
                expiry_date,
                pcr_open_interest,
                pcr_volume,
                pcr_change_in_oi,
                expiry_month,

                DENSE_RANK() OVER (
                    PARTITION BY symbol
                    ORDER BY expiry_month
                ) AS month_rank
            FROM base
        )

        SELECT *,
            CASE 
                WHEN month_rank = 1 THEN 'CURRENT'
                WHEN month_rank = 2 THEN 'NEXT'
                WHEN month_rank = 3 THEN 'NEXT_NEXT'
            END AS expiry_tag
        FROM month_ranked
        WHERE month_rank <= 3
        ORDER BY symbol, expiry_date;
    """

    return pd.read_sql(query, engine)

# --------------------------------------------------------------------------
def get_latest_pcr_data(cur, asset_type="index"):
    pcr_table = FNO_TABLE_MAP[asset_type][3]

    query = f"""
        SELECT DISTINCT ON (symbol)
            symbol,
            trade_date,
            expiry_date,
            pcr_open_interest,
            pcr_volume,
            pcr_change_in_oi
        FROM {pcr_table}
        ORDER BY 
            symbol,
            trade_date DESC,
            expiry_date ASC
    """

    cur.execute(query)
    rows = cur.fetchall()

    if not rows:
        return pd.DataFrame()

    cols = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=cols)

    # enforce custom order
    order = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]
    df["sort_key"] = df["symbol"].apply(lambda x: order.index(x) if x in order else 999)

    df = df.sort_values("sort_key").drop(columns=["sort_key"])

    return df
# --------------------------------------------------------------------------
