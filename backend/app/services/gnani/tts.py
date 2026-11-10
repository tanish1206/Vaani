"""
Gnani Timbre Text-to-Speech (TTS) Service.
Communicates directly with the official Gnani TTS endpoints:
- REST: POST https://api.vachana.ai/api/v1/tts/inference
- SSE Streaming: POST https://api.vachana.ai/api/v1/tts/sse

Strictly validates model and voice compatibility before dispatching requests.
Wraps raw linear PCM audio into standard RIFF WAV container for immediate browser playback.
"""

from typing import Optional, Dict, Any, AsyncGenerator, Tuple
import io
import json
import wave
import httpx
from app.services.gnani.config import GnaniConfig
from app.services.gnani.voice_catalog import VoiceCatalogService

class GnaniTTSService:
    """Production client for Gnani Timbre Text-to-Speech (REST & SSE)."""

    @classmethod
    async def synthesize(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        sample_rate: int = 48000
    ) -> Optional[bytes]:
        """
        Synthesize text into WAV audio bytes using Gnani Timbre.
        Returns WAV binary bytes or None if unconfigured/failed.
        """
        if not text or not text.strip():
            return None

        if not GnaniConfig.is_configured():
            print("[Gnani TTS] GNANI_API_KEY is not configured in .env. Skipping speech synthesis.")
            return None

        target_model = model or GnaniConfig.get_tts_model()
        target_voice = VoiceCatalogService.resolve_voice_id(
            voice_id or GnaniConfig.get_default_voice_id(),
            target_model=target_model
        )

        # Enforce model and voice compatibility
        is_valid, err_msg = VoiceCatalogService.validate_model_and_voice(target_model, target_voice)
        if not is_valid:
            print(f"[Gnani TTS] Incompatible model/voice combination: {err_msg}")
            # Try to resolve to default voice of that model
            target_voice = VoiceCatalogService.resolve_voice_id(None, target_model=target_model)

        endpoint = GnaniConfig.get_tts_endpoint()
        headers = {
            **GnaniConfig.get_auth_headers(),
            "Content-Type": "application/json"
        }

        # Determine target language code
        lang_code = language or "hi-IN"
        if lang_code == "auto":
            lang_code = "hi-IN"

        payload = {
            "text": text.strip(),
            "voice": target_voice,
            "model": target_model,
            "language": lang_code,
            "speed": max(0.5, min(2.0, float(speed))),
            "audio_config": {
                "sample_rate": sample_rate,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
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
                    print(f"[Gnani TTS] 400 Bad Request: {resp.text[:200]}")
                    return None
                else:
                    print(f"[Gnani TTS] Upstream error {resp.status_code}: {resp.text[:200]}")
                    return None
        except httpx.TimeoutException:
            print("[Gnani TTS] Request timed out (>14s).")
            return None
        except Exception as e:
            print(f"[Gnani TTS] Connection exception: {e}")
            return None

    @classmethod
    async def stream_synthesize(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        sample_rate: int = 48000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream speech chunks using Gnani Timbre SSE endpoint: POST /api/v1/tts/sse.
        Yields events:
            {"event": "start", "data": {...}}
            {"event": "chunk", "audio": "<base64>", "chunk_index": int}
            {"event": "complete", "data": {...}}
        """
        if not text or not text.strip() or not GnaniConfig.is_configured():
            yield {"event": "error", "error": "Unconfigured or empty text"}
            return

        target_model = model or GnaniConfig.get_tts_model()
        target_voice = VoiceCatalogService.resolve_voice_id(
            voice_id or GnaniConfig.get_default_voice_id(),
            target_model=target_model
        )

        endpoint = GnaniConfig.get_tts_sse_endpoint()
        headers = {
            **GnaniConfig.get_auth_headers(),
            "Content-Type": "application/json"
        }

        lang_code = language or "hi-IN"
        if lang_code == "auto":
            lang_code = "hi-IN"

        payload = {
            "text": text.strip(),
            "voice": target_voice,
            "model": target_model,
            "language": lang_code,
            "speed": max(0.5, min(2.0, float(speed))),
            "audio_config": {
                "sample_rate": sample_rate,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        yield {"event": "error", "error": f"Upstream error {response.status_code}"}
                        return

                    current_event = "message"
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("event:"):
                            current_event = line.replace("event:", "").strip()
                        elif line.startswith("data:"):
                            raw_data = line.replace("data:", "").strip()
                            try:
                                parsed = json.loads(raw_data)
                                yield {"event": current_event, **parsed}
                            except Exception:
                                yield {"event": current_event, "data": raw_data}
        except Exception as e:
            yield {"event": "error", "error": str(e)}
