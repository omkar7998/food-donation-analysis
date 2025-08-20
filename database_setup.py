import sqlite3

# Connect to database (creates file if not exists)
conn = sqlite3.connect("food_wastage.db")
cursor = conn.cursor()

# Drop existing tables if they exist (for a clean start)
cursor.execute("DROP TABLE IF EXISTS providers;")
cursor.execute("DROP TABLE IF EXISTS receivers;")
cursor.execute("DROP TABLE IF EXISTS food_listings;")
cursor.execute("DROP TABLE IF EXISTS claims;")

# Create Providers Table
cursor.execute("""
CREATE TABLE providers (
    Provider_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    Address TEXT,
    City TEXT,
    Contact TEXT
);
""")

# Create Receivers Table
cursor.execute("""
CREATE TABLE receivers (
    Receiver_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    City TEXT,
    Contact TEXT
);
""")

# Create Food Listings Table
cursor.execute("""
CREATE TABLE food_listings (
    Food_ID INTEGER PRIMARY KEY,
    Food_Name TEXT,
    Quantity INTEGER,
    Expiry_Date TEXT,
    Provider_ID INTEGER,
    Provider_Type TEXT,
    Location TEXT,
    Food_Type TEXT,
    Meal_Type TEXT,
    FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID)
);
""")

# Create Claims Table
cursor.execute("""
CREATE TABLE claims (
    Claim_ID INTEGER PRIMARY KEY,
    Food_ID INTEGER,
    Receiver_ID INTEGER,
    Status TEXT,
    Timestamp TEXT,
    FOREIGN KEY (Food_ID) REFERENCES food_listings(Food_ID),
    FOREIGN KEY (Receiver_ID) REFERENCES receivers(Receiver_ID)
);
""")

conn.commit()
conn.close()

print("✅ Database and tables created successfully with matching CSV columns!")
