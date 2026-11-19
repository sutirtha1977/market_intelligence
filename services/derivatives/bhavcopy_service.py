import requests
import zipfile
import io
import time
import random
import csv
from datetime import date, timedelta, datetime
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import json

from config.logger import log
from config.constants import FNO_BHAV_URL, FNO_BHAV_HEADERS
from config.paths import BHAVCOPY_FNO_HIST_DIR, BHAVCOPY_FNO_INCR_DIR, BHAVCOPY_FNO_OLD_DIR
from database.connection import get_db_connection_cm
from services.derivatives.route_service import route_staging_to_fno_tables

# --------------------------------------------------------------------------
BASE_SLEEP = 2.0
JITTER_MIN = 0.5
JITTER_MAX = 1.5
ROW_BATCH_SIZE = 10_000

# --------------------------------------------------------------------------
BHAVCOPY_FNO_HIST_DIR.mkdir(parents=True, exist_ok=True)
BHAVCOPY_FNO_INCR_DIR.mkdir(parents=True, exist_ok=True)
BHAVCOPY_FNO_OLD_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
def polite_sleep():
    """Sleep with jitter to avoid rate limits"""
    time.sleep(BASE_SLEEP + random.uniform(JITTER_MIN, JITTER_MAX))

# --------------------------------------------------------------------------
def clean_folder(folder: Path, name: str):
    log(f"🧹 Cleaning folder: {name} | {folder}")
    for f in folder.glob("*"):
        try:
            f.unlink()
            log(f"Deleted file: {f.name}")
        except Exception as e:
            log(f"❌ Failed deleting {f.name}: {e}")

# --------------------------------------------------------------------------
def parse_date(value: str | None):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%b-%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue
    return None

def has_valid_date(value: str | None) -> bool:
    return parse_date(value) is not None

def parse_float(v):
    try:
        return float(v) if v not in ("", None) else None
    except Exception:
        return None

def parse_int(v):
    try:
        return int(v) if v not in ("", None) else None
    except Exception:
        return None

# --------------------------------------------------------------------------
def resolve_bhavcopy_folder(folder_type: str) -> Path:
    mapping = {
        "historical": BHAVCOPY_FNO_HIST_DIR,
        "incremental": BHAVCOPY_FNO_INCR_DIR,
        "old": BHAVCOPY_FNO_OLD_DIR,
    }
    if folder_type not in mapping:
        raise ValueError(f"Invalid folder_type: {folder_type}")
    return mapping[folder_type]

# --------------------------------------------------------------------------
def download_bhavcopy(
    start_date: date | None = None,
    end_date: date | None = None,
    folder_type: str = "historical",
):
    """Download NSE F&O bhavcopy files with robust logging and fail-safe"""
    folder = resolve_bhavcopy_folder(folder_type)
    clean_folder(folder, folder_type)

    # ----------------------------------------------------------------------
    # Normalize dates
    # ----------------------------------------------------------------------
    if start_date is None:
        with get_db_connection_cm() as conn:
            df = pd.read_sql("SELECT MAX(trade_date) AS last_trade_date FROM fno_index_futures", conn)
            last_date = df.iloc[0]["last_trade_date"]
            start_date = last_date + timedelta(days=1) if pd.notna(last_date) else date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()

    log(f"📅 Download range: {start_date} → {end_date} | folder: {folder_type}")
    
    curr: date = start_date # type: ignore
    session = requests.Session()
    downloaded = skipped = failed = 0

    # ----------------------------------------------------------------------
    # Loop per date
    # ----------------------------------------------------------------------
    while curr <= end_date:
        try:
            if folder_type == "old":

                url = (
                    "https://www.nseindia.com/api/reports?"
                    "archives=%5B%7B%22name%22%3A%22F%26O%20-%20Bhavcopy(csv)%22%2C"
                    "%22type%22%3A%22archives%22%2C"
                    "%22category%22%3A%22derivatives%22%2C"
                    "%22section%22%3A%22equity%22%7D%5D"
                    f"&date={curr.strftime('%d-%b-%Y')}&type=equity&mode=single"
                )

                log(f"🔗 Downloading (old) URL: {url}")

                r = session.get(url, headers=FNO_BHAV_HEADERS, timeout=30)

                if r.status_code == 200 and r.content:
                    out = folder / f"BhavCopy_FNO_{curr}.csv"
                    out.write_bytes(r.content)
                    downloaded += 1
                    log(f"✅ Downloaded (old) {curr}")
                else:
                    skipped += 1
                    log(f"⚠️ Skipped {curr} (status={r.status_code}, bytes={len(r.content)})")
            else:
                url = FNO_BHAV_URL.format(yyyymmdd=curr.strftime("%Y%m%d"))
                log(f"🔗 Downloading URL: {url}")
                r = session.get(url, headers=FNO_BHAV_HEADERS, timeout=30)
                if r.status_code == 200 and r.content.startswith(b"PK"):
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        z.extractall(folder)
                    downloaded += 1
                    log(f"✅ Downloaded {curr}")
                else:
                    skipped += 1
                    log(f"⚠️ Skipped {curr} (status={r.status_code}, bytes={len(r.content)})")
        except Exception as e:
            failed += 1
            log(f"❌ Failed download {curr} | {e}")
        polite_sleep()
        curr += timedelta(days=1)

    log(f"📥 Download summary | downloaded={downloaded} skipped={skipped} failed={failed}")

