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
from fastapi.responses import JSONResponse, FileResponse

from app.config import settings
from app.db.session import init_db, get_db
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
    print("  -> [health_check] Starting...")
    counts = {}
    journal_mode = "unknown"
    try:
        print("  -> [health_check] Entering get_db()...")
        with get_db() as conn:
            print("  -> [health_check] Got conn, running PRAGMA journal_mode...")
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode;")
            journal_mode = cur.fetchone()[0]
            print(f"  -> [health_check] journal_mode={journal_mode}, counting tables...")
            for tbl in ["customers", "ledger_entries", "prescriptions", "reminders", "watchlist"]:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    counts[tbl] = cur.fetchone()[0]
                except Exception:
                    counts[tbl] = 0
            print(f"  -> [health_check] Table counts={counts}")
    except Exception as e:
        print(f"  -> [health_check] Exception: {e}")
        journal_mode = f"error: {e}"

    print("  -> [health_check] Calling settings.get_service_readiness()...")
    readiness = settings.get_service_readiness()
    print("  -> [health_check] Got readiness, returning response...")

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": "1.0.0",
        "demo_mode": settings.is_demo_mode(),
        "service_readiness": settings.get_service_readiness(),
        "database": {
            "path": settings.DB_PATH,
            "wal_mode": str(journal_mode).lower() == "wal",
            "journal_mode": journal_mode,
            "row_counts": counts
        },
        "latency_budget_target_seconds": 4.0
    }

# Path to frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
APP_PAGES_DIR = FRONTEND_DIR / "app"

# Multi-Page Workspace Routes
@app.get("/app")
@app.get("/app/")
async def serve_overview():
    """Application central hub & module overview."""
    overview_html = APP_PAGES_DIR / "overview.html"
    if overview_html.exists():
        return FileResponse(str(overview_html))
    fallback = FRONTEND_DIR / "app.html"
    if fallback.exists():
        return FileResponse(str(fallback))
    return JSONResponse(status_code=404, content={"error": "Overview page not found"})

@app.get("/app/bol-khata")
@app.get("/app/bol-khata/")
async def serve_bol_khata():
    """Dedicated Bol-Khata (Business Ledger) workspace."""
    page = APP_PAGES_DIR / "bol-khata.html"
    if page.exists():
        return FileResponse(str(page))
    return JSONResponse(status_code=404, content={"error": "Bol-Khata page not found"})

@app.get("/app/parchi")
@app.get("/app/parchi/")
async def serve_parchi():
    """Dedicated Parchi (Medicine Reminders) workspace."""
    page = APP_PAGES_DIR / "parchi.html"
    if page.exists():
        return FileResponse(str(page))
    return JSONResponse(status_code=404, content={"error": "Parchi page not found"})

@app.get("/app/sensex-awaaz")
@app.get("/app/sensex-awaaz/")
async def serve_sensex_awaaz():
    """Dedicated Sensex Awaaz (Market Intelligence) workspace."""
    page = APP_PAGES_DIR / "sensex-awaaz.html"
    if page.exists():
        return FileResponse(str(page))
    return JSONResponse(status_code=404, content={"error": "Sensex Awaaz page not found"})

@app.get("/app/settings")
@app.get("/app/settings/")
async def serve_settings():
    """Application Settings and AI Readiness Diagnostics."""
    page = APP_PAGES_DIR / "settings.html"
    if page.exists():
        return FileResponse(str(page))
    return JSONResponse(status_code=404, content={"error": "Settings page not found"})

# Static Frontend Mount for landing page, css, js, assets
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
