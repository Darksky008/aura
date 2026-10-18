"""Server-side localized strings for safety-critical sentences (never left to the LLM alone)."""

LANGUAGES = {
    "en": {"name": "English", "locale": "en-IN", "llm_name": "English"},
    "ta": {"name": "தமிழ்", "locale": "ta-IN", "llm_name": "Tamil (தமிழ்)"},
    "hi": {"name": "हिन्दी", "locale": "hi-IN", "llm_name": "Hindi (हिन्दी)"},
}
DEFAULT_LANGUAGE = "en"

ALLERGY_NOTICE = {
    "en": "Please confirm with our restaurant team before ordering, as cross-contact may occur during food preparation.",
    "ta": "உணவு தயாரிக்கும் போது குறுக்கு மாசுபாடு ஏற்பட வாய்ப்புள்ளதால், ஆர்டர் செய்வதற்கு முன் எங்கள் உணவகக் குழுவிடம் உறுதிப்படுத்திக் கொள்ளுங்கள்.",
    "hi": "खाना तैयार करते समय अन्य सामग्री के संपर्क में आने की संभावना हो सकती है, इसलिए कृपया ऑर्डर करने से पहले हमारी रेस्तरां टीम से पुष्टि कर लें।",
}
# If the model's reply already contains one of these, we don't repeat the notice.
ALLERGY_NOTICE_MARKERS = (
    "cross-contact", "cross contact", "restaurant team", "kitchen team",
    "குறுக்கு", "உணவகக் குழு", "क्रॉस", "रेस्तरां टीम", "रेस्टोरेंट टीम", "संपर्क में आने",
)

UNKNOWN_INFO = {
    "en": "I don't have that information in the current menu database. Please confirm with our restaurant team.",
    "ta": "தற்போதைய மெனு தரவுத்தளத்தில் அந்தத் தகவல் என்னிடம் இல்லை. தயவுசெய்து எங்கள் உணவகக் குழுவிடம் உறுதிப்படுத்திக் கொள்ளுங்கள்.",
    "hi": "यह जानकारी मेरे पास वर्तमान मेनू डेटाबेस में उपलब्ध नहीं है। कृपया हमारी रेस्तरां टीम से पुष्टि करें।",
}

TRANSIENT_ERROR = {
    "en": "I'm sorry, I'm having trouble right now. Could you please try again in a moment?",
    "ta": "மன்னிக்கவும், இப்போது எனக்குச் சிறிய சிரமம் உள்ளது. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்க முடியுமா?",
    "hi": "क्षमा करें, अभी मुझे थोड़ी समस्या आ रही है। कृपया थोड़ी देर बाद फिर कोशिश करें।",
}


def norm_lang(code: str | None) -> str:
    code = (code or DEFAULT_LANGUAGE).lower().split("-")[0]
    return code if code in LANGUAGES else DEFAULT_LANGUAGE
