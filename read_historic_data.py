#!/usr/bin/env python3
"""
Prepare historic flood data for Leaflet.js
Writes:
- historic-flood-data-original.geojson
- historic-flood-data.geojson  (EPSG:4326 for Leaflet, clipped to Leicester)
- historic-flood-summary.json
"""

import json
import zipfile
from pathlib import Path

import geopandas as gpd

HISTORIC_DIR = Path("/Volumes/DevProjects/data/leicester-flood-map/NDL-historic")
DOCS_DIR = Path(__file__).parent / "docs"

LEICESTER_BBOX_WGS84 = (-1.25, 52.58, -1.05, 52.72)

def load_historic_gdf():
    geojson_files = list(HISTORIC_DIR.glob("*.geojson"))

    if not geojson_files:
        print("❌ No GeoJSON found. Extracting zip...")
        zip_file = HISTORIC_DIR / "Historic_Flood_Map.geojson.zip"
        if zip_file.exists():
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(HISTORIC_DIR)
            geojson_files = list(HISTORIC_DIR.glob("*.geojson"))

    if geojson_files:
        return gpd.read_file(geojson_files[0])

    shp_files = list(HISTORIC_DIR.glob("*.shp"))
    if shp_files:
        return gpd.read_file(shp_files[0])

    raise FileNotFoundError("No supported historic flood data file found")

gdf = load_historic_gdf()

print(f"✅ Loaded {len(gdf)} historic flood outlines")
print(f"📍 CRS: {gdf.crs}")
print(f"📊 Columns: {gdf.columns.tolist()}")

DOCS_DIR.mkdir(parents=True, exist_ok=True)

original_file = DOCS_DIR / "historic-flood-data-original.geojson"
wgs84_file = DOCS_DIR / "historic-flood-data.geojson"

gdf.to_file(original_file, driver="GeoJSON")
print(f"✅ Saved original CRS file: {original_file}")
print(f"📁 Original file size: {original_file.stat().st_size / 1024:.2f} KB")

if gdf.crs is None:
    print("⚠️ No CRS set, assuming EPSG:27700 before converting")
    gdf = gdf.set_crs("EPSG:27700")

gdf_wgs84 = gdf.to_crs("EPSG:4326")
gdf_wgs84 = gpd.clip(gdf_wgs84, LEICESTER_BBOX_WGS84)

gdf_wgs84 = gdf_wgs84[gdf_wgs84.geometry.notnull()].copy()
gdf_wgs84 = gdf_wgs84[~gdf_wgs84.geometry.is_empty].copy()

gdf_wgs84.to_file(wgs84_file, driver="GeoJSON")
print(f"✅ Saved clipped Leaflet-ready file: {wgs84_file}")
print(f"📁 WGS84 clipped file size: {wgs84_file.stat().st_size / 1024:.2f} KB")

summary = {
    "total_features_original": len(gdf),
    "total_features_wgs84_clipped": len(gdf_wgs84),
    "geometry_type": gdf.geometry.type.unique().tolist(),
    "coordinate_system": str(gdf.crs),
    "bounding_box": {
        "min_x": float(gdf.total_bounds[0]),
        "min_y": float(gdf.total_bounds[1]),
        "max_x": float(gdf.total_bounds[2]),
        "max_y": float(gdf.total_bounds[3]),
    },
    "wgs84_coordinate_system": str(gdf_wgs84.crs),
    "wgs84_bounding_box": {
        "min_x": float(gdf_wgs84.total_bounds[0]) if len(gdf_wgs84) else None,
        "min_y": float(gdf_wgs84.total_bounds[1]) if len(gdf_wgs84) else None,
        "max_x": float(gdf_wgs84.total_bounds[2]) if len(gdf_wgs84) else None,
        "max_y": float(gdf_wgs84.total_bounds[3]) if len(gdf_wgs84) else None,
    },
    "clip_bbox_wgs84": {
        "min_x": LEICESTER_BBOX_WGS84[0],
        "min_y": LEICESTER_BBOX_WGS84[1],
        "max_x": LEICESTER_BBOX_WGS84[2],
        "max_y": LEICESTER_BBOX_WGS84[3],
    },
    "columns": gdf.columns.tolist(),
}

summary_file = DOCS_DIR / "historic-flood-summary.json"
with open(summary_file, "w") as f:
    json.dump(summary, f, indent=2)

print(f"✅ Summary saved to: {summary_file}")
