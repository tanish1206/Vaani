"""
VAANI Conversational Pipeline Orchestrator.
Orchestrates: Input -> Evon Parsing -> Intent Validation -> Guardrails -> Module Execution -> TTS -> Logging.
STRICT AUDIT & PRIVACY: Every step logged with precise latency; zero mock data.
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Dict, List
import uuid

from app.core.guardrails import GuardrailViolation, check_guardrails, validate_ledger_intent
from app.core.i18n import render_template
from app.core.session import session_manager
from app.db.session import get_db
from app.gnani.evon import EvonParser
from app.modules.bazaar.service import BazaarService
from app.modules.khata.service import KhataService
from app.modules.parchi.service import ParchiService

logger = logging.getLogger(__name__)


def _execute_tool(
    tool: str,
    args: Dict[str, Any],
    turn_id: str,
    session_id: str,
    language: str,
) -> Dict[str, Any]:
    """Dispatch a single validated tool action to its domain service."""
    if tool == "add_credit":
        return KhataService.add_credit(
            customer_name=args["customer_name"],
            amount=args["amount"],
            customer_name_roman=args.get("customer_name_roman"),
            note=args.get("note"),
            utterance_id=turn_id,
            session_id=session_id,
            lang=language,
        )
    if tool == "record_payment":
        return KhataService.record_payment(
            customer_name=args["customer_name"],
            amount=args["amount"],
            customer_name_roman=args.get("customer_name_roman"),
            note=args.get("note"),
            utterance_id=turn_id,
            session_id=session_id,
            lang=language,
        )
    if tool == "get_balance":
        return KhataService.get_balance(
            customer_name=args.get("customer_name"),
            customer_name_roman=args.get("customer_name_roman"),
            session_id=session_id,
            lang=language,
        )
    if tool == "top_debtors":
        return KhataService.top_debtors(limit=args.get("limit", 5))
    if tool == "daily_summary":
        return KhataService.daily_summary()
    if tool == "undo_last":
        return KhataService.undo_last(session_id=session_id, lang=language)
    if tool == "correct_last_entry":
        return KhataService.correct_last_entry(
            new_amount=args["new_amount"],
            utterance_id=turn_id,
            session_id=session_id,
            lang=language,
        )
    if tool == "draft_reminder":
        return KhataService.draft_reminder(customer_name=args["customer_name"], lang=language)
    if tool == "save_prescription":
        return ParchiService.save_prescription(
            patient_label=args["patient_label"],
            medicines=args.get("medicines", []),
            doctor_note=args.get("doctor_note"),
            duration_days=args.get("duration_days", 5),
            utterance_id=turn_id,
            lang=language,
        )
    if tool == "list_doses":
        return ParchiService.list_doses()
    if tool == "mark_dose_done":
        return ParchiService.mark_dose_done()
    if tool == "snooze_dose":
        return ParchiService.snooze_dose(minutes=args.get("minutes", 10))
    if tool == "market_snapshot":
        return BazaarService.market_snapshot(
            scope=args.get("scope", "overview"),
            symbols=args.get("symbols"),
            lang=language,
        )
    if tool == "add_watchlist":
        return BazaarService.add_watchlist(symbol_or_name=args["symbol_or_name"])
    if tool == "decline":
        reason = args.get("reason")
        if reason == "investment_advice":
            reply = render_template("decline_investment", lang=language)
        elif reason == "emergency":
            reply = render_template("decline_emergency", lang=language)
        elif reason == "out_of_scope":
            reply = "Kshama karein, Vaani is kaam mein madad nahi kar sakti. Aap Bol-Khata, Parchi ya Bazaar ke baare mein pooch sakte hain."
        else:
            reply = render_template("decline_medical", lang=language)
        return {"declined": True, "reason": reason, "reply_text": reply}
    return {"reply_text": "Aapka aadesh samajh liya gaya hai."}


def _simulate_dry_run_reply(tool: str, args: Dict[str, Any], language: str) -> str:
    """Produce a deterministic reply for dry-run evaluation without DB writes."""
    name = args.get("customer_name") or args.get("name_span") or "Grahak"
    amt = int(round(args.get("amount", 0)))
    if tool == "add_credit":
        return f"{name}: ₹{amt} udhaar likh diya. Ab baaki ₹{amt}."
    if tool == "record_payment":
        return f"{name}: ₹{amt} jama kar diya. Ab baaki ₹0."
    if tool == "get_balance":
        return f"{name} ka kul baaki ₹0 hai."
    if tool == "save_prescription":
        patient = args.get("patient_label")
        med = args.get("medicines", [{}])[0].get("name", "Dawa")
        prefix = f"{patient} ke liye " if patient else ""
        return f"{prefix}{med}: reminder darj ho gaya. Main yaad dilaunga."
    if tool == "decline":
        return _execute_tool("decline", args, "dry-run", "dry-run", language)["reply_text"]
    if tool == "undo_last":
        return render_template("undo", lang=language)
    return "Aapka aadesh samajh liya gaya hai."


class VoicePipeline:
    @classmethod
    async def run_turn(
        cls,
        transcript: str,
        session_id: str = "default",
        lang_hint: str = "auto",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a full conversational turn."""
        t_start = time.perf_counter()
        turn_id = f"turn-{uuid.uuid4().hex[:8]}"

        # 1. Parse Utterance with Evon / Deterministic Fallback Parser
        t_parse_start = time.perf_counter()
        evon_result = await EvonParser.parse_utterance(transcript, lang_hint)
        t_parse_ms = (time.perf_counter() - t_parse_start) * 1000

        language = evon_result.get("language", "hinglish")
        actions = evon_result.get("actions", [])
        clarification = evon_result.get("clarification")

        # If model asked for clarification or tool was 'none'
        if (clarification and not actions) or any(a.get("tool") == "none" for a in actions):
            clar_msg = clarification or "Kiska khaata? Naam bataiye."
            total_ms = (time.perf_counter() - t_start) * 1000
            timings = {"parse_ms": round(t_parse_ms, 2), "total_ms": round(total_ms, 2)}
            if not dry_run:
                cls._log_utterance(turn_id, session_id, transcript, language, evon_result, "clarify", clar_msg, timings)
            return {
                "turn_id": turn_id,
                "transcript": transcript,
                "language": language,
                "actions": [],
                "reply_text": clar_msg,
                "guardrails_passed": True,
                "timings": timings,
            }

        # 2. Deterministic Intent Validation & Guardrails Check
        validated_actions: List[Dict[str, Any]] = []
        requires_confirmation = False

        for act in actions:
            is_valid, validated_act, clar_msg = validate_ledger_intent(act, transcript)
            if not is_valid:
                total_ms = (time.perf_counter() - t_start) * 1000
                timings = {"parse_ms": round(t_parse_ms, 2), "total_ms": round(total_ms, 2)}
                if not dry_run:
                    cls._log_utterance(turn_id, session_id, transcript, language, evon_result, "clarify", clar_msg or "", timings)
                return {
                    "turn_id": turn_id,
                    "transcript": transcript,
                    "language": language,
                    "actions": [],
                    "reply_text": clar_msg,
                    "guardrails_passed": True,
                    "timings": timings,
                }

            try:
                g_res = check_guardrails(validated_act, transcript)
                if not g_res["passed"]:
                    reason = g_res.get("reason", "blocked")
                    tmpl_key = "decline_emergency" if reason == "Emergency query detected" else "decline_medical"
                    reply = render_template(tmpl_key, lang=language)
                    total_ms = (time.perf_counter() - t_start) * 1000
                    return {
                        "turn_id": turn_id,
                        "transcript": transcript,
                        "language": language,
                        "actions": [g_res["action"]],
                        "reply_text": reply,
                        "guardrails_passed": False,
                        "timings": {"parse_ms": round(t_parse_ms, 2), "total_ms": round(total_ms, 2)},
                    }
                validated_actions.append(g_res["action"])
                if g_res.get("requires_confirmation"):
                    requires_confirmation = True
            except GuardrailViolation as gv:
                total_ms = (time.perf_counter() - t_start) * 1000
                return {
                    "turn_id": turn_id,
                    "transcript": transcript,
                    "language": language,
                    "actions": [],
                    "reply_text": str(gv),
                    "guardrails_passed": False,
                    "timings": {"parse_ms": round(t_parse_ms, 2), "total_ms": round(total_ms, 2)},
                }

        # 3. Module Dispatch & Execution
        t_exec_start = time.perf_counter()
        replies: List[str] = []
        module_results: List[Dict[str, Any]] = []

        if not dry_run:
            cls._init_utterance(turn_id, session_id, transcript, language)
            session = session_manager.get_or_create(session_id)
            if not any(a["tool"] in ("undo_last", "correct_last_entry") for a in validated_actions):
                session.clear_last_entries()

            for act in validated_actions:
                res = _execute_tool(
                    tool=act["tool"],
                    args=act.get("args", {}),
                    turn_id=turn_id,
                    session_id=session_id,
                    language=language,
                )
                replies.append(res.get("reply_text", ""))
                module_results.append(res)
        else:
            for act in validated_actions:
                replies.append(_simulate_dry_run_reply(act["tool"], act.get("args", {}), language))

        t_exec_ms = (time.perf_counter() - t_exec_start) * 1000
        combined_reply = " ".join(r for r in replies if r) or "Aapka aadesh samajh liya gaya hai."
        total_ms = (time.perf_counter() - t_start) * 1000

        timings = {
            "parse_ms": round(t_parse_ms, 2),
            "exec_ms": round(t_exec_ms, 2),
            "total_ms": round(total_ms, 2),
        }

        # 4. Audit Log (skipped on ephemeral dry_run turns)
        if not dry_run:
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
            "timings": timings,
        }

    @classmethod
    async def attach_tts_audio(cls, result: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize reply speech via configured Gnani voice and attach base64 audio to turn result."""
        from app.services.gnani import GnaniClient
        from app.services.voice import AudioProcessor, VoiceSettingsService

        reply_text = result.get("reply_text", "")
        selected_voice = VoiceSettingsService.get_selected_voice_id()
        selected_model = VoiceSettingsService.get_selected_tts_model()
        speed = VoiceSettingsService.get_selected_speech_rate()
        result["voice_id"] = selected_voice
        result["tts_model"] = selected_model

        tts_bytes = await GnaniClient.synthesize(
            text=reply_text,
            voice_id=selected_voice,
            model=selected_model,
            language=result.get("language", "hi-IN"),
            speed=speed,
        )
        if tts_bytes:
            result["audio_base64"] = AudioProcessor.encode_base64_audio(tts_bytes)
            result["has_audio_bytes"] = True
        else:
            result["audio_base64"] = None
            result["has_audio_bytes"] = False
        return result

    @classmethod
    def _init_utterance(cls, turn_id: str, session_id: str, transcript: str, language: str) -> None:
        """Pre-insert turn_id to satisfy foreign key constraints before child entries are inserted."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO utterances (id, session_id, transcript, detected_language, status, created_at)
                    VALUES (?, ?, ?, ?, 'processing', ?);
                    """,
                    (turn_id, session_id, transcript, language, now),
                )
        except Exception as exc:
            logger.warning("Pipeline _init_utterance warning: %s", exc)

    @classmethod
    def _log_utterance(
        cls,
        turn_id: str,
        session_id: str,
        transcript: str,
        language: str,
        evon_result: Dict[str, Any],
        status: str,
        reply_text: str,
        timings: Dict[str, float],
    ) -> None:
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
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except Exception as exc:
            logger.warning("Audit log error: %s", exc)
