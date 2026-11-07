"""
Settings REST API endpoints for user preferences.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

@router.get("")
async def get_settings():
    """Fetch all current application settings."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings;")
        return {r["key"]: r["value"] for r in cur.fetchall()}

@router.post("")
async def update_settings(req: SettingsUpdateRequest):
    """Update user preferences."""
    with get_db() as conn:
        cur = conn.cursor()
        for k, v in req.settings.items():
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);", (k, str(v)))
    return {"status": "updated", "settings": req.settings}

