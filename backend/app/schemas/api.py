import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.tools.schemas import ALLERGEN_CODES, DIETARY

Spice = Literal["none", "mild", "medium", "high"]
SpecialType = Literal["today", "weekend", "chef_recommendation", "seasonal"]
DocType = Literal["restaurant", "chef", "philosophy", "faq", "policy", "dish_story", "preparation"]


class SessionCreate(BaseModel):
    language: str = "en"
    channel: Literal["web", "kiosk", "tablet", "qr"] = "web"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: uuid.UUID | None = None
    language: str = "en"
    dish_id: uuid.UUID | None = None

    @field_validator("message")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class RecommendRequest(BaseModel):
    preferences: dict = Field(default_factory=dict)
    language: str = "en"


class EventRequest(BaseModel):
    event_type: Literal["dish_viewed", "voice_used", "language_changed", "special_viewed", "conversation_started"]
    session_id: uuid.UUID | None = None
    payload: dict = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def _small(cls, v: dict) -> dict:
        if len(str(v)) > 600:
            raise ValueError("payload too large")
        return v


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=900)


class DishUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    name_translations: dict[str, str] | None = None
    aliases: list[str] | None = None
    description: str | None = Field(default=None, max_length=1200)
    category_id: uuid.UUID | None = None
    cuisine: str | None = Field(default=None, max_length=120)
    spice_level: Spice | None = None
    calories_kcal: int | None = Field(default=None, ge=0, le=5000)
    price: float | None = Field(default=None, ge=0, le=1_000_000)
    ingredients: list[str] | None = None
    allergens: list[str] | None = None
    dietary: dict[str, Literal["yes", "no", "unknown"]] | None = None
    preparation_notes: str | None = Field(default=None, max_length=1200)
    image_url: str | None = Field(default=None, max_length=500)
    is_chef_special: bool | None = None
    is_available: bool | None = None
    sort_order: int | None = None

    @field_validator("allergens")
    @classmethod
    def _allergens(cls, v):
        bad = [a for a in (v or []) if a not in ALLERGEN_CODES]
        if bad:
            raise ValueError(f"Unknown allergen: {', '.join(bad)}")
        return v

    @field_validator("dietary")
    @classmethod
    def _dietary(cls, v):
        bad = [k for k in (v or {}) if k not in DIETARY]
        if bad:
            raise ValueError(f"Unknown dietary tag: {', '.join(bad)}")
        return v


class DishCreate(DishUpdate):
    name: str = Field(min_length=2, max_length=160)
    spice_level: Spice = "none"


class SpecialIn(BaseModel):
    dish_id: uuid.UUID | None = None
    special_type: SpecialType = "today"
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=600)
    starts_on: date | None = None
    ends_on: date | None = None
    is_active: bool = True


class KnowledgeIn(BaseModel):
    doc_type: DocType = "faq"
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10, max_length=8000)
    is_published: bool = True


class SettingsIn(BaseModel):
    hotel_name: str | None = Field(default=None, min_length=2, max_length=160)
    tagline: str | None = Field(default=None, max_length=255)
    assistant_name: str | None = Field(default=None, min_length=2, max_length=60)
    restaurant_name: str | None = Field(default=None, min_length=2, max_length=160)
    restaurant_description: str | None = Field(default=None, max_length=1200)
    supported_languages: list[Literal["en", "ta", "hi"]] | None = None
