"""
Text Turn API Endpoint for VAANI.
Allows text-based interaction following the same pipeline as voice.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.pipeline import VoicePipeline

router = APIRouter(prefix="/api/v1", tags=["Text Turn"])

class TextTurnRequest(BaseModel):
    text: str
    session_id: Optional[str] = "demo-session"
    language_hint: Optional[str] = "auto"
    dry_run: Optional[bool] = False

@router.post("/text/turn")
async def handle_text_turn(req: TextTurnRequest):
    """Execute one text-based conversational turn."""
    return await VoicePipeline.run_turn(
        transcript=req.text,
        session_id=req.session_id or "demo-session",
        lang_hint=req.language_hint or "auto",
        dry_run=req.dry_run or False
    )

