"""
Audio Stream and Buffer Processor.
Validates audio size, format, and handles temporary in-memory playback payloads.
Transcodes incoming browser audio streams (WebM, Ogg, MP4, AAC) into standard 16 kHz Mono RIFF WAV
for official Gnani Prisma v3.0 STT compatibility.

STRICT PRIVACY: Never persists raw user microphone recordings to disk.
"""

from typing import Tuple
import base64
import io
import logging
import wave

logger = logging.getLogger(__name__)

try:
    import av
    HAS_AV = True
except Exception:
    HAS_AV = False

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB cap (matches Gnani limits)
TARGET_SAMPLE_RATE = 16000

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

        valid_exts = (".webm", ".wav", ".ogg", ".mp3", ".m4a", ".aac", ".flac", ".mp4")
        if not any(filename.lower().endswith(ext) for ext in valid_exts):
            return False, f"Unsupported audio container format. Allowed: {', '.join(valid_exts)}"

        return True, "OK"

    @classmethod
    def ensure_gnani_compatible_wav(cls, audio_bytes: bytes, filename: str = "turn.webm") -> Tuple[bytes, str, str]:
        """
        Normalize any incoming audio stream (WebM Opus, OGG, AAC, MP4, MP3, WAV)
        into a standard 16 kHz Mono 16-bit PCM RIFF WAV container accepted by Gnani Prisma STT.

        Returns:
            Tuple[bytes, str, str]: (wav_bytes, "turn.wav", "audio/wav")

        STRICT PRIVACY: Purely in-memory using io.BytesIO. Never touches disk.
        """
        if not audio_bytes or len(audio_bytes) < 44:
            return audio_bytes, filename, "audio/wav"

        # Check if already a valid 16 kHz Mono 16-bit WAV
        if audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:16]:
            try:
                with wave.open(io.BytesIO(audio_bytes), "rb") as w:
                    if w.getnchannels() == 1 and w.getframerate() == TARGET_SAMPLE_RATE and w.getsampwidth() == 2:
                        return audio_bytes, "turn.wav", "audio/wav"
            except Exception:
                pass  # Fall through to transcode

        # Use PyAV (ffmpeg) in-memory decoding and resampling if available
        if HAS_AV:
            try:
                input_buf = io.BytesIO(audio_bytes)
                output_buf = io.BytesIO()

                with av.open(input_buf) as container:
                    audio_streams = [s for s in container.streams if s.type == "audio"]
                    if not audio_streams:
                        # If no audio stream found, fallback to original if format is allowed by Gnani
                        if any(filename.endswith(ext) for ext in (".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a")):
                            return audio_bytes, filename, "audio/wav" if filename.endswith(".wav") else "audio/ogg"
                        return audio_bytes, "turn.wav", "audio/wav"

                    stream = audio_streams[0]
                    resampler = av.AudioResampler(
                        format="s16",
                        layout="mono",
                        rate=TARGET_SAMPLE_RATE
                    )

                    with wave.open(output_buf, "wb") as wav_out:
                        wav_out.setnchannels(1)
                        wav_out.setsampwidth(2)
                        wav_out.setframerate(TARGET_SAMPLE_RATE)

                        for frame in container.decode(stream):
                            for rf in resampler.resample(frame):
                                wav_out.writeframes(rf.to_ndarray().tobytes())

                        # Flush resampler buffer
                        for rf in resampler.resample(None):
                            wav_out.writeframes(rf.to_ndarray().tobytes())

                wav_bytes = output_buf.getvalue()
                if len(wav_bytes) > 44:  # Valid WAV header is 44 bytes
                    return wav_bytes, "turn.wav", "audio/wav"
            except Exception as exc:
                logger.warning("Audio transcoding failed (%s). Attempting passthrough fallback.", exc)

        # Fallback: if already a recognized gnani format, pass through with proper MIME
        ext = filename.split(".")[-1].lower() if "." in filename else "wav"
        mime_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "aac": "audio/aac",
            "m4a": "audio/m4a"
        }
        if ext in mime_map:
            return audio_bytes, filename, mime_map[ext]

        return audio_bytes, "turn.wav", "audio/wav"

    @classmethod
    def encode_base64_audio(cls, audio_bytes: bytes) -> str:
        """Encode audio bytes into base64 string for immediate JSON transport."""
        return base64.b64encode(audio_bytes).decode("ascii")
