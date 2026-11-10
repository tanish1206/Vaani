import sqlite3
from pathlib import Path

db_path = Path("Vaani/data/vaani.db")
if not db_path.exists():
    db_path = Path("data/vaani.db")

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables and counts:")
for t in tables:
    if t != "sqlite_sequence":
        count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count}")

print("\nUtterances sample:")
for row in cur.execute("SELECT id, session_id, transcript, reply_text, created_at FROM utterances LIMIT 5").fetchall():
    print(" ", row)

print("\nCustomers sample:")
for row in cur.execute("SELECT id, name, name_roman, created_at FROM customers LIMIT 5").fetchall():
    print(" ", row)

print("\nPrescriptions sample:")
for row in cur.execute("SELECT id, patient_label, created_at FROM prescriptions LIMIT 5").fetchall():
    print(" ", row)

print("\nSettings:")
for row in cur.execute("SELECT key, value FROM settings").fetchall():
    print(" ", row)

