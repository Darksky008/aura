"""One canonical shape for a dish, used by the REST API *and* by the AI tools (so they can never disagree)."""
from app.models import Dish

DIETARY_CODES = ("vegetarian", "vegan", "gluten_free", "halal", "jain")
SPICE_ORDER = {"none": 0, "mild": 1, "medium": 2, "high": 3}


def dietary_map(dish: Dish) -> dict[str, str]:
    """yes | no | unknown  - 'unknown' means the database makes NO claim."""
    result = {code: "unknown" for code in DIETARY_CODES}
    for link in dish.dietary_links:
        result[link.tag.code] = link.value
    return result


def dish_to_dict(dish: Dish) -> dict:
    cat = dish.category
    return {
        "id": str(dish.id),
        "hotel_id": str(dish.hotel_id),
        "restaurant_id": str(dish.restaurant_id),
        "slug": dish.slug,
        "name": dish.name,
        "names": {"en": dish.name, **(dish.name_translations or {})},
        "aliases": list(dish.aliases or []),
        "description": dish.description,
        "category": {"id": str(cat.id), "slug": cat.slug, "name": cat.name, "names": {"en": cat.name, **(cat.name_translations or {})}} if cat else None,
        "cuisine": dish.cuisine,
        "spice_level": dish.spice_level,
        "calories_kcal": dish.calories_kcal,
        "calories_approximate": True,
        "price": float(dish.price) if dish.price is not None else None,
        "ingredients": [link.ingredient.name for link in dish.ingredient_links],
        "allergens": [{"code": l.allergen.code, "label": l.allergen.label} for l in dish.allergen_links],
        "dietary": dietary_map(dish),
        "preparation_notes": dish.preparation_notes,
        "image_url": dish.image_url,
        "is_chef_special": dish.is_chef_special,
        "is_available": dish.is_available,
        "sort_order": dish.sort_order,
    }


def dish_for_tool(dish: Dish, *, detail: bool = False) -> dict:
    """Compact, LLM-friendly facts. Absent/unknown stays explicit so the model cannot over-claim."""
    d = dish_to_dict(dish)
    out = {
        "name": d["name"],
        "name_ta": d["names"].get("ta"),
        "name_hi": d["names"].get("hi"),
        "category": d["category"]["name"] if d["category"] else None,
        "cuisine": d["cuisine"],
        "spice_level": d["spice_level"],
        "calories_kcal_approx": d["calories_kcal"],
        "vegetarian": d["dietary"]["vegetarian"],
        "vegan": d["dietary"]["vegan"],
        "gluten_free": d["dietary"]["gluten_free"],
        "halal": d["dietary"]["halal"],
        "jain": d["dietary"]["jain"],
        "listed_allergens": [a["label"] for a in d["allergens"]] or "none listed",
        "chef_special": d["is_chef_special"],
        "available": d["is_available"],
        "price": d["price"] if d["price"] is not None else "not in menu data",
    }
    if detail:
        out["description"] = d["description"]
        out["ingredients"] = d["ingredients"]
        out["preparation"] = d["preparation_notes"] or "not in menu data"
    return out
