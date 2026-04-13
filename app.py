import streamlit as st
import pydeck as pdk
import pandas as pd
from geopy.geocoders import Nominatim

# Full screen layout
st.set_page_config(page_title="Farmland ROI Map", layout="wide")

# Initialize geocoder
geolocator = Nominatim(user_agent="farmland_app_v1")

# --- 1. LOAD SEARCH INDEX (Cached for speed) ---
@st.cache_data
def load_index():
    # Loading your search_index.csv to enable searching by APN
    return pd.read_csv("search_index.csv", dtype={'APN': str})

df_index = load_index()

# --- 2. SIDEBAR FILTERS & SEARCH ---
with st.sidebar:
    st.title("Navigation & Filters")
    
    st.subheader("Locate Parcel")
    search_query = st.text_input("Enter APN (e.g., 00101001)")
    
    # Logic to find coordinates for the search bar
    target_view = None
    if search_query:
        match = df_index[df_index['APN'] == search_query]
        if not match.empty:
            target_view = {
                "lat": match.iloc[0]['lat'],
                "lon": match.iloc[0]['lon'],
                "zoom": 15
            }
            st.success(f"Located APN {search_query}")
        else:
            st.error("APN not found in index.")

    st.markdown("---")
    st.subheader("Visual Filters")
    show_prime = st.checkbox("Show Prime Soils", value=True)
    show_marginal = st.checkbox("Show Marginal Soils", value=True)
    only_irrigated = st.checkbox("Only Irrigated Parcels", value=False)

# --- 3. DYNAMIC MAP LOGIC ---
prime_color = "[34, 139, 34, 80]" if show_prime else "[0, 0, 0, 0]"
marginal_color = "[255, 80, 80, 80]" if show_marginal else "[0, 0, 0, 0]"
irrigation_check = "properties.W_Dist == 1" if only_irrigated else "true"

fill_color_logic = f"""
    ({irrigation_check}) ? 
        (properties.S_Bin == 1 ? {marginal_color} : {prime_color}) 
    : [0, 0, 0, 0]
"""

# --- 4. MAP VIEW STATE ---
# If user searched an APN, zoom there. Otherwise, default view.
if target_view:
    initial_view = pdk.ViewState(latitude=target_view['lat'], longitude=target_view['lon'], zoom=target_view['zoom'])
else:
    initial_view = pdk.ViewState(latitude=36.7783, longitude=-119.4179, zoom=8)

layer = pdk.Layer(
    "MVTLayer",
    data="https://andrewphankt.github.io/farmland-roi/static/tiles/{z}/{x}/{y}.pbf", 
    id="agri-parcel-layer",
    min_zoom=6,
    max_zoom=14, 
    pickable=True,       
    auto_highlight=True, 
    highlight_color=[255, 255, 255, 200], 
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 80],
    line_width_min_pixels=0.5,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=initial_view,
    tooltip={"html": "<b>APN:</b> {APN}<br><b>Acres:</b> {Acres}"},
    map_style="mapbox://styles/mapbox/satellite-v9" 
)

# --- 5. MAIN DISPLAY ---
map_col, info_col = st.columns([3, 1])

with map_col:
    map_event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

with info_col:
    st.subheader("Parcel Details")
    
    if map_event and map_event.selection and map_event.selection.get("objects"):
        selected_data = map_event.selection["objects"].get("agri-parcel-layer", [])
        
        if selected_data:
            props = selected_data[0].get("properties", {})
            coords = selected_data[0].get("coordinate", [0, 0]) # [lon, lat]
            
            apn = props.get('APN')
            st.success(f"Selected APN: **{apn}**")
            
            # 1. Fetch Address via Geopy
            try:
                location = geolocator.reverse(f"{coords[1]}, {coords[0]}", timeout=3)
                address = location.address if location else "Address not found"
            except:
                address = "Service busy, try again"
            
            # 2. Translate Soil/Water
            soil_status = "Marginal Soil" if props.get('S_Bin') == 1 else "Prime Farmland"
            water_status = "Irrigated" if props.get('W_Dist') == 1 else "Non-Irrigated"
            
            # Display info
            st.write(f"**Estimated Address:** {address}")
            st.write(f"**County:** {props.get('County')}")
            st.write(f"**Size:** {props.get('Acres')} Acres")
            st.write(f"**Soil Class:** {soil_status}")
            st.write(f"**Water Access:** {water_status}")
            
            st.divider()
            st.warning("Owner Name: To view legal owners, you must upload the County Assessor's Roll CSV.")
    else:
        st.info("Search for an APN or click a parcel on the map.")
