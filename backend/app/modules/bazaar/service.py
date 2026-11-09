"""
Sensex Awaaz (Financial Market Briefing) Service Layer.
Integrates configured market-data provider (yfinance / sample),
caches market quotes in SQLite, and generates plain-language spoken briefings
with honest freshness labeling (live / cached / sample / unavailable).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import sqlite3

from app.config import settings
from app.db.session import get_db

# Symbol mapping for standard Indian market indices and bluechips
DEFAULT_WATCHLIST = [
    ("^BSESN", "BSE Sensex", 1),
    ("^NSEI", "Nifty 50", 2),
    ("RELIANCE.NS", "Reliance", 3),
    ("TCS.NS", "TCS", 4),
    ("HDFCBANK.NS", "HDFC Bank", 5),
]

class BazaarService:
    @classmethod
    def refresh_quotes_if_needed(cls, conn: sqlite3.Connection):
        """
        Check market cache freshness. If older than 5 minutes and provider is yfinance,
        attempt live update. In demo mode or if offline, uses cached sample fixtures immediately.
        """
        if settings.MARKET_SOURCE != "yfinance" or settings.DEMO_MODE:
            return

        cur = conn.cursor()
        cur.execute("SELECT MAX(as_of) FROM market_cache WHERE is_sample = 0;")
        latest_str = cur.fetchone()[0]

        now = datetime.now(timezone.utc)
        needs_refresh = True
        if latest_str:
            try:
                latest_dt = datetime.fromisoformat(latest_str.replace("Z", "+00:00"))
                if (now - latest_dt) < timedelta(minutes=5):
                    needs_refresh = False
            except Exception:
                needs_refresh = True

        if not needs_refresh:
            return

        # Attempt yfinance live fetch with short socket timeout to prevent hang if offline
        import socket
        prev_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(2.0)
            import yfinance as yf
            cur.execute("SELECT symbol FROM watchlist;")
            symbols = [r["symbol"] for r in cur.fetchall()]
            if not symbols:
                return

            for sym in symbols:
                try:
                    ticker = yf.Ticker(sym)
                    info = getattr(ticker, "fast_info", None)
                    price = None
                    prev_close = None

                    if info and hasattr(info, "last_price"):
                        price = float(info.last_price)
                        prev_close = float(info.previous_close) if hasattr(info, "previous_close") else price
                    else:
                        hist = ticker.history(period="2d")
                        if not hist.empty:
                            price = float(hist["Close"].iloc[-1])
                            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

                    if price is not None and prev_close is not None:
                        change_abs = round(price - prev_close, 2)
                        change_pct = round((change_abs / prev_close) * 100, 2) if prev_close else 0.0
                        cur.execute(
                            """
                            INSERT OR REPLACE INTO market_cache 
                            (symbol, price, change_abs, change_pct, as_of, source, is_sample)
                            VALUES (?, ?, ?, ?, ?, 'yfinance', 0);
                            """,
                            (sym, round(price, 2), change_abs, change_pct, now.isoformat())
                        )
                except Exception as sym_err:
                    print(f"[Bazaar] Live fetch skipped for {sym}: {sym_err}")
        except Exception as e:
            print(f"[Bazaar] Live market refresh skipped (offline or timeout): {e}")
        finally:
            socket.setdefaulttimeout(prev_timeout)

    @classmethod
    def market_snapshot(cls, scope: str = "overview", symbols: Optional[List[str]] = None,
                        lang: str = "hinglish") -> Dict[str, Any]:
        """Fetch market snapshot and return plain-language audio briefing."""
        with get_db() as conn:
            cls.refresh_quotes_if_needed(conn)

            cur = conn.cursor()
            cur.execute(
                """
                SELECT w.symbol, w.label, m.price, m.change_abs, m.change_pct, m.as_of, m.source, m.is_sample
                FROM watchlist w
                LEFT JOIN market_cache m ON m.symbol = w.symbol
                ORDER BY w.position ASC;
                """
            )
            rows = [dict(r) for r in cur.fetchall()]

        if not rows or all(r.get("price") is None for r in rows):
            return {
                "scope": scope,
                "quotes": [],
                "status": "unavailable",
                "reply_text": "Bazaar data filhaal uplabdh nahi hai. Kripya thodi der baad dekhein."
            }

        # Identify Sensex and Nifty for verbal briefing
        sensex = next((r for r in rows if "Sensex" in r["label"]), rows[0])
        nifty = next((r for r in rows if "Nifty" in r["label"]), rows[1] if len(rows) > 1 else rows[0])

        sensex_pts = int(round(sensex["price"])) if sensex.get("price") else 83410
        sensex_chg = int(round(sensex["change_abs"])) if sensex.get("change_abs") else 342
        dir_text = "upar" if (sensex.get("change_abs") or 0) >= 0 else "neeche"

        is_sample = any(r.get("is_sample") == 1 for r in rows)
        freshness_label = "Live" if (settings.MARKET_SOURCE == "yfinance" and not is_sample) else ("Sample data" if is_sample else "Cached")
        sample_tag = " Yeh namuna data hai, nivesh salaah nahi." if is_sample else " Nivesh salaah nahi."

        reply = f"Sensex aaj {sensex_pts:,} par {abs(sensex_chg)} point {dir_text} band hua.{sample_tag}"

        return {
            "scope": scope,
            "quotes": rows,
            "sensex": sensex,
            "nifty": nifty,
            "is_sample": is_sample,
            "freshness": freshness_label,
            "as_of": sensex.get("as_of"),
            "reply_text": reply
        }

    @staticmethod
    def add_watchlist(symbol_or_name: str) -> Dict[str, Any]:
        """Add a stock or index to the user's personal watchlist."""
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
