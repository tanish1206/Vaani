"""
Gnani Timbre v2.5 Text-to-Speech Adapter.
Posts text to https://api.vachana.ai/api/v1/tts/inference.
"""

from typing import Optional
import httpx
from app.config import settings

class TimbreTTSClient:
    TTS_URL = f"{settings.GNANI_BASE_URL.rstrip('/')}/api/v1/tts/inference"

    @classmethod
    async def synthesize(cls, text: str, voice: str = "sia",
                         lang: str = "hi") -> Optional[bytes]:
        """Synthesize spoken audio with Gnani Timbre v2.5."""
        if settings.GNANI_API_KEY and settings.GNANI_API_KEY != "dummy_key_local":
            headers = {
                "X-API-Key-ID": settings.GNANI_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "voice": voice,
                "model": settings.TTS_MODEL or "timbre-v2.5"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(cls.TTS_URL, headers=headers, json=payload)
                    if resp.status_code == 200:
                        return resp.content
            except Exception as e:
                print(f"[Timbre] Synthesis failed ({e}), client will use Web Speech synthesis.")

        return None

