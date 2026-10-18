"""Executes LLM tool calls against PostgreSQL. Pure functions of (args, context) -> JSON-serialisable dict."""
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.i18n import ALLERGY_NOTICE
from app.core.logging import log_ctx
from app.models import Hotel, Restaurant
from app.services.knowledge.service import KnowledgeService
from app.services.menu.allergens import allergen_codes, ingredient_hits, resolve_allergen
from app.services.menu.serialize import SPICE_ORDER, dietary_map, dish_for_tool
from app.services.menu.service import MenuService
from app.services.recommendation.engine import Preferences, RecommendationEngine

log = logging.getLogger("tools")
DIETARY_LABEL = {"vegetarian": "vegetarian", "vegan": "vegan", "gluten_free": "gluten free", "halal": "halal", "jain": "Jain"}


@dataclass
class ToolContext:
    db: Session
    hotel: Hotel
    restaurant: Restaurant
    language: str = "en"
    dishes_seen: list[str] = field(default_factory=list)
    events: list[tuple[str, dict]] = field(default_factory=list)
    allergen_used: bool = False
    unknown_info: bool = False

    def __post_init__(self):
        self.menu = MenuService(self.db, self.hotel.id, self.restaurant.id)
        self.knowledge = KnowledgeService(self.db, self.hotel.id)
        self.engine = RecommendationEngine(self.menu)

    def track(self, dishes) -> None:
        for d in dishes:
            if d.name not in self.dishes_seen:
                self.dishes_seen.append(d.name)

    def event(self, kind: str, **payload) -> None:
        self.events.append((kind, payload))


def _lookup(ctx: ToolContext, name: str):
    res = ctx.menu.resolve(name or "")
    if res.dish:
        ctx.track([res.dish])
        return res.dish, None
    if res.candidates:
        return None, {"error": "ambiguous_or_unsure", "message": "Several dishes could match. Ask the guest which one they mean.",
                      "candidates": [d.name for d in res.candidates]}
    return None, {"error": "dish_not_found", "message": f"No dish called '{name}' is on the menu.",
                  "menu": [d.name for d in ctx.menu.list_dishes()]}


# ------------------------------------------------------------------ tools
def search_menu(ctx: ToolContext, query: str, limit: int = 5) -> dict:
    found = ctx.menu.search(query, limit=int(limit or 5))
    ctx.track(found)
    return {"query": query, "count": len(found), "matches": [dish_for_tool(d) for d in found],
            **({} if found else {"note": "Nothing on the menu matched."})}


def get_dish_details(ctx: ToolContext, dish_name: str) -> dict:
    dish, err = _lookup(ctx, dish_name)
    if err:
        return err
    ctx.event("dish_viewed", dishes=[dish.name], via="assistant")
    return {"dish": dish_for_tool(dish, detail=True),
            "note": "Dietary flags marked 'unknown' are NOT confirmed - do not claim them."}


def get_ingredients(ctx: ToolContext, dish_name: str) -> dict:
    dish, err = _lookup(ctx, dish_name)
    if err:
        return err
    ctx.event("ingredient_question", dishes=[dish.name])
    d = dish_for_tool(dish, detail=True)
    ings = d.get("ingredients") or []
    note = ("This is the complete listed ingredient list; do not add others." if ings
            else "Ingredients are not listed in the current menu data. Please confirm with our restaurant team.")
    return {"dish": d["name"], "name_ta": d["name_ta"], "name_hi": d["name_hi"], "ingredients": ings,
            "listed_allergens": d["listed_allergens"], "note": note}


