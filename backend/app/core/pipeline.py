"""
VAANI Conversational Pipeline Orchestrator.
Orchestrates: Input -> Evon Parsing -> Guardrails -> Module Execution -> TTS -> Logging.
"""

import time
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.gnani.evon import EvonParser
from app.core.guardrails import check_guardrails, GuardrailViolation
from app.core.i18n import render_template
from app.core.session import session_manager
from app.modules.khata.service import KhataService
from app.modules.parchi.service import ParchiService
from app.modules.bazaar.service import BazaarService
from app.db.session import get_db

class VoicePipeline:
    @classmethod
    async def run_turn(cls, transcript: str, session_id: str = "default",
                       lang_hint: str = "auto", dry_run: bool = False) -> Dict[str, Any]:
        """Execute a full conversational turn."""
        t_start = time.perf_counter()
        turn_id = f"turn-{uuid.uuid4().hex[:8]}"

        # 1. Parse Utterance with Evon / Fallback Parser
        t_parse_start = time.perf_counter()
        evon_result = await EvonParser.parse_utterance(transcript, lang_hint)
        t_parse_ms = (time.perf_counter() - t_parse_start) * 1000

        language = evon_result.get("language", "hinglish")
        actions = evon_result.get("actions", [])
        clarification = evon_result.get("clarification")

        # If model asked for clarification
        if clarification and not actions:
            total_ms = (time.perf_counter() - t_start) * 1000
            cls._log_utterance(turn_id, session_id, transcript, language, evon_result, "clarify", clarification, {"parse_ms": t_parse_ms, "total_ms": total_ms})
            return {
                "turn_id": turn_id,
                "transcript": transcript,
                "language": language,
                "actions": [],
                "reply_text": clarification,
                "guardrails_passed": True,
                "timings": {"parse_ms": t_parse_ms, "total_ms": total_ms}
            }

        # 2. Guardrails Check
        validated_actions = []
        requires_confirmation = False

        for act in actions:
            try:
                g_res = check_guardrails(act, transcript)
                if not g_res["passed"]:
                    # Refusal or safety block
                    reason = g_res.get("reason", "blocked")
                    if reason == "Emergency query detected":
                        reply = render_template("decline_emergency", lang=language)
                    else:
                        reply = render_template("decline_medical", lang=language)
                    return {
                        "turn_id": turn_id,
                        "transcript": transcript,
                        "language": language,
                        "actions": [g_res["action"]],
                        "reply_text": reply,
                        "guardrails_passed": False,
                        "timings": {"parse_ms": t_parse_ms, "total_ms": (time.perf_counter() - t_start) * 1000}
                    }
                validated_actions.append(g_res["action"])
                if g_res.get("requires_confirmation"):
                    requires_confirmation = True
            except GuardrailViolation as gv:
                return {
                    "turn_id": turn_id,
                    "transcript": transcript,
                    "language": language,
                    "actions": [],
                    "reply_text": str(gv),
                    "guardrails_passed": False,
                    "timings": {"parse_ms": t_parse_ms, "total_ms": (time.perf_counter() - t_start) * 1000}
                }

        # 3. Module Dispatch & Execution
        t_exec_start = time.perf_counter()
        replies = []
        module_results = []

        if not dry_run:
            for act in validated_actions:
                tool = act["tool"]
                args = act.get("args", {})

                if tool == "add_credit":
                    res = KhataService.add_credit(
                        customer_name=args["customer_name"],
                        amount=args["amount"],
                        note=args.get("note"),
                        utterance_id=turn_id,
                        session_id=session_id,
                        lang=language
                    )
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "record_payment":
                    res = KhataService.record_payment(
                        customer_name=args["customer_name"],
                        amount=args["amount"],
                        note=args.get("note"),
                        utterance_id=turn_id,
                        session_id=session_id,
                        lang=language
                    )
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "get_balance":
                    res = KhataService.get_balance(
                        customer_name=args.get("customer_name"),
                        session_id=session_id,
                        lang=language
                    )
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "top_debtors":
                    res = KhataService.top_debtors(limit=args.get("limit", 5))
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "daily_summary":
                    res = KhataService.daily_summary()
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "undo_last":
                    res = KhataService.undo_last(session_id=session_id, lang=language)
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "draft_reminder":
                    res = KhataService.draft_reminder(customer_name=args["customer_name"], lang=language)
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "save_prescription":
                    res = ParchiService.save_prescription(
                        patient_label=args["patient_label"],
                        medicines=args.get("medicines", []),
                        doctor_note=args.get("doctor_note"),
                        duration_days=args.get("duration_days", 5),
                        utterance_id=turn_id,
                        lang=language
                    )
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "list_doses":
                    res = ParchiService.list_doses()
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "mark_dose_done":
                    res = ParchiService.mark_dose_done()
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "snooze_dose":
                    res = ParchiService.snooze_dose(minutes=args.get("minutes", 10))
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "market_snapshot":
                    res = BazaarService.market_snapshot(
                        scope=args.get("scope", "overview"),
                        symbols=args.get("symbols"),
                        lang=language
                    )
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "add_watchlist":
                    res = BazaarService.add_watchlist(symbol_or_name=args["symbol_or_name"])
                    replies.append(res["reply_text"])
                    module_results.append(res)

                elif tool == "decline":
                    reason = args.get("reason")
                    if reason == "investment_advice":
                        reply = render_template("decline_investment", lang=language)
                    elif reason == "emergency":
                        reply = render_template("decline_emergency", lang=language)
                    else:
                        reply = render_template("decline_medical", lang=language)
                    replies.append(reply)
                    module_results.append({"declined": True, "reason": reason})

        t_exec_ms = (time.perf_counter() - t_exec_start) * 1000
        combined_reply = " ".join(replies) if replies else "Aapka aadesh samajh liya gaya hai."
        total_ms = (time.perf_counter() - t_start) * 1000

        timings = {
            "parse_ms": round(t_parse_ms, 2),
            "exec_ms": round(t_exec_ms, 2),
            "total_ms": round(total_ms, 2)
        }

        # 4. Audit Log
        cls._log_utterance(turn_id, session_id, transcript, language, evon_result, "ok", combined_reply, timings)

        return {
            "turn_id": turn_id,
            "transcript": transcript,
            "language": language,
            "actions": validated_actions,
            "reply_text": combined_reply,
            "module_results": module_results,
            "guardrails_passed": True,
            "requires_confirmation": requires_confirmation,
            "timings": timings
        }

    @classmethod
    def _log_utterance(cls, turn_id: str, session_id: str, transcript: str,
                       language: str, evon_result: Dict[str, Any], status: str,
                       reply_text: str, timings: Dict[str, float]):
        """Persist turn execution to SQLite utterances table."""
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO utterances 
                    (id, session_id, transcript, detected_language, parser, llm_json, status, reply_text, timings_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        turn_id,
                        session_id,
                        transcript,
                        language,
                        evon_result.get("parser", "rules"),
                        json.dumps(evon_result),
                        status,
                        reply_text,
                        json.dumps(timings),
                        datetime.now(timezone.utc).isoformat()
                    )
                )
        except Exception as e:
            print(f"[Audit Log Error] {e}")

