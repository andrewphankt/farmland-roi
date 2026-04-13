import streamlit as st
import pydeck as pdk
import pandas as pd

# Full screen layout
st.set_page_config(page_title="Farmland ROI Map", layout="wide")

# --- 1. LOAD SEARCH INDEX ---
# Caching ensures the 560k row CSV only loads once, keeping the app fast
@st.cache_data
def load_index():
    return pd.read_csv("search_index.csv", dtype={'APN': str})

df_index = load_index()

# --- 2. SIDEBAR FILTERS & SEARCH ---
with st.sidebar:
    st.title("Navigation & Filters")
    
    st.subheader("Locate Parcel")
    search_query = st.text_input("Enter APN (e.g., 00101001)")
    
    target_view = None
    if search_query:
        # Strip whitespace just in case the user pasted it with spaces
        search_query = search_query.strip()
        match = df_index[df_index['APN'] == search_query]
        
        if not match.empty:
            target_view = {
                "lat": float(match.iloc[0]['lat']),
                "lon": float(match.iloc[0]['lon']),
                "zoom": 15
            }
        else:
            st.error("APN not found in index.")

    st.markdown("---")
    st.subheader("Visual Filters")
    show_prime = st.checkbox("Show Prime Soils", value=True)
    show_marginal = st.checkbox("Show Marginal Soils", value=True)
    only_irrigated = st.checkbox("Only Irrigated Parcels", value=False)

# --- 3. DYNAMIC MAP LOGIC ---
# Alpha locked at 120 for visibility across all zoom levels
prime_color = "[34, 139, 34, 120]" if show_prime else "[0, 0, 0, 0]"
marginal_color = "[255, 80, 80, 120]" if show_marginal else "[0, 0, 0, 0]"
irrigation_check = "properties.W_Dist == 1" if only_irrigated else "true"

fill_color_logic = f"""
    ({irrigation_check}) ? 
        (properties.S_Bin == 1 ? {marginal_color} : {prime_color}) 
    : [0, 0, 0, 0]
"""

# --- 4. MAP VIEW STATE ---
if target_view:
    initial_view = pdk.ViewState(latitude=target_view['lat'], longitude=target_view['lon'], zoom=target_view['zoom'])
else:
    # Default view over Central Valley
    initial_view = pdk.ViewState(latitude=36.7783, longitude=-119.4179, zoom=8)

layer = pdk.Layer(
    "MVTLayer",
    data="https://andrewphankt.github.io/farmland-roi/static/tiles/{z}/{x}/{y}.pbf", 
    id="agri-parcel-layer",
    min_zoom=6,
    max_zoom=14, 
    pickable=True,       
    auto_highlight=True, 
    highlight_color=[255, 255, 255, 180], # Bold white on hover
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 60],
    line_width_min_pixels=0.5,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=initial_view,
    tooltip={
        "html": "<b>APN:</b> {APN}<br><b>Acres:</b> {Acres}",
        "style": {"backgroundColor": "#222222", "color": "white", "borderRadius": "4px"}
    },
    map_style="mapbox://styles/mapbox/satellite-v9" 
)

# --- 5. MAIN DISPLAY ---
map_col, info_col = st.columns([3, 1])

with map_col:
    map_event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

with info_col:
    st.subheader("Parcel Details")
    
    # If a parcel is selected via click
    if map_event and map_event.selection and map_event.selection.get("objects"):
        selected_data = map_event.selection["objects"].get("agri-parcel-layer", [])
        
        if selected_data:
            props = selected_data[0].get("properties", {})
            apn = str(props.get('APN'))
            
            st.success(f"Selected APN: **{apn}**")
            
            # --- THE GOOGLE MAPS BRIDGE (PRO FIX) ---
            # Look up the exact coordinate of the clicked parcel from the background CSV
            match = df_index[df_index['APN'] == apn]
            
            if not match.empty:
                lat = float(match.iloc[0]['lat'])
                lon = float(match.iloc[0]['lon'])
                # Official Google Maps Search URL format
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.link_button("📍 Open in Google Maps", google_maps_url, use_container_width=True)
            else:
                st.warning("Coordinate lookup failed for this APN. Cannot generate Google Maps link.")
            
            # --- TRANSLATE DATA ---
            soil_status = "Marginal Soil" if props.get('S_Bin') == 1 else "Prime Farmland"
            water_status = "Irrigated" if props.get('W_Dist') == 1 else "Non-Irrigated"
            
            st.markdown(f"""
            ### Attributes
            - **County:** {props.get('County')}
            - **Size:** {props.get('Acres')} Acres
            - **Soil Quality:** {soil_status}
            - **Water Access:** {water_status}
            - **Crop ID:** {props.get('C_ID')}
            """)
            
            st.divider()
            st.caption("Copy the APN to search county records for legal owner names.")
    else:
        st.info("Click a parcel to unlock the Google Maps link and view attributes.")
