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
        zoom=12
    )

layer = pdk.Layer(
    "MVTLayer",
    data="static/tiles/{z}/{x}/{y}.pbf",
    id="primitive-layer-v10",
    pickable=True,
    binary=False,
    load_options={
        "mvt": {
            "layers": ["all_counties_diamonds"],
            "binary": False,
            "worker": False
        }
    },
    # Use NO spaces inside these lists to avoid character-count errors
    get_fill_color=[255,0,0,150], 
    get_line_color=[255,255,255,100],
    line_width_min_pixels=1,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=st.session_state.view_state,
    map_style="mapbox://styles/mapbox/satellite-v9",
    api_keys={"mapbox": st.secrets["MAPBOX_API_KEY"]},
    tooltip={
        "html": "<b>APN:</b> {APN}",
        "style": {"color": "white", "backgroundColor": "black"}
    }
)

st.pydeck_chart(deck)
