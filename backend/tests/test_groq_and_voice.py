"""Groq tool-calling loop against a mocked HTTP transport + STT guard rails."""
import json

import httpx
import pytest

from app.services.ai.assistant import AssistantService
from app.services.ai.factory import build_providers
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.offline_provider import OfflineProvider
from app.services.ai.provider import ProviderError
from app.core.config import get_settings
from app.services.voice.stt import GroqSpeechToText, build_prompt
from app.core.text import clean_for_speech, detect_script_language


def groq_with(handler):
    return GroqProvider("test-key", "openai/gpt-oss-120b", transport=httpx.MockTransport(handler))


def test_tool_loop_executes_tool_then_answers(db, hotel, restaurant):
    calls = []

    def handler(request: httpx.Request):
        body = json.loads(request.content)
        calls.append(body)
        assert request.headers["authorization"] == "Bearer test-key"
        if len(calls) == 1:
            assert body["model"] == "openai/gpt-oss-120b" and body["reasoning_effort"] == "low" and body["tools"]
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "get_ingredients", "arguments": json.dumps({"dish_name": "Paneer Tikka"})}}]}}]})
        tool_msg = [m for m in body["messages"] if m["role"] == "tool"][0]
        assert "Bell pepper" in tool_msg["content"]          # the DB result was handed back to the LLM
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "Paneer Tikka contains paneer, yogurt and bell pepper."}}]})

    svc = AssistantService(db, hotel, restaurant, groq_with(handler))
    s = svc.start_session("en")
    out = svc.chat(s, "What's in the paneer tikka?", "en")
    assert out["reply"].startswith("Paneer Tikka contains") and out["tools_used"] == ["get_ingredients"] and out["provider"] == "groq"
    assert len(calls) == 2
    system = calls[0]["messages"][0]["content"]
    assert "Paneer" not in system        # menu is NOT dumped into the system prompt


