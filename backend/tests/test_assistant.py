"""The ten spec scenarios + unknown-info test, run through the full tool pipeline (offline provider)."""
import pytest

from app.services.ai.factory import build_providers
from app.services.ai.assistant import AssistantService
from app.core.config import get_settings


@pytest.fixture()
def bot(db, hotel, restaurant):
    primary, fallback = build_providers(db, hotel, restaurant.id, get_settings())
    svc = AssistantService(db, hotel, restaurant, primary, fallback)
    session = svc.start_session("en")

    def ask(q: str) -> dict:
        return svc.chat(session, q, "en")
    return ask


def test_recommend_vegetarian(bot):
    r = bot("Recommend a vegetarian dish.")
    assert "recommend_dishes" in r["tools_used"]
    assert "Chicken" not in r["reply"] and "Paneer Tikka" in r["reply"]


def test_ingredients(bot):
    r = bot("What are the ingredients in Paneer Tikka?")
    assert r["tools_used"] == ["get_ingredients"] and "Paneer" in r["reply"] and "yogurt" in r["reply"].lower()


def test_is_paneer_tikka_spicy(bot):
    assert "mildly spiced" in bot("Is Paneer Tikka spicy?")["reply"]


def test_nuts_in_malai_kofta_has_safety_notice(bot):
    r = bot("Does Malai Kofta contain nuts?")
    assert "tree nuts" in r["reply"].lower() and "restaurant team" in r["reply"]


def test_paneer_tikka_nuts_not_listed_with_cross_contact_warning(bot):
    r = bot("Does the paneer tikka contain nuts?")
    assert "not listed" in r["reply"] and "cross-contact" in r["reply"]


def test_vegan_list(bot):
    r = bot("Which dishes are vegan?")
    assert "Masala Dosa" in r["reply"] and "Vegetable Biryani" in r["reply"] and "Butter" not in r["reply"]


def test_todays_special(bot):
    assert "Royal Chicken Biryani" in bot("What is today's special?")["reply"]


def test_compare(bot):
    r = bot("Compare Butter Chicken and Chicken Biryani.")
    assert r["tools_used"] == ["compare_dishes"] and "Butter Chicken" in r["reply"] and "Royal Chicken Biryani" in r["reply"]


def test_dairy_free(bot):
    r = bot("I don't eat dairy. What can I have?")
    assert "Masala Dosa" in r["reply"] and "Vegetable Biryani" in r["reply"] and "Paneer" not in r["reply"]
    assert "restaurant team" in r["reply"]


def test_mild_and_vegetarian(bot):
    r = bot("I want something mild and vegetarian.")
    assert "Paneer Tikka" in r["reply"] and "Malai Kofta" in r["reply"] and "Biryani" not in r["reply"]


def test_chicken_biryani_not_vegan(bot):
    assert bot("Is chicken biryani vegan?")["reply"].startswith("No, Royal Chicken Biryani is not vegan")


def test_unknown_information_is_not_invented(bot):
    r = bot("Does the Chicken Biryani contain artificial coloring?")
    assert "don't have information" in r["reply"] and "restaurant team" in r["reply"]


def test_price_not_invented(bot):
    assert "don't have prices" in bot("How much is the butter chicken?")["reply"]


def test_conversation_memory(bot):
    bot("Recommend something vegetarian.")
    r = bot("Which one is less spicy?")
    assert r["tools_used"] == ["compare_dishes"] and "milder" in r["reply"]


def test_ambiguous_dish_asks_back(bot):
    assert "Which one did you mean" in bot("What's in the biryani?")["reply"]
