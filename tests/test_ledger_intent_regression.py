"""
VAANI — Regression Test Suite for Ledger Intent Parsing & Parchi Medicine Reminders.

Verifies:
1. Spoken customer names are NEVER substituted by other names (e.g. Tanish is NOT Ramesh).
2. Credit vs Payment direction matches strict particle/keyword rules:
   - "गणेश को 500 रुपए दिए हैं" -> add_credit for Ganesh (NOT Sunita, NOT payment).
   - "गणेश ने 500 दिए" -> record_payment for Ganesh.
   - "ganesh ko udhaar 200" -> add_credit for Ganesh.
3. Missing name utterances trigger clarification:
   - "500 ka udhaar likh do" -> clarify ("Kiska khaata?"), 0 DB writes.
4. Balance inquiries:
   - "ramesh ka hisaab batao" -> get_balance for Ramesh, 0 ledger entries.
5. Parchi dynamic prescription parsing (Devanagari & Latin):
   - "दादाजी की दवा Paracetamol 8:00 बजे याद दिलाओ।" -> patient "दादाजी", medicine "Paracetamol".
   - "dadaji ki dawaai paracetamol 8 baje yaad dilao" -> patient "Dadaji", medicine "Paracetamol".
"""

import sys
from pathlib import Path
import pytest
import asyncio

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.pipeline import VoicePipeline
from app.db.session import get_db

@pytest.fixture(autouse=True)
def clean_test_customers():
    """Ensure test customers are cleaned up before and after each test."""
    test_names = ["tanish", "ganesh", "गणेश", "dadaji", "दादाजी", "ramesh", "kiran"]
    with get_db() as conn:
        cur = conn.cursor()
        for name in test_names:
            cur.execute("DELETE FROM ledger_entries WHERE customer_id IN (SELECT id FROM customers WHERE lower(name) = ? OR lower(name_roman) = ?);", (name.lower(), name.lower()))
            cur.execute("DELETE FROM customers WHERE lower(name) = ? OR lower(name_roman) = ?;", (name.lower(), name.lower()))
        cur.execute("DELETE FROM reminders WHERE medicine_id IN (SELECT id FROM medicines WHERE prescription_id IN (SELECT id FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी')));")
        cur.execute("DELETE FROM medicines WHERE prescription_id IN (SELECT id FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी'));")
        cur.execute("DELETE FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी');")
    yield
    with get_db() as conn:
        cur = conn.cursor()
        for name in test_names:
            cur.execute("DELETE FROM ledger_entries WHERE customer_id IN (SELECT id FROM customers WHERE lower(name) = ? OR lower(name_roman) = ?);", (name.lower(), name.lower()))
            cur.execute("DELETE FROM customers WHERE lower(name) = ? OR lower(name_roman) = ?;", (name.lower(), name.lower()))
        cur.execute("DELETE FROM reminders WHERE medicine_id IN (SELECT id FROM medicines WHERE prescription_id IN (SELECT id FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी')));")
        cur.execute("DELETE FROM medicines WHERE prescription_id IN (SELECT id FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी'));")
        cur.execute("DELETE FROM prescriptions WHERE patient_label IN ('Dadaji', 'दादाजी');")

@pytest.mark.asyncio
async def test_tanish_credit():
    """STT 'tanish ka 500 ka udhaar likh do' must create CREDIT for Tanish (NOT Ramesh)."""
    transcript = "tanish ka 500 ka udhaar likh do"
    res = await VoicePipeline.run_turn(transcript, session_id="test-tanish")
    
    assert res["actions"], "Should contain actions"
    act = res["actions"][0]
    assert act["tool"] == "add_credit", f"Expected add_credit, got {act['tool']}"
    assert act["args"]["amount"] == 500.0
    assert "tanish" in act["args"]["customer_name"].lower()

    # Verify DB record
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_roman FROM customers WHERE lower(name) = 'tanish' OR lower(name_roman) = 'tanish';")
        cust = cur.fetchone()
        assert cust is not None, "Customer 'tanish' must be created in DB"

        cur.execute("SELECT kind, amount_paise FROM ledger_entries WHERE customer_id = ?;", (cust["id"],))
        entry = cur.fetchone()
        assert entry is not None, "Ledger entry must exist"
        assert entry["kind"] == "CREDIT", f"Expected CREDIT, got {entry['kind']}"
        assert entry["amount_paise"] == 50000

    # Verify reply text template
    assert "tanish" in res["reply_text"].lower()
    assert "₹500 udhaar likh diya" in res["reply_text"]
    assert "ramesh" not in res["reply_text"].lower()

