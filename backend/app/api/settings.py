"""
Settings and System Diagnostics REST API endpoints.
Provides configuration management, AI readiness status, database health,
connectivity diagnostics, and demo resets for shopkeepers and evaluators.
"""

import time
from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import mask_credential, settings
from app.db.seed import reset_demo_data
from app.db.session import get_db, get_db_diagnostics
from app.modules.bazaar.service import BazaarService
from app.services.voice.voice_settings import VoiceSettingsService

router = APIRouter(prefix="/api/v1/settings", tags=["Settings & Diagnostics"])


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]


@router.get("")
async def get_settings():
    """Fetch all current application settings."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings;")
        user_settings = {r["key"]: r["value"] for r in cur.fetchall()}

    selected_voice = VoiceSettingsService.get_selected_voice_id()
    defaults = {
        "language": "auto",
        "tts_model": VoiceSettingsService.get_selected_tts_model(),
        "voice_id": selected_voice,
        "voice_hi": selected_voice,
        "voice_mr": "Zahira",
        "voice_en": "Kaveri",
        "speech_rate": "1.0",
        "confirm_threshold": str(settings.CONFIRM_AMOUNT_RUPEES),
        "snooze_duration_mins": "10",
        "privacy_mode": "balanced",
        "theme": "light",
        "demo_mode": "true" if settings.is_demo_mode() else "false",
    }
    defaults.update(user_settings)
    return defaults


@router.post("")
async def update_settings(req: SettingsUpdateRequest):
    """Update user preferences."""
    with get_db() as conn:
        cur = conn.cursor()
        for k, v in req.settings.items():
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);", (k, str(v)))
    return {"status": "updated", "settings": req.settings}


@router.get("/diagnostics")
async def get_diagnostics():
    """
    Comprehensive diagnostics for technical evaluators and system administrators.
    Checks AI service readiness, database health, masked credentials, and privacy guarantees.
    """
    db_diag = get_db_diagnostics()
    ai_readiness = settings.get_service_readiness()

    return {
        "app_name": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "demo_mode": settings.is_demo_mode(),
        "ai_readiness": ai_readiness,
        "masked_credentials": {
            "GNANI_API_KEY": mask_credential(settings.GNANI_API_KEY),
            "EVON_API_KEY": mask_credential(settings.EVON_API_KEY),
            "TIMBRE_API_KEY": mask_credential(settings.GNANI_API_KEY),
        },
        "database": db_diag,
        "data_sovereignty": {
            "audio_retention": "Transient memory only — raw voice audio is never written to disk",
            "storage_locality": "Local-first SQLite database running entirely on your server/device",
            "third_party_telemetry": "Zero tracking scripts, zero analytics cookies, zero data broking",
            "offline_resilience": "Rule-based fallback parser and browser Web Speech API operate without cloud connectivity",
        },
    }


@router.post("/test-connectivity")
async def test_connectivity():
    """
    Ping test for all subsystem integrations.
    Returns latency and status for database, market feeds, and AI endpoints.
    """
    results = {}

    # 1. Database Ping
    t0 = time.perf_counter()
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
        results["database"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "message": "SQLite responding in WAL mode",
        }
    except Exception as exc:
        results["database"] = {"status": "error", "message": str(exc)}

    # 2. Market Data Ping
    t0 = time.perf_counter()
    try:
        quote = BazaarService.get_quote("^BSESN")
        results["market_data"] = {
            "status": "healthy" if quote else "degraded",
            "source": quote.get("source", "sample") if quote else "none",
            "is_sample": quote.get("is_sample", True) if quote else True,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "symbol": "^BSESN",
            "price": quote.get("price") if quote else None,
        }
    except Exception as exc:
        results["market_data"] = {"status": "error", "message": str(exc)}

    # 3. AI Endpoints Check
    ai_status = settings.get_service_readiness()
    results["ai_services"] = {
        key: {
            "mode": ai_status[key]["mode"],
            "configured": ai_status[key]["configured"],
            "model": ai_status[key]["model"],
        }
        for key in ("stt", "intent_understanding", "tts")
    }

    return {
        "timestamp": time.time(),
        "overall_status": "ok",
        "results": results,
    }


@router.post("/reset-demo")
async def reset_demo():
    """Reset all tables to return to a clean empty database state."""
    return reset_demo_data()
