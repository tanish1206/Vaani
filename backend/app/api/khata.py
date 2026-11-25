"""
Bol-Khata REST API endpoints.
Provides customer ledger balances, transaction history, summaries, top debtors,
and manual transaction/undo actions.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.khata.service import KhataService

router = APIRouter(prefix="/api/v1/khata", tags=["Bol-Khata"])


class TransactionRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=120)
    kind: str  # 'CREDIT' or 'PAYMENT'
    amount: float = Field(..., gt=0, le=100000)
    note: Optional[str] = None
    session_id: Optional[str] = "default"


class UndoRequest(BaseModel):
    session_id: Optional[str] = "default"


@router.get("/customers")
async def get_customers():
    """List all customers and their outstanding ledger balances."""
    return KhataService.list_customers()


@router.get("/customer/{customer_id}/entries")
async def get_customer_entries(customer_id: int):
    """Get ledger history entries for a specific customer."""
    return KhataService.get_customer_entries(customer_id)


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
    customer_name = req.customer_name.strip()
    if not customer_name:
        raise HTTPException(status_code=422, detail="customer_name cannot be blank.")

    kind = req.kind.strip().upper()
    session_id = req.session_id or "default"

    if kind in ("CREDIT", "UDHAAR"):
        return KhataService.add_credit(
            customer_name=customer_name,
            amount=req.amount,
            note=req.note,
            session_id=session_id,
        )
    if kind in ("PAYMENT", "JAMA"):
        return KhataService.record_payment(
            customer_name=customer_name,
            amount=req.amount,
            note=req.note,
            session_id=session_id,
        )
    raise HTTPException(
        status_code=400,
        detail=f"Invalid transaction kind: '{req.kind}'. Expected CREDIT or PAYMENT.",
    )


@router.post("/undo")
async def undo_transaction(req: UndoRequest):
    """Undo the most recent transaction in the session."""
    return KhataService.undo_last(session_id=req.session_id or "default")
