import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import Tenant, get_tenant, require_admin
from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.database.session import get_db
from app.models import Allergen, ConversationMessage, ConversationSession, DietaryTag, KnowledgeDocument, Special
from app.schemas.api import DishCreate, DishUpdate, KnowledgeIn, SettingsIn, SpecialIn
from app.services.analytics.service import summary
from app.services.menu.serialize import dish_to_dict
from app.services.menu.service import MenuService
from app.tools.schemas import TOOL_NAMES

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _menu(db: Session, t: Tenant) -> MenuService:
    return MenuService(db, t.hotel.id, t.restaurant.id)


@router.get("/ping")
def ping():
    return {"ok": True}


@router.get("/analytics")
def analytics(days: int = Query(7, ge=1, le=90), t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return summary(db, t.hotel.id, days)


@router.get("/reference")
def reference(t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return {"allergens": [{"code": a.code, "label": a.label} for a in db.scalars(select(Allergen).order_by(Allergen.label))],
            "dietary_tags": [{"code": d.code, "label": d.label} for d in db.scalars(select(DietaryTag))],
            "categories": [{"id": str(c.id), "name": c.name} for c in _menu(db, t).categories()]}


# ---- dishes -------------------------------------------------------------------
@router.get("/dishes")
def list_dishes(t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return [dish_to_dict(d) for d in _menu(db, t).list_dishes()]


@router.post("/dishes", status_code=201)
def create_dish(body: DishCreate, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return dish_to_dict(_menu(db, t).create_dish(body.model_dump(exclude_unset=True)))


@router.put("/dishes/{dish_id}")
def update_dish(dish_id: uuid.UUID, body: DishUpdate, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return dish_to_dict(_menu(db, t).update_dish(dish_id, body.model_dump(exclude_unset=True)))


@router.patch("/dishes/{dish_id}/availability")
def toggle_availability(dish_id: uuid.UUID, available: bool, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return dish_to_dict(_menu(db, t).update_dish(dish_id, {"is_available": available}))


@router.patch("/dishes/{dish_id}/chef-special")
def toggle_chef_special(dish_id: uuid.UUID, special: bool, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return dish_to_dict(_menu(db, t).update_dish(dish_id, {"is_chef_special": special}))


@router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(dish_id: uuid.UUID, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    _menu(db, t).delete_dish(dish_id)


# ---- specials -----------------------------------------------------------------
def _special_out(s: Special) -> dict:
    return {"id": str(s.id), "type": s.special_type, "title": s.title, "description": s.description, "is_active": s.is_active,
            "starts_on": s.starts_on.isoformat() if s.starts_on else None, "ends_on": s.ends_on.isoformat() if s.ends_on else None,
            "dish": {"id": str(s.dish.id), "name": s.dish.name} if s.dish else None}


def _own_special(db: Session, t: Tenant, sid: uuid.UUID) -> Special:
    s = db.get(Special, sid)
    if not s or s.hotel_id != t.hotel.id:
        raise NotFoundError("Special not found.")
    return s


@router.get("/specials")
def list_specials(t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    rows = db.scalars(select(Special).where(Special.hotel_id == t.hotel.id).order_by(Special.created_at.desc()))
    return [_special_out(s) for s in rows]


@router.post("/specials", status_code=201)
def create_special(body: SpecialIn, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    if body.dish_id:
        _menu(db, t).get_dish(body.dish_id)  # tenant ownership check
    s = Special(hotel_id=t.hotel.id, restaurant_id=t.restaurant.id, **body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _special_out(s)


@router.put("/specials/{sid}")
def update_special(sid: uuid.UUID, body: SpecialIn, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    s = _own_special(db, t, sid)
    if body.dish_id:
        _menu(db, t).get_dish(body.dish_id)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _special_out(s)


@router.delete("/specials/{sid}", status_code=204)
def delete_special(sid: uuid.UUID, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    db.delete(_own_special(db, t, sid))
    db.commit()


# ---- knowledge ----------------------------------------------------------------
def _doc_out(d: KnowledgeDocument) -> dict:
    return {"id": str(d.id), "doc_type": d.doc_type, "title": d.title, "content": d.content, "is_published": d.is_published,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None}


def _own_doc(db: Session, t: Tenant, did: uuid.UUID) -> KnowledgeDocument:
    d = db.get(KnowledgeDocument, did)
    if not d or d.hotel_id != t.hotel.id:
        raise NotFoundError("Document not found.")
    return d


@router.get("/knowledge")
def list_docs(t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return [_doc_out(d) for d in db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.hotel_id == t.hotel.id).order_by(KnowledgeDocument.title))]


@router.post("/knowledge", status_code=201)
def create_doc(body: KnowledgeIn, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    d = KnowledgeDocument(hotel_id=t.hotel.id, restaurant_id=t.restaurant.id, **body.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return _doc_out(d)


@router.put("/knowledge/{did}")
def update_doc(did: uuid.UUID, body: KnowledgeIn, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    d = _own_doc(db, t, did)
    for k, v in body.model_dump().items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return _doc_out(d)


@router.delete("/knowledge/{did}", status_code=204)
def delete_doc(did: uuid.UUID, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    db.delete(_own_doc(db, t, did))
    db.commit()


# ---- conversations ------------------------------------------------------------
@router.get("/conversations")
def conversations(limit: int = Query(40, ge=1, le=200), offset: int = Query(0, ge=0), t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    sessions = list(db.scalars(select(ConversationSession).where(ConversationSession.hotel_id == t.hotel.id)
                               .order_by(ConversationSession.started_at.desc()).limit(limit).offset(offset)))
    counts = dict(db.execute(select(ConversationMessage.session_id, func.count()).where(ConversationMessage.hotel_id == t.hotel.id)
                             .group_by(ConversationMessage.session_id)).all())
    return [{"id": str(s.id), "language": s.language, "channel": s.channel, "started_at": s.started_at.isoformat(),
             "messages": counts.get(s.id, 0)} for s in sessions]


@router.get("/conversations/{sid}")
def conversation(sid: uuid.UUID, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    s = db.get(ConversationSession, sid)
    if not s or s.hotel_id != t.hotel.id:
        raise NotFoundError("Conversation not found.")
    return {"id": str(s.id), "language": s.language, "started_at": s.started_at.isoformat(),
            "messages": [{"role": m.role, "content": m.content, "tools_used": m.tools_used, "latency_ms": m.latency_ms,
                          "at": m.created_at.isoformat()} for m in s.messages]}


# ---- settings / assistant status ---------------------------------------------------
def _settings_out(t: Tenant) -> dict:
    h, r = t.hotel, t.restaurant
    return {"hotel_name": h.name, "tagline": h.tagline, "assistant_name": h.assistant_name, "supported_languages": h.supported_languages,
            "restaurant_name": r.name, "restaurant_description": r.description, "slug": h.slug}


@router.get("/settings")
def get_settings_(t: Tenant = Depends(get_tenant)):
    return _settings_out(t)


@router.put("/settings")
def put_settings(body: SettingsIn, t: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for src, (obj, attr) in {"hotel_name": (t.hotel, "name"), "tagline": (t.hotel, "tagline"), "assistant_name": (t.hotel, "assistant_name"),
                             "supported_languages": (t.hotel, "supported_languages"), "restaurant_name": (t.restaurant, "name"),
                             "restaurant_description": (t.restaurant, "description")}.items():
        if src in data and data[src] is not None:
            setattr(obj, attr, data[src])
    db.commit()
    return _settings_out(t)


@router.get("/assistant")
def assistant_status(settings: Settings = Depends(get_settings)):
    from app.services.voice.tts import get_tts

    tts = get_tts(settings)
    return {"llm_provider": "groq" if settings.groq_api_key else "offline", "llm_model": settings.groq_model if settings.groq_api_key else "rule-based (set GROQ_API_KEY)",
            "stt": settings.groq_stt_model if settings.groq_api_key else None, "tts": tts.name if tts else None,
            "tts_voices": {"en": settings.tts_voice_en, "ta": settings.tts_voice_ta, "hi": settings.tts_voice_hi},
            "avatar_provider": settings.avatar_provider, "voice_provider": settings.voice_provider, "tools": TOOL_NAMES,
            "environment": settings.app_env, "admin_protected": bool(settings.admin_api_key)}
