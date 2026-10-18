import json

from app.services.menu.service import MenuService
from app.services.recommendation.engine import Preferences, RecommendationEngine
from app.tools.executor import ToolContext, execute_tool
from app.tools.schemas import TOOL_NAMES


def names(dishes):
    return {d.name for d in dishes}


def test_seed_has_seven_dishes(db, hotel, restaurant):
    assert len(MenuService(db, hotel.id, restaurant.id).list_dishes()) == 7


def test_menu_retrieval_and_categories(db, hotel, restaurant):
    svc = MenuService(db, hotel.id, restaurant.id)
    assert names(svc.list_dishes(category_slug="desserts")) == {"Gulab Jamun"}
    assert names(svc.list_dishes(chef_special=True)) == {"Royal Chicken Biryani", "Malai Kofta", "Butter Chicken"}
    assert names(svc.list_dishes(dietary="vegan")) == {"Masala Dosa", "Vegetable Biryani"}


def test_name_resolution(db, hotel, restaurant):
    svc = MenuService(db, hotel.id, restaurant.id)
    assert svc.resolve("chicken biryani").dish.name == "Royal Chicken Biryani"
    assert svc.resolve("veg biryani").dish.name == "Vegetable Biryani"
    assert svc.resolve("பனீர் டிக்கா").dish.name == "Paneer Tikka"      # Tamil
    assert svc.resolve("मसाला डोसा").dish.name == "Masala Dosa"          # Hindi
    amb = svc.resolve("biryani")
    assert amb.dish is None and len(amb.candidates) == 2               # ambiguity is reported, never guessed
    assert svc.resolve("pizza").dish is None


def test_ingredient_lookup(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    r = execute_tool(ctx, "get_ingredients", {"dish_name": "Paneer Tikka"})
    assert "Paneer" in r["ingredients"] and "Bell pepper" in r["ingredients"] and len(r["ingredients"]) == 14


def test_allergen_lookup_dish_and_group(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    r = execute_tool(ctx, "get_allergens", {"dish_name": "Malai Kofta", "allergen": "nuts"})
    assert r["declared_contains"] is True and "Tree nuts" in r["matched_allergens"] and r["safety_notice"]
    r = execute_tool(ctx, "get_allergens", {"dish_name": "Paneer Tikka", "allergen": "nuts"})
    assert r["declared_contains"] is False and r["related_ingredients_listed"] == []
    r = execute_tool(ctx, "get_allergens", {"allergen": "nuts"})
    assert [c["dish"] for c in r["contain_declared"]] == ["Malai Kofta"]
    assert ctx.allergen_used


def test_allergen_ingredient_safety_net(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    r = execute_tool(ctx, "get_allergens", {"dish_name": "Masala Dosa", "allergen": "mustard"})
    assert r["declared_contains"] is False and "Mustard seeds" in r["related_ingredients_listed"]   # flagged, not called safe
    assert execute_tool(ctx, "get_allergens", {"allergen": "unobtainium"})["error"] == "allergen_not_tracked"


def test_vegetarian_mild_recommendation(db, hotel, restaurant):
    eng = RecommendationEngine(MenuService(db, hotel.id, restaurant.id))
    got = {s.dish.name for s in eng.recommend(Preferences(vegetarian=True, spice_level="mild"))}
    assert got == {"Paneer Tikka", "Malai Kofta"}


def test_dietary_and_spice_filters(db, hotel, restaurant):
    eng = RecommendationEngine(MenuService(db, hotel.id, restaurant.id))
    vegan = {s.dish.name for s in eng.recommend(Preferences(vegan=True, limit=10))}
    assert vegan == {"Masala Dosa", "Vegetable Biryani"}
    medium = {s.dish.name for s in eng.recommend(Preferences(spice_level="medium", limit=10))}
    assert medium == {"Royal Chicken Biryani", "Masala Dosa", "Vegetable Biryani"}
    no_dairy = {s.dish.name for s in eng.recommend(Preferences(exclude_allergens=["dairy"], limit=10))}
    assert no_dairy == {"Masala Dosa", "Vegetable Biryani"}
    mains_light = eng.recommend(Preferences(category="main course", lightest=True, limit=1))
    assert mains_light[0].dish.calories_kcal == 520


def test_unavailable_dish_is_never_recommended(db, hotel, restaurant):
    svc = MenuService(db, hotel.id, restaurant.id)
    dish = svc.resolve("paneer tikka").dish
    svc.update_dish(dish.id, {"is_available": False})
    got = {s.dish.name for s in RecommendationEngine(svc).recommend(Preferences(vegetarian=True, spice_level="mild"))}
    assert got == {"Malai Kofta"}


def test_unknown_dietary_is_not_claimed(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    r = execute_tool(ctx, "get_dishes_by_dietary_preference", {"preference": "halal"})
    assert r["count"] == 0 and "Do NOT claim" in r["note"]
    d = execute_tool(ctx, "get_dish_details", {"dish_name": "butter chicken"})["dish"]
    assert d["halal"] == "unknown" and d["price"] == "not in menu data"


def test_compare_and_specials_and_bad_tool(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    c = execute_tool(ctx, "compare_dishes", {"dish_names": ["Paneer Tikka", "Masala Dosa"]})
    assert c["highlights"]["mildest"] == ["Paneer Tikka"] and c["highlights"]["lightest"] == ["Paneer Tikka"]
    s = execute_tool(ctx, "get_today_specials", {})
    assert s["specials"][0]["type"] == "today" and s["specials"][0]["dish"]["name"] == "Royal Chicken Biryani"
    assert execute_tool(ctx, "nope", {})["error"] == "unknown_tool"
    assert execute_tool(ctx, "get_dish_details", {"bogus": 1})["error"] == "bad_arguments"
    assert set(TOOL_NAMES) >= {"search_menu", "get_dish_details", "get_ingredients", "get_allergens", "recommend_dishes", "compare_dishes"}
    json.dumps(s)  # tool output must be JSON-serialisable


def test_tenant_isolation(db, hotel, restaurant):
    import uuid
    from app.core.errors import NotFoundError
    other = MenuService(db, uuid.uuid4(), restaurant.id)
    dish = MenuService(db, hotel.id, restaurant.id).resolve("paneer tikka").dish
    try:
        other.get_dish(dish.id)
        assert False, "should not be visible to another hotel"
    except NotFoundError:
        pass


def test_dessert_does_not_pad_savoury_recommendations(db, hotel, restaurant):
    eng = RecommendationEngine(MenuService(db, hotel.id, restaurant.id))
    got = {s.dish.name for s in eng.recommend(Preferences(vegetarian=True, max_spice_level="mild", limit=6))}
    assert got == {"Paneer Tikka", "Malai Kofta"}
    assert {s.dish.name for s in eng.recommend(Preferences(category="dessert"))} == {"Gulab Jamun"}
