"""
Gnani Timbre Text-to-Speech Adapter.
Delegates to GnaniTTSService.
"""

from typing import Optional
from app.services.gnani.tts import GnaniTTSService
from app.services.voice.voice_settings import VoiceSettingsService

class TimbreTTSClient:
    """Service adapter for Gnani Timbre Text-to-Speech."""

    @classmethod
    async def synthesize(cls, text: str, voice: Optional[str] = None,
                         lang: str = "hi") -> Optional[bytes]:
        """
        Synthesize text to speech using Gnani Timbre REST endpoint.
        Uses selected voice if not explicitly passed.
        """
        voice_id = voice or VoiceSettingsService.get_selected_voice_id()
        return await GnaniTTSService.synthesize(text=text, voice_id=voice_id)
