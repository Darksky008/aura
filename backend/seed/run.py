"""Idempotent demo seeding:  python seed.py [--reset]"""
import logging
import random
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import Base
from app.models import (AnalyticsEvent, Allergen, DietaryTag, Dish, DishAllergen, DishDietaryTag, DishIngredient,
                        Hotel, Ingredient, KnowledgeDocument, MenuCategory, Restaurant, Special)
from seed import demo_data as D

log = logging.getLogger("seed")


def seed_demo(db: Session, *, reset: bool = False, with_events: bool = True) -> bool:
    """Returns True if data was written, False if the hotel already existed."""
    bind = db.get_bind()
    if reset:
        db.rollback()
        Base.metadata.drop_all(bind)
    Base.metadata.create_all(bind)

    if db.scalar(select(Hotel).where(Hotel.slug == D.HOTEL["slug"])):
        return False

    tags = {c: DietaryTag(code=c, label=l) for c, l in D.DIETARY_TAGS}
    allergens = {c: Allergen(code=c, label=l) for c, l in D.ALLERGENS}
    for existing in db.scalars(select(DietaryTag)):
        tags[existing.code] = existing
    for existing in db.scalars(select(Allergen)):
        allergens[existing.code] = existing
    db.add_all([*tags.values(), *allergens.values()])

    hotel = Hotel(**D.HOTEL)
    restaurant = Restaurant(hotel=hotel, **D.RESTAURANT)
    db.add_all([hotel, restaurant])
    db.flush()

    categories = {}
    for c in D.CATEGORIES:
        cat = MenuCategory(hotel_id=hotel.id, restaurant_id=restaurant.id, **c)
        db.add(cat)
        categories[c["slug"]] = cat
    db.flush()

    ingredient_cache: dict[str, Ingredient] = {}
    dishes: dict[str, Dish] = {}
    for d in D.DISHES:
        dish = Dish(
            hotel_id=hotel.id, restaurant_id=restaurant.id, category_id=categories[d["category"]].id,
            slug=d["slug"], name=d["name"], name_translations=d["name_translations"], aliases=d["aliases"],
            description=d["description"], cuisine=d["cuisine"], spice_level=d["spice_level"],
            calories_kcal=d["calories_kcal"], price=None, preparation_notes=d["preparation_notes"],
            is_chef_special=d["chef_special"], is_available=d["available"], sort_order=d["sort_order"],
        )
        db.add(dish)
        db.flush()
        for pos, name in enumerate(d["ingredients"]):
            ing = ingredient_cache.get(name.lower())
            if not ing:
                ing = Ingredient(hotel_id=hotel.id, name=name)
                db.add(ing)
                db.flush()
                ingredient_cache[name.lower()] = ing
            db.add(DishIngredient(dish_id=dish.id, ingredient_id=ing.id, position=pos))
        for code in d["allergens"]:
            db.add(DishAllergen(dish_id=dish.id, allergen_id=allergens[code].id))
        for code, value in d["dietary"].items():
            db.add(DishDietaryTag(dish_id=dish.id, tag_id=tags[code].id, value=value, basis=D.BASIS))
        dishes[d["slug"]] = dish

    today = date.today()
    for slug, kind, title, desc in D.SPECIALS:
        db.add(Special(hotel_id=hotel.id, restaurant_id=restaurant.id, dish_id=dishes[slug].id, special_type=kind,
                       title=title, description=desc, starts_on=today - timedelta(days=30), ends_on=None, is_active=True))

    for doc_type, title, content in D.KNOWLEDGE:
        db.add(KnowledgeDocument(hotel_id=hotel.id, restaurant_id=restaurant.id, doc_type=doc_type, title=title, content=content))

    if with_events:
        _seed_events(db, hotel, [d["name"] for d in D.DISHES])
    db.commit()
    log.info("demo data seeded")
    return True


def _seed_events(db: Session, hotel: Hotel, dish_names: list[str]) -> None:
    """Demo analytics so the dashboard has something to show. Flagged source='seed'."""
    rnd = random.Random(7)
    topics = [("ingredient_question", 22), ("allergen_question", 14), ("dietary_question", 28), ("dish_recommended", 30),
              ("special_viewed", 16), ("voice_used", 24), ("dish_viewed", 36)]
    now = datetime.utcnow()
    for day in range(7):
        for _ in range(rnd.randint(4, 11)):
            when = now - timedelta(days=day, hours=rnd.randint(0, 20), minutes=rnd.randint(0, 59))
            db.add(AnalyticsEvent(hotel_id=hotel.id, event_type="conversation_started", payload={}, source="seed", created_at=when))
    weights = [w for _, w in topics]
    for _ in range(160):
        kind = rnd.choices([t for t, _ in topics], weights=weights)[0]
        payload: dict = {}
        if kind in {"ingredient_question", "allergen_question", "dish_recommended", "dish_viewed"}:
            payload["dishes"] = [rnd.choices(dish_names, weights=[9, 7, 8, 6, 8, 5, 4])[0]]
        if kind in {"dietary_question", "dish_recommended"}:
            payload["dietary"] = rnd.choices(["vegetarian", "vegan", "gluten_free"], weights=[6, 2, 1])[0]
        if kind == "special_viewed":
            payload["chef_special"] = rnd.random() < 0.6
        when = now - timedelta(days=rnd.randint(0, 6), hours=rnd.randint(0, 23))
        db.add(AnalyticsEvent(hotel_id=hotel.id, event_type=kind, payload=payload, source="seed", created_at=when))
