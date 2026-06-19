#!/usr/bin/env python3
"""
Prepare historic flood data for Leaflet.js
"""

import geopandas as gpd
from pathlib import Path
import json

# Configuration
HISTORIC_DIR = Path(__file__).parent / "/Volumes/DevProjects/data/leicester-flood-map" / "NDL-historic"
DOCS_DIR = Path(__file__).parent / "docs"

# Find the GeoJSON file
geojson_files = list(HISTORIC_DIR.glob("*.geojson"))
if not geojson_files:
    print("❌ No GeoJSON file found. Extracting...")
    import zipfile
    zip_file = HISTORIC_DIR / "Historic_Flood_Map.geojson.zip"
    if zip_file.exists():
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(HISTORIC_DIR)
        geojson_files = list(HISTORIC_DIR.glob("*.geojson"))

if not geojson_files:
    print("❌ Still no GeoJSON found. Checking for other formats...")
    # Try SHP
    shp_files = list(HISTORIC_DIR.glob("*.shp"))
    if shp_files:
        gdf = gpd.read_file(shp_files[0])
    else:
        print("❌ No supported data format found")
        exit(1)
else:
    # Read the GeoJSON
    gdf = gpd.read_file(geojson_files[0])

print(f"✅ Loaded {len(gdf)} historic flood events")
print(f"📍 CRS: {gdf.crs}")
print(f"📊 Columns: {gdf.columns.tolist()}")

# Convert to WGS84 if needed
if gdf.crs != 'EPSG:4326':
    print(f"🔄 Converting to EPSG:4326...")
    gdf = gdf.to_crs('EPSG:4326')

# Save to docs folder
DOCS_DIR.mkdir(parents=True, exist_ok=True)
output_file = DOCS_DIR / "historic-flood-data.geojson"

gdf.to_file(output_file, driver='GeoJSON')

print(f"✅ Saved to: {output_file}")
print(f"📁 File size: {output_file.stat().st_size / 1024:.2f} KB")

# Create summary
summary = {
    'total_events': len(gdf),
    'geometry_type': gdf.geometry.type.unique().tolist(),
    'coordinate_system': str(gdf.crs),
    'bounding_box': {
        'min_x': float(gdf.total_bounds[0]),
        'min_y': float(gdf.total_bounds[1]),
        'max_x': float(gdf.total_bounds[2]),
        'max_y': float(gdf.total_bounds[3])
    },
    'columns': gdf.columns.tolist()
}

summary_file = DOCS_DIR / "historic-flood-summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Summary saved to: {summary_file}")
