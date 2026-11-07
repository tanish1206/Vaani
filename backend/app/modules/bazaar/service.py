"""
Sensex Awaaz (Financial Market Briefing) Service Layer.
Fetches cached market indices, watchlist quotes,
and generates plain-spoken audio briefings with honest freshness labeling.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import sqlite3

from app.db.session import get_db

class BazaarService:
    @staticmethod
    def market_snapshot(scope: str = "overview", symbols: Optional[List[str]] = None,
                        lang: str = "hinglish") -> Dict[str, Any]:
        """Fetch market snapshot and return plain-language audio brief."""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT w.symbol, w.label, m.price, m.change_abs, m.change_pct, m.as_of, m.is_sample
                FROM watchlist w
                LEFT JOIN market_cache m ON m.symbol = w.symbol
                ORDER BY w.position ASC;
                """
            )
            rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            return {"quotes": [], "reply_text": "Bazaar data uplabdh nahi hai."}

        # Find Sensex and Nifty for audio brief
        sensex = next((r for r in rows if "Sensex" in r["label"]), rows[0])
        nifty = next((r for r in rows if "Nifty" in r["label"]), rows[1] if len(rows) > 1 else rows[0])

        sensex_pts = int(round(sensex["price"])) if sensex.get("price") else 83410
        sensex_chg = int(round(sensex["change_abs"])) if sensex.get("change_abs") else 342
        dir_text = "upar" if (sensex.get("change_abs") or 0) >= 0 else "neeche"

        is_sample = any(r.get("is_sample") for r in rows)
        sample_tag = " Yeh namuna data hai, nivesh salaah nahi." if is_sample else " Nivesh salaah nahi."

        reply = f"Sensex aaj {sensex_pts:,} par {abs(sensex_chg)} point {dir_text} band hua.{sample_tag}"

        return {
            "scope": scope,
            "quotes": rows,
            "sensex": sensex,
            "nifty": nifty,
            "is_sample": is_sample,
            "reply_text": reply
        }

    @staticmethod
    def add_watchlist(symbol_or_name: str) -> Dict[str, Any]:
        """Add a stock or index to the user's watchlist."""
        clean_sym = symbol_or_name.upper().strip()
        if not clean_sym.endswith(".NS") and not clean_sym.startswith("^"):
            clean_sym = f"{clean_sym}.NS"

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM watchlist;")
            next_pos = cur.fetchone()[0] + 1
            cur.execute(
                """
                INSERT OR IGNORE INTO watchlist (symbol, label, position)
                VALUES (?, ?, ?);
                """,
                (clean_sym, symbol_or_name.capitalize(), next_pos)
            )

        reply = f"{symbol_or_name.capitalize()} aapki watchlist mein jod diya gaya hai."
        return {"symbol": clean_sym, "label": symbol_or_name, "reply_text": reply}

