
import sqlite3
from pathlib import Path

# Create the database beside this Python file
DB_PATH = Path(__file__).parent / "aura_restaurant.db"

# Connect to the database (creates the file if it doesn't exist)
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Create the menu table
cursor.execute("""
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
)
""")

# Sample menu: 15 dishes
dishes = [
    ("Idli", "Breakfast", 40),
    ("Medu Vada", "Breakfast", 50),
    ("Pongal", "Breakfast", 60),
    ("Masala Dosa", "Breakfast", 90),
    ("Ghee Roast Dosa", "Breakfast", 110),
    ("Paneer Tikka", "Starter", 180),
    ("Gobi Manchurian", "Starter", 140),
    ("Veg Spring Rolls", "Starter", 130),
    ("Paneer Butter Masala", "Main Course", 220),
    ("Veg Fried Rice", "Main Course", 160),
    ("Veg Biryani", "Main Course", 180),
    ("Butter Naan", "Main Course", 40),
    ("Gulab Jamun", "Dessert", 60),
    ("Vanilla Ice Cream", "Dessert", 70),
    ("Fresh Lime Juice", "Beverage", 50),
]

# Insert dishes only if the table is empty
cursor.execute("SELECT COUNT(*) FROM menu_items")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO menu_items (dish_name, category, price) VALUES (?, ?, ?)",
        dishes,
    )

connection.commit()
connection.close()

print(f"Database created successfully: {DB_PATH}")
print("15 sample menu items are ready!")
