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

layer_id = "test_layer_v100"

r_js = "properties.C_ID == 1 ? 34 : (properties.C_ID == 2 ? 245 : 239)"
g_js = "properties.C_ID == 1 ? 197 : (properties.C_ID == 2 ? 158 : 68)"
b_js = "properties.C_ID == 1 ? 94 : (properties.C_ID == 2 ? 11 : 68)"

v_parts = []
if show_prime:
    v_parts.append("properties.C_ID == 1")
    if not only_irrigated: v_parts.append("properties.C_ID == 2")
if show_marginal and not only_irrigated: 
    v_parts.append("properties.C_ID == 3")

logic_chain = " || ".join(v_parts) if v_parts else "false"
alpha_js = f"({logic_chain}) ? 100 : 0"

    
layer = pdk.Layer(
    "TileLayer",
    data="https://raw.githubusercontent.com/andrewphankt/farmland-roi/main/static/tiles/{z}/{x}/{y}.pbf",
    id="parcel-tile-layer",
    # This bypasses the broken MVT worker entirely
    loaders=["https://unpkg.com/@loaders.gl/mvt@3.4.4/dist/mvt-loader.umd.js"],
    get_tile_data=None, # Let deck.gl handle the fetch
    
    # We tell deck.gl how to render each tile manually
    render_sub_layers=f"""
        new GeoJsonLayer(props, {{
            id: props.id + '-geojson',
            data: props.data,
            getFillColor: [{r_js}, {g_js}, {b_js}, {alpha_js}],
            getLineColor: [255, 255, 255, 50],
            lineWidthMinPixels: 1,
            pickable: true
        }})
    """,
    pickable=True,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=st.session_state.view_state,
    map_style=None,
    api_keys={"mapbox": st.secrets["MAPBOX_API_KEY"]},
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

event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object")

if event and "selection" in event and event["selection"]["objects"]:
    all_selected = event["selection"]["objects"]
    if all_selected:
        first_layer_objects = next(iter(all_selected.values()))
        if first_layer_objects:
            selected_obj = first_layer_objects[0]
            apn_clicked = str(selected_obj.get("APN"))
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

st.caption(f"Analyzing {len(df_all):,} agricultural parcels.")
