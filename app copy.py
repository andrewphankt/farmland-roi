import streamlit as st
import pydeck as pdk
import pandas as pd

# Set page to wide mode for the best map experience
st.set_page_config(layout="wide", page_title="Agri-Diamond ROI Engine")

# --- 1. DATA LOADING ---
@st.cache_data(persist="disk")
def load_index():
    return pd.read_csv("search_index.csv", dtype={'APN': str, 'S_Class': str, 'W_Dist': str})

try:
    df_search = load_index()
except:
    st.error("Search index not found. Please run the bake process.")
    st.stop()

# --- 2. SIDEBAR ---
st.sidebar.title("💎 ROI Parameters")
show_prime = st.sidebar.checkbox("Show Prime Soil (Green/Yellow)", value=True)
show_marginal = st.sidebar.checkbox("Show Marginal Soil (Red)", value=True)
st.sidebar.write("---")
only_irrigated = st.sidebar.toggle("Only Show Irrigated Parcels", value=False)

search_apn = st.sidebar.selectbox(
    "Jump to APN", 
    options=[""] + sorted(df_search['APN'].unique().tolist())
)

# --- 3. DYNAMIC STYLING LOGIC ---
# Colors: 1=Green, 2=Yellow, 3=Red
r_js = "properties.C_ID == 1 ? 34 : (properties.C_ID == 2 ? 245 : 239)"
g_js = "properties.C_ID == 1 ? 197 : (properties.C_ID == 2 ? 158 : 68)"
b_js = "properties.C_ID == 1 ? 94 : (properties.C_ID == 2 ? 11 : 68)"

# Visibility Logic
v_parts = []
if show_prime:
    v_parts.append("properties.C_ID == 1")
    if not only_irrigated:
        v_parts.append("properties.C_ID == 2")
if show_marginal and not only_irrigated:
    v_parts.append("properties.C_ID == 3")

# Construct the logic chain for alpha channels
logic_chain = " || ".join(v_parts) if v_parts else "false"

# NEW UPDATE: Line Alpha now follows the visibility logic to hide 'Ghost Lines'
alpha_js = f"({logic_chain}) ? (properties.isHovered ? 230 : 80) : 0"
line_alpha_js = f"({logic_chain}) ? 40 : 0"

# --- 4. VIEW STATE ---
view = pdk.ViewState(latitude=36.3, longitude=-119.3, zoom=9)
if search_apn:
    t = df_search[df_search['APN'] == search_apn].iloc[0]
    view = pdk.ViewState(latitude=t['lat'], longitude=t['lon'], zoom=15)

# --- 5. THE LAYER ---
layer = pdk.Layer(
    "MVTLayer",
    data="http://localhost:8000/tiles/{z}/{x}/{y}.pbf",
    id="ag_layer",
    pickable=True,
    auto_highlight=True,
    get_fill_color=f"[{r_js}, {g_js}, {b_js}, {alpha_js}]",
    # Updated: Line color is now dynamic
    get_line_color=f"[255, 255, 255, {line_alpha_js}]",
    line_width_min_pixels=1,
    update_triggers={
        "get_fill_color": [show_prime, show_marginal, only_irrigated],
        "get_line_color": [show_prime, show_marginal, only_irrigated]
    }
)

# --- 6. RENDER ---
st.pydeck_chart(pdk.Deck(
    layers=[layer], 
    initial_view_state=view, 
    map_style="mapbox://styles/mapbox/satellite-v9",
    tooltip={
        "html": """
            <div style="font-family: sans-serif; background: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #444;">
                <b style="font-size: 16px; color: #00ffcc;">APN: {APN}</b><br/>
                <hr style="margin: 8px 0; border: 0; border-top: 1px solid #555;">
                <div style="line-height: 1.6;">
                    <b>Soil Quality:</b> {S_Class}<br/>
                    <b>Irrigated:</b> {W_Dist}<br/>
                    <b>Size:</b> <span style="color: #ffcc00;">{Acres} acres</span>
                </div>
            </div>
        """,
        "style": {"color": "white", "backgroundColor": "transparent", "zIndex": 1000}
    }
), width='stretch')

# Status Indicator
if not show_prime and not show_marginal:
    st.warning("⚠️ All filters are hidden. Select a parameter in the sidebar to view parcel data.")
else:
    st.caption(f"Displaying {len(df_search):,} analyzed agricultural parcels.")
