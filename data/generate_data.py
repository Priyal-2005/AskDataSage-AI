"""
AskDataSage AI — E-Commerce Database Generator
Generates a realistic SQLite database with users, products, orders, and order_items.
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")

NUM_USERS = 500
NUM_PRODUCTS = 200
NUM_ORDERS = 5000
AVG_ITEMS_PER_ORDER = 2  # yields ~10,000 order_items

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Books",
    "Home & Kitchen",
    "Sports",
    "Beauty",
    "Toys",
]

ORDER_STATUSES = ["completed", "pending", "cancelled", "returned"]
STATUS_WEIGHTS = [0.65, 0.15, 0.12, 0.08]  # realistic distribution

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Product catalog (realistic names per category)
# ---------------------------------------------------------------------------
PRODUCT_TEMPLATES = {
    "Electronics": [
        "Wireless Bluetooth Headphones", "USB-C Fast Charger", "Portable Power Bank 20000mAh",
        "Smart Watch Pro", "Noise Cancelling Earbuds", "4K Webcam HD", "Mechanical Keyboard RGB",
        "Wireless Gaming Mouse", "Portable SSD 1TB", "Smart Home Speaker",
        "Tablet Stand Adjustable", "HDMI Cable 6ft", "Ring Light 10-inch",
        "Wireless Charging Pad", "Laptop Cooling Pad", "Digital Thermometer",
        "Smart Plug WiFi", "Bluetooth FM Transmitter", "USB Hub 7-Port",
        "Action Camera 4K", "Drone Mini Pro", "VR Headset Lite",
        "E-Reader 8-inch", "Fitness Tracker Band", "Portable Projector Mini",
        "Smart Door Lock", "Wireless Presenter Remote", "Car Dash Camera",
        "Surge Protector 8-Outlet", "LED Desk Lamp Smart",
    ],
    "Clothing": [
        "Classic Fit Cotton T-Shirt", "Slim Fit Denim Jeans", "Casual Hoodie Pullover",
        "Athletic Running Shorts", "Formal Dress Shirt", "Winter Puffer Jacket",
        "Leather Belt Premium", "Cotton Crew Socks 6-Pack", "UV Protection Sunglasses",
        "Canvas Sneakers Low-Top", "Wool Blend Sweater", "Rain Jacket Waterproof",
        "Cargo Pants Relaxed Fit", "Silk Neck Tie", "Baseball Cap Adjustable",
        "Compression Leggings", "Flannel Pajama Set", "Linen Summer Shorts",
        "Polo Shirt Classic", "Windbreaker Jacket Lightweight",
        "Beanie Knit Cap", "Scarf Cashmere Blend", "Swim Trunks Board Shorts",
        "Ankle Boots Leather", "Flip Flops Comfort", "Graphic Print Tee",
        "Jogger Pants Tapered", "Trench Coat Long", "Tank Top Breathable",
        "Down Vest Packable",
    ],
    "Books": [
        "Python Programming Masterclass", "Data Science Handbook", "Machine Learning A-Z",
        "The Art of Clean Code", "Deep Learning with PyTorch", "SQL for Data Analysis",
        "Algorithms Unlocked", "System Design Interview Guide", "Web Development Bootcamp",
        "Cloud Computing Essentials", "Cybersecurity Fundamentals", "AI Ethics & Society",
        "Statistics for Everyone", "Product Management 101", "Startup Playbook",
        "Digital Marketing Strategy", "Leadership in Tech", "UX Design Principles",
        "Blockchain Explained", "Quantum Computing Intro",
        "Science Fiction Anthology", "Mystery Thriller Collection", "Historical Fiction Epic",
        "Self-Help Mindset Book", "Cookbook Mediterranean", "Travel Guide Europe",
        "Biography Tech Visionary", "Children's Adventure Story", "Graphic Novel Vol. 1",
        "Poetry Collection Modern",
    ],
    "Home & Kitchen": [
        "Stainless Steel Cookware Set", "Non-Stick Frying Pan 12-inch", "Knife Block Set 15-Piece",
        "Instant Pot Pressure Cooker", "Coffee Maker Drip 12-Cup", "Blender High-Speed",
        "Toaster 4-Slice Wide Slot", "Cutting Board Bamboo Set", "Food Storage Container Set",
        "Kitchen Scale Digital", "Spice Rack Organizer 20-Jar", "Silicone Baking Mat Set",
        "Cast Iron Skillet 10-inch", "Electric Kettle 1.7L", "Hand Mixer 5-Speed",
        "Dish Drying Rack Stainless", "Vacuum Insulated Tumbler", "Ice Cube Tray Silicone",
        "Paper Towel Holder Stand", "Trash Can Motion Sensor",
        "Scented Candle Set 3-Pack", "Throw Blanket Fleece", "Decorative Pillows Set",
        "Wall Clock Modern", "Photo Frame Collage", "Indoor Plant Pot Ceramic",
        "LED String Lights 33ft", "Bath Towel Set Cotton", "Shower Curtain Waterproof",
        "Laundry Basket Foldable",
    ],
    "Sports": [
        "Yoga Mat Non-Slip 6mm", "Resistance Bands Set 5-Pack", "Adjustable Dumbbells 25lb",
        "Jump Rope Speed Cable", "Foam Roller High-Density", "Water Bottle Insulated 32oz",
        "Running Armband Phone Holder", "Gym Bag Duffel Large", "Pull-Up Bar Doorway",
        "Exercise Ball 65cm", "Kettlebell Cast Iron 20lb", "Boxing Gloves 12oz",
        "Tennis Racket Pro", "Basketball Indoor/Outdoor", "Soccer Ball Official Size",
        "Cycling Gloves Padded", "Hiking Backpack 40L", "Camping Tent 2-Person",
        "Fishing Rod Telescopic", "Skateboard Complete 31-inch",
        "Golf Balls 12-Pack", "Swimming Goggles Anti-Fog", "Badminton Set Complete",
        "Table Tennis Paddle Set", "Ab Roller Wheel", "Wrist Wraps Lifting",
        "Compression Arm Sleeves", "Sport Headband Sweat-Wicking",
        "Ankle Weights 5lb Pair", "Lacrosse Ball Massage",
    ],
    "Beauty": [
        "Moisturizing Face Cream SPF30", "Vitamin C Serum 30ml", "Gentle Foam Cleanser",
        "Retinol Night Cream", "Hyaluronic Acid Serum", "Sunscreen Lotion SPF50",
        "Makeup Brush Set 12-Piece", "Liquid Foundation Medium", "Mascara Volumizing Waterproof",
        "Lipstick Matte Collection", "Eyeshadow Palette 18-Color", "Setting Spray Long-Lasting",
        "Micellar Cleansing Water", "Sheet Mask Variety 10-Pack", "Hair Serum Anti-Frizz",
        "Dry Shampoo Volume Boost", "Perfume Eau de Parfum 50ml", "Nail Polish Set 6-Pack",
        "Electric Toothbrush Sonic", "Hair Dryer Ionic 1875W",
        "Curling Iron 1-inch Barrel", "Flat Iron Ceramic Plates", "Body Lotion Shea Butter",
        "Hand Cream Intensive Repair", "Lip Balm SPF15 3-Pack", "Eye Cream Anti-Aging",
        "Exfoliating Scrub Gentle", "Toner Balancing Alcohol-Free",
        "Deodorant Natural 3-Pack", "Bath Bomb Gift Set 12-Pack",
    ],
    "Toys": [
        "Building Blocks 500-Piece Set", "Remote Control Car Off-Road", "Board Game Strategy Classic",
        "Puzzle 1000-Piece Landscape", "Action Figure Collectible", "Stuffed Animal Bear Large",
        "Art Supply Kit 150-Piece", "Science Experiment Kit", "Magnetic Tiles 60-Piece",
        "Play Dough 10-Color Pack", "Card Game Family Fun", "RC Drone Beginner",
        "Water Gun Super Soaker", "Nerf Blaster Elite", "Dollhouse Wooden Furnished",
        "Train Set Electric Classic", "Toy Kitchen Playset", "Dinosaur Figure Set 12-Pack",
        "Bubble Machine Automatic", "Kite Large Rainbow",
        "Telescope Kids Starter", "Magic Kit Beginner", "Walkie Talkie Kids 2-Pack",
        "Sandbox Toys Beach Set", "Trampoline Mini Indoor", "Bike Helmet Kids Adjustable",
        "Scooter Foldable Kids", "Robot Programmable STEM",
        "Musical Instrument Set Kids", "Craft Kit DIY Jewelry",
    ],
}

# Price ranges per category (min, max)
PRICE_RANGES = {
    "Electronics": (9.99, 299.99),
    "Clothing": (12.99, 149.99),
    "Books": (8.99, 49.99),
    "Home & Kitchen": (7.99, 199.99),
    "Sports": (9.99, 129.99),
    "Beauty": (6.99, 79.99),
    "Toys": (7.99, 89.99),
}


def create_tables(cursor: sqlite3.Cursor) -> None:
    """Create the database schema."""
    cursor.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            city        TEXT NOT NULL,
            signup_date TEXT NOT NULL  -- ISO 8601 date
        );

        CREATE TABLE products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            category        TEXT NOT NULL,
            price           REAL NOT NULL,
            stock_quantity  INTEGER NOT NULL
        );

        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            order_date   TEXT NOT NULL,  -- ISO 8601 datetime
            status       TEXT NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL,
            product_id  INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            unit_price  REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE INDEX idx_orders_user_id    ON orders(user_id);
        CREATE INDEX idx_orders_order_date ON orders(order_date);
        CREATE INDEX idx_orders_status     ON orders(status);
        CREATE INDEX idx_order_items_order  ON order_items(order_id);
        CREATE INDEX idx_order_items_product ON order_items(product_id);
        CREATE INDEX idx_products_category ON products(category);
    """)


