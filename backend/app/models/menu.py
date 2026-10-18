import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (JSON, Boolean, Date, ForeignKey, Integer, Numeric, String, Text,
                        UniqueConstraint, Uuid)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, uuid_pk

SPICE_LEVELS = ("none", "mild", "medium", "high")
SPECIAL_TYPES = ("today", "weekend", "chef_recommendation", "seasonal")


class MenuCategory(Base, TimestampMixin):
    __tablename__ = "menu_categories"
    __table_args__ = (UniqueConstraint("restaurant_id", "slug", name="uq_category_slug"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(100))
    name_translations: Mapped[dict] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Ingredient(Base, TimestampMixin):
    __tablename__ = "ingredients"
    __table_args__ = (UniqueConstraint("hotel_id", "name", name="uq_ingredient_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))


class DietaryTag(Base):
    """Global reference data (vegetarian, vegan, gluten_free, halal, jain)."""

    __tablename__ = "dietary_tags"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(40), unique=True)
    label: Mapped[str] = mapped_column(String(80))


class Allergen(Base):
    """Global reference data (dairy, gluten, tree_nuts, peanuts, ...)."""

    __tablename__ = "allergens"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(40), unique=True)
    label: Mapped[str] = mapped_column(String(80))


class Dish(Base, TimestampMixin):
    __tablename__ = "dishes"
    __table_args__ = (UniqueConstraint("restaurant_id", "slug", name="uq_dish_slug"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("menu_categories.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(160))
    name_translations: Mapped[dict] = mapped_column(JSON, default=dict)  # {"ta": "...", "hi": "..."}
    aliases: Mapped[list] = mapped_column(JSON, default=list)  # alternate spellings the guest may say
    description: Mapped[str | None] = mapped_column(Text)
    cuisine: Mapped[str | None] = mapped_column(String(120))
    spice_level: Mapped[str] = mapped_column(String(10), default="none")
    calories_kcal: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # None => never state a price
    preparation_notes: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_chef_special: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    category: Mapped[MenuCategory | None] = relationship()
    ingredient_links: Mapped[list["DishIngredient"]] = relationship(
        cascade="all, delete-orphan", order_by="DishIngredient.position", lazy="selectin"
    )
    allergen_links: Mapped[list["DishAllergen"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    dietary_links: Mapped[list["DishDietaryTag"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class DishIngredient(Base):
    __tablename__ = "dish_ingredients"

    dish_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    ingredient: Mapped[Ingredient] = relationship(lazy="joined")


class DishAllergen(Base):
    __tablename__ = "dish_allergens"

    dish_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    allergen_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True)

    allergen: Mapped[Allergen] = relationship(lazy="joined")


class DishDietaryTag(Base):
    """A dietary claim with an explicit yes/no. Missing row == 'unknown' (never claimable)."""

    __tablename__ = "dish_dietary_tags"

    dish_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("dietary_tags.id", ondelete="CASCADE"), primary_key=True)
    value: Mapped[str] = mapped_column(String(8), default="yes")  # yes | no
    basis: Mapped[str | None] = mapped_column(String(120))  # e.g. "listed ingredients"

    tag: Mapped[DietaryTag] = relationship(lazy="joined")


class Special(Base, TimestampMixin):
    __tablename__ = "specials"

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("dishes.id", ondelete="SET NULL"))
    special_type: Mapped[str] = mapped_column(String(30), default="today")
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    dish: Mapped[Dish | None] = relationship(lazy="joined")