def test_allergy_notice_is_enforced_even_if_model_forgets(db, hotel, restaurant):
    n = {"i": 0}

    def handler(request):
        n["i"] += 1
        if n["i"] == 1:
            return httpx.Response(200, json={"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "a", "type": "function", "function": {"name": "get_allergens", "arguments": json.dumps({"dish_name": "Malai Kofta", "allergen": "nuts"})}}]}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "Yes, it has cashews."}}]})

    svc = AssistantService(db, hotel, restaurant, groq_with(handler))
    r = svc.chat(svc.start_session("en"), "nuts in kofta?", "en")
    assert "Yes, it has cashews." in r["reply"] and "restaurant team" in r["reply"]


def test_tamil_notice_is_localised(db, hotel, restaurant):
    n = {"i": 0}

    def handler(request):
        n["i"] += 1
        if n["i"] == 1:
            return httpx.Response(200, json={"choices": [{"message": {"content": None, "tool_calls": [
                {"id": "a", "type": "function", "function": {"name": "get_allergens", "arguments": json.dumps({"dish_name": "Paneer Tikka"})}}]}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "பனீர் டிக்காவில் பால் பொருட்கள் உள்ளன."}}]})

    svc = AssistantService(db, hotel, restaurant, groq_with(handler))
    r = svc.chat(svc.start_session("ta"), "பனீர் டிக்கா ஒவ்வாமை?", "ta")
    assert "உணவகக் குழுவிடம்" in r["reply"]
    assert detect_script_language(r["reply"]) == "ta"


def test_groq_failure_falls_back_to_offline(db, hotel, restaurant):
    primary = groq_with(lambda req: httpx.Response(401, json={"error": "bad key"}))
    _, offline = build_providers(db, hotel, restaurant.id, get_settings().model_copy(update={"groq_api_key": "x"}))
    svc = AssistantService(db, hotel, restaurant, primary, offline)
    r = svc.chat(svc.start_session("en"), "What is today's special?", "en")
    assert "Royal Chicken Biryani" in r["reply"] and r["provider"] == "offline"


def test_provider_failure_without_fallback_is_friendly(db, hotel, restaurant):
    svc = AssistantService(db, hotel, restaurant, groq_with(lambda req: httpx.Response(400, json={"error": "x"})))
    r = svc.chat(svc.start_session("en"), "hello there", "en")
    assert "trouble" in r["reply"] and "400" not in r["reply"]


def test_groq_requires_key():
    with pytest.raises(ProviderError):
        GroqProvider("", "m")


# ------------------------------------------------------------------ STT guards
def stt():
    return GroqSpeechToText("k", "whisper-large-v3", "https://x", 0.22)


def seg(text="x", lp=-0.2, ns=0.01, cr=1.2, start=0, end=2):
    return {"avg_logprob": lp, "no_speech_prob": ns, "compression_ratio": cr, "start": start, "end": end}


def test_stt_accepts_clear_speech():
    r = stt().evaluate({"text": "Is the paneer tikka vegetarian?", "duration": 3, "segments": [seg()]}, "en")
    assert r.status == "ok" and r.confidence > 0.7


def test_stt_drops_silence_hallucination():
    r = stt().evaluate({"text": "Thank you.", "duration": 1.0, "segments": [seg(lp=-1.2, ns=0.5)]}, "en")
    assert r.status == "empty"
    # ...but a real, confident "thank you" survives
    ok = stt().evaluate({"text": "Thank you", "duration": 2.5, "segments": [seg(lp=-0.15, ns=0.02)]}, "en")
    assert ok.status == "ok"


def test_stt_flags_low_confidence_and_repetition():
    assert stt().evaluate({"text": "blah", "duration": 3, "segments": [seg(lp=-2.5)]}, "en").status == "unclear"
    assert stt().evaluate({"text": "ha ha ha ha", "duration": 3, "segments": [seg(cr=3.4)]}, "en").status == "unclear"
    assert stt().evaluate({"text": "", "segments": []}, "en").status == "empty"


def test_stt_prompt_uses_native_script_names():
    p = build_prompt("ta", {"en": ["Paneer Tikka"], "ta": ["பனீர் டிக்கா"], "hi": ["पनीर टिक्का"]})
    assert "பனீர் டிக்கா" in p and "Paneer" not in p


def test_speech_cleaning_and_script_detection():
    assert clean_for_speech("**Paneer Tikka**\n• mild\n• 390 kcal 😀") == "Paneer Tikka. mild. 390 calories"
    assert [detect_script_language(t) for t in ("hello", "வணக்கம்", "नमस्ते")] == ["en", "ta", "hi"]


# ------------------------------------------------------- voice HTTP layer
import asyncio


def test_whisper_request_shape_and_result():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        body = request.content.decode("latin-1")
        seen["body"] = body
        return httpx.Response(200, json={"text": "பனீர் டிக்கா சைவமா?", "duration": 3.1, "segments": [seg(lp=-0.25)]})

    s = GroqSpeechToText("k", "whisper-large-v3", "https://api.groq.com/openai/v1", 0.22, transport=httpx.MockTransport(handler))
    r = asyncio.run(s.transcribe(b"x" * 3000, "speech.webm", "audio/webm", "ta", build_prompt("ta", {"ta": ["பனீர் டிக்கா"]})))
    assert r.status == "ok" and "டிக்கா" in r.text
    assert seen["url"].endswith("/audio/transcriptions")
    for needle in ('name="language"', "whisper-large-v3", 'name="temperature"', "verbose_json", 'name="prompt"'):
        assert needle in seen["body"]


def test_tts_endpoint_uses_provider_and_returns_audio(client, monkeypatch):
    class Fake:
        name = "fake"

        async def synthesize(self, text):
            return b"ID3fake-mp3", detect_script_language(text)

    monkeypatch.setattr("app.api.voice.get_tts", lambda settings: Fake())
    r = client.post("/api/voice/tts", json={"text": "வணக்கம்"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and r.headers["x-voice-language"] == "ta"
    assert client.post("/api/voice/tts", json={"text": ""}).status_code == 422
    assert client.post("/api/voice/tts", json={"text": "x" * 901}).status_code == 422


def test_tts_failure_is_503_not_500(client, monkeypatch):
    class Broken:
        name = "broken"

        async def synthesize(self, text):
            raise RuntimeError("upstream down")

    monkeypatch.setattr("app.api.voice.get_tts", lambda settings: Broken())
    r = client.post("/api/voice/tts", json={"text": "hello"})
    assert r.status_code == 503 and "upstream" not in r.text


def test_tts_voice_selection_follows_script():
    from app.services.voice.tts import EdgeTTS
    tts = EdgeTTS(get_settings())
    assert [tts.voices[detect_script_language(t)] for t in ("hello", "வணக்கம்", "नमस्ते")] == ["en-IN-NeerjaNeural", "ta-IN-PallaviNeural", "hi-IN-SwaraNeural"]


def test_transcribe_endpoint_validates_audio(client, monkeypatch):
    from app.core.config import get_settings as gs
    monkeypatch.setenv("GROQ_API_KEY", "k")
    gs.cache_clear()
    try:
        bad = client.post("/api/voice/transcribe", files={"audio": ("a.txt", b"0" * 4000, "text/plain")}, data={"language": "en"})
        assert bad.status_code == 415
        tiny = client.post("/api/voice/transcribe", files={"audio": ("a.webm", b"0" * 100, "audio/webm")}, data={"language": "en"})
        assert tiny.json()["status"] == "empty"
    finally:
        monkeypatch.delenv("GROQ_API_KEY")
        gs.cache_clear()
