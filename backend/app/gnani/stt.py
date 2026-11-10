"""
Gnani Prisma v3.0 Speech-to-Text Adapter.
Delegates to GnaniASRService.
STRICT ZERO DEMO DATA: Never returns fake or predefined sentences.
"""

from typing import Dict, Any, Optional
from app.services.gnani.asr import GnaniASRService

class PrismaSTTClient:
    """Service adapter for Gnani Prisma v3.0 Speech-to-Text."""

    @classmethod
    async def transcribe(cls, audio_bytes: bytes, filename: str = "turn.webm",
                         language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio bytes using Gnani Prisma v3.0.
        Returns actual transcript or explicit error state.
        """
        return await GnaniASRService.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language_code=language_code
        )
