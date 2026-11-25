"""
Gnani Prisma v3.0 Automatic Speech Recognition (ASR) Service.
Communicates directly with the official Gnani STT endpoint: POST https://api.vachana.ai/stt/v3.
Zero mock data: Only returns genuine transcripts or explicit error states.
Standardizes incoming audio streams to 16 kHz Mono WAV for guaranteed Gnani compatibility.
"""

from typing import Any, Dict, Optional
import httpx

from app.services.gnani.config import GnaniConfig
from app.services.voice.audio_processor import AudioProcessor


def _asr_error(error: str, error_code: str) -> Dict[str, Any]:
    """Return a standardized ASR error payload."""
    return {
        "success": False,
        "transcript": "",
        "language_code": "unknown",
        "confidence": 0.0,
        "error": error,
        "error_code": error_code,
    }

class GnaniASRService:
    """Production client for Gnani Prisma v3.0 Speech-to-Text."""

    @classmethod
    async def transcribe(cls, audio_bytes: bytes, filename: str = "turn.webm",
                          language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe user recorded audio via Gnani Prisma v3.0.
        Automatically normalizes incoming browser containers (WebM, Ogg, MP4, AAC)
        into 16 kHz Mono RIFF WAV before uploading to https://api.vachana.ai/stt/v3.

        Returns:
            {
                "success": bool,
                "transcript": str,
                "language_code": str,
                "confidence": float,
                "error": Optional[str],
                "error_code": Optional[str]
            }
        """
        if not audio_bytes or len(audio_bytes) < 120:
            return _asr_error(
                "Audio recording is empty or too short. Please speak clearly into the microphone.",
                "AUDIO_TOO_SHORT",
            )

        if not GnaniConfig.is_configured():
            return _asr_error(
                "Gnani API key is not configured. Please add GNANI_API_KEY in .env.",
                "CONFIGURATION_MISSING",
            )

        # Normalize incoming audio container to Gnani-supported 16 kHz Mono RIFF WAV
        clean_bytes, clean_filename, clean_content_type = AudioProcessor.ensure_gnani_compatible_wav(
            audio_bytes=audio_bytes,
            filename=filename,
        )

        headers = GnaniConfig.get_auth_headers()
        endpoint = GnaniConfig.get_asr_endpoint()
        model = GnaniConfig.get_stt_model()

        data: Dict[str, str] = {
            "model": model,
            "format": "transcribe",
            "language_code": language_code if (language_code and language_code != "auto") else "indic-auto",
        }
        files = {"audio_file": (clean_filename, clean_bytes, clean_content_type)}

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                resp = await client.post(endpoint, headers=headers, data=data, files=files)

                if resp.status_code == 200:
                    payload = resp.json()
                    lang = (
                        payload.get("detected_language_code")
                        or payload.get("language_code")
                        or (language_code if language_code != "auto" else "hi-IN")
                    )
                    return {
                        "success": True,
                        "transcript": payload.get("transcript", "").strip(),
                        "language_code": lang,
                        "detected_language_code": lang,
                        "confidence": float(payload.get("confidence", 0.95)),
                        "request_id": payload.get("request_id", ""),
                        "latency": payload.get("end_to_end_latency") or payload.get("processing_time"),
                        "model": payload.get("model", model),
                        "provider": "gnani-prisma-v3.0",
                    }
                if resp.status_code == 400:
                    try:
                        err_json = resp.json()
                        err_detail = err_json.get("error", {})
                        msg = err_detail.get("message") if isinstance(err_detail, dict) else str(err_json)
                        err_type = err_detail.get("type", "BAD_REQUEST") if isinstance(err_detail, dict) else "BAD_REQUEST"
                    except Exception:
                        msg = resp.text[:140]
                        err_type = "BAD_REQUEST"
                    return _asr_error(f"Gnani ASR rejected request: {msg}", err_type)
                if resp.status_code == 401:
                    return _asr_error(
                        "Gnani API key is invalid or unauthorized (401). Please check GNANI_API_KEY in .env.",
                        "AUTHENTICATION_FAILED",
                    )
                if resp.status_code == 429:
                    return _asr_error(
                        "Gnani rate limit reached. Please wait a moment before speaking again.",
                        "RATE_LIMITED",
                    )
                return _asr_error(
                    f"Gnani ASR returned status {resp.status_code}: {resp.text[:140]}",
                    f"UPSTREAM_ERROR_{resp.status_code}",
                )
        except httpx.TimeoutException:
            return _asr_error(
                "Gnani ASR request timed out. Please check network connectivity.",
                "TIMEOUT",
            )
        except Exception as exc:
            return _asr_error(f"Gnani connection error: {exc}", "CONNECTION_ERROR")
