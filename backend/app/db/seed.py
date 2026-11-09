"""
Seed data manager for VAANI.
Enforces strict separation between DEMO fixtures and clean PRODUCTION mode.
"""

from datetime import datetime, timezone
from app.config import settings
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
    Populate database with demo customers and sample data ONLY if DEMO_MODE is true.
    In Production (DEMO_MODE=false), ensures schema exists without mock records.
    """
    init_db()
    
    # If production mode and not forced, do not insert demo fixtures
    if not settings.DEMO_MODE and not force:
        print("[Database] Running in PRODUCTION mode: clean database initialized, skipping demo fixtures.")
        return

    with get_db() as conn:
        cur = conn.cursor()
        
        # Check if already seeded
        cur.execute("SELECT COUNT(*) FROM customers;")
        if cur.fetchone()[0] > 0 and not force:
            print("[Database] Customers already exist. Skipping seed.")
            return

        print("[Database] Seeding demo data (DEMO_MODE=true)...")
        now = datetime.now(timezone.utc).isoformat()

        # 0. Insert seed utterance record to satisfy foreign key
        cur.execute(
            """
            INSERT OR IGNORE INTO utterances (id, session_id, transcript, status, reply_text, created_at)
            VALUES ('seed', 'seed-session', 'Initial demo seed', 'ok', 'Database seeded', ?);
            """,
            (now,)
        )

        # 1. Seed Demo Customers & Opening Balances (Tagged with 'seed')
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
            
            cur.execute(
                """
                INSERT INTO ledger_entries (customer_id, kind, amount_paise, note, utterance_id, created_at)
                VALUES (?, 'CREDIT', ?, 'Opening balance (seed)', 'seed', ?);
                """,
                (customer_id, amount_paise, now)
            )

        # 2. Seed Default Watchlist
        watchlist_items = [
            ("^BSESN", "BSE Sensex", 1),
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

        # 3. Seed Market Cache (Explicitly Tagged is_sample=1 and source='sample')
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

        # 4. Seed Demo Prescriptions & Reminders if empty
        cur.execute("SELECT COUNT(*) FROM prescriptions;")
        if cur.fetchone()[0] == 0:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            cur.execute(
                """
                INSERT INTO prescriptions (patient_label, doctor_note, start_date, duration_days, status, utterance_id, created_at)
                VALUES ('दादी जी (Dadi Ji)', 'Dr. Sharma - General Checkup', ?, 5, 'active', 'seed', ?);
                """,
                (today_str, now)
            )
            presc_id = cur.lastrowid
            
            # Medicine 1: Amlodipine 5mg
            cur.execute(
                """
                INSERT INTO medicines (prescription_id, name, dose_text, with_food, times_json)
                VALUES (?, 'Amlodipine 5mg', '1 goli naashte ke baad', 'after', '["morning"]');
                """,
                (presc_id,)
            )
            m1_id = cur.lastrowid
            
            # Medicine 2: Multivitamin
            cur.execute(
                """
                INSERT INTO medicines (prescription_id, name, dose_text, with_food, times_json)
                VALUES (?, 'Multivitamin', '1 capsule dopahar khaane ke baad', 'after', '["afternoon"]');
                """,
                (presc_id,)
            )
            m2_id = cur.lastrowid
            
            # Medicine 3: Calcium + D3
            cur.execute(
                """
                INSERT INTO medicines (prescription_id, name, dose_text, with_food, times_json)
                VALUES (?, 'Calcium + D3', '1 tablet raat ko doodh ke saath', 'after', '["night"]');
                """,
                (presc_id,)
            )
            m3_id = cur.lastrowid
            
            # Reminders for today
            cur.execute("INSERT INTO reminders (medicine_id, due_at, status) VALUES (?, ?, 'pending');", (m1_id, f"{today_str}T08:00:00Z"))
            cur.execute("INSERT INTO reminders (medicine_id, due_at, status) VALUES (?, ?, 'pending');", (m2_id, f"{today_str}T13:30:00Z"))
            cur.execute("INSERT INTO reminders (medicine_id, due_at, status) VALUES (?, ?, 'pending');", (m3_id, f"{today_str}T21:30:00Z"))

        # 5. Seed Settings
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

        print("[Database] Demo seeding completed successfully.")

def reset_demo_data():
    """Clear all transactional records and reseed demo data."""
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
        cur.execute("DELETE FROM utterances;")
    seed_demo_data(force=True)
    return {"status": "reset", "message": "Demo data has been reset to defaults"}

if __name__ == "__main__":
    seed_demo_data()
