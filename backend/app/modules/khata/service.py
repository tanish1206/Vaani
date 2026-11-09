"""
Bol-Khata (Business Ledger) Service Layer.
Handles Customer Management, Transactions, Balances, Daily Summaries, and Undo.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import sqlite3

from app.db.session import get_db
from app.db.seed import normalise_name_key
from app.core.i18n import to_paise, format_rupees, render_template
from app.core.session import session_manager

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

def find_or_create_customer(conn: sqlite3.Connection, name: str, name_roman: Optional[str] = None) -> Tuple[int, str, bool]:
    """
    Find existing customer by exact or fuzzy matching, or create a new one.
    Returns: (customer_id, display_name, is_new_customer)
    """
    cur = conn.cursor()
    roman = name_roman or name
    key = normalise_name_key(roman)

    # 1. Exact match on normalised key
    cur.execute("SELECT id, name, name_roman FROM customers WHERE name_key = ?;", (key,))
    row = cur.fetchone()
    if row:
        return row["id"], row["name"], False

    # 2. Fuzzy match across all customers if rapidfuzz is available
    cur.execute("SELECT id, name, name_roman, name_key FROM customers;")
    all_customers = cur.fetchall()
    
    best_match = None
    best_score = 0

    for c in all_customers:
        score_key = fuzz.ratio(key, c["name_key"]) if HAS_RAPIDFUZZ else (100 if key in c["name_key"] else 0)
        score_roman = fuzz.ratio(roman.lower(), c["name_roman"].lower()) if HAS_RAPIDFUZZ else 0
        score = max(score_key, score_roman)
        if score > best_score:
            best_score = score
            best_match = c

    if best_match and best_score >= 85:
        return best_match["id"], best_match["name"], False

    # 3. Create new customer
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        """
        INSERT INTO customers (name, name_roman, name_key, phone, created_at)
        VALUES (?, ?, ?, NULL, ?);
        """,
        (name, roman, key, now)
    )
    new_id = cur.lastrowid
    return new_id, name, True

class KhataService:
    @staticmethod
    def add_credit(customer_name: str, amount: float, note: Optional[str] = None,
                   utterance_id: Optional[str] = None, session_id: str = "default",
                   lang: str = "hinglish") -> Dict[str, Any]:
        """Record credit given to a customer."""
        amount_paise = to_paise(amount)
        now = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            cur = conn.cursor()
            cust_id, display_name, is_new = find_or_create_customer(conn, customer_name)
            
            cur.execute(
                """
                INSERT INTO ledger_entries (customer_id, kind, amount_paise, note, utterance_id, created_at)
                VALUES (?, 'CREDIT', ?, ?, ?, ?);
                """,
                (cust_id, amount_paise, note, utterance_id, now)
            )
            entry_id = cur.lastrowid

            # Fetch updated balance
            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            new_balance_paise = cur.fetchone()["balance_paise"]

        # Update session
        session = session_manager.get_or_create(session_id)
        session.set_last_customer(cust_id, display_name)
        session.record_turn_entries([entry_id], [{"tool": "add_credit", "entry_id": entry_id}])

        reply = render_template(
            "add_credit",
            lang=lang,
            customer_name=display_name,
            amount=format_rupees(amount_paise),
            new_balance=format_rupees(new_balance_paise)
        )
        if is_new:
            prefix = "Naya khaata banaya: " if lang == "hinglish" else "नया खाता बनाया: "
            reply = f"{prefix}{display_name}। {reply}"

        return {
            "customer_id": cust_id,
            "customer_name": display_name,
            "amount_paise": amount_paise,
            "balance_paise": new_balance_paise,
            "entry_id": entry_id,
            "reply_text": reply
        }

    @staticmethod
    def record_payment(customer_name: str, amount: float, note: Optional[str] = None,
                       utterance_id: Optional[str] = None, session_id: str = "default",
                       lang: str = "hinglish") -> Dict[str, Any]:
        """Record payment received from a customer."""
        amount_paise = to_paise(amount)
        now = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            cur = conn.cursor()
            cust_id, display_name, _ = find_or_create_customer(conn, customer_name)
            
            cur.execute(
                """
                INSERT INTO ledger_entries (customer_id, kind, amount_paise, note, utterance_id, created_at)
                VALUES (?, 'PAYMENT', ?, ?, ?, ?);
                """,
                (cust_id, amount_paise, note, utterance_id, now)
            )
            entry_id = cur.lastrowid

            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            new_balance_paise = cur.fetchone()["balance_paise"]

        session = session_manager.get_or_create(session_id)
        session.set_last_customer(cust_id, display_name)
        session.record_turn_entries([entry_id], [{"tool": "record_payment", "entry_id": entry_id}])

        if new_balance_paise <= 0:
            reply = render_template(
                "payment_cleared",
                lang=lang,
                customer_name=display_name,
                amount=format_rupees(amount_paise)
            )
        else:
            reply = render_template(
                "record_payment",
                lang=lang,
                customer_name=display_name,
                amount=format_rupees(amount_paise),
                new_balance=format_rupees(new_balance_paise)
            )

        return {
            "customer_id": cust_id,
            "customer_name": display_name,
            "amount_paise": amount_paise,
            "balance_paise": new_balance_paise,
            "entry_id": entry_id,
            "reply_text": reply
        }

    @staticmethod
    def get_balance(customer_name: Optional[str] = None, session_id: str = "default",
                    lang: str = "hinglish") -> Dict[str, Any]:
        """Fetch customer balance and last 5 entries."""
        session = session_manager.get_or_create(session_id)
        target_name = customer_name or session.last_customer_name

        if not target_name:
            return {
                "reply_text": "Kiska balance dekhna hai? Kripya naam batayein."
            }

        with get_db() as conn:
            cur = conn.cursor()
            cust_id, display_name, is_new = find_or_create_customer(conn, target_name)
            if is_new:
                return {
                    "customer_name": display_name,
                    "balance_paise": 0,
                    "entries": [],
                    "reply_text": f"{display_name} ka koi purana hisaab nahi hai."
                }

            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            balance_paise = cur.fetchone()["balance_paise"]

            cur.execute(
                """
                SELECT id, kind, amount_paise, note, created_at, voided_at
                FROM ledger_entries
                WHERE customer_id = ? AND voided_at IS NULL
                ORDER BY created_at DESC
                LIMIT 5;
                """,
                (cust_id,)
            )
            entries = [dict(r) for r in cur.fetchall()]

        session.set_last_customer(cust_id, display_name)

        reply = render_template(
            "get_balance",
            lang=lang,
            customer_name=display_name,
            balance=format_rupees(balance_paise)
        )

        return {
            "customer_id": cust_id,
            "customer_name": display_name,
            "balance_paise": balance_paise,
            "entries": entries,
            "reply_text": reply
        }

    @staticmethod
    def top_debtors(limit: int = 5) -> Dict[str, Any]:
        """Get customers with the highest outstanding credit balances."""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.id, c.name, c.name_roman, b.balance_paise
                FROM customer_balances b
                JOIN customers c ON c.id = b.customer_id
                WHERE b.balance_paise > 0
                ORDER BY b.balance_paise DESC
                LIMIT ?;
                """,
                (limit,)
            )
            rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return {"debtors": [], "reply_text": "Kisi par bhi koi udhaar baaki nahi hai."}

        top = rows[0]
        reply = f"Sabse zyada udhaar {top['name']} ka hai, {format_rupees(top['balance_paise'])}।"
        return {"debtors": rows, "reply_text": reply}

    @staticmethod
    def daily_summary() -> Dict[str, Any]:
        """Get summary of today's credit given, payments received, and net cashflow."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    COALESCE(SUM(CASE WHEN kind = 'CREDIT' THEN amount_paise END), 0) AS total_credit,
                    COALESCE(SUM(CASE WHEN kind = 'PAYMENT' THEN amount_paise END), 0) AS total_payment,
                    COUNT(*) AS count_entries
                FROM ledger_entries
                WHERE created_at LIKE ? AND voided_at IS NULL AND utterance_id != 'seed';
                """,
                (f"{today}%",)
            )
            row = dict(cur.fetchone())

        total_cr = row["total_credit"]
        total_pm = row["total_payment"]
        reply = f"Aaj kul {format_rupees(total_cr)} udhaar diya gaya aur {format_rupees(total_pm)} wasool hua."
        return {
            "date": today,
            "total_credit_paise": total_cr,
            "total_payment_paise": total_pm,
            "count": row["count_entries"],
            "reply_text": reply
        }

    @staticmethod
    def undo_last(session_id: str = "default", lang: str = "hinglish") -> Dict[str, Any]:
        """Revert / void the entries created in the most recent turn."""
        session = session_manager.get_or_create(session_id)
        if not session.last_entry_ids:
            return {"reply_text": "Hataane ke liye koi haaliya hisaab nahi hai."}

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            for entry_id in session.last_entry_ids:
                cur.execute(
                    "UPDATE ledger_entries SET voided_at = ?, voided_by = 'undo' WHERE id = ?;",
                    (now, entry_id)
                )

        session.clear_last_entries()
        reply = render_template("undo", lang=lang)
        return {"undone": True, "reply_text": reply}

    undo_last_turn = undo_last

    @staticmethod
    def draft_reminder(customer_name: str, lang: str = "hinglish") -> Dict[str, Any]:
        """Generate a polite WhatsApp reminder message draft."""
        with get_db() as conn:
            cur = conn.cursor()
            cust_id, display_name, _ = find_or_create_customer(conn, customer_name)
            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            row = cur.fetchone()
            balance_paise = row["balance_paise"] if row else 0

        draft_text = f"Namaste {display_name} ji, aapka dukaan par {format_rupees(balance_paise)} baaki hai. Jab suvidha ho, kripya bhej dein. Dhanyavaad."
        reply = f"{display_name} ke liye reminder message taiyyar hai. Aap ise copy karke WhatsApp par bhej sakte hain."
        return {
            "customer_name": display_name,
            "balance_paise": balance_paise,
            "draft_text": draft_text,
            "reply_text": reply
        }

