"""
Text Turn API Endpoint for VAANI.
Allows text-based interaction following the same pipeline as voice, using the selected Gnani voice.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.pipeline import VoicePipeline

router = APIRouter(prefix="/api/v1", tags=["Text Turn"])


class TextTurnRequest(BaseModel):
    text: str
    session_id: Optional[str] = "app-user"
    language_hint: Optional[str] = "auto"
    dry_run: Optional[bool] = False


@router.post("/text/turn")
async def handle_text_turn(req: TextTurnRequest):
    """Execute one text-based conversational turn."""
    session_id = req.session_id or "app-user"
    is_ephemeral = bool(req.dry_run or session_id.startswith("landing"))

    result = await VoicePipeline.run_turn(
        transcript=req.text,
        session_id=session_id,
        lang_hint=req.language_hint or "auto",
        dry_run=is_ephemeral,
    )
    return await VoicePipeline.attach_tts_audio(result)
