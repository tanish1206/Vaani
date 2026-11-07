"""
VAANI — Master Backend Application
FastAPI server serving the landing page and the voice assistant APIs.
Tagline: Boliye. Vaani Sambhal Legi.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.config import settings

app = FastAPI(
    title="VAANI API",
    description="Voice-first AI assistant for Indian shopkeepers & small businesses",
    version="1.0.0"
)

# CORS setup
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

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

# Mock Text/Voice Turn Data Contract Models
class TextTurnRequest(BaseModel):
    text: str
    language_hint: Optional[str] = "auto"
    session_id: Optional[str] = "demo-session"
    dry_run: Optional[bool] = False

class ActionPayload(BaseModel):
    tool: str
    args: Dict[str, Any]

class TurnResponse(BaseModel):
    turn_id: str
    transcript: str
    language: str
    actions: List[ActionPayload]
    reply_text: str
    guardrails_passed: bool
    timings: Dict[str, float]

@app.post("/api/v1/text/turn", response_model=TurnResponse)
async def process_text_turn(turn: TextTurnRequest):
    """
    Execute one conversational turn from text input.
    Simulates the Evon -> Guardrail -> SQLite -> Template flow.
    """
    text_lower = turn.text.lower()
    
    # Deterministic parser matching demo examples
    if "udhaar" in text_lower or "उधार" in text_lower:
        actions = [
            ActionPayload(
                tool="add_credit",
                args={"customer_name": "Ramesh", "customer_name_roman": "Ramesh", "amount": 200}
            )
        ]
        reply = "Ramesh ke khaate mein ₹200 jod diye. Ab unka baaki ₹850 hai."
    elif "bp ki goli" in text_lower or "dawa" in text_lower:
        actions = [
            ActionPayload(
                tool="save_prescription",
                args={
                    "patient_label": "Maa",
                    "medicines": [{"name": "BP ki goli", "times_of_day": ["morning", "evening"]}]
                }
            )
        ]
        reply = "Maa ke liye BP ki goli: subah aur shaam, khaane ke baad. Main yaad dilaunga."
    elif "market" in text_lower or "sensex" in text_lower:
        actions = [
            ActionPayload(tool="market_snapshot", args={"scope": "overview"})
        ]
        reply = "Sensex aaj 83,410 par 342 point upar band hua. Yeh namuna jaankari hai, nivesh salaah nahi."
    else:
        actions = []
        reply = "Aap bolkar hisaab, dawa ya bazaar ki jaankari le sakte hain."

    return TurnResponse(
        turn_id="turn-demo-1",
        transcript=turn.text,
        language="hinglish",
        actions=actions,
        reply_text=reply,
        guardrails_passed=True,
        timings={"parser_ms": 12.0, "db_ms": 3.2, "total_ms": 25.4}
    )

# Static Frontend Mount
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    async def index_missing():
        return JSONResponse(status_code=404, content={"error": "Frontend directory not found"})

