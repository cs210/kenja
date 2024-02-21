"""
Main interface for the Sommelier app.
"""

# Stuff for Streamlit -- comment out for now
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Main packages to import
import streamlit as st
import folium
from geopy.geocoders import Nominatim
from sommelier_functions.sommelier_helpers import find_match
from metrics import SEARCH_COUNT
from state import count_sessions

# Initialize geopy geocoder
geolocator = Nominatim(user_agent="geoapiExercises", timeout=10)

# Header + increment visit count
count_sessions()
st.title("🍷 Sommelier")
st.subheader("You give us a request, we give you wine recs.")

# Core form/search function
submitted = False
slider_val = ""
with st.form("input_form"):
    st.write("Describe what wine you're looking for...")
    slider_val = st.text_input(
        'Ex: "I want a wine that goes well' ' with gouda and has notes of paprika."'
    )

    # Submit function
    submitted = st.form_submit_button("Submit")

# Checking for submitted + increment count
if submitted:
    SEARCH_COUNT.inc()
    st.subheader("Recommendations")
    results = find_match(slider_val)

    # Display results
    for i in range(len(results["documents"][0])):
        metadata = results["metadatas"][0][i]
        st.write("🍷 " + metadata["designation"])
        st.write("Vineyard: " + metadata["winery"])
        st.write("Variety: " + metadata["variety"])
        st.write("Points: " + metadata["points"])
        st.write("Country: " + metadata["country"])
        st.write(
            "Location: "
            + metadata["province"]
            + ", "
            + metadata["region_1"]
            + ", "
            + metadata["region_2"]
        )
        st.write("Price: " + metadata["price"])

        try:
            loc = geolocator.geocode(
                metadata["province"] + ", " + metadata["region_1"], timeout=10
            )
            if loc:
                m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=10)
                folium.Marker(
                    [loc.latitude, loc.longitude], popup=metadata["winery"]
                ).add_to(m)
                st.write(m)
            else:
                st.write("Could not find location")

        except Exception as e:
            print("An error occurred:", e)
        st.divider()