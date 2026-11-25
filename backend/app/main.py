"""
VAANI — Master Backend Application
FastAPI server serving the landing page, dedicated multi-page application workspaces,
and voice assistant APIs.
Tagline: Boliye. Vaani Sambhal Legi.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import bazaar, khata, parchi, settings as settings_api, text, voice
from app.config import BASE_DIR, settings
from app.db.session import get_db_diagnostics, init_db

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VAANI API",
    description="Voice-first AI assistant for Indian shopkeepers & small businesses",
    version=settings.VERSION,
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log unhandled server errors and return a sanitized error payload."""
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    content = {"error": "Internal Server Error"}
    if settings.DEBUG:
        content["detail"] = str(exc)
    return JSONResponse(status_code=500, content=content)


# Connect API Routers
app.include_router(text.router)
app.include_router(voice.router)
app.include_router(khata.router)
app.include_router(parchi.router)
app.include_router(bazaar.router)
app.include_router(settings_api.router)


@app.get("/test-ping")
def test_ping():
    return {"ping": "pong"}


@app.get("/api/v1/health")
async def health_check():
    """Health status and diagnostic info for evaluators and monitoring."""
    db_diag = get_db_diagnostics()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "demo_mode": settings.is_demo_mode(),
        "models": {
            "stt": settings.STT_MODEL,
            "evon": settings.EVON_MODEL,
            "tts": settings.TTS_MODEL,
        },
        "service_readiness": settings.get_service_readiness(),
        "database": {
            "path": db_diag["path"],
            "wal_mode": db_diag["wal_mode"],
            "journal_mode": db_diag["journal_mode"],
            "row_counts": db_diag["row_counts"],
        },
        "latency_budget_target_seconds": 4.0,
    }


# Path to frontend resolution (supports local, nested repo, and serverless Lambda)
_frontend_candidates = [
    BASE_DIR / "frontend",
    Path(__file__).resolve().parent.parent.parent / "frontend",
    Path(__file__).resolve().parent.parent / "frontend",
    Path.cwd() / "frontend",
]
FRONTEND_DIR = next((p for p in _frontend_candidates if p.exists()), _frontend_candidates[0])
APP_PAGES_DIR = FRONTEND_DIR / "app"


def serve_html_file(file_path: Path):
    """Serve an HTML file from the frontend directory with clean error handling."""
    try:
        if file_path.exists():
            return HTMLResponse(content=file_path.read_text(encoding="utf-8"))
        return JSONResponse(status_code=404, content={"error": f"Page not found: {file_path.name}"})
    except OSError as exc:
        logger.error("Failed to read HTML file %s: %s", file_path, exc)
        return JSONResponse(status_code=500, content={"error": "Failed to load page"})


@app.get("/")
async def serve_landing():
    """Editorial Landing Page."""
    return serve_html_file(FRONTEND_DIR / "index.html")


@app.get("/app")
@app.get("/app/")
async def serve_overview():
    """Application central hub & module overview."""
    overview_html = APP_PAGES_DIR / "overview.html"
    if overview_html.exists():
        return serve_html_file(overview_html)
    return serve_html_file(FRONTEND_DIR / "app.html")


@app.get("/app/bol-khata")
@app.get("/app/bol-khata/")
async def serve_bol_khata():
    """Dedicated Bol-Khata (Business Ledger) workspace."""
    return serve_html_file(APP_PAGES_DIR / "bol-khata.html")


@app.get("/app/parchi")
@app.get("/app/parchi/")
async def serve_parchi():
    """Dedicated Parchi (Medicine Reminders) workspace."""
    return serve_html_file(APP_PAGES_DIR / "parchi.html")


@app.get("/app/sensex-awaaz")
@app.get("/app/sensex-awaaz/")
async def serve_sensex_awaaz():
    """Dedicated Sensex Awaaz (Market Intelligence) workspace."""
    return serve_html_file(APP_PAGES_DIR / "sensex-awaaz.html")


@app.get("/app/settings")
@app.get("/app/settings/")
async def serve_settings():
    """Application Settings and AI Readiness Diagnostics."""
    return serve_html_file(APP_PAGES_DIR / "settings.html")


# Static Frontend Mount for static assets (css, js, assets, sounds)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="frontend")
