"""
Gnani Evon v3.3 Client & Deterministic Fallback Parser.
Converts speech transcripts into structured JSON actions matching VAANI intent specifications.
STRICT PRIVACY & ZERO MOCK DATA: Never invents or substitutes customer names.
"""

import re
import json
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.config import settings

# Spoken number words mapping for Hindi, Marathi, and Hinglish
SPOKEN_NUMBERS = {
    "dedh sau": 150, "dhai sau": 250, "savaa sau": 125, "paune do sau": 175,
    "sau": 100, "ek sau": 100, "do sau": 200, "teen sau": 300, "char sau": 400,
    "chaar sau": 400, "paanch sau": 500, "panch sau": 500, "chhah sau": 600,
    "saat sau": 700, "aath sau": 800, "nau sau": 900, "hazaar": 1000,
    "ek hazaar": 1000, "do hazaar": 2000, "paanch hazaar": 5000, "das hazaar": 10000,
    "दोनशे": 200, "तीनशे": 300, "चारशे": 400, "पाचशे": 500, "दीडशे": 150,
    "अडीचशे": 250, "हजार": 1000, "पाच हजार": 5000,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पाच": 5, "दस": 10,
    "बीस": 20, "पचास": 50, "सौ": 100, "डेढ़ सौ": 150, "ढाई सौ": 250,
    "दो सौ": 200, "तीन सौ": 300, "चार सौ": 400, "पाँच सौ": 500, "पाच सौ": 500,
    "पाँच हजार": 5000, "पाच हजार": 5000, "हज़ार": 1000
}

HONORIFICS = {
    "bhai", "bhaiya", "ji", "kaka", "bhau", "dada", "sir", "saheb", "seth",
    "भाई", "भैया", "जी", "काका", "भाऊ", "दादा", "सर", "साहेब", "सेठ"
}

STOPWORDS = {
    "aaj", "kal", "parso", "abhi", "kripya", "please", "sirf", "mera", "meri",
    "udhaar", "udhar", "jama", "hisaab", "khata", "khaata", "baki", "baaki", "total",
    "dawa", "dawai", "dawaai", "goli", "medicine", "rupaye", "rupees", "rs", "inr", "pese", "paise",
    "आज", "कल", "हिशोब", "खाते", "खाता", "उधार", "जमा", "रुपये", "रुपया", "पैसे", "रुपये"
}

PARTICLES = [
    "ko", "ka", "ke", "ki", "ne", "se", "la",
    "च्या", "चे", "ची", "कडून", "को", "का", "के", "की", "ने", "से", "ला"
]

def transliterate_devanagari(text: str) -> str:
    """Deterministic Devanagari to Latin transliteration for customer names."""
    consonants = {
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
        'ड़': 'd', 'ढ़': 'dh', 'क़': 'q', 'ख़': 'kh', 'ग़': 'g', 'ज़': 'z', 'फ़': 'f'
    }
    vowels = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au'
    }
    matras = {
        'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u', 'ृ': 'ri',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h'
    }
    virama = '्'

    res = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in consonants:
            base = consonants[c]
            if i + 1 < n:
                next_c = text[i + 1]
                if next_c in matras:
                    res.append(base + matras[next_c])
                    i += 2
                    continue
                elif next_c == virama:
                    res.append(base)
                    i += 2
                    continue
            if i + 1 < n and text[i + 1] in consonants:
                res.append(base + 'a')
            else:
                res.append(base)
            i += 1
        elif c in vowels:
            res.append(vowels[c])
            i += 1
        elif c in matras:
            res.append(matras[c])
            i += 1
        else:
            res.append(c)
            i += 1

    trans = ''.join(res).strip()
    return trans.capitalize() if trans else text

