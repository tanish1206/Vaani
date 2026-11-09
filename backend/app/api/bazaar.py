"""
Sensex Awaaz REST API endpoints.
Provides market snapshot, index quotes, spoken briefings, and watchlist management.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.modules.bazaar.service import BazaarService

router = APIRouter(prefix="/api/v1/bazaar", tags=["Sensex Awaaz"])

class WatchlistAddRequest(BaseModel):
    symbol_or_name: str

@router.get("/snapshot")
@router.get("/overview")
async def get_market_snapshot(scope: str = "overview"):
    """Get market snapshot with index prices and audio brief text."""
    return BazaarService.market_snapshot(scope=scope)

@router.get("/briefing")
async def get_spoken_briefing(lang: str = "hinglish"):
    """Get plain-language spoken market briefing."""
    data = BazaarService.market_snapshot(lang=lang)
    return {
        "briefing": data.get("reply_text"),
        "freshness": data.get("freshness"),
        "is_sample": data.get("is_sample", True)
    }

@router.post("/watchlist")
async def add_to_watchlist(req: WatchlistAddRequest):
    """Add a symbol to the user's personal watchlist."""
    return BazaarService.add_watchlist(req.symbol_or_name)
