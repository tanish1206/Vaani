"""
Voice Settings & Preference Persistence Service.
Saves, retrieves, and validates user-selected Gnani voice IDs in SQLite.
"""

from typing import Dict, Any, Optional
from app.db.session import get_db
from app.services.gnani.voices import GnaniVoiceService, GNANI_VOICE_CATALOGUE

class VoiceSettingsService:
    """Manages user-selected voice preferences stored in SQLite settings."""

    @classmethod
    def get_selected_voice_id(cls) -> str:
        """Retrieve the persisted voice ID or fallback to default."""
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = 'voice_id';")
                row = cur.fetchone()
                if row and row[0]:
                    return GnaniVoiceService.resolve_voice_id(row[0])
        except Exception as e:
            print(f"[VoiceSettings] Could not read voice_id from database: {e}")
        return "Bhavna"

    @classmethod
    def get_selected_voice_details(cls) -> Dict[str, Any]:
        """Retrieve full metadata for the currently active voice."""
        current_id = cls.get_selected_voice_id()
        for v in GNANI_VOICE_CATALOGUE:
            if v["id"].lower() == current_id.lower():
                return {**v, "selected": True}
        return {
            "id": current_id,
            "display_name": current_id,
            "language_name": "Hindi / Hinglish",
            "characteristics": "Default voice",
            "selected": True
        }

    @classmethod
    def set_selected_voice_id(cls, voice_id: str) -> Dict[str, Any]:
        """
        Validate and persist the user's selected voice ID.
        Raises ValueError if the voice is not supported by Gnani.
        """
        if not voice_id or not voice_id.strip():
            raise ValueError("Voice ID cannot be empty.")

        resolved_id = GnaniVoiceService.resolve_voice_id(voice_id)
        if not GnaniVoiceService.is_supported(resolved_id):
            raise ValueError(f"Voice '{voice_id}' is not an official supported Gnani voice.")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('voice_id', ?);",
                (resolved_id,)
            )

        return {
            "status": "success",
            "voice_id": resolved_id,
            "message": f"VAANI voice preference updated to {resolved_id}."
        }
