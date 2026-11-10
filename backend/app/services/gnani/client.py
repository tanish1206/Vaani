"""
Unified Gnani Voice AI Service Client Facade.
Provides centralized access to Prisma v3.0 STT, Timbre v3.0/v2.5 TTS, Streaming Relay, and Voice Catalog.
"""

from typing import Dict, Any, Optional, List, AsyncGenerator
from app.services.gnani.config import GnaniConfig
from app.services.gnani.asr import GnaniASRService
from app.services.gnani.tts import GnaniTTSService
from app.services.gnani.voice_catalog import VoiceCatalogService
from app.services.gnani.streaming import GnaniStreamingRelay

class GnaniClient:
    """Unified access point for Gnani Voice Recognition, Synthesis, and Catalogue."""

    config = GnaniConfig
    asr = GnaniASRService
    tts = GnaniTTSService
    catalog = VoiceCatalogService
    streaming = GnaniStreamingRelay

    @classmethod
    async def transcribe(
        cls,
        audio_bytes: bytes,
        filename: str = "turn.webm",
        language_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe speech audio via Gnani Prisma v3.0."""
        return await cls.asr.transcribe(audio_bytes, filename=filename, language_code=language_code)

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
        """Synthesize text into WAV audio using Gnani Timbre."""
        return await cls.tts.synthesize(
            text=text,
            voice_id=voice_id,
            model=model,
            language=language,
            speed=speed,
            sample_rate=sample_rate
        )

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
        """Stream synthesized chunks using Gnani Timbre SSE."""
        async for chunk in cls.tts.stream_synthesize(
            text=text,
            voice_id=voice_id,
            model=model,
            language=language,
            speed=speed,
            sample_rate=sample_rate
        ):
            yield chunk

    @classmethod
    def get_catalog(cls) -> Dict[str, Any]:
        """Get complete two-model voice catalogue."""
        return cls.catalog.get_catalog()

    @classmethod
    def get_voice_options(cls, model: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get voices for the specified or default model."""
        target_model = model or cls.config.get_tts_model()
        return cls.catalog.get_voices_for_model(target_model)

    @classmethod
    def validate_model_and_voice(cls, model: str, voice_id: str) -> tuple:
        """Validate model and voice compatibility."""
        return cls.catalog.validate_model_and_voice(model, voice_id)

    @classmethod
    async def check_health(cls) -> Dict[str, Any]:
        """Check live connectivity and diagnostics."""
        return await cls.config.check_connectivity()