def get_allergens(ctx: ToolContext, dish_name: str | None = None, allergen: str | None = None) -> dict:
    ctx.allergen_used = True
    group = None
    if allergen:
        group = resolve_allergen(allergen)
        if not group:
            ctx.unknown_info = True
            return {"error": "allergen_not_tracked", "allergen": allergen,
                    "message": "The menu data does not track this allergen. Say you don't have that information and refer to the restaurant team."}
    base = {"safety_notice": ALLERGY_NOTICE.get(ctx.language, ALLERGY_NOTICE["en"]),
            "basis": "Declared allergens + listed ingredients only. Cross-contact is possible."}

    if dish_name:
        dish, err = _lookup(ctx, dish_name)
        if err:
            return err
        declared = [l.allergen.label for l in dish.allergen_links]
        ctx.event("allergen_question", dishes=[dish.name], allergen=group or allergen)
        out = {**base, "dish": dish.name, "declared_allergens": declared or "none listed"}
        if group:
            codes = {l.allergen.code for l in dish.allergen_links}
            hits = ingredient_hits(group, [l.ingredient.name for l in dish.ingredient_links])
            contains = bool(codes & set(allergen_codes(group)))
            matched = [l.allergen.label for l in dish.allergen_links if l.allergen.code in allergen_codes(group)]
            out.update({"asked_about": group, "declared_contains": contains, "matched_allergens": matched, "related_ingredients_listed": hits,
                        "verdict": "contains (declared)" if contains else ("not declared, but a related ingredient is listed" if hits else "not listed in allergens or ingredients")})
        return out

    if group:
        contains, mentions, clear = [], [], []
        for dish in ctx.menu.list_dishes(available_only=True):
            codes = {l.allergen.code for l in dish.allergen_links}
            hits = ingredient_hits(group, [l.ingredient.name for l in dish.ingredient_links])
            if codes & set(allergen_codes(group)):
                contains.append({"dish": dish.name, "declared": [l.allergen.label for l in dish.allergen_links if l.allergen.code in allergen_codes(group)],
                                 "related_ingredients": hits})
                ctx.track([dish])
            elif hits:
                mentions.append({"dish": dish.name, "related_ingredients": hits})
                ctx.track([dish])
            else:
                clear.append(dish.name)
        ctx.event("allergen_question", dishes=[c["dish"] for c in contains], allergen=group)
        extra = {}
        if group == "nuts":
            extra["note"] = "Coconut is tracked separately; mention dishes with a coconut allergen only if relevant."
        return {**base, "asked_about": group, "contain_declared": contains, "ingredient_mention_only": mentions,
                "not_listed_in": clear, **extra}
    return {"error": "need_dish_or_allergen"}


def get_dishes_by_dietary_preference(ctx: ToolContext, preference: str) -> dict:
    ctx.event("dietary_question", dietary=preference)
    matches = [d for d in ctx.menu.list_dishes(available_only=True) if dietary_map(d)[preference] == "yes"]
    ctx.track(matches)
    out = {"preference": preference, "count": len(matches), "dishes": [dish_for_tool(d) for d in matches]}
    if preference in ("halal", "jain") and not matches:
        ctx.unknown_info = True
        out["note"] = f"The menu data does not mark any dish as {DIETARY_LABEL[preference]}. Do NOT claim any dish is."
    return out


def get_dishes_by_spice_level(ctx: ToolContext, spice_level: str, include_milder: bool = False) -> dict:
    target = SPICE_ORDER.get(spice_level, 0)
    matches = [d for d in ctx.menu.list_dishes(available_only=True)
               if (SPICE_ORDER.get(d.spice_level, 0) <= target if include_milder else d.spice_level == spice_level)]
    ctx.track(matches)
    return {"spice_level": spice_level, "include_milder": include_milder, "count": len(matches),
            "dishes": [dish_for_tool(d) for d in matches]}


def get_today_specials(ctx: ToolContext) -> dict:
    specials = ctx.menu.active_specials()
    ctx.event("special_viewed", chef_special=any(s.dish and s.dish.is_chef_special for s in specials))
    items = []
    for s in specials:
        if s.dish:
            ctx.track([s.dish])
        items.append({"type": s.special_type, "title": s.title, "note": s.description,
                      "dish": dish_for_tool(s.dish) if s.dish else None})
    return {"count": len(items), "specials": items,
            **({} if items else {"note": "No specials are set right now."})}


def get_available_dishes(ctx: ToolContext, category: str | None = None) -> dict:
    from app.core.text import normalize
    dishes = ctx.menu.list_dishes()
    if category:
        c = normalize(category).replace(" ", "-")
        dishes = [d for d in dishes if d.category and (d.category.slug == c or d.category.slug.rstrip("s") == c.rstrip("s") or normalize(d.category.name) == normalize(category))]
    avail = [d for d in dishes if d.is_available]
    ctx.track(avail)
    return {"available": [dish_for_tool(d) for d in avail], "currently_unavailable": [d.name for d in dishes if not d.is_available]}


