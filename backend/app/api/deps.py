import hmac
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.database.session import get_db
from app.models import Hotel, Restaurant


@dataclass
class Tenant:
    hotel: Hotel
    restaurant: Restaurant


def get_tenant(db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
               x_hotel_slug: str | None = Header(default=None), hotel: str | None = Query(default=None, max_length=80)) -> Tenant:
    slug = x_hotel_slug or hotel or settings.default_hotel_slug
    h = db.scalar(select(Hotel).where(Hotel.slug == slug, Hotel.is_active.is_(True)))
    if not h:
        raise NotFoundError("This venue isn't set up yet. Please ask the hotel team to load the menu.")
    r = db.scalar(select(Restaurant).where(Restaurant.hotel_id == h.id, Restaurant.is_active.is_(True)).order_by(Restaurant.created_at))
    if not r:
        raise NotFoundError("This venue has no restaurant configured yet.")
    return Tenant(h, r)


def require_admin(x_admin_key: str | None = Header(default=None), settings: Settings = Depends(get_settings)) -> None:
    if not settings.admin_api_key:
        if settings.is_production:
            raise HTTPException(503, "Admin is disabled until ADMIN_API_KEY is configured.")
        return  # open in local development only
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(401, "Invalid admin key.")


_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def rate_limit(bucket: str, multiplier: float = 1.0):
    """Sliding-window per-IP limiter (in-memory; use Redis when running several instances)."""

    def dep(request: Request, settings: Settings = Depends(get_settings)) -> None:
        limit = int(settings.rate_limit_per_minute * multiplier)
        fwd = request.headers.get("x-forwarded-for", "")
        ip = fwd.split(",")[0].strip() or (request.client.host if request.client else "unknown")
        q, now = _hits[(bucket, ip)], time.monotonic()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "You're going a little fast. Please wait a moment.")
        q.append(now)

    return dep
