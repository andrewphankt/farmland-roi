import streamlit as st
import pydeck as pdk
import pandas as pd
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide", page_title="AgriParcel Index")

@st.cache_data(persist="disk")
def load_index():
    return pd.read_csv("search_index.csv", dtype={'APN': str, 'C_ID': int, 'S_Bin': int, 'W_Dist': int, 'County': str})

try:
    df_all = load_index()
except Exception:
    st.error("Search index not found.")
    st.stop()

if "view_state" not in st.session_state:
    st.session_state.view_state = pdk.ViewState(
        latitude=36.3, 
        longitude=-119.3, 
        zoom=9, 
        pitch=0, 
        bearing=0
    )

st.sidebar.title("AgriParcel Index")

show_prime = st.sidebar.checkbox("Show Prime Soil", value=True)
show_marginal = st.sidebar.checkbox("Show Marginal Soil", value=True)
only_irrigated = st.sidebar.toggle("Only Irrigated (Water District)", value=False)

st.sidebar.write("---")

address_input = st.sidebar.text_input("Search by Address", placeholder="e.g. Fresno, CA")
if st.sidebar.button("Fly to Address") and address_input:
    try:
        geolocator = Nominatim(user_agent="agri_parcel_index")
        location = geolocator.geocode(address_input)
        if location:
            st.session_state.view_state = pdk.ViewState(
                latitude=location.latitude, 
                longitude=location.longitude, 
                zoom=14
            )
            st.rerun()
    except:
        st.sidebar.error("Address not found.")

search_apn = st.sidebar.selectbox("Jump to APN", options=[""] + sorted(df_all['APN'].unique().tolist()))
if search_apn:
    t = df_all[df_all['APN'] == search_apn].iloc[0]
    st.session_state.view_state = pdk.ViewState(latitude=t['lat'], longitude=t['lon'], zoom=15)

# 1. Create a simplified logic for opacity
# If the logic is complex, the "Expected Comma" error triggers.
# We will use a simple property-based opacity check.
v_parts = []
if show_prime:
    v_parts.append("properties.C_ID == 1")
    if not only_irrigated: 
        v_parts.append("properties.C_ID == 2")
if show_marginal and not only_irrigated: 
    v_parts.append("properties.C_ID == 3")

logic_chain = " || ".join(v_parts) if v_parts else "false"

layer = pdk.Layer(
    "MVTLayer",
    data="static/tiles/{z}/{x}/{y}.pbf",
    id="final_v6_no_logic_strings",
    pickable=True,
    auto_highlight=True,
    loaders=["https://unpkg.com/@loaders.gl/mvt@3.4.4/dist/mvt-loader.umd.js"],
    binary=False,
    load_options={
        "mvt": {
            "layers": ["all_counties_diamonds"],
            "binary": False,
            "worker": False
        }
    },
    # 2. We use a single color for testing to ELIMINATE the comma error.
    # Once the parcels appear, we can re-add the complex color logic.
    get_fill_color=[34, 197, 94, 150], 
    get_line_color=[255, 255, 255, 30],
    line_width_min_pixels=1,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=st.session_state.view_state,
    map_style="mapbox://styles/mapbox/satellite-v9",
    api_keys={"mapbox": st.secrets["MAPBOX_API_KEY"]},
    tooltip={
        "html": "<b>APN:</b> {APN}<br/><b>County:</b> {County}",
        "style": {"color": "white", "backgroundColor": "#1e1e1e"}
    }
)

st.pydeck_chart(deck)
st.caption(f"Analyzing {len(df_all):,} agricultural parcels.")
