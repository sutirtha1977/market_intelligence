from datetime import timedelta
from database.connection import get_db_connection, close_db_connection
from config.logger import log
from config.db_table import FNO_TABLE_MAP
from tqdm import tqdm

# --------------------------------------------------------------------------
def update_iv_stats(asset_type: str):
    options_table = FNO_TABLE_MAP[asset_type][0]
    greeks_table = FNO_TABLE_MAP[asset_type][4]
    iv_table = FNO_TABLE_MAP[asset_type][5]
    log(f"📈 IV STATS START | {asset_type.upper()}")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT MAX(trade_date) FROM {iv_table}")
        row = cur.fetchone()
        last_done = row[0] if row and row[0] else None
        cur.execute(f"""
            SELECT MIN(trade_date), MAX(trade_date)
            FROM {greeks_table}
            WHERE implied_volatility > 0
        """)
        row = cur.fetchone()
        if not row or not row[0] or not row[1]:
            log(f"⚠️ No Greeks data in {greeks_table}")
            return
        src_min, src_max = row
        start_date = (last_done + timedelta(days=1)) if last_done else src_min
        end_date = src_max
        if start_date > end_date:
            log(f"✅ IV already up-to-date | {asset_type.upper()} (last={last_done})")
            return
        dates = []
        d = start_date
        while d <= end_date:
            dates.append(d)
            d += timedelta(days=1)
        log(f"📊 Processing {asset_type.upper()} | {start_date} → {end_date} | days={len(dates)}")
        for trade_date in tqdm(dates, desc=f"IV {asset_type}", ncols=100):
            query = f"""
            WITH base AS (
                SELECT
                    o.trade_date,
                    o.symbol,
                    o.expiry_date,
                    o.strike_price,
                    o.underlying_price,
                    g.implied_volatility,
                    ABS(o.strike_price - o.underlying_price) AS gap
                FROM {options_table} o
                JOIN {greeks_table} g
                  ON o.trade_date = g.trade_date
                 AND o.symbol = g.symbol
                 AND o.expiry_date = g.expiry_date
                 AND o.strike_price = g.strike_price
                 AND o.option_type = g.option_type
                WHERE g.implied_volatility > 0
                  AND o.trade_date = %s
            ),
            atm_iv AS (
                SELECT DISTINCT ON (trade_date, symbol)
                    trade_date,
                    symbol,
                    implied_volatility AS iv_current
                FROM base
                ORDER BY trade_date, symbol, gap
            ),
            iv_window AS (
                SELECT
                    a.trade_date,
                    a.symbol,
                    a.iv_current,
                    MAX(a.iv_current) OVER (
                        PARTITION BY a.symbol
                        ORDER BY a.trade_date
                        ROWS BETWEEN 365 PRECEDING AND CURRENT ROW
                    ) AS iv_52w_high,
                    MIN(a.iv_current) OVER (
                        PARTITION BY a.symbol
                        ORDER BY a.trade_date
                        ROWS BETWEEN 365 PRECEDING AND CURRENT ROW
                    ) AS iv_52w_low
                FROM atm_iv a
            )
            INSERT INTO {iv_table} (
                trade_date,
                symbol,
                iv_current,
                iv_52w_high,
                iv_52w_low,
                iv_rank,
                iv_percentile,
                created_at
            )
            SELECT
                trade_date,
                symbol,
                iv_current,
                iv_52w_high,
                iv_52w_low,
                CASE
                    WHEN iv_52w_high = iv_52w_low THEN 0
                    ELSE ROUND(
                        (
                            (iv_current - iv_52w_low) /
                            NULLIF((iv_52w_high - iv_52w_low), 0)
                        )::numeric,
                        4
                    )
                END,
                0,
                NOW()
            FROM iv_window
            ON CONFLICT (trade_date, symbol)
            DO UPDATE SET
                iv_current = EXCLUDED.iv_current,
                iv_52w_high = EXCLUDED.iv_52w_high,
                iv_52w_low = EXCLUDED.iv_52w_low,
                iv_rank = EXCLUDED.iv_rank,
                created_at = NOW();
            """
            cur.execute(query, (trade_date,))
            conn.commit()
        log(f"✅ IV STATS DONE | {asset_type.upper()}")
    except Exception as e:
        conn.rollback()
        log(f"❌ IV STATS FAILED | {asset_type.upper()} | {e}")
        raise
    finally:
        close_db_connection(conn)

# --------------------------------------------------------------------------
def update_all_iv_stats():
    log("🚀 IV STATS PIPELINE START")
    for asset in ["stock", "index"]:
        try:
            update_iv_stats(asset)
        except Exception as e:
            log(f"❌ Failed for {asset.upper()} | {e}")
    log("🎉 IV STATS PIPELINE COMPLETE")
# --------------------------------------------------------------------------