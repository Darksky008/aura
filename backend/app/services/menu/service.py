"""All reads/writes of menu data. Every query is scoped by hotel_id (tenant isolation)."""
import difflib
import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.core.text import normalize, tokens
from app.database.restaurant_db import MenuItem, get_restaurant_session_maker
from app.models import (Allergen, DietaryTag, Dish, DishAllergen, DishDietaryTag, DishIngredient, Ingredient,
                        MenuCategory, Special)

log = logging.getLogger("menu.service")

_STOP = {"the", "a", "an", "of", "please", "dish", "item", "and", "with", "in", "is", "does", "what", "which", "i", "me", "my",
         "do", "have", "any", "contain", "contains", "ingredients", "ingredient", "about", "tell", "show"}


@dataclass
class Resolution:
    dish: Dish | None = None
    candidates: list[Dish] = field(default_factory=list)  # set when ambiguous / near-miss


def _slugify(name: str) -> str:
    return "-".join(tokens(name)) or uuid.uuid4().hex[:8]


DISH_TRANSLATIONS = {
    "Idli": {"ta": "இட்லி", "hi": "इडली"},
    "Medu Vada": {"ta": "மெது வடை", "hi": "मेदु वड़ा"},
    "Pongal": {"ta": "பொங்கல்", "hi": "पोंगल"},
    "Masala Dosa": {"ta": "மசாலா தோசை", "hi": "मसाला डोसा"},
    "Ghee Roast Dosa": {"ta": "நெய் ரோஸ்ட் தோசை", "hi": "घी रोस्ट डोसा"},
    "Paneer Tikka": {"ta": "பனீர் டிக்கா", "hi": "पनीर टिक्का"},
    "Gobi Manchurian": {"ta": "கோபி மஞ்சூரியன்", "hi": "गोभी मंचूरियन"},
    "Veg Spring Rolls": {"ta": "வெஜ் ஸ்பிரிங் ரோல்ஸ்", "hi": "वेज स्प्रिंग रोल्स"},
    "Paneer Butter Masala": {"ta": "பனீர் பட்டர் மசாலா", "hi": "पनीर बटर मसाला"},
    "Veg Fried Rice": {"ta": "வெஜ் ஃப்ரைட் ரைஸ்", "hi": "वेज फ्राइड राइस"},
    "Veg Biryani": {"ta": "வெஜ் பிரியாணி", "hi": "वेज बिरयानी"},
    "Butter Naan": {"ta": "பட்டர் நான்", "hi": "बटर नान"},
    "Gulab Jamun": {"ta": "குலாப் ஜாமுன்", "hi": "गुलाब जामुन"},
    "Vanilla Ice Cream": {"ta": "வெண்ணிலா ஐஸ்கிரீம்", "hi": "वेनिला आइसक्रीम"},
    "Fresh Lime Juice": {"ta": "ஃப்ரெஷ் லைம் ஜூஸ்", "hi": "ताज़ा नींबू का रस"},
}

CATEGORY_TRANSLATIONS = {
    "Breakfast": {"ta": "காலை உணவு", "hi": "नाश्ता"},
    "Starter": {"ta": "ஸ்டார்ட்டர்", "hi": "स्टार्टर"},
    "Main Course": {"ta": "முதன்மை உணவு", "hi": "मुख्य भोजन"},
    "Dessert": {"ta": "இனிப்பு", "hi": "मिठाई"},
    "Beverage": {"ta": "பானங்கள்", "hi": "पेय"},
}

DISH_ALIASES = {
    "Idli": ["idly", "idlis", "steamed idli"],
    "Medu Vada": ["vada", "vadai", "medu vadai", "crispy vada"],
    "Pongal": ["ven pongal", "ghee pongal"],
    "Masala Dosa": ["dosa", "masala dose", "crispy dosa"],
    "Ghee Roast Dosa": ["ghee roast", "ghee dosa", "roast dosa"],
    "Paneer Tikka": ["tikka", "paneer tikka starter"],
    "Gobi Manchurian": ["gobi", "manchurian", "cauliflower manchurian"],
    "Veg Spring Rolls": ["spring rolls", "spring roll", "veg rolls"],
    "Paneer Butter Masala": ["paneer butter", "paneer makhani", "butter paneer"],
    "Veg Fried Rice": ["fried rice", "chinese fried rice"],
    "Veg Biryani": ["biryani", "vegetable biryani", "veg dum biryani"],
    "Butter Naan": ["naan", "butter roti"],
    "Gulab Jamun": ["jamun", "gulab jamuns"],
    "Vanilla Ice Cream": ["ice cream", "vanilla scoop"],
    "Fresh Lime Juice": ["lime juice", "fresh lime", "lemon juice", "nimbu pani"],
}

