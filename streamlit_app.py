import streamlit as st
import pandas as pd
import psycopg
import psycopg2
providers_df = pd.read_csv('providers_data.csv')
receivers_df = pd.read_csv('receivers_data.csv')
food_listings_df = pd.read_csv('food_listings_data.csv')
claims_df = pd.read_csv('claims_data.csv')
st.set_page_config(page_title="Local Food Wastage Management", layout="wide")
st.title(" Local Food Wastage Management System")
st.write("Connect surplus food providers with receivers in need. Use the filters below to find available food, or manage listings and claims.")
connection = psycopg2.connect(host = "localhost",database = "ramji", user = "postgres" , password ="Ktm@9291")
cur = connection.cursor()
st.sidebar.header("Filter Listings")
# Load options from database for each filter (to get unique values)
cur.execute("SELECT DISTINCT City FROM providers;")
cities = [row[0] for row in cur.fetchall()]
cities.insert(0, "All") # add an "All" option
selected_city = st.sidebar.selectbox("City", cities)
cur.execute("SELECT DISTINCT Name FROM providers;")
providers = [row[0] for row in cur.fetchall()]
providers.insert(0, "All")
selected_provider = st.sidebar.selectbox("Provider", providers)
cur.execute("SELECT DISTINCT Food_Type FROM food_listings;")
food_types = [row[0] for row in cur.fetchall()]
food_types.insert(0, "All")
selected_food_type = st.sidebar.selectbox("Food Type", food_types)

cur.execute("SELECT DISTINCT Meal_Type FROM food_listings;")
meal_types = [row[0] for row in cur.fetchall()]
meal_types.insert(0, "All")
selected_meal_type = st.sidebar.selectbox("Meal Type", meal_types)
where_clauses = []
if selected_city != "All":
    where_clauses.append(f"Location = '{selected_city}'")
if selected_provider != "All":
    where_clauses.append(f"Provider_ID = (SELECT Provider_ID FROM providers WHERE Name = '{selected_provider}')")
if selected_food_type != "All":
    where_clauses.append(f"Food_Type = '{selected_food_type}'")
if selected_meal_type != "All":
    where_clauses.append(f"Meal_Type = '{selected_meal_type}'")
where_clause = " AND ".join(where_clauses)
query = "SELECT Food_ID, Food_Name, Quantity, Expiry_Date, Location, Food_Type,Meal_Type, Provider_ID FROM food_listings"
if where_clause:
    query += " WHERE " + where_clause
cur.execute(query)
rows = cur.fetchall()
filtered_listings = pd.DataFrame(rows,columns = [desc[0] for desc in cur.description])
    

providers_df = providers_df.rename(columns={"Provider_ID": "provider_id"})
st.subheader("Available Food Listings")
if filtered_listings.empty:
    st.write("No food listings match the selected filters.")
else:
    # Join with providers to get provider name and contact
    filtered_listings = filtered_listings.merge(providers_df, on="provider_id",how="left") # assuming you loaded providers_df earlier or query join in SQL
    filtered_listings.rename(columns={"Name": "Provider_Name", "Contact":"Provider_Contact"}, inplace=True)
    st.dataframe(filtered_listings[["Food_Name","Quantity","Expiry_Date","Location","Food_Type","Meal_Type"]])
#st.sidebar.markdown("---")
if st.sidebar.checkbox("Show Key Statistics"):
    st.subheader("📊 Key Statistics")
    # Example 1: Total listings count
    cur.execute("SELECT COUNT(*) FROM food_listings")
    total_listings = cur.fetchall()[0]
    cur.execute("SELECT COUNT(*) FROM claims")
    total_claims = cur.fetchall()[0]
    st.metric("Total Food Listings", total_listings)
    st.metric("Total Claims Made", total_claims)
# Example 2: Top 3 provider contributions
    top_providers = pd.read_sql_query("SELECT p.Name, COUNT(f.Food_ID) AS listings FROM food_listings f JOIN providers p ON f.Provider_ID=p.Provider_ID GROUP BY p.Name ORDER BY listings DESC LIMIT 3;", conn)
    st.write("**Top 3 Providers by Number of Listings:**")
    st.table(top_providers)
# Example 3: Claims by status (could use a pie chart)
    status_counts = pd.read_sql_query("SELECT Status, COUNT(*) as count FROM claims GROUP BY Status;", conn)
    fig = ... # create a matplotlib or plotly pie chart from status_counts
    st.pyplot(fig)
    
	#st.subheader("Manage Listings")
# Tab or section for adding a new listing:
with st.expander("Add New Food Listing"):
    with st.form("new_listing_form"):
        # Inputs for new listing
        provider_choice = st.selectbox("Provider", providers)
        # choose provider by name
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry = st.date_input("Expiry Date")
        food_type = st.selectbox("Food Type", ["Vegetarian","Non-Vegetarian","Vegan"])
        meal_type = st.selectbox("Meal Type",["Breakfast","Lunch","Dinner","Snacks"])
        submit_new = st.form_submit_button("Add Listing")
    if submit_new:
# Find Provider_ID from name
        cur.execute("SELECT Provider_ID, Type, City FROM providers WHERE Name=?;", (provider_choice,))
        result = cur.fetchall()
        if result:
            prov_id, prov_type, prov_city = result
# Insert into food_listings
            cur.execute("""INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date,Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)VALUES (?, ?, ?, ?, ?, ?, ?, ?);""", (food_name, quantity, expiry.strftime("%Y-%m-%d"), prov_id,prov_type, prov_city, food_type, meal_type))
            conn.commit()
            st.success(f"Added listing for '{food_name}' by {provider_choice}.")
        else:
            st.error("Provider not found!")
			
			
st.sidebar.subheader("Contact Directory")
contact_type = st.sidebar.radio("View contacts for:", ["Providers","Receivers"])
if contact_type == "Providers":
    cur.execute("SELECT Name, City, Contact FROM providers;")
    rows = cur.fetchall()
    provider_contacts = pd.DataFrame(rows,columns = [desc[0] for desc in cur.description])
    st.sidebar.dataframe(provider_contacts)
else:
    cur.execute("SELECT Name, City, Contact FROM receivers;")
    rows = cur.fetchall()
    receiver_contacts = pd.DataFrame(rows,columns = [desc[0] for desc in cur.description])
    st.sidebar.dataframe(receiver_contacts)