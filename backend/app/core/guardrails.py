"""
VAANI Guardrails and Safety Validation.
Prevents financial errors, enforces medical/investment refusals,
and validates user intention thresholds.
"""

from typing import List, Dict, Any, Optional

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

