import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import Tenant, get_tenant, rate_limit
from app.core.i18n import LANGUAGES
from app.database.session import get_db
from app.models import Hotel
from app.schemas.api import EventRequest
from app.services.analytics.service import record_event
from app.services.menu.serialize import dish_to_dict
from app.services.menu.service import MenuService

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/hotels")
def hotels(db: Session = Depends(get_db)):
    rows = db.scalars(select(Hotel).where(Hotel.is_active.is_(True)).order_by(Hotel.name))
    return [{"slug": h.slug, "name": h.name, "tagline": h.tagline} for h in rows]


@router.get("/hotels/current")
def current_hotel(tenant: Tenant = Depends(get_tenant)):
    h, r = tenant.hotel, tenant.restaurant
    return {"slug": h.slug, "name": h.name, "tagline": h.tagline, "city": h.city, "assistant_name": h.assistant_name,
            "default_language": h.default_language,
            "languages": [{"code": c, **LANGUAGES[c]} for c in h.supported_languages if c in LANGUAGES],
            "restaurant": {"id": str(r.id), "name": r.name, "description": r.description, "positioning": r.positioning,
                           "currency": r.currency}}


@router.get("/restaurants")
def restaurants(tenant: Tenant = Depends(get_tenant)):
    return [{"id": str(r.id), "name": r.name, "description": r.description} for r in tenant.hotel.restaurants if r.is_active]


@router.get("/menu")
def menu(category: str | None = Query(None, max_length=60), dietary: str | None = Query(None, pattern="^(vegetarian|vegan|gluten_free)$"),
         chef_special: bool | None = None, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    svc = MenuService(db, tenant.hotel.id, tenant.restaurant.id)
    dishes = svc.list_dishes(category_slug=category, dietary=dietary, chef_special=chef_special)
    return {"categories": [{"id": str(c.id), "slug": c.slug, "name": c.name, "names": {"en": c.name, **(c.name_translations or {})}} for c in svc.categories()],
            "dishes": [dish_to_dict(d) for d in dishes]}


@router.get("/menu/{dish_id}")
def menu_item(dish_id: uuid.UUID, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return dish_to_dict(MenuService(db, tenant.hotel.id, tenant.restaurant.id).get_dish(dish_id))


@router.get("/specials")
def specials(tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    svc = MenuService(db, tenant.hotel.id, tenant.restaurant.id)
    return [{"id": str(s.id), "type": s.special_type, "title": s.title, "description": s.description,
             "dish": dish_to_dict(s.dish) if s.dish else None} for s in svc.active_specials()]


@router.post("/analytics/events", status_code=202, dependencies=[Depends(rate_limit("events", 2))])
def post_event(body: EventRequest, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    record_event(db, tenant.hotel.id, body.session_id, body.event_type, body.payload)
    return {"accepted": True}
