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
        "sample_text": "Namaste, main Vaani hoon. Aap bataiye, main aapki kya madad kar sakti hoon?"
    },
    {
        "id": "Deepak",
        "display_name": "Deepak",
        "language_code": "hi-IN",
        "language_name": "Hindi / Hinglish",
        "gender": "Male",
        "characteristics": "Clear, professional and balanced tone",
        "sample_text": "Namaste! Main Deepak hoon. Aaj aapka khata aur hisaab dekhne mein madad karunga."
    },
    {
        "id": "Madhuri",
        "display_name": "Madhuri",
        "language_code": "mr-IN",
        "language_name": "Marathi / Hindi",
        "gender": "Female",
        "characteristics": "Expressive Marathi & Devanagari vernacular",
        "sample_text": "Namaskar! Me Vaani ahe. Bola, me tumhala kashi madat karu shakte?"
    },
    {
        "id": "Radhika",
        "display_name": "Radhika",
        "language_code": "en-IN",
        "language_name": "English (India) / Hinglish",
        "gender": "Female",
        "characteristics": "Articulate, crisp and modern bilingual tone",
        "sample_text": "Hello, I am Vaani. How can I assist you with your business ledger today?"
    },
    {
        "id": "Gaurav",
        "display_name": "Gaurav",
        "language_code": "hi-IN",
        "language_name": "Hindi / Hinglish",
        "gender": "Male",
        "characteristics": "Lively Kirana merchant and energetic tone",
        "sample_text": "Ram Ram! Main Gaurav. Boliye kis grahak ka udhaar ya jama likhna hai?"
    },
    {
        "id": "Nalini",
        "display_name": "Nalini",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Female",
        "characteristics": "Formal, courteous and gentle tone",
        "sample_text": "Namaskar, aapki har zaroori dawa aur parchi ka dhyan main rakhungi."
    },
    {
        "id": "Vikrant",
        "display_name": "Vikrant",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Male",
        "characteristics": "Calm, authoritative and confident voice",
        "sample_text": "Namaste, Sensex Awaaz aur bazaar ke hisaab mein aapka swagat hai."
    },
    {
        "id": "Aarohi",
        "display_name": "Aarohi",
        "language_code": "hi-IN",
        "language_name": "Hindi",
        "gender": "Female",
        "characteristics": "Soft, friendly and pleasant tone",
        "sample_text": "Namaste ji, main Vaani. Aapka hisaab hamesha surakshit rahega."
    },
    {
        "id": "Omkar",
        "display_name": "Omkar",
        "language_code": "mr-IN",
        "language_name": "Marathi / Hindi",
        "gender": "Male",
        "characteristics": "Resonant Marathi vernacular voice",
        "sample_text": "Namaskar, me Omkar. Tumcha khata aani hishob surakshit thevnyat me madat karen."
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
    async def get_available_voices(cls) -> List[Dict[str, Any]]:
        """
        Retrieves supported voice options.
        If a custom Gnani voice list endpoint is configured and reachable, queries it;
        otherwise returns the verified official catalogue.
        """
        custom_endpoint = GnaniConfig.get_voice_list_endpoint()
        if custom_endpoint and GnaniConfig.is_configured():
            try:
                headers = GnaniConfig.get_auth_headers()
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(custom_endpoint, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            return data
                        elif isinstance(data, dict) and "voices" in data:
                            return data["voices"]
            except Exception as e:
                # Log and proceed with officially documented catalogue
                pass

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
