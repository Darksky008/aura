import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.restaurant_db import resolve_restaurant_db_path, get_restaurant_session_maker, MenuItem
from app.services.menu.service import MenuService
from app.services.ai.factory import build_providers
from app.services.ai.assistant import AssistantService
from app.database.session import SessionLocal
from app.models import Hotel
from sqlalchemy import select
from app.core.config import get_settings

def run_verification():
    print("=" * 60)
    print("1. CONFIRM BACKEND QUERIES database/aura_restaurant.db")
    print("=" * 60)
    db_path = resolve_restaurant_db_path("database/aura_restaurant.db")
    print(f"Resolved database path: {db_path}")
    assert db_path.exists(), f"Database does not exist at {db_path}"

    sm = get_restaurant_session_maker(str(db_path))
    with sm() as s:
        items = list(s.query(MenuItem).order_by(MenuItem.id).all())
        print(f"Total rows in menu_items table: {len(items)}")
        assert len(items) == 15, f"Expected 15 items, found {len(items)}"
        for it in items:
            print(f"  [{it.id}] {it.dish_name:22} | {it.category:12} | Rs {it.price}")

    print("\n" + "=" * 60)
    print("2. TEST KNOWN DISH, CATEGORY, AND PRICE QUERIES")
    print("=" * 60)
    with SessionLocal() as db:
        hotel = db.scalar(select(Hotel).where(Hotel.slug == "aurelia-grand"))
        assert hotel is not None
        restaurant = hotel.restaurants[0]
        svc = MenuService(db, hotel.id, restaurant.id, restaurant_db_path="database/aura_restaurant.db")

        # Test known dish lookup
        dosa = svc.resolve("Masala Dosa").dish
        assert dosa is not None, "Failed to resolve Masala Dosa"
        print(f"Known dish resolved: {dosa.name} (Category: {dosa.category.name}, Price: Rs {dosa.price})")
        assert dosa.price == 90.0, f"Expected Rs 90.0, got {dosa.price}"

        tikka = svc.resolve("Paneer Tikka").dish
        assert tikka is not None, "Failed to resolve Paneer Tikka"
        print(f"Known dish resolved: {tikka.name} (Category: {tikka.category.name}, Price: Rs {tikka.price})")
        assert tikka.price == 180.0, f"Expected Rs 180.0, got {tikka.price}"

        # Test category query
        categories = [c.name for c in svc.categories()]
        print(f"Categories in database: {categories}")
        assert categories == ["Breakfast", "Starter", "Main Course", "Dessert", "Beverage"]

        breakfast_dishes = svc.list_dishes(category_slug="breakfast")
        breakfast_names = [d.name for d in breakfast_dishes]
        print(f"Dishes in Breakfast category: {breakfast_names}")
        assert set(breakfast_names) == {"Idli", "Medu Vada", "Pongal", "Masala Dosa", "Ghee Roast Dosa"}

        starter_dishes = svc.list_dishes(category_slug="starter")
        starter_names = [d.name for d in starter_dishes]
        print(f"Dishes in Starter category: {starter_names}")
        assert set(starter_names) == {"Paneer Tikka", "Gobi Manchurian", "Veg Spring Rolls"}

        # Test price query via assistant
        settings = get_settings()
        settings.restaurant_database_path = "database/aura_restaurant.db"
        primary, fallback = build_providers(db, hotel, restaurant.id, settings)
        assistant = AssistantService(db, hotel, restaurant, primary, fallback)
        session = assistant.start_session("en")

        q1 = "What is the price of Masala Dosa?"
        r1 = assistant.chat(session, q1, "en")
        print(f"\nUser: {q1}")
        print(f"Assistant: {r1['reply']}")
        assert "90" in r1["reply"], f"Expected 90 in reply, got: {r1['reply']}"

        q2 = "How much does Paneer Tikka cost?"
        r2 = assistant.chat(session, q2, "en")
        print(f"\nUser: {q2}")
        print(f"Assistant: {r2['reply']}")
        assert "180" in r2["reply"], f"Expected 180 in reply, got: {r2['reply']}"

        q3 = "What dishes do you have in Breakfast?"
        r3 = assistant.chat(session, q3, "en")
        print(f"\nUser: {q3}")
        print(f"Assistant: {r3['reply']}")
        assert any(dish in r3["reply"] for dish in ["Idli", "Medu Vada", "Pongal", "Masala Dosa"]), f"Expected breakfast items in reply, got: {r3['reply']}"

        q4 = "What are your categories?"
        r4 = assistant.chat(session, q4, "en")
        print(f"\nUser: {q4}")
        print(f"Assistant: {r4['reply']}")
        assert "Breakfast" in r4["reply"] and "Starter" in r4["reply"], f"Expected categories in reply, got: {r4['reply']}"

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
