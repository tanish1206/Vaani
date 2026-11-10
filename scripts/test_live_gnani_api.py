"""
Live Gnani Speech API Verification Script.
Tests live Gnani STT and TTS endpoints against https://api.vachana.ai using the configured API key.
"""

import sys
from pathlib import Path
import asyncio

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.gnani import GnaniClient, GnaniConfig

async def test_live():
    print("Testing live Gnani connectivity...")
    health = await GnaniClient.check_health()
    print("Health response:", health)

    if not GnaniConfig.is_configured():
        print("GNANI_API_KEY is not configured in .env. Skipping live synthesis tests.")
        return

    # 1. Test Timbre v3.0 Live TTS
    print("\nSynthesizing via Timbre v3.0 (voice: Shivani)...")
    audio_v3 = await GnaniClient.synthesize(
        text="नमस्ते, मैं वाणी हूँ. आपकी दुकान का डिजिटल साथी.",
        voice_id="Shivani",
        model="timbre-v3.0",
        language="hi-IN"
    )
    if audio_v3:
        print(f"✓ Timbre v3.0 Success: Received {len(audio_v3):,} bytes of audio (Header: {audio_v3[:4]})")
    else:
        print("✗ Timbre v3.0 synthesis returned None (check model/voice availability)")

    # 2. Test Timbre v2.5 Live TTS
    print("\nSynthesizing via Timbre v2.5 (voice: Bhavna)...")
    audio_v25 = await GnaniClient.synthesize(
        text="नमस्ते, मैं भावना हूँ. आपकी दुकान का डिजिटल साथी.",
        voice_id="Bhavna",
        model="timbre-v2.5",
        language="hi-IN"
    )
    if audio_v25:
        print(f"✓ Timbre v2.5 Success: Received {len(audio_v25):,} bytes of audio (Header: {audio_v25[:4]})")
    else:
        print("✗ Timbre v2.5 synthesis returned None")

if __name__ == "__main__":
    asyncio.run(test_live())

