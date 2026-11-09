"""
SQLite Database Connection and Session Management for VAANI.
Enforces WAL mode, foreign keys, and integer paise math.
"""

import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from app.config import settings, BASE_DIR

raw_db_path = Path(settings.DB_PATH)
DB_FILE = raw_db_path if raw_db_path.is_absolute() else (BASE_DIR / raw_db_path)
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database with foreign keys and row factory."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=10.0)
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

def init_db():
    """Initialize database tables from schema.sql if needed."""
    with get_db() as conn:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        # Verify schema version
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM schema_version;")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("INSERT INTO schema_version (version) VALUES (1);")
