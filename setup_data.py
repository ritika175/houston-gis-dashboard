import os
import requests
import json
import geopandas as gpd

os.makedirs("data", exist_ok=True)

def download_tracts():
    if not os.path.exists("data/harris_tracts.gpkg"):
        print("Downloading census tracts...")
        tracts = gpd.read_file(
            "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_48_tract.zip",
            engine="pyogrio"
        )
        houston = tracts[tracts["COUNTYFP"] == "201"].copy()
        houston.to_file("data/harris_tracts.gpkg", driver="GPKG")
        print("Saved harris_tracts.gpkg")

def download_fema():
    if not os.path.exists("data/fema_flood.gpkg"):
        print("Downloading FEMA flood zones...")
        url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0/query"
        params = {
            "where": "DFIRM_ID LIKE '48201%'",
            "outFields": "FLD_ZONE,ZONE_SUBTY",
            "f": "geojson",
            "resultRecordCount": 2000
        }
        response = requests.get(url, params=params)
        data = response.json()
        with open("data/fema_flood.geojson", "w") as f:
            json.dump(data, f)
        fema = gpd.read_file("data/fema_flood.geojson", engine="pyogrio")
        fema.to_file("data/fema_flood.gpkg", driver="GPKG")
        print("Saved fema_flood.gpkg")

download_tracts()
download_fema()