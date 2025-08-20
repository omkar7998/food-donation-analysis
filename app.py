import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from typing import Tuple, List

DB_PATH = "food_wastage.db"

# -----------------------------
# DB Helpers
# -----------------------------
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def run_query(sql: str, params: Tuple = ()):  # returns DataFrame
    try:
        return pd.read_sql_query(sql, get_conn(), params=params)
    except Exception as e:
        st.error(f"SQL error: {e}")
        return pd.DataFrame()

def run_execute(sql: str, params: Tuple = ()):  # execute write
    try:
        cur = get_conn().cursor()
        cur.execute(sql, params)
        get_conn().commit()
        return cur.lastrowid
    except Exception as e:
        st.error(f"SQL error: {e}")
        return None

# -----------------------------
# App Shell
# -----------------------------
st.set_page_config(page_title="Local Food Wastage Management", layout="wide")
st.title("🥗 Local Food Wastage Management System")
st.caption("Filter, contact, and manage donations. Backed by SQLite.")

PAGES = [
    "Browse & Filter",
    "Contacts",
    "CRUD",
    "SQL Insights (15 Queries)",
]
page = st.sidebar.radio("Navigate", PAGES)

# Load reference data once per render
providers_df = run_query("SELECT Provider_ID, Name, Type, City, Contact FROM providers ORDER BY Name")
receivers_df = run_query("SELECT Receiver_ID, Name, Type, City, Contact FROM receivers ORDER BY Name")
listings_df = run_query("SELECT * FROM food_listings ORDER BY Food_ID")
claims_df = run_query("SELECT * FROM claims ORDER BY Claim_ID")

# -----------------------------
# Page 1: Browse & Filter
# -----------------------------
if page == "Browse & Filter":
    st.subheader("🔎 Filter food donations")

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        cities = sorted(list({str(x) for x in listings_df["Location"].dropna().tolist()}))
        f_city = st.multiselect("Location", options=cities)
    with c2:
        prov_names = providers_df["Name"].dropna().tolist()
        f_provider = st.multiselect("Provider (name)", options=prov_names)
    with c3:
        food_types = sorted(list({str(x) for x in listings_df["Food_Type"].dropna().tolist()}))
        f_foodtype = st.multiselect("Food Type", options=food_types)

    # Build dynamic SQL
    conditions: List[str] = []
    params: List = []

    if f_city:
        placeholders = ",".join(["?"] * len(f_city))
        conditions.append(f"l.Location IN ({placeholders})")
        params.extend(f_city)

    if f_provider:
        placeholders = ",".join(["?"] * len(f_provider))
        conditions.append(f"p.Name IN ({placeholders})")
        params.extend(f_provider)

    if f_foodtype:
        placeholders = ",".join(["?"] * len(f_foodtype))
        conditions.append(f"l.Food_Type IN ({placeholders})")
        params.extend(f_foodtype)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f'''
        SELECT l.Food_ID, l.Food_Name, l.Quantity, l.Expiry_Date,
               p.Name AS Provider_Name, p.Type AS Provider_Type, p.City AS Provider_City, p.Contact AS Provider_Contact,
               l.Location, l.Food_Type, l.Meal_Type
        FROM food_listings l
        LEFT JOIN providers p ON p.Provider_ID = l.Provider_ID
        {where_clause}
        ORDER BY date(l.Expiry_Date) ASC
    '''
    results = run_query(sql, tuple(params))

    st.write(f"Found **{len(results)}** listing(s).")
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.markdown("### 📞 Quick Contact")
    cprov, crec = st.columns(2)
    with cprov:
        st.markdown("**Contact a Provider**")
        if not results.empty:
            opts = results[["Food_ID", "Provider_Name", "Provider_Contact"]].drop_duplicates().copy()
            opts["Label"] = opts.apply(lambda r: f"Food #{r['Food_ID']} • {r['Provider_Name']} • {r['Provider_Contact']}", axis=1)
            st.selectbox("Select provider", options=opts["Label"].tolist(), key="prov_sel")
            st.caption("Use your phone/email app to contact them.")
        else:
            st.info("Apply filters to see provider contacts.")
    with crec:
        st.markdown("**Contact a Receiver**")
        if not claims_df.empty:
            # receivers who claimed those food IDs
            recs = run_query(
                """
                SELECT DISTINCT r.Receiver_ID, r.Name, r.City, r.Contact
                FROM receivers r
                JOIN claims c ON c.Receiver_ID = r.Receiver_ID
                ORDER BY r.Name
                """
            )
            if not recs.empty:
                recs["Label"] = recs.apply(lambda r: f"{r['Name']} • {r['City']} • {r['Contact']}", axis=1)
                st.selectbox("Select receiver", options=recs["Label"].tolist(), key="rec_sel")
                st.caption("Use your phone/email app to contact them.")
            else:
                st.info("No receivers found.")
        else:
            st.info("No claims found yet.")

