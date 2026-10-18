"""OpenAI-compatible function schemas exposed to the LLM (Groq speaks this format).

Tool arguments are ALWAYS in English (dish names may be given as the guest said them) so lookups are reliable
regardless of the conversation language."""

SPICE = ["none", "mild", "medium", "high"]
DIETARY = ["vegetarian", "vegan", "gluten_free", "halal", "jain"]
ALLERGEN_CODES = ["dairy", "gluten", "tree_nuts", "peanuts", "coconut", "soy", "eggs", "fish", "shellfish", "sesame"]


def _fn(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {"type": "function", "function": {"name": name, "description": description,
                                             "parameters": {"type": "object", "properties": properties, "required": required or []}}}


_DISH = {"type": "string", "description": "Dish name as the guest said it (English or transliterated), e.g. 'paneer tikka'."}

TOOL_SCHEMAS: list[dict] = [
    _fn("search_menu", "Free-text search across dish names, ingredients, cuisine and categories.",
        {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 8}}, ["query"]),
    _fn("get_dish_details", "Full facts for ONE dish: description, ingredients, spice, calories, dietary flags, allergens, availability, price.",
        {"dish_name": _DISH}, ["dish_name"]),
    _fn("get_ingredients", "The listed ingredients of ONE dish.", {"dish_name": _DISH}, ["dish_name"]),
    _fn("get_allergens",
        "Allergen facts. Give dish_name to see one dish's declared allergens (optionally checking one allergen), or only "
        "allergen (e.g. 'nuts', 'dairy', 'gluten') to see which dishes contain it. Always use this for any allergy question.",
        {"dish_name": _DISH, "allergen": {"type": "string", "description": "e.g. nuts, peanuts, dairy, gluten, coconut, egg, soy"}}),
    _fn("get_dishes_by_dietary_preference", "Dishes the menu explicitly marks as vegetarian / vegan / gluten_free / halal / jain.",
        {"preference": {"type": "string", "enum": DIETARY}}, ["preference"]),
    _fn("get_dishes_by_spice_level", "Dishes at a spice level. include_milder=true returns that level and everything milder.",
        {"spice_level": {"type": "string", "enum": SPICE}, "include_milder": {"type": "boolean"}}, ["spice_level"]),
    _fn("get_today_specials", "Today's special, weekend special, chef recommendation and seasonal items.", {}),
    _fn("get_available_dishes", "Dishes currently available with current prices and spice levels, optionally for one category (starter, main course, breakfast, dessert, beverage). Use for category listings, category prices, or finding the cheapest dishes.",
        {"category": {"type": "string"}}),
    _fn("recommend_dishes",
        "Filter and rank dishes from the live menu by guest preferences. Includes dish names, prices, and spice levels. Use for 'recommend', 'something mild and vegetarian', "
        "'what can I have without dairy', 'lightest main course', 'a dessert'.",
        {"preferences": {"type": "object", "properties": {
            "vegetarian": {"type": "boolean"}, "vegan": {"type": "boolean"}, "gluten_free": {"type": "boolean"},
            "halal": {"type": "boolean"}, "jain": {"type": "boolean"},
            "spice_level": {"type": "string", "enum": SPICE, "description": "exact level wanted"},
            "max_spice_level": {"type": "string", "enum": SPICE, "description": "'not too spicy' => mild"},
            "min_spice_level": {"type": "string", "enum": SPICE},
            "max_calories": {"type": "integer"},
            "category": {"type": "string", "description": "starter | main course | south indian | dessert"},
            "cuisine": {"type": "string", "description": "e.g. north indian, south indian, hyderabadi"},
            "chef_special": {"type": "boolean"},
            "exclude_allergens": {"type": "array", "items": {"type": "string", "enum": ALLERGEN_CODES}},
            "lightest": {"type": "boolean", "description": "sort by lowest calories"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 6}}}}, ["preferences"]),
    _fn("compare_dishes", "Side-by-side facts for 2-3 dishes.",
        {"dish_names": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3}}, ["dish_names"]),
    _fn("search_knowledge", "Restaurant/hotel knowledge: chef, cooking philosophy, FAQs, dining policies, dish stories.",
        {"query": {"type": "string"}}, ["query"]),
]

TOOL_NAMES = [t["function"]["name"] for t in TOOL_SCHEMAS]
