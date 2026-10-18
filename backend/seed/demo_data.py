"""Fictional demo data for AURELIA GRAND HOTEL / Saffron Terrace.

Replace this file (or load your own via the admin API) to onboard a real hotel. Nothing in the UI or the
AI layer hardcodes any of it - everything is read from PostgreSQL.
"""

HOTEL = {
    "slug": "aurelia-grand",
    "name": "Aurelia Grand Hotel",
    "tagline": "A premium modern Indian dining experience",
    "description": "Aurelia Grand Hotel is a fictional luxury hotel used for the AURA concierge demo.",
    "city": "Chennai",
    "default_language": "en",
    "supported_languages": ["en", "ta", "hi"],
    "assistant_name": "AURA",
}

RESTAURANT = {
    "slug": "saffron-terrace",
    "name": "Saffron Terrace",
    "positioning": "A premium modern Indian dining experience blending traditional Indian cuisine with contemporary presentation.",
    "description": (
        "Saffron Terrace is the signature dining restaurant of Aurelia Grand Hotel, offering contemporary Indian "
        "cuisine inspired by regional recipes, traditional cooking techniques, and modern presentation."
    ),
    "cuisine_style": "Contemporary Indian",
    "currency": "INR",
}

CATEGORIES = [
    {"slug": "starters", "name": "Starters", "sort_order": 1, "name_translations": {"ta": "ஸ்டார்டர்கள்", "hi": "स्टार्टर्स"}},
    {"slug": "main-course", "name": "Main Course", "sort_order": 2, "name_translations": {"ta": "முதன்மை உணவு", "hi": "मुख्य व्यंजन"}},
    {"slug": "south-indian", "name": "South Indian", "sort_order": 3, "name_translations": {"ta": "தென்னிந்திய உணவு", "hi": "दक्षिण भारतीय"}},
    {"slug": "desserts", "name": "Desserts", "sort_order": 4, "name_translations": {"ta": "இனிப்புகள்", "hi": "मिठाई"}},
]

DIETARY_TAGS = [
    ("vegetarian", "Vegetarian"), ("vegan", "Vegan"), ("gluten_free", "Gluten free"),
    ("halal", "Halal"), ("jain", "Jain"),
]

ALLERGENS = [
    ("dairy", "Dairy"), ("gluten", "Gluten"), ("tree_nuts", "Tree nuts"), ("peanuts", "Peanuts"),
    ("coconut", "Coconut"), ("soy", "Soy"), ("eggs", "Eggs"), ("fish", "Fish"),
    ("shellfish", "Shellfish"), ("sesame", "Sesame"),
]

BASIS = "listed ingredients"

