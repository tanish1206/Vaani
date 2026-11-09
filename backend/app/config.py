"""
Configuration settings and centralized configuration loader for VAANI.
Validates environment parameters, masks credentials, and exposes
service readiness diagnostics safely.
"""

from typing import Union, Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def mask_credential(val: Optional[str]) -> str:
    """Safely mask API key or secret for public display in settings/health."""
    if not val or not val.strip():
        return "Not Configured"
    v = val.strip()
    if len(v) <= 8:
        return "****"
    return f"{v[:4]}****{v[-4:]}"

class Settings(BaseSettings):
    APP_NAME: str = "VAANI"
    TAGLINE: str = "Boliye. Vaani Sambhal Legi."
    VERSION: str = "2.0.0"
    DEBUG: Union[bool, str] = True
    DEMO_MODE: Union[bool, str] = True
    
    @field_validator("DEBUG", mode="before")
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "debug")
        return bool(v)

    @field_validator("DEMO_MODE", mode="before")
    def parse_demo(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "demo")
        return bool(v)
    
    # Database Path
    DB_PATH: str = str(BASE_DIR / "data" / "vaani.db")
    
    # Gnani Services (External Sovereign Indian AI)
    GNANI_API_KEY: str = ""
    GNANI_BASE_URL: str = "https://api.vachana.ai"
    
    # STT (Prisma v3.0)
    STT_MODEL: str = "prisma-v3.0"
    STT_DEFAULT_LANGUAGE: str = "hi-IN"
    
    # TTS (Timbre v2.5)
    TTS_MODEL: str = "timbre-v2.5"
    TTS_VOICE_HI: str = "sia"
    TTS_VOICE_MR: str = "sia"
    TTS_VOICE_EN: str = "sia"
    TTS_SAMPLE_RATE: int = 44100
    
    # Evon LLM (Reasoning & Intent Extraction)
    EVON_ENABLED: bool = True
    EVON_BASE_URL: str = "http://localhost:8001"
    EVON_MODEL: str = "gnani/gnani-evon-v3.3-30B-A3B"
    EVON_API_KEY: str = ""
    
    # Market Data Source ("yfinance" | "sample")
    MARKET_SOURCE: str = "yfinance"
    
    # Operational Thresholds & Safety
    MAX_AUDIO_SECONDS: int = 20
    CONFIRM_AMOUNT_RUPEES: int = 5000
    AUDIO_TTL_MIN: int = 30
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def is_prisma_configured(self) -> bool:
        return bool(self.GNANI_API_KEY and self.GNANI_API_KEY.strip())

    def is_evon_configured(self) -> bool:
        return bool(self.EVON_ENABLED and self.EVON_BASE_URL and self.EVON_BASE_URL.strip())

    def is_timbre_configured(self) -> bool:
        return bool(self.GNANI_API_KEY and self.GNANI_API_KEY.strip())

    def is_market_configured(self) -> bool:
        return self.MARKET_SOURCE in ("yfinance", "sample")

    def get_service_readiness(self) -> Dict[str, Any]:
        """
        Return safe status for all external service integrations.
        Never reveals secret API keys.
        """
        return {
            "prisma": {
                "status": "Configured" if self.is_prisma_configured() else "Missing",
                "endpoint": f"{self.GNANI_BASE_URL.rstrip('/')}/stt/v3",
                "model": self.STT_MODEL,
                "api_key_masked": mask_credential(self.GNANI_API_KEY),
                "is_active": self.is_prisma_configured()
            },
            "evon": {
                "status": "Configured" if self.is_evon_configured() else "Missing",
                "endpoint": f"{self.EVON_BASE_URL.rstrip('/')}/v1/chat/completions",
                "model": self.EVON_MODEL,
                "fallback_parser": "Deterministic Multilingual Rules Parser (Active)",
                "is_active": self.is_evon_configured()
            },
            "timbre": {
                "status": "Configured" if self.is_timbre_configured() else "Missing",
                "endpoint": f"{self.GNANI_BASE_URL.rstrip('/')}/api/v1/tts/inference",
                "model": self.TTS_MODEL,
                "default_voice": self.TTS_VOICE_HI,
                "fallback_engine": "Browser Web Speech API (Active)",
                "api_key_masked": mask_credential(self.GNANI_API_KEY),
                "is_active": self.is_timbre_configured()
            },
            "market_data": {
                "status": "Configured",
                "provider": self.MARKET_SOURCE,
                "is_live": self.MARKET_SOURCE == "yfinance",
                "auto_cache_ttl_sec": 300
            },
            "environment": {
                "demo_mode": bool(self.DEMO_MODE),
                "debug": bool(self.DEBUG),
                "database_path": self.DB_PATH
            }
        }

settings = Settings()
