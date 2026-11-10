"""
Voice & Audio API Endpoints for VAANI.
Provides official Gnani ASR, TTS, Dynamic Voice Selection, Voice Previews, and Unified Voice Turn Orchestration.
STRICT PRIVACY: Audio processed in-memory; ephemeral previews and demo turns never touch database.
"""

from fastapi import APIRouter, Request, HTTPException, Body
from typing import Optional, Dict, Any
import base64

from app.services.gnani import GnaniClient
from app.services.voice import VoiceSettingsService, AudioProcessor
from app.core.pipeline import VoicePipeline

router = APIRouter(prefix="/api/v1", tags=["Voice Engine"])

@router.get("/voice/health")
async def get_voice_health():
    """
    Diagnostic health status of the Gnani Voice integration.
    Distinguishes:
      - CONFIGURATION_MISSING
      - CONNECTED
      - AUTHENTICATION_FAILED
      - SERVICE_UNAVAILABLE
    """
    health = await GnaniClient.check_health()
    selected_voice = VoiceSettingsService.get_selected_voice_id()
    health["selected_voice"] = selected_voice
    return health

@router.get("/voice/options")
async def get_voice_options():
    """
    Retrieve provider-supported Gnani voice options and user's current selection.
    """
    voices = await GnaniClient.get_voice_options()
    current_voice_id = VoiceSettingsService.get_selected_voice_id()

    # Mark current voice
    for v in voices:
        v["selected"] = (v["id"].lower() == current_voice_id.lower())

    return {
        "provider": "gnani-timbre",
        "default_voice": "Bhavna",
        "current_voice": current_voice_id,
        "voices": voices
    }

@router.post("/voice/preview")
async def preview_voice(payload: Dict[str, Any] = Body(...)):
    """
    Generate an ephemeral voice preview using real Gnani TTS.
    STRICT PRIVACY:
      - Never written to database
      - Never stored in conversation history
      - Zero customer or transactional writes
    """
    voice_id = payload.get("voice_id", "Bhavna")
    text = payload.get(
        "text",
        "Namaste, main Vaani hoon. Aap bataiye, main aapki kya madad kar sakti hoon?"
    )

    if not GnaniClient.config.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Gnani API key is not configured in .env. Please configure GNANI_API_KEY to preview voices."
        )

    resolved_voice = GnaniClient.voices.resolve_voice_id(voice_id)
    audio_bytes = await GnaniClient.synthesize(text=text, voice_id=resolved_voice)

    if not audio_bytes:
        raise HTTPException(
            status_code=502,
            detail="Gnani TTS failed to generate preview audio. Check API credentials and network."
        )

    return {
        "voice_id": resolved_voice,
        "text": text,
        "audio_base64": AudioProcessor.encode_base64_audio(audio_bytes),
        "content_type": "audio/wav"
    }

@router.get("/settings/voice")
async def get_voice_settings():
    """Get current voice preference and full metadata."""
    current_voice = VoiceSettingsService.get_selected_voice_details()
    voices = await GnaniClient.get_voice_options()
    return {
        "selected_voice": current_voice,
        "available_voices": voices
    }

