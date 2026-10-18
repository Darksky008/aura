"""Deterministic filtering + ranking. The LLM only *explains* what this returns."""
from dataclasses import dataclass, field

from app.core.text import normalize
from app.models import Dish
from app.services.menu.serialize import SPICE_ORDER, dietary_map
from app.services.menu.service import MenuService


@dataclass
class Preferences:
    vegetarian: bool | None = None
    vegan: bool | None = None
    gluten_free: bool | None = None
    halal: bool | None = None
    jain: bool | None = None
    spice_level: str | None = None      # exact: none | mild | medium | high
    max_spice_level: str | None = None  # "not too spicy" => mild
    min_spice_level: str | None = None
    max_calories: int | None = None
    category: str | None = None         # starter | main course | dessert | south indian ...
    cuisine: str | None = None
    chef_special: bool | None = None
    exclude_allergens: list[str] = field(default_factory=list)
    lightest: bool = False
    limit: int = 4

    @classmethod
    def from_dict(cls, data: dict | None) -> "Preferences":
        data = data or {}
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and v not in (None, "", [])}
        if "spice_level" in known:
            known["spice_level"] = {"hot": "high", "spicy": "high", "low": "mild", "not_spicy": "mild"}.get(known["spice_level"], known["spice_level"])
        if "exclude_allergens" in known and isinstance(known["exclude_allergens"], str):
            known["exclude_allergens"] = [known["exclude_allergens"]]
        return cls(**known)


@dataclass
class Scored:
    dish: Dish
    score: float
    reasons: list[str]


_CATEGORY_ALIASES = {
    "starter": "starter", "starters": "starter", "appetizer": "starter", "appetiser": "starter",
    "main": "main-course", "main course": "main-course", "mains": "main-course", "entree": "main-course",
    "dessert": "dessert", "desserts": "dessert", "sweet": "dessert",
    "south indian": "breakfast", "south": "breakfast",
    "breakfast": "breakfast", "tiffin": "breakfast",
    "beverage": "beverage", "beverages": "beverage", "drink": "beverage", "drinks": "beverage", "juice": "beverage",
}


class RecommendationEngine:
    def __init__(self, menu: MenuService):
        self.menu = menu

    def recommend(self, prefs: Preferences) -> list[Scored]:
        out: list[Scored] = []
        wants_dessert = bool(prefs.category and "dessert" in normalize(prefs.category)) or bool(prefs.category and "sweet" in normalize(prefs.category))
        cat_slug = _CATEGORY_ALIASES.get(normalize(prefs.category)) if prefs.category else None
        for dish in self.menu.list_dishes(available_only=True):
            diet = dietary_map(dish)
            reasons: list[str] = []
            # --- hard filters: "unknown" never satisfies a dietary requirement ---
            ok = True
            for code in ("vegetarian", "vegan", "gluten_free", "halal", "jain"):
                want = getattr(prefs, code)
                if want is True:
                    ok &= diet[code] == "yes"
                    reasons.append(code.replace("_", " "))
                elif want is False:
                    ok &= diet[code] == "no"
            if not ok:
                continue
            level = SPICE_ORDER.get(dish.spice_level, 0)
            if prefs.spice_level and dish.spice_level != prefs.spice_level:
                continue
            if prefs.max_spice_level and level > SPICE_ORDER.get(prefs.max_spice_level, 3):
                continue
            if prefs.min_spice_level and level < SPICE_ORDER.get(prefs.min_spice_level, 0):
                continue
            if prefs.spice_level or prefs.max_spice_level:
                reasons.append(f"{dish.spice_level} spice")
            if prefs.max_calories and (dish.calories_kcal is None or dish.calories_kcal > prefs.max_calories):
                continue
            if cat_slug and (not dish.category or (dish.category.slug != cat_slug and dish.category.slug.rstrip("s") != cat_slug.rstrip("s"))):
                continue
            if prefs.cuisine and normalize(prefs.cuisine) not in normalize(dish.cuisine or ""):
                continue
            if prefs.chef_special is True and not dish.is_chef_special:
                continue
            declared = {l.allergen.code for l in dish.allergen_links}
            if any(a in declared for a in prefs.exclude_allergens):
                continue
            if prefs.exclude_allergens:
                reasons.append("no " + ", ".join(prefs.exclude_allergens) + " listed")

            score = 1.0
            if dish.is_chef_special:
                score += 0.5 if prefs.chef_special else 0.2
            if not cat_slug and not wants_dessert and dish.category and dish.category.slug == "desserts":
                score -= 0.8  # don't lead with dessert unless asked
            out.append(Scored(dish, score, reasons))

        if not cat_slug and not wants_dessert:
            # a dessert never pads out a savoury answer when real savoury matches exist
            savoury = [x for x in out if not (x.dish.category and x.dish.category.slug == "desserts")]
            if len(savoury) >= 2:
                out = savoury

        if prefs.lightest:
            out.sort(key=lambda s: (s.dish.calories_kcal if s.dish.calories_kcal is not None else 10**6, s.dish.sort_order))
        else:
            out.sort(key=lambda s: (-s.score, s.dish.sort_order))
        return out[: max(1, min(prefs.limit, 10))]
