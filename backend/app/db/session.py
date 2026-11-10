"""
SQLite Database Connection and Session Management for VAANI.
Enforces WAL mode, foreign keys, and integer paise math.
"""

import os
import shutil
import sqlite3
from pathlib import Path
import tempfile
from typing import Generator
from contextlib import contextmanager

from app.config import settings, BASE_DIR

raw_db_path = Path(settings.DB_PATH)
if os.environ.get("VERCEL"):
    raw_db_path = Path(tempfile.gettempdir()) / "vaani.db"

DB_FILE = raw_db_path if raw_db_path.is_absolute() else (BASE_DIR / raw_db_path)
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database with foreign keys and row factory."""
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Copy bundled database to temp directory if running on Vercel and not present
    if os.environ.get("VERCEL") and not DB_FILE.exists():
        bundled_db = BASE_DIR / "data" / "vaani.db"
        if bundled_db.exists():
            try:
                shutil.copy2(str(bundled_db), str(DB_FILE))
            except Exception:
                pass

    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        conn.execute("PRAGMA journal_mode = DELETE;")
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
