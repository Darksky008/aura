from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Hotel
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.offline_provider import OfflineProvider
from app.services.ai.provider import AIProvider, ProviderError
from app.services.menu.service import MenuService


def build_providers(db: Session, hotel: Hotel, restaurant_id, settings: Settings) -> tuple[AIProvider, AIProvider | None]:
    """Returns (primary, fallback). Without a Groq key the grounded offline provider is primary."""
    menu = MenuService(db, hotel.id, restaurant_id)

    def names() -> list[tuple[str, str]]:
        from app.core.text import normalize
        out = []
        for d in menu.list_dishes():
            for v in (d.name, *(d.aliases or []), *(d.name_translations or {}).values()):
                n = normalize(v)
                if n:
                    out.append((n, d.name))
        return out

    def categories() -> list[str]:
        return [c.name for c in menu.categories()]

    offline = OfflineProvider(names, categories)
    if not settings.groq_api_key:
        return offline, None
    try:
        return GroqProvider(settings.groq_api_key, settings.groq_model, base_url=settings.groq_base_url,
                            timeout=settings.llm_timeout_seconds, reasoning_effort=settings.groq_reasoning_effort), offline
    except ProviderError:
        return offline, None
