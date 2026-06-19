#!/usr/bin/env python3
"""
Simple script to convert CSV/FGDB to GeoJSON without matplotlib
"""

import geopandas as gpd
from pathlib import Path
import json

# Configuration
DATA_DIR = Path(__file__).parent / "data" / "leicester-city"
OUTPUT_DIR = Path(__file__).parent / "docs"

# Read GeoJSON file
geojson_path = DATA_DIR / "flood-risk-register-of-structures-and-features.geojson"

print(f"Reading: {geojson_path}")
print(f"Exists: {geojson_path.exists()}")

if geojson_path.exists():
    # Read the file
    gdf = gpd.read_file(geojson_path)
    
    print(f"✅ Loaded {len(gdf)} features")
    print(f"📍 CRS: {gdf.crs}")
    
    # Convert to WGS84 (EPSG:4326) for Leaflet
    if gdf.crs != 'EPSG:4326':
        print(f"🔄 Converting to EPSG:4326...")
        gdf = gdf.to_crs('EPSG:4326')
    
    # Save to docs folder
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "leicester-flood-data.geojson"
    
    gdf.to_file(output_file, driver='GeoJSON')
    
    print(f"✅ Saved to: {output_file}")
    print(f"📁 File size: {output_file.stat().st_size / 1024:.2f} KB")
    
    # Create summary
    summary = {
        'total_features': len(gdf),
        'geometry_type': gdf.geometry.type.unique().tolist(),
        'coordinate_system': str(gdf.crs),
        'bounding_box': {
            'min_x': float(gdf.total_bounds[0]),
            'min_y': float(gdf.total_bounds[1]),
            'max_x': float(gdf.total_bounds[2]),
            'max_y': float(gdf.total_bounds[3])
        }
    }
    
    summary_file = OUTPUT_DIR / "leicester-flood-summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Summary saved to: {summary_file}")
else:
    print("❌ Error: GeoJSON file not found!")
    print(f"Expected location: {geojson_path}")