DISH_CUISINES = {
    "Breakfast": "South Indian",
    "Starter": "Indo-Chinese & Tandoori",
    "Main Course": "North Indian & Indian",
    "Dessert": "Indian Desserts",
    "Beverage": "Beverages",
}

DISH_SPICE = {
    "Idli": "none",
    "Medu Vada": "mild",
    "Pongal": "mild",
    "Masala Dosa": "mild",
    "Ghee Roast Dosa": "mild",
    "Paneer Tikka": "medium",
    "Gobi Manchurian": "medium",
    "Veg Spring Rolls": "mild",
    "Paneer Butter Masala": "mild",
    "Veg Fried Rice": "mild",
    "Veg Biryani": "medium",
    "Butter Naan": "none",
    "Gulab Jamun": "none",
    "Vanilla Ice Cream": "none",
    "Fresh Lime Juice": "none",
}


@dataclass
class CategoryAdapter:
    id: uuid.UUID
    slug: str
    name: str
    name_translations: dict = field(default_factory=dict)
    sort_order: int = 0


class DishAdapter:
    def __init__(self, item: MenuItem, hotel_id: uuid.UUID, restaurant_id: uuid.UUID | None = None, legacy: Dish | None = None):
        self._item = item
        self.raw_id = item.id
        self.id = uuid.uuid5(uuid.NAMESPACE_OID, f"dish-{item.id}")
        self.hotel_id = hotel_id
        self.restaurant_id = restaurant_id
        self.slug = _slugify(item.dish_name)
        self.name = item.dish_name
        self.price = Decimal(str(item.price)) if item.price is not None else None

        cat_slug = _slugify(item.category)
        self.category = CategoryAdapter(
            id=uuid.uuid5(uuid.NAMESPACE_OID, f"cat-{cat_slug}"),
            slug=cat_slug,
            name=item.category,
            name_translations={"en": item.category, **CATEGORY_TRANSLATIONS.get(item.category, {})},
        )
        self.category_id = self.category.id

        self.name_translations = {"en": item.dish_name, **DISH_TRANSLATIONS.get(item.dish_name, {})}
        self.aliases = list(DISH_ALIASES.get(item.dish_name, []))
        self.description = f"Freshly prepared {item.dish_name} from our {item.category} selection."
        self.cuisine = DISH_CUISINES.get(item.category, "Indian")
        self.spice_level = DISH_SPICE.get(item.dish_name, "mild")
        self.calories_kcal = None
        self.preparation_notes = None
        self.image_url = None
        self.is_chef_special = item.dish_name in {"Paneer Butter Masala", "Ghee Roast Dosa", "Veg Biryani"}
        self.is_available = True
        self.sort_order = item.id

        if legacy:
            if legacy.description:
                self.description = legacy.description
            if legacy.cuisine:
                self.cuisine = legacy.cuisine
            if legacy.spice_level:
                self.spice_level = legacy.spice_level
            if legacy.calories_kcal:
                self.calories_kcal = legacy.calories_kcal
            if legacy.preparation_notes:
                self.preparation_notes = legacy.preparation_notes
            if legacy.image_url:
                self.image_url = legacy.image_url
            self.ingredient_links = list(getattr(legacy, "ingredient_links", []))
            self.allergen_links = list(getattr(legacy, "allergen_links", []))
            self.dietary_links = list(getattr(legacy, "dietary_links", []))
        else:
            self.ingredient_links = []
            self.allergen_links = []
            self.dietary_links = []


