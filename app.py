import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Houston GIS Dashboard", layout="wide")

st.title("Houston Flood Risk & Urban Heat Dashboard")
st.markdown("Exploring flood vulnerability and urban heat patterns across Houston census tracts.")

# -- sidebar --
st.sidebar.header("Filters")
layer = st.sidebar.selectbox("Display Layer", ["Flood Risk", "Tree Canopy Cover", "Land Surface Temp"])

# -- metrics --
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Tree Canopy Cover", "18.4%")
with col2:
    st.metric("High Flood Risk Tracts", "142")
with col3:
    st.metric("Avg Land Surface Temp", "38.2°C")

# --map--
st.subheader("Map")
m = folium.Map(location=[29.7604, -95.3698], zoom_start=10, tiles="CartoDB dark_matter")

#Sample points representing census tract centroids
np.random.seed(42)
n = 80
lats = np.random.normal(29.7604, 0.15, n)
lons = np.random.normal(-95.3698, 0.18, n)
risk_scores = np.random.uniform(0, 1, n)

for lat, lon, risk in zip(lats, lons, risk_scores):
    color = "red" if risk > 0.66 else "orange" if risk > 0.33 else "green"
    folium.CircleMarker(
        location=[lat,lon],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.7,
        tooltip=f"Flood Risk Score: {risk:.2f}"
    ).add_to(m)

st_folium(m, width="100%",height=500)

# --legend--
st.markdown("🔴 High Risk &nbsp;&nbsp; 🟠 Medium Risk &nbsp;&nbsp; 🟢 Low Risk")

#--scatterplot--
st.subheader("Canopy Cover vs. Land Surface Temperature")

np.random.seed(7)
n_tracts = 100
canopy = np.random.uniform(5, 45, n_tracts)
lst = 42 - (0.35 * canopy) + np.random.normal(0, 2.5, n_tracts)

df = pd.DataFrame({
    "Canopy Cover (%)": canopy,
    "Land Surface Temp (degC)": lst,
    "Flood Risk": np.random.choice(["High", "Medium", "Low"], n_tracts)
})

fig = px.scatter(
    df,
    x="Canopy Cover (%)",
    y="Land Surface Temp (degC)",
    color="Flood Risk",
    color_discrete_map={"High": "red", "Medium": "orange", "Low": "green"},
    title="Tree Canopy Cover vs. Land Surface Temperature (Houston Census Tracts)",
    template = "plotly_dark"
)

fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)