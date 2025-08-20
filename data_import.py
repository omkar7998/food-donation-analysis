import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "food_wastage.db"
DATA_FOLDER = "data"

# ------------------------------
# Utility function to run SQL
# ------------------------------
def execute_query(query, params=None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()

# ------------------------------
# Step 1: Clear all tables
# ------------------------------
def clear_tables():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        tables = ["providers", "receivers", "food_listings", "claims"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()
    print("🗑 All tables cleared before import.")

# ------------------------------
# Step 2: Import CSVs into DB
# ------------------------------
def import_csv_to_table(csv_file, table_name):
    file_path = os.path.join(DATA_FOLDER, csv_file)
    try:
        df = pd.read_csv(file_path)
        with sqlite3.connect(DB_FILE) as conn:
            df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"✅ Imported {file_path} into {table_name}")
    except Exception as e:
        print(f"⚠️ Error importing {file_path}: {e}")

# ------------------------------
# Step 3: Data Cleaning
# ------------------------------
def clean_data():
    today = datetime.today().strftime('%Y-%m-%d')

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Remove expired food
        cursor.execute(f"DELETE FROM food_listings WHERE date(Expiry_Date) < date('{today}')")
        expired_count = cursor.rowcount

        # Fix negative quantities
        cursor.execute("UPDATE food_listings SET Quantity = 1 WHERE Quantity < 0")

        # Remove invalid claims
        cursor.execute("""
            DELETE FROM claims
            WHERE Food_ID NOT IN (SELECT Food_ID FROM food_listings)
            OR Receiver_ID NOT IN (SELECT Receiver_ID FROM receivers)
        """)
        conn.commit()

    print(f"🧹 Data cleaned: {expired_count} expired food items removed, negative quantities fixed, invalid claims deleted.")

# ------------------------------
# Step 4: Data Quality Check
# ------------------------------
def data_quality_check():
    with sqlite3.connect(DB_FILE) as conn:
        # Show table row counts
        print("\n📊 --- Table Row Counts ---")
        for table in ["providers", "receivers", "food_listings", "claims"]:
            count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)['count'][0]
            print(f"{table}: {count} rows")

        # Show first 5 rows from each table
        print("\n🔍 --- First 5 Rows from Each Table ---")
        for table in ["providers", "receivers", "food_listings", "claims"]:
            print(f"\n--- {table.upper()} ---")
            print(pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5", conn))

        # Missing values check
        print("\n⚠️ --- Data Quality Checks ---")
        for table in ["providers", "receivers", "food_listings", "claims"]:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            if df.isnull().values.any():
                print(f"{table}: ❌ Missing values found")
            else:
                print(f"{table}: ✅ No missing values")

        # Quantity check
        df_food = pd.read_sql_query("SELECT * FROM food_listings", conn)
        if (df_food['Quantity'] <= 0).any():
            print("food_listings: ❌ Invalid quantities found")
        else:
            print("food_listings: ✅ All quantities are valid")

# ------------------------------
# Main Execution
# ------------------------------
if __name__ == "__main__":
    clear_tables()

    # Import datasets
    import_csv_to_table("providers_data.csv", "providers")
    import_csv_to_table("receivers_data.csv", "receivers")
    import_csv_to_table("food_listings_data.csv", "food_listings")
    import_csv_to_table("claims_data.csv", "claims")

    # Clean data
    clean_data()

    # Run data quality check
    data_quality_check()

    print("\n🎯 All CSV files imported, cleaned, and checked successfully.")
