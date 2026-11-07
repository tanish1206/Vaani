"""
End-to-end verification test script for VAANI.
Tests HTTP endpoints, Application Shell, Bol-Khata, Parchi, Sensex Awaaz, and SQLite transactions.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_application():
    print("=" * 60)
    print("  RUNNING VAANI END-TO-END APPLICATION TEST")
    print("=" * 60)

    # 1. Health Diagnostic
    print("\n[1] Testing /api/v1/health...")
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "VAANI"
    print(f"  Status: OK, App: {data['app']}, Models: {data['models']}")

    # 2. Landing Page
    print("\n[2] Testing GET / (Landing Page)...")
    r = client.get("/")
    assert r.status_code == 200
    assert "VAANI" in r.text
    assert "Boliye," in r.text
    print(f"  Landing page served successfully ({len(r.text)} bytes)")

    # 3. Application Shell
    print("\n[3] Testing GET /app (Two-Pane Application Shell)...")
    r = client.get("/app")
    assert r.status_code == 200
    assert "VAANI App" in r.text
    assert "appConvoHistory" in r.text
    assert "Bol-Khata (Ledger)" in r.text
    assert "Parchi (Reminders)" in r.text
    assert "Sensex Awaaz (Bazaar)" in r.text
    print(f"  Application shell served successfully ({len(r.text)} bytes)")

    # 4. App Static Assets
    print("\n[4] Testing app static assets (styles & scripts)...")
    for asset in ["/styles/app.css", "/js/app.js", "/styles/tokens.css", "/assets/botanical-artwork.svg", "/assets/mandala.svg"]:
        r = client.get(asset)
        assert r.status_code == 200
        print(f"  Asset {asset}: OK ({len(r.content)} bytes)")

    # 5. Khata REST Endpoints
    print("\n[5] Testing /api/v1/khata endpoints...")
    r = client.get("/api/v1/khata/customers")
    assert r.status_code == 200
    customers = r.json()
    assert len(customers) >= 5
    print(f"  Found {len(customers)} customers:")
    for c in customers[:3]:
        print(f"    - {c['name']} ({c['name_roman']}): ₹{c['balance_paise'] // 100}")

    r = client.get("/api/v1/khata/summary")
    assert r.status_code == 200
    print(f"  Daily summary: {r.json()['reply_text']}")

    # 6. Parchi REST Endpoints
    print("\n[6] Testing /api/v1/parchi endpoints...")
    r = client.get("/api/v1/parchi/doses")
    assert r.status_code == 200
    print(f"  Parchi doses query: {r.json()['reply_text']}")

    # 7. Bazaar REST Endpoints
    print("\n[7] Testing /api/v1/bazaar endpoints...")
    r = client.get("/api/v1/bazaar/snapshot")
    assert r.status_code == 200
    data = r.json()
    print(f"  Sensex brief: {data['reply_text']}")

    # 8. Live Turn Execution & Financial Transaction
    print("\n[8] Testing live conversational turn execution (Khata transaction)...")
    turn_input = {"text": "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye", "session_id": "test-session"}
    r = client.post("/api/v1/text/turn", json=turn_input)
    assert r.status_code == 200
    res = r.json()
    print(f"  Reply: \"{res['reply_text']}\"")
    print(f"  Actions executed: {[a['tool'] for a in res['actions']]}")
    print(f"  Timings: {res['timings']}")

    # 9. Verify database balances updated in SQLite
    r = client.get("/api/v1/khata/customers")
    customers = {c["name_roman"]: c["balance_paise"] // 100 for c in r.json()}
    print(f"  Updated balances in SQLite: Ramesh = ₹{customers.get('Ramesh')}, Sunita = ₹{customers.get('Sunita')}")
    assert customers.get("Ramesh") == 850, f"Expected Ramesh balance ₹850, got {customers.get('Ramesh')}"
    assert customers.get("Sunita") == 0, f"Expected Sunita balance ₹0, got {customers.get('Sunita')}"

    # 10. Undo Last Action
    print("\n[10] Testing Undo last transaction...")
    r = client.post("/api/v1/text/turn", json={"text": "Galat ho gaya, hata do", "session_id": "test-session"})
    assert r.status_code == 200
    print(f"  Undo reply: \"{r.json()['reply_text']}\"")

    # Verify balances reverted
    r = client.get("/api/v1/khata/customers")
    customers = {c["name_roman"]: c["balance_paise"] // 100 for c in r.json()}
    print(f"  Reverted balances in SQLite: Ramesh = ₹{customers.get('Ramesh')}, Sunita = ₹{customers.get('Sunita')}")
    assert customers.get("Ramesh") == 650, f"Expected Ramesh reverted balance ₹650, got {customers.get('Ramesh')}"
    assert customers.get("Sunita") == 150, f"Expected Sunita reverted balance ₹150, got {customers.get('Sunita')}"

    print("\n" + "=" * 60)
    print("  ALL 10 VERIFICATION TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_application()
