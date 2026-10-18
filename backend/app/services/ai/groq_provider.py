"""Groq via its OpenAI-compatible REST API (httpx). Key + model come from the environment only."""
import json
import logging
import time

import httpx

from app.core.logging import log_ctx
from app.services.ai.provider import AIProvider, AIResponse, ProviderError, ToolCall, ToolUseFailed

log = logging.getLogger("ai.groq")


class GroqProvider(AIProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str, *, base_url: str = "https://api.groq.com/openai/v1",
                 timeout: float = 40.0, reasoning_effort: str = "low", transport: httpx.BaseTransport | None = None):
        if not api_key:
            raise ProviderError("GROQ_API_KEY is not set")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    def _payload(self, messages, tools, temperature, max_tokens) -> dict:
        body: dict = {"model": self.model, "messages": messages, "temperature": temperature, "max_completion_tokens": max_tokens}
        if tools:
            body.update(tools=tools, tool_choice="auto")
        if self.model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = self.reasoning_effort or "low"
            body["include_reasoning"] = False
        return body

    def complete(self, messages, tools=None, *, temperature=0.3, max_tokens=900) -> AIResponse:
        body = self._payload(messages, tools, temperature, max_tokens)
        last_error = "unknown"
        for attempt in range(3):
            started = time.perf_counter()
            try:
                resp = self._client.post("/chat/completions", json=body)
            except httpx.HTTPError as exc:
                last_error = f"network: {exc.__class__.__name__}"
                time.sleep(0.6 * (attempt + 1))
                continue
            latency = int((time.perf_counter() - started) * 1000)
            if resp.status_code == 200:
                log.info("groq ok", extra=log_ctx(model=self.model, latency_ms=latency, attempt=attempt))
                return self._parse(resp.json())
            last_error = f"http {resp.status_code}"
            if resp.status_code == 400 and "tool_use_failed" in resp.text:
                raise ToolUseFailed("malformed tool call")
            if resp.status_code in (429, 500, 502, 503, 504):
                wait = min(float(resp.headers.get("retry-after", 0) or 0), 5.0) or 0.8 * (attempt + 1)
                time.sleep(wait)
                continue
            log.error("groq error", extra=log_ctx(status=resp.status_code, body=resp.text[:300]))
            raise ProviderError(last_error)
        raise ProviderError(last_error)

    @staticmethod
    def _parse(data: dict) -> AIResponse:
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("unexpected response shape") from exc
        calls: list[ToolCall] = []
        raw_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
                if not isinstance(args, dict):
                    args = {}
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(id=tc.get("id", f"call_{len(calls)}"), name=fn.get("name", ""), arguments=args))
            raw_calls.append({"id": calls[-1].id, "type": "function",
                              "function": {"name": calls[-1].name, "arguments": json.dumps(args, ensure_ascii=False)}})
        raw = {"role": "assistant", "content": msg.get("content") or ""}
        if raw_calls:
            raw["tool_calls"] = raw_calls
        return AIResponse(content=msg.get("content"), tool_calls=calls, raw_message=raw)
