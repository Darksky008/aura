"""LLM provider abstraction. The assistant only ever talks to `AIProvider`; Groq is one implementation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(Exception):
    """Any failure talking to a model. Never shown to guests."""


class ToolUseFailed(ProviderError):
    """Model produced a malformed tool call."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class AIResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_message: dict = field(default_factory=dict)  # assistant message to append to the transcript


class AIProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict] | None = None, *, temperature: float = 0.3,
                 max_tokens: int = 900) -> AIResponse: ...
