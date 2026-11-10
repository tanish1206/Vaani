"""
Gnani Timbre Text-to-Speech (TTS) Service.
Communicates directly with the official Gnani TTS endpoint: POST https://api.vachana.ai/api/v1/tts/inference.
Wraps raw linear PCM audio into standard RIFF WAV container for immediate browser playback.
"""

from typing import Optional, Dict, Any
import io
import wave
import httpx
from app.services.gnani.config import GnaniConfig
from app.services.gnani.voices import GnaniVoiceService

class GnaniTTSService:
    """Production client for Gnani Timbre Text-to-Speech."""

    @classmethod
    async def synthesize(cls, text: str, voice_id: Optional[str] = None,
                          sample_rate: int = 44100) -> Optional[bytes]:
        """
        Synthesize text into WAV audio bytes using Gnani Timbre.
        Returns WAV binary bytes or None if unconfigured/failed.
        """
        if not text or not text.strip():
            return None

        if not GnaniConfig.is_configured():
            print("[Gnani TTS] GNANI_API_KEY is not configured in .env. Skipping speech synthesis.")
            return None

        target_voice = GnaniVoiceService.resolve_voice_id(voice_id or GnaniConfig.get_default_voice_id())
        model = GnaniConfig.get_tts_model()
        endpoint = GnaniConfig.get_tts_endpoint()
        headers = {
            **GnaniConfig.get_auth_headers(),
            "Content-Type": "application/json"
        }

        payload = {
            "text": text.strip(),
            "voice": target_voice,
            "model": model,
            "audio_config": {
                "sample_rate": sample_rate,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)

                if resp.status_code == 200 and len(resp.content) > 100:
                    content = resp.content
                    # If raw PCM, wrap in standard RIFF WAV header
                    if not content.startswith(b"RIFF"):
                        buf = io.BytesIO()
                        with wave.open(buf, "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)
                            wf.setframerate(sample_rate)
                            wf.writeframes(content)
                        return buf.getvalue()
                    return content
                elif resp.status_code == 401:
                    print("[Gnani TTS] 401 Unauthorized: Invalid GNANI_API_KEY in .env.")
                    return None
                elif resp.status_code == 400:
                    print(f"[Gnani TTS] 400 Bad Request: {resp.text[:160]}")
                    return None
                else:
                    print(f"[Gnani TTS] Upstream error {resp.status_code}: {resp.text[:160]}")
                    return None
        except httpx.TimeoutException:
            print("[Gnani TTS] Request timed out (>12s).")
            return None
        except Exception as e:
            print(f"[Gnani TTS] Connection exception: {e}")
            return None
