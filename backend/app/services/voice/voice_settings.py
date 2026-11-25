"""
Voice Settings & Preference Persistence Service.
Saves, retrieves, and validates user-selected Gnani TTS model and voice IDs in SQLite.
Enforces strict model-voice compatibility (e.g. Timbre v3.0 vs Timbre v2.5).
"""

import logging
from typing import Any, Dict, Optional

from app.db.session import get_db
from app.services.gnani.voice_catalog import VoiceCatalogService

logger = logging.getLogger(__name__)


class VoiceSettingsService:
    """Manages user-selected voice preferences stored in SQLite settings."""

    @classmethod
    def _load_settings_map(cls) -> Dict[str, str]:
        """Load voice-related settings in a single SQLite roundtrip."""
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT key, value FROM settings WHERE key IN ('tts_model', 'voice_id', 'speech_rate', 'language');"
                )
                return {row["key"]: row["value"] for row in cur.fetchall() if row["value"] is not None}
        except Exception as exc:
            logger.warning("Could not read voice settings from database: %s", exc)
            return {}

    @classmethod
    def _resolve_model(cls, settings_map: Dict[str, str]) -> str:
        model = settings_map.get("tts_model", "").strip().lower()
        return model if model in ("timbre-v3.0", "timbre-v2.5") else "timbre-v3.0"

    @classmethod
    def _resolve_voice(cls, settings_map: Dict[str, str], current_model: str) -> str:
        default_voice = "Shivani" if "v3" in current_model else "Bhavna"
        voice = settings_map.get("voice_id", "").strip()
        if voice and VoiceCatalogService.is_voice_supported_by_model(current_model, voice):
            return VoiceCatalogService.resolve_voice_id(voice, target_model=current_model)
        return default_voice

    @classmethod
    def get_selected_tts_model(cls) -> str:
        """Retrieve persisted TTS model or default to timbre-v3.0."""
        return cls._resolve_model(cls._load_settings_map())

    @classmethod
    def get_selected_voice_id(cls) -> str:
        """Retrieve the persisted voice ID for current model or fallback to default."""
        settings_map = cls._load_settings_map()
        return cls._resolve_voice(settings_map, cls._resolve_model(settings_map))

    @classmethod
    def get_selected_speech_rate(cls) -> float:
        """Retrieve persisted speech rate or default to 1.0."""
        raw = cls._load_settings_map().get("speech_rate")
        try:
            return float(raw) if raw else 1.0
        except ValueError:
            return 1.0

    @classmethod
    def get_selected_language(cls) -> str:
        """Retrieve persisted preferred language."""
        lang = cls._load_settings_map().get("language", "").strip()
        return lang or "auto"

    @classmethod
    def _build_voice_details(cls, model: str, voice_id: str) -> Dict[str, Any]:
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
            "selected": True,
        }

    @classmethod
    def get_selected_voice_details(cls) -> Dict[str, Any]:
        """Retrieve full metadata for the currently active model and voice."""
        settings_map = cls._load_settings_map()
        model = cls._resolve_model(settings_map)
        voice_id = cls._resolve_voice(settings_map, model)
        return cls._build_voice_details(model, voice_id)

    @classmethod
    def get_full_settings(cls) -> Dict[str, Any]:
        """Retrieve composite voice settings in a single DB query."""
        settings_map = cls._load_settings_map()
        model = cls._resolve_model(settings_map)
        voice_id = cls._resolve_voice(settings_map, model)
        raw_rate = settings_map.get("speech_rate")
        try:
            speech_rate = float(raw_rate) if raw_rate else 1.0
        except ValueError:
            speech_rate = 1.0

        return {
            "tts_model": model,
            "voice_id": voice_id,
            "language": settings_map.get("language", "").strip() or "auto",
            "speech_rate": speech_rate,
            "voice_details": cls._build_voice_details(model, voice_id),
        }

    @classmethod
    def set_voice_settings(
        cls,
        voice_id: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        speech_rate: Optional[float] = None,
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
            "message": f"VAANI voice preference updated to {resolved_voice} ({target_model}).",
        }

    @classmethod
    def set_selected_voice_id(cls, voice_id: str) -> Dict[str, Any]:
        """Backwards compatible helper."""
        return cls.set_voice_settings(voice_id=voice_id, model=cls.get_selected_tts_model())