@pytest.mark.asyncio
async def test_ganesh_credit_with_diye():
    """STT 'गणेश को 500 रुपए दिए हैं' must be CREDIT for Ganesh (NOT Payment, NOT Sunita)."""
    transcript = "गणेश को 500 रुपए दिए हैं"
    res = await VoicePipeline.run_turn(transcript, session_id="test-ganesh-cr")

    assert res["actions"], "Should contain actions"
    act = res["actions"][0]
    assert act["tool"] == "add_credit", f"Expected add_credit, got {act['tool']}"
    assert act["args"]["amount"] == 500.0
    assert act["args"]["customer_name"] == "गणेश"

    # Verify DB record
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_roman FROM customers WHERE name = 'गणेश' OR lower(name_roman) = 'ganesh';")
        cust = cur.fetchone()
        assert cust is not None, "Customer 'गणेश' must be created in DB"
        assert "sunita" not in cust["name_roman"].lower()

        cur.execute("SELECT kind, amount_paise FROM ledger_entries WHERE customer_id = ?;", (cust["id"],))
        entry = cur.fetchone()
        assert entry is not None, "Ledger entry must exist"
        assert entry["kind"] == "CREDIT", f"Expected CREDIT, got {entry['kind']}"
        assert entry["amount_paise"] == 50000

    # Verify reply text template
    assert "गणेश: ₹500 udhaar likh diya" in res["reply_text"]
    assert "sunita" not in res["reply_text"].lower()

@pytest.mark.asyncio
async def test_ganesh_payment():
    """STT 'गणेश ने 500 दिए' must be PAYMENT for Ganesh."""
    transcript = "गणेश ने 500 दिए"
    res = await VoicePipeline.run_turn(transcript, session_id="test-ganesh-pm")

    assert res["actions"], "Should contain actions"
    act = res["actions"][0]
    assert act["tool"] == "record_payment", f"Expected record_payment, got {act['tool']}"
    assert act["args"]["amount"] == 500.0
    assert act["args"]["customer_name"] == "गणेश"

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_roman FROM customers WHERE name = 'गणेश' OR lower(name_roman) = 'ganesh';")
        cust = cur.fetchone()
        assert cust is not None, "Customer 'गणेश' must exist"

        cur.execute("SELECT kind, amount_paise FROM ledger_entries WHERE customer_id = ?;", (cust["id"],))
        entry = cur.fetchone()
        assert entry is not None, "Ledger entry must exist"
        assert entry["kind"] == "PAYMENT", f"Expected PAYMENT, got {entry['kind']}"
        assert entry["amount_paise"] == 50000

    assert "गणेश: ₹500 jama kar diya" in res["reply_text"]

@pytest.mark.asyncio
async def test_ganesh_credit_short():
    """STT 'ganesh ko udhaar 200' must be CREDIT for Ganesh for ₹200."""
    transcript = "ganesh ko udhaar 200"
    res = await VoicePipeline.run_turn(transcript, session_id="test-ganesh-200")

    assert res["actions"], "Should contain actions"
    act = res["actions"][0]
    assert act["tool"] == "add_credit"
    assert act["args"]["amount"] == 200.0
    assert "ganesh" in act["args"]["customer_name"].lower()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_roman FROM customers WHERE lower(name) = 'ganesh' OR lower(name_roman) = 'ganesh';")
        cust = cur.fetchone()
        assert cust is not None

        cur.execute("SELECT kind, amount_paise FROM ledger_entries WHERE customer_id = ?;", (cust["id"],))
        entry = cur.fetchone()
        assert entry["kind"] == "CREDIT"
        assert entry["amount_paise"] == 20000

    assert "₹200 udhaar likh diya" in res["reply_text"]

