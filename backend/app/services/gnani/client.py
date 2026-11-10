"""
Unified Gnani Voice AI Service Client Facade.
"""

from typing import Dict, Any, Optional, List
from app.services.gnani.config import GnaniConfig
from app.services.gnani.asr import GnaniASRService
from app.services.gnani.tts import GnaniTTSService
from app.services.gnani.voices import GnaniVoiceService

class GnaniClient:
    """Unified access point for Gnani Voice Recognition, Synthesis, and Voices."""

    config = GnaniConfig
    asr = GnaniASRService
    tts = GnaniTTSService
    voices = GnaniVoiceService

    @classmethod
    async def transcribe(cls, audio_bytes: bytes, filename: str = "turn.webm",
                          language_code: Optional[str] = None) -> Dict[str, Any]:
        return await cls.asr.transcribe(audio_bytes, filename=filename, language_code=language_code)

    @classmethod
    async def synthesize(cls, text: str, voice_id: Optional[str] = None,
                          sample_rate: int = 44100) -> Optional[bytes]:
        return await cls.tts.synthesize(text, voice_id=voice_id, sample_rate=sample_rate)

    @classmethod
    async def get_voice_options(cls) -> List[Dict[str, Any]]:
        return await cls.voices.get_available_voices()

    @classmethod
    async def check_health(cls) -> Dict[str, Any]:
        return await cls.config.check_connectivity()
