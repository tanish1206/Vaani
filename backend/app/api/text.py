"""
Text Turn API Endpoint for VAANI.
Allows text-based interaction following the same pipeline as voice, using the selected Gnani voice.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.pipeline import VoicePipeline
from app.services.gnani import GnaniClient
from app.services.voice import VoiceSettingsService, AudioProcessor

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
        dry_run=is_ephemeral
    )

    # Synthesize speech using the user's selected Gnani voice and model
    reply_text = result.get("reply_text", "")
    selected_voice = VoiceSettingsService.get_selected_voice_id()
    selected_model = VoiceSettingsService.get_selected_tts_model()
    speed = VoiceSettingsService.get_selected_speech_rate()
    result["voice_id"] = selected_voice
    result["tts_model"] = selected_model

    tts_bytes = await GnaniClient.synthesize(
        text=reply_text,
        voice_id=selected_voice,
        model=selected_model,
        language=result.get("language", "hi-IN"),
        speed=speed
    )
    if tts_bytes:
        result["audio_base64"] = AudioProcessor.encode_base64_audio(tts_bytes)
        result["has_audio_bytes"] = True
    else:
        result["audio_base64"] = None
        result["has_audio_bytes"] = False

    return result
