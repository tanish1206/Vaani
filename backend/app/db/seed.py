"""
Seed demo data for VAANI as specified in data-model.md §5.
"""

from datetime import datetime, timezone
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

def seed_demo_data():
    """Populate database with demo customers, seed ledger entries, and market watchlist."""
    init_db()
    
    with get_db() as conn:
        cur = conn.cursor()
        
        # Check if already seeded
        cur.execute("SELECT COUNT(*) FROM customers;")
        if cur.fetchone()[0] > 0:
            print("Database already contains customer records. Skipping seed.")
            return

        print("Seeding demo data into VAANI database...")
        now = datetime.now(timezone.utc).isoformat()

        # 0. Insert seed utterance record to satisfy foreign key
        cur.execute(
            """
            INSERT OR IGNORE INTO utterances (id, session_id, transcript, status, reply_text, created_at)
            VALUES ('seed', 'seed-session', 'Initial demo seed', 'ok', 'Database seeded', ?);
            """,
            (now,)
        )

        # 1. Seed Customers & Initial Balances
        seed_customers = [
            ("रमेश", "Ramesh", 65000),      # ₹650
            ("सुनीता", "Sunita", 15000),    # ₹150
            ("पाटील", "Patil", 120000),     # ₹1,200
            ("गणेश", "Ganesh", 40000),      # ₹400
            ("शिंदे", "Shinde", 30000),     # ₹300
        ]

        for name, name_roman, amount_paise in seed_customers:
            name_key = normalise_name_key(name_roman)
            cur.execute(
                """
                INSERT INTO customers (name, name_roman, name_key, phone, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (name, name_roman, name_key, None, now)
            )
            customer_id = cur.lastrowid
            
            # Insert initial credit entry tagged with 'seed'
            cur.execute(
                """
                INSERT INTO ledger_entries (customer_id, kind, amount_paise, note, utterance_id, created_at)
                VALUES (?, 'CREDIT', ?, 'Opening balance (seed)', 'seed', ?);
                """,
                (customer_id, amount_paise, now)
            )

        # 2. Seed Watchlist
        watchlist_items = [
            ("^BSESN", "Sensex", 1),
            ("^NSEI", "Nifty 50", 2),
            ("RELIANCE.NS", "Reliance", 3),
            ("TCS.NS", "TCS", 4),
            ("HDFCBANK.NS", "HDFC Bank", 5),
        ]
        for symbol, label, pos in watchlist_items:
            cur.execute(
                """
                INSERT OR IGNORE INTO watchlist (symbol, label, position)
                VALUES (?, ?, ?);
                """,
                (symbol, label, pos)
            )

        # 3. Seed Market Cache
        market_quotes = [
            ("^BSESN", 83410.20, 342.80, 0.43),
            ("^NSEI", 25480.60, 98.25, 0.39),
            ("RELIANCE.NS", 2980.50, 14.20, 0.48),
            ("TCS.NS", 4120.00, -12.50, -0.30),
            ("HDFCBANK.NS", 1640.80, 8.60, 0.53),
        ]
        for sym, price, chg_abs, chg_pct in market_quotes:
            cur.execute(
                """
                INSERT OR REPLACE INTO market_cache (symbol, price, change_abs, change_pct, as_of, source, is_sample)
                VALUES (?, ?, ?, ?, ?, 'sample', 1);
                """,
                (sym, price, chg_abs, chg_pct, now)
            )

        # 4. Seed Settings
        default_settings = [
            ("language", "auto"),
            ("voice_hi", "sia"),
            ("voice_mr", "sia"),
            ("voice_en", "sia"),
            ("theme", "light"),
        ]
        for k, v in default_settings:
            cur.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);",
                (k, v)
            )

        print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_demo_data()