DISHES = [
    {
        "slug": "royal-chicken-biryani", "category": "main-course", "name": "Royal Chicken Biryani",
        "name_translations": {"ta": "ராயல் சிக்கன் பிரியாணி", "hi": "रॉयल चिकन बिरयानी"},
        "aliases": ["chicken biryani", "hyderabadi biryani", "hyderabadi chicken biryani", "சிக்கன் பிரியாணி", "चिकन बिरयानी"],
        "cuisine": "Indian / Hyderabadi",
        "description": "Fragrant basmati rice layered with marinated chicken, caramelized onions, saffron, mint, coriander, and aromatic biryani spices.",
        "preparation_notes": "Marinated chicken and basmati rice are layered with caramelized onions, saffron, mint, coriander and biryani spices.",
        "ingredients": ["Basmati rice", "Chicken", "Yogurt", "Fried onion", "Mint", "Coriander", "Saffron", "Ginger", "Garlic",
                        "Green chili", "Cinnamon", "Cardamom", "Cloves", "Bay leaf", "Cumin", "Garam masala", "Salt", "Cooking oil"],
        "dietary": {"vegetarian": "no", "vegan": "no", "gluten_free": "yes"},
        "spice_level": "medium", "calories_kcal": 680, "allergens": ["dairy"], "chef_special": True, "available": True, "sort_order": 1,
    },
    {
        "slug": "paneer-tikka", "category": "starters", "name": "Paneer Tikka",
        "name_translations": {"ta": "பனீர் டிக்கா", "hi": "पनीर टिक्का"},
        "aliases": ["tikka", "paneer tikka starter", "பன்னீர் டிக்கா"],
        "cuisine": "North Indian",
        "description": "Char-grilled cubes of Indian cottage cheese marinated in yogurt, ginger, garlic, spices, and bell peppers.",
        "preparation_notes": "Cubes of paneer are marinated in yogurt, ginger, garlic and spices, then char-grilled with bell peppers.",
        "ingredients": ["Paneer", "Yogurt", "Bell pepper", "Onion", "Ginger", "Garlic", "Kashmiri chili", "Turmeric", "Cumin",
                        "Coriander powder", "Garam masala", "Lemon juice", "Salt", "Cooking oil"],
        "dietary": {"vegetarian": "yes", "vegan": "no", "gluten_free": "yes"},
        "spice_level": "mild", "calories_kcal": 390, "allergens": ["dairy"], "chef_special": False, "available": True, "sort_order": 2,
    },
    {
        "slug": "malai-kofta", "category": "main-course", "name": "Malai Kofta",
        "name_translations": {"ta": "மலாய் கோஃப்தா", "hi": "मलाई कोफ्ता"},
        "aliases": ["kofta", "மலாய் கோப்தா"],
        "cuisine": "North Indian",
        "description": "Soft paneer and vegetable dumplings served in a rich, mildly spiced tomato and cream gravy.",
        "preparation_notes": "Soft paneer and vegetable dumplings are served in a rich, mildly spiced tomato and cream gravy.",
        "ingredients": ["Paneer", "Potato", "Corn flour", "Tomato", "Cream", "Cashew", "Onion", "Ginger", "Garlic", "Cardamom",
                        "Cinnamon", "Garam masala", "Kasuri methi", "Salt", "Cooking oil"],
        "dietary": {"vegetarian": "yes", "vegan": "no", "gluten_free": "yes"},
        "spice_level": "mild", "calories_kcal": 520, "allergens": ["dairy", "tree_nuts"], "chef_special": True, "available": True, "sort_order": 3,
    },
    {
        "slug": "masala-dosa", "category": "south-indian", "name": "Masala Dosa",
        "name_translations": {"ta": "மசாலா தோசை", "hi": "मसाला डोसा"},
        "aliases": ["dosa", "dosai", "masala dosai", "தோசை", "डोसा"],
        "cuisine": "South Indian",
        "description": "Crisp fermented rice and lentil crepe served with spiced potato filling, coconut chutney, and sambar.",
        "preparation_notes": "A crisp fermented rice and lentil crepe is served with spiced potato filling, coconut chutney and sambar.",
        "ingredients": ["Rice", "Urad dal", "Potato", "Onion", "Green chili", "Mustard seeds", "Curry leaves", "Turmeric", "Coconut",
                        "Toor dal", "Tamarind", "Sambar spices", "Salt", "Cooking oil"],
        "dietary": {"vegetarian": "yes", "vegan": "yes", "gluten_free": "yes"},
        "spice_level": "medium", "calories_kcal": 420, "allergens": ["coconut"], "chef_special": False, "available": True, "sort_order": 4,
    },
    {
        "slug": "butter-chicken", "category": "main-course", "name": "Butter Chicken",
        "name_translations": {"ta": "பட்டர் சிக்கன்", "hi": "बटर चिकन"},
        "aliases": ["murgh makhani", "chicken makhani", "makhani chicken"],
        "cuisine": "North Indian",
        "description": "Tender chicken cooked in a creamy tomato-based makhani gravy enriched with butter and aromatic Indian spices.",
        "preparation_notes": "Tender chicken is cooked in a creamy tomato-based makhani gravy enriched with butter and spices.",
        "ingredients": ["Chicken", "Tomato", "Butter", "Cream", "Yogurt", "Ginger", "Garlic", "Kashmiri chili", "Garam masala",
                        "Cumin", "Coriander", "Fenugreek leaves", "Salt"],
        "dietary": {"vegetarian": "no", "vegan": "no", "gluten_free": "yes"},
        "spice_level": "mild", "calories_kcal": 610, "allergens": ["dairy"], "chef_special": True, "available": True, "sort_order": 5,
    },
    {
        "slug": "vegetable-biryani", "category": "main-course", "name": "Vegetable Biryani",
        "name_translations": {"ta": "வெஜிடபிள் பிரியாணி", "hi": "वेजिटेबल बिरयानी"},
        "aliases": ["veg biryani", "veggie biryani", "vegetarian biryani", "வெஜ் பிரியாணி", "वेज बिरयानी"],
        "cuisine": "Indian",
        "description": "Aromatic basmati rice cooked with seasonal vegetables, saffron, mint, coriander, and traditional biryani spices.",
        "preparation_notes": "Basmati rice is cooked with seasonal vegetables, saffron, mint, coriander and biryani spices.",
        "ingredients": ["Basmati rice", "Carrot", "Green peas", "Beans", "Potato", "Cauliflower", "Onion", "Mint", "Coriander", "Saffron",
                        "Ginger", "Garlic", "Cinnamon", "Cardamom", "Cloves", "Cumin", "Garam masala", "Salt", "Cooking oil"],
        "dietary": {"vegetarian": "yes", "vegan": "yes", "gluten_free": "yes"},
        "spice_level": "medium", "calories_kcal": 520, "allergens": [], "chef_special": False, "available": True, "sort_order": 6,
    },
    {
        "slug": "gulab-jamun", "category": "desserts", "name": "Gulab Jamun",
        "name_translations": {"ta": "குலாப் ஜாமூன்", "hi": "गुलाब जामुन"},
        "aliases": ["gulab jamoon", "jamun", "குலாப் ஜாமுன்"],
        "cuisine": "Indian",
        "description": "Soft golden milk-based dumplings soaked in warm cardamom-infused sugar syrup and served with a delicate garnish.",
        "preparation_notes": "Soft golden milk-based dumplings are soaked in warm cardamom-infused sugar syrup.",
        "ingredients": ["Milk solids", "Flour", "Sugar", "Cardamom", "Rose water", "Cooking oil"],
        "dietary": {"vegetarian": "yes", "vegan": "no", "gluten_free": "no"},
        "spice_level": "none", "calories_kcal": 280, "allergens": ["dairy", "gluten"], "chef_special": False, "available": True, "sort_order": 7,
    },
]

