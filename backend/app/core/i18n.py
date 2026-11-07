"""
VAANI Internationalization, Number Phrasing, and Spoken Reply Templates.
Supports Hindi, Marathi, Hinglish, and English.
"""

from typing import Dict, Any

def to_paise(rupees: float) -> int:
    """Convert rupee float/int to integer paise without float inaccuracy."""
    return int(round(rupees * 100))

def format_rupees(paise: int) -> str:
    """Format integer paise to standard rupee string, e.g. 85000 -> '₹850'."""
    rupees = paise / 100
    if rupees.is_integer():
        return f"₹{int(rupees):,}"
    return f"₹{rupees:,.2f}"

# Hindi number words dictionary for common currency units
HINDI_NUMBER_WORDS = {
    0: "शून्य", 1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पाँच",
    6: "छह", 7: "सात", 8: "आठ", 9: "नौ", 10: "दस",
    20: "बीस", 50: "पचास", 100: "सौ", 150: "डेढ़ सौ", 200: "दो सौ",
    250: "ढाई सौ", 300: "तीन सौ", 400: "चार सौ", 500: "पाँच सौ",
    650: "साढ़े छह सौ", 850: "साढ़े आठ सौ", 1000: "एक हज़ार",
    1200: "बारह सौ", 5000: "पाँच हज़ार"
}

MARATHI_NUMBER_WORDS = {
    0: "शून्य", 1: "एक", 2: "दोन", 3: "तीन", 4: "चार", 5: "पाच",
    6: "सहा", 7: "सात", 8: "आठ", 9: "नऊ", 10: "दहा",
    100: "शंभर", 150: "दीडशे", 200: "दोनशे", 250: "अडीचशे",
    300: "तीनशे", 400: "चारशे", 500: "पाचशे", 850: "साडे आठशे",
    1000: "एक हजार", 1200: "बाराशे"
}

def number_to_words(number: int, lang: str = "hi") -> str:
    """Return spoken words for a number in Hindi, Marathi or English."""
    if lang == "mr" and number in MARATHI_NUMBER_WORDS:
        return MARATHI_NUMBER_WORDS[number]
    if number in HINDI_NUMBER_WORDS:
        return HINDI_NUMBER_WORDS[number]
    return str(number)

TEMPLATES: Dict[str, Dict[str, str]] = {
    "add_credit": {
        "hinglish": "{customer_name} ke khaate mein {amount} jod diye. Ab unka baaki {new_balance} hai.",
        "hi": "{customer_name} के खाते में {amount} जोड़ दिए। अब उनका कुल बाक़ी {new_balance} है।",
        "mr": "{customer_name} यांच्या खात्यात {amount} उधार नोंदवले. आता त्यांची एकूण बाकी {new_balance} आहे.",
        "en": "Added credit of {amount} to {customer_name}. Total balance is now {new_balance}."
    },
    "record_payment": {
        "hinglish": "{customer_name} ke {amount} jama ho gaye. Ab unka baaki {new_balance} hai.",
        "hi": "{customer_name} के {amount} जमा हो गए। अब उनका बाक़ी {new_balance} है।",
        "mr": "{customer_name} यांच्याकडून {amount} जमा झाले. आता बाकी {new_balance} आहे.",
        "en": "Recorded payment of {amount} from {customer_name}. Outstanding balance is {new_balance}."
    },
    "payment_cleared": {
        "hinglish": "{customer_name} ke {amount} jama ho gaye. Ab unka hisaab barabar hai.",
        "hi": "{customer_name} के {amount} जमा हो गए। अब उनका कोई बाक़ी नहीं है।",
        "mr": "{customer_name} यांनी {amount} दिले. आता हिशोब पूर्ण चुकता झाला आहे.",
        "en": "Recorded {amount} from {customer_name}. Account is completely cleared."
    },
    "get_balance": {
        "hinglish": "{customer_name} ka kul baaki {balance} hai.",
        "hi": "{customer_name} का कुल बाक़ी {balance} है।",
        "mr": "{customer_name} यांची एकूण बाकी {balance} आहे.",
        "en": "{customer_name}'s current balance is {balance}."
    },
    "undo": {
        "hinglish": "Aakhri hisaab hata diya gaya hai.",
        "hi": "पिछला हिसाब हटा दिया गया है।",
        "mr": "शेवटचा हिशोब रद्द करण्यात आला आहे.",
        "en": "Last transaction has been undone."
    },
    "correction": {
        "hinglish": "Hisaab sudhaar kar {new_amount} likh diya. Naya baaki {new_balance} hai.",
        "hi": "हिसाब सुधार कर {new_amount} कर दिया। अब बाक़ी {new_balance} है।",
        "mr": "हिशोब दुरुस्त करून {new_amount} केला. आता बाकी {new_balance} आहे.",
        "en": "Corrected entry to {new_amount}. Balance is now {new_balance}."
    },
    "save_prescription": {
        "hinglish": "{patient_label} ke liye {med_name}: {schedule}. Main yaad dilaunga.",
        "hi": "{patient_label} के लिए {med_name}: {schedule}। मैं समय पर याद दिलाऊँगा।",
        "mr": "{patient_label} यांच्यासाठी {med_name}: {schedule}. मी आठवण करून देईन.",
        "en": "Saved prescription for {patient_label}: {med_name} {schedule}. Reminders scheduled."
    },
    "decline_medical": {
        "hinglish": "Kshama karein, Vaani dawa lene ya badalne ki salaah nahi deta. Kripya doctor se sampark karein.",
        "hi": "क्षमा करें, वाणी दवा लेने या बदलने की सलाह नहीं देता। कृपया डॉक्टर से पूछिए।",
        "mr": "माफ करा, वाणी औषध सल्ला देत नाही. कृपया डॉक्टरांशी संपर्क साधा.",
        "en": "I cannot provide medical advice or dosage guidance. Please consult a qualified doctor."
    },
    "decline_investment": {
        "hinglish": "Vaani share bazaar mein nivesh ki salaah nahi deta. Yeh sirf jaankari ke liye hai.",
        "hi": "वाणी शेयर बाज़ार में निवेश की सलाह नहीं देता। यह केवल जानकारी के लिए है।",
        "mr": "वाणी शेअर बाजारात गुंतवणुकीचा सल्ला देत नाही. ही फक्त माहितीसाठी आहे.",
        "en": "Vaani does not give investment advice. Market data is for information only."
    },
    "decline_emergency": {
        "hinglish": "Yeh aapaatkaal ho sakta hai! Kripya turant 108 ya paas ke hospital se sampark karein.",
        "hi": "यह आपातकाल हो सकता है! कृपया तुरंत 108 डायल करें या पास के अस्पताल जाएं।",
        "mr": "हा आणीबाणीचा प्रसंग असू शकतो! कृपया त्वरित १०८ वर कॉल करा किंवा रुग्णालयात जा.",
        "en": "This may be a medical emergency. Please call 108 or visit an emergency room immediately."
    }
}

def render_template(key: str, lang: str = "hinglish", **kwargs) -> str:
    """Render a localized reply template."""
    lang_key = lang if lang in ["hi", "mr", "en"] else "hinglish"
    template_dict = TEMPLATES.get(key, TEMPLATES["add_credit"])
    tmpl = template_dict.get(lang_key, template_dict.get("hinglish", ""))
    return tmpl.format(**kwargs)

