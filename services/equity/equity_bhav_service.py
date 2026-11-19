import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from config.logger import log
from config.constants import NSE_EQ_DELV_BHAV
from database.connection import get_db_connection_cm
from psycopg2.extras import execute_values

# --------------------------------------------------------------------------
def update_delv_pct_from_nse_hist(start_year=2000, save_dir=None):
    try:
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                # Fetch active symbols
                cur.execute("SELECT symbol_id, symbol FROM yahoo_india_equity_symbols WHERE is_active=TRUE")
                symbols = cur.fetchall()
                if not symbols:
                    log("⚠️ No active symbols found")
                    return
                current_year = datetime.today().year
                if save_dir:
                    hist_dir = Path(save_dir)
                else:
                    hist_dir = Path.cwd() / "equity_bhavcopy_historical"
                hist_dir.mkdir(parents=True, exist_ok=True)
                for symbol_id, symbol in symbols:
                    symbol_clean = symbol.replace(".NS", "")
                    log(f"🔹 Processing symbol: {symbol_clean}")
                    for year in range(start_year, current_year + 1):
                        from_date = f"01-01-{year}"
                        to_date = datetime.today().strftime("%d-%m-%Y") if year == current_year else f"31-12-{year}"
                        url = NSE_EQ_DELV_BHAV.format(symbol_clean=symbol_clean, from_date=from_date, to_date=to_date)
                        csv_file = hist_dir / f"{symbol_clean}_{year}.csv"
                        try:
                            headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv,application/vnd.ms-excel"}
                            response = requests.get(url, headers=headers, timeout=30)
                            if response.status_code != 200 or "404" in response.text:
                                log(f"❌ Failed to download {symbol_clean} {year}: HTTP {response.status_code}")
                                continue
                            csv_file.write_text(response.text, encoding='utf-8-sig')
                            log(f"    ✅ CSV saved: {csv_file}")
                        except Exception as e:
                            log(f"❌ Error downloading {symbol_clean} {year}: {e}")
                            continue
                        try:
                            df = pd.read_csv(
                                csv_file,
                                usecols=lambda x: 'Date' in x or 'Series' in x or 'Dly Qt' in x,
                                encoding='utf-8-sig'
                            )

                            # Clean column names
                            df.columns = df.columns.str.strip().str.replace(r'[^\x00-\x7F]+', '', regex=True)
                            pct_col = [c for c in df.columns if 'Dly Qt' in c][0]
                            df.rename(columns={pct_col: '% Dly Qt to Traded Qty'}, inplace=True)

                            # Filter EQ series
                            df = df[df['Series'] == 'EQ']
                            if df.empty:
                                log(f"⚠️ No EQ data in {csv_file}, skipping")
                                continue

                            # Convert Date
                            df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y', errors='coerce')
                            df = df.dropna(subset=['Date'])
                            df['Date'] = df['Date'].dt.date

                            # Clean numeric column
                            df['% Dly Qt to Traded Qty'] = (
                                df['% Dly Qt to Traded Qty']
                                .astype(str)
                                .str.replace(',', '')   # remove thousand separators
                                .replace('-', '0')     # replace '-' with 0
                            )
                            df['% Dly Qt to Traded Qty'] = pd.to_numeric(df['% Dly Qt to Traded Qty'], errors='coerce').fillna(0)

                            # Prepare batch update
                            updates = [(row['% Dly Qt to Traded Qty'], symbol_id, row['Date']) for _, row in df.iterrows()]
                            if not updates:
                                log(f"⚠️ No valid % Dly Qt data for {symbol_clean} {year}")
                                continue

                            # Batch update DB
                            update_sql = """
                                UPDATE yahoo_india_equity_price
                                SET delv_pct = data.delv_pct
                                FROM (VALUES %s) AS data(delv_pct, symbol_id, date)
                                WHERE yahoo_india_equity_price.symbol_id = data.symbol_id
                                  AND yahoo_india_equity_price.date = data.date
                                  AND timeframe='1d';
                            """
                            execute_values(cur, update_sql, updates, template=None, page_size=1000)
                            conn.commit()
                            log(f"    🔹 Updated {len(updates)} rows for {symbol_clean} {year}")

                        except Exception as e:
                            conn.rollback()
                            log(f"❌ Error processing {csv_file}: {e}")

        log("🔒 Database connection closed")

    except Exception as e:
        log(f"❌ Database operation failed: {e}")
        raise
# --------------------------------------------------------------------------