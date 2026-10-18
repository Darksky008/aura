"""Unicode-safe text helpers (English, Tamil, Hindi) shared by search, STT prompts and TTS."""
import re
import unicodedata

_TAMIL = re.compile(r"[\u0B80-\u0BFF]")
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def normalize(text: str) -> str:
    """Lowercase, NFKC, drop punctuation/symbols but KEEP combining marks (vital for Tamil/Hindi)."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    kept = [ch if (ch.isspace() or unicodedata.category(ch)[0] in "LNM") else " " for ch in text]
    return re.sub(r"\s+", " ", "".join(kept)).strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def detect_script_language(text: str) -> str:
    """Return 'ta', 'hi' or 'en' by dominant script. Used to pick the right TTS voice."""
    ta = len(_TAMIL.findall(text))
    hi = len(_DEVANAGARI.findall(text))
    if ta == 0 and hi == 0:
        return "en"
    return "ta" if ta >= hi else "hi"


_MD = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    (re.compile(r"__(.+?)__"), r"\1"),
    (re.compile(r"`([^`]+)`"), r"\1"),
    (re.compile(r"^\s*[•\-*]\s+", re.M), ""),
    (re.compile(r"^#+\s*", re.M), ""),
]
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")


def clean_for_speech(text: str) -> str:
    """Strip markdown/emoji and expand symbols so neural voices read naturally."""
    for pattern, repl in _MD:
        text = pattern.sub(repl, text)
    text = _EMOJI.sub("", text)
    text = re.sub(r"(\d)\s*kcal", r"\1 calories", text, flags=re.I)
    text = text.replace("&", " and ").replace("~", "about ").replace("≈", "about ")
    text = re.sub(r"\n+", ". ", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    return re.sub(r"\s{2,}", " ", text).strip()
