"""
Gnani Timbre v2.5 Text-to-Speech Adapter.
Implements the exact API contract documented in docs/api.md:
Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Auth: X-API-Key-ID header
"""

from typing import Optional, Dict, Any
import io
import wave
import httpx
from app.config import settings

# Supported voices for Gnani Timbre v2.5 (with graceful legacy aliasing)
VOICE_MAP = {
    "sia": "Bhavna",
    "kabir": "Deepak",
    "priya": "Madhuri",
    "bhavna": "Bhavna",
    "madhuri": "Madhuri",
    "radhika": "Radhika",
    "deepak": "Deepak",
    "nalini": "Nalini",
    "gaurav": "Gaurav"
}

class TimbreTTSClient:
    """Service adapter for Gnani Timbre v2.5 Text-to-Speech."""

    @classmethod
    async def synthesize(cls, text: str, voice: Optional[str] = None,
                         lang: str = "hi") -> Optional[bytes]:
        """
        Synthesize text to speech using Gnani Timbre v2.5 REST endpoint.
        Returns RIFF WAV audio bytes or None if unconfigured/offline.
        """
        if not text or not text.strip():
            return None

        if settings.is_timbre_configured():
            raw_voice = voice or (settings.TTS_VOICE_MR if lang == "mr" else settings.TTS_VOICE_HI)
            target_voice = VOICE_MAP.get(raw_voice.lower(), raw_voice if raw_voice.istitle() else "Bhavna")
            
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
                        content = resp.content
                        # If raw PCM without RIFF header, wrap in standard WAV container
                        if content[:4] != b"RIFF":
                            buf = io.BytesIO()
                            with wave.open(buf, "wb") as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(settings.TTS_SAMPLE_RATE or 44100)
                                wf.writeframes(content)
                            return buf.getvalue()
                        return content
                    elif resp.status_code == 401:
                        print("[Timbre TTS] 401 Unauthorized: Invalid GNANI_API_KEY.")
                    else:
                        print(f"[Timbre TTS] Response {resp.status_code}: {resp.text[:120]}")
            except httpx.TimeoutException:
                print("[Timbre TTS] Request timed out (>10s).")
            except Exception as e:
                print(f"[Timbre TTS] Connection exception: {e}")

        # In browser, Web Speech API provides immediate, zero-latency natural speech fallback
        return None
