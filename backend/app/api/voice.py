import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import Tenant, get_tenant, rate_limit
from app.core.config import Settings, get_settings
from app.core.i18n import norm_lang
from app.database.session import get_db
from app.schemas.api import TTSRequest
from app.services.menu.service import MenuService
from app.services.voice.stt import GroqSpeechToText, build_prompt
from app.services.voice.tts import get_tts

router = APIRouter(prefix="/voice", tags=["voice"])
log = logging.getLogger("api.voice")
MAX_AUDIO = 8 * 1024 * 1024
ALLOWED = ("audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav", "audio/m4a", "audio/x-m4a", "video/webm", "application/octet-stream")


@lru_cache
def _stt(key: str, model: str, base: str, min_conf: float) -> GroqSpeechToText:
    return GroqSpeechToText(key, model, base, min_conf)


@router.get("/capabilities")
def capabilities(settings: Settings = Depends(get_settings)):
    tts = get_tts(settings)
    return {"stt": bool(settings.groq_api_key), "stt_model": settings.groq_stt_model if settings.groq_api_key else None,
            "tts": tts is not None, "tts_provider": tts.name if tts else None, "languages": ["en", "ta", "hi"]}


@router.post("/transcribe", dependencies=[Depends(rate_limit("stt"))])
async def transcribe(audio: UploadFile = File(...), language: str = Form("en"), tenant: Tenant = Depends(get_tenant),
                     db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if not settings.groq_api_key:
        raise HTTPException(503, "Speech recognition is not configured on the server.")
    if (audio.content_type or "application/octet-stream").split(";")[0] not in ALLOWED:
        raise HTTPException(415, "Unsupported audio format.")
    data = await audio.read(MAX_AUDIO + 1)
    if len(data) > MAX_AUDIO:
        raise HTTPException(413, "Recording too long.")
    if len(data) < 1500:
        return {"text": "", "status": "empty", "confidence": 0.0, "language": language}

    lang = norm_lang(language)
    menu = MenuService(db, tenant.hotel.id, tenant.restaurant.id)
    dishes = menu.list_dishes()
    names = {"en": [d.name for d in dishes], "ta": [d.name_translations.get("ta", d.name) for d in dishes],
             "hi": [d.name_translations.get("hi", d.name) for d in dishes]}
    try:
        result = await _stt(settings.groq_api_key, settings.groq_stt_model, settings.groq_base_url, settings.stt_min_confidence).transcribe(
            data, audio.filename or "speech.webm", (audio.content_type or "audio/webm").split(";")[0], lang, build_prompt(lang, names))
    except RuntimeError:
        raise HTTPException(503, "Speech recognition is temporarily unavailable.")
    log.info("transcribed", extra={"ctx": {"status": result.status, "confidence": result.confidence, "chars": len(result.text), "lang": lang}})
    return {"text": result.text, "status": result.status, "confidence": result.confidence, "language": lang, "reason": result.reason}


@router.post("/tts", dependencies=[Depends(rate_limit("tts", 2))])
async def tts(body: TTSRequest, settings: Settings = Depends(get_settings)):
    provider = get_tts(settings)
    if provider is None:
        raise HTTPException(503, "Voice output is disabled.")
    try:
        audio, lang = await provider.synthesize(body.text)
    except Exception:
        # Fallback to EdgeTTS before reporting failure
        try:
            from app.services.voice.tts import EdgeTTS
            edge = EdgeTTS(settings)
            audio, lang = await edge.synthesize(body.text)
        except Exception:
            log.exception("tts failed")
            raise HTTPException(503, "Voice output is temporarily unavailable.")
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "private, max-age=3600", "X-Voice-Language": lang})
