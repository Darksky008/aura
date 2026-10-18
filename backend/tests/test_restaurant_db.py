import pytest
from app.database.restaurant_db import MenuItem, get_restaurant_session_maker, resolve_restaurant_db_path
from app.services.ai.assistant import AssistantService
from app.services.ai.factory import build_providers
from app.services.menu.service import MenuService
from app.tools.executor import ToolContext, execute_tool


def test_restaurant_db_connection():
    path = resolve_restaurant_db_path("database/aura_restaurant.db")
    assert path.exists(), f"aura_restaurant.db was not found at {path}"
    assert path.name == "aura_restaurant.db"

    sm = get_restaurant_session_maker(str(path))
    with sm() as s:
        items = list(s.query(MenuItem).order_by(MenuItem.id).all())
        assert len(items) == 15
        item_map = {it.dish_name: (it.category, it.price) for it in items}
        assert item_map["Masala Dosa"] == ("Breakfast", 90.0)
        assert item_map["Paneer Tikka"] == ("Starter", 180.0)
        assert item_map["Idli"] == ("Breakfast", 40.0)
        assert item_map["Gulab Jamun"] == ("Dessert", 60.0)
        assert item_map["Fresh Lime Juice"] == ("Beverage", 50.0)


def test_menu_service_with_restaurant_db(db, hotel, restaurant):
    svc = MenuService(db, hotel.id, restaurant.id, restaurant_db_path="database/aura_restaurant.db")
    dishes = svc.list_dishes()
    assert len(dishes) == 15

    # Categories test
    categories = [c.name for c in svc.categories()]
    assert categories == ["Breakfast", "Starter", "Main Course", "Dessert", "Beverage"]

    # Category queries
    breakfast = svc.list_dishes(category_slug="breakfast")
    assert {d.name for d in breakfast} == {"Idli", "Medu Vada", "Pongal", "Masala Dosa", "Ghee Roast Dosa"}

    starters = svc.list_dishes(category_slug="starter")
    assert {d.name for d in starters} == {"Paneer Tikka", "Gobi Manchurian", "Veg Spring Rolls"}

    desserts = svc.list_dishes(category_slug="dessert")
    assert {d.name for d in desserts} == {"Gulab Jamun", "Vanilla Ice Cream"}

    # Known dish and price query
    dosa = svc.resolve("Masala Dosa").dish
    assert dosa is not None
    assert dosa.name == "Masala Dosa"
    assert dosa.price == 90.0
    assert dosa.category.name == "Breakfast"

    tikka = svc.resolve("Paneer Tikka").dish
    assert tikka is not None
    assert tikka.name == "Paneer Tikka"
    assert tikka.price == 180.0
    assert tikka.category.name == "Starter"


def test_executor_tools_with_restaurant_db(db, hotel, restaurant):
    ctx = ToolContext(db, hotel, restaurant)
    ctx.menu = MenuService(db, hotel.id, restaurant.id, restaurant_db_path="database/aura_restaurant.db")

    # get_dish_details test
    details = execute_tool(ctx, "get_dish_details", {"dish_name": "Masala Dosa"})
    assert details["dish"]["name"] == "Masala Dosa"
    assert details["dish"]["price"] == 90.0
    assert details["dish"]["category"] == "Breakfast"

    # get_available_dishes test by category
    avail = execute_tool(ctx, "get_available_dishes", {"category": "Breakfast"})
    dish_names = [d["name"] for d in avail["available"]]
    assert "Idli" in dish_names and "Masala Dosa" in dish_names


def test_assistant_queries_restaurant_db(db, hotel, restaurant):
    from app.core.config import get_settings
    settings = get_settings()
    settings.restaurant_database_path = "database/aura_restaurant.db"

    primary, fallback = build_providers(db, hotel, restaurant.id, settings)
    svc = AssistantService(db, hotel, restaurant, primary, fallback)
    session = svc.start_session("en")

    # Test price query
    r_price = svc.chat(session, "What is the price of Masala Dosa?", "en")
    assert "90" in r_price["reply"]

    # Test category / dishes query
    r_cat = svc.chat(session, "What are the categories?", "en")
    assert "Breakfast" in r_cat["reply"] or "Starter" in r_cat["reply"]