@pytest.mark.asyncio
async def test_no_name_clarify():
    """STT '500 ka udhaar likh do' must clarify 'Kiska khaata?' with zero DB writes."""
    transcript = "500 ka udhaar likh do"
    res = await VoicePipeline.run_turn(transcript, session_id="test-no-name")

    assert res["actions"] == [], "Must not execute any actions when name is missing"
    assert "kiska khaata" in res["reply_text"].lower()

    # Verify zero DB writes occurred for this turn
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ledger_entries WHERE utterance_id = ?;", (res["turn_id"],))
        count = cur.fetchone()[0]
        assert count == 0, "No ledger entry should be created without customer name"

@pytest.mark.asyncio
async def test_ramesh_balance():
    """STT 'ramesh ka hisaab batao' must query balance without creating transactions."""
    transcript = "ramesh ka hisaab batao"
    res = await VoicePipeline.run_turn(transcript, session_id="test-bal")

    assert res["actions"], "Should return get_balance action"
    act = res["actions"][0]
    assert act["tool"] == "get_balance"
    assert "ramesh" in act["args"]["customer_name"].lower()

    # Verify NO ledger entries were created
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ledger_entries WHERE customer_id IN (SELECT id FROM customers WHERE lower(name) = 'ramesh');")
        assert cur.fetchone()[0] == 0, "Balance query must never insert ledger entries"

@pytest.mark.asyncio
async def test_parchi_devanagari():
    """STT 'दादाजी की दवा Paracetamol 8:00 बजे याद दिलाओ।' must extract Dadaji & Paracetamol."""
    transcript = "दादाजी की दवा Paracetamol 8:00 बजे याद दिलाओ।"
    res = await VoicePipeline.run_turn(transcript, session_id="test-parchi-dev")

    assert res["actions"], "Should parse prescription action"
    act = res["actions"][0]
    assert act["tool"] == "save_prescription"
    args = act["args"]
    assert args["patient_label"] == "दादाजी", f"Expected patient दादाजी, got {args['patient_label']}"
    assert len(args["medicines"]) > 0
    assert "paracetamol" in args["medicines"][0]["name"].lower(), f"Expected Paracetamol, got {args['medicines'][0]['name']}"

    # Verify reply text mentions Dadaji and Paracetamol
    assert "दादाजी" in res["reply_text"]
    assert "Paracetamol" in res["reply_text"]
    assert "Maa ke liye BP ki goli" not in res["reply_text"]

@pytest.mark.asyncio
async def test_parchi_roman():
    """STT 'dadaji ki dawaai paracetamol 8 baje yaad dilao' must extract Dadaji & Paracetamol."""
    transcript = "dadaji ki dawaai paracetamol 8 baje yaad dilao"
    res = await VoicePipeline.run_turn(transcript, session_id="test-parchi-rom")

    assert res["actions"], "Should parse prescription action"
    act = res["actions"][0]
    assert act["tool"] == "save_prescription"
    args = act["args"]
    assert "dadaji" in args["patient_label"].lower()
    assert len(args["medicines"]) > 0
    assert "paracetamol" in args["medicines"][0]["name"].lower()

    # Verify reply text
    assert "Dadaji" in res["reply_text"]
    assert "Paracetamol" in res["reply_text"]
    assert "Maa ke liye BP ki goli" not in res["reply_text"]

@pytest.mark.asyncio
async def test_parchi_no_patient():
    """Medicine reminder with no explicit patient must not hallucinate 'Maa' or any name."""
    transcript = "paracetamol 8 baje yaad dilao"
    res = await VoicePipeline.run_turn(transcript, session_id="test-parchi-nopatient")

    assert res["actions"]
    act = res["actions"][0]
    assert act["tool"] == "save_prescription"
    assert act["args"]["patient_label"] is None
    assert "paracetamol" in act["args"]["medicines"][0]["name"].lower()
    assert "Maa" not in res["reply_text"]
    assert "Paracetamol: 08:00 baje" in res["reply_text"]

@pytest.mark.asyncio
async def test_parchi_marathi():
    """Marathi medicine reminder with Devanagari numerals must be accurately localized."""
    transcript = "दादाजींचे औषध ८ वाजता आठवण करा"
    res = await VoicePipeline.run_turn(transcript, session_id="test-parchi-mr")

    assert res["actions"]
    act = res["actions"][0]
    assert act["tool"] == "save_prescription"
    assert res["language"] == "mr"
    assert "दादाजी" in res["reply_text"]
    assert "मी आठवण करून देईन" in res["reply_text"]
