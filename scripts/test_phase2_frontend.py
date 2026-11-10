"""
Phase 2 Frontend & Gnani Branding Verification Test Suite.
Verifies all 8 priority enhancements across the VAANI landing page.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_phase2_verification():
    print("=" * 65)
    print("  VAANI — PHASE 2 FRONTEND & GNANI BRANDING VERIFICATION")
    print("=" * 65)

    r = client.get("/")
    assert r.status_code == 200, "Landing page returned non-200"
    html = r.text

    checks = [
        # Priority 1: Hero & Botanical Architecture
        ("Hero Stage Badge", "heroBotanicalStageBadge" in html),
        ("Subterranean Soil Stratum", "groundEarthGrad" in html and "botanicalGround" in html),
        ("Deep Lateral Roots", "botanicalRoots" in html),
        ("Subterranean Baseline Ruler", "ROOT AXIS" in html),

        # Priority 2: Interactive Showcase Demonstrations
        ("Bol-Khata Total Balance", "khataDemoTotalBal" in html),
        ("Bol-Khata Add Udhaar Button", "khataDemoAddBtn" in html),
        ("Bol-Khata Undo Button", "khataDemoUndoBtn" in html),
        ("Parchi Done Buttons", "parchiDoneBtn1" in html and "parchiDoneBtn2" in html),
        ("Parchi Snooze Buttons", "parchiSnoozeBtn1" in html and "parchiSnoozeBtn2" in html),
        ("Parchi Progress Fill", "parchiProgressFill" in html),
        ("Parchi Doctor Disclaimer", "doctor-disclaimer-note" in html),
        ("Sensex Timeframe Tabs", "data-period=\"1D\"" in html and "data-period=\"1M\"" in html),
        ("Sensex Candlestick Bars", "sensexBar1" in html and "sensexBar8" in html),
        ("Sensex Listen Briefing Button", "sensexListenBtn" in html),

        # Priority 3: Interactive Voice Demo ("Experience VAANI")
        ("Experience VAANI Title", "Experience VAANI" in html),
        ("Live Decibel Canvas", "voiceDecibelCanvas" in html),
        ("Voice Text Input Dock", "voiceTextInput" in html and "voiceTextSendBtn" in html),
        ("Sandbox Demo Mode Badge", "SANDBOX DEMO MODE" in html),
        ("Inspector Play Audio Button", "inspectorAudioPlayBtn" in html),

        # Priority 4: Official Gnani Branding
        ("Location A: Hero Gnani Attribution", "hero-gnani-attribution" in html and "assets/gnani-logo.svg" in html),
        ("Location B: Technology Gnani Banner", "gnani-featured-banner" in html and "Voice Intelligence Powered by Gnani" in html),
        ("Location C: Footer Gnani Badge", "footer-gnani-badge" in html and "assets/gnani-logo-white.svg" in html),
        ("Gnani Official Website Links", html.count("https://www.gnani.ai") >= 3),

        # Priority 5: 5-Stage Voice-First Pipeline
        ("Pipeline Stage 01", "STAGE 01" in html),
        ("Pipeline Stage 02", "STAGE 02" in html and "Gnani Prisma v3.0" in html),
        ("Pipeline Stage 03", "STAGE 03" in html and "Gnani Evon v3.3" in html),
        ("Pipeline Stage 04", "STAGE 04" in html and "SQLite WAL" in html),
        ("Pipeline Stage 05", "STAGE 05" in html and "Gnani Timbre v2.5" in html),
        ("Pipeline Progress Track", "pipeline-progress-track" in html),

        # Priority 6: Multilingual Audio Listen Buttons
        ("Multilingual Command Audio Button", "data-lang-audio=\"cmd\"" in html),
        ("Multilingual Response Audio Button", "data-lang-audio=\"resp\"" in html),

        # Priority 7: Trust, Safety & Sovereignty Section
        ("Trust & Safety Section", "id=\"trust-safety\"" in html),
        ("Deterministic Integer Arithmetic Card", "Deterministic Integer Arithmetic" in html and "Zero LLM Math" in html),
        ("Append-Only SQLite WAL Card", "Append-Only SQLite WAL with Voice Undo" in html),
        ("Medical & Investment Guardrails Card", "Strict Medical &amp; Investment Guardrails" in html),
        ("Local SQLite Data Sovereignty Card", "Local SQLite Data Sovereignty" in html),

        # Priority 8: Section Polish & Accessibility
        ("FAQ Accessible Buttons", "aria-expanded=\"true\"" in html and "aria-controls=" in html),
        ("Final CTA Title", "Your business. Your voice. Your Vaani." in html),
        ("Final CTA Tagline", "Apne roz ke kaam ko aur aasaan banaiye. Boliye, Vaani sambhal legi." in html),
    ]

    passed = 0
    for name, condition in checks:
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}")
            raise AssertionError(f"Check failed: {name}")

    print("\n" + "=" * 65)
    print(f"  ALL {passed}/{len(checks)} PHASE 2 VERIFICATION CHECKS PASSED (100%)")
    print("=" * 65)

if __name__ == "__main__":
    run_phase2_verification()
