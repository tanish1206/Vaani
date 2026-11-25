"""
Unit and API tests for VAANI core services, guardrails, and REST endpoints.
Uses an isolated temporary SQLite database so production data/vaani.db is never modified.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.core.i18n import format_rupees, to_paise
from app.core.pipeline import VoicePipeline
from app.db import session as db_session
from app.main import app
from app.services.gnani.voice_catalog import VoiceCatalogService
from app.services.voice.audio_processor import AudioProcessor


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point database operations at a fresh temporary SQLite file for each test."""
    test_db = tmp_path / "test_vaani.db"
    monkeypatch.setattr(db_session, "DB_FILE", test_db)
    monkeypatch.setattr(settings, "DB_PATH", str(test_db))
    db_session.init_db()
    return test_db


def test_paise_precision_and_formatting():
    assert to_paise(850) == 85000
    assert to_paise(12.34) == 1234
    assert format_rupees(85000) == "₹850"
    assert format_rupees(125050) == "₹1,250.50"


def test_voice_catalog_strict_compatibility():
    ok, _ = VoiceCatalogService.validate_model_and_voice("timbre-v3.0", "Shivani")
    assert ok
    ok, err = VoiceCatalogService.validate_model_and_voice("timbre-v3.0", "Bhavna")
    assert not ok and "Timbre v2.5" in err
    ok, err = VoiceCatalogService.validate_model_and_voice("timbre-v2.5", "Shivani")
    assert not ok and "Timbre v3.0" in err


def test_audio_validation():
    valid_wav = b"RIFF" + b"\x00" * 120
    ok, _ = AudioProcessor.validate_audio_bytes(valid_wav, "turn.wav")
    assert ok
    ok, _ = AudioProcessor.validate_audio_bytes(b"tiny", "turn.wav")
    assert not ok
    ok, _ = AudioProcessor.validate_audio_bytes(valid_wav, "turn.txt")
    assert not ok


def test_khata_manual_credit_and_payment_endpoints(isolated_db):
    client = TestClient(app)

    r_credit = client.post(
        "/api/v1/khata/transaction",
        json={"customer_name": "Asha", "kind": "CREDIT", "amount": 500, "session_id": "test-api"},
    )
    assert r_credit.status_code == 200
    assert r_credit.json()["balance_paise"] == 50000

    # Regression: PAYMENT / JAMA previously crashed with AttributeError: add_payment
    r_pay = client.post(
        "/api/v1/khata/transaction",
        json={"customer_name": "Asha", "kind": "PAYMENT", "amount": 200, "session_id": "test-api"},
    )
    assert r_pay.status_code == 200
    assert r_pay.json()["balance_paise"] == 30000

    # Invalid inputs rejected cleanly
    assert client.post(
        "/api/v1/khata/transaction",
        json={"customer_name": "Asha", "kind": "CREDIT", "amount": -10},
    ).status_code == 422
    assert client.post(
        "/api/v1/khata/transaction",
        json={"customer_name": "Asha", "kind": "INVALID", "amount": 100},
    ).status_code == 400


@pytest.mark.asyncio
async def test_compound_turn_and_correction(isolated_db):
    res = await VoicePipeline.run_turn(
        "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye",
        session_id="test-compound",
    )
    tools = [a["tool"] for a in res["actions"]]
    assert tools == ["add_credit", "record_payment"]

    # Correct the last entry (Sunita's 150 -> 300)
    corr = await VoicePipeline.run_turn("Nahi, 300 likh", session_id="test-compound")
    assert corr["actions"][0]["tool"] == "correct_last_entry"
    assert corr["module_results"][0]["corrected"] is True
    assert corr["module_results"][0]["amount_paise"] == 30000


@pytest.mark.asyncio
async def test_dry_run_makes_zero_db_writes(isolated_db):
    await VoicePipeline.run_turn(
        "Vikram ko 400 udhaar likh do",
        session_id="landing-ephemeral",
        dry_run=True,
    )
    with db_session.get_db() as conn:
        cur = conn.cursor()
        assert cur.execute("SELECT COUNT(*) FROM customers;").fetchone()[0] == 0
        assert cur.execute("SELECT COUNT(*) FROM utterances;").fetchone()[0] == 0


def test_health_diagnostics_and_voice_validation(isolated_db):
    client = TestClient(app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["version"] == "2.0.0"

    diag = client.get("/api/v1/settings/diagnostics")
    assert diag.status_code == 200
    assert diag.json()["version"] == "2.0.0"

    bad_speed = client.put(
        "/api/v1/settings/voice",
        json={"voice_id": "Shivani", "model": "timbre-v3.0", "speed": "fast"},
    )
    assert bad_speed.status_code == 422
