import geopandas as gpd
import os

os.makedirs("data", exist_ok=True)

# Houston census tracts from Census TIGER
print("Downloading census tracts...")
tracts = gpd.read_file(
    "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_48_tract.zip",
    engine="pyogrio"
)

# Filter to Harris County (FIPS 201)
houston = tracts[tracts["COUNTYFP"] == "201"].copy()
print(f"Harris County tracts: {len(houston)}")

houston.to_file("data/harris_tracts.gpkg", driver="GPKG")
print("Saved harris_tracts.gpkg")

# FEMA flood zones via ArcGIS REST API
print("Downloading FEMA flood zones...")
import requests
import json

url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0/query"
params = {
    "where": "DFIRM_ID LIKE '48201%'",
    "outFields": "FLD_ZONE,ZONE_SUBTY",
    "f": "geojson",
    "resultRecordCount": 2000
}

response = requests.get(url, params=params)
data = response.json()
print("API response keys:", list(data.keys()))

with open("data/fema_flood.geojson", "w") as f:
    json.dump(data, f)

if "features" in data and len(data["features"]) > 0:
    fema = gpd.read_file("data/fema_flood.geojson", engine="pyogrio")
    print(f"FEMA features: {len(fema)}")
    fema.to_file("data/fema_flood.gpkg", driver="GPKG")
    print("Saved fema_flood.gpkg")
else:
    print("No features returned:", data.get("error", "unknown issue"))