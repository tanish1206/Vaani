"""
Voice Settings & Preference Persistence Service.
Saves, retrieves, and validates user-selected Gnani TTS model and voice IDs in SQLite.
Enforces strict model-voice compatibility (e.g. Timbre v3.0 vs Timbre v2.5).
"""

from typing import Dict, Any, Optional
from app.db.session import get_db
from app.services.gnani.voice_catalog import VoiceCatalogService

class VoiceSettingsService:
    """Manages user-selected voice preferences stored in SQLite settings."""

    @classmethod
    def get_selected_tts_model(cls) -> str:
        """Retrieve persisted TTS model or default to timbre-v3.0."""
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = 'tts_model';")
                row = cur.fetchone()
                if row and row[0]:
                    model = row[0].strip().lower()
                    if model in ("timbre-v3.0", "timbre-v2.5"):
                        return model
        except Exception as e:
            print(f"[VoiceSettings] Could not read tts_model from database: {e}")
        return "timbre-v3.0"

    @classmethod
    def get_selected_voice_id(cls) -> str:
        """Retrieve the persisted voice ID for current model or fallback to default."""
        current_model = cls.get_selected_tts_model()
        default_voice = "Shivani" if "v3" in current_model else "Bhavna"

        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = 'voice_id';")
                row = cur.fetchone()
                if row and row[0]:
                    voice = row[0].strip()
                    # Verify voice belongs to current model
                    if VoiceCatalogService.is_voice_supported_by_model(current_model, voice):
                        return VoiceCatalogService.resolve_voice_id(voice, target_model=current_model)
        except Exception as e:
            print(f"[VoiceSettings] Could not read voice_id from database: {e}")
        return default_voice

    @classmethod
    def get_selected_speech_rate(cls) -> float:
        """Retrieve persisted speech rate or default to 1.0."""
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = 'speech_rate';")
                row = cur.fetchone()
                if row and row[0]:
                    return float(row[0])
        except Exception:
            pass
        return 1.0

    @classmethod
    def get_selected_language(cls) -> str:
        """Retrieve persisted preferred language."""
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM settings WHERE key = 'language';")
                row = cur.fetchone()
                if row and row[0]:
                    return row[0].strip()
        except Exception:
            pass
        return "auto"

    @classmethod
    def get_selected_voice_details(cls) -> Dict[str, Any]:
        """Retrieve full metadata for the currently active model and voice."""
        model = cls.get_selected_tts_model()
        voice_id = cls.get_selected_voice_id()
        meta = VoiceCatalogService.get_voice_metadata(voice_id, model=model)
        if meta:
            return {**meta, "selected": True}
        return {
            "id": voice_id,
            "display_name": voice_id,
            "model": model,
            "gender": "Female",
            "primary_language": "hi-IN",
            "primary_language_name": "Hindi / Hinglish",
            "persona": "Standard Voice",
            "selected": True
        }

    @classmethod
    def get_full_settings(cls) -> Dict[str, Any]:
        """Retrieve composite voice settings."""
        model = cls.get_selected_tts_model()
        voice_id = cls.get_selected_voice_id()
        voice_meta = cls.get_selected_voice_details()
        return {
            "tts_model": model,
            "voice_id": voice_id,
            "language": cls.get_selected_language(),
            "speech_rate": cls.get_selected_speech_rate(),
            "voice_details": voice_meta
        }

    @classmethod
    def set_voice_settings(
        cls,
        voice_id: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speech_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate and persist the user's chosen TTS model and voice persona.
        Strictly enforces that the voice belongs to the requested model.
        """
        if not voice_id or not voice_id.strip():
            raise ValueError("voice_id cannot be empty.")

        target_model = (model or cls.get_selected_tts_model()).strip().lower()
        if target_model not in ("timbre-v3.0", "timbre-v2.5"):
            target_model = "timbre-v3.0"

        # Validate voice belongs to model
        resolved_voice = VoiceCatalogService.resolve_voice_id(voice_id, target_model=target_model)
        is_valid, err_msg = VoiceCatalogService.validate_model_and_voice(target_model, resolved_voice)
        if not is_valid:
            raise ValueError(err_msg)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tts_model', ?);", (target_model,))
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('voice_id', ?);", (resolved_voice,))
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('voice_hi', ?);", (resolved_voice,))
            if language:
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('language', ?);", (str(language),))
            if speech_rate is not None:
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('speech_rate', ?);", (str(speech_rate),))

        return {
            "status": "success",
            "tts_model": target_model,
            "voice_id": resolved_voice,
            "message": f"VAANI voice preference updated to {resolved_voice} ({target_model})."
        }

    @classmethod
    def set_selected_voice_id(cls, voice_id: str) -> Dict[str, Any]:
        """Backwards compatible helper."""
        current_model = cls.get_selected_tts_model()
        return cls.set_voice_settings(voice_id=voice_id, model=current_model)
