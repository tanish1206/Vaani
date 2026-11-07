"""
Parchi REST API endpoints.
Provides active prescriptions, scheduled reminder doses, and dose completion updates.
"""

from fastapi import APIRouter
from app.modules.parchi.service import ParchiService

router = APIRouter(prefix="/api/v1/parchi", tags=["Parchi"])

@router.get("/doses")
async def get_today_doses():
    """Get active doses scheduled for today."""
    return ParchiService.list_doses()

@router.post("/done")
async def mark_dose_done():
    """Mark earliest pending medicine dose as completed."""
    return ParchiService.mark_dose_done()

@router.post("/snooze")
async def snooze_dose(minutes: int = 10):
    """Snooze pending reminder."""
    return ParchiService.snooze_dose(minutes=minutes)

