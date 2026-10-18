"""OfflineProvider - a deterministic, rule-based stand-in for the LLM.

It speaks the exact same protocol as GroqProvider (it *plans* tool calls, then *composes* an answer from the tool
results), so the whole pipeline - tools, PostgreSQL, safety notices, memory, analytics - runs without any API key.
It is used (a) when GROQ_API_KEY is not configured, (b) as an automatic fallback if Groq is unreachable, (c) in tests.
It replies in English and never states anything that is not in a tool result.
"""
import json
import re
from collections.abc import Callable

from app.core.i18n import ALLERGY_NOTICE, UNKNOWN_INFO
from app.core.text import normalize
from app.services.ai.provider import AIProvider, AIResponse, ToolCall
from app.services.menu.allergens import allergen_codes, resolve_allergen

SPICE_WORDS = {"none": "not spicy at all", "mild": "mildly spiced", "medium": "medium spiced", "high": "quite spicy"}
UNKNOWN_ATTR = re.compile(r"(artificial |natural |added )?(colou?ring|colou?rs?|preservatives?|additives?|msg|organic|sugar free|keto|flavou?ring)|artificial|imported|sourced")
ALLERGEN_WORDS = {"nut", "nuts", "peanut", "peanuts", "cashew", "cashews", "almond", "almonds", "dairy", "milk", "lactose", "gluten",
                  "wheat", "coconut", "egg", "eggs", "soy", "soya", "sesame", "shellfish", "fish", "prawn", "shrimp", "mustard"}


def _join(items: list[str], word: str = "and") -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {word} " + items[-1]