# dish slug -> (type, title, description)
SPECIALS = [
    ("royal-chicken-biryani", "today", "Today's Special", "Our Royal Chicken Biryani is today's special."),
    ("butter-chicken", "chef_recommendation", "Chef's Recommendation", "A guest favourite recommended by our chef."),
    ("malai-kofta", "weekend", "Weekend Special", "A rich vegetarian main for the weekend."),
    ("gulab-jamun", "seasonal", "Seasonal Sweet", "A warm, cardamom-scented dessert to end the meal."),
]

KNOWLEDGE = [
    ("restaurant", "About Saffron Terrace", RESTAURANT["description"] + " " + RESTAURANT["positioning"]),
    ("philosophy", "Our cooking philosophy",
     "The kitchen draws on regional Indian recipes and traditional cooking techniques, then presents each dish in a modern, "
     "contemporary style. Dishes are described using the ingredients listed on the menu."),
    ("faq", "Allergen and dietary information",
     "Dietary and allergen information on our menu is based on the ingredients we list for each dish. Cross-contact may occur "
     "during food preparation. Guests with serious allergies should always confirm with the restaurant team before ordering."),
    ("dish_story", "Royal Chicken Biryani",
     "Royal Chicken Biryani is our Hyderabadi-style biryani and one of the chef's specials. It layers marinated chicken with "
     "fragrant basmati rice, caramelized onions and saffron."),
    ("faq", "Chef specials",
     "Dishes marked as Chef Special on the menu are the kitchen's featured creations. Today's special changes and is shown in the specials list."),
]
