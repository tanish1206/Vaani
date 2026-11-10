"""
Database initialization and name normalization utilities for VAANI.
STRICT ZERO DEMO DATA POLICY:
No sample customers, transactions, prescriptions, or watchlists are ever seeded.
Fresh instances start completely empty.
"""

from app.db.session import get_db, init_db

def normalise_name_key(name: str) -> str:
    """
    Normalise customer name for fuzzy and exact matching:
    lowercase -> strip honorifics -> collapse repeats -> w->v, etc.
    """
    key = name.lower().strip()
    for honorific in ["ji", "bhai", "kaka", "mama", "sir", "madam"]:
        if key.endswith(" " + honorific) or key.endswith(honorific):
            key = key[: -len(honorific)].strip()
    
    # Character substitutions
    key = key.replace("w", "v").replace("ph", "f").replace("sh", "s")
    key = key.replace("ee", "i").replace("oo", "u")
    
    # Remove spaces and non-alphanumeric chars
    key = "".join(c for c in key if c.isalnum())
    return key

def seed_demo_data(force: bool = False):
    """
    Enforces clean production database schema initialization.
    STRICT ZERO DEMO DATA: Never seeds mock customers or transactions.
    """
    init_db()
    with get_db() as conn:
        cur = conn.cursor()
        # Ensure default system settings exist if empty
        default_settings = [
            ("language", "auto"),
            ("voice_id", "sia"),
            ("voice_hi", "sia"),
            ("voice_mr", "madhuri"),
            ("voice_en", "radhika"),
            ("theme", "light"),
        ]
        for k, v in default_settings:
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);",
                (k, v)
            )

def reset_demo_data():
    """
    Clear all transactional and user records to return to a completely empty state.
    Never inserts sample data.
    """
    init_db()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM reminders;")
        cur.execute("DELETE FROM medicines;")
        cur.execute("DELETE FROM prescriptions;")
        cur.execute("DELETE FROM ledger_entries;")
        cur.execute("DELETE FROM customers;")
        cur.execute("DELETE FROM watchlist;")
        cur.execute("DELETE FROM market_cache;")
        cur.execute("DELETE FROM pending_confirmations;")
        cur.execute("DELETE FROM utterances;")
    return {"status": "reset", "message": "Database cleared to completely empty state"}

if __name__ == "__main__":
    seed_demo_data()
