"""
Bol-Khata REST API endpoints.
Provides customer ledger balances, transaction history, summaries, and top debtors.
"""

from fastapi import APIRouter
from app.db.session import get_db
from app.modules.khata.service import KhataService

router = APIRouter(prefix="/api/v1/khata", tags=["Bol-Khata"])

@router.get("/customers")
async def get_customers():
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

@router.get("/customer/{customer_id}/entries")
async def get_customer_entries(customer_id: int):
    """Get ledger history entries for a specific customer."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, kind, amount_paise, note, created_at, voided_at
            FROM ledger_entries
            WHERE customer_id = ?
            ORDER BY created_at DESC;
            """,
            (customer_id,)
        )
        return [dict(r) for r in cur.fetchall()]

@router.get("/summary")
async def get_daily_summary():
    """Get today's total credit given and payments collected."""
    return KhataService.daily_summary()

@router.get("/debtors")
async def get_top_debtors():
    """Get top 5 customers with highest unpaid credit."""
    return KhataService.top_debtors(limit=5)

