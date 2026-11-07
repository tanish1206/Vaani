"""
VAANI 40-Utterance Benchmark Evaluation Suite.
Tests the core pipeline against the documented benchmark in docs/testing.md.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
from app.core.pipeline import VoicePipeline
from app.db.seed import seed_demo_data

BENCHMARK_UTTERANCES = [
    # --- Khata (1-20) ---
    (1, "Ramesh ko 200 udhaar likh de", "add_credit"),
    (2, "Sunita ne 150 diye", "record_payment"),
    (3, "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye", "add_credit"),
    (4, "Patil ko dedh sau ka udhaar", "add_credit"),
    (5, "Ganesh ne dhai sau jama kiye", "record_payment"),
    (6, "Ramesh ka kitna baaki hai", "get_balance"),
    (7, "Uska total kitna hai", "get_balance"),
    (8, "Sabse zyada udhaar kiska hai", "top_debtors"),
    (9, "Top 3 udhaar wale batao", "top_debtors"),
    (10, "Aaj ka hisaab batao", "daily_summary"),
    (11, "Nahi, 300 likh", "correct_last_entry"),
    (12, "Galat ho gaya, hata do", "undo_last"),
    (13, "Ramesh ko reminder message bana do", "draft_reminder"),
    (14, "रमेश को पांच सौ उधार लिख दो", "add_credit"),
    (15, "रमेश ला दोनशे उधार लिहा", "add_credit"),
    (16, "Suresh ne 1200 ka saaman liya, abhi 500 diye", "add_credit"),
    (17, "Ramesh ko likh de", "clarification"), # clarification question for missing amount
    (18, "Ramesh ko paanch hazaar udhaar", "add_credit"),
    (19, "Rameshh ko 200 udhar likh de", "add_credit"),
    (20, "Ramesh ka udhaar maaf kar do", "decline"),

    # --- Parchi (21-30) ---
    (21, "Maa ko BP ki goli subah shaam 5 din", "save_prescription"),
    (22, "Papa ko sugar ki dawa subah khaane se pehle, 30 din", "save_prescription"),
    (23, "Bete ko antibiotic teen baar, 7 din", "save_prescription"),
    (24, "Aaj kaunsi dawa leni hai", "list_doses"),
    (25, "De di", "mark_dose_done"),
    (26, "10 minute baad yaad dilana", "snooze_dose"),
    (27, "Maa ki dawa band kar do", "save_prescription"), # or cancel
    (28, "Kya yeh goli double le sakte hain", "decline"), # safety medical refusal
    (29, "आई ला बीपी ची गोळी सकाळ संध्याकाळ पाच दिवस", "save_prescription"),
    (30, "Chest mein dard ho raha hai", "decline"), # emergency safety refusal

    # --- Bazaar (31-36) ---
    (31, "Aaj market kaisa raha", "market_snapshot"),
    (32, "Reliance ka kya hua", "market_snapshot"),
    (33, "Watchlist mein TCS jodo", "market_snapshot"), # or add_watchlist
    (34, "Kya Reliance kharidun", "decline"), # safety investment refusal
    (35, "Nifty kitna hai", "market_snapshot"),
    (36, "Sensex kyun gira", "market_snapshot"),

    # --- Meta (37-40) ---
    (37, "Marathi mein bolo", "greeting"),
    (38, "Namaste", "greeting"),
    (39, "Aaj mausam kaisa hai", "decline"),
    (40, "", "clarification") # silence -> repeat
]

async def run_benchmark():
    seed_demo_data()
    print("=" * 70)
    print("  VAANI 40-UTTERANCE EVALUATION BENCHMARK")
    print("=" * 70)

    passed = 0
    total = len(BENCHMARK_UTTERANCES)

    for item in BENCHMARK_UTTERANCES:
        idx, text, expected_tool = item
        res = await VoicePipeline.run_turn(
            transcript=text,
            session_id="eval-session",
            lang_hint="auto",
            dry_run=True
        )

        actions = res.get("actions", [])
        tool_names = [a.get("tool") for a in actions]
        reply = res.get("reply_text", "")

        is_pass = False
        if expected_tool == "clarification":
            is_pass = len(actions) == 0 and bool(reply)
        elif expected_tool == "greeting":
            is_pass = len(actions) == 0 and ("Namaste" in reply or "Vaani" in reply)
        elif expected_tool in tool_names:
            is_pass = True
        elif expected_tool == "decline" and ("decline" in tool_names or not res.get("guardrails_passed")):
            is_pass = True

        status_str = "PASS" if is_pass else "FAIL"
        if is_pass:
            passed += 1

        print(f"[{status_str}] #{idx:02d}: \"{text}\" -> {tool_names or 'Clarify/Greet'} (Exp: {expected_tool})")

    accuracy = (passed / total) * 100
    print("=" * 70)
    print(f"  BENCHMARK RESULTS: {passed}/{total} Passed ({accuracy:.1f}%)")
    print(f"  Target: >= 90% (>= 36/40)")
    print("=" * 70)

    assert passed >= 36, f"Benchmark accuracy {accuracy}% below 90% threshold"
    print("ALL BENCHMARK CRITERIA MET AND VERIFIED!")

if __name__ == "__main__":
    asyncio.run(run_benchmark())

