"""
Official Gnani Voice Catalogue & Model Compatibility Validator.
Based directly on official Gnani documentation:
- Model A: Timbre v3.0 (timbre-v3.0) - 13 voices across 10 Indian languages.
- Model B: Timbre v2.5 (timbre-v2.5) - 42 language-specific vernacular voices.

STRICT COMPATIBILITY ENFORCEMENT:
A voice belonging to Timbre v2.5 cannot be used with Timbre v3.0.
A voice belonging to Timbre v3.0 cannot be used with Timbre v2.5.
"""

from typing import Dict, Any, List, Optional, Tuple

# All 10 Indian languages supported by Timbre v3.0
TIMBRE_V3_LANGUAGES = [
    {"code": "hi-IN", "name": "Hindi"},
    {"code": "mr-IN", "name": "Marathi"},
    {"code": "en-IN", "name": "English (India)"},
    {"code": "ta-IN", "name": "Tamil"},
    {"code": "te-IN", "name": "Telugu"},
    {"code": "kn-IN", "name": "Kannada"},
    {"code": "ml-IN", "name": "Malayalam"},
    {"code": "bn-IN", "name": "Bengali"},
    {"code": "gu-IN", "name": "Gujarati"},
    {"code": "pa-IN", "name": "Punjabi"}
]

