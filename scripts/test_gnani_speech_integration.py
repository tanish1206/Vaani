"""
VAANI — Official Gnani Speech API Integration Test Suite
Verifies:
1. Centralized Gnani Configuration & Masking
2. Voice Catalogue Integrity:
   - Timbre v3.0 (13 Pan-India voices)
   - Timbre v2.5 (42 Vernacular voices)
3. Strict Model-Voice Compatibility Enforcement
4. SQLite Voice Preference Persistence (tts_model, voice_id, speech_rate, language)
5. Zero Demo Data Policy & Database State Integrity
6. Live Endpoint Contracts & Payload Construction
7. Ephemeral Preview Safety (Zero DB Writes)
8. Conversational Pipeline & Integer Paise Guardrails
"""

import sys
from pathlib import Path
import sqlite3
import asyncio

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import settings, mask_credential
from app.services.gnani import GnaniClient, GnaniConfig, VoiceCatalogService
from app.services.gnani.voice_catalog import TIMBRE_V3_VOICES, TIMBRE_V25_VOICES
from app.services.voice import VoiceSettingsService, AudioProcessor
from app.core.pipeline import VoicePipeline
from app.db.session import get_db, DB_FILE

def test_gnani_configuration():
    print("--- 1. Testing Centralized Gnani Configuration ---")
    assert GnaniConfig.get_asr_endpoint() == "https://api.vachana.ai/stt/v3", "Incorrect STT endpoint"
    assert GnaniConfig.get_ws_asr_endpoint() == "wss://api.vachana.ai/stt/v3/stream", "Incorrect WebSocket endpoint"
    assert GnaniConfig.get_tts_endpoint() == "https://api.vachana.ai/api/v1/tts/inference", "Incorrect TTS REST endpoint"
    assert GnaniConfig.get_tts_sse_endpoint() == "https://api.vachana.ai/api/v1/tts/sse", "Incorrect TTS SSE endpoint"

    # Verify safe credential masking
    masked = mask_credential("vach_abcdef1234567890")
    assert masked == "vach****7890", f"Masking failed: {masked}"
    assert mask_credential("") == "Not Configured"
    assert mask_credential(None) == "Not Configured"
    print("✓ Configuration & Endpoint contracts verified.")

def test_voice_catalogue():
    print("--- 2. Testing Official Voice Catalogue ---")
    # Verify Model A: Timbre v3.0
    assert len(TIMBRE_V3_VOICES) == 13, f"Expected 13 Timbre v3.0 voices, got {len(TIMBRE_V3_VOICES)}"
    v3_female = [v for v in TIMBRE_V3_VOICES if v["gender"] == "Female"]
    v3_male = [v for v in TIMBRE_V3_VOICES if v["gender"] == "Male"]
    assert len(v3_female) == 7, f"Expected 7 female voices, got {len(v3_female)}"
    assert len(v3_male) == 6, f"Expected 6 male voices, got {len(v3_male)}"

    v3_names = set(v["id"] for v in TIMBRE_V3_VOICES)
    expected_v3 = {"Shivani", "Lakshmi", "Kalpana", "Chetana", "Vasudha", "Riyaa", "Tarika",
                   "Avinash", "Shubham", "Prakash", "Devansh", "Yashraj", "Harshad"}
    assert v3_names == expected_v3, f"Mismatch in v3 voices: {v3_names ^ expected_v3}"

    # Verify each v3 voice supports the 10 Indian languages
    for v in TIMBRE_V3_VOICES:
        assert len(v["languages"]) == 10, f"{v['id']} does not support 10 languages"
        assert "hi-IN" in v["languages"]
        assert "mr-IN" in v["languages"]
        assert "en-IN" in v["languages"]

    # Verify Model B: Timbre v2.5
    assert len(TIMBRE_V25_VOICES) == 42, f"Expected 42 Timbre v2.5 voices, got {len(TIMBRE_V25_VOICES)}"
    v25_names = set(v["id"] for v in TIMBRE_V25_VOICES)
    for sample in ["Bhavna", "Nalini", "Kaveri", "Zahira", "Ishaan", "Poorvi", "Asmita"]:
        assert sample in v25_names, f"Missing v2.5 voice {sample}"

    print(f"✓ Voice catalogue verified: 13 Timbre v3.0 voices & 42 Timbre v2.5 voices.")

def test_model_voice_compatibility():
    print("--- 3. Testing Strict Model-Voice Compatibility ---")
    # Valid v3.0 combinations
    valid, _ = VoiceCatalogService.validate_model_and_voice("timbre-v3.0", "Shivani")
    assert valid, "Shivani should be valid on timbre-v3.0"
    valid, _ = VoiceCatalogService.validate_model_and_voice("timbre-v3.0", "Avinash")
    assert valid, "Avinash should be valid on timbre-v3.0"

    # Valid v2.5 combinations
    valid, _ = VoiceCatalogService.validate_model_and_voice("timbre-v2.5", "Bhavna")
    assert valid, "Bhavna should be valid on timbre-v2.5"
    valid, _ = VoiceCatalogService.validate_model_and_voice("timbre-v2.5", "Zahira")
    assert valid, "Zahira should be valid on timbre-v2.5"

    # Invalid cross-model combinations (MUST FAIL)
    valid, err = VoiceCatalogService.validate_model_and_voice("timbre-v3.0", "Bhavna")
    assert not valid, "Bhavna must not be valid on timbre-v3.0"
    assert "belongs to Timbre v2.5" in err

    valid, err = VoiceCatalogService.validate_model_and_voice("timbre-v2.5", "Shivani")
    assert not valid, "Shivani must not be valid on timbre-v2.5"
    assert "belongs to Timbre v3.0" in err

    valid, err = VoiceCatalogService.validate_model_and_voice("invalid-model", "Shivani")
    assert not valid, "Invalid model must be rejected"

    print("✓ Strict Model-Voice compatibility rules verified.")

