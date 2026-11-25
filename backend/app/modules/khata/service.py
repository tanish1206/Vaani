"""
Bol-Khata (Business Ledger) Service Layer.
Handles Customer Management, Transactions, Balances, Daily Summaries, Corrections, and Undo.
STRICT PRIVACY & ACCURACY: Pulls customer name directly from verified database record.
"""

from datetime import datetime, timezone
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from app.core.i18n import format_rupees, render_template, to_paise
from app.core.session import session_manager
from app.db.seed import normalise_name_key
from app.db.session import get_db
from app.gnani.evon import transliterate_devanagari

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


def _format_plain_rupees(paise: int) -> str:
    """Format paise without thousands separator for compact template replies."""
    if paise % 100 == 0:
        return f"{paise // 100}"
    return f"{paise / 100:.2f}"


def find_customer(
    conn: sqlite3.Connection,
    name: str,
    name_roman: Optional[str] = None,
    fuzzy_threshold: int = 85,
) -> Optional[sqlite3.Row]:
    """Find an existing customer by normalised key, raw name, or fuzzy match."""
    cur = conn.cursor()
    roman = name_roman or transliterate_devanagari(name) or name
    key = normalise_name_key(roman)

    cur.execute("SELECT id, name, name_roman FROM customers WHERE name_key = ?;", (key,))
    row = cur.fetchone()
    if row:
        return row

    cur.execute(
        "SELECT id, name, name_roman FROM customers WHERE lower(name) = ? OR lower(name_roman) = ?;",
        (name.lower(), roman.lower()),
    )
    row = cur.fetchone()
    if row:
        return row

    cur.execute("SELECT id, name, name_roman, name_key FROM customers;")
    best_match = None
    best_score = 0
    for customer in cur.fetchall():
        score_key = (
            fuzz.ratio(key, customer["name_key"])
            if HAS_RAPIDFUZZ
            else (100 if key and key in customer["name_key"] else 0)
        )
        score_roman = fuzz.ratio(roman.lower(), customer["name_roman"].lower()) if HAS_RAPIDFUZZ else 0
        score = max(score_key, score_roman)
        if score > best_score:
            best_score = score
            best_match = customer

    if best_match and best_score >= fuzzy_threshold:
        return best_match
    return None


