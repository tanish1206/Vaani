"""
Audio Stream and Buffer Processor.
Validates audio size, format, and handles temporary in-memory playback payloads.
STRICT PRIVACY: Never persists raw user microphone recordings to disk.
"""

from typing import Tuple
import base64

MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB cap

class AudioProcessor:
    """Validates and processes audio streams purely in-memory."""

    @classmethod
    def validate_audio_bytes(cls, audio_bytes: bytes, filename: str) -> Tuple[bool, str]:
        """Validate audio upload against security and size constraints."""
        if not audio_bytes:
            return False, "Audio payload is empty."
        if len(audio_bytes) < 100:
            return False, "Audio recording is too short (empty recording)."
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            return False, f"Audio file exceeds maximum size limit ({MAX_AUDIO_BYTES // (1024*1024)} MB)."

        valid_exts = (".webm", ".wav", ".ogg", ".mp3", ".m4a")
        if not any(filename.lower().endswith(ext) for ext in valid_exts):
            return False, f"Unsupported audio container format. Allowed: {', '.join(valid_exts)}"

        return True, "OK"

    @classmethod
    def encode_base64_audio(cls, audio_bytes: bytes) -> str:
        """Encode audio bytes into base64 string for immediate JSON transport."""
        return base64.b64encode(audio_bytes).decode("ascii")
