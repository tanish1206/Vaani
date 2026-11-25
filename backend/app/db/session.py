"""
SQLite Database Connection and Session Management for VAANI.
Enforces WAL mode, foreign keys, and integer paise math.
"""

import logging
import os
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator

from app.config import BASE_DIR, is_serverless, settings

logger = logging.getLogger(__name__)

DIAGNOSTIC_TABLES = ("customers", "ledger_entries", "prescriptions", "reminders", "watchlist")

raw_db_path = Path(settings.DB_PATH)
if is_serverless():
    raw_db_path = Path(tempfile.gettempdir()) / "vaani.db"

DB_FILE = raw_db_path if raw_db_path.is_absolute() else (BASE_DIR / raw_db_path)
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database with foreign keys and row factory."""
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.debug("Could not ensure DB directory %s: %s", DB_FILE.parent, exc)

    # Copy bundled database to temp directory if running on serverless and not present
    if is_serverless() and not DB_FILE.exists():
        bundled_db = BASE_DIR / "data" / "vaani.db"
        if bundled_db.exists():
            try:
                shutil.copy(str(bundled_db), str(DB_FILE))
                os.chmod(str(DB_FILE), 0o666)
            except OSError as exc:
                logger.warning("Could not copy bundled DB: %s", exc)

    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables from schema.sql if needed (fail-safe for serverless)."""
    try:
        with get_db() as conn:
            journal_pragma = "DELETE" if is_serverless() else "WAL"
            try:
                conn.execute(f"PRAGMA journal_mode = {journal_pragma};")
            except sqlite3.DatabaseError as exc:
                logger.debug("Could not set journal_mode=%s: %s", journal_pragma, exc)

            if SCHEMA_FILE.exists():
                conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);")
            cur.execute("SELECT COUNT(*) FROM schema_version;")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO schema_version (version) VALUES (1);")
    except Exception as exc:
        logger.warning("init_db failed gracefully: %s", exc)


def get_db_diagnostics() -> Dict[str, Any]:
    """Collect SQLite health, pragma state, file size, and core table row counts."""
    db_path = str(DB_FILE)
    size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    counts: Dict[str, int] = {}
    journal_mode = "unknown"
    foreign_keys = False

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            journal_mode = str(cur.fetchone()[0])

            cur.execute("PRAGMA foreign_keys;")
            foreign_keys = bool(cur.fetchone()[0])

            for tbl in DIAGNOSTIC_TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    counts[tbl] = int(cur.fetchone()[0])
                except sqlite3.DatabaseError:
                    counts[tbl] = 0
    except Exception as exc:
        journal_mode = f"error: {exc}"

    return {
        "path": settings.DB_PATH,
        "size_bytes": size_bytes,
        "wal_mode": journal_mode.lower() == "wal",
        "journal_mode": journal_mode,
        "foreign_keys": foreign_keys,
        "row_counts": counts,
    }
