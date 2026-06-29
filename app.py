import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.express as px

import setup_data
setup_data.download_tracts()
setup_data.download_fema()

st.set_page_config(page_title="Houston GIS Dashboard", layout="wide")

st.title("Houston Flood Risk & Urban Heat Dashboard")
st.markdown("Exploring flood vulnerability and urban heat patterns across Houston census tracts.")

# --- Load data ---
@st.cache_data
def load_data():
    tracts = gpd.read_file("data/harris_tracts.gpkg", engine="pyogrio")
    fema = gpd.read_file("data/fema_flood.gpkg", engine="pyogrio")

    # Reproject to same CRS
    fema = fema.to_crs(tracts.crs)

    # Spatial join — flag tracts that intersect flood zones
    flood_join = gpd.sjoin(tracts, fema[["FLD_ZONE", "geometry"]], how="left", predicate="intersects")
    
    # Summarize flood zone per tract
    flood_summary = flood_join.groupby("TRACTCE")["FLD_ZONE"].agg(
        lambda x: x.dropna().iloc[0] if x.dropna().any() else "X"
    ).reset_index()
    flood_summary.columns = ["TRACTCE", "flood_zone"]

    tracts = tracts.merge(flood_summary, on="TRACTCE", how="left")
    tracts["flood_zone"] = tracts["flood_zone"].fillna("X")

    # Assign risk score
    zone_risk = {"A": 1.0, "AE": 0.9, "AO": 0.8, "AH": 0.8, "VE": 1.0, "V": 1.0, "X": 0.1, "D": 0.5}
    tracts["flood_risk_score"] = tracts["flood_zone"].map(lambda z: zone_risk.get(z[:2] if len(z) >= 2 else z, 0.2))

    # Simulated canopy and LST (real NLCD integration coming next)
    np.random.seed(42)
    n = len(tracts)
    tracts["canopy_pct"] = np.random.uniform(5, 45, n)
    tracts["lst_c"] = 42 - (0.35 * tracts["canopy_pct"]) + np.random.normal(0, 2.5, n)

    # Simplify geometry for faster rendering
    tracts = tracts.to_crs(epsg=4326)
    tracts["geometry"] = tracts["geometry"].simplify(0.001)

    return tracts

with st.spinner("Loading spatial data..."):
    tracts = load_data()

# --- Sidebar ---
st.sidebar.header("Filters")
layer = st.sidebar.selectbox("Display Layer", ["Flood Risk", "Tree Canopy Cover (%)", "Land Surface Temp (°C)"])

# --- Metrics ---
high_risk = (tracts["flood_risk_score"] > 0.5).sum()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Tree Canopy Cover", f"{tracts['canopy_pct'].mean():.1f}%")
with col2:
    st.metric("High Flood Risk Tracts", int(high_risk))
with col3:
    st.metric("Avg Land Surface Temp", f"{tracts['lst_c'].mean():.1f}°C")

# --- Map ---
st.subheader("Map")

def get_color(value, layer):
    if layer == "Flood Risk":
        return "red" if value > 0.66 else "orange" if value > 0.33 else "green"
    elif layer == "Tree Canopy Cover (%)":
        return "green" if value > 30 else "orange" if value > 15 else "red"
    else:
        return "red" if value > 38 else "orange" if value > 34 else "green"

layer_col = {"Flood Risk": "flood_risk_score", "Tree Canopy Cover (%)": "canopy_pct", "Land Surface Temp (°C)": "lst_c"}
col = layer_col[layer]

m = folium.Map(location=[29.7604, -95.3698], zoom_start=10, tiles="CartoDB dark_matter")

for _, row in tracts.iterrows():
    if row["geometry"] is None:
        continue
    color = get_color(row[col], layer)
    folium.GeoJson(
        row["geometry"].__geo_interface__,
        style_function=lambda x, c=color: {
            "fillColor": c,
            "color": c,
            "weight": 0.5,
            "fillOpacity": 0.5
        },
        tooltip=f"Tract: {row['TRACTCE']} | {layer}: {row[col]:.2f} | Flood Zone: {row['flood_zone']}"
    ).add_to(m)

st_folium(m, width="100%", height=500)

if layer == "Flood Risk":
    st.markdown("🔴 High Risk &nbsp;&nbsp; 🟠 Medium Risk &nbsp;&nbsp; 🟢 Low Risk")
elif layer == "Tree Canopy Cover (%)":
    st.markdown("🟢 High Canopy (>30%) &nbsp;&nbsp; 🟠 Medium (15-30%) &nbsp;&nbsp; 🔴 Low (<15%)")
else:
    st.markdown("🔴 High Temp (>38°C) &nbsp;&nbsp; 🟠 Medium (34-38°C) &nbsp;&nbsp; 🟢 Low (<34°C)")

# --- Scatter Plot ---
st.subheader("Canopy Cover vs. Land Surface Temperature")

fig = px.scatter(
    tracts,
    x="canopy_pct",
    y="lst_c",
    color="flood_risk_score",
    color_continuous_scale="RdYlGn_r",
    labels={"canopy_pct": "Tree Canopy Cover (%)", "lst_c": "Land Surface Temp (°C)", "flood_risk_score": "Flood Risk"},
    title="Tree Canopy Cover vs. Land Surface Temperature (Harris County Tracts)",
    template="plotly_dark"
)
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)