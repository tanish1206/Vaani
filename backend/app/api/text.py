"""
Text Turn API Endpoint for VAANI.
Allows text-based interaction following the same pipeline as voice.
"""

import base64
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.pipeline import VoicePipeline
from app.gnani.tts import TimbreTTSClient

router = APIRouter(prefix="/api/v1", tags=["Text Turn"])

class TextTurnRequest(BaseModel):
    text: str
    session_id: Optional[str] = "demo-session"
    language_hint: Optional[str] = "auto"
    dry_run: Optional[bool] = False

@router.post("/text/turn")
async def handle_text_turn(req: TextTurnRequest):
    """Execute one text-based conversational turn."""
    result = await VoicePipeline.run_turn(
        transcript=req.text,
        session_id=req.session_id or "demo-session",
        lang_hint=req.language_hint or "auto",
        dry_run=req.dry_run or False
    )

    # Synthesize Timbre v2.5 speech
    reply_text = result.get("reply_text", "")
    tts_bytes = await TimbreTTSClient.synthesize(text=reply_text, lang=result.get("language", "hi"))
    if tts_bytes:
        result["audio_base64"] = base64.b64encode(tts_bytes).decode("ascii")
        result["has_audio_bytes"] = True
    else:
        result["audio_base64"] = None
        result["has_audio_bytes"] = False

    return result

