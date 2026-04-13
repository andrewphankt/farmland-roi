import streamlit as st
import pydeck as pdk

# Full screen layout
st.set_page_config(page_title="Farmland ROI Map", layout="wide")

# =========================================================
# 1. SIDEBAR & FILTERS
# =========================================================
with st.sidebar:
    st.title("Search & Filter")
    
    st.subheader("Locate Parcel")
    st.info("Note: To make search zoom work, you must load your original CSV database in the background to look up coordinates.")
    search_apn = st.text_input("Search by APN")
    search_address = st.text_input("Search by Address")
    
    st.markdown("---")
    st.subheader("Map Filters")
    show_prime = st.checkbox("Show Prime Soils", value=True)
    show_marginal = st.checkbox("Show Marginal Soils", value=True)
    only_irrigated = st.checkbox("Only Irrigated Parcels", value=False)

# =========================================================
# 2. DYNAMIC COLOR & FILTER LOGIC (JS Expressions)
# =========================================================
# We control transparency here. [R, G, B, Alpha]. 
# Alpha 80 makes them transparent by default. 0 makes them invisible (filtered out).
prime_color = "[34, 139, 34, 80]" if show_prime else "[0, 0, 0, 0]"
marginal_color = "[255, 80, 80, 80]" if show_marginal else "[0, 0, 0, 0]"

# If "Only Irrigated" is checked, we check if W_Dist == 1. Otherwise, we allow all.
irrigation_check = "properties.W_Dist == 1" if only_irrigated else "true"

# Deck.gl evaluates this JavaScript for every single parcel to determine its color
fill_color_logic = f"""
    ({irrigation_check}) ? 
        (properties.S_Bin == 1 ? {marginal_color} : {prime_color}) 
    : [0, 0, 0, 0]
"""

# =========================================================
# 3. MAP LAYER
# =========================================================
layer = pdk.Layer(
    "MVTLayer",
    data="https://andrewphankt.github.io/farmland-roi/static/tiles/{z}/{x}/{y}.pbf", 
    id="agri-parcel-layer",
    min_zoom=6,
    max_zoom=14, 
    pickable=True,       
    # auto_highlight makes the parcel turn bright, opaque white when hovered over!
    auto_highlight=True, 
    highlight_color=[255, 255, 255, 200], 
    get_fill_color=fill_color_logic,
    get_line_color=[255, 255, 255, 80],
    line_width_min_pixels=0.5,
)

view_state = pdk.ViewState(
    latitude=36.7783,   
    longitude=-119.4179, 
    zoom=8,
    pitch=0,
)

# Plain English Tooltip Translation
custom_tooltip = {
    "html": """
        <div style='font-family: sans-serif;'>
            <b>APN:</b> {APN} <br/>
            <b>Acres:</b> {Acres} <br/>
            <b>Soil Status:</b> {S_Bin} (1=Marginal, 0=Prime) <br/>
            <b>Irrigated:</b> {W_Dist} (1=Yes, 0=No)
        </div>
    """,
    "style": {
        "backgroundColor": "#222222",
        "color": "white",
        "padding": "10px",
        "borderRadius": "4px"
    }
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=custom_tooltip, 
    map_style="mapbox://styles/mapbox/satellite-v9" 
)

# =========================================================
# 4. MAIN LAYOUT & CLICK INTERACTIVITY
# =========================================================
# Split the screen: 3/4 for the map, 1/4 for the detailed info panel
map_col, info_col = st.columns([3, 1])

with map_col:
    # Requires Streamlit 1.34+. Captures clicks on the map.
    map_event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

with info_col:
    st.subheader("Parcel Details")
    
    # Check if a user clicked a parcel
    if map_event and map_event.selection and map_event.selection.get("objects"):
        # Extract the clicked parcel's data dictionary
        selected_data = map_event.selection["objects"].get("agri-parcel-layer", [])
        
        if selected_data:
            props = selected_data[0].get("properties", {})
            
            # Translate raw numbers to plain English for the sidebar
            soil_class = "Marginal" if props.get("S_Bin") == 1 else "Prime"
            is_irrigated = "Yes" if props.get("W_Dist") == 1 else "No"
            
            st.success(f"Selected APN: **{props.get('APN')}**")
            
            st.markdown(f"""
            - **Address:** *(Requires Database Link)*
            - **Owner:** *(Requires Database Link)*
            - **County:** {props.get('County')}
            - **Acres:** {props.get('Acres')}
            - **Soil Class:** {soil_class}
            - **Irrigated:** {is_irrigated}
            - **Crop ID:** {props.get('C_ID')}
            """)
            
            st.info("To enable zooming onto this specific parcel on click, you must link the background coordinate database to update Pydeck's ViewState.")
    else:
        st.write("Click on a parcel on the map to view detailed information here.")
