"""
Comprehensive Phase 2 Multi-Page and API Readiness Integration Test Suite.
Verifies all 5 web workspaces, REST endpoints, database WAL integrity,
masked credential security, and zero regressions across modules.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("VAANI — PHASE 2 MULTI-PAGE & API READINESS VERIFICATION")
    print("=" * 60)

    tests_run = 0
    tests_passed = 0

    def assert_check(name: str, condition: bool, extra: str = ""):
        nonlocal tests_run, tests_passed
        tests_run += 1
        if condition:
            tests_passed += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")
            raise AssertionError(f"Check failed: {name} {extra}")

    # 1. Multi-Page Workspaces Availability
    print("\n--- 1. Multi-Page Routes Availability ---")
    
    r_landing = client.get("/")
    assert_check("Landing Page (GET /)", r_landing.status_code == 200 and "VAANI" in r_landing.text)

    r_overview = client.get("/app")
    assert_check("Overview Hub (GET /app)", r_overview.status_code == 200 and "Vaani Hub" in r_overview.text)

    r_khata = client.get("/app/bol-khata")
    assert_check("Bol-Khata Page (GET /app/bol-khata)", r_khata.status_code == 200 and "Bol-Khata" in r_khata.text)

    r_parchi = client.get("/app/parchi")
    assert_check("Parchi Page (GET /app/parchi)", r_parchi.status_code == 200 and "Parchi" in r_parchi.text)

    r_bazaar = client.get("/app/sensex-awaaz")
    assert_check("Sensex Awaaz Page (GET /app/sensex-awaaz)", r_bazaar.status_code == 200 and "Sensex Awaaz" in r_bazaar.text)

    r_settings = client.get("/app/settings")
    assert_check("Settings Page (GET /app/settings)", r_settings.status_code == 200 and "Settings & Diagnostics" in r_settings.text)

    # 2. System Health & Diagnostics
    print("\n--- 2. Health & Diagnostics Endpoints ---")
    
    r_health = client.get("/api/v1/health")
    assert_check("Health check (GET /api/v1/health)", r_health.status_code == 200)
    h_data = r_health.json()
    assert_check("Health status 'ok'", h_data.get("status") == "ok")
    assert_check("Database WAL mode reported", h_data.get("database", {}).get("wal_mode") is True)
    assert_check("Service readiness included", "service_readiness" in h_data)

    r_diag = client.get("/api/v1/settings/diagnostics")
    assert_check("Diagnostics (GET /api/v1/settings/diagnostics)", r_diag.status_code == 200)
    d_data = r_diag.json()
    assert_check("AI Readiness STT present", "stt" in d_data.get("ai_readiness", {}))
    assert_check("AI Readiness Intent present", "intent_understanding" in d_data.get("ai_readiness", {}))
    assert_check("AI Readiness TTS present", "tts" in d_data.get("ai_readiness", {}))
    assert_check("AI Readiness Market present", "market_data" in d_data.get("ai_readiness", {}))
    assert_check("Data sovereignty statement present", "audio_retention" in d_data.get("data_sovereignty", {}))

    # 3. Credential Security & Masking
    print("\n--- 3. Credential Security & Zero Leakage ---")
    masked = d_data.get("masked_credentials", {})
    for key, val in masked.items():
        if val is not None:
            is_safe = (val == "") or ("*" in val) or (len(val) <= 12 and "..." in val) or val.endswith("****")
            assert_check(f"Masked credential {key}", is_safe, f"-> {val}")

    # 4. Connectivity Ping Test
    print("\n--- 4. Connectivity Diagnostics ---")
    r_ping = client.post("/api/v1/settings/test-connectivity")
    assert_check("Subsystem Ping (POST /api/v1/settings/test-connectivity)", r_ping.status_code == 200)
    p_data = r_ping.json()
    assert_check("Database Ping Healthy", p_data.get("results", {}).get("database", {}).get("status") == "healthy")
    assert_check("Market Feed Responding", p_data.get("results", {}).get("market_data", {}).get("status") in ("healthy", "degraded"))

    # 5. Bol-Khata Dedicated Business Endpoints
    print("\n--- 5. Bol-Khata Ledger Operations ---")
    r_cust = client.get("/api/v1/khata/customers")
    assert_check("Fetch customers (GET /api/v1/khata/customers)", r_cust.status_code == 200 and isinstance(r_cust.json(), list))

    # Add transaction via direct REST
    r_tx = client.post("/api/v1/khata/transaction", json={
        "customer_name": "TestCustomer",
        "kind": "CREDIT",
        "amount": 250.0,
        "note": "Phase2 verification test"
    })
    assert_check("Add Manual Credit (POST /api/v1/khata/transaction)", r_tx.status_code == 200 and "reply_text" in r_tx.json())

    # Undo transaction
    r_undo = client.post("/api/v1/khata/undo", json={"session_id": "default"})
    assert_check("Undo Transaction (POST /api/v1/khata/undo)", r_undo.status_code == 200 and "reply_text" in r_undo.json())

    # 6. Parchi Medicine Reminders
    print("\n--- 6. Parchi Reminder Operations ---")
    r_doses = client.get("/api/v1/parchi/doses")
    assert_check("Fetch Doses (GET /api/v1/parchi/doses)", r_doses.status_code == 200 and "doses" in r_doses.json())
    doses_list = r_doses.json().get("doses", [])
    if doses_list:
        dose_id = doses_list[0]["id"]
        r_done = client.post(f"/api/v1/parchi/dose/{dose_id}/done")
        assert_check("Mark Dose Done (POST /api/v1/parchi/dose/{id}/done)", r_done.status_code == 200)

    # 7. Sensex Awaaz Market Operations
    print("\n--- 7. Sensex Awaaz Operations ---")
    r_overview = client.get("/api/v1/bazaar/overview")
    assert_check("Bazaar Overview (GET /api/v1/bazaar/overview)", r_overview.status_code == 200 and "quotes" in r_overview.json())
    
    r_brief = client.get("/api/v1/bazaar/briefing?lang=hinglish")
    assert_check("Spoken Market Briefing (GET /api/v1/bazaar/briefing)", r_brief.status_code == 200 and "briefing" in r_brief.json())

    # 8. Demo Data Reset
    print("\n--- 8. Demo Reset Operation ---")
    r_reset = client.post("/api/v1/settings/reset-demo")
    assert_check("Reset Demo (POST /api/v1/settings/reset-demo)", r_reset.status_code == 200 and r_reset.json().get("status") == "reset")

    print("\n" + "=" * 60)
    print(f"PHASE 2 VERIFICATION SUMMARY: {tests_passed}/{tests_run} TESTS PASSED (100%)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