def recommend_dishes(ctx: ToolContext, preferences: dict | None = None) -> dict:
    prefs = Preferences.from_dict(preferences)
    if prefs.exclude_allergens:
        ctx.allergen_used = True  # allergy-driven filtering always carries the safety notice
    results = ctx.engine.recommend(prefs)
    ctx.track([r.dish for r in results])
    dietary = next((c for c in ("vegetarian", "vegan", "gluten_free") if getattr(prefs, c)), None)
    ctx.event("dish_recommended", dishes=[r.dish.name for r in results], dietary=dietary)
    if dietary:
        ctx.event("dietary_question", dietary=dietary)
    if prefs.chef_special:
        ctx.event("special_viewed", chef_special=True)
    out: dict = {"criteria": {k: v for k, v in prefs.__dict__.items() if v not in (None, [], False)}, "count": len(results),
                 **({"safety_notice": ALLERGY_NOTICE.get(ctx.language, ALLERGY_NOTICE["en"])} if prefs.exclude_allergens else {}),
                 "recommendations": [{"dish": dish_for_tool(r.dish), "matched": r.reasons} for r in results]}
    if not results:
        relaxed = Preferences.from_dict({**prefs.__dict__})
        for field_name in ("spice_level", "max_spice_level", "min_spice_level", "max_calories", "category", "cuisine", "chef_special"):
            if getattr(relaxed, field_name):
                setattr(relaxed, field_name, None)
                alt = ctx.engine.recommend(relaxed)
                if alt:
                    ctx.track([r.dish for r in alt])
                    out["note"] = f"Nothing matched every preference. Closest options relax '{field_name}':"
                    out["closest"] = [dish_for_tool(r.dish) for r in alt]
                    break
        else:
            out["note"] = "Nothing on the menu matches those requirements."
    return out


def compare_dishes(ctx: ToolContext, dish_names: list[str]) -> dict:
    dishes, problems = [], []
    for n in dish_names or []:
        d, err = _lookup(ctx, n)
        (dishes.append(d) if d else problems.append({"asked": n, **err}))
    if len(dishes) < 2:
        return {"error": "need_two_known_dishes", "problems": problems}
    ctx.event("dish_viewed", dishes=[d.name for d in dishes], via="compare")
    facts = [dish_for_tool(d, detail=True) for d in dishes]
    cal = [(f["name"], f["calories_kcal_approx"]) for f in facts if f["calories_kcal_approx"] is not None]
    levels = [SPICE_ORDER.get(f["spice_level"], 0) for f in facts]
    low_cal = min((c for _, c in cal), default=None)
    high_cal = max((c for _, c in cal), default=None)
    return {"dishes": facts, "problems": problems,
            "highlights": {
                "mildest": [f["name"] for f, lv in zip(facts, levels) if lv == min(levels)],
                "spiciest": [f["name"] for f, lv in zip(facts, levels) if lv == max(levels)],
                "all_equally_spiced": len(set(levels)) == 1,
                "lightest": [n for n, c in cal if c == low_cal],
                "richest_in_calories": [n for n, c in cal if c == high_cal],
                "all_equal_calories": low_cal == high_cal}}


def search_knowledge(ctx: ToolContext, query: str) -> dict:
    passages = ctx.knowledge.search(query)
    if not passages:
        ctx.unknown_info = True
    return {"count": len(passages), "passages": [{"title": p.title, "type": p.doc_type, "text": p.content} for p in passages],
            **({} if passages else {"note": "No knowledge document matches; say you don't have that information."})}


REGISTRY = {f.__name__: f for f in (
    search_menu, get_dish_details, get_ingredients, get_allergens, get_dishes_by_dietary_preference, get_dishes_by_spice_level,
    get_today_specials, get_available_dishes, recommend_dishes, compare_dishes, search_knowledge)}


def execute_tool(ctx: ToolContext, name: str, arguments: dict) -> dict:
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": "unknown_tool", "tool": name}
    try:
        result = fn(ctx, **(arguments or {}))
        log.info("tool executed", extra=log_ctx(tool=name, ok=True))
        return result
    except TypeError as exc:  # model sent bad arguments
        log.warning("tool bad arguments", extra=log_ctx(tool=name, error=str(exc)))
        return {"error": "bad_arguments", "message": "Check the tool schema and retry with valid arguments."}
    except Exception:  # noqa: BLE001 - never leak SQL/stack traces to the model or guest
        log.exception("tool failed", extra=log_ctx(tool=name))
        return {"error": "tool_failed", "message": "The lookup failed. Say you could not check right now."}
