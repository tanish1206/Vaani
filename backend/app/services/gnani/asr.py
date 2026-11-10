"""
Gnani Prisma v3.0 Automatic Speech Recognition (ASR) Service.
Communicates directly with the official Gnani STT endpoint: POST https://api.vachana.ai/stt/v3.
Zero mock data: Only returns genuine transcripts or explicit error states.
"""

from typing import Dict, Any, Optional
import httpx
from app.services.gnani.config import GnaniConfig
from app.services.gnani.exceptions import (
    GnaniConfigurationMissingError,
    GnaniAuthError,
    GnaniRateLimitError,
    GnaniTimeoutError,
    GnaniError
)

class GnaniASRService:
    """Production client for Gnani Prisma v3.0 Speech-to-Text."""

    @classmethod
    async def transcribe(cls, audio_bytes: bytes, filename: str = "turn.webm",
                          language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe user recorded audio via Gnani Prisma v3.0.
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
            return {
                "success": False,
                "transcript": "",
                "language_code": "unknown",
                "confidence": 0.0,
                "error": "Audio recording is empty or too short. Please speak clearly into the microphone.",
                "error_code": "AUDIO_TOO_SHORT"
            }

        if not GnaniConfig.is_configured():
            return {
                "success": False,
                "transcript": "",
                "language_code": "unknown",
                "confidence": 0.0,
                "error": "Gnani API key is not configured. Please add GNANI_API_KEY in .env.",
                "error_code": "CONFIGURATION_MISSING"
            }

        headers = GnaniConfig.get_auth_headers()
        endpoint = GnaniConfig.get_asr_endpoint()
        model = GnaniConfig.get_stt_model()

        # Official Gnani Prisma v3.0 parameters
        data: Dict[str, str] = {
            "model": model,
            "format": "transcribe"
        }
        if language_code and language_code != "auto":
            data["language_code"] = language_code
        else:
            data["language_code"] = "indic-auto"

        # Determine MIME type
        content_type = "audio/webm"
        if filename.endswith(".wav"):
            content_type = "audio/wav"
        elif filename.endswith(".ogg"):
            content_type = "audio/ogg"
        elif filename.endswith(".mp3"):
            content_type = "audio/mpeg"

        files = {"audio_file": (filename, audio_bytes, content_type)}

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                resp = await client.post(endpoint, headers=headers, data=data, files=files)

                if resp.status_code == 200:
                    payload = resp.json()
                    transcript = payload.get("transcript", "").strip()
                    lang = (
                        payload.get("detected_language_code")
                        or payload.get("language_code")
                        or (language_code if language_code != "auto" else "hi-IN")
                    )
                    confidence = float(payload.get("confidence", 0.95))
                    request_id = payload.get("request_id", "")
                    latency = payload.get("end_to_end_latency") or payload.get("processing_time")
                    return {
                        "success": True,
                        "transcript": transcript,
                        "language_code": lang,
                        "detected_language_code": lang,
                        "confidence": confidence,
                        "request_id": request_id,
                        "latency": latency,
                        "model": payload.get("model", model),
                        "provider": "gnani-prisma-v3.0"
                    }
                elif resp.status_code == 401:
                    return {
                        "success": False,
                        "transcript": "",
                        "language_code": "unknown",
                        "confidence": 0.0,
                        "error": "Gnani API key is invalid or unauthorized (401). Please check GNANI_API_KEY in .env.",
                        "error_code": "AUTHENTICATION_FAILED"
                    }
                elif resp.status_code == 429:
                    return {
                        "success": False,
                        "transcript": "",
                        "language_code": "unknown",
                        "confidence": 0.0,
                        "error": "Gnani rate limit reached. Please wait a moment before speaking again.",
                        "error_code": "RATE_LIMITED"
                    }
                else:
                    return {
                        "success": False,
                        "transcript": "",
                        "language_code": "unknown",
                        "confidence": 0.0,
                        "error": f"Gnani ASR returned status {resp.status_code}: {resp.text[:140]}",
                        "error_code": f"UPSTREAM_ERROR_{resp.status_code}"
                    }
        except httpx.TimeoutException:
            return {
                "success": False,
                "transcript": "",
                "language_code": "unknown",
                "confidence": 0.0,
                "error": "Gnani ASR request timed out. Please check network connectivity.",
                "error_code": "TIMEOUT"
            }
        except Exception as e:
            return {
                "success": False,
                "transcript": "",
                "language_code": "unknown",
                "confidence": 0.0,
                "error": f"Gnani connection error: {str(e)}",
                "error_code": "CONNECTION_ERROR"
            }
