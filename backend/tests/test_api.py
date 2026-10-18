import json

import pytest


def test_health_and_docs(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"].startswith("AURA")


def test_menu_endpoints(client):
    data = client.get("/api/menu").json()
    assert len(data["dishes"]) == 7 and [c["slug"] for c in data["categories"]] == ["starters", "main-course", "south-indian", "desserts"]
    assert {d["name"] for d in client.get("/api/menu?dietary=vegan").json()["dishes"]} == {"Masala Dosa", "Vegetable Biryani"}
    one = data["dishes"][0]
    assert client.get(f"/api/menu/{one['id']}").json()["name"] == one["name"]
    assert client.get("/api/menu/00000000-0000-0000-0000-000000000000").status_code == 404
    assert client.get("/api/menu?dietary=bogus").status_code == 422
    assert all(d["price"] is None for d in data["dishes"])      # prices are never invented


def test_unknown_hotel_is_friendly(client):
    r = client.get("/api/menu", headers={"X-Hotel-Slug": "nope"})
    assert r.status_code == 404 and "isn't set up" in r.json()["error"]


def test_specials_and_current_hotel(client):
    assert client.get("/api/specials").json()[0]["type"] == "today"
    h = client.get("/api/hotels/current").json()
    assert h["assistant_name"] == "AURA" and [l["code"] for l in h["languages"]] == ["en", "ta", "hi"]


def test_chat_roundtrip_and_memory(client):
    sid = client.post("/api/assistant/session", json={"language": "en"}).json()["session_id"]
    r = client.post("/api/assistant/chat", json={"message": "Recommend something vegetarian", "session_id": sid}).json()
    assert r["session_id"] == sid and "Paneer Tikka" in r["reply"]
    r2 = client.post("/api/assistant/chat", json={"message": "Which one is less spicy?", "session_id": sid}).json()
    assert "milder" in r2["reply"]


def test_chat_stream_emits_tool_then_final(client):
    with client.stream("POST", "/api/assistant/chat/stream", json={"message": "What is today's special?"}) as resp:
        events = [json.loads(line) for line in resp.iter_lines() if line]
    assert events[0] == {"type": "tool", "name": "get_today_specials"} and events[-1]["type"] == "final"


def test_chat_validation_and_bad_session(client):
    assert client.post("/api/assistant/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/assistant/chat", json={"message": "x" * 1001}).status_code == 422
    r = client.post("/api/assistant/chat", json={"message": "hi", "session_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404 and "expired" in r.json()["error"]


def test_dish_context_is_used(client):
    dish = next(d for d in client.get("/api/menu").json()["dishes"] if d["name"] == "Masala Dosa")
    r = client.post("/api/assistant/chat", json={"message": "Why should I try this dish?", "dish_id": dish["id"]}).json()
    assert "Masala Dosa" in r["reply"]


def test_recommend_endpoint(client):
    r = client.post("/api/assistant/recommend", json={"preferences": {"vegetarian": True, "spice_level": "mild"}}).json()
    assert {x["dish"]["name"] for x in r["recommendations"]} == {"Paneer Tikka", "Malai Kofta"}


def test_voice_capabilities_and_transcribe_requires_config(client):
    caps = client.get("/api/voice/capabilities").json()
    assert caps["stt"] is False and "ta" in caps["languages"]
    r = client.post("/api/voice/transcribe", files={"audio": ("a.webm", b"0" * 4000, "audio/webm")}, data={"language": "ta"})
    assert r.status_code == 503


def test_admin_dish_crud_with_validation(client):
    payload = {"name": "Dal Makhani", "spice_level": "mild", "calories_kcal": 450, "ingredients": ["Black lentils", "Butter", "Cream"],
               "allergens": ["dairy"], "dietary": {"vegetarian": "yes", "vegan": "no"}, "price": 650, "category_id": None}
    created = client.post("/api/admin/dishes", json=payload)
    assert created.status_code == 201, created.text
    dish = created.json()
    assert dish["dietary"]["vegetarian"] == "yes" and dish["dietary"]["halal"] == "unknown" and dish["price"] == 650
    assert [i for i in dish["ingredients"]] == ["Black lentils", "Butter", "Cream"]

    upd = client.put(f"/api/admin/dishes/{dish['id']}", json={"spice_level": "medium", "ingredients": ["Black lentils"]}).json()
    assert upd["spice_level"] == "medium" and upd["ingredients"] == ["Black lentils"] and upd["name"] == "Dal Makhani"
    assert client.patch(f"/api/admin/dishes/{dish['id']}/availability?available=false").json()["is_available"] is False
    assert "Dal Makhani" not in client.post("/api/assistant/recommend", json={"preferences": {"vegetarian": True, "limit": 10}}).text
    assert client.delete(f"/api/admin/dishes/{dish['id']}").status_code == 204
    assert client.get(f"/api/menu/{dish['id']}").status_code == 404

    bad = client.post("/api/admin/dishes", json={"name": "x", "calories_kcal": -5, "allergens": ["lava"]})
    assert bad.status_code == 422 and bad.json()["fields"]


def test_admin_specials_knowledge_analytics_settings(client):
    dish = client.get("/api/menu").json()["dishes"][1]
    sp = client.post("/api/admin/specials", json={"dish_id": dish["id"], "special_type": "seasonal", "title": "Monsoon pick"})
    assert sp.status_code == 201 and sp.json()["dish"]["name"] == dish["name"]
    assert client.post("/api/admin/specials", json={"dish_id": "00000000-0000-0000-0000-000000000000", "title": "Ghost"}).status_code == 404
    doc = client.post("/api/admin/knowledge", json={"doc_type": "chef", "title": "Our chef", "content": "The chef trained in regional kitchens."}).json()
    assert client.put(f"/api/admin/knowledge/{doc['id']}", json={"doc_type": "chef", "title": "Our chef", "content": "Updated content here, long enough."}).json()["content"].startswith("Updated")
    r = client.post("/api/assistant/chat", json={"message": "Tell me about the chef"}).json()
    assert "Updated content" in r["reply"] or "chef" in r["reply"].lower()
    a = client.get("/api/admin/analytics").json()
    assert a["total_menu_items"] == 7 and a["ai_conversations"] >= 1 and len(a["conversations_per_day"]) == 7
    s = client.put("/api/admin/settings", json={"tagline": "Dining, reimagined"}).json()
    assert s["tagline"] == "Dining, reimagined"
    assert client.get("/api/admin/assistant").json()["llm_provider"] == "offline"
    assert client.get("/api/admin/conversations").json()


def test_analytics_events_whitelist(client):
    assert client.post("/api/analytics/events", json={"event_type": "voice_used", "payload": {"language": "ta"}}).status_code == 202
    assert client.post("/api/analytics/events", json={"event_type": "drop_tables"}).status_code == 422


def test_admin_key_enforced(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setenv("ADMIN_API_KEY", "s3cret")
    get_settings.cache_clear()
    try:
        assert client.get("/api/admin/dishes").status_code == 401
        assert client.get("/api/admin/dishes", headers={"X-Admin-Key": "nope"}).status_code == 401
        assert client.get("/api/admin/dishes", headers={"X-Admin-Key": "s3cret"}).status_code == 200
        assert client.get("/api/menu").status_code == 200       # public stays public
    finally:
        monkeypatch.delenv("ADMIN_API_KEY")
        get_settings.cache_clear()
