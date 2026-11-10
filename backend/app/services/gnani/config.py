"""
Gnani Voice AI Service Configuration.
Loads, validates, and manages connectivity status for Gnani ASR, TTS, and Voice options.
"""

from typing import Dict, Any, Optional
import httpx
from app.config import settings

class GnaniConfig:
    """Manages Gnani provider settings, endpoints, and live health diagnostics."""

    @classmethod
    def get_api_key(cls) -> str:
        return settings.GNANI_API_KEY.strip() if settings.GNANI_API_KEY else ""

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def get_asr_endpoint(cls) -> str:
        if hasattr(settings, "GNANI_ASR_ENDPOINT") and settings.GNANI_ASR_ENDPOINT:
            return settings.GNANI_ASR_ENDPOINT
        return f"{settings.GNANI_BASE_URL.rstrip('/')}/stt/v3"

    @classmethod
    def get_tts_endpoint(cls) -> str:
        if hasattr(settings, "GNANI_TTS_ENDPOINT") and settings.GNANI_TTS_ENDPOINT:
            return settings.GNANI_TTS_ENDPOINT
        return f"{settings.GNANI_BASE_URL.rstrip('/')}/api/v1/tts/inference"

    @classmethod
    def get_voice_list_endpoint(cls) -> str:
        if hasattr(settings, "GNANI_VOICE_LIST_ENDPOINT") and settings.GNANI_VOICE_LIST_ENDPOINT:
            return settings.GNANI_VOICE_LIST_ENDPOINT
        return f"{settings.GNANI_BASE_URL.rstrip('/')}/api/v1/tts/voices"

    @classmethod
    def get_stt_model(cls) -> str:
        return getattr(settings, "STT_MODEL", "prisma-v3.0")

    @classmethod
    def get_tts_model(cls) -> str:
        return getattr(settings, "TTS_MODEL", "timbre-v2.5")

    @classmethod
    def get_default_voice_id(cls) -> str:
        return getattr(settings, "GNANI_DEFAULT_VOICE_ID", "Bhavna")

    @classmethod
    def get_auth_headers(cls) -> Dict[str, str]:
        key = cls.get_api_key()
        if not key:
            return {}
        return {"X-API-Key-ID": key}

    @classmethod
    async def check_connectivity(cls) -> Dict[str, Any]:
        """
        Evaluate actual service status without simulated results:
        Returns:
          - CONFIGURATION_MISSING: Key not provided in .env
          - CONNECTED: Endpoint reachable and credentials accepted
          - AUTHENTICATION_FAILED: Key rejected (401)
          - SERVICE_UNAVAILABLE: Connection timeout or upstream error
        """
        if not cls.is_configured():
            return {
                "status": "CONFIGURATION_MISSING",
                "message": "Gnani API key is not configured. Please set GNANI_API_KEY in .env.",
                "has_api_key": False,
                "endpoints": {
                    "asr": cls.get_asr_endpoint(),
                    "tts": cls.get_tts_endpoint()
                }
            }

        headers = cls.get_auth_headers()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # Test ping against STT endpoint
                resp = await client.post(cls.get_asr_endpoint(), headers=headers)
                if resp.status_code == 401:
                    return {
                        "status": "AUTHENTICATION_FAILED",
                        "message": "Gnani API key was rejected by api.vachana.ai (401 Unauthorized).",
                        "has_api_key": True
                    }
                elif resp.status_code in (200, 400, 422):
                    # 422/400 means authenticated and reached FastAPI endpoint validator
                    return {
                        "status": "CONNECTED",
                        "message": "Connected to Gnani Sovereign Voice Infrastructure.",
                        "has_api_key": True,
                        "stt_model": cls.get_stt_model(),
                        "tts_model": cls.get_tts_model(),
                        "default_voice": cls.get_default_voice_id()
                    }
                else:
                    return {
                        "status": "SERVICE_UNAVAILABLE",
                        "message": f"Gnani service returned status {resp.status_code}.",
                        "has_api_key": True
                    }
        except httpx.TimeoutException:
            return {
                "status": "SERVICE_UNAVAILABLE",
                "message": "Connection to Gnani timed out (>4s).",
                "has_api_key": True
            }
        except Exception as e:
            return {
                "status": "SERVICE_UNAVAILABLE",
                "message": f"Connectivity check error: {str(e)}",
                "has_api_key": True
            }
