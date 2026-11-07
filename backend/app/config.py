"""
Configuration settings for VAANI application.
"""

from typing import Union
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "VAANI"
    TAGLINE: str = "Boliye. Vaani Sambhal Legi."
    DEBUG: Union[bool, str] = True
    
    @field_validator("DEBUG", mode="before")
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "debug")
        return bool(v)
    
    # Database
    DB_PATH: str = str(BASE_DIR / "data" / "vaani.db")
    
    # Gnani Services
    GNANI_API_KEY: str = "dummy_key_local"
    GNANI_BASE_URL: str = "https://api.vachana.ai"
    STT_MODEL: str = "prisma-v3.0"
    STT_DEFAULT_LANGUAGE: str = "hi-IN"
    
    TTS_MODEL: str = "timbre-v2.5"
    TTS_VOICE_HI: str = "sia"
    TTS_VOICE_MR: str = "sia"
    TTS_VOICE_EN: str = "sia"
    
    # Evon LLM
    EVON_ENABLED: bool = True
    EVON_BASE_URL: str = "http://localhost:8001"
    EVON_MODEL: str = "gnani/gnani-evon-v3.3-30B-A3B"
    EVON_API_KEY: str = ""
    
    # Market
    MARKET_SOURCE: str = "sample"  # yfinance or sample
    
    # Limits & Rules
    MAX_AUDIO_SECONDS: int = 20
    CONFIRM_AMOUNT_RUPEES: int = 5000
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
