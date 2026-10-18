"""Speech-to-text via Groq Whisper, hardened for noisy hotel environments.

Accuracy measures:
  * temperature 0 + language hint (en/ta/hi) so Whisper doesn't mis-detect short utterances
  * `prompt` biasing with the real menu vocabulary (dish names in the guest's own script)
  * verbose_json -> confidence from avg_logprob, no_speech_prob and compression_ratio
  * hallucination guard: Whisper invents "Thank you." / "Thanks for watching" on near-silence; we drop those
"""
import logging
import math
from dataclasses import dataclass

import httpx

from app.core.logging import log_ctx
from app.core.text import normalize

log = logging.getLogger("voice.stt")

_HALLUCINATIONS = {
    "thank you", "thanks", "thanks for watching", "thank you for watching", "thank you so much", "please subscribe", "bye", "you",
    "subtitles by the amaraorg community", "subtitles by", "okay", "ok", "hmm", "mm", "uh", "um",
    "நன்றி", "வணக்கம்", "धन्यवाद", "शुक्रिया", "धन्यवाद दोस्तों",
}

_VOCAB_TERMS = {
    "en": "vegetarian, vegan, mild, medium, spicy, ingredients, allergens, nuts, dairy, gluten, today's special, chef special, dessert, starter, main course, calories, compare",
    "ta": "சைவம், அசைவம், காரம், பொருட்கள், ஒவ்வாமை, கொட்டை, பால், இனிப்பு, இன்றைய சிறப்பு, ஒப்பிடு",
    "hi": "शाकाहारी, वीगन, कम तीखा, मसालेदार, सामग्री, एलर्जी, मेवे, डेयरी, मिठाई, आज का स्पेशल, तुलना",
}


@dataclass
class Transcription:
    text: str = ""
    language: str = "en"
    confidence: float = 0.0
    status: str = "ok"  # ok | empty | unclear
    reason: str | None = None


def build_prompt(language: str, dish_names: dict[str, list[str]]) -> str:
    names = dish_names.get(language) or dish_names.get("en") or []
    lead = {"en": "Restaurant menu questions. Dishes:", "ta": "உணவக மெனு கேள்விகள். உணவுகள்:", "hi": "रेस्तरां मेनू के प्रश्न। व्यंजन:"}[language]
    return f"{lead} {', '.join(names)}. {_VOCAB_TERMS[language]}"[:600]


class GroqSpeechToText:
    def __init__(self, api_key: str, model: str, base_url: str, min_confidence: float, transport: httpx.AsyncBaseTransport | None = None):
        self.model, self.min_confidence = model, min_confidence
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=30.0, transport=transport,
                                         headers={"Authorization": f"Bearer {api_key}"})

    async def transcribe(self, audio: bytes, filename: str, content_type: str, language: str, prompt: str) -> Transcription:
        data = {"model": self.model, "response_format": "verbose_json", "temperature": "0", "language": language, "prompt": prompt}
        resp = None
        for attempt in range(2):
            try:
                resp = await self._client.post("/audio/transcriptions", data=data, files={"file": (filename, audio, content_type)})
            except httpx.HTTPError as exc:
                log.warning("stt network error", extra=log_ctx(error=exc.__class__.__name__))
                continue
            if resp.status_code == 200:
                break
            if resp.status_code in (429, 500, 502, 503):
                continue
            log.error("stt error", extra=log_ctx(status=resp.status_code, body=resp.text[:200]))
            break
        if resp is None or resp.status_code != 200:
            raise RuntimeError("stt_unavailable")
        return self.evaluate(resp.json(), language)

    def evaluate(self, payload: dict, language: str) -> Transcription:
        text = (payload.get("text") or "").strip()
        segments = payload.get("segments") or []
        duration = float(payload.get("duration") or sum(s.get("end", 0) - s.get("start", 0) for s in segments) or 0)
        if not text:
            return Transcription(language=language, status="empty", reason="no speech")
        total = sum(max(s.get("end", 0) - s.get("start", 0), 0.01) for s in segments) or 1.0
        avg_lp = sum(s.get("avg_logprob", -0.3) * max(s.get("end", 0) - s.get("start", 0), 0.01) for s in segments) / total if segments else -0.3
        no_speech = max((s.get("no_speech_prob", 0.0) for s in segments), default=0.0)
        avg_no_speech = sum(s.get("no_speech_prob", 0.0) for s in segments) / len(segments) if segments else 0.0
        compression = max((s.get("compression_ratio", 1.0) for s in segments), default=1.0)
        confidence = round(math.exp(max(min(avg_lp, 0.0), -5.0)), 3)

        if segments and all(s.get("no_speech_prob", 0) > 0.7 for s in segments):
            return Transcription(language=language, status="empty", reason="no_speech_prob")
        if compression > 2.6:
            return Transcription(language=language, confidence=confidence, status="unclear", reason="repetition")
        norm = normalize(text)
        if norm in _HALLUCINATIONS and (avg_no_speech > 0.3 or avg_lp < -0.8 or duration < 1.6):
            return Transcription(language=language, confidence=confidence, status="empty", reason="hallucination_guard")
        if confidence < self.min_confidence:
            return Transcription(text=text, language=language, confidence=confidence, status="unclear", reason="low_confidence")
        return Transcription(text=text, language=language, confidence=confidence, status="ok")
