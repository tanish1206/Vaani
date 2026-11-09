"""
Gnani Timbre v2.5 Text-to-Speech Adapter.
Implements the exact API contract documented in docs/api.md:
Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Auth: X-API-Key-ID header
"""

from typing import Optional, Dict, Any
import httpx
from app.config import settings

class TimbreTTSClient:
    """Service adapter for Gnani Timbre v2.5 Text-to-Speech."""

    @classmethod
    async def synthesize(cls, text: str, voice: Optional[str] = None,
                         lang: str = "hi") -> Optional[bytes]:
        """
        Synthesize text to speech using Gnani Timbre v2.5 REST endpoint.
        Returns raw audio bytes or None if unconfigured/offline.
        """
        if not text or not text.strip():
            return None

        if settings.is_timbre_configured():
            target_voice = voice or (settings.TTS_VOICE_MR if lang == "mr" else settings.TTS_VOICE_HI)
            headers = {
                "X-API-Key-ID": settings.GNANI_API_KEY.strip(),
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "voice": target_voice,
                "model": settings.TTS_MODEL or "timbre-v2.5"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.GNANI_BASE_URL.rstrip('/')}/api/v1/tts/inference",
                        headers=headers,
                        json=payload
                    )
                    if resp.status_code == 200 and len(resp.content) > 100:
                        return resp.content
                    elif resp.status_code == 401:
                        print("[Timbre TTS] 401 Unauthorized: Invalid GNANI_API_KEY.")
            except httpx.TimeoutException:
                print("[Timbre TTS] Request timed out (>10s).")
            except Exception as e:
                print(f"[Timbre TTS] Connection exception: {e}")

        # In browser, Web Speech API provides immediate, zero-latency natural speech fallback
        return None