class OfflineProvider(AIProvider):
    name = "offline"
    model = "rule-based"

    def __init__(self, dish_names: Callable[[], list[tuple[str, str]]] | None = None, category_names: Callable[[], list[str]] | None = None):
        # callable returning [(variant, canonical_name)], e.g. [("chicken biryani", "Royal Chicken Biryani")]
        self._names = dish_names or (lambda: [])
        self._categories = category_names or (lambda: [])

    # -------------------------------------------------------------- protocol
    def complete(self, messages, tools=None, *, temperature=0.0, max_tokens=0) -> AIResponse:
        idx = max(i for i, m in enumerate(messages) if m["role"] == "user")
        raw = messages[idx]["content"]
        viewing = re.match(r"\[The guest is currently viewing the dish: (.+?)\]\n", raw)
        text = raw[viewing.end():] if viewing else raw
        system = messages[0]["content"] if messages[0]["role"] == "system" else ""
        recent = re.search(r"recently discussed dishes: ([^\n]+?)\.", system)
        last = [s.strip() for s in recent.group(1).split(",")] if recent and "none yet" not in recent.group(1) else []
        tool_msgs = [m for m in messages[idx + 1:] if m["role"] == "tool"]
        plan = self._plan(text, last, viewing.group(1) if viewing else None)

        if plan["kind"] == "static":
            return self._say(plan["text"])
        if not tool_msgs:
            calls = plan.get("calls")
            if not calls:
                calls = [ToolCall(id="offline_1", name=plan["tool"], arguments=plan["args"])]
            raw_calls = [{"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.arguments)}} for c in calls]
            return AIResponse(None, calls, {"role": "assistant", "content": "", "tool_calls": raw_calls})
        results = [json.loads(m["content"]) for m in tool_msgs]
        return self._say(self._compose(plan, results, text))

    @staticmethod
    def _say(text: str) -> AIResponse:
        return AIResponse(text, [], {"role": "assistant", "content": text})

    # -------------------------------------------------------------- planning
    def _mentions(self, text: str) -> list[str]:
        t = f" {normalize(text)} "
        found: list[tuple[int, str]] = []
        for variant, canonical in sorted(self._names(), key=lambda p: -len(p[0])):
            v = f" {variant} "
            pos = t.find(v)
            if pos >= 0:
                t = t[:pos] + " " * len(v) + t[pos + len(v):]
                found.append((pos, canonical))
        ordered = [c for _, c in sorted(found)]
        out = list(dict.fromkeys(ordered))
        if not out and "biryani" in t:
            out = ["biryani"]
        return out

    def _plan(self, text: str, last: list[str], viewing: str | None) -> dict:
        t = normalize(text.replace("'", "").replace("\u2019", ""))
        words = set(t.split())
        m = self._mentions(text)
        if viewing and not m and re.search(r"\b(this|it|that)\b|why should|try", t):
            m = [viewing]

        if re.search(r"\b(thank|thanks|bye|goodbye)\b", t):
            return {"kind": "static", "text": "You're most welcome. Please let me know if there is anything else I can help you with."}
        if t in {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}:
            return {"kind": "static", "text": "Welcome to Aura! What can I help you discover from our menu today?"}

        if (re.search(r"\bcompare\b|\bvs\b|\bversus\b|difference between|\bor\b.*\bbetter\b", t) and len(m) >= 2):
            return {"kind": "tool", "intent": "compare", "tool": "compare_dishes", "args": {"dish_names": m[:3]}}
        if len(last) >= 2 and re.search(r"which (one|of)|of (them|these|those)|\bwhich is\b", t) and re.search(
                r"less|least|more|most|mild|spic|light|heav|calori|healthier|richer", t):
            return {"kind": "tool", "intent": "compare", "tool": "compare_dishes", "args": {"dish_names": last[:3]}}

        if re.search(r"\b(what are the|what are your|list|show)\b.*\bcategor(y|ies)\b|\bcategor(y|ies)\b", t) and not m:
            cats = self._categories()
            if cats:
                return {"kind": "static", "text": f"Our menu includes the following categories: {_join(cats)}."}

        if "special" in words or "specials" in words:
            return {"kind": "tool", "intent": "specials", "tool": "get_today_specials", "args": {}}

        # Extract category if present
        cat = None
        if "dessert" in t or "sweet" in t:
            cat = "dessert"
        elif re.search(r"starter|appetizer|appetiser", t):
            cat = "starter"
        elif "south indian" in t or "breakfast" in t or "tiffin" in t:
            cat = "breakfast"
        elif re.search(r"main course|\bmains?\b", t):
            cat = "main course"
        elif re.search(r"beverage|drink|juice", t):
            cat = "beverage"

        has_price = bool(re.search(r"\bprice|\bcost|how much|\brate\b", t))
        has_rec = bool(re.search(r"recommend|suggest|which is your|best|what would you|something", t))
        has_cheapest = bool(re.search(r"\b(cheap|cheapest|lowest price|least expensive|most affordable|best price)\b", t))

        # 1. Cheapest query (e.g. "What is the cheapest starter and what do you recommend?")
        if has_cheapest:
            calls = [
                ToolCall(id="call_avail", name="get_available_dishes", arguments={"category": cat} if cat else {}),
                ToolCall(id="call_rec", name="recommend_dishes", arguments={"preferences": {"category": cat, "limit": 3}} if cat else {"preferences": {"limit": 3}})
            ]
            return {"kind": "tool", "intent": "cheapest_and_recommend", "calls": calls, "category": cat or "starter"}

        # 2. Specific dish price + category recommendation (e.g. "Tell me the price of paneer tikka and recommend a main course")
        if m and has_price and has_rec:
            rec_cat = cat if (cat and cat != "starter") else (cat or "main course")
            calls = [
                ToolCall(id="call_price", name="get_dish_details", arguments={"dish_name": m[0]}),
                ToolCall(id="call_rec", name="recommend_dishes", arguments={"preferences": {"category": rec_cat, "limit": 3}}),
            ]
            return {"kind": "tool", "intent": "dish_price_and_recommend", "calls": calls, "dish_name": m[0], "rec_category": rec_cat}

        # 3. Category dishes + prices + recommendation (e.g. "What is the price and what would you recommend for starters?")
        if cat and (has_price or re.search(r"what.*have|what do you have|list|show|options", t)) and has_rec:
            calls = [
                ToolCall(id="call_avail", name="get_available_dishes", arguments={"category": cat}),
                ToolCall(id="call_rec", name="recommend_dishes", arguments={"preferences": {"category": cat, "limit": 3}}),
            ]
            return {"kind": "tool", "intent": "category_prices_and_recommend", "calls": calls, "category": cat}

        # 4. Category prices without specific dish (e.g. "What are the prices for starters?")
        if cat and has_price and not m:
            calls = [ToolCall(id="call_avail", name="get_available_dishes", arguments={"category": cat})]
            return {"kind": "tool", "intent": "category_prices", "calls": calls, "category": cat}

        # 5. Multiple mentioned dishes with price
        if len(m) >= 2 and has_price:
            calls = [ToolCall(id=f"call_{i}", name="get_dish_details", arguments={"dish_name": name}) for i, name in enumerate(m[:3])]
            return {"kind": "tool", "intent": "multiple_prices", "calls": calls, "dishes": m[:3]}

        # 6. Single dish with price
        if has_price and m:
            return {"kind": "tool", "intent": "price", "tool": "get_dish_details", "args": {"dish_name": m[0]}}

        # 7. Price requested with no dish and no category
        if has_price and not m and not cat:
            return {"kind": "static", "text": UNKNOWN_INFO["en"]}
        if UNKNOWN_ATTR.search(t):
            if m:
                return {"kind": "tool", "intent": "unknown_attr", "tool": "get_dish_details", "args": {"dish_name": m[0]}, "attr": (UNKNOWN_ATTR.search(t).group(0).strip() or "that")}
            return {"kind": "static", "text": UNKNOWN_INFO["en"]}
        if re.search(r"\bhalal\b|\bjain\b", t):
            diet = "halal" if "halal" in t else "jain"
            if m:
                return {"kind": "tool", "intent": "attr", "tool": "get_dish_details", "args": {"dish_name": m[0]}, "attr": diet}
            return {"kind": "tool", "intent": "dietary_list", "tool": "get_dishes_by_dietary_preference", "args": {"preference": diet}}

        group = None
        for w in t.split():
            if w in ALLERGEN_WORDS:
                group = resolve_allergen(w)
                break
        if "tree nut" in t:
            group = "tree_nuts"
        if group or "allerg" in t:
            exclusion = re.search(r"dont eat|do not eat|\bavoid|without|\bfree\b|allergic|cant eat|cannot eat|\bno\b|\bnot eat|intolerant|dont have|cant have", t) and not re.search(
                r"contain|include|ingredient|has any|have any|does", t)
            if exclusion and group and not m:
                codes = allergen_codes(group) if group in {"dairy", "gluten", "nuts", "tree_nuts", "peanuts", "coconut", "soy", "eggs", "fish", "shellfish", "sesame"} else []
                if codes:
                    return {"kind": "tool", "intent": "exclude", "tool": "recommend_dishes", "args": {"preferences": {"exclude_allergens": codes, "limit": 4}}, "group": group}
            args = {k: v for k, v in {"dish_name": m[0] if m else None, "allergen": group}.items() if v}
            if not args:
                return {"kind": "static", "text": "Of course. Which allergy should I check for - for example nuts, dairy or gluten? " + ALLERGY_NOTICE["en"]}
            return {"kind": "tool", "intent": "allergen", "tool": "get_allergens", "args": args or {}, "group": group, "multi": not m}

        if m and re.search(r"ingredient|made of|made with|whats in|what is in|\bcontains?\b|\bin the\b", t) and not re.search(r"vegan|vegetarian|spicy|spice|calor", t):
            return {"kind": "tool", "intent": "ingredients", "tool": "get_ingredients", "args": {"dish_name": m[0]}}

        prefs = self._prefs(t)
        if m and re.match(r"^(is|are|does|do|how)\b", t) or (m and re.search(r"vegan|vegetarian|spic|gluten|calor", t) and not re.search(r"recommend|suggest|similar", t)):
            attr = next((a for a, p in (("vegan", "vegan"), ("vegetarian", r"vegetarian|veg\b"), ("gluten_free", "gluten"), ("spice", r"spic|hot|mild"), ("calories", "calor")) if re.search(p, t)), None)
            if attr:
                return {"kind": "tool", "intent": "attr", "tool": "get_dish_details", "args": {"dish_name": m[0]}, "attr": attr}
        if prefs or re.search(r"recommend|suggest|something|what can i|i want|i would like|show me|which dishes|what dishes|what do you have|what is on the|any dish|good", t):
            listing = bool(re.search(r"which dishes|what dishes|what do you have|list|all", t))
            prefs.setdefault("limit", 6 if listing else 3)
            return {"kind": "tool", "intent": "recommend", "tool": "recommend_dishes", "args": {"preferences": prefs}, "listing": listing}
        if m:
            return {"kind": "tool", "intent": "details", "tool": "get_dish_details", "args": {"dish_name": m[0]}}
        if re.search(r"chef|philosoph|story|restaurant|hotel|about|policy|hours|reservation|open", t):
            return {"kind": "tool", "intent": "knowledge", "tool": "search_knowledge", "args": {"query": t}}
        return {"kind": "tool", "intent": "search", "tool": "search_menu", "args": {"query": t}}

    @staticmethod
    def _prefs(t: str) -> dict:
        p: dict = {}
        if re.search(r"\bvegan\b", t):
            p["vegan"] = True
        elif re.search(r"vegetarian|\bveg\b|veggie", t) and not re.search(r"non vegetarian|non veg", t):
            p["vegetarian"] = True
        if re.search(r"gluten free", t):
            p["gluten_free"] = True
        if re.search(r"not too spicy|not very spicy|not spicy|less spicy|low spice|not hot|mild or", t):
            p["max_spice_level"] = "mild"
        elif re.search(r"\bmild\b", t):
            p["spice_level"] = "mild"
        elif re.search(r"medium spic|medium", t):
            p["spice_level"] = "medium"
        elif re.search(r"\bspicy\b|\bhot\b|high spice", t):
            p["min_spice_level"] = "medium"
        if re.search(r"lightest|light\b|low calorie|healthy|healthier", t):
            p["lightest"] = True
        if "dessert" in t or "sweet" in t:
            p["category"] = "dessert"
        elif re.search(r"starter|appetizer|appetiser", t):
            p["category"] = "starter"
        elif "south indian" in t or "breakfast" in t or "tiffin" in t:
            p["category"] = "breakfast"
        elif re.search(r"main course|\bmains?\b", t):
            p["category"] = "main course"
        elif re.search(r"beverage|drink|juice", t):
            p["category"] = "beverage"
        if "north indian" in t:
            p["cuisine"] = "north indian"
        if re.search(r"chef special|chefs special|chefs", t):
            p["chef_special"] = True
        return p

    # ------------------------------------------------------------- composing
    def _compose(self, plan: dict, results_or_r, text: str) -> str:
        if isinstance(results_or_r, list):
            results = results_or_r
            r = results[0] if results else {}
        else:
            results = [results_or_r]
            r = results_or_r

        intent = plan["intent"]
        for res in results:
            if res.get("error") in {"ambiguous_or_unsure", "dish_not_found", "need_two_known_dishes"}:
                cands = res.get("candidates") or res.get("menu") or []
                if res["error"] == "ambiguous_or_unsure":
                    return f"Which one did you mean - {_join(cands[:3], 'or')}?"
                return f"I couldn't find that on our menu. Our dishes include {_join(cands[:7])}."
            if res.get("error") == "allergen_not_tracked":
                return UNKNOWN_INFO["en"]
        notice = r.get("safety_notice")

        # Multi-part intent: specific dish price + category recommendation
        if intent == "dish_price_and_recommend":
            r0 = results[0] if len(results) > 0 else {}
            r1 = results[1] if len(results) > 1 else {}
            d = r0.get("dish")
            if not d:
                cands = r0.get("candidates") or r0.get("menu") or []
                return f"Which dish did you mean - {_join(cands[:3], 'or')}?"
            p = d.get("price")
            price_str = f"{p:g} rupees" if isinstance(p, (int, float)) else "not listed"
            price_part = f"{d['name']} is priced at {price_str}."
            recs = [x["dish"] for x in r1.get("recommendations", [])]
            rec_cat = plan.get("rec_category", "main course")
            if recs:
                rec_names = _join([x["name"] for x in recs[:3]])
                rec_part = f"For {rec_cat}, I recommend {rec_names}."
            else:
                rec_part = f"For {rec_cat}, please check our chef's specials."
            return f"{price_part} {rec_part} Would you like to hear more about any of these dishes?"

        # Multi-part intent: category dishes + prices + recommendation
        if intent == "category_prices_and_recommend":
            r0 = results[0] if len(results) > 0 else {}
            r1 = results[1] if len(results) > 1 else {}
            avail = r0.get("available", [])
            cat = plan.get("category", "starter")
            if not avail:
                return f"We currently have no available dishes listed under {cat} in our menu database."
            items = []
            for d in avail:
                p = d.get("price")
                if isinstance(p, (int, float)):
                    items.append(f"{d['name']} at {p:g} rupees")
                else:
                    items.append(d["name"])
            list_str = _join(items)
            recs = [x["dish"] for x in r1.get("recommendations", [])]
            if recs:
                rec_name = recs[0]["name"]
                rec_sp = SPICE_WORDS.get(recs[0].get("spice_level", "mild"), "mild")
                rec_str = f"Our chef particularly recommends the {rec_name}, which is {rec_sp}."
            else:
                rec_str = f"I would recommend trying the {avail[0]['name']}."
            return f"Our {cat} selection includes {list_str}. {rec_str} Would you like to hear the ingredients or more details on any of these?"

        # Multi-part intent: cheapest dish + recommendation
        if intent == "cheapest_and_recommend":
            r0 = results[0] if len(results) > 0 else {}
            r1 = results[1] if len(results) > 1 else {}
            avail = r0.get("available", [])
            cat = plan.get("category", "starter")
            priced = [d for d in avail if isinstance(d.get("price"), (int, float)) and d.get("price") is not None]
            if not priced:
                return f"I don't have listed prices for {cat}s in our current menu data. Please check with our restaurant team."
            cheapest = min(priced, key=lambda d: d["price"])
            lead = f"The cheapest {cat} on our menu is {cheapest['name']} at {cheapest['price']:g} rupees."
            recs = [x["dish"] for x in r1.get("recommendations", [])]
            if recs:
                rec_names = _join([d["name"] for d in recs[:2]])
                rec_text = f"For recommendations, I suggest {rec_names}."
            else:
                rec_text = f"I also recommend the {cheapest['name']} for a great value."
            return f"{lead} {rec_text} Would you like to know more about its ingredients?"

        # Category prices
        if intent == "category_prices":
            r0 = results[0] if len(results) > 0 else {}
            avail = r0.get("available", [])
            cat = plan.get("category", "starter")
            if not avail:
                return f"We currently have no available dishes listed under {cat} in our menu database."
            items = []
            for d in avail:
                p = d.get("price")
                if isinstance(p, (int, float)):
                    items.append(f"{d['name']} at {p:g} rupees")
                else:
                    items.append(d["name"])
            return f"The prices for our {cat}s are: {_join(items)}."

        # Multiple prices
        if intent == "multiple_prices":
            lines = []
            for r_item in results:
                d = r_item.get("dish")
                if d:
                    p = d.get("price")
                    if isinstance(p, (int, float)):
                        lines.append(f"{d['name']} is {p:g} rupees")
                    else:
                        lines.append(f"{d['name']} (price unlisted)")
            return f"{_join(lines)}. Would you like recommendations as well?"

        if intent in {"recommend", "exclude"}:
            recs = [x["dish"] for x in r.get("recommendations", [])]
            crit = r.get("criteria", {})
            if not recs:
                closest = r.get("closest") or []
                if closest:
                    names = _join([c["name"] for c in closest[:3]])
                    return f"Nothing matches every preference, but the closest options are {names}. Shall I tell you more about them?"
                return "I'm sorry, nothing on the menu matches those requirements."
            names = _join([d["name"] for d in recs])
            if crit.get("lightest"):
                top = recs[0]["calories_kcal_approx"]
                ties = [d["name"] for d in recs if d["calories_kcal_approx"] == top]
                cat = (crit.get("category") or "dish").lower()
                return f"The lightest {cat} is {_join(ties)}, at about {top} calories. Would you like to hear the ingredients?"
            if intent == "exclude":
                lead = "Without that allergen listed, I would suggest"
            elif crit.get("category") == "dessert":
                lead = "For dessert, I'd recommend"
            elif crit.get("category") == "breakfast":
                lead = "For breakfast, I'd recommend"
            elif crit.get("category") == "starter":
                lead = "For starters, I'd recommend"
            elif crit.get("category") == "beverage":
                lead = "For beverages, I'd recommend"
            elif plan.get("listing"):
                lead = "According to our menu, the dishes that match are"
            else:
                lead = "I'd recommend"
            detail_parts = []
            for d in recs[:2]:
                sp = SPICE_WORDS.get(d.get("spice_level", "mild"), "mildly spiced")
                cal = f" at about {d['calories_kcal_approx']} calories" if d.get("calories_kcal_approx") is not None else ""
                detail_parts.append(f"{d['name']} is {sp}{cal}.")
            detail = " ".join(detail_parts)
            tail = " Would you like to hear its ingredients?" if len(recs) == 1 else " Would you like to hear the ingredients of any of these?"
            return f"{lead} {names}. {detail}{tail}" + (f" {notice}" if notice else "")

        if intent == "specials":
            items = r.get("specials", [])
            if not items:
                return "There are no specials set at the moment. I'd be happy to suggest a chef's favourite instead."
            first = items[0]
            line = f"{first['title']} is {first['dish']['name']}." if first.get("dish") else f"{first['title']}: {first.get('note') or ''}"
            others = [i["dish"]["name"] for i in items[1:3] if i.get("dish")]
            more = f" We also feature {_join(others)}." if others else ""
            return f"{line}{more} Would you like to know what is in it?"

        if intent == "ingredients":
            ings = r.get("ingredients") or []
            if not ings:
                return f"I don't have listed ingredients for {r['dish']} in the current menu data. Please confirm with our restaurant team."
            shown = ings if len(ings) <= 9 else ings[:8]
            more = f" and {len(ings) - len(shown)} more spices and seasonings" if len(ings) > len(shown) else ""
            allergens = r.get("listed_allergens")
            al = f" It lists {_join(allergens).lower()} as allergens." if isinstance(allergens, list) else " No allergens are listed for it."
            return f"{r['dish']} contains {_join(shown)}{more}.{al} Would you like a similar dish?"

        if intent == "allergen":
            if plan.get("multi"):
                cd = r.get("contain_declared", [])
                asked = r.get("asked_about", "that allergen").replace("_", " ")
                if cd:
                    parts = []
                    for c in cd:
                        ing = f" (listed ingredient: {_join(c['related_ingredients']).lower()})" if c.get("related_ingredients") else ""
                        parts.append(f"{c['dish']} lists {_join(c['declared']).lower()}{ing}")
                    extra = ""
                    if r.get("ingredient_mention_only"):
                        extra = f" {_join([c['dish'] for c in r['ingredient_mention_only']])} also list a related ingredient."
                    return f"According to our menu information, {_join(parts)}.{extra} No other dish declares it. {notice}"
                return f"According to our menu information, none of our dishes declare {asked}. {notice}"
            dish = r.get("dish")
            if "asked_about" in r:
                asked = r["asked_about"].replace("_", " ")
                if r["declared_contains"]:
                    hits = r["related_ingredients_listed"]
                    ing = f", and its ingredients include {_join(hits).lower()}" if hits else ""
                    body = f"Yes, {dish} lists {_join(r['matched_allergens']).lower()} as an allergen{ing}."
                elif r["related_ingredients_listed"]:
                    body = f"{dish} does not declare {asked} as an allergen, but its ingredients include {_join(r['related_ingredients_listed']).lower()}."
                else:
                    body = f"{asked.capitalize()} {'are' if asked.endswith('s') else 'is'} not listed as an ingredient or allergen in {dish}."
                return f"{body} {notice}"
            declared = r.get("declared_allergens")
            body = f"{dish} lists {_join(declared).lower()} as allergens." if isinstance(declared, list) else f"No allergens are listed for {dish}."
            return f"{body} {notice}"

        if intent == "compare":
            ds, h = r["dishes"], r["highlights"]
            lines = [f"{d['name']} is {SPICE_WORDS[d['spice_level']]} at about {d['calories_kcal_approx']} calories, and "
                     f"{'vegetarian' if d['vegetarian'] == 'yes' else 'non-vegetarian' if d['vegetarian'] == 'no' else 'of unconfirmed dietary type'}." for d in ds]
            low = normalize(text)
            spice_line = (f"They are equally spiced." if h["all_equally_spiced"] else
                          f"{_join(h['mildest'])} {'is' if len(h['mildest']) == 1 else 'are'} the milder choice.")
            light_line = (f"They have the same calories." if h["all_equal_calories"] else
                          f"{_join(h['lightest'])} {'is' if len(h['lightest']) == 1 else 'are'} the lighter option.")
            if re.search(r"spic|mild", low):
                focus = " " + spice_line
            elif re.search(r"light|calor|healthier|heav|richer", low):
                focus = " " + light_line
            else:
                focus = f" {spice_line} {light_line}"
            return " ".join(lines) + focus + " Shall I tell you more about any of them?"

        if intent in {"details", "attr", "price", "unknown_attr"}:
            d = r.get("dish")
            if not d:
                cands = r.get("candidates") or r.get("menu") or []
                return f"I couldn't find that on our menu. Our dishes include {_join(cands[:7])}."
            if intent == "price":
                if isinstance(d.get("price"), (int, float)):
                    return f"{d['name']} is priced at {d['price']:g} rupees."
                return "I don't have prices in the current menu data. Please confirm with our restaurant team."
            if intent == "unknown_attr":
                return f"I don't have information about {plan['attr']} for {d['name']} in the current menu data. Please confirm with our restaurant team."
            if intent == "attr":
                attr = plan["attr"]
                if attr in {"vegan", "vegetarian", "gluten_free", "halal", "jain"}:
                    val = d[attr]
                    label = attr.replace("_", " ")
                    if val == "yes":
                        return f"Yes, {d['name']} is {label} according to our menu information. Would you like to hear what else is in it?"
                    if val == "no":
                        return f"No, {d['name']} is not {label}. Would you like me to suggest {label} options?"
                    return f"I don't have {label} information for {d['name']} in the current menu data. Please confirm with our restaurant team."
                if attr == "spice":
                    return f"{d['name']} is {SPICE_WORDS[d['spice_level']]}. Would you like something milder or spicier?"
                if attr == "calories":
                    return f"{d['name']} is approximately {d['calories_kcal_approx']} calories."
            veg = {"yes": "vegetarian", "no": "non-vegetarian"}.get(d["vegetarian"], "")
            chef = " It is one of our chef's specials." if d["chef_special"] else ""
            return f"{d['name']} is a {veg + ' ' if veg else ''}{(d['category'] or 'dish').lower()} dish, {SPICE_WORDS[d['spice_level']]}, at about {d['calories_kcal_approx']} calories. {d['description']}{chef} Would you like the ingredients?"

        if intent == "dietary_list":
            ds = r.get("dishes", [])
            return (f"{_join([d['name'] for d in ds])} are marked on our menu." if ds else
                    f"I'm sorry, none of our dishes are marked {r['preference']} in the current menu data. Please confirm with our restaurant team.")

        if intent == "knowledge":
            ps = r.get("passages", [])
            return ps[0]["text"] if ps else UNKNOWN_INFO["en"]

        matches = r.get("matches", [])
        if matches:
            return f"I found {_join([d['name'] for d in matches[:3]])}. Would you like details on any of them?"
        return "I'd be glad to help with our menu. You can ask about ingredients, allergens, vegetarian or mild dishes, or today's specials."
