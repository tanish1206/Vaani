"""
Sensex Awaaz REST API endpoints.
Provides market snapshot, index quotes, and watchlist management.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.modules.bazaar.service import BazaarService

router = APIRouter(prefix="/api/v1/bazaar", tags=["Sensex Awaaz"])

class WatchlistAddRequest(BaseModel):
    symbol_or_name: str

@router.get("/snapshot")
async def get_market_snapshot(scope: str = "overview"):
    """Get market snapshot with index prices and audio brief text."""
    return BazaarService.market_snapshot(scope=scope)

@router.post("/watchlist")
async def add_to_watchlist(req: WatchlistAddRequest):
    """Add a symbol to the user's personal watchlist."""
    return BazaarService.add_watchlist(req.symbol_or_name)

