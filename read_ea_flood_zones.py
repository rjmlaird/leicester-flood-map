#!/usr/bin/env python3
"""
Prepare Environment Agency Flood Zones for Planning (with Climate Change)
FIXED version
"""

import geopandas as gpd
from pathlib import Path
import json

# Configuration
EA_DIR = Path(__file__).parent / "data" / "ea-flood-zones"
DOCS_DIR = Path(__file__).parent / "docs"

# Find the GeoJSON file
geojson_files = list(EA_DIR.glob("*.geojson"))
if not geojson_files:
    print("❌ No GeoJSON file found. Extracting...")
    import zipfile
    zip_file = EA_DIR / "Flood_Map_for_Planning_Flood_Zones.geojson.zip"
    if zip_file.exists():
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(EA_DIR)
        geojson_files = list(EA_DIR.glob("*.geojson"))

if not geojson_files:
    print("❌ Still no GeoJSON found")
    exit(1)

# Read the GeoJSON
print(f"Reading: {geojson_files[0]}")
gdf = gpd.read_file(geojson_files[0])

print(f"✅ Loaded {len(gdf)} flood zone polygons")
print(f"📍 CRS: {gdf.crs}")
print(f"📊 Columns: {gdf.columns.tolist()}")

# Convert to WGS84 if needed
if gdf.crs != 'EPSG:4326':
    print(f"\n🔄 Converting to EPSG:4326...")
    gdf = gdf.to_crs('EPSG:4326')
    print(f"✅ Converted to {gdf.crs}")

# Filter to Leicester area (optional - reduces file size)
leicester_bounds = (-1.25, 52.55, -1.05, 52.70)

# Clip to Leicester bounding box using intersect
from shapely.geometry import box
leicester_box = box(leicester_bounds[0], leicester_bounds[1], leicester_bounds[2], leicester_bounds[3])

# Intersect with bounding box
gdf_leicester = gdf.intersection(leicester_box)

# Filter to only keep geometries that are not empty
gdf_leicester = gdf_leicester[~gdf_leicester.geometry.is_empty]

print(f"\n📍 Filtered to Leicester: {len(gdf_leicester)} polygons")

# Save to docs folder
DOCS_DIR.mkdir(parents=True, exist_ok=True)
output_file = DOCS_DIR / "ea-flood-zones.geojson"

gdf_leicester.to_file(output_file, driver='GeoJSON')

print(f"\n✅ Saved to: {output_file}")
print(f"📁 File size: {output_file.stat().st_size / 1024:.2f} KB")

# Create summary
summary = {
    'total_zones': len(gdf_leicester),
    'original_zones': len(gdf),
    'geometry_type': gdf_leicester.geometry.type.unique().tolist(),
    'coordinate_system': str(gdf_leicester.crs),
    'bounding_box': {
        'min_x': float(gdf_leicester.total_bounds[0]),
        'min_y': float(gdf_leicester.total_bounds[1]),
        'max_x': float(gdf_leicester.total_bounds[2]),
        'max_y': float(gdf_leicester.total_bounds[3])
    },
    'columns': gdf_leicester.columns.tolist()
}

summary_file = DOCS_DIR / "ea-flood-zones-summary.json"
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Summary saved to: {summary_file}")
