import streamlit as st
import pydeck as pdk
import pandas as pd
from geopy.geocoders import Nominatim

# Configuration
st.set_page_config(layout="wide", page_title="Agri-Diamond ROI Engine")

# --- 1. DATA LOADING ---
@st.cache_data(persist="disk")
def load_index():
    # Loading optimized search index
    return pd.read_csv("search_index.csv", dtype={'APN': str, 'C_ID': int, 'S_Bin': int, 'W_Dist': int, 'County': str})

try:
    df_all = load_index()
except Exception as e:
    st.error(f"Search index not found. Please run spatial_join.py first.")
    st.stop()

# Initialize View State in Session
if "view_state" not in st.session_state:
    st.session_state.view_state = pdk.ViewState(
        latitude=36.3, 
        longitude=-119.3, 
        zoom=9, 
        pitch=0, 
        bearing=0
    )

# --- 2. SIDEBAR ---
st.sidebar.title("💎 ROI Parameters")

# Main ROI Toggles
show_prime = st.sidebar.checkbox("Show Prime Soil", value=True)
show_marginal = st.sidebar.checkbox("Show Marginal Soil", value=True)
only_irrigated = st.sidebar.toggle("Only Irrigated (Water District)", value=False)

st.sidebar.write("---")

# Address Search
address_input = st.sidebar.text_input("📍 Search by Address", placeholder="123 Main St, Visalia, CA")
if st.sidebar.button("Fly to Address") and address_input:
    try:
        geolocator = Nominatim(user_agent="agri_diamond_finder")
        location = geolocator.geocode(address_input)
        if location:
            st.session_state.view_state = pdk.ViewState(
                latitude=location.latitude, 
                longitude=location.longitude, 
                zoom=14
            )
            st.rerun()
    except:
        st.sidebar.error("Address not found. Try adding the city or zip code.")

# APN Jump (Global Search)
search_apn = st.sidebar.selectbox("Jump to APN", options=[""] + sorted(df_all['APN'].unique().tolist()))
if search_apn:
    t = df_all[df_all['APN'] == search_apn].iloc[0]
    st.session_state.view_state = pdk.ViewState(latitude=t['lat'], longitude=t['lon'], zoom=15)

# --- 3. DYNAMIC LAYER STYLING ---
# Unique ID forces a refresh when filters change
layer_id = f"ag_layer_{show_prime}_{show_marginal}_{only_irrigated}"

# C_ID 1: Green, 2: Yellow, 3: Red
r_js = "properties.C_ID == 1 ? 34 : (properties.C_ID == 2 ? 245 : 239)"
g_js = "properties.C_ID == 1 ? 197 : (properties.C_ID == 2 ? 158 : 68)"
b_js = "properties.C_ID == 1 ? 94 : (properties.C_ID == 2 ? 11 : 68)"

# Filtering Logic
v_parts = []
if show_prime:
    v_parts.append("properties.C_ID == 1")
    if not only_irrigated: v_parts.append("properties.C_ID == 2")
if show_marginal and not only_irrigated: 
    v_parts.append("properties.C_ID == 3")

logic_chain = " || ".join(v_parts) if v_parts else "false"
alpha_js = f"({logic_chain}) ? 100 : 0"

# --- 4. MAP COMPONENT ---
layer = pdk.Layer(
    "MVTLayer",
    data="http://localhost:8000/tiles/{z}/{x}/{y}.pbf",
    id=layer_id,
    pickable=True,
    auto_highlight=True,
    # --- ADD THESE TWO LINES ---
    min_zoom=6, 
    max_zoom=14,
    # ---------------------------
    highlight_color=[255, 255, 255, 80],
    get_fill_color=f"[{r_js}, {g_js}, {b_js}, {alpha_js}]",
    get_line_color=[255, 255, 255, 30], 
    line_width_min_pixels=1,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=st.session_state.view_state,
    map_style="mapbox://styles/mapbox/satellite-v9",
    tooltip={
        "html": """
            <div style="font-family: sans-serif; padding: 5px;">
                <b>APN:</b> {APN}<br/>
                <b>County:</b> {County}<br/>
                <b>Size:</b> {Acres} acres<br/>
                <hr style="margin: 5px 0; border: 0; border-top: 1px solid #555;">
                <b>Soil Quality:</b> {S_Bin} (1=Prime, 0=Marginal)<br/>
                <b>Water Access:</b> {W_Dist} (1=Yes, 0=No)
            </div>
        """,
        "style": {"color": "white", "backgroundColor": "#1e1e1e", "border": "1px solid #444"}
    }
)

# Render and catch selection
event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

# --- 5. HANDLE CLICK-TO-ZOOM ---
if event and "selection" in event and event["selection"]["objects"]:
    all_selected = event["selection"]["objects"]
    # Extract object from the dynamic layer_id key
    first_layer_objects = list(all_selected.values())[0]
    
    if first_layer_objects:
        selected_obj = first_layer_objects[0]
        apn_clicked = str(selected_obj.get("APN"))
        
        # Cross-ref for zoom coords
        match = df_all[df_all['APN'] == apn_clicked]
        if not match.empty:
            st.session_state.view_state = pdk.ViewState(
                latitude=match.iloc[0]['lat'], 
                longitude=match.iloc[0]['lon'], 
                zoom=15,
                pitch=0,
                bearing=0
            )
            st.rerun()

st.caption(f"Analyzing {len(df_all):,} agricultural parcels for ROI diamonds.")