@router.put("/settings/voice")
async def update_voice_settings(payload: Dict[str, Any] = Body(...)):
    """Persist user selected voice ID to database settings."""
    voice_id = payload.get("voice_id")
    if not voice_id:
        raise HTTPException(status_code=422, detail="voice_id is required.")

    try:
        result = VoiceSettingsService.set_selected_voice_id(voice_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/voice/transcribe")
async def transcribe_audio(request: Request):
    """
    Transcribe uploaded audio bytes with Gnani Prisma v3.0.
    """
    audio_bytes = await request.body()
    content_type = request.headers.get("content-type", "audio/webm")
    filename = "turn.webm" if "webm" in content_type else "turn.wav"

    valid, err_msg = AudioProcessor.validate_audio_bytes(audio_bytes, filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    stt_res = await GnaniClient.transcribe(audio_bytes, filename=filename)
    if not stt_res.get("success"):
        raise HTTPException(
            status_code=400 if stt_res.get("error_code") == "AUDIO_TOO_SHORT" else 502,
            detail=stt_res.get("error", "Transcription failed")
        )

    return stt_res

@router.post("/voice/speak")
async def synthesize_speech(payload: Dict[str, Any] = Body(...)):
    """
    Synthesize speech using Gnani Timbre and the selected voice.
    """
    text = payload.get("text", "")
    voice_id = payload.get("voice_id") or VoiceSettingsService.get_selected_voice_id()

    if not text.strip():
        raise HTTPException(status_code=422, detail="text is required.")

    audio_bytes = await GnaniClient.synthesize(text=text, voice_id=voice_id)
    if not audio_bytes:
        raise HTTPException(status_code=502, detail="Gnani TTS failed to generate audio.")

    return {
        "text": text,
        "voice_id": voice_id,
        "audio_base64": AudioProcessor.encode_base64_audio(audio_bytes),
        "content_type": "audio/wav"
    }

@router.post("/voice/turn")
async def handle_voice_turn(request: Request):
    """
    Process one voice turn end to end:
    1. Receives real recorded audio stream or JSON base64 from browser.
    2. Transcribes via Gnani Prisma v3.0 (Zero mock transcripts).
    3. Executes conversational pipeline & database transactions.
    4. Synthesizes speech reply using selected Gnani voice.
    """
    content_type = request.headers.get("content-type", "")
    session_id = request.headers.get("X-Session-ID", "app-user")
    lang_hint = request.headers.get("X-Lang-Hint", "auto")

    audio_bytes = b""
    filename = "turn.webm"

    if "application/json" in content_type:
        body = await request.json()
        audio_b64 = body.get("audio_base64", "")
        session_id = body.get("session_id", session_id)
        lang_hint = body.get("lang_hint", lang_hint)
        filename = body.get("filename", "turn.webm")
        if audio_b64:
            try:
                audio_bytes = base64.b64decode(audio_b64)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid base64 audio data.")
    else:
        audio_bytes = await request.body()
        filename = "turn.webm" if "webm" in content_type else "turn.wav"

    valid, err_msg = AudioProcessor.validate_audio_bytes(audio_bytes, filename)
    if not valid:
        return {
            "turn_id": "error",
            "transcript": "",
            "language": "hinglish",
            "actions": [],
            "reply_text": f"Kshama karein, awaaz sahi se record nahi hui ({err_msg}).",
            "audio_base64": None,
            "has_audio_bytes": False,
            "error": err_msg
        }

    # 1. Transcribe audio with Gnani Prisma STT
    stt_res = await GnaniClient.transcribe(
        audio_bytes=audio_bytes,
        filename=filename,
        language_code=lang_hint if lang_hint in ["hi-IN", "mr-IN", "en-IN"] else None
    )

    if not stt_res.get("success"):
        error_msg = stt_res.get("error", "Awaaz pehchanne mein samasya aayi.")
        return {
            "turn_id": "stt-error",
            "transcript": "",
            "language": "hinglish",
            "actions": [],
            "reply_text": error_msg,
            "audio_base64": None,
            "has_audio_bytes": False,
            "error": error_msg,
            "error_code": stt_res.get("error_code")
        }

    transcript = stt_res.get("transcript", "").strip()
    if not transcript:
        return {
            "turn_id": "empty-transcript",
            "transcript": "",
            "language": "hinglish",
            "actions": [],
            "reply_text": "Kuch sunaai nahi diya. Kripya mic dabakar dobara boliye.",
            "audio_base64": None,
            "has_audio_bytes": False
        }

    # 2. Check if turn is an ephemeral landing sandbox turn
    is_ephemeral = session_id.startswith("landing")

    # 3. Execute conversational pipeline
    result = await VoicePipeline.run_turn(
        transcript=transcript,
        session_id=session_id,
        lang_hint=lang_hint,
        dry_run=is_ephemeral
    )

    # 4. Synthesize speech using the user's selected Gnani voice
    reply_text = result.get("reply_text", "")
    selected_voice = VoiceSettingsService.get_selected_voice_id()
    result["voice_id"] = selected_voice

    tts_bytes = await GnaniClient.synthesize(text=reply_text, voice_id=selected_voice)
    if tts_bytes:
        result["audio_base64"] = AudioProcessor.encode_base64_audio(tts_bytes)
        result["has_audio_bytes"] = True
    else:
        result["audio_base64"] = None
        result["has_audio_bytes"] = False

    return result
