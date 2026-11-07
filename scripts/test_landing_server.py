"""
Test script to verify FastAPI server, static file serving, and endpoints.
"""

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all():
    print("Testing /api/v1/health...")
    r = client.get("/api/v1/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health_data = r.json()
    assert health_data["app"] == "VAANI"
    print("Health check OK:", health_data)

    print("\nTesting GET / (Landing Page)...")
    r = client.get("/")
    assert r.status_code == 200, f"Root / failed: {r.status_code}"
    assert "VAANI" in r.text
    assert "Boliye," in r.text
    assert "Bol-Khata" in r.text
    assert "Parchi" in r.text
    assert "Sensex Awaaz" in r.text
    print("Landing page HTML loaded successfully (Length:", len(r.text), "bytes)")

    print("\nTesting static assets...")
    assets = [
        "/styles/tokens.css",
        "/styles/landing.css",
        "/styles/components.css",
        "/assets/botanical-artwork.svg",
        "/assets/mandala.svg",
        "/js/landing.js",
        "/js/voice-simulator.js",
        "/js/audio-visualizer.js"
    ]
    for asset in assets:
        r = client.get(asset)
        assert r.status_code == 200, f"Asset {asset} returned {r.status_code}"
        print(f"Asset {asset} OK ({len(r.content)} bytes)")

    print("\nTesting POST /api/v1/text/turn...")
    r = client.post("/api/v1/text/turn", json={"text": "Ramesh ko 200 udhaar likh de"})
    assert r.status_code == 200, f"Turn failed: {r.status_code}"
    turn_data = r.json()
    assert turn_data["actions"][0]["tool"] == "add_credit"
    print("Turn API OK:", turn_data["reply_text"])

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all()

