
# database/connection.py

import threading
from contextlib import contextmanager
from typing import Optional, Generator

from psycopg2 import pool
from psycopg2.extensions import (
    connection,
    TRANSACTION_STATUS_IDLE,
)

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL

from config.logger import log, log_exception
from config.db_config import DB_CONFIG


# =========================================================
# CONFIGURATION
# =========================================================

DB_HOST = DB_CONFIG["host"]
DB_NAME = DB_CONFIG["dbname"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]
DB_PORT = DB_CONFIG.get("port", 5432)

CONNECT_TIMEOUT = 15
STATEMENT_TIMEOUT = 300000  # 5 minutes, milliseconds

# psycopg2 write pool
WRITE_POOL_MIN = 2
WRITE_POOL_MAX = 10

# SQLAlchemy read pool
READ_POOL_SIZE = 5
READ_MAX_OVERFLOW = 5
READ_POOL_TIMEOUT = 30
READ_POOL_RECYCLE = 1800

APPLICATION_NAME = "stock_market_app"


# =========================================================
# GLOBAL OBJECTS
# =========================================================

_ENGINE: Optional[Engine] = None

_CONNECTION_POOL: Optional[pool.ThreadedConnectionPool] = None

_ENGINE_LOCK = threading.Lock()
_POOL_LOCK = threading.Lock()


# =========================================================
# DATABASE CONNECTION PARAMETERS
# =========================================================

def _get_connection_params():

    return {
        "host": DB_HOST,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
        "connect_timeout": CONNECT_TIMEOUT,
        "application_name": APPLICATION_NAME,
        "options": f"-c statement_timeout={STATEMENT_TIMEOUT}",
    }


# =========================================================
# SQLALCHEMY ENGINE (READ / PANDAS)
# =========================================================

def get_engine() -> Engine:

    global _ENGINE

    if _ENGINE is not None:
        return _ENGINE

    with _ENGINE_LOCK:

        if _ENGINE is None:

            try:

                database_url = URL.create(
                    drivername="postgresql+psycopg2",
                    username=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                )

                _ENGINE = create_engine(
                    database_url,
                    pool_size=READ_POOL_SIZE,
                    max_overflow=READ_MAX_OVERFLOW,
                    pool_timeout=READ_POOL_TIMEOUT,
                    pool_recycle=READ_POOL_RECYCLE,
                    pool_pre_ping=True,
                    connect_args={
                        "connect_timeout": CONNECT_TIMEOUT,
                        "application_name": APPLICATION_NAME,
                        "options": (
                            f"-c statement_timeout={STATEMENT_TIMEOUT}"
                        ),
                    },
                )

                log("SQLAlchemy database engine initialized")

            except Exception:
                log_exception("SQLAlchemy engine initialization failed")
                raise

    return _ENGINE


# =========================================================
# PSYCOPG2 THREAD-SAFE CONNECTION POOL (WRITE)
# =========================================================

def get_connection_pool():

    global _CONNECTION_POOL

    if _CONNECTION_POOL is not None:
        return _CONNECTION_POOL

    with _POOL_LOCK:

        if _CONNECTION_POOL is None:

            try:

                _CONNECTION_POOL = pool.ThreadedConnectionPool(
                    minconn=WRITE_POOL_MIN,
                    maxconn=WRITE_POOL_MAX,
                    **_get_connection_params()
                )

                log(
                    f"PostgreSQL connection pool initialized "
                    f"({WRITE_POOL_MIN}-{WRITE_POOL_MAX})"
                )

            except Exception:
                log_exception(
                    "PostgreSQL connection pool initialization failed"
                )
                raise

    return _CONNECTION_POOL


# =========================================================
# CONNECTION VALIDATION
# =========================================================

def validate_connection(conn: Optional[connection]) -> None:

    if conn is None:
        raise RuntimeError("Database connection is None")

    if conn.closed:
        raise RuntimeError("Database connection is closed")

    if conn.get_transaction_status() == 3:
        raise RuntimeError("Database connection is in failed transaction state")


# =========================================================
# GET CONNECTION (WRITE)
# =========================================================

def get_db_connection() -> connection:

    conn = None
    connection_pool = get_connection_pool()

    try:

        conn = connection_pool.getconn()

        validate_connection(conn)

        # Recover any unfinished transaction left by
        # previous code using the connection.
        if conn.get_transaction_status() != TRANSACTION_STATUS_IDLE:
            conn.rollback()

        return conn

    except Exception:

        if conn is not None:

            try:
                connection_pool.putconn(conn, close=True)
            except Exception:
                pass

        log_exception("Failed to acquire PostgreSQL connection")
        raise


# =========================================================
# RETURN CONNECTION TO POOL
# =========================================================

def close_db_connection(
    conn: Optional[connection],
    discard: bool = False
) -> None:

    if conn is None:
        return

    try:

        connection_pool = get_connection_pool()

        # Never return an unfinished transaction
        # to the shared pool.
        if not conn.closed:
            conn.rollback()

        connection_pool.putconn(
            conn,
            close=(discard or bool(conn.closed))
        )

    except Exception:

        log_exception("Failed to return PostgreSQL connection")

        # Attempt to discard an unhealthy connection.
        try:
            if not conn.closed:
                conn.close()
        except Exception:
            pass


# =========================================================
# CONTEXT MANAGER (TRANSACTION SAFE)
# =========================================================

@contextmanager
def get_db_connection_cm() -> Generator[connection, None, None]:

    conn = get_db_connection()

    try:

        yield conn

        conn.commit()

    except Exception:

        try:
            if not conn.closed:
                conn.rollback()
        except Exception:
            log_exception("PostgreSQL transaction rollback failed")

        raise

    finally:

        close_db_connection(conn)
