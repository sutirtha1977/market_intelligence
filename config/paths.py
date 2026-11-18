# config/paths.py

from pathlib import Path

# ---------------- BASE Directory ----------------
BASE_DIR: Path = Path(__file__).parent.parent

# ---------------- Directories ----------------
DATA_DIR: Path = BASE_DIR / "data"

# ---------------- NSE Holiday Lists ----------------
NSE_HOLIDAYS: Path = DATA_DIR / "nse_holiday_lists.csv"
SYMBOLS_MASTER: Path = DATA_DIR / "symbols_master.xlsx"

# ---------------- Symbols Directories ----------------
NSE_DIR: Path = DATA_DIR / "nse"

# ---------------- Equity Bhavcopy Directories ----------------
BHAVCOPY_EQ_DIR: Path = DATA_DIR / "equity_bhavcopy"
BHAVCOPY_EQ_HIST_DIR: Path = BHAVCOPY_EQ_DIR / "historical"
BHAVCOPY_EQ_DAILY_DIR: Path = BHAVCOPY_EQ_DIR / "daily"

# ---------------- FNO Bhavcopy Directories ----------------
BHAVCOPY_FNO_DIR: Path = DATA_DIR / "fno_bhavcopy"
BHAVCOPY_FNO_HIST_DIR: Path = BHAVCOPY_FNO_DIR / "historical"
BHAVCOPY_FNO_INCR_DIR: Path = BHAVCOPY_FNO_DIR / "incremental"
BHAVCOPY_FNO_OLD_DIR: Path = BHAVCOPY_FNO_DIR / "old"

# ---------------- Scanner Directories ----------------
SCANNER_DIR: Path = DATA_DIR / "scanner_results"

# ---------------- Logging ----------------
LOG_FILE: Path = BASE_DIR / "audit_trail.log"

# ---------------- Helper Function ----------------
def ensure_folder(path: Path) -> None:
    """Ensure the folder exists."""
    path.mkdir(parents=True, exist_ok=True)

# ---------------- Ensure folder exists ----------------
FOLDERS_TO_ENSURE = [
    # Base
    DATA_DIR,
    
    #NSE   
    NSE_DIR,

    # Equity Bhavcopy
    BHAVCOPY_EQ_DIR,
    BHAVCOPY_EQ_HIST_DIR,
    BHAVCOPY_EQ_DAILY_DIR,

    # FNO Bhavcopy
    BHAVCOPY_FNO_DIR,
    BHAVCOPY_FNO_HIST_DIR,
    BHAVCOPY_FNO_INCR_DIR,
    BHAVCOPY_FNO_OLD_DIR,

    # Scanner
    SCANNER_DIR,
]

for folder in FOLDERS_TO_ENSURE:
    ensure_folder(folder)