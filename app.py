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
        latitude=36.77, longitude=-119.74, zoom=10
    )

st.sidebar.title("AgriParcel Index")
show_prime = st.sidebar.checkbox("Show Prime Soil", value=True)
show_marginal = st.sidebar.checkbox("Show Marginal Soil", value=True)
only_irrigated = st.sidebar.toggle("Only Irrigated", value=False)

# Logic for colors - Using Strings to avoid the "Comma" parser error
# We use RGBA strings instead of lists []
p_color = "rgba(34,197,94,0.7)" if show_prime else "rgba(0,0,0,0)"
m_color = "rgba(234,179,8,0.7)" if show_marginal else "rgba(0,0,0,0)"

# If only irrigated is on, we override the non-irrigated ones to invisible
p2_color = "rgba(0,0,0,0)" if only_irrigated else p_color
m_color_final = "rgba(0,0,0,0)" if only_irrigated else m_color

# We build the logic using string results, NOT lists
fill_color_logic = (
    f"properties.C_ID == 1 ? '{p_color}' : "
    f"properties.C_ID == 2 ? '{p2_color}' : "
    f"properties.C_ID == 3 ? '{m_color_final}' : "
    "'rgba(0,0,0,0)'"
)

layer = pdk.Layer(
    "MVTLayer",
    data="static/tiles/{z}/{x}/{y}.pbf",
    id="final-v15-nuclear",
    pickable=True,
    auto_highlight=True,
    # The external loader is still here to handle the "Type 4" data
    loaders=["https://unpkg.com/@loaders.gl/mvt@3.4.4/dist/mvt-loader.umd.js"],
    binary=False,
    load_options={
        "mvt": {
            "layers": ["all_counties_diamonds"],
            "binary": False
        }
    },
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 40],
    line_width_min_pixels=0.5,
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