# --------------------------------------------------------------------------
def parse_and_upload_bhavcopies(bhavcopy_dir: Path):
    """Parse CSVs and upload to staging table with robust error handling"""
    is_old = bhavcopy_dir == BHAVCOPY_FNO_OLD_DIR
    pattern = "BhavCopy_FNO_*.csv" if is_old else "BhavCopy_NSE_FO_*.csv"
    files = sorted(bhavcopy_dir.glob(pattern))

    OLD_TO_CANONICAL = {
        "FUTIDX": "IDF",
        "OPTIDX": "IDO",
        "FUTSTK": "STF",
        "OPTSTK": "STO",
    }

    total_rows = skipped_rows = failed_files = 0

    with get_db_connection_cm() as conn:
        log("🧹 Clearing fno_bhavcopy_staging table...")
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE fno_bhavcopy_staging;")

        for file in tqdm(files, desc="Uploading bhavcopies"):
            try:
                buffer = []
                encoding = "cp1252" if is_old else "utf-8"
                
                # with open(file, encoding="utf-8") as f:
                with open(file, mode="r", encoding=encoding, errors="replace") as f:
                    reader = csv.DictReader(f)
                    # reader.fieldnames = [h.strip().lstrip("\ufeff") for h in reader.fieldnames]
                    if reader.fieldnames is None:
                        raise ValueError("CSV file has no header row")

                    reader.fieldnames = [h.strip().lstrip("\ufeff") for h in reader.fieldnames]

                    for r in reader:
                        if is_old:
                            if not has_valid_date(r.get("RptgDt")) or not has_valid_date(r.get("XpryDt")):
                                skipped_rows += 1
                                continue
                        else:
                            if not has_valid_date(r.get("TradDt")) or not has_valid_date(r.get("XpryDt")):
                                skipped_rows += 1
                                continue

                        # ------------------------------------------------------------------
                        # Map row
                        # ------------------------------------------------------------------
                        try:
                            if is_old:
                                # instr = OLD_TO_CANONICAL.get(r.get("FinInstrmNm"))
                                key = r.get("FinInstrmNm")

                                if key is not None:
                                    instr = OLD_TO_CANONICAL.get(key)
                                else:
                                    instr = None
                                if not instr:
                                    skipped_rows += 1
                                    continue
                                row = {
                                    "trade_date": parse_date(r.get("RptgDt")),
                                    "instrument_type": instr,
                                    "symbol": r.get("TckrSymb"),
                                    "expiry_date": parse_date(r.get("XpryDt")),
                                    "actual_expiry_date": None,
                                    "strike_price": parse_float(r.get("StrkPric")),
                                    "option_type": r.get("OptnTp"),
                                    "open_price": parse_float(r.get("OpnPric")),
                                    "high_price": parse_float(r.get("HghPric")),
                                    "low_price": parse_float(r.get("LwPric")),
                                    "close_price": parse_float(r.get("ClsPric")),
                                    "last_price": parse_float(r.get("ClsPric")),
                                    "prev_close_price": parse_float(r.get("PrvsClsgPric")),
                                    "underlying_price": 0.0,
                                    "settlement_price": parse_float(r.get("SttlmPric")),
                                    "open_interest": parse_int(r.get("OpnIntrst")),
                                    "change_in_oi": parse_int(r.get("ChngInOpnIntrst")),
                                    "traded_volume": parse_int(r.get("TtlTradgVol")),
                                    "lot_size": 0,
                                }
                            else:
                                row = {
                                    "trade_date": parse_date(r.get("TradDt")),
                                    "instrument_type": r.get("FinInstrmTp"),
                                    "symbol": r.get("TckrSymb"),
                                    "expiry_date": parse_date(r.get("XpryDt")),
                                    "actual_expiry_date": parse_date(r.get("FininstrmActlXpryDt")),
                                    "strike_price": parse_float(r.get("StrkPric")),
                                    "option_type": r.get("OptnTp"),
                                    "open_price": parse_float(r.get("OpnPric")),
                                    "high_price": parse_float(r.get("HghPric")),
                                    "low_price": parse_float(r.get("LwPric")),
                                    "close_price": parse_float(r.get("ClsPric")),
                                    "last_price": parse_float(r.get("LastPric")),
                                    "prev_close_price": parse_float(r.get("PrvsClsgPric")),
                                    "underlying_price": parse_float(r.get("UndrlygPric")),
                                    "settlement_price": parse_float(r.get("SttlmPric")),
                                    "open_interest": parse_int(r.get("OpnIntrst")),
                                    "change_in_oi": parse_int(r.get("ChngInOpnIntrst")),
                                    "traded_volume": parse_int(r.get("TtlTradgVol")),
                                    "lot_size": parse_int(r.get("NewBrdLotQty")),
                                }
                        except Exception as e:
                            skipped_rows += 1
                            log(f"⚠️ Skipped row due to parsing error: {e}")
                            continue

                        buffer.append(row)

                        if len(buffer) >= ROW_BATCH_SIZE:
                            cols = list(buffer[0].keys())
                            placeholders = ", ".join([f"%({c})s" for c in cols])
                            sql = f"INSERT INTO fno_bhavcopy_staging ({','.join(cols)}) VALUES ({placeholders})"
                            with conn.cursor() as cur:
                                cur.executemany(sql, buffer)
                            total_rows += len(buffer)
                            buffer.clear()

                # Insert remaining rows
                if buffer:
                    cols = list(buffer[0].keys())
                    placeholders = ", ".join([f"%({c})s" for c in cols])
                    sql = f"INSERT INTO fno_bhavcopy_staging ({','.join(cols)}) VALUES ({placeholders})"
                    with conn.cursor() as cur:
                        cur.executemany(sql, buffer)
                    total_rows += len(buffer)

            except Exception as e:
                failed_files += 1
                log(f"❌ Failed file {file.name}: {e}")

    log(f"✅ Upload summary | files={len(files)} rows={total_rows} skipped={skipped_rows} failed_files={failed_files}")

# --------------------------------------------------------------------------
def download_and_load_bhavcopies(
    start_date: date | None = None,
    end_date: date | None = None,
    folder_type: str = "historical",
):
    """Full pipeline: download, parse, upload, route, cleanup"""
    log("🚀 NSE F&O bhavcopy pipeline started")
    
    log("🚀 Download bhavcopy started...")
    download_bhavcopy(start_date, end_date, folder_type)
    log("🚀 Download bhavcopy finished...")

    log("🚀 Upsert in database started...")
    parse_and_upload_bhavcopies(resolve_bhavcopy_folder(folder_type))
    
    route_staging_to_fno_tables()
    log("🚀 Upsert in database finished...")

    clean_folder(resolve_bhavcopy_folder(folder_type), folder_type)
    log("🏁 Pipeline finished")