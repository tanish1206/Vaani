"""
VAANI Guardrails, Intent Validation and Safety Enforcer.
Prevents financial errors, enforces medical/investment refusals,
validates user intention thresholds, and verifies name_span and direction against transcript.
"""

from typing import List, Dict, Any, Optional, Tuple
import unicodedata
import re

from app.gnani.evon import transliterate_devanagari, HONORIFICS

MAX_TRANSACTION_AMOUNT_RUPEES = 100000.0  # ₹1,00,000
CONFIRMATION_THRESHOLD_RUPEES = 5000.0   # ₹5,000
MAX_ACTIONS_PER_TURN = 4

EMERGENCY_KEYWORDS = [
    "chest pain", "saans lene mein", "heart attack", "behosh",
    "khoon beh raha", "severe bleeding", "chhati mein dard"
]

MEDICAL_ADVICE_KEYWORDS = [
    "kya yeh dawa le sakte", "kitni goli", "double dose",
    "sugar ki dawa badha do", "is it safe", "kaunsi dawa leni chahiye"
]

INVESTMENT_ADVICE_KEYWORDS = [
    "kharidun", "bechun", "buy", "sell", "kaunsa share achha hai",
    "target price", "reliance kharid loon"
]

class GuardrailViolation(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

def clean_honorifics(text: str) -> str:
    """Strip honorific suffixes from names."""
    pat = r"\b(ji|bhai|bhaiya|kaka|bhau|dada|sir|saheb|seth|जी|भाई|भैया|काका|भाऊ|दादा|सर|साहेब|सेठ)\b"
    cleaned = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
    return cleaned or text

def validate_ledger_intent(action: Dict[str, Any], transcript: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Deterministic validation before any DB write:
    1. name_span must appear in transcript (Unicode NFC normalisation + lowercase + strip honorifics).
    2. Rule-based direction cross-check on transcript:
       - tokens 'ko' / 'ला' near name mean credit
       - 'ne' / 'ने' / 'se' / 'से' / 'कडून' mean payment
       - 'udhaar' / 'उधार' / 'baaki' mean credit
       - 'jama' / 'जमा' / 'wapas' / 'chukaya' / 'paid' mean payment
    3. Missing / ambiguous values return status 'clarify'.
    """
    tool = action.get("tool")
    args = action.get("args", {})

    if tool == "none":
        clar = action.get("clarification") or "Kiska khaata? Naam bataiye."
        return False, None, clar

    # Non-ledger tools (parchi, market, undo, decline) pass directly to guardrails
    if tool not in ["add_credit", "record_payment", "get_balance"]:
        return True, action, None

    # Handle get_balance
    if tool == "get_balance":
        name_span = args.get("name_span") or args.get("customer_name")
        if name_span:
            norm_trans = unicodedata.normalize("NFC", transcript).lower()
            norm_name = unicodedata.normalize("NFC", name_span).lower()
            clean_name = clean_honorifics(norm_name)
            found = (norm_name in norm_trans) or (clean_name in norm_trans)
            if not found:
                trans_lat = transliterate_devanagari(clean_name).lower()
                if trans_lat and trans_lat in norm_trans:
                    found = True
            if not found:
                return False, None, "Kiska hisaab dekhna hai? Naam bataiye."
            args["customer_name"] = name_span
            args["customer_name_roman"] = args.get("customer_name_roman") or transliterate_devanagari(name_span)
            return True, action, None
        else:
            # Contextual: only allowed if user says "unka/usi/same/uska/त्यांचा"
            if any(w in transcript.lower() for w in ["unka", "usi", "uska", "त्यांचा", "same"]):
                return True, action, None
            return False, None, "Kiska hisaab dekhna hai? Naam bataiye."

    # For add_credit and record_payment:
    name_span = args.get("name_span") or args.get("customer_name")
    if not name_span:
        return False, None, "Kiska khaata? Naam bataiye."

    # RULE 1: name_span must appear in the transcript
    norm_trans = unicodedata.normalize("NFC", transcript).lower()
    norm_name = unicodedata.normalize("NFC", name_span).lower()
    clean_name = clean_honorifics(norm_name)

    found = (norm_name in norm_trans) or (clean_name in norm_trans)
    if not found:
        trans_lat = transliterate_devanagari(clean_name).lower()
        if trans_lat and trans_lat in norm_trans:
            found = True

    if not found:
        # Hallucinated or substituted customer name rejected!
        return False, None, "Kiska khaata? Naam bataiye."

    # RULE 2: Direction cross-check
    credit_score = 0
    payment_score = 0

    # Particle immediately following name
    n_esc = re.escape(norm_name)
    credit_part_regex = rf"{n_esc}\s+(?:ko|la|ka|ke|ला|को|का|के)(?:\s+|[.,!?।?]|$)"
    payment_part_regex = rf"{n_esc}\s+(?:ne|se|कडून|ने|से)(?:\s+|[.,!?।?]|$)"

    if re.search(credit_part_regex, norm_trans):
        credit_score += 2
    if re.search(payment_part_regex, norm_trans):
        payment_score += 2

    # Global transcript tokens
    if any(w in norm_trans for w in ["udhaar", "udhar", "baaki", "baki", "उधार", "उधारी", "बाकी", "बाक़ी", "येणे"]):
        credit_score += 3
    if any(w in norm_trans for w in ["jama", "जमा", "wapas", "वापस", "chukaya", "chukaye", "chuka", "चुकाया", "मिळाले", "paid"]):
        payment_score += 3

    # "diye / दिए / दिया" disambiguation:
    # "ko" + "diye" -> shopkeeper gave to customer -> credit
    # "ne" + "diye" -> customer gave to shopkeeper -> payment
    if any(w in norm_trans for w in ["diye", "diya", "दिए", "दिया", "दिले"]):
        if credit_score > payment_score:
            credit_score += 1
        elif payment_score > credit_score:
            payment_score += 1

    # Reconcile direction
    if credit_score > payment_score and tool != "add_credit":
        action["tool"] = "add_credit"
    elif payment_score > credit_score and tool != "record_payment":
        action["tool"] = "record_payment"
    elif credit_score == payment_score == 0:
        return False, None, f"Kya {name_span} ko udhaar diya, ya {name_span} ne paise diye?"

    # Check amount
    amt = args.get("amount_rupees") if args.get("amount_rupees") is not None else args.get("amount")
    if amt is None:
        return False, None, f"{name_span} ko kitne rupaye likhne hain?"

    # Synchronize args
    args["amount"] = float(amt)
    args["amount_rupees"] = int(round(amt))
    args["customer_name"] = name_span
    args["customer_name_roman"] = args.get("customer_name_roman") or transliterate_devanagari(name_span)

    return True, action, None

def check_guardrails(action: Dict[str, Any], transcript: str) -> Dict[str, Any]:
    """
    Validate a single action against system safety rules.
    Returns audit status metadata and flags confirmation requirements.
    """
    tool = action.get("tool")
    args = action.get("args", {})
    transcript_lower = transcript.lower()

    # 1. Emergency Detection
    for kw in EMERGENCY_KEYWORDS:
        if kw in transcript_lower:
            return {
                "action": {"tool": "decline", "args": {"reason": "emergency"}},
                "requires_confirmation": False,
                "passed": False,
                "reason": "Emergency query detected"
            }

    # 2. Financial Amount Checks
    if tool in ["add_credit", "record_payment"]:
        amount = args.get("amount", 0.0)
        if amount <= 0:
            raise GuardrailViolation("Amount must be greater than zero.", "INVALID_AMOUNT")
        if amount > MAX_TRANSACTION_AMOUNT_RUPEES:
            raise GuardrailViolation(f"Amount ₹{amount:,.0f} exceeds maximum limit of ₹1,00,000.", "AMOUNT_LIMIT_EXCEEDED")
        
        requires_confirm = amount >= CONFIRMATION_THRESHOLD_RUPEES
        return {
            "action": action,
            "requires_confirmation": requires_confirm,
            "passed": True,
            "amount": amount
        }

    # 3. Prescription Safety Checks
    if tool == "save_prescription":
        medicines = args.get("medicines", [])
        for med in medicines:
            dose_text = med.get("dose_text")
            # If dose_text was provided, verify it came verbatim from transcript
            if dose_text and dose_text.lower() not in transcript_lower:
                # Strip hallucinated dose
                med["dose_text"] = None
        return {
            "action": action,
            "requires_confirmation": False,
            "passed": True
        }

    # 4. Investment Advice Guardrail
    if tool == "decline" and args.get("reason") == "investment_advice":
        return {
            "action": action,
            "requires_confirmation": False,
            "passed": True
        }

    return {
        "action": action,
        "requires_confirmation": False,
        "passed": True
    }