def generate_users(cursor: sqlite3.Cursor) -> None:
    """Insert realistic user records."""
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "Indianapolis", "San Francisco", "Seattle", "Denver", "Washington",
        "Nashville", "Oklahoma City", "Portland", "Las Vegas", "Memphis",
        "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson",
    ]

    users = []
    emails_seen = set()
    for i in range(NUM_USERS):
        name = fake.name()
        # Generate unique email
        base_email = f"{name.lower().replace(' ', '.')}{random.randint(1, 999)}@{fake.free_email_domain()}"
        while base_email in emails_seen:
            base_email = f"{name.lower().replace(' ', '.')}{random.randint(1, 9999)}@{fake.free_email_domain()}"
        emails_seen.add(base_email)

        city = random.choice(cities)
        # Signup dates spread over last 3 years
        days_ago = random.randint(0, 1095)
        signup_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        users.append((name, base_email, city, signup_date))

    cursor.executemany(
        "INSERT INTO users (name, email, city, signup_date) VALUES (?, ?, ?, ?)",
        users,
    )
    print(f"  ✓ Inserted {len(users)} users")


def generate_products(cursor: sqlite3.Cursor) -> list[tuple]:
    """Insert product records and return (id, category, price) for order generation."""
    products = []
    product_id = 1
    products_per_category = NUM_PRODUCTS // len(CATEGORIES)
    extra = NUM_PRODUCTS % len(CATEGORIES)

    for cat_idx, category in enumerate(CATEGORIES):
        count = products_per_category + (1 if cat_idx < extra else 0)
        templates = PRODUCT_TEMPLATES[category]
        price_min, price_max = PRICE_RANGES[category]

        for i in range(count):
            name = templates[i % len(templates)]
            # Add variant suffix if we cycle through templates
            if i >= len(templates):
                name = f"{name} v{i // len(templates) + 1}"
            price = round(random.uniform(price_min, price_max), 2)
            stock = random.randint(10, 500)
            products.append((name, category, price, stock))
            product_id += 1

    cursor.executemany(
        "INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
        products,
    )
    print(f"  ✓ Inserted {len(products)} products")

    # Return product info for order generation
    cursor.execute("SELECT id, category, price FROM products")
    return cursor.fetchall()


