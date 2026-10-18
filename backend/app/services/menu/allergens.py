"""Maps what a guest says ("nuts", "milk", "wheat") to allergen codes + ingredient keywords.

Ingredient keywords are a *safety net*: if an ingredient is listed that implies an allergen the dish
record does not declare, the assistant is told so and must flag it rather than claim the dish is safe.
"""
from app.core.text import normalize

# phrase -> (allergen codes, ingredient keywords)
_GROUPS: dict[str, tuple[list[str], list[str]]] = {
    "nuts": (["tree_nuts", "peanuts"], ["cashew", "almond", "pistachio", "walnut", "hazelnut", "pecan", "peanut", "groundnut"]),
    "tree_nuts": (["tree_nuts"], ["cashew", "almond", "pistachio", "walnut", "hazelnut", "pecan"]),
    "peanuts": (["peanuts"], ["peanut", "groundnut"]),
    "dairy": (["dairy"], ["milk", "cream", "butter", "yogurt", "curd", "paneer", "ghee", "cheese", "khoya", "milk solids"]),
    "gluten": (["gluten"], ["wheat", "maida", "atta", "semolina", "rava", "barley", "flour"]),
    "coconut": (["coconut"], ["coconut"]),
    "soy": (["soy"], ["soy"]),
    "eggs": (["eggs"], ["egg"]),
    "fish": (["fish"], ["fish"]),
    "shellfish": (["shellfish"], ["prawn", "shrimp", "crab", "lobster"]),
    "sesame": (["sesame"], ["sesame", "til"]),
    "mustard": ([], ["mustard"]),
}
_SYNONYMS = {
    "nut": "nuts", "nuts": "nuts", "tree nut": "tree_nuts", "tree nuts": "tree_nuts", "cashew": "tree_nuts", "cashews": "tree_nuts",
    "almond": "tree_nuts", "almonds": "tree_nuts", "peanut": "peanuts", "peanuts": "peanuts", "groundnut": "peanuts",
    "dairy": "dairy", "milk": "dairy", "lactose": "dairy", "cheese": "dairy", "paneer": "dairy", "cream": "dairy",
    "gluten": "gluten", "wheat": "gluten", "coconut": "coconut", "soy": "soy", "soya": "soy",
    "egg": "eggs", "eggs": "eggs", "fish": "fish", "shellfish": "shellfish", "prawn": "shellfish", "shrimp": "shellfish",
    "sesame": "sesame", "mustard": "mustard",
    # Tamil / Hindi
    "கொட்டை": "nuts", "கொட்டைகள்": "nuts", "முந்திரி": "tree_nuts", "நிலக்கடலை": "peanuts", "பால்": "dairy",
    "பால் பொருட்கள்": "dairy", "கோதுமை": "gluten", "தேங்காய்": "coconut",
    "मेवे": "nuts", "नट्स": "nuts", "काजू": "tree_nuts", "मूंगफली": "peanuts", "दूध": "dairy", "डेयरी": "dairy",
    "ग्लूटेन": "gluten", "गेहूं": "gluten", "नारियल": "coconut",
}
# ingredients that look like a trigger but are not (e.g. corn flour is not gluten)
_FALSE_FRIENDS = ("corn flour", "rice flour", "coconut milk", "coconut cream", "cocoa butter", "nutmeg", "butternut")


def resolve_allergen(text: str) -> str | None:
    t = normalize(text)
    if t in _SYNONYMS:
        return _SYNONYMS[t]
    if t.replace(" ", "_") in _GROUPS:
        return t.replace(" ", "_")
    for phrase, group in _SYNONYMS.items():
        if phrase in t.split() or (" " in phrase and phrase in t):
            return group
    return None


def allergen_codes(group: str) -> list[str]:
    return _GROUPS[group][0]


def ingredient_hits(group: str, ingredients: list[str]) -> list[str]:
    keywords = _GROUPS[group][1]
    hits = []
    for ing in ingredients:
        low = normalize(ing)
        if any(f in low for f in _FALSE_FRIENDS):
            continue
        if any(k in low for k in keywords):
            hits.append(ing)
    return hits
