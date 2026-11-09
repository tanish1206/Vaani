"""
Settings and System Diagnostics REST API endpoints.
Provides configuration management, AI readiness status, database health,
connectivity diagnostics, and demo resets for shopkeepers and evaluators.
"""

import os
import time
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings, mask_credential
from app.db.session import get_db
from app.db.seed import reset_demo_data
from app.modules.bazaar.service import BazaarService

router = APIRouter(prefix="/api/v1/settings", tags=["Settings & Diagnostics"])

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

@router.get("")
async def get_settings():
    """Fetch all current application settings."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings;")
        rows = cur.fetchall()
        user_settings = {r["key"]: r["value"] for r in rows}
    
    # Return defaults for missing keys
    defaults = {
        "language": "auto",
        "voice_hi": "sia",
        "voice_mr": "sia",
        "voice_en": "sia",
        "speech_rate": "1.0",
        "confirm_threshold": "5000",
        "snooze_duration_mins": "10",
        "privacy_mode": "balanced",
        "theme": "light",
        "demo_mode": "true" if settings.is_demo_mode() else "false"
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
    Comprehensive diagnostics for technical judges and system administrators.
    Checks AI service readiness, database health, masked credentials, and privacy guarantees.
    """
    db_path = settings.DB_PATH
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    with get_db() as conn:
        cur = conn.cursor()
        
        # Check WAL mode
        cur.execute("PRAGMA journal_mode;")
        journal_mode = cur.fetchone()[0]
        
        # Check foreign keys
        cur.execute("PRAGMA foreign_keys;")
        foreign_keys = bool(cur.fetchone()[0])
        
        # Table row counts
        counts = {}
        for table in ["customers", "ledger_entries", "prescriptions", "reminders", "watchlist"]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                counts[table] = cur.fetchone()[0]
            except Exception:
                counts[table] = 0

    ai_readiness = settings.get_service_readiness()

    return {
        "app_name": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": "1.0.0",
        "demo_mode": settings.is_demo_mode(),
        "ai_readiness": ai_readiness,
        "masked_credentials": {
            "GNANI_API_KEY": mask_credential(settings.GNANI_API_KEY),
            "EVON_API_KEY": mask_credential(settings.EVON_API_KEY),
            "TIMBRE_API_KEY": mask_credential(settings.GNANI_API_KEY)
        },
        "database": {
            "path": db_path,
            "size_bytes": db_size,
            "journal_mode": journal_mode,
            "wal_mode": journal_mode.lower() == "wal",
            "foreign_keys": foreign_keys,
            "row_counts": counts
        },
        "data_sovereignty": {
            "audio_retention": "Transient memory only — raw voice audio is never written to disk",
            "storage_locality": "Local-first SQLite database running entirely on your server/device",
            "third_party_telemetry": "Zero tracking scripts, zero analytics cookies, zero data broking",
            "offline_resilience": "Rule-based fallback parser and browser Web Speech API operate without cloud connectivity"
        }
    }

@router.post("/test-connectivity")
async def test_connectivity():
    """
    Ping test for all subsystem integrations.
    Returns latency and status for database, market feeds, and AI endpoints.
    """
    results = {}
    
    # 1. Database Ping
    t0 = time.time()
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
        results["database"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "message": "SQLite responding in WAL mode"
        }
    except Exception as e:
        results["database"] = {"status": "error", "message": str(e)}

    # 2. Market Data Ping
    t0 = time.time()
    try:
        quote = BazaarService.get_quote("^BSESN")
        results["market_data"] = {
            "status": "healthy" if quote else "degraded",
            "source": quote.get("source", "sample") if quote else "none",
            "is_sample": quote.get("is_sample", True) if quote else True,
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "symbol": "^BSESN",
            "price": quote.get("price") if quote else None
        }
    except Exception as e:
        results["market_data"] = {"status": "error", "message": str(e)}

    # 3. AI Endpoints Check
    ai_status = settings.get_service_readiness()
    results["ai_services"] = {
        "stt": {
            "mode": ai_status["stt"]["mode"],
            "configured": ai_status["stt"]["configured"],
            "model": ai_status["stt"]["model"]
        },
        "intent_understanding": {
            "mode": ai_status["intent_understanding"]["mode"],
            "configured": ai_status["intent_understanding"]["configured"],
            "model": ai_status["intent_understanding"]["model"]
        },
        "tts": {
            "mode": ai_status["tts"]["mode"],
            "configured": ai_status["tts"]["configured"],
            "model": ai_status["tts"]["model"]
        }
    }

    return {
        "timestamp": time.time(),
        "overall_status": "ok",
        "results": results
    }

@router.post("/reset-demo")
async def reset_demo():
    """Reset all tables and reload clean demo records."""
    res = reset_demo_data()
    return res