def generate_orders_and_items(
    cursor: sqlite3.Cursor, product_info: list[tuple]
) -> None:
    """Generate orders with realistic items, quantities, and totals."""
    now = datetime.now()
    orders = []
    all_items = []

    for order_idx in range(NUM_ORDERS):
        user_id = random.randint(1, NUM_USERS)
        # Order dates spread over last 2 years, skewed toward recent
        days_ago = int(random.betavariate(2, 5) * 730)
        order_date = (now - timedelta(days=days_ago, hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59)))
        order_date_str = order_date.strftime("%Y-%m-%d %H:%M:%S")

        status = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        # Generate items for this order
        num_items = max(1, int(random.gauss(AVG_ITEMS_PER_ORDER, 1)))
        num_items = min(num_items, 6)  # cap at 6 items per order

        selected_products = random.sample(
            product_info, min(num_items, len(product_info))
        )

        order_total = 0.0
        order_items = []
        for prod_id, _, prod_price in selected_products:
            quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3], k=1)[0]
            # Slight price variation (sales, discounts)
            unit_price = round(prod_price * random.uniform(0.85, 1.0), 2)
            line_total = round(unit_price * quantity, 2)
            order_total += line_total
            order_items.append((prod_id, quantity, unit_price))

        order_total = round(order_total, 2)
        orders.append((user_id, order_date_str, status, order_total))
        all_items.append(order_items)

    # Insert orders
    cursor.executemany(
        "INSERT INTO orders (user_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)",
        orders,
    )

    # Insert order items with correct order IDs
    flat_items = []
    for order_idx, items in enumerate(all_items):
        order_id = order_idx + 1  # AUTOINCREMENT starts at 1
        for prod_id, quantity, unit_price in items:
            flat_items.append((order_id, prod_id, quantity, unit_price))

    cursor.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        flat_items,
    )
    print(f"  ✓ Inserted {len(orders)} orders")
    print(f"  ✓ Inserted {len(flat_items)} order items")


def generate_database() -> str:
    """Generate the full e-commerce database. Returns the DB path."""
    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print(f"🗄️  Generating e-commerce database at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        create_tables(cursor)
        generate_users(cursor)
        product_info = generate_products(cursor)
        generate_orders_and_items(cursor, product_info)
        conn.commit()

        # Print summary
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"\n📊 Database Summary:")
        print(f"  Users:       {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM products")
        print(f"  Products:    {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM orders")
        print(f"  Orders:      {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM order_items")
        print(f"  Order Items: {cursor.fetchone()[0]}")
        cursor.execute("SELECT MIN(order_date), MAX(order_date) FROM orders")
        min_date, max_date = cursor.fetchone()
        print(f"  Date Range:  {min_date[:10]} → {max_date[:10]}")

        print(f"\n✅ Database generated successfully!")
        return DB_PATH

    finally:
        conn.close()


if __name__ == "__main__":
    generate_database()
