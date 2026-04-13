import streamlit as st
import pydeck as pdk

# Make the Streamlit app use the full width of the screen
st.set_page_config(page_title="Farmland ROI Map", layout="wide")

st.title("Farmland ROI & Marginal Soil Analysis")
st.markdown("Hover over the parcels to view soil data and ROI metrics.")

# =========================================================
# 1. COLOR LOGIC (Using S_Bin from your metadata)
# =========================================================
# S_Bin == 1 turns Red [255, 80, 80], otherwise Green [34, 139, 34]
fill_color_logic = "properties.S_Bin == 1 ? [255, 80, 80, 200] : [34, 139, 34, 100]" 

# =========================================================
# 2. MAP LAYER 
# =========================================================
layer = pdk.Layer(
    "MVTLayer",
    data="https://andrewphankt.github.io/farmland-roi/static/tiles/{z}/{x}/{y}.pbf", 
    id="agri-parcel-layer",
    min_zoom=6,
    max_zoom=14, 
    pickable=True,       
    auto_highlight=True, 
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 80],
    line_width_min_pixels=0.5,
)

# =========================================================
# 3. MAP VIEW STATE
# =========================================================
view_state = pdk.ViewState(
    latitude=36.7783,   
    longitude=-119.4179, 
    zoom=8,
    pitch=0,
)

# =========================================================
# 4. HOVER TOOLTIP (Using exact columns from metadata.json)
# =========================================================
custom_tooltip = {
    "html": """
        <div style='font-family: sans-serif;'>
            <b>APN (Parcel ID):</b> {APN} <br/>
            <b>County:</b> {County} <br/>
            <b>Acres:</b> {Acres} <br/>
            <b>Crop ID (C_ID):</b> {C_ID} <br/>
            <b>Marginal Soil (S_Bin):</b> {S_Bin} <br/>
            <b>Water Dist (W_Dist):</b> {W_Dist}
        </div>
    """,
    "style": {
        "backgroundColor": "#222222",
        "color": "white",
        "padding": "10px",
        "borderRadius": "4px",
        "boxShadow": "2px 2px 4px rgba(0,0,0,0.5)"
    }
}

# =========================================================
# 5. RENDER THE MAP
# =========================================================
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=custom_tooltip, 
    map_style="mapbox://styles/mapbox/satellite-v9" 
)

# Display the map in Streamlit
st.pydeck_chart(deck)
