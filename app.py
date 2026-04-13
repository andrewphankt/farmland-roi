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
        latitude=36.77, 
        longitude=-119.74, 
        zoom=10, 
        pitch=0, 
        bearing=0
    )

# --- SIDEBAR CONTROLS ---
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
    st.session_state.view_state = pdk.ViewState(latitude=float(t['lat']), longitude=float(t['lon']), zoom=15)

# --- MAP LOGIC ---
# Back to clean, standard formatting
fill_color_logic = (
    "properties.C_ID == 1 ? [34, 197, 94, {}] : "
    "properties.C_ID == 2 ? [34, 197, 94, {}] : "
    "properties.C_ID == 3 ? [234, 179, 8, {}] : "
    "[0, 0, 0, 0]"
).format(
    180 if show_prime else 0,
    180 if (show_prime and not only_irrigated) else 0,
    180 if (show_marginal and not only_irrigated) else 0
)

layer = pdk.Layer(
    "MVTLayer",
    # The official Streamlit Cloud static file path
    data="app/static/tiles/{z}/{x}/{y}.pbf", 
    id="agri-parcel-layer",
    pickable=True,
    auto_highlight=True,
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 40],
    line_width_min_pixels=0.5,
    # Adding these stops the map from requesting tiles that don't exist
    # (Adjust these numbers based on what you actually generated in your tiles folder)
    min_zoom=10, 
    max_zoom=15, 
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
