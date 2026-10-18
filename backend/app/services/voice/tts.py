"""Text-to-speech providers (Tamil, Hindi, English). Swap by changing TTS_PROVIDER - nothing else changes.

  * AzureTTS  - production-grade (Azure Speech REST), same neural voices
  * EdgeTTS   - free Microsoft neural voices via the `edge-tts` package (unofficial endpoint; fine for demos)
The frontend falls back to the browser's speechSynthesis automatically if this endpoint is unavailable.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from xml.sax.saxutils import escape

import httpx

from app.core.config import Settings
from app.core.logging import log_ctx
from app.core.text import clean_for_speech, detect_script_language

log = logging.getLogger("voice.tts")
LOCALES = {"en": "en-IN", "ta": "ta-IN", "hi": "hi-IN"}


class TTSProvider(ABC):
    name = "base"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.voices = {"en": settings.tts_voice_en, "ta": settings.tts_voice_ta, "hi": settings.tts_voice_hi}
        self._cache: OrderedDict[tuple[str, str], bytes] = OrderedDict()

    @abstractmethod
    async def _synthesize(self, text: str, lang: str, voice: str) -> bytes: ...

    async def synthesize(self, text: str) -> tuple[bytes, str]:
        """Returns (mp3 bytes, language used). The language is detected from the text's script."""
        spoken = clean_for_speech(text)
        lang = detect_script_language(spoken)
        voice = self.voices[lang]
        key = (voice, spoken)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key], lang
        audio = await asyncio.wait_for(self._synthesize(spoken, lang, voice), timeout=25)
        if not audio:
            raise RuntimeError("empty audio")
        self._cache[key] = audio
        while len(self._cache) > 200:
            self._cache.popitem(last=False)
        return audio, lang


class EdgeTTS(TTSProvider):
    name = "edge"

    async def _synthesize(self, text, lang, voice):
        import edge_tts

        buf = bytearray()
        async for chunk in edge_tts.Communicate(text, voice, rate=self.settings.tts_rate).stream():
            if chunk["type"] == "audio":
                buf += chunk["data"]
        return bytes(buf)


class AzureTTS(TTSProvider):
    name = "azure"

    async def _synthesize(self, text, lang, voice):
        s = self.settings
        ssml = (f"<speak version='1.0' xml:lang='{LOCALES[lang]}'><voice name='{voice}'>"
                f"<prosody rate='{s.tts_rate}'>{escape(text)}</prosody></voice></speak>")
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"https://{s.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1", content=ssml.encode("utf-8"),
                headers={"Ocp-Apim-Subscription-Key": s.azure_speech_key, "Content-Type": "application/ssml+xml",
                         "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3", "User-Agent": "aura-concierge"})
        if r.status_code != 200:
            log.error("azure tts error", extra=log_ctx(status=r.status_code))
            raise RuntimeError("azure_tts_failed")
        return r.content


_instance: TTSProvider | None = None


def get_tts(settings: Settings) -> TTSProvider | None:
    global _instance
    choice = settings.tts_provider.lower()
    if choice == "none":
        return None
    has_azure = bool(settings.azure_speech_key and settings.azure_speech_region and not settings.azure_speech_key.startswith("#"))
    wants_azure = choice == "azure" or (choice == "auto" and has_azure)
    if _instance is None or (wants_azure and not isinstance(_instance, AzureTTS)) or (not wants_azure and not isinstance(_instance, EdgeTTS)):
        if wants_azure:
            _instance = AzureTTS(settings)
        else:
            _instance = EdgeTTS(settings)
    return _instance
