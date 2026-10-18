import uuid
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AnalyticsEvent, ConversationSession, Dish

EVENT_TYPES = {
    "conversation_started", "question_asked", "dish_viewed", "dish_recommended", "special_viewed", "ingredient_question",
    "allergen_question", "dietary_question", "voice_used", "language_changed",
}
TOPIC_LABELS = {"ingredient_question": "Ingredients", "allergen_question": "Allergens", "dietary_question": "Dietary preferences",
                "dish_recommended": "Recommendations", "special_viewed": "Specials", "dish_viewed": "Dish details"}


def record_event(db: Session, hotel_id: uuid.UUID, session_id: uuid.UUID | None, event_type: str, payload: dict | None = None,
                 *, commit: bool = True) -> None:
    """Event payloads never contain guest free-text - only structured facts (dish names, language, flags)."""
    db.add(AnalyticsEvent(hotel_id=hotel_id, session_id=session_id, event_type=event_type, payload=payload or {}))
    if commit:
        db.commit()


def summary(db: Session, hotel_id: uuid.UUID, days: int = 7) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    events = list(db.scalars(select(AnalyticsEvent).where(AnalyticsEvent.hotel_id == hotel_id, AnalyticsEvent.created_at >= since)
                             .order_by(AnalyticsEvent.created_at.desc()).limit(10000)))
    by_type = Counter(e.event_type for e in events)
    dish_counter: Counter = Counter()
    for e in events:
        for name in (e.payload or {}).get("dishes", []) or []:
            dish_counter[name] += 1
    topics = Counter({k: by_type[k] for k in TOPIC_LABELS if by_type.get(k)})
    perday: Counter = Counter()
    for e in events:
        if e.event_type == "conversation_started":
            perday[e.created_at.date().isoformat()] += 1
    series = []
    for i in range(days - 1, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
        series.append({"date": d, "conversations": perday.get(d, 0)})
    veg = sum(1 for e in events if (e.payload or {}).get("dietary") == "vegetarian")
    chef = sum(1 for e in events if e.event_type == "special_viewed" or (e.payload or {}).get("chef_special"))
    sessions = db.scalar(select(func.count()).select_from(ConversationSession).where(ConversationSession.hotel_id == hotel_id)) or 0
    dishes = db.scalar(select(func.count()).select_from(Dish).where(Dish.hotel_id == hotel_id)) or 0
    top_topic = topics.most_common(1)[0][0] if topics else None
    return {
        "total_menu_items": dishes,
        "ai_conversations": sessions,
        "most_asked_dish": dish_counter.most_common(1)[0][0] if dish_counter else None,
        "most_asked_topic": TOPIC_LABELS.get(top_topic) if top_topic else None,
        "vegetarian_requests": veg,
        "chef_special_searches": chef,
        "conversations_per_day": series,
        "top_dishes": [{"name": n, "count": c} for n, c in dish_counter.most_common(7)],
        "topics": [{"label": TOPIC_LABELS[k], "count": v} for k, v in topics.most_common()],
        "events_by_type": dict(by_type),
        "voice_sessions": by_type.get("voice_used", 0),
        "window_days": days,
    }
