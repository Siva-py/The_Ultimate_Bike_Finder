import streamlit as st
import json
from bikes_logic import filter_and_score, get_height_range_mm, safe_int, safe_float

# Load data
DATA_PATH = r"C:\DM Drive\VIT SEM 1\Ai\projects\expertise system\The_Ultimate_Bike_Finder\data\bikes_data.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    bikes = json.load(f)

st.set_page_config(page_title="🏍️ Ultimate Bike Finder", layout="centered")

st.title("🏍️ Ultimate Bike Finder")
st.write("Answer a few quick questions to discover bikes that match your needs!")

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    brand = st.selectbox("Preferred brand", ["any", "hero", "honda", "yamaha", "bajaj", "suzuki", "royal enfield"])
    budget_min = st.number_input("Min Budget (₹)", 0, 1000000, 50000, step=5000)
    budget_max = st.number_input("Max Budget (₹)", 0, 2000000, 200000, step=5000)
    min_mileage = st.slider("Minimum Mileage (kmpl)", 0, 100, 40)
    engine_min = st.slider("Min Engine CC", 50, 2000, 100)
    engine_max = st.slider("Max Engine CC", 50, 2000, 500)
with col2:
    user_height_cm = st.slider("Your Height (cm)", 140, 200, 170)
    ride_type = st.selectbox("Ride Type", ["both", "city", "highway"])
    wants_lightweight = st.checkbox("Prefer lightweight bikes (for city use)?")
    long_rides = st.checkbox("Planning many long rides / touring?")
    bike_type = st.selectbox("Bike Type", ["any", "sport", "commuter", "adventure", "cruiser"])

if st.button("🔍 Find My Bike"):
    prefs = {
        "brand": None if brand == "any" else brand.lower(),
        "budget_min": budget_min,
        "budget_max": budget_max,
        "min_mileage": min_mileage,
        "engine_min": engine_min,
        "engine_max": engine_max,
        "user_height_cm": user_height_cm,
        "ride_type": ride_type,
        "wants_lightweight": wants_lightweight,
        "long_rides": long_rides,
        "bike_type": None if bike_type == "any" else bike_type.lower(),
    }

    results = filter_and_score(bikes, prefs)

    if not results:
        st.warning("No bikes matched your preferences. Try adjusting filters.")
    else:
        st.success(f"Found {len(results)} matching bikes!")
        for i, (b, s) in enumerate(results[:10], 1):
            with st.container():
                st.markdown(f"### {i}. {b['brand'].title()} {b['model'].title()}")
                st.markdown(f"**Type:** {b.get('category_group', 'N/A').title()}")
                st.markdown(f"💰 **Price:** ₹{b['price_inr']:,}")
                st.markdown(f"⛽ **Mileage:** {b['mileage_kmpl']} km/l | **Engine:** {b['engine_cc']} cc")
                st.markdown(f"📏 **Seat Height:** {b['seat_height_mm']/10:.1f} cm | ⚖️ **Weight:** {b['kerb_weight_kg']} kg")
                st.markdown(f"⛽ **Fuel Tank:** {b['fuel_tank_l']} L | 🛋️ **Comfort:** {b.get('comfort_level',3)}/5")
                st.progress(float(s))
                st.write("---")
