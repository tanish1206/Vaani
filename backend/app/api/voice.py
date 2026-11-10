"""
Voice & Audio API Endpoints for VAANI.
Provides official Gnani Prisma v3.0 STT, Timbre v3.0/v2.5 TTS, Realtime WebSocket Streaming Relay,
Voice Discovery, Ephemeral Voice Previews, and Unified Voice Turn Orchestration.

STRICT PRIVACY: Audio processed in-memory; ephemeral previews and demo turns never touch database.
"""

from fastapi import APIRouter, Request, HTTPException, Body, WebSocket, Query
from typing import Optional, Dict, Any
import base64

from app.services.gnani import GnaniClient
from app.services.gnani.voice_catalog import VoiceCatalogService
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
    full_settings = VoiceSettingsService.get_full_settings()
    health["current_settings"] = full_settings
    return health

@router.get("/voice/catalog")
def get_voice_catalog():
    """
    Retrieve the complete official two-model voice catalogue.
    Includes Timbre v3.0 (13 Pan-India voices) and Timbre v2.5 (42 Vernacular voices).
    """
    catalog = GnaniClient.get_catalog()
    current_settings = VoiceSettingsService.get_full_settings()
    return {
        **catalog,
        "current_settings": current_settings
    }

@router.get("/voice/options")
def get_voice_options(model: Optional[str] = Query(None)):
    """
    Retrieve provider-supported Gnani voice options for the requested or currently active model.
    """
    active_model = model or VoiceSettingsService.get_selected_tts_model()
    voices = [dict(v) for v in GnaniClient.get_voice_options(model=active_model)]
    current_voice_id = VoiceSettingsService.get_selected_voice_id()

    # Mark current voice
    for v in voices:
        v["selected"] = (
            v["id"].lower() == current_voice_id.lower() and
            v.get("model", "").lower() == active_model.lower()
        )

    return {
        "provider": "gnani-timbre",
        "current_model": active_model,
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
    target_model = payload.get("model") or VoiceSettingsService.get_selected_tts_model()
    voice_id = payload.get("voice_id") or ("Shivani" if "v3" in target_model else "Bhavna")
    speed = float(payload.get("speed", 1.0))
    language = payload.get("language", "hi-IN")

    # Select appropriate preview text based on language
    default_text = "नमस्ते, मैं वाणी हूँ. आपकी दुकान का डिजिटल साथी."
    if language == "mr-IN" or language == "mr":
        default_text = "नमस्कार! मी वाणी आहे. तुमच्या दुकानाचा डिजिटल सोबती."
    elif language == "en-IN" or language == "en":
        default_text = "Hello! I am Vaani, your digital business assistant."

    text = payload.get("text", default_text)

    if not GnaniClient.config.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Gnani API key is not configured in .env. Please configure GNANI_API_KEY to preview voices."
        )

    # Validate model-voice compatibility
    is_valid, err_msg = VoiceCatalogService.validate_model_and_voice(target_model, voice_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    resolved_voice = VoiceCatalogService.resolve_voice_id(voice_id, target_model=target_model)
    audio_bytes = await GnaniClient.synthesize(
        text=text,
        voice_id=resolved_voice,
        model=target_model,
        language=language,
        speed=speed
    )

    if not audio_bytes:
        raise HTTPException(
            status_code=502,
            detail=f"Gnani TTS failed to generate preview audio with voice '{resolved_voice}' ({target_model})."
        )

    return {
        "voice_id": resolved_voice,
        "model": target_model,
        "text": text,
        "audio_base64": AudioProcessor.encode_base64_audio(audio_bytes),
        "content_type": "audio/wav"
    }

@router.get("/settings/voice")
def get_voice_settings():
    """Get current voice preference, model, and metadata."""
    return VoiceSettingsService.get_full_settings()

@router.put("/settings/voice")
async def update_voice_settings(payload: Dict[str, Any] = Body(...)):
    """
    Persist user selected TTS model, voice ID, language, and speed to database settings.
    Strictly enforces model-voice compatibility.
    """
    voice_id = payload.get("voice_id")
    model = payload.get("model") or payload.get("tts_model")
    language = payload.get("language")
    speech_rate = payload.get("speech_rate") or payload.get("speed")

    if not voice_id:
        raise HTTPException(status_code=422, detail="voice_id is required.")

    try:
        result = VoiceSettingsService.set_voice_settings(
            voice_id=voice_id,
            model=model,
            language=language,
            speech_rate=float(speech_rate) if speech_rate is not None else None
        )
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
    lang_hint = request.headers.get("X-Lang-Hint", "indic-auto")

    valid, err_msg = AudioProcessor.validate_audio_bytes(audio_bytes, filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    stt_res = await GnaniClient.transcribe(
        audio_bytes=audio_bytes,
        filename=filename,
        language_code=lang_hint
    )
    if not stt_res.get("success"):
        raise HTTPException(
            status_code=400 if stt_res.get("error_code") == "AUDIO_TOO_SHORT" else 502,
            detail=stt_res.get("error", "Transcription failed")
        )

    return stt_res

@router.post("/voice/speak")
async def synthesize_speech(payload: Dict[str, Any] = Body(...)):
    """
    Synthesize speech using Gnani Timbre and the selected voice and model.
    """
    text = payload.get("text", "")
    voice_id = payload.get("voice_id") or VoiceSettingsService.get_selected_voice_id()
    model = payload.get("model") or VoiceSettingsService.get_selected_tts_model()
    speed = float(payload.get("speed", VoiceSettingsService.get_selected_speech_rate()))
    language = payload.get("language", "hi-IN")

    if not text.strip():
        raise HTTPException(status_code=422, detail="text is required.")

    # Validate
    is_valid, err_msg = VoiceCatalogService.validate_model_and_voice(model, voice_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    audio_bytes = await GnaniClient.synthesize(
        text=text,
        voice_id=voice_id,
        model=model,
        language=language,
        speed=speed
    )
    if not audio_bytes:
        raise HTTPException(status_code=502, detail="Gnani TTS failed to generate audio.")

    return {
        "text": text,
        "voice_id": voice_id,
        "model": model,
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
    4. Synthesizes speech reply using selected Gnani voice and model.
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
        language_code=lang_hint if lang_hint in ["hi-IN", "mr-IN", "en-IN"] else "indic-auto"
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

    # 4. Synthesize speech using the user's selected Gnani voice & model
    reply_text = result.get("reply_text", "")
    selected_voice = VoiceSettingsService.get_selected_voice_id()
    selected_model = VoiceSettingsService.get_selected_tts_model()
    speed = VoiceSettingsService.get_selected_speech_rate()
    result["voice_id"] = selected_voice
    result["tts_model"] = selected_model
    result["detected_language_code"] = stt_res.get("detected_language_code") or result.get("language")

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

@router.websocket("/voice/stream")
async def websocket_voice_stream(websocket: WebSocket, lang: str = "indic-auto"):
    """
    Real-time bidirectional WebSocket relay between browser and Gnani Prisma v3.0 stream.
    Accepts 16 kHz Mono PCM audio frames and returns real-time transcript events.
    """
    await GnaniClient.streaming.handle_client_stream(
        client_ws=websocket,
        language_code=lang
    )