# Model A: Timbre v3.0 Catalogue (13 Documented Voices)
TIMBRE_V3_VOICES: List[Dict[str, Any]] = [
    # Female Voices (7)
    {
        "id": "Shivani",
        "display_name": "Shivani",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Warm & Conversational",
        "description": "Default warm, natural and expressive Pan-Indian female persona.",
        "sample_text": "नमस्ते, मैं वाणी हूँ. आपकी दुकान का डिजिटल साथी."
    },
    {
        "id": "Lakshmi",
        "display_name": "Lakshmi",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Gentle & Respectful",
        "description": "Gentle, calm and clear tone suited for everyday retail updates.",
        "sample_text": "नमस्ते, आपका व्यापार खाता और हिसाब यहाँ सुरक्षित है."
    },
    {
        "id": "Kalpana",
        "display_name": "Kalpana",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Articulate & Professional",
        "description": "Crisp and professional assistant persona for clear announcements.",
        "sample_text": "नमस्कार, आज के सारे वित्तीय और दवा सम्बन्धी अपडेट तैयार हैं."
    },
    {
        "id": "Chetana",
        "display_name": "Chetana",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Lively & Upbeat",
        "description": "Upbeat, energetic and approachable voice for fast-paced retail.",
        "sample_text": "राम राम! बोलिए आज किस ग्राहक का खाता देखना है?"
    },
    {
        "id": "Vasudha",
        "display_name": "Vasudha",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Calm & Authoritative",
        "description": "Steady, trustworthy tone ideal for market summaries and medicine schedules.",
        "sample_text": "नमस्ते, आपकी हर ज़रूरी पर्ची और बाज़ार की जानकारी यहाँ है."
    },
    {
        "id": "Riyaa",
        "display_name": "Riyaa",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "en-IN",
        "primary_language_name": "Pan-India / Hinglish",
        "persona": "Modern & Bilingual",
        "description": "Youthful, modern tone fluent in code-mixed Hindi and English.",
        "sample_text": "Hello! Vaani aapke saath hai, naya transaction likhne ke liye boliye."
    },
    {
        "id": "Tarika",
        "display_name": "Tarika",
        "model": "timbre-v3.0",
        "gender": "Female",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Polite & Attentive",
        "description": "Polite, focused customer service cadence.",
        "sample_text": "नमस्ते जी, बताइए आज क्या सहायता करूँ?"
    },
    # Male Voices (6)
    {
        "id": "Avinash",
        "display_name": "Avinash",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Confident & Balanced",
        "description": "Clear, balanced and articulate Pan-Indian male voice.",
        "sample_text": "नमस्ते! मैं अविनाश. आज का हिसाब और लेन-देन देखने में मदद करूँगा."
    },
    {
        "id": "Shubham",
        "display_name": "Shubham",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Kirana Merchant",
        "description": "Energetic, grounded merchant tone tailored for dukandars.",
        "sample_text": "राम राम! शुभम हाज़िर है, बोलिए किस ग्राहक का उधार लिखना है?"
    },
    {
        "id": "Prakash",
        "display_name": "Prakash",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Authoritative & Senior",
        "description": "Authoritative, seasoned persona well-suited for market insights.",
        "sample_text": "सेंसेक्स आवाज़ और बाज़ार के ताज़ा आंकड़ों में आपका स्वागत है."
    },
    {
        "id": "Devansh",
        "display_name": "Devansh",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Courteous & Measured",
        "description": "Gentle, measured cadence with clear pronunciation.",
        "sample_text": "नमस्ते, आपकी दुकान का पूरा हिसाब-किताब व्यवस्थित रहेगा."
    },
    {
        "id": "Yashraj",
        "display_name": "Yashraj",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Strong & Professional",
        "description": "Resonant, professional baritone voice for business ledgers.",
        "sample_text": "नमस्कार! व्यापारिक लेन-देन और बकाया राशि की पूरी जानकारी यहाँ है."
    },
    {
        "id": "Harshad",
        "display_name": "Harshad",
        "model": "timbre-v3.0",
        "gender": "Male",
        "languages": ["hi-IN", "mr-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "bn-IN", "gu-IN", "pa-IN"],
        "primary_language": "hi-IN",
        "primary_language_name": "Pan-India / Hindi",
        "persona": "Conversational & Swift",
        "description": "Fast-paced, conversational and direct tone.",
        "sample_text": "नमस्ते! बोलिए, कौन सा हिसाब दर्ज करना है?"
    }
]

# Model B: Timbre v2.5 Catalogue (42 Documented Voices)
TIMBRE_V25_VOICES: List[Dict[str, Any]] = [
    # English (6)
    {"id": "Kaveri", "display_name": "Kaveri", "model": "timbre-v2.5", "gender": "Female", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Crisp Professional", "description": "Articulate Indian English voice.", "sample_text": "Hello, I am Kaveri. How can I assist you with your ledger?"},
    {"id": "Trupti", "display_name": "Trupti", "model": "timbre-v2.5", "gender": "Female", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Warm Assistant", "description": "Warm, natural Indian English tone.", "sample_text": "Hello! Your ledger balance has been updated."},
    {"id": "Devika", "display_name": "Devika", "model": "timbre-v2.5", "gender": "Female", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Measured & Clear", "description": "Measured corporate and retail assistant.", "sample_text": "Namaste, here is your daily transaction summary."},
    {"id": "Pranav", "display_name": "Pranav", "model": "timbre-v2.5", "gender": "Male", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Modern Professional", "description": "Modern urban Indian English male voice.", "sample_text": "Welcome back! Ready to record new business credit."},
    {"id": "Shlok", "display_name": "Shlok", "model": "timbre-v2.5", "gender": "Male", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Energetic & Direct", "description": "Clear and direct English persona.", "sample_text": "Sensex closed up three hundred and forty points today."},
    {"id": "Girish", "display_name": "Girish", "model": "timbre-v2.5", "gender": "Male", "languages": ["en-IN"], "primary_language": "en-IN", "primary_language_name": "English (India)", "persona": "Authoritative", "description": "Experienced and steady English voice.", "sample_text": "Your prescription reminders have been scheduled."},

    # Hindi (13)
    {"id": "Bhavna", "display_name": "Bhavna", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Warm & Natural", "description": "Default natural conversational Hindi voice for Timbre v2.5.", "sample_text": "नमस्ते, मैं भावना हूँ. आपकी दुकान का डिजिटल साथी."},
    {"id": "Nalini", "display_name": "Nalini", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Gentle & Courteous", "description": "Gentle, polite Devanagari Hindi voice.", "sample_text": "नमस्कार, आपकी हर ज़रूरी दवा और पर्ची का ध्यान मैं रखूँगी."},
    {"id": "Yashvi", "display_name": "Yashvi", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Clear & Friendly", "description": "Friendly everyday conversational Hindi.", "sample_text": "नमस्ते जी, बताइए क्या दर्ज करना है?"},
    {"id": "Urmila", "display_name": "Urmila", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Traditional & Respectful", "description": "Respectful elder retail tone.", "sample_text": "आपका खाता सुरक्षित रूप से अपडेट हो गया है."},
    {"id": "Jwala", "display_name": "Jwala", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Vibrant", "description": "Vibrant and articulate Hindi voice.", "sample_text": "राम राम! लेन-देन सफलता पूर्वक दर्ज हुआ."},
    {"id": "Chitra", "display_name": "Chitra", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Soft & Measured", "description": "Soft and steady Hindi cadence.", "sample_text": "नमस्ते, आपकी दवा का समय हो गया है."},
    {"id": "Ambuja", "display_name": "Ambuja", "model": "timbre-v2.5", "gender": "Female", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Warm Vernacular", "description": "Comfortable vernacular Hindi tone.", "sample_text": "दुकान का पूरा हिसाब वाणी संभाल लेगी."},
    {"id": "Deepak", "display_name": "Deepak", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Clear Professional", "description": "Balanced, professional Hindi male voice.", "sample_text": "नमस्ते! मैं दीपक हूँ. आज आपका हिसाब देखने में मदद करूँगा."},
    {"id": "Roopesh", "display_name": "Roopesh", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Energetic Merchant", "description": "Swift merchant tone for retail transactions.", "sample_text": "खाते में उधार सफलतापूर्वक जोड़ दिया गया है."},
    {"id": "Vikrant", "display_name": "Vikrant", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Confident & Steady", "description": "Confident, authoritative Hindi male voice.", "sample_text": "सेंसेक्स और बाज़ार के ताज़ा आंकड़ों में आपका स्वागत है."},
    {"id": "Hemraj", "display_name": "Hemraj", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Traditional Retail", "description": "Traditional Kirana trader Hindi persona.", "sample_text": "राम राम! सारा बही-खाता यहाँ तैयार है."},
    {"id": "Jalaj", "display_name": "Jalaj", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi", "persona": "Calm & Pleasant", "description": "Calm, gentle conversational male Hindi.", "sample_text": "नमस्ते, आज का कुल जमा और उधार देख सकते हैं."},
    {"id": "Omkar", "display_name": "Omkar", "model": "timbre-v2.5", "gender": "Male", "languages": ["hi-IN", "mr-IN"], "primary_language": "hi-IN", "primary_language_name": "Hindi / Marathi", "persona": "Resonant Vernacular", "description": "Resonant bilingual Hindi and Marathi male voice.", "sample_text": "नमस्ते, आपका बही-खाता पूरी तरह सुरक्षित है."},

    # Hinglish (1)
    {"id": "Poorvi", "display_name": "Poorvi", "model": "timbre-v2.5", "gender": "Female", "languages": ["en-IN", "hi-IN"], "primary_language": "hi-IN", "primary_language_name": "Hinglish", "persona": "Natural Code-Mix", "description": "Native Hinglish speaker designed for code-mixed commands.", "sample_text": "Ledger mein entry save ho gayi hai. Next kya karna hai?"},

    # Tamil (5)
    {"id": "Asmita", "display_name": "Asmita", "model": "timbre-v2.5", "gender": "Female", "languages": ["ta-IN"], "primary_language": "ta-IN", "primary_language_name": "Tamil", "persona": "Clear Vernacular", "description": "Authentic Tamil female voice.", "sample_text": "வணக்கம், உங்கள் கணக்கு விவரங்கள் இங்கே உள்ளன."},
    {"id": "Trisha", "display_name": "Trisha", "model": "timbre-v2.5", "gender": "Female", "languages": ["ta-IN"], "primary_language": "ta-IN", "primary_language_name": "Tamil", "persona": "Warm & Modern", "description": "Modern Tamil conversational tone.", "sample_text": "வணக்கம்! என்ன உதவி வேண்டும்?"},
    {"id": "Brinda", "display_name": "Brinda", "model": "timbre-v2.5", "gender": "Female", "languages": ["ta-IN"], "primary_language": "ta-IN", "primary_language_name": "Tamil", "persona": "Polite Assistant", "description": "Gentle Tamil assistant.", "sample_text": "உங்கள் மருந்து நேரம் வந்துவிட்டது."},
    {"id": "Vedika", "display_name": "Vedika", "model": "timbre-v2.5", "gender": "Female", "languages": ["ta-IN"], "primary_language": "ta-IN", "primary_language_name": "Tamil", "persona": "Articulate", "description": "Crisp Tamil speaker.", "sample_text": "வரவு செலவு விவரங்கள் புதுப்பிக்கப்பட்டன."},
    {"id": "Noopur", "display_name": "Noopur", "model": "timbre-v2.5", "gender": "Female", "languages": ["ta-IN"], "primary_language": "ta-IN", "primary_language_name": "Tamil", "persona": "Courteous", "description": "Courteous Tamil persona.", "sample_text": "வணக்கம், சந்தை தகவல்கள் தயாராக உள்ளன."},

    # Telugu (5)
    {"id": "Suhana", "display_name": "Suhana", "model": "timbre-v2.5", "gender": "Female", "languages": ["te-IN"], "primary_language": "te-IN", "primary_language_name": "Telugu", "persona": "Clear Vernacular", "description": "Clear and natural Telugu voice.", "sample_text": "నమస్కారం! మీ వ్యాపార లెక్కలు సిద్ధంగా ఉన్నాయి."},
    {"id": "Lehara", "display_name": "Lehara", "model": "timbre-v2.5", "gender": "Female", "languages": ["te-IN"], "primary_language": "te-IN", "primary_language_name": "Telugu", "persona": "Warm Assistant", "description": "Warm Telugu conversational voice.", "sample_text": "నమస్తే, మీ ఖాతా విజయవంతంగా అప్డేట్ అయింది."},
    {"id": "Lavanya", "display_name": "Lavanya", "model": "timbre-v2.5", "gender": "Female", "languages": ["te-IN"], "primary_language": "te-IN", "primary_language_name": "Telugu", "persona": "Polite", "description": "Polite everyday Telugu persona.", "sample_text": "మీ మందుల సమయం అయింది."},
    {"id": "Yukti", "display_name": "Yukti", "model": "timbre-v2.5", "gender": "Female", "languages": ["te-IN"], "primary_language": "te-IN", "primary_language_name": "Telugu", "persona": "Upbeat", "description": "Upbeat Telugu voice for commerce.", "sample_text": "నమస్తే! ఈరోజు బజారు సమాచారం."},
    {"id": "Varuni", "display_name": "Varuni", "model": "timbre-v2.5", "gender": "Female", "languages": ["te-IN"], "primary_language": "te-IN", "primary_language_name": "Telugu", "persona": "Measured", "description": "Calm Telugu cadence.", "sample_text": "మీ లావాదేవీ నమోదు చేయబడింది."},

    # Kannada (2)
    {"id": "Saanvi", "display_name": "Saanvi", "model": "timbre-v2.5", "gender": "Female", "languages": ["kn-IN"], "primary_language": "kn-IN", "primary_language_name": "Kannada", "persona": "Warm Vernacular", "description": "Natural Kannada female voice.", "sample_text": "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ವ್ಯಾಪಾರ ಖಾತೆ ಸಿದ್ಧವಾಗಿದೆ."},
    {"id": "Kavin", "display_name": "Kavin", "model": "timbre-v2.5", "gender": "Male", "languages": ["kn-IN"], "primary_language": "kn-IN", "primary_language_name": "Kannada", "persona": "Balanced Male", "description": "Clear Kannada male voice.", "sample_text": "ನಮಸ್ಕಾರ, ನಿಮ್ಮ ಲೆಕ್ಕಾಚಾರ ಸುರಕ್ಷಿತವಾಗಿದೆ."},

    # Malayalam (2)
    {"id": "Reshma", "display_name": "Reshma", "model": "timbre-v2.5", "gender": "Female", "languages": ["ml-IN"], "primary_language": "ml-IN", "primary_language_name": "Malayalam", "persona": "Articulate Female", "description": "Natural Malayalam female tone.", "sample_text": "നമസ്കാരം, നിങ്ങളുടെ അക്കൗണ്ട് വിവരങ്ങൾ ഇവിടെയുണ്ട്."},
    {"id": "Riyaan", "display_name": "Riyaan", "model": "timbre-v2.5", "gender": "Male", "languages": ["ml-IN"], "primary_language": "ml-IN", "primary_language_name": "Malayalam", "persona": "Clear Male", "description": "Clear Malayalam male persona.", "sample_text": "നമസ്കാരം, ഇന്നത്തെ വിപണി വിവരങ്ങൾ ഇതാ."},

    # Marathi (2)
    {"id": "Zahira", "display_name": "Zahira", "model": "timbre-v2.5", "gender": "Female", "languages": ["mr-IN"], "primary_language": "mr-IN", "primary_language_name": "Marathi", "persona": "Vernacular Marathi", "description": "Natural Marathi female assistant.", "sample_text": "नमस्कार! मी वाणी आहे. बोला, मी तुम्हाला कशी मदत करू शकते?"},
    {"id": "Ishaan", "display_name": "Ishaan", "model": "timbre-v2.5", "gender": "Male", "languages": ["mr-IN"], "primary_language": "mr-IN", "primary_language_name": "Marathi", "persona": "Resonant Marathi", "description": "Warm Marathi male merchant tone.", "sample_text": "नमस्कार! तुमचा खाता आणि हिशोब सुरक्षित ठेवण्यात मदत करेन."},

    # Bengali (2)
    {"id": "Kirra", "display_name": "Kirra", "model": "timbre-v2.5", "gender": "Female", "languages": ["bn-IN"], "primary_language": "bn-IN", "primary_language_name": "Bengali", "persona": "Sweet & Clear", "description": "Melodious Bengali female voice.", "sample_text": "নমস্কার! আপনার ব্যবসার হিসাব প্রস্তুত."},
    {"id": "Dhruva", "display_name": "Dhruva", "model": "timbre-v2.5", "gender": "Male", "languages": ["bn-IN"], "primary_language": "bn-IN", "primary_language_name": "Bengali", "persona": "Authoritative Male", "description": "Confident Bengali male tone.", "sample_text": "নমস্কার, আপনার আজকের লেনদেন সংরক্ষিত হয়েছে."},

    # Gujarati (2)
    {"id": "Falak", "display_name": "Falak", "model": "timbre-v2.5", "gender": "Female", "languages": ["gu-IN"], "primary_language": "gu-IN", "primary_language_name": "Gujarati", "persona": "Warm Vyapari", "description": "Expressive Gujarati female tone for retail.", "sample_text": "નમસ્તે! તમારા ખાતાની વિગતો અહીં છે."},
    {"id": "Veera", "display_name": "Veera", "model": "timbre-v2.5", "gender": "Female", "languages": ["gu-IN"], "primary_language": "gu-IN", "primary_language_name": "Gujarati", "persona": "Friendly Vernacular", "description": "Friendly Gujarati shopkeeper voice.", "sample_text": "નમસ્તે, તમારો વ્યવહાર સફળતાપૂર્વક નોંધાયો છે."},

    # Punjabi (2)
    {"id": "Mehuli", "display_name": "Mehuli", "model": "timbre-v2.5", "gender": "Female", "languages": ["pa-IN"], "primary_language": "pa-IN", "primary_language_name": "Punjabi", "persona": "Upbeat Punjabi", "description": "Warm Punjabi female voice.", "sample_text": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! ਤੁਹਾਡਾ ਖਾਤਾ ਤਿਆਰ ਹੈ."},
    {"id": "Zayan", "display_name": "Zayan", "model": "timbre-v2.5", "gender": "Male", "languages": ["pa-IN"], "primary_language": "pa-IN", "primary_language_name": "Punjabi", "persona": "Direct & Friendly", "description": "Energetic Punjabi male tone.", "sample_text": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਦੱਸੋ ਕਿਹੜਾ ਹਿਸਾਬ ਦਰਜ ਕਰਨਾ ਹੈ."}
]

# Legacy and common case aliases
VOICE_ALIASES: Dict[str, str] = {
    "sia": "Shivani",         # Legacy default maps to v3.0 default
    "shivani": "Shivani",
    "bhavna": "Bhavna",
    "deepak": "Deepak",
    "nalini": "Nalini",
    "madhuri": "Zahira",       # Older v2 alias maps to documented Marathi voice
    "radhika": "Kaveri",      # Older v2 alias maps to documented English voice
}

class VoiceCatalogService:
    """Provides voice discovery, catalog retrieval, and strict model compatibility validation."""

    @classmethod
    def get_catalog(cls) -> Dict[str, Any]:
        """Return the complete official catalogue for both models."""
        return {
            "models": [
                {
                    "id": "timbre-v3.0",
                    "display_name": "Gnani Timbre v3.0",
                    "tagline": "Flagship Sovereign AI (13 Pan-India Voices across 10 Languages)",
                    "default_voice": "Shivani",
                    "voice_count": len(TIMBRE_V3_VOICES),
                    "voices": TIMBRE_V3_VOICES
                },
                {
                    "id": "timbre-v2.5",
                    "display_name": "Gnani Timbre v2.5",
                    "tagline": "Vernacular Specialised (42 Language-Specific Voices)",
                    "default_voice": "Bhavna",
                    "voice_count": len(TIMBRE_V25_VOICES),
                    "voices": TIMBRE_V25_VOICES
                }
            ],
            "total_voices": len(TIMBRE_V3_VOICES) + len(TIMBRE_V25_VOICES)
        }

    @classmethod
    def get_voices_for_model(cls, model: str) -> List[Dict[str, Any]]:
        """Return list of supported voices for a specific model."""
        norm_model = (model or "timbre-v3.0").strip().lower()
        if norm_model in ("timbre-v3.0", "v3", "timbre-v3"):
            return TIMBRE_V3_VOICES
        elif norm_model in ("timbre-v2.5", "v2.5", "timbre-v2"):
            return TIMBRE_V25_VOICES
        return TIMBRE_V3_VOICES

    @classmethod
    def is_voice_supported_by_model(cls, model: str, voice_id: str) -> bool:
        """Check if a voice ID belongs strictly to the chosen TTS model."""
        norm_model = (model or "").strip().lower()
        norm_voice = (voice_id or "").strip().lower()

        resolved = cls.resolve_voice_id(voice_id, target_model=norm_model)

        if norm_model in ("timbre-v3.0", "v3", "timbre-v3"):
            return any(v["id"].lower() == resolved.lower() for v in TIMBRE_V3_VOICES)
        elif norm_model in ("timbre-v2.5", "v2.5", "timbre-v2"):
            return any(v["id"].lower() == resolved.lower() for v in TIMBRE_V25_VOICES)
        return False

    @classmethod
    def validate_model_and_voice(cls, model: str, voice_id: str) -> Tuple[bool, str]:
        """
        Enforce strict model compatibility.
        Returns (is_valid, error_message).
        """
        if not model or not model.strip():
            return False, "TTS model cannot be empty. Must be 'timbre-v3.0' or 'timbre-v2.5'."

        norm_model = model.strip().lower()
        if norm_model not in ("timbre-v3.0", "timbre-v2.5"):
            return False, f"Unsupported TTS model '{model}'. Supported models are 'timbre-v3.0' and 'timbre-v2.5'."

        if not voice_id or not voice_id.strip():
            return False, "Voice ID cannot be empty."

        # Check if voice is in the other model
        resolved_voice = cls.resolve_voice_id(voice_id, target_model=norm_model)

        if norm_model == "timbre-v3.0":
            if any(v["id"].lower() == resolved_voice.lower() for v in TIMBRE_V3_VOICES):
                return True, ""
            if any(v["id"].lower() == resolved_voice.lower() for v in TIMBRE_V25_VOICES):
                return False, f"Voice '{resolved_voice}' belongs to Timbre v2.5 and cannot be used with Timbre v3.0."
            return False, f"Voice '{voice_id}' is not an official Timbre v3.0 voice. Choose from: {', '.join([v['id'] for v in TIMBRE_V3_VOICES])}."

        if norm_model == "timbre-v2.5":
            if any(v["id"].lower() == resolved_voice.lower() for v in TIMBRE_V25_VOICES):
                return True, ""
            if any(v["id"].lower() == resolved_voice.lower() for v in TIMBRE_V3_VOICES):
                return False, f"Voice '{resolved_voice}' belongs to Timbre v3.0 and cannot be used with Timbre v2.5."
            return False, f"Voice '{voice_id}' is not an official Timbre v2.5 voice."

        return False, "Invalid model or voice."

    @classmethod
    def resolve_voice_id(cls, voice_id: Optional[str], target_model: str = "timbre-v3.0") -> str:
        """
        Resolve aliases or return default for the model.
        """
        if not voice_id or not voice_id.strip():
            return "Shivani" if "v3" in target_model.lower() else "Bhavna"

        lower = voice_id.strip().lower()

        # Handle legacy "sia"
        if lower == "sia":
            return "Shivani" if "v3" in target_model.lower() else "Bhavna"

        if lower in VOICE_ALIASES:
            alias_resolved = VOICE_ALIASES[lower]
            # Check if alias exists in target model
            target_list = TIMBRE_V3_VOICES if "v3" in target_model.lower() else TIMBRE_V25_VOICES
            if any(v["id"].lower() == alias_resolved.lower() for v in target_list):
                return alias_resolved

        # Search target model directly
        target_list = TIMBRE_V3_VOICES if "v3" in target_model.lower() else TIMBRE_V25_VOICES
        for v in target_list:
            if v["id"].lower() == lower:
                return v["id"]

        # Search all
        for v in TIMBRE_V3_VOICES + TIMBRE_V25_VOICES:
            if v["id"].lower() == lower:
                return v["id"]

        return "Shivani" if "v3" in target_model.lower() else "Bhavna"

    @classmethod
    def get_voice_metadata(cls, voice_id: str, model: str = "timbre-v3.0") -> Optional[Dict[str, Any]]:
        """Retrieve full voice metadata dictionary."""
        resolved = cls.resolve_voice_id(voice_id, target_model=model)
        for v in TIMBRE_V3_VOICES + TIMBRE_V25_VOICES:
            if v["id"].lower() == resolved.lower() and (v["model"].lower() == model.lower() or not model):
                return dict(v)
        return None

