"""
Gnani Voice Catalogue & Discovery Service.
Provides supported voices verified directly against Gnani's Timbre v2.5 / v3.0 voice catalogue.
"""

from typing import Dict, Any, List, Optional
import httpx
from app.services.gnani.config import GnaniConfig
from app.services.gnani.exceptions import GnaniVoiceNotFoundError

# Official Gnani Timbre Supported Voice Catalogue
GNANI_VOICE_CATALOGUE: List[Dict[str, Any]] = [
    {
        "id": "Bhavna",
        "display_name": "Bhavna",
        "language_code": "hi-IN",
        "language_name": "Hindi / Hinglish",
        "gender": "Female",
        "characteristics": "Warm, natural conversational tone (Default)",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्ते, मैं वाणी हूँ. आपकी दुकान का डिजिटल साथी."
    },
    {
        "id": "Deepak",
        "display_name": "Deepak",
        "language_code": "hi-IN",
        "language_name": "Hindi / Hinglish",
        "gender": "Male",
        "characteristics": "Clear, professional and balanced tone",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्ते! मैं दीपक हूँ. आज आपका खाता और हिसाब देखने में मदद करूँगा."
    },
    {
        "id": "Madhuri",
        "display_name": "Madhuri",
        "language_code": "mr-IN",
        "language_name": "Marathi / Hindi",
        "gender": "Female",
        "characteristics": "Expressive Marathi & Devanagari vernacular",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्कार! मी वाणी आहे. बोला, मी तुम्हाला कशी मदत करू शकते?"
    },
    {
        "id": "Radhika",
        "display_name": "Radhika",
        "language_code": "en-IN",
        "language_name": "English (India) / Hinglish",
        "gender": "Female",
        "characteristics": "Articulate, crisp and modern bilingual tone",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "Hello! I am Vaani. How can I assist you with your business ledger today?"
    },
    {
        "id": "Gaurav",
        "display_name": "Gaurav",
        "language_code": "hi-IN",
        "language_name": "Hindi / Hinglish",
        "gender": "Male",
        "characteristics": "Lively Kirana merchant and energetic tone",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "राम राम! मैं गौरव. बोलिए किस ग्राहक का उधार या जमा लिखना है?"
    },
    {
        "id": "Nalini",
        "display_name": "Nalini",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Female",
        "characteristics": "Formal, courteous and gentle tone",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्कार, आपकी हर ज़रूरी दवा और पर्ची का ध्यान मैं रखूँगी."
    },
    {
        "id": "Vikrant",
        "display_name": "Vikrant",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Male",
        "characteristics": "Calm, authoritative and confident voice",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्ते, सेंसेक्स आवाज़ और बाज़ार के हिसाब में आपका स्वागत है."
    },
    {
        "id": "Aarohi",
        "display_name": "Aarohi",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Female",
        "characteristics": "Soft, friendly and pleasant tone",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्ते जी, मैं वाणी. आपका हिसाब हमेशा सुरक्षित रहेगा."
    },
    {
        "id": "Omkar",
        "display_name": "Omkar",
        "language_code": "mr-IN",
        "language_name": "Marathi / Hindi",
        "gender": "Male",
        "characteristics": "Resonant Marathi vernacular voice",
        "engine": "Gnani Timbre v2.5",
        "sample_text": "नमस्कार, मी ओंकार. तुमचा खाता आणि हिशोब सुरक्षित ठेवण्यात मदत करेन."
    }
]

# Legacy and lowercase aliases to verified official names
VOICE_ALIASES: Dict[str, str] = {
    "sia": "Bhavna",
    "bhavna": "Bhavna",
    "deepak": "Deepak",
    "kabir": "Deepak",
    "madhuri": "Madhuri",
    "priya": "Madhuri",
    "radhika": "Radhika",
    "gaurav": "Gaurav",
    "nalini": "Nalini",
    "vikrant": "Vikrant",
    "aarohi": "Aarohi",
    "omkar": "Omkar"
}

class GnaniVoiceService:
    """Service to discover, list, and validate supported Gnani voices."""

    @classmethod
    def get_available_voices(cls) -> List[Dict[str, Any]]:
        """
        Retrieves supported voice options from the official verified catalogue.
        """
        return GNANI_VOICE_CATALOGUE

    @classmethod
    def resolve_voice_id(cls, voice_id: Optional[str]) -> str:
        """
        Resolves an input voice ID or alias to the exact official Gnani voice name.
        Defaults to Bhavna if unspecified or invalid.
        """
        if not voice_id:
            return "Bhavna"
        
        normalized = voice_id.strip()
        lower = normalized.lower()

        if lower in VOICE_ALIASES:
            return VOICE_ALIASES[lower]

        # Check if already exact title match
        for v in GNANI_VOICE_CATALOGUE:
            if v["id"].lower() == lower:
                return v["id"]

        # If not recognized, fallback to default Bhavna
        return "Bhavna"

    @classmethod
    def is_supported(cls, voice_id: str) -> bool:
        """Check whether a voice is supported."""
        if not voice_id:
            return False
        lower = voice_id.strip().lower()
        if lower in VOICE_ALIASES:
            return True
        return any(v["id"].lower() == lower for v in GNANI_VOICE_CATALOGUE)
