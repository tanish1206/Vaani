"""
Legacy Gnani Voice Catalogue compatibility wrapper.
Delegates directly to VoiceCatalogService so there is a single source of truth.
"""

from typing import Any, Dict, List, Optional

from app.services.gnani.voice_catalog import (
    TIMBRE_V25_VOICES,
    TIMBRE_V3_VOICES,
    VOICE_ALIASES,
    VoiceCatalogService,
)

GNANI_VOICE_CATALOGUE: List[Dict[str, Any]] = TIMBRE_V3_VOICES + TIMBRE_V25_VOICES


class GnaniVoiceService:
    """Backwards-compatible facade over VoiceCatalogService."""

    @classmethod
    def get_available_voices(cls) -> List[Dict[str, Any]]:
        """Retrieve supported voice options from the unified verified catalogue."""
        return GNANI_VOICE_CATALOGUE

    @classmethod
    def resolve_voice_id(cls, voice_id: Optional[str]) -> str:
        """Resolve an input voice ID or alias to an official Gnani voice name."""
        return VoiceCatalogService.resolve_voice_id(voice_id)

    @classmethod
    def is_supported(cls, voice_id: str) -> bool:
        """Check whether a voice is supported across Timbre models."""
        if not voice_id:
            return False
        lower = voice_id.strip().lower()
        if lower in VOICE_ALIASES:
            return True
        return any(v["id"].lower() == lower for v in GNANI_VOICE_CATALOGUE)
