
# config/logger.py

import logging
import logging.handlers
import sys
from pathlib import Path
from config.paths import DATA_DIR

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

LOGS_DIR = Path(DATA_DIR).parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "app.log"

LOG_LEVEL = logging.INFO

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

LOGGER_NAME = "stock_market"


# ---------------------------------------------------------
# LOGGER INITIALIZATION
# ---------------------------------------------------------

def _initialize_logger():

    logger = logging.getLogger(LOGGER_NAME)

    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Detailed formatter
    detailed_formatter = logging.Formatter(
        fmt=(
            "[%(asctime)s] "
            "[%(levelname)-8s] "
            "[%(name)s:%(lineno)d] "
            "[%(process)d:%(thread)d] "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console formatter
    console_formatter = logging.Formatter(
        "[%(levelname)-8s] %(message)s"
    )

    # -----------------------------------------------------
    # CONSOLE HANDLER
    # -----------------------------------------------------

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(console_formatter)

    # -----------------------------------------------------
    # FILE HANDLER
    # -----------------------------------------------------

    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )

    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(detailed_formatter)

    # -----------------------------------------------------
    # REGISTER HANDLERS
    # -----------------------------------------------------

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


_logger = _initialize_logger()


# ---------------------------------------------------------
# PUBLIC LOGGING FUNCTIONS
# ---------------------------------------------------------

def log(message: str, level: str = "info"):

    log_func = getattr(_logger, level.lower(), None)

    if not callable(log_func):
        log_func = _logger.info

    log_func(message)


def log_debug(message: str):
    _logger.debug(message)


def log_info(message: str):
    _logger.info(message)


def log_warning(message: str):
    _logger.warning(message)


def log_error(message: str):
    _logger.error(message)


def log_exception(message: str):
    _logger.exception(message)


def log_critical(message: str):
    _logger.critical(message)


# ---------------------------------------------------------
# LOG FILE MANAGEMENT
# ---------------------------------------------------------

def clear_log():

    try:
        for handler in _logger.handlers:
            if isinstance(
                handler,
                logging.handlers.RotatingFileHandler
            ):
                handler.acquire()
                try:
                    handler.flush()
                    handler.close()
                    handler.stream = handler._open()
                finally:
                    handler.release()

        if LOG_FILE.exists():
            LOG_FILE.write_text("", encoding="utf-8")

    except Exception as e:
        print(
            f"[LOG CLEAR ERROR] {e}",
            file=sys.stderr
        )
