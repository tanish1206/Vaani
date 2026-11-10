"""
Database cleanup script: removes all seeded demo records from data/vaani.db.
Preserves schema, migrations, and user settings.
"""

import sqlite3
from pathlib import Path

db_path = Path("Vaani/data/vaani.db")
if not db_path.exists():
    db_path = Path("data/vaani.db")

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print("Beginning purge of seeded demo records...")

# Delete seeded demo records
cur.execute("DELETE FROM reminders WHERE id IN (SELECT r.id FROM reminders r JOIN medicines m ON r.medicine_id = m.id JOIN prescriptions p ON m.prescription_id = p.id WHERE p.utterance_id = 'seed' OR p.patient_label LIKE '%Dadi Ji%');")
cur.execute("DELETE FROM medicines WHERE prescription_id IN (SELECT id FROM prescriptions WHERE utterance_id = 'seed' OR patient_label LIKE '%Dadi Ji%');")
cur.execute("DELETE FROM prescriptions WHERE utterance_id = 'seed' OR patient_label LIKE '%Dadi Ji%';")

cur.execute("DELETE FROM ledger_entries WHERE utterance_id = 'seed' OR note LIKE '%(seed)%';")
cur.execute("DELETE FROM customers WHERE name_roman IN ('Ramesh', 'Sunita', 'Patil', 'Ganesh', 'Shinde');")

cur.execute("DELETE FROM watchlist WHERE symbol IN ('^BSESN', '^NSEI', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS');")
cur.execute("DELETE FROM market_cache WHERE is_sample = 1 OR source = 'sample';")

cur.execute("DELETE FROM utterances WHERE id = 'seed' OR session_id = 'seed-session' OR transcript LIKE '%Initial demo seed%';")

# Also delete any other test-leftover utterances
cur.execute("DELETE FROM utterances WHERE session_id IN ('agent-parchi', 'landing-demo', 'test-session');")
cur.execute("DELETE FROM ledger_entries WHERE utterance_id NOT IN (SELECT id FROM utterances);")

conn.commit()

print("Purge completed. Current table counts:")
tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    if t != "sqlite_sequence":
        count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count}")

conn.close()
