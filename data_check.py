# data_check.py
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "food_wastage.db"

def fetch_table_data(conn, table_name):
    return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

def delete_expired_food(conn):
    today = datetime.now()
    cur = conn.cursor()

    # Select expired food before deletion for logging
    expired = pd.read_sql_query("""
        SELECT Food_ID, Food_Name, Expiry_Date 
        FROM food_listings
    """, conn)

    expired['Expiry_Date'] = pd.to_datetime(expired['Expiry_Date'], errors='coerce', dayfirst=False)
    expired_items = expired[expired['Expiry_Date'] < today]

    if not expired_items.empty:
        ids_to_delete = tuple(expired_items['Food_ID'])
        cur.execute(f"DELETE FROM food_listings WHERE Food_ID IN ({','.join('?'*len(ids_to_delete))})", ids_to_delete)
        conn.commit()
        print(f"🗑 Deleted {len(expired_items)} expired food items.")
    else:
        print("✅ No expired food found.")

def check_and_fix_data():
    conn = sqlite3.connect(DB_FILE)
    tables = ["providers", "receivers", "food_listings", "claims"]

    print("\n📊 --- Table Row Counts ---")
    for table in tables:
        count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)['count'][0]
        print(f"{table}: {count} rows")

    print("\n🔍 --- First 5 Rows from Each Table ---")
    for table in tables:
        print(f"\n--- {table.upper()} ---")
        print(fetch_table_data(conn, table).head())

    print("\n⚠️ --- Data Quality Checks ---\n")

    # Missing values check
    for table in tables:
        df = fetch_table_data(conn, table)
        if df.isnull().sum().sum() == 0:
            print(f"{table}: ✅ No missing values")
        else:
            print(f"{table}: ❌ Missing values found\n{df.isnull().sum()}")

    # Quantity check
    food_df = fetch_table_data(conn, "food_listings")
    if (food_df['Quantity'] <= 0).any():
        print("food_listings: ❌ Invalid quantities found")
    else:
        print("food_listings: ✅ All quantities are valid")

    # Expired food check + fix
    food_df['Expiry_Date'] = pd.to_datetime(food_df['Expiry_Date'], errors='coerce', dayfirst=False)
    today = datetime.now()
    expired = food_df[food_df['Expiry_Date'] < today]

    if not expired.empty:
        print("\nfood_listings: ❌ Expired food items found")
        print(expired[['Food_ID', 'Food_Name', 'Expiry_Date']].head())
        delete_expired_food(conn)
    else:
        print("food_listings: ✅ No expired food found")

    conn.close()
    print("\n✅ Data check and cleanup completed.")

if __name__ == "__main__":
    check_and_fix_data()