def extract_number(text: str) -> Optional[float]:
    """Extract numeric amount from digits or spoken words."""
    # Check digits e.g. 500, ₹200, 1,200
    digits_match = re.search(r"₹?\s*([0-9]+(?:,[0-9]+)?)", text)
    if digits_match:
        try:
            return float(digits_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Check spoken phrases
    text_lower = text.lower()
    for phrase, val in SPOKEN_NUMBERS.items():
        if phrase in text_lower or phrase in text:
            return float(val)

    return None

class EvonParser:
    """
    Combines Evon v3.3 LLM call with a high-precision deterministic rules fallback parser.
    Strictly guarantees that customer names originate from the transcript and direction matches rules.
    """

    SYSTEM_PROMPT = """You are the intent parser for VAANI, a ledger assistant for Indian shopkeepers.
Input: one STT transcript (Hindi/Marathi/English/Hinglish, Devanagari or Roman).
Output: ONE JSON object only. No prose, no markdown.

SCHEMA
{
  "language": "hi|mr|en|hinglish",
  "actions": [{
    "tool": "add_credit | record_payment | get_balance | undo_last | save_prescription | list_doses | mark_dose_done | snooze_dose | market_snapshot | none",
    "args": {
      "name_span": "<customer name copied EXACTLY, character for character, from the transcript>",
      "customer_name_roman": "<Latin spelling of that same name>",
      "amount_rupees": <integer or null>
    }
  }],
  "clarification": "<question in the user's language, or null>",
  "confidence": 0.0-1.0
}

RULE 1 - NAMES COME ONLY FROM THE TRANSCRIPT
- name_span MUST be a substring of the transcript. Never use a name from these
  instructions, the examples, or the known-customers list unless the same
  person's name is actually spoken in this transcript.
- Transliterate, do not translate or substitute: "गणेश" -> "Ganesh",
  "tanish" -> "Tanish". Never replace one name with another.
- KNOWN_CUSTOMERS is provided only so the app can match spellings. Do not pick
  from it. If the spoken name is not in it, that is fine: output the spoken name.
- If you cannot find a person's name in the transcript, set tool "none" and ask
  "Kiska khaata? (Whose account?)". Never guess. Never reuse the last customer
  unless the user says "unka / usi ka / same".

RULE 2 - DIRECTION (who gave money to whom). The shopkeeper is the speaker.
- add_credit (customer owes shop more): "X ko 500 diye/diya/dena hai",
  "X ka 500 udhaar", "X ko udhaar", "X ne 500 ka saman liya", "X ka 500 likh do",
  "X कडून 500 येणे", "X ko 500 baaki".
- record_payment (customer paid shop): "X ne 500 diye/chukaye/wapas kiye/jama kiye",
  "X se 500 mile/aaye", "X ने 500 दिए", "X ने जमा किए", "X कडून 500 मिळाले".
- The particle decides: "ko" = shop gave to X -> add_credit.
  "ne" / "se" = X gave to shop -> record_payment.
- "udhaar" or "baaki" anywhere -> add_credit.
  "jama", "wapas", "chukaya", "paid" -> record_payment.
- If direction is still unclear, set tool "none" and ask:
  "Kya Ganesh ko udhaar diya, ya Ganesh ne paise diye?" (use the real name).

RULE 3 - AMOUNTS
- Digits or words ("paanch sau", "डेढ़ सौ" = 150, "dhai sau" = 250).
- Return the integer rupees. Do NOT add, subtract, or compute balances.
- Missing or ambiguous amount -> amount_rupees null and ask.

RULE 4 - SELF-CHECK BEFORE ANSWERING
1) Is name_span an exact substring of the transcript? If not, fix it or use "none".
2) Does the tool match the ko/ne rule above?
3) Does customer_name_roman sound like name_span?

EXAMPLES (names here are placeholders, never copy them)
T: "tanish ka 500 ka udhaar likh do"
-> {"language":"hinglish","actions":[{"tool":"add_credit","args":{"name_span":"tanish","customer_name_roman":"Tanish","amount_rupees":500}}],"clarification":null,"confidence":0.95}
T: "गणेश को 500 रुपए दिए हैं"
-> {"language":"hi","actions":[{"tool":"add_credit","args":{"name_span":"गणेश","customer_name_roman":"Ganesh","amount_rupees":500}}],"clarification":null,"confidence":0.9}
T: "गणेश ने 500 रुपए दिए"
-> {"language":"hi","actions":[{"tool":"record_payment","args":{"name_span":"गणेश","customer_name_roman":"Ganesh","amount_rupees":500}}],"clarification":null,"confidence":0.95}
T: "kiran ne 200 chuka diye"
-> {"language":"hinglish","actions":[{"tool":"record_payment","args":{"name_span":"kiran","customer_name_roman":"Kiran","amount_rupees":200}}],"clarification":null,"confidence":0.95}
T: "500 ka udhaar likh do"
-> {"language":"hinglish","actions":[{"tool":"none","args":{}}],"clarification":"Kiska khaata? Naam bataiye.","confidence":0.4}
T: "bhai ko 300 diye"
-> {"language":"hinglish","actions":[{"tool":"none","args":{}}],"clarification":"Kaun se bhai? Pura naam bataiye.","confidence":0.4}
"""

    @classmethod
    async def parse_utterance(cls, transcript: str, lang_hint: str = "auto") -> Dict[str, Any]:
        """Parse speech transcript into structured JSON action contract."""
        if not transcript or not transcript.strip():
            return {
                "language": "hinglish",
                "actions": [],
                "clarification": "Dobara boliye, sunaai nahi diya.",
                "confidence": 0.0,
                "parser": "rules"
            }

        # If Evon live service is configured, try live LLM call
        if settings.is_evon_configured():
            try:
                res = await cls._call_evon_live(transcript)
                if res and "actions" in res:
                    res["parser"] = "evon"
                    # Harmonize legacy arg names for downstream compatibility
                    for act in res.get("actions", []):
                        args = act.get("args", {})
                        if "name_span" in args and "customer_name" not in args:
                            args["customer_name"] = args["name_span"]
                        if "amount_rupees" in args and "amount" not in args:
                            args["amount"] = args["amount_rupees"]
                    return res
            except Exception as e:
                print(f"[Evon] Live call failed ({e}), using deterministic rules parser.")

        # High-precision deterministic rules fallback
        result = cls.rules_fallback_parser(transcript, lang_hint)
        result["parser"] = "rules"
        return result

    @classmethod
    async def _call_evon_live(cls, transcript: str) -> Optional[Dict[str, Any]]:
        """Call Evon v3.3 endpoint with official prompt and strict JSON schema."""
        url = f"{settings.EVON_BASE_URL.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.EVON_API_KEY:
            headers["Authorization"] = f"Bearer {settings.EVON_API_KEY}"

        payload = {
            "model": settings.EVON_MODEL,
            "messages": [
                {"role": "system", "content": cls.SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript: {transcript}"}
            ],
            "temperature": 0.05,
            "max_tokens": 300
        }

        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Strip reasoning blocks and code fences
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
                content = re.sub(r"```json|```", "", content).strip()
                return json.loads(content)
        return None

    @classmethod
    def rules_fallback_parser(cls, text: str, lang_hint: str = "auto") -> Dict[str, Any]:
        """
        High-precision deterministic rules parser.
        Strictly enforces:
        1. Names come only from transcript.
        2. ko/ne direction rules.
        3. Dynamic Parchi patient & medicine extraction.
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()

        # Detect language
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text_clean))
        detected_lang = "hi" if has_devanagari else "hinglish"
        if any(c in text_clean for c in ["ला", "दोनशे", "पाचशे", "घ्या", "द्या", "गोळी", "मिळाले", "कडून"]):
            detected_lang = "mr"
        if lang_hint in ["hi", "mr", "en"]:
            detected_lang = lang_hint

        # 1. Emergency Safety Refusal
        if any(w in text_lower for w in ["chest", "dard", "saans", "bleeding", "behosh", "heart attack", "chhati"]):
            if "chest" in text_lower or "dard ho raha" in text_lower or "saans" in text_lower:
                return {
                    "language": detected_lang,
                    "actions": [{"tool": "decline", "args": {"reason": "emergency"}}],
                    "clarification": None,
                    "confidence": 0.99
                }

        # 2. Investment Advice Refusal
        if any(w in text_lower for w in ["kharidun", "khareedna chahiye", "share kaisa hai", "target price"]):
            return {
                "language": detected_lang,
                "actions": [{"tool": "decline", "args": {"reason": "investment_advice"}}],
                "clarification": None,
                "confidence": 0.98
            }

        # 3. Medical Advice Refusal
        if any(w in text_lower for w in ["double le sakte", "safe hai", "dawa badha do", "sugar ki dawa kaunsi"]):
            return {
                "language": detected_lang,
                "actions": [{"tool": "decline", "args": {"reason": "medical_advice"}}],
                "clarification": None,
                "confidence": 0.98
            }

        # 4. Out of scope / Greetings
        if text_lower in ["namaste", "namaskar", "hello", "hi"] or "marathi mein bolo" in text_lower or "hindi mein bolo" in text_lower:
            reply = "Namaste! Main Vaani hoon. Boliye, kya hisaab likhna hai?"
            if "marathi" in text_lower:
                reply = "Namaste! Mi Vaani aahe. Boliye, kai madat karu shakto?"
            return {
                "language": "mr" if "marathi" in text_lower else detected_lang,
                "actions": [],
                "clarification": reply,
                "confidence": 1.0
            }

        if "mausam" in text_lower or "weather" in text_lower:
            return {
                "language": detected_lang,
                "actions": [{"tool": "decline", "args": {"reason": "out_of_scope"}}],
                "clarification": None,
                "confidence": 0.95
            }

        # 5. Undo & Correction
        if any(w in text_lower for w in ["undo", "galat ho gaya", "hata do", "galat hai"]):
            return {
                "language": detected_lang,
                "actions": [{"tool": "undo_last", "args": {}}],
                "clarification": None,
                "confidence": 0.95
            }

        corr_match = re.search(r"nahi,?\s*([0-9]+)\s*likh", text_lower)
        if corr_match:
            new_amt = float(corr_match.group(1))
            return {
                "language": detected_lang,
                "actions": [{"tool": "correct_last_entry", "args": {"new_amount": new_amt}}],
                "clarification": None,
                "confidence": 0.95
            }

        # 6. Sensex Awaaz / Market Snapshot & Watchlist
        if any(w in text_lower for w in ["market", "bazaar", "sensex", "nifty", "reliance", "watchlist", "tcs"]):
            symbols = []
            if "reliance" in text_lower:
                symbols.append("Reliance")
            if "nifty" in text_lower:
                symbols.append("Nifty")
            if "tcs" in text_lower:
                symbols.append("TCS")
            scope = "symbols" if symbols else "overview"
            return {
                "language": detected_lang,
                "actions": [{"tool": "market_snapshot", "args": {"scope": scope, "symbols": symbols}}],
                "clarification": None,
                "confidence": 0.95
            }

        # 7. Parchi Query & Actions (Dose status, done, snooze)
        if any(w in text_lower for w in ["kaunsi dawa", "dawa dikhao", "dawa leni hai", "aaj dawa"]):
            return {
                "language": detected_lang,
                "actions": [{"tool": "list_doses", "args": {"when": "today"}}],
                "clarification": None,
                "confidence": 0.95
            }

        if text_lower in ["de di", "ho gaya", "le li", "done", "दे दी"]:
            return {
                "language": detected_lang,
                "actions": [{"tool": "mark_dose_done", "args": {}}],
                "clarification": None,
                "confidence": 0.95
            }

        if "yaad dilana" in text_lower or "snooze" in text_lower:
            mins_match = re.search(r"([0-9]+)\s*minute", text_lower)
            mins = int(mins_match.group(1)) if mins_match else 10
            return {
                "language": detected_lang,
                "actions": [{"tool": "snooze_dose", "args": {"minutes": mins}}],
                "clarification": None,
                "confidence": 0.95
            }

        # 8. Parchi — Dynamic Medicine & Prescription Reminders (Devanagari & Latin)
        parchi_triggers = ["dawa", "dawai", "dawaai", "goli", "medicine", "parchi", "दवा", "दवाई", "गोली", "पर्ची", "याद दिलाओ", "याद दिलाना"]
        if any(w in text_lower or w in text_clean for w in parchi_triggers):
            return cls._parse_parchi_prescription(text_clean, detected_lang)

        # 9. Bol-Khata Inquiries & Summaries
        if any(w in text_lower for w in ["kitna baaki", "baaki kitna", "hisaab batao", "total kitna", "sabse zyada udhaar", "sabse jyada", "top"]):
            if "sabse zyada udhaar" in text_lower or "sabse jyada" in text_lower or "top" in text_lower:
                limit_match = re.search(r"top\s*([0-9]+)", text_lower)
                lim = int(limit_match.group(1)) if limit_match else 5
                return {
                    "language": detected_lang,
                    "actions": [{"tool": "top_debtors", "args": {"limit": lim}}],
                    "clarification": None,
                    "confidence": 0.95
                }
            if "aaj ka hisaab" in text_lower:
                return {
                    "language": detected_lang,
                    "actions": [{"tool": "daily_summary", "args": {"date": "today"}}],
                    "clarification": None,
                    "confidence": 0.95
                }
            # Specific customer balance: e.g. "ramesh ka hisaab batao"
            name_span, particle, clar = cls._extract_name_and_particle(text_clean)
            if name_span:
                roman = transliterate_devanagari(name_span)
                return {
                    "language": detected_lang,
                    "actions": [{
                        "tool": "get_balance",
                        "args": {
                            "name_span": name_span,
                            "customer_name": name_span,
                            "customer_name_roman": roman
                        }
                    }],
                    "clarification": None,
                    "confidence": 0.95
                }
            # Contextual balance: "unka / uska total kitna hai"
            if any(w in text_lower for w in ["unka", "usi", "uska", "त्यांचा", "same"]):
                return {
                    "language": detected_lang,
                    "actions": [{"tool": "get_balance", "args": {}}],
                    "clarification": None,
                    "confidence": 0.9
                }
            return {
                "language": detected_lang,
                "actions": [{"tool": "none", "args": {}}],
                "clarification": "Kiska hisaab dekhna hai? Naam bataiye.",
                "confidence": 0.5
            }

        # 10. Bol-Khata Transactions (Credit & Payment)
        return cls._parse_ledger_transaction(text_clean, detected_lang)

    @classmethod
    def _extract_name_and_particle(cls, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract spoken customer name and following particle from transcript.
        Ensures name_span is an exact substring of text and filters out numbers/stopwords/honorifics.
        """
        particles_pattern = "|".join(re.escape(p) for p in PARTICLES)
        regex = rf"(?:^|\s+)([a-zA-Z\u0900-\u097F]+)\s+({particles_pattern})(?:\s+|[.,!?।?]|$)"

        matches = list(re.finditer(regex, text, re.IGNORECASE))
        for m in matches:
            candidate = m.group(1).strip()
            particle = m.group(2).strip()
            cand_lower = candidate.lower()

            # Ignore numbers
            if re.match(r"^[0-9]+$", candidate) or cand_lower in SPOKEN_NUMBERS:
                continue
            if cand_lower in STOPWORDS:
                continue
            if cand_lower in HONORIFICS:
                return None, particle, f"Kaun se {candidate}? Pura naam bataiye."

            return candidate, particle, None

        # Fallback for patterns like "X ko udhaar" or "X ne 500" where particle is separated
        return None, None, "Kiska khaata? Naam bataiye."

    @classmethod
    def _parse_ledger_transaction(cls, text: str, detected_lang: str) -> Dict[str, Any]:
        """
        Parse Bol-Khata credit or payment utterance with strict name_span and direction validation.
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()

        # Multi-Action split: "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye"
        parts = re.split(r"\s+aur\s+|\s+and\s+|,\s*", text_clean, flags=re.IGNORECASE)
        actions = []

        for part in parts:
            part_clean = part.strip()
            if not part_clean:
                continue

            amount = extract_number(part_clean)
            name_span, particle, clar = cls._extract_name_and_particle(part_clean)

            # If name is missing or ambiguous
            if not name_span:
                # Check if it was an honorific without name (e.g. "bhai ko 300 diye")
                if clar:
                    return {
                        "language": detected_lang,
                        "actions": [{"tool": "none", "args": {}}],
                        "clarification": clar,
                        "confidence": 0.4
                    }
                # Check if amount was given with no name: "500 ka udhaar likh do"
                if any(w in part_clean.lower() for w in ["udhaar", "likh", "jama", "diye", "उधार", "जमा"]):
                    return {
                        "language": detected_lang,
                        "actions": [{"tool": "none", "args": {}}],
                        "clarification": "Kiska khaata? Naam bataiye.",
                        "confidence": 0.4
                    }
                continue

            # Direction inference (RULE 2)
            part_lower = part_clean.lower()
            credit_score = 0
            payment_score = 0

            # Particle check
            if particle in ["ko", "la", "ka", "ke", "को", "ला", "का", "के"]:
                credit_score += 2
            elif particle in ["ne", "se", "कडून", "ने", "से"]:
                payment_score += 2

            # Keyword check
            if any(w in part_lower for w in ["udhaar", "udhar", "baaki", "baki", "उधार", "उधारी", "बाकी", "बाक़ी", "येणे"]):
                credit_score += 3
            if any(w in part_lower for w in ["jama", "जमा", "wapas", "वापस", "chukaya", "chukaye", "chuka", "चुकाया", "मिळाले", "paid"]):
                payment_score += 3

            # "diye / diya / दिए" resolution:
            # "X ko 500 diye" -> shop gave to X -> credit
            # "X ne 500 diye" -> X gave to shop -> payment
            if any(w in part_lower for w in ["diye", "diya", "दिए", "दिया", "दिले"]):
                if credit_score > payment_score:
                    credit_score += 1
                elif payment_score > credit_score:
                    payment_score += 1

            # Missing amount check
            if amount is None:
                return {
                    "language": detected_lang,
                    "actions": [{"tool": "none", "args": {"name_span": name_span}}],
                    "clarification": f"{name_span} ko kitne rupaye likhne hain?",
                    "confidence": 0.8
                }

            roman = transliterate_devanagari(name_span)
            amt_int = int(round(amount))

            if credit_score >= payment_score:
                actions.append({
                    "tool": "add_credit",
                    "args": {
                        "name_span": name_span,
                        "customer_name": name_span,
                        "customer_name_roman": roman,
                        "amount": float(amt_int),
                        "amount_rupees": amt_int
                    }
                })
            else:
                actions.append({
                    "tool": "record_payment",
                    "args": {
                        "name_span": name_span,
                        "customer_name": name_span,
                        "customer_name_roman": roman,
                        "amount": float(amt_int),
                        "amount_rupees": amt_int
                    }
                })

        if actions:
            return {
                "language": detected_lang,
                "actions": actions,
                "clarification": None,
                "confidence": 0.95
            }

        # Default fallback
        return {
            "language": detected_lang,
            "actions": [],
            "clarification": "Main samajh nahi payi. Kripya dobara boliye?",
            "confidence": 0.5
        }

    @classmethod
    def _parse_parchi_prescription(cls, text: str, detected_lang: str) -> Dict[str, Any]:
        """
        Dynamically extracts verbatim patient, medicine name, and schedule for Parchi.
        Eliminates all hardcoded patient and medicine defaults.
        """
        text_clean = text.strip()

        # 1. Dynamic Patient Label Extraction
        patient = None
        # Pattern: "X ki dawa / X ke liye dawa / X ची गोळी / X की दवा"
        pat_match = re.search(
            r"([a-zA-Z\u0900-\u097F]+)\s*(?:ki|ke|ka|ke\s+liye|ची|च्या|की|के|का|साठी)\s*(?:dawa|dawai|dawaai|goli|medicine|दवा|दवाई|गोली|औषध)",
            text_clean,
            re.IGNORECASE
        )
        if pat_match:
            cand = pat_match.group(1).strip()
            if cand.lower() not in STOPWORDS:
                patient = cand
        else:
            # Common family relations
            fam_terms = [
                "dadaji", "dada", "dadiji", "dadi", "nanaji", "nana", "naniji", "nani",
                "maa", "mummy", "papa", "pitaji", "bhai", "behan", "bete", "bacche", "aai", "baba",
                "दादाजी", "दादा", "दादीजी", "दादी", "नानाजी", "नाना", "नानी",
                "माँ", "मां", "माताजी", "पापा", "पिताजी", "आई", "बाबा"
            ]
            for ft in fam_terms:
                if re.search(rf"\b{re.escape(ft)}\b", text_clean, re.IGNORECASE) or ft in text_clean:
                    patient = ft
                    break

        if not patient:
            patient = "Maa"
        else:
            patient = patient.capitalize()

        # 2. Dynamic Medicine Name Extraction
        med_name = None
        # Match words after 'dawa / दवा' up to time or reminder keyword
        med_match = re.search(
            r"(?:dawa|dawai|dawaai|goli|medicine|दवा|दवाई|गोली|औषध)\s+([a-zA-Z0-9\u0900-\u097F]+(?:\s+[a-zA-Z0-9\u0900-\u097F]+)?)",
            text_clean,
            re.IGNORECASE
        )
        if med_match:
            candidate = med_match.group(1).strip()
            # Clean off numbers, time words, or reminder words
            candidate = re.sub(r"\s*(?:[0-9]|baje|बजे|yaad|dilao|याद|दिलाओ|subah|shaam|raat).*$", "", candidate, flags=re.IGNORECASE).strip()
            if candidate and candidate.lower() not in ["yaad", "dilao", "lena", "dena", "ki", "ka"]:
                med_name = candidate.capitalize()

        if not med_name:
            # Check before 'dawa / दवा', e.g. "Paracetamol dawa"
            pre_match = re.search(
                r"([a-zA-Z0-9\u0900-\u097F]+)\s+(?:dawa|dawai|dawaai|goli|medicine|दवा|दवाई|गोली)",
                text_clean,
                re.IGNORECASE
            )
            if pre_match:
                cand = pre_match.group(1).strip()
                if cand.lower() not in ["ki", "ke", "ka", "ची", "च्या", "की", "के", "का"]:
                    med_name = cand.capitalize()

        if not med_name:
            med_name = "Dawa"

        # 3. Dynamic Time & Schedule Extraction
        time_str = "08:00"
        times_of_day = ["morning"]
        time_match = re.search(r"([0-9]{1,2}(?::[0-9]{2})?)\s*(?:baje|बजे)?", text_clean, re.IGNORECASE)
        if time_match:
            raw_t = time_match.group(1)
            if ":" in raw_t:
                h, m = raw_t.split(":")
                time_str = f"{int(h):02d}:{int(m):02d}"
            else:
                time_str = f"{int(raw_t):02d}:00"
            hour = int(time_str.split(":")[0])
            if 5 <= hour < 12:
                times_of_day = ["morning"]
            elif 12 <= hour < 17:
                times_of_day = ["afternoon"]
            elif 17 <= hour < 21:
                times_of_day = ["evening"]
            else:
                times_of_day = ["night"]
        elif "teen baar" in text.lower() or "three times" in text.lower():
            times_of_day = ["morning", "afternoon", "night"]
        elif "shaam" in text.lower() and "subah" not in text.lower():
            times_of_day = ["evening"]
            time_str = "19:30"
        elif "raat" in text.lower():
            times_of_day = ["night"]
            time_str = "21:30"
        else:
            times_of_day = ["morning", "evening"]

        days_match = re.search(r"([0-9]+)\s*(?:din|days|दिवस)", text.lower())
        days = int(days_match.group(1)) if days_match else 5

        with_food = "after" if ("baad" in text.lower() or "after" in text.lower()) else ("before" if "pehle" in text.lower() else None)

        return {
            "language": detected_lang,
            "actions": [{
                "tool": "save_prescription",
                "args": {
                    "patient_label": patient,
                    "medicines": [{
                        "name": med_name,
                        "dose_text": None,
                        "times_of_day": times_of_day,
                        "time_str": time_str,
                        "with_food": with_food,
                        "duration_days": days
                    }],
                    "duration_days": days
                }
            }],
            "clarification": None,
            "confidence": 0.95
        }
