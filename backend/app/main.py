"""
VAANI — Master Backend Application
FastAPI server serving the landing page, full application shell, and voice assistant APIs.
Tagline: Boliye. Vaani Sambhal Legi.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from app.config import settings
from app.db.session import init_db
from app.api import text, voice, khata, parchi, bazaar, settings as settings_api

app = FastAPI(
    title="VAANI API",
    description="Voice-first AI assistant for Indian shopkeepers & small businesses",
    version="1.0.0"
)

# Initialize database on startup
init_db()

# CORS setup
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect API Routers
app.include_router(text.router)
app.include_router(voice.router)
app.include_router(khata.router)
app.include_router(parchi.router)
app.include_router(bazaar.router)
app.include_router(settings_api.router)

@app.get("/api/v1/health")
async def health_check():
    """Health status and diagnostic info for judges and monitoring."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": "1.0.0",
        "models": {
            "stt": settings.STT_MODEL,
            "evon": settings.EVON_MODEL,
            "tts": settings.TTS_MODEL
        },
        "database": {
            "path": settings.DB_PATH,
            "wal_mode": True
        },
        "latency_budget_target_seconds": 4.0
    }

# Path to frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

@app.get("/app")
async def serve_app():
    """Serve the full working application shell."""
    app_html = FRONTEND_DIR / "app.html"
    if app_html.exists():
        return FileResponse(str(app_html))
    return JSONResponse(status_code=404, content={"error": "App HTML not found"})

# Static Frontend Mount for landing page, css, js, assets
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
