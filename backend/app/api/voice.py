"""
Voice Turn API Endpoint for VAANI.
Receives recorded audio (binary stream or JSON base64) directly from browser MediaRecorder,
transcribes with Gnani Prisma v3.0, and executes the conversational voice pipeline.
"""

from fastapi import APIRouter, Request
from typing import Optional
import base64

from app.gnani.stt import PrismaSTTClient
from app.gnani.tts import TimbreTTSClient
from app.core.pipeline import VoicePipeline

router = APIRouter(prefix="/api/v1", tags=["Voice Turn"])

@router.post("/voice/turn")
async def handle_voice_turn(request: Request):
    """
    Process one voice turn end to end:
    Receives raw audio stream or multipart/json, calls Prisma STT,
    executes Evon pipeline, and returns spoken result.
    """
    content_type = request.headers.get("content-type", "")
    session_id = request.headers.get("X-Session-ID", "app-user")
    lang_hint = request.headers.get("X-Lang-Hint", "auto")

    audio_bytes = b""
    filename = "turn.wav"

    if "application/json" in content_type:
        body = await request.json()
        audio_b64 = body.get("audio_base64", "")
        session_id = body.get("session_id", session_id)
        lang_hint = body.get("lang_hint", lang_hint)
        filename = body.get("filename", "turn.wav")
        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
    else:
        # Direct binary audio upload
        audio_bytes = await request.body()
        filename = "turn.webm" if "webm" in content_type else "turn.wav"

    # 1. Transcribe audio with Prisma STT
    stt_res = await PrismaSTTClient.transcribe(
        audio_bytes=audio_bytes,
        filename=filename,
        language_code=lang_hint if lang_hint in ["hi-IN", "mr-IN", "en-IN"] else None
    )
    transcript = stt_res.get("transcript", "")

    # 2. Run Voice Pipeline
    result = await VoicePipeline.run_turn(
        transcript=transcript,
        session_id=session_id,
        lang_hint=lang_hint
    )

    # 3. Synthesize speech if possible
    reply_text = result.get("reply_text", "")
    tts_bytes = await TimbreTTSClient.synthesize(text=reply_text, lang=result.get("language", "hi"))

    result["has_audio_bytes"] = tts_bytes is not None
    return result
