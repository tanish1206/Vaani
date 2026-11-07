-- VAANI Database Schema (SQLite)
-- Schema version: 1
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

-- Every voice or text turn, kept for debugging, idempotency, audit trail
CREATE TABLE IF NOT EXISTS utterances (
    id                TEXT PRIMARY KEY,          -- turn_id (UUID)
    session_id        TEXT NOT NULL,
    transcript        TEXT,
    detected_language TEXT,                      -- hi | mr | en | hinglish
    parser            TEXT,                      -- evon | rules
    llm_json          TEXT,                      -- validated JSON from Evon
    status            TEXT NOT NULL,             -- ok | clarify | error
    error_code        TEXT,
    reply_text        TEXT,
    timings_json      TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,                   -- as spoken / transcribed (Devanagari or Latin)
    name_roman  TEXT NOT NULL,                   -- Latin form from Evon, e.g. "Ramesh"
    name_key    TEXT NOT NULL UNIQUE,            -- normalised key for fuzzy matching
    phone       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_customers_key ON customers(name_key);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id        INTEGER NOT NULL REFERENCES customers(id),
    kind               TEXT NOT NULL CHECK (kind IN ('CREDIT','PAYMENT')),
    amount_paise       INTEGER NOT NULL CHECK (amount_paise > 0),
    note               TEXT,
    utterance_id       TEXT REFERENCES utterances(id),
    corrects_entry_id  INTEGER REFERENCES ledger_entries(id),
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    voided_at          TEXT,
    voided_by          TEXT                        -- utterance id or 'ui'
);
CREATE INDEX IF NOT EXISTS idx_entries_customer ON ledger_entries(customer_id, created_at);

-- Balance = credit given - payments received, ignoring voided entries
CREATE VIEW IF NOT EXISTS customer_balances AS
SELECT 
    c.id AS customer_id, 
    c.name, 
    c.name_roman,
    COALESCE(SUM(CASE WHEN e.kind = 'CREDIT'  AND e.voided_at IS NULL THEN e.amount_paise END), 0)
    - COALESCE(SUM(CASE WHEN e.kind = 'PAYMENT' AND e.voided_at IS NULL THEN e.amount_paise END), 0)
    AS balance_paise
FROM customers c 
LEFT JOIN ledger_entries e ON e.customer_id = c.id
GROUP BY c.id;

CREATE TABLE IF NOT EXISTS prescriptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_label TEXT NOT NULL,                  -- "Maa", "Papa", "Aarav"
    doctor_note   TEXT,
    start_date    TEXT NOT NULL,                  -- local date, YYYY-MM-DD
    duration_days INTEGER,
    status        TEXT NOT NULL DEFAULT 'active', -- active | cancelled | completed
    utterance_id  TEXT REFERENCES utterances(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS medicines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,                -- as the user said it (verbatim)
    dose_text       TEXT,                         -- verbatim; never interpreted or altered
    with_food       TEXT CHECK (with_food IN ('before','after','with') OR with_food IS NULL),
    times_json      TEXT NOT NULL                 -- JSON array e.g. ["morning","evening"]
);

CREATE TABLE IF NOT EXISTS reminders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id    INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    due_at         TEXT NOT NULL,                 -- UTC ISO string
    status         TEXT NOT NULL DEFAULT 'pending', -- pending | done | snoozed | missed
    snoozed_until  TEXT,
    done_at        TEXT
);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(status, due_at);

CREATE TABLE IF NOT EXISTS watchlist (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol   TEXT NOT NULL UNIQUE,                -- e.g. ^BSESN, RELIANCE.NS
    label    TEXT NOT NULL,                       -- "Sensex", "Reliance"
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS market_cache (
    symbol      TEXT PRIMARY KEY,
    price       REAL NOT NULL,
    change_abs  REAL,
    change_pct  REAL,
    as_of       TEXT NOT NULL,                    -- UTC
    source      TEXT NOT NULL,                    -- live | cache | sample
    is_sample   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pending_confirmations (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    expires_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY, 
    value TEXT NOT NULL
);