def find_or_create_customer(
    conn: sqlite3.Connection,
    name: str,
    name_roman: Optional[str] = None,
) -> Tuple[int, str, bool]:
    """
    Find existing customer by exact or fuzzy matching, or create a new customer.
    Returns: (customer_id, display_name, is_new_customer)
    """
    existing = find_customer(conn, name, name_roman=name_roman)
    if existing:
        return existing["id"], existing["name"], False

    roman = name_roman or transliterate_devanagari(name) or name
    key = normalise_name_key(roman)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO customers (name, name_roman, name_key, phone, created_at)
        VALUES (?, ?, ?, NULL, ?);
        """,
        (name, roman, key, now),
    )
    return cur.lastrowid, name, True


class KhataService:
    @staticmethod
    def list_customers() -> List[Dict[str, Any]]:
        """List all customers and their outstanding ledger balances."""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.id, c.name, c.name_roman, c.phone, COALESCE(b.balance_paise, 0) AS balance_paise
                FROM customers c
                LEFT JOIN customer_balances b ON b.customer_id = c.id
                ORDER BY c.id ASC;
                """
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def get_customer_entries(customer_id: int) -> List[Dict[str, Any]]:
        """Return ledger history entries for a specific customer."""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, kind, amount_paise, note, created_at, voided_at
                FROM ledger_entries
                WHERE customer_id = ?
                ORDER BY created_at DESC;
                """,
                (customer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def _record_entry(
        kind: str,
        customer_name: str,
        amount: float,
        customer_name_roman: Optional[str] = None,
        note: Optional[str] = None,
        utterance_id: Optional[str] = None,
        session_id: str = "default",
        corrects_entry_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Shared helper for recording CREDIT or PAYMENT entries in integer paise."""
        amount_paise = to_paise(amount)
        now = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            cur = conn.cursor()
            cust_id, display_name, _ = find_or_create_customer(
                conn, customer_name, name_roman=customer_name_roman
            )
            cur.execute(
                """
                INSERT INTO ledger_entries
                    (customer_id, kind, amount_paise, note, utterance_id, corrects_entry_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (cust_id, kind, amount_paise, note, utterance_id, corrects_entry_id, now),
            )
            entry_id = cur.lastrowid

            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            new_balance_paise = cur.fetchone()["balance_paise"]

        tool_name = "add_credit" if kind == "CREDIT" else "record_payment"
        session = session_manager.get_or_create(session_id)
        session.set_last_customer(cust_id, display_name)
        session.record_turn_entries([entry_id], [{"tool": tool_name, "entry_id": entry_id}])

        amt_disp = _format_plain_rupees(amount_paise)
        bal_disp = _format_plain_rupees(new_balance_paise)
        verb = "udhaar likh diya" if kind == "CREDIT" else "jama kar diya"
        reply = f"{display_name}: ₹{amt_disp} {verb}. Ab baaki ₹{bal_disp}."

        return {
            "customer_id": cust_id,
            "customer_name": display_name,
            "amount_paise": amount_paise,
            "balance_paise": new_balance_paise,
            "entry_id": entry_id,
            "reply_text": reply,
        }

    @staticmethod
    def add_credit(
        customer_name: str,
        amount: float,
        customer_name_roman: Optional[str] = None,
        note: Optional[str] = None,
        utterance_id: Optional[str] = None,
        session_id: str = "default",
        lang: str = "hinglish",
    ) -> Dict[str, Any]:
        """Record credit given to a customer."""
        return KhataService._record_entry(
            kind="CREDIT",
            customer_name=customer_name,
            amount=amount,
            customer_name_roman=customer_name_roman,
            note=note,
            utterance_id=utterance_id,
            session_id=session_id,
        )

    @staticmethod
    def record_payment(
        customer_name: str,
        amount: float,
        customer_name_roman: Optional[str] = None,
        note: Optional[str] = None,
        utterance_id: Optional[str] = None,
        session_id: str = "default",
        lang: str = "hinglish",
    ) -> Dict[str, Any]:
        """Record payment received from a customer."""
        return KhataService._record_entry(
            kind="PAYMENT",
            customer_name=customer_name,
            amount=amount,
            customer_name_roman=customer_name_roman,
            note=note,
            utterance_id=utterance_id,
            session_id=session_id,
        )

    @staticmethod
    def get_balance(
        customer_name: Optional[str] = None,
        customer_name_roman: Optional[str] = None,
        session_id: str = "default",
        lang: str = "hinglish",
    ) -> Dict[str, Any]:
        """Fetch customer balance and last 5 entries."""
        session = session_manager.get_or_create(session_id)
        target_name = customer_name or session.last_customer_name

        if not target_name:
            return {"reply_text": "Kiska hisaab dekhna hai? Kripya naam batayein."}

        with get_db() as conn:
            row = find_customer(conn, target_name, name_roman=customer_name_roman)
            if not row:
                return {
                    "customer_name": target_name,
                    "balance_paise": 0,
                    "entries": [],
                    "reply_text": f"{target_name} ka koi purana hisaab nahi hai.",
                }

            cust_id = row["id"]
            display_name = row["name"]
            cur = conn.cursor()
            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            row_bal = cur.fetchone()
            balance_paise = row_bal["balance_paise"] if row_bal else 0

            cur.execute(
                """
                SELECT id, kind, amount_paise, note, created_at, voided_at
                FROM ledger_entries
                WHERE customer_id = ? AND voided_at IS NULL
                ORDER BY created_at DESC
                LIMIT 5;
                """,
                (cust_id,),
            )
            entries = [dict(r) for r in cur.fetchall()]

        session.set_last_customer(cust_id, display_name)
        bal_disp = _format_plain_rupees(balance_paise)
        return {
            "customer_id": cust_id,
            "customer_name": display_name,
            "balance_paise": balance_paise,
            "entries": entries,
            "reply_text": f"{display_name} ka kul baaki ₹{bal_disp} hai.",
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
                (limit,),
            )
            rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return {"debtors": [], "reply_text": "Kisi par bhi koi udhaar baaki nahi hai."}

        top = rows[0]
        reply = f"Sabse zyada udhaar {top['name']} ka hai, {format_rupees(top['balance_paise'])}।"
        return {"debtors": rows, "reply_text": reply}

    @staticmethod
    def daily_summary() -> Dict[str, Any]:
        """Get summary of today's credit given, payments received, and entry count."""
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
                WHERE created_at LIKE ? AND voided_at IS NULL AND (utterance_id IS NULL OR utterance_id != 'seed');
                """,
                (f"{today}%",),
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
            "reply_text": reply,
        }

    @staticmethod
    def undo_last(session_id: str = "default", lang: str = "hinglish") -> Dict[str, Any]:
        """Revert / void the entries created in the most recent turn."""
        session = session_manager.get_or_create(session_id)
        if not session.last_entry_ids:
            return {"undone": False, "reply_text": "Hataane ke liye koi haaliya hisaab nahi hai."}

        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            for entry_id in session.last_entry_ids:
                cur.execute(
                    "UPDATE ledger_entries SET voided_at = ?, voided_by = 'undo' WHERE id = ?;",
                    (now, entry_id),
                )

        session.clear_last_entries()
        return {"undone": True, "reply_text": render_template("undo", lang=lang)}

    undo_last_turn = undo_last

    @staticmethod
    def correct_last_entry(
        new_amount: float,
        utterance_id: Optional[str] = None,
        session_id: str = "default",
        lang: str = "hinglish",
    ) -> Dict[str, Any]:
        """Void the most recent session entry and replace it with the corrected amount."""
        session = session_manager.get_or_create(session_id)
        if not session.last_entry_ids:
            return {"corrected": False, "reply_text": "Sudhaar karne ke liye koi haaliya hisaab nahi hai."}

        target_entry_id = session.last_entry_ids[-1]
        now = datetime.now(timezone.utc).isoformat()
        new_amount_paise = to_paise(new_amount)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.id, e.customer_id, e.kind, e.note, c.name
                FROM ledger_entries e
                JOIN customers c ON c.id = e.customer_id
                WHERE e.id = ? AND e.voided_at IS NULL;
                """,
                (target_entry_id,),
            )
            orig = cur.fetchone()
            if not orig:
                return {"corrected": False, "reply_text": "Sudhaar karne ke liye koi haaliya hisaab nahi hai."}

            cur.execute(
                "UPDATE ledger_entries SET voided_at = ?, voided_by = ? WHERE id = ?;",
                (now, utterance_id or "correction", target_entry_id),
            )
            cur.execute(
                """
                INSERT INTO ledger_entries
                    (customer_id, kind, amount_paise, note, utterance_id, corrects_entry_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    orig["customer_id"],
                    orig["kind"],
                    new_amount_paise,
                    orig["note"],
                    utterance_id,
                    target_entry_id,
                    now,
                ),
            )
            new_entry_id = cur.lastrowid
            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (orig["customer_id"],))
            new_balance_paise = cur.fetchone()["balance_paise"]

        session.clear_last_entries()
        session.record_turn_entries([new_entry_id], [{"tool": "correct_last_entry", "entry_id": new_entry_id}])

        reply = render_template(
            "correction",
            lang=lang,
            new_amount=format_rupees(new_amount_paise),
            new_balance=format_rupees(new_balance_paise),
        )
        return {
            "corrected": True,
            "customer_id": orig["customer_id"],
            "customer_name": orig["name"],
            "entry_id": new_entry_id,
            "amount_paise": new_amount_paise,
            "balance_paise": new_balance_paise,
            "reply_text": reply,
        }

    @staticmethod
    def draft_reminder(customer_name: str, lang: str = "hinglish") -> Dict[str, Any]:
        """Generate a polite WhatsApp reminder message draft without creating phantom customers."""
        with get_db() as conn:
            row = find_customer(conn, customer_name)
            if not row:
                return {
                    "customer_name": customer_name,
                    "balance_paise": 0,
                    "draft_text": None,
                    "reply_text": f"{customer_name} ka koi purana hisaab nahi mila.",
                }
            cust_id = row["id"]
            display_name = row["name"]
            cur = conn.cursor()
            cur.execute("SELECT balance_paise FROM customer_balances WHERE customer_id = ?;", (cust_id,))
            bal_row = cur.fetchone()
            balance_paise = bal_row["balance_paise"] if bal_row else 0

        draft_text = (
            f"Namaste {display_name} ji, aapka dukaan par {format_rupees(balance_paise)} baaki hai. "
            "Jab suvidha ho, kripya bhej dein. Dhanyavaad."
        )
        reply = f"{display_name} ke liye reminder message taiyyar hai. Aap ise copy karke WhatsApp par bhej sakte hain."
        return {
            "customer_name": display_name,
            "balance_paise": balance_paise,
            "draft_text": draft_text,
            "reply_text": reply,
        }