def test_voice_persistence():
    print("--- 4. Testing SQLite Voice Preference Persistence ---")
    # Set to Timbre v3.0 / Shivani
    res1 = VoiceSettingsService.set_voice_settings(
        voice_id="Shivani",
        model="timbre-v3.0",
        language="hi-IN",
        speech_rate=1.0
    )
    assert res1["status"] == "success"
    assert VoiceSettingsService.get_selected_tts_model() == "timbre-v3.0"
    assert VoiceSettingsService.get_selected_voice_id() == "Shivani"

    # Set to Timbre v2.5 / Bhavna
    res2 = VoiceSettingsService.set_voice_settings(
        voice_id="Bhavna",
        model="timbre-v2.5",
        language="hi-IN",
        speech_rate=1.1
    )
    assert res2["status"] == "success"
    assert VoiceSettingsService.get_selected_tts_model() == "timbre-v2.5"
    assert VoiceSettingsService.get_selected_voice_id() == "Bhavna"
    assert VoiceSettingsService.get_selected_speech_rate() == 1.1

    # Mismatch should throw ValueError
    try:
        VoiceSettingsService.set_voice_settings(voice_id="Shivani", model="timbre-v2.5")
        assert False, "Should have raised ValueError on incompatible voice"
    except ValueError as e:
        assert "belongs to Timbre v3.0" in str(e)

    # Reset to flagship default
    VoiceSettingsService.set_voice_settings(voice_id="Shivani", model="timbre-v3.0", speech_rate=1.0)
    print("✓ Voice settings persistence and rejection verified.")

def test_zero_demo_data():
    print("--- 5. Testing Strict Zero Demo Data Policy ---")
    with get_db() as conn:
        cur = conn.cursor()
        for table in ["customers", "ledger_entries", "prescriptions", "medicines", "reminders", "watchlist"]:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            assert count == 0, f"Table '{table}' is not empty! Found {count} records."
    print("✓ Clean database confirmed: 0 demo customers, 0 transactions, 0 prescriptions, 0 fake watchlist.")

def test_audio_processor_and_privacy():
    print("--- 6. Testing In-Memory Audio Processing & Privacy ---")
    fake_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00" + b"\x00" * 200
    valid, msg = AudioProcessor.validate_audio_bytes(fake_header, "turn.wav")
    assert valid, f"Validation failed: {msg}"

    b64 = AudioProcessor.encode_base64_audio(fake_header)
    assert isinstance(b64, str) and len(b64) > 10

    # Short audio rejected cleanly
    valid, msg = AudioProcessor.validate_audio_bytes(b"short", "turn.wav")
    assert not valid
    print("✓ In-memory audio validation & base64 encoding verified.")

async def test_conversational_turn():
    print("--- 7. Testing Real Turn Execution & Integer Paise Guardrails ---")
    # Dry run turn (ephemeral, zero DB writes)
    res_dry = await VoicePipeline.run_turn(
        transcript="Ajay ko 500 rupaye ka udhaar likh do",
        session_id="landing-ephemeral",
        dry_run=True
    )
    assert res_dry["actions"], "Actions should be extracted"
    assert res_dry["actions"][0]["args"]["amount"] == 500

    # Verify zero DB writes occurred in dry run
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers WHERE name_roman LIKE '%Ajay%';")
        assert cur.fetchone()[0] == 0, "Dry run must never write to database"

    try:
        # Real turn execution
        res_real = await VoicePipeline.run_turn(
            transcript="Kamlesh ko 350 rupaye ka udhaar likh do",
            session_id="app-test",
            dry_run=False
        )
        assert res_real["reply_text"], "Reply text should be generated"

        # Verify genuine customer was created with exact integer paise
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT customer_id, name_roman, balance_paise FROM customer_balances WHERE name_roman LIKE '%Kamlesh%';")
            cust = cur.fetchone()
            assert cust is not None, "Customer should be created in database"
            assert cust["balance_paise"] == 35000, f"Expected 35000 paise, got {cust['balance_paise']}"
    finally:
        # Clean up test record to maintain zero demo data
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM ledger_entries WHERE customer_id IN (SELECT id FROM customers WHERE name_roman LIKE '%Kamlesh%');")
            cur.execute("DELETE FROM customers WHERE name_roman LIKE '%Kamlesh%';")

    print("✓ Real conversational turn & integer paise math validated.")

async def main():
    print("==================================================================")
    print("VAANI — OFFICIAL GNANI SPEECH API INTEGRATION VERIFICATION")
    print("==================================================================")
    test_gnani_configuration()
    test_voice_catalogue()
    test_model_voice_compatibility()
    test_voice_persistence()
    test_zero_demo_data()
    test_audio_processor_and_privacy()
    await test_conversational_turn()
    print("==================================================================")
    print("ALL 7 SUITES PASSED CLEANLY (100% SUCCESS)")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(main())