# -----------------------------
# Page 2: Contacts (Providers & Receivers)
# -----------------------------
elif page == "Contacts":
    st.subheader("📇 Providers & Receivers")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Providers")
        st.dataframe(providers_df, use_container_width=True, hide_index=True)
        st.caption("Tip: Filter with the column headers or export via right-click → Copy.")

    with c2:
        st.markdown("#### Receivers")
        st.dataframe(receivers_df, use_container_width=True, hide_index=True)

# -----------------------------
# Page 3: CRUD
# -----------------------------
elif page == "CRUD":
    st.subheader("🛠️ CRUD Operations")
    st.caption("Create, Read, Update, Delete for Providers, Receivers, Food Listings, and Claims")

    entity = st.selectbox("Choose table", ["providers", "receivers", "food_listings", "claims"])

    # READ
    st.markdown("#### Current Records")
    current = run_query(f"SELECT * FROM {entity} LIMIT 500")
    st.dataframe(current, use_container_width=True, hide_index=True)

    st.markdown("---")

    # CREATE
    st.markdown("#### ➕ Add New Record")
    if entity == "providers":
        with st.form("add_provider"):
            Provider_ID = st.number_input("Provider_ID", min_value=1, step=1)
            Name = st.text_input("Name")
            Type = st.text_input("Type")
            Address = st.text_input("Address")
            City = st.text_input("City")
            Contact = st.text_input("Contact")
            submitted = st.form_submit_button("Add Provider")
        if submitted:
            run_execute(
                "INSERT INTO providers (Provider_ID, Name, Type, Address, City, Contact) VALUES (?,?,?,?,?,?)",
                (Provider_ID, Name, Type, Address, City, Contact),
            )
            st.success("Provider added!")

    elif entity == "receivers":
        with st.form("add_receiver"):
            Receiver_ID = st.number_input("Receiver_ID", min_value=1, step=1)
            Name = st.text_input("Name")
            Type = st.text_input("Type")
            City = st.text_input("City")
            Contact = st.text_input("Contact")
            submitted = st.form_submit_button("Add Receiver")
        if submitted:
            run_execute(
                "INSERT INTO receivers (Receiver_ID, Name, Type, City, Contact) VALUES (?,?,?,?,?)",
                (Receiver_ID, Name, Type, City, Contact),
            )
            st.success("Receiver added!")

    elif entity == "food_listings":
        with st.form("add_food"):
            Food_ID = st.number_input("Food_ID", min_value=1, step=1)
            Food_Name = st.text_input("Food_Name")
            Quantity = st.number_input("Quantity", min_value=1, step=1)
            Expiry_Date = st.text_input("Expiry_Date (YYYY-MM-DD)")
            Provider_ID = st.number_input("Provider_ID", min_value=1, step=1)
            Provider_Type = st.text_input("Provider_Type")
            Location = st.text_input("Location")
            Food_Type = st.text_input("Food_Type")
            Meal_Type = st.text_input("Meal_Type")
            submitted = st.form_submit_button("Add Food Listing")
        if submitted:
            run_execute(
                """
                INSERT INTO food_listings (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type),
            )
            st.success("Food listing added!")

    elif entity == "claims":
        with st.form("add_claim"):
            Claim_ID = st.number_input("Claim_ID", min_value=1, step=1)
            Food_ID = st.number_input("Food_ID", min_value=1, step=1)
            Receiver_ID = st.number_input("Receiver_ID", min_value=1, step=1)
            Status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
            Timestamp = st.text_input("Timestamp (YYYY-MM-DD HH:MM)")
            submitted = st.form_submit_button("Add Claim")
        if submitted:
            run_execute(
                "INSERT INTO claims (Claim_ID, Food_ID, Receiver_ID, Status, Timestamp) VALUES (?,?,?,?,?)",
                (Claim_ID, Food_ID, Receiver_ID, Status, Timestamp),
            )
            st.success("Claim added!")

    st.markdown("---")

    # UPDATE
    st.markdown("#### ✏️ Update Record")
    key_col = {
        "providers": "Provider_ID",
        "receivers": "Receiver_ID",
        "food_listings": "Food_ID",
        "claims": "Claim_ID",
    }[entity]

    with st.form("update_form"):
        record_id = st.number_input(f"{key_col} to update", min_value=1, step=1)
        field = st.selectbox("Field", [col for col in current.columns if col != key_col])
        new_value = st.text_input("New value")
        submitted_u = st.form_submit_button("Update")
    if submitted_u:
        run_execute(f"UPDATE {entity} SET {field} = ? WHERE {key_col} = ?", (new_value, record_id))
        st.success("Record updated!")

    st.markdown("---")

    # DELETE
    st.markdown("#### 🗑️ Delete Record")
    with st.form("delete_form"):
        del_id = st.number_input(f"{key_col} to delete", min_value=1, step=1, key="del")
        submitted_d = st.form_submit_button("Delete")
    if submitted_d:
        run_execute(f"DELETE FROM {entity} WHERE {key_col} = ?", (del_id,))
        st.warning("Record deleted.")

# -----------------------------
# Page 4: SQL Insights (15 Queries)
# -----------------------------
elif page == "SQL Insights (15 Queries)":
    st.subheader("📈 SQL-powered Analysis & Insights (15 queries)")
    st.caption("Tables only (no charts), as requested.")

    # 1) Total donations by provider (count & quantity)
    st.markdown("**1) Total donations by provider (count & quantity)**")
    st.dataframe(run_query(
        """
        SELECT p.Provider_ID, p.Name AS Provider, COUNT(l.Food_ID) AS Listings,
               COALESCE(SUM(l.Quantity),0) AS Total_Quantity
        FROM providers p
        LEFT JOIN food_listings l ON l.Provider_ID = p.Provider_ID
        GROUP BY p.Provider_ID, p.Name
        ORDER BY Total_Quantity DESC
        """
    ), use_container_width=True, hide_index=True)

    # 2) Provider types by total quantity
    st.markdown("**2) Provider types by total quantity**")
    st.dataframe(run_query(
        """
        SELECT p.Type AS Provider_Type, COALESCE(SUM(l.Quantity),0) AS Total_Quantity,
               COUNT(l.Food_ID) AS Listings
        FROM providers p
        LEFT JOIN food_listings l ON l.Provider_ID = p.Provider_ID
        GROUP BY p.Type
        ORDER BY Total_Quantity DESC
        """
    ), use_container_width=True, hide_index=True)

    # 3) Most frequent food items
    st.markdown("**3) Most frequent food items**")
    st.dataframe(run_query(
        """
        SELECT Food_Name, COUNT(*) AS Appearances, COALESCE(SUM(Quantity),0) AS Total_Quantity
        FROM food_listings
        GROUP BY Food_Name
        ORDER BY Appearances DESC
        """
    ), use_container_width=True, hide_index=True)

    # 4) Highest demand locations (by claims)
    st.markdown("**4) Highest demand locations (by claims)**")
    st.dataframe(run_query(
        """
        SELECT l.Location, COUNT(c.Claim_ID) AS Claims
        FROM claims c
        JOIN food_listings l ON l.Food_ID = c.Food_ID
        GROUP BY l.Location
        ORDER BY Claims DESC
        """
    ), use_container_width=True, hide_index=True)

    # 5) Claim status distribution
    st.markdown("**5) Claim status distribution**")
    st.dataframe(run_query("SELECT Status, COUNT(*) AS Count FROM claims GROUP BY Status"), use_container_width=True, hide_index=True)

    # 6) Average quantity per food type
    st.markdown("**6) Average quantity per food type**")
    st.dataframe(run_query(
        "SELECT Food_Type, ROUND(AVG(Quantity),2) AS Avg_Quantity FROM food_listings GROUP BY Food_Type ORDER BY Avg_Quantity DESC"
    ), use_container_width=True, hide_index=True)

    # 7) Near-expiry items (next 3 days)
    st.markdown("**7) Near-expiry items (next 3 days)**")
    today = date.today().strftime('%Y-%m-%d')
    st.dataframe(run_query(
        """
        SELECT Food_ID, Food_Name, Quantity, Expiry_Date, Location
        FROM food_listings
        WHERE date(Expiry_Date) BETWEEN date(?) AND date(?, '+3 day')
        ORDER BY date(Expiry_Date)
        """,
        (today, today),
    ), use_container_width=True, hide_index=True)

    # 8) Unclaimed items (no claims)
    st.markdown("**8) Unclaimed items (no claims)**")
    st.dataframe(run_query(
        """
        SELECT l.Food_ID, l.Food_Name, l.Location, l.Quantity
        FROM food_listings l
        LEFT JOIN claims c ON c.Food_ID = l.Food_ID
        WHERE c.Food_ID IS NULL
        ORDER BY l.Food_ID
        """
    ), use_container_width=True, hide_index=True)

    # 9) Receiver activity (claims per receiver)
    st.markdown("**9) Receiver activity (claims per receiver)**")
    st.dataframe(run_query(
        """
        SELECT r.Receiver_ID, r.Name AS Receiver, COUNT(c.Claim_ID) AS Claims
        FROM receivers r
        LEFT JOIN claims c ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Receiver_ID, r.Name
        ORDER BY Claims DESC
        """
    ), use_container_width=True, hide_index=True)

    # 10) Daily claims trend (table)
    st.markdown("**10) Daily claims trend**")
    st.dataframe(run_query(
        """
        SELECT substr(Timestamp,1,10) AS Day, COUNT(*) AS Claims
        FROM claims
        GROUP BY substr(Timestamp,1,10)
        ORDER BY Day
        """
    ), use_container_width=True, hide_index=True)

    # 11) Wastage risk (expired items still present)
    st.markdown("**11) Wastage risk (expired items still present)**")
    st.dataframe(run_query(
        """
        SELECT Food_ID, Food_Name, Location, Expiry_Date
        FROM food_listings
        WHERE date(Expiry_Date) < date('now')
        ORDER BY date(Expiry_Date)
        """
    ), use_container_width=True, hide_index=True)

    # 12) Provider cities with most donations
    st.markdown("**12) Provider cities with most donations**")
    st.dataframe(run_query(
        """
        SELECT p.City, COUNT(l.Food_ID) AS Listings, COALESCE(SUM(l.Quantity),0) AS Total_Quantity
        FROM providers p
        LEFT JOIN food_listings l ON l.Provider_ID = p.Provider_ID
        GROUP BY p.City
        ORDER BY Total_Quantity DESC
        """
    ), use_container_width=True, hide_index=True)

    # 13) Claim-to-availability ratio per location
    st.markdown("**13) Claim-to-availability ratio per location**")
    st.dataframe(run_query(
        """
        WITH listings AS (
            SELECT Location, COUNT(*) AS L
            FROM food_listings
            GROUP BY Location
        ), claims_cte AS (
            SELECT l.Location AS Location, COUNT(c.Claim_ID) AS C
            FROM claims c JOIN food_listings l ON l.Food_ID = c.Food_ID
            GROUP BY l.Location
        )
        SELECT listings.Location,
               L AS Listings,
               COALESCE(C,0) AS Claims,
               ROUND(CAST(COALESCE(C,0) AS FLOAT)/NULLIF(L,0), 2) AS Claim_to_Listings_Ratio
        FROM listings LEFT JOIN claims_cte USING(Location)
        ORDER BY Claim_to_Listings_Ratio DESC
        """
    ), use_container_width=True, hide_index=True)

    # 14) Demand vs supply by food type
    st.markdown("**14) Demand vs supply by food type**")
    st.dataframe(run_query(
        """
        WITH supply AS (
            SELECT Food_Type, SUM(Quantity) AS Supply_Qty
            FROM food_listings
            GROUP BY Food_Type
        ), demand AS (
            SELECT l.Food_Type, COUNT(c.Claim_ID) AS Demand_Claims
            FROM claims c JOIN food_listings l ON l.Food_ID = c.Food_ID
            GROUP BY l.Food_Type
        )
        SELECT s.Food_Type,
               s.Supply_Qty,
               COALESCE(d.Demand_Claims,0) AS Demand_Claims
        FROM supply s LEFT JOIN demand d ON d.Food_Type = s.Food_Type
        ORDER BY Demand_Claims DESC
        """
    ), use_container_width=True, hide_index=True)

    # 15) Meal type distribution by location
    st.markdown("**15) Meal type distribution by location**")
    st.dataframe(run_query(
        """
        SELECT Location, Meal_Type, COUNT(*) AS Listings
        FROM food_listings
        GROUP BY Location, Meal_Type
        ORDER BY Listings DESC
        """
    ), use_container_width=True, hide_index=True)

    st.success("All 15 queries executed.")
