import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import Tenant, get_tenant, rate_limit
from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.schemas.api import ChatRequest, RecommendRequest, SessionCreate
from app.services.ai.assistant import AssistantService
from app.services.ai.factory import build_providers
from app.services.menu.serialize import dish_for_tool
from app.services.menu.service import MenuService
from app.services.recommendation.engine import Preferences, RecommendationEngine

router = APIRouter(prefix="/assistant", tags=["assistant"])
log = logging.getLogger("api.assistant")


def _service(db: Session, tenant: Tenant, settings: Settings) -> AssistantService:
    primary, fallback = build_providers(db, tenant.hotel, tenant.restaurant.id, settings)
    return AssistantService(db, tenant.hotel, tenant.restaurant, primary, fallback)


@router.post("/session", dependencies=[Depends(rate_limit("session", 0.5))])
def create_session(body: SessionCreate, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db),
                   settings: Settings = Depends(get_settings)):
    s = _service(db, tenant, settings).start_session(body.language, body.channel)
    return {"session_id": str(s.id), "language": s.language}


@router.post("/chat", dependencies=[Depends(rate_limit("chat"))])
def chat(body: ChatRequest, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db),
         settings: Settings = Depends(get_settings)):
    svc = _service(db, tenant, settings)
    session = svc.get_session(body.session_id, body.language)
    return svc.chat(session, body.message, body.language, body.dish_id)


@router.post("/chat/stream", dependencies=[Depends(rate_limit("chat"))])
def chat_stream(body: ChatRequest, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db),
                settings: Settings = Depends(get_settings)):
    """NDJSON: {"type":"tool","name":...} events while tools run, then one {"type":"final",...}."""
    svc = _service(db, tenant, settings)
    session = svc.get_session(body.session_id, body.language)

    def gen():
        try:
            for event in svc.stream(session, body.message, body.language, body.dish_id):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception:  # noqa: BLE001
            log.exception("stream failed")
            yield json.dumps({"type": "error", "message": "Something went wrong. Please try again."}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@router.post("/recommend", dependencies=[Depends(rate_limit("chat"))])
def recommend(body: RecommendRequest, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    """Deterministic recommendation (no LLM). The chat endpoint uses the same engine through a tool."""
    engine = RecommendationEngine(MenuService(db, tenant.hotel.id, tenant.restaurant.id))
    results = engine.recommend(Preferences.from_dict(body.preferences))
    return {"count": len(results), "recommendations": [{"dish": dish_for_tool(r.dish), "matched": r.reasons} for r in results]}
