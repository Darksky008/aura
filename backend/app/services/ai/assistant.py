"""AssistantService: the tool-calling loop that turns a guest question into a grounded answer."""
import json
import logging
import re
import time
import uuid
from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.i18n import ALLERGY_NOTICE, ALLERGY_NOTICE_MARKERS, TRANSIENT_ERROR, norm_lang
from app.core.logging import log_ctx
from app.models import ConversationMessage, ConversationSession, Hotel, Restaurant
from app.services.ai.prompts import build_system_prompt
from app.services.ai.provider import AIProvider, ProviderError
from app.services.analytics.service import record_event
from app.tools.executor import ToolContext, execute_tool
from app.tools.schemas import TOOL_SCHEMAS

log = logging.getLogger("assistant")
MAX_STEPS = 5
HISTORY_TURNS = 12


class AssistantService:
    def __init__(self, db: Session, hotel: Hotel, restaurant: Restaurant, provider: AIProvider, fallback: AIProvider | None = None):
        self.db, self.hotel, self.restaurant = db, hotel, restaurant
        self.provider, self.fallback = provider, fallback

    # ---------------------------------------------------------------- sessions
    def start_session(self, language: str = "en", channel: str = "web") -> ConversationSession:
        session = ConversationSession(hotel_id=self.hotel.id, restaurant_id=self.restaurant.id, language=norm_lang(language),
                                      channel=channel, context={})
        self.db.add(session)
        self.db.commit()
        record_event(self.db, self.hotel.id, session.id, "conversation_started", {"language": session.language, "channel": channel})
        return session

    def get_session(self, session_id: uuid.UUID | None, language: str) -> ConversationSession:
        if session_id:
            session = self.db.get(ConversationSession, session_id)
            if not session or session.hotel_id != self.hotel.id:  # tenant check
                raise NotFoundError("That conversation has expired. Please start again.")
            return session
        return self.start_session(language)

    # ------------------------------------------------------------------- turn
    def stream(self, session: ConversationSession, message: str, language: str, dish_id: uuid.UUID | None = None) -> Iterator[dict]:
        started = time.perf_counter()
        lang = norm_lang(language)
        if lang != session.language:
            record_event(self.db, self.hotel.id, session.id, "language_changed", {"from": session.language, "to": lang})
        session.language = lang

        history = self._history(session)
        self.db.add(ConversationMessage(session_id=session.id, hotel_id=self.hotel.id, role="user", content=message))
        record_event(self.db, self.hotel.id, session.id, "question_asked", {"language": lang, "chars": len(message)})
        self.db.commit()

        ctx = ToolContext(self.db, self.hotel, self.restaurant, language=lang)
        user_content = message
        if dish_id:
            try:
                viewing = ctx.menu.get_dish(dish_id)
                user_content = f"[The guest is currently viewing the dish: {viewing.name}]\n{message}"
                ctx.track([viewing])
            except NotFoundError:
                pass

        last_dishes = (session.context or {}).get("last_dishes", [])
        messages: list[dict] = [{"role": "system", "content": build_system_prompt(self.hotel, self.restaurant, lang, last_dishes)},
                                *history, {"role": "user", "content": user_content}]
        tools_used: list[str] = []
        provider = self.provider
        reply = ""
        used_fallback = False

        for _ in range(MAX_STEPS):
            try:
                resp = provider.complete(messages, TOOL_SCHEMAS)
            except ProviderError as exc:
                log.warning("provider failed", extra=log_ctx(provider=provider.name, error=str(exc)))
                if self.fallback and provider is not self.fallback:
                    provider, used_fallback = self.fallback, True
                    continue
                reply = TRANSIENT_ERROR[lang]
                break
            if resp.tool_calls:
                messages.append(resp.raw_message)
                for tc in resp.tool_calls:
                    yield {"type": "tool", "name": tc.name}
                    tools_used.append(tc.name)
                    result = execute_tool(ctx, tc.name, tc.arguments)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False, default=str)[:9000]})
                continue
            reply = (resp.content or "").strip()
            if reply:
                break
        else:
            reply = TRANSIENT_ERROR[lang]
        if not reply:
            reply = TRANSIENT_ERROR[lang]

        reply = self._postprocess(reply, ctx, lang)
        latency = int((time.perf_counter() - started) * 1000)
        self.db.add(ConversationMessage(session_id=session.id, hotel_id=self.hotel.id, role="assistant", content=reply,
                                        tools_used=list(dict.fromkeys(tools_used)), latency_ms=latency))
        if ctx.dishes_seen:
            session.context = {**(session.context or {}), "last_dishes": ctx.dishes_seen[:6]}
        for kind, payload in ctx.events:
            record_event(self.db, self.hotel.id, session.id, kind, payload, commit=False)
        self.db.commit()
        log.info("turn complete", extra=log_ctx(session=str(session.id), latency_ms=latency, tools=tools_used,
                                                provider=provider.name, fallback=used_fallback))
        yield {"type": "final", "session_id": str(session.id), "reply": reply, "language": lang,
               "tools_used": list(dict.fromkeys(tools_used)), "dishes": ctx.dishes_seen[:6],
               "provider": provider.name, "latency_ms": latency}

    def chat(self, session, message, language, dish_id=None) -> dict:
        final = {}
        for event in self.stream(session, message, language, dish_id):
            if event["type"] == "final":
                final = event
        return final

    # ---------------------------------------------------------------- helpers
    def _history(self, session: ConversationSession) -> list[dict]:
        rows = self.db.scalars(
            select(ConversationMessage).where(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.created_at.desc()).limit(HISTORY_TURNS)
        )
        return [{"role": m.role, "content": m.content} for m in reversed(list(rows))]

    @staticmethod
    def _postprocess(reply: str, ctx: ToolContext, lang: str) -> str:
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip()
        reply = re.sub(r"\n{3,}", "\n\n", reply)[:1500]
        if ctx.allergen_used and not any(m in reply.lower() for m in ALLERGY_NOTICE_MARKERS):
            reply = f"{reply} {ALLERGY_NOTICE[lang]}".strip()
        return reply