class MenuService:
    def __init__(self, db: Session, hotel_id: uuid.UUID, restaurant_id: uuid.UUID | None = None, restaurant_db_path: str | None = None):
        self.db = db
        self.hotel_id = hotel_id
        self.restaurant_id = restaurant_id
        self.restaurant_db_path = restaurant_db_path if restaurant_db_path is not None else get_settings().restaurant_database_path

    # ------------------------------------------------------------------ reads
    def _dish_query(self):
        q = select(Dish).where(Dish.hotel_id == self.hotel_id).options(selectinload(Dish.category))
        if self.restaurant_id:
            q = q.where(Dish.restaurant_id == self.restaurant_id)
        return q.order_by(Dish.sort_order, Dish.name)

    def _load_restaurant_items(self) -> list[DishAdapter]:
        if not self.restaurant_db_path:
            return []
        try:
            sm = get_restaurant_session_maker(self.restaurant_db_path)
            with sm() as s:
                items = list(s.scalars(select(MenuItem).order_by(MenuItem.id)))
                if not items:
                    return []
                legacy_dishes = {}
                if self.db is not None:
                    try:
                        legacy_dishes = {d.name.lower(): d for d in self.db.scalars(self._dish_query())}
                    except Exception:
                        legacy_dishes = {}
                return [DishAdapter(it, self.hotel_id, self.restaurant_id, legacy_dishes.get(it.dish_name.lower())) for it in items]
        except Exception as exc:
            log.warning("Could not query restaurant db (%s): %s", self.restaurant_db_path, exc)
            return []

    def categories(self) -> list:
        r_items = self._load_restaurant_items()
        if r_items:
            seen = set()
            cats = []
            for d in r_items:
                if d.category and d.category.slug not in seen:
                    seen.add(d.category.slug)
                    cats.append(d.category)
            return cats

        q = select(MenuCategory).where(MenuCategory.hotel_id == self.hotel_id).order_by(MenuCategory.sort_order)
        if self.restaurant_id:
            q = q.where(MenuCategory.restaurant_id == self.restaurant_id)
        return list(self.db.scalars(q))

    def list_dishes(self, *, available_only: bool = False, category_slug: str | None = None,
                    chef_special: bool | None = None, dietary: str | None = None) -> list:
        r_items = self._load_restaurant_items()
        if r_items:
            dishes = r_items
            if available_only:
                dishes = [d for d in dishes if d.is_available]
            if chef_special is not None:
                dishes = [d for d in dishes if d.is_chef_special is chef_special]
            if category_slug:
                norm_cat = category_slug.lower().replace(" ", "-").rstrip("s")
                dishes = [d for d in dishes if d.category and (d.category.slug == category_slug or d.category.slug.rstrip("s") == norm_cat or d.category.slug == norm_cat)]
            if dietary:
                from app.services.menu.serialize import dietary_map
                dishes = [d for d in dishes if dietary_map(d).get(dietary) == "yes"]
            return dishes

        q = self._dish_query()
        if available_only:
            q = q.where(Dish.is_available.is_(True))
        if chef_special is not None:
            q = q.where(Dish.is_chef_special.is_(chef_special))
        if category_slug:
            q = q.join(MenuCategory, Dish.category_id == MenuCategory.id).where(MenuCategory.slug == category_slug)
        dishes = list(self.db.scalars(q))
        if dietary:
            from app.services.menu.serialize import dietary_map
            dishes = [d for d in dishes if dietary_map(d).get(dietary) == "yes"]
        return dishes

    def get_dish(self, dish_id: uuid.UUID | str) -> Dish:
        sid = str(dish_id).lower()
        for d in self.list_dishes():
            if str(d.id).lower() == sid or str(getattr(d, "raw_id", "")).lower() == sid or d.slug == sid:
                return d
        dish = self.db.scalar(self._dish_query().where(Dish.id == dish_id)) if isinstance(dish_id, uuid.UUID) else None
        if not dish:  # also covers "dish belongs to another hotel"
            raise NotFoundError("That dish isn't on our menu.")
        return dish

    # ------------------------------------------------------------ name lookup
    @staticmethod
    def _name_variants(d: Dish) -> list[str]:
        raw = [d.name, *(d.aliases or []), *(d.name_translations or {}).values()]
        return [n for n in (normalize(x) for x in raw) if n]

    def resolve(self, name: str) -> Resolution:
        """Exact -> alias -> token containment -> fuzzy. Ambiguity is reported, never guessed."""
        q = normalize(name)
        if not q:
            return Resolution()
        dishes = self.list_dishes()
        exact = [d for d in dishes if q in self._name_variants(d)]
        if len(exact) == 1:
            return Resolution(exact[0])

        qt = {t for t in q.split() if t not in _STOP}
        if qt:
            full = [d for d in dishes if any(qt <= set(v.split()) for v in self._name_variants(d))]
            if len(full) == 1:
                return Resolution(full[0])
            if len(full) > 1:
                return Resolution(None, full)

        scored = []
        for d in dishes:
            best = max((difflib.SequenceMatcher(None, q, v).ratio() for v in self._name_variants(d)), default=0)
            scored.append((best, d))
        scored.sort(key=lambda s: -s[0])
        if scored and scored[0][0] >= 0.78 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.08):
            return Resolution(scored[0][1])
        near = [d for s, d in scored if s >= 0.6][:3]
        return Resolution(None, near)

    def search(self, query: str, limit: int = 5) -> list[Dish]:
        qt = [t for t in tokens(query) if t not in _STOP]
        if not qt:
            return []
        scored = []
        for d in self.list_dishes():
            name_toks = {t for v in self._name_variants(d) for t in v.split()}
            ing_toks = {t for i in getattr(d, "ingredient_links", []) for t in tokens(i.ingredient.name)}
            meta_toks = set(tokens(f"{d.cuisine or ''} {d.category.name if d.category else ''}"))
            desc_toks = set(tokens(d.description or ""))
            score = sum(3 * (t in name_toks) + 2 * (t in ing_toks) + 2 * (t in meta_toks) + (t in desc_toks) for t in qt)
            if score:
                scored.append((score, d.sort_order, d))
        scored.sort(key=lambda s: (-s[0], s[1]))
        return [d for _, _, d in scored[:limit]]

    # ---------------------------------------------------------------- specials
    def active_specials(self) -> list[Special]:
        from datetime import date

        today = date.today()
        q = select(Special).where(Special.hotel_id == self.hotel_id, Special.is_active.is_(True))
        if self.restaurant_id:
            q = q.where(Special.restaurant_id == self.restaurant_id)
        rows = [s for s in self.db.scalars(q) if (not s.starts_on or s.starts_on <= today) and (not s.ends_on or s.ends_on >= today)]
        order = {"today": 0, "chef_recommendation": 1, "weekend": 2, "seasonal": 3}
        return sorted(rows, key=lambda s: order.get(s.special_type, 9))

    # ------------------------------------------------------------ admin writes
    def _ingredient(self, name: str) -> Ingredient:
        name = name.strip()
        found = self.db.scalar(select(Ingredient).where(Ingredient.hotel_id == self.hotel_id, func.lower(Ingredient.name) == name.lower()))
        if found:
            return found
        ing = Ingredient(hotel_id=self.hotel_id, name=name)
        self.db.add(ing)
        self.db.flush()
        return ing

    def _apply(self, dish: Dish, data: dict) -> None:
        simple = ["name", "name_translations", "aliases", "description", "cuisine", "spice_level", "calories_kcal",
                  "preparation_notes", "image_url", "is_chef_special", "is_available", "sort_order", "category_id"]
        nullable = {"calories_kcal", "image_url", "description", "preparation_notes", "cuisine", "category_id"}
        for key in simple:
            if key not in data or (data[key] is None and key not in nullable):
                continue
            setattr(dish, key, data[key])
        if "price" in data:
            dish.price = Decimal(str(data["price"])) if data["price"] is not None else None
        if "ingredients" in data and data["ingredients"] is not None:
            dish.ingredient_links.clear()
            self.db.flush()
            seen = set()
            for pos, name in enumerate(n for n in data["ingredients"] if n and n.strip()):
                ing = self._ingredient(name)
                if ing.id in seen:
                    continue
                seen.add(ing.id)
                dish.ingredient_links.append(DishIngredient(dish_id=dish.id, ingredient_id=ing.id, position=pos, ingredient=ing))
        if "allergens" in data and data["allergens"] is not None:
            dish.allergen_links.clear()
            self.db.flush()
            for code in dict.fromkeys(data["allergens"]):
                al = self.db.scalar(select(Allergen).where(Allergen.code == code))
                if al:
                    dish.allergen_links.append(DishAllergen(dish_id=dish.id, allergen_id=al.id, allergen=al))
        if "dietary" in data and data["dietary"] is not None:
            dish.dietary_links.clear()
            self.db.flush()
            for code, value in data["dietary"].items():
                if value not in ("yes", "no"):
                    continue  # 'unknown' == no row
                tag = self.db.scalar(select(DietaryTag).where(DietaryTag.code == code))
                if tag:
                    dish.dietary_links.append(DishDietaryTag(dish_id=dish.id, tag_id=tag.id, value=value, basis="admin entry", tag=tag))

    def create_dish(self, data: dict) -> Dish:
        if not self.restaurant_id:
            raise NotFoundError("No restaurant selected.")
        slug = _slugify(data["name"])
        base, n = slug, 2
        while self.db.scalar(select(Dish.id).where(Dish.restaurant_id == self.restaurant_id, Dish.slug == slug)):
            slug, n = f"{base}-{n}", n + 1
        self._validate_category(data.get("category_id"))
        dish = Dish(hotel_id=self.hotel_id, restaurant_id=self.restaurant_id, slug=slug, name=data["name"])
        self.db.add(dish)
        self.db.flush()
        self._apply(dish, data)
        self.db.commit()
        return self.get_dish(dish.id)

    def update_dish(self, dish_id: uuid.UUID, data: dict) -> Dish:
        dish = self.get_dish(dish_id)
        self._validate_category(data.get("category_id"))
        self._apply(dish, data)
        self.db.commit()
        self.db.expire_all()
        return self.get_dish(dish_id)

    def delete_dish(self, dish_id: uuid.UUID) -> None:
        dish = self.get_dish(dish_id)
        self.db.delete(dish)
        self.db.commit()

    def _validate_category(self, category_id) -> None:
        if category_id is None:
            return
        cat = self.db.get(MenuCategory, category_id)
        if not cat or cat.hotel_id != self.hotel_id:  # tenant ownership check
            raise NotFoundError("Unknown category.")
