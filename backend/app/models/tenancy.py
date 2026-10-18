import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, uuid_pk


class Hotel(Base, TimestampMixin):
    """Tenant root. Every business entity below carries hotel_id."""

    __tablename__ = "hotels"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    tagline: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    default_language: Mapped[str] = mapped_column(String(8), default="en")
    supported_languages: Mapped[list] = mapped_column(JSON, default=lambda: ["en", "ta", "hi"])
    assistant_name: Mapped[str] = mapped_column(String(60), default="AURA")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurants: Mapped[list["Restaurant"]] = relationship(back_populates="hotel", cascade="all, delete-orphan")


class Restaurant(Base, TimestampMixin):
    __tablename__ = "restaurants"
    __table_args__ = (UniqueConstraint("hotel_id", "slug", name="uq_restaurant_slug"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    positioning: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    cuisine_style: Mapped[str | None] = mapped_column(String(160))
    opening_hours: Mapped[str | None] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    hotel: Mapped[Hotel] = relationship(back_populates="restaurants")
