"""
VAANI — Master Backend Application
FastAPI server serving the landing page, dedicated multi-page application workspaces,
and voice assistant APIs.
Tagline: Boliye. Vaani Sambhal Legi.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse

from app.config import settings
from app.db.session import init_db, get_db
from app.api import text, voice, khata, parchi, bazaar, settings as settings_api

app = FastAPI(
    title="VAANI API",
    description="Voice-first AI assistant for Indian shopkeepers & small businesses",
    version="2.0.0"
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
async def global_exception_handler(request, exc):
    import traceback
    err_msg = str(exc)
    tb = traceback.format_exc()
    print(f"[Unhandled Exception] {err_msg}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": err_msg, "traceback": tb}
    )

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
    """Health status and diagnostic info for judges and monitoring."""
    counts = {}
    journal_mode = "unknown"
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            journal_mode = cur.fetchone()[0]
            for tbl in ["customers", "ledger_entries", "prescriptions", "reminders", "watchlist"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    counts[tbl] = cur.fetchone()[0]
                except Exception:
                    counts[tbl] = 0
    except Exception as e:
        journal_mode = f"error: {e}"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": "2.0.0",
        "demo_mode": settings.is_demo_mode(),
        "models": {
            "stt": settings.STT_MODEL,
            "evon": settings.EVON_MODEL,
            "tts": settings.TTS_MODEL
        },
        "service_readiness": settings.get_service_readiness(),
        "database": {
            "path": settings.DB_PATH,
            "wal_mode": str(journal_mode).lower() == "wal",
            "journal_mode": journal_mode,
            "row_counts": counts
        },
        "latency_budget_target_seconds": 4.0
    }

from app.config import settings, BASE_DIR

# Path to frontend
FRONTEND_DIR = BASE_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
APP_PAGES_DIR = FRONTEND_DIR / "app"

def serve_html_file(file_path: Path):
    if file_path.exists():
        return HTMLResponse(content=file_path.read_text(encoding="utf-8"))
    return JSONResponse(status_code=404, content={"error": f"Page not found: {file_path.name}"})

# Landing Page Route
@app.get("/")
async def serve_landing():
    """Editorial Landing Page."""
    return serve_html_file(FRONTEND_DIR / "index.html")

# Multi-Page Workspace Routes
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
