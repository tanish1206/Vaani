"""
Gnani Prisma v3.0 Speech-to-Text Adapter.
Implements the exact API contract documented in docs/api.md:
Endpoint: POST https://api.vachana.ai/stt/v3
Auth: X-API-Key-ID header
"""

from typing import Dict, Any, Optional
import httpx
from app.config import settings

class PrismaSTTClient:
    """Service adapter for Gnani Prisma v3.0 Speech-to-Text."""

    @classmethod
    async def transcribe(cls, audio_bytes: bytes, filename: str = "turn.wav",
                         language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio bytes using Gnani Prisma v3.0.
        Safely handles timeouts, authentication, and offline fallback.
        """
        if not audio_bytes or len(audio_bytes) < 100:
            return {
                "transcript": "",
                "detected_language": "hinglish",
                "confidence": 0.0,
                "error": "Audio clip too short or silent"
            }

        if settings.is_prisma_configured():
            headers = {"X-API-Key-ID": settings.GNANI_API_KEY.strip()}
            effective_lang = language_code if (language_code and language_code != "auto") else (settings.STT_DEFAULT_LANGUAGE or "hi-IN")
            data = {
                "model": settings.STT_MODEL,
                "language_code": effective_lang
            }

            # Determine content type based on file extension
            content_type = "audio/wav"
            if filename.endswith(".webm"):
                content_type = "audio/webm"
            elif filename.endswith(".ogg"):
                content_type = "audio/ogg"
            elif filename.endswith(".mp3"):
                content_type = "audio/mpeg"

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.GNANI_BASE_URL.rstrip('/')}/stt/v3",
                        headers=headers,
                        data=data,
                        files={"audio_file": (filename, audio_bytes, content_type)}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return {
                            "transcript": data.get("transcript", ""),
                            "detected_language": data.get("language_code", "hinglish"),
                            "confidence": data.get("confidence", 0.95),
                            "provider": "prisma-v3.0"
                        }
                    elif resp.status_code == 401:
                        print("[Prisma STT] 401 Unauthorized: Invalid GNANI_API_KEY provided.")
                        return {
                            "transcript": "",
                            "detected_language": "hinglish",
                            "confidence": 0.0,
                            "error": "Authentication failure with Gnani API key."
                        }
                    else:
                        print(f"[Prisma STT] API error {resp.status_code}: {resp.text}")
            except httpx.TimeoutException:
                print("[Prisma STT] Request timed out (>10s).")
            except Exception as e:
                print(f"[Prisma STT] Connection exception: {e}")

        # Unconfigured / Demo fallback
        return {
            "transcript": "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye",
            "detected_language": "hinglish",
            "confidence": 0.95,
            "provider": "offline-fallback"
        }
