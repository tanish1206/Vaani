"""
Bol-Khata REST API endpoints.
Provides customer ledger balances, transaction history, summaries, top debtors,
and manual transaction/undo actions.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.db.session import get_db
from app.modules.khata.service import KhataService

router = APIRouter(prefix="/api/v1/khata", tags=["Bol-Khata"])

class TransactionRequest(BaseModel):
    customer_name: str
    kind: str  # 'CREDIT' or 'PAYMENT'
    amount: float
    note: Optional[str] = None
    session_id: Optional[str] = "default"

class UndoRequest(BaseModel):
    session_id: Optional[str] = "default"

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

@router.post("/transaction")
async def add_manual_transaction(req: TransactionRequest):
    """Add credit or payment manually via form."""
    k = req.kind.strip().upper()
    if k == "CREDIT":
        res = KhataService.add_credit(
            customer_name=req.customer_name,
            amount=req.amount,
            note=req.note,
            session_id=req.session_id or "default"
        )
    elif k in ("PAYMENT", "JAMA"):
        res = KhataService.add_payment(
            customer_name=req.customer_name,
            amount=req.amount,
            note=req.note,
            session_id=req.session_id or "default"
        )
    else:
        return {"error": f"Invalid transaction kind: '{req.kind}'. Expected CREDIT or PAYMENT."}
    return res

@router.post("/undo")
async def undo_transaction(req: UndoRequest):
    """Undo the most recent transaction in the session."""
    return KhataService.undo_last(session_id=req.session_id or "default")
