"""
Gnani Timbre Text-to-Speech (TTS) Service.
Communicates directly with the official Gnani TTS endpoints:
- REST: POST https://api.vachana.ai/api/v1/tts/inference
- SSE Streaming: POST https://api.vachana.ai/api/v1/tts/sse

Strictly validates model and voice compatibility before dispatching requests.
Wraps raw linear PCM audio into standard RIFF WAV container for immediate browser playback.
"""

import io
import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
import wave
import httpx

from app.services.gnani.config import GnaniConfig
from app.services.gnani.voice_catalog import VoiceCatalogService

logger = logging.getLogger(__name__)


def _wrap_pcm_as_wav(pcm_bytes: bytes, sample_rate: int) -> bytes:
    """Wrap raw 16-bit mono PCM audio in a standard RIFF WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


class GnaniTTSService:
    """Production client for Gnani Timbre Text-to-Speech (REST & SSE)."""

    @classmethod
    def _build_request_parts(
        cls,
        text: str,
        voice_id: Optional[str],
        model: Optional[str],
        language: Optional[str],
        speed: float,
        sample_rate: int,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Resolve model/voice compatibility and construct TTS headers and JSON payload."""
        target_model = model or GnaniConfig.get_tts_model()
        target_voice = VoiceCatalogService.resolve_voice_id(
            voice_id or GnaniConfig.get_default_voice_id(),
            target_model=target_model,
        )

        is_valid, err_msg = VoiceCatalogService.validate_model_and_voice(target_model, target_voice)
        if not is_valid:
            logger.warning("Incompatible model/voice combination: %s", err_msg)
            target_voice = VoiceCatalogService.resolve_voice_id(None, target_model=target_model)

        headers = {
            **GnaniConfig.get_auth_headers(),
            "Content-Type": "application/json",
        }
        lang_code = "hi-IN" if not language or language == "auto" else language

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
                "container": "wav",
            },
        }
        return headers, payload

    @classmethod
    async def synthesize(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        sample_rate: int = 48000,
    ) -> Optional[bytes]:
        """
        Synthesize text into WAV audio bytes using Gnani Timbre.
        Returns WAV binary bytes or None if unconfigured/failed.
        """
        if not text or not text.strip():
            return None

        if not GnaniConfig.is_configured():
            logger.debug("GNANI_API_KEY is not configured. Skipping speech synthesis.")
            return None

        endpoint = GnaniConfig.get_tts_endpoint()
        headers, payload = cls._build_request_parts(text, voice_id, model, language, speed, sample_rate)

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)

                if resp.status_code == 200 and len(resp.content) > 100:
                    content = resp.content
                    return content if content.startswith(b"RIFF") else _wrap_pcm_as_wav(content, sample_rate)
                if resp.status_code == 401:
                    logger.warning("Gnani TTS returned 401 Unauthorized: check GNANI_API_KEY.")
                    return None
                logger.warning("Gnani TTS upstream error %s: %s", resp.status_code, resp.text[:200])
                return None
        except httpx.TimeoutException:
            logger.warning("Gnani TTS request timed out (>14s).")
            return None
        except Exception as exc:
            logger.warning("Gnani TTS connection exception: %s", exc)
            return None

    @classmethod
    async def stream_synthesize(
        cls,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        sample_rate: int = 48000,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream speech chunks using Gnani Timbre SSE endpoint: POST /api/v1/tts/sse."""
        if not text or not text.strip() or not GnaniConfig.is_configured():
            yield {"event": "error", "error": "Unconfigured or empty text"}
            return

        endpoint = GnaniConfig.get_tts_sse_endpoint()
        headers, payload = cls._build_request_parts(text, voice_id, model, language, speed, sample_rate)

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
                            except json.JSONDecodeError:
                                yield {"event": current_event, "data": raw_data}
        except Exception as exc:
            yield {"event": "error", "error": str(exc)}
