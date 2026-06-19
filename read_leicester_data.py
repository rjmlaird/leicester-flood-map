#!/usr/bin/env python3
"""
Leicester City Flood Risk Data Reader
Reads and analyzes flood risk register data from Leicester Open Data
"""

import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path(__file__).parent / "data" / "leicester-city"
OUTPUT_DIR = Path(__file__).parent / "docs"

# ============================================================================
# 1. READ GEOJSON (RECOMMENDED FOR LEAFLET)
# ============================================================================

def read_geojson():
    """Read GeoJSON file (best for Leaflet.js mapping)"""
    geojson_path = DATA_DIR / "flood-risk-register-of-structures-and-features.geojson"
    
    print("=" * 80)
    print("READING GEOJSON FILE")
    print("=" * 80)
    print(f"File: {geojson_path}")
    print(f"Exists: {geojson_path.exists()}")
    
    if not geojson_path.exists():
        print("❌ Error: GeoJSON file not found!")
        return None
    
    # Read GeoJSON as GeoDataFrame
    gdf = gpd.read_file(geojson_path)
    
    print(f"\n✅ Successfully loaded {len(gdf)} structures/features")
    print(f"\n📊 Geometry Type: {gdf.geometry.type.unique()}")
    print(f"\n📍 Coordinate System: {gdf.crs}")
    
    return gdf

# ============================================================================
# 2. READ CSV (ALTERNATIVE FORMAT)
# ============================================================================

def read_csv():
    """Read CSV file (alternative format)"""
    csv_path = DATA_DIR / "flood-risk-register-of-structures-and-features.csv"
    
    print("=" * 80)
    print("READING CSV FILE")
    print("=" * 80)
    print(f"File: {csv_path}")
    print(f"Exists: {csv_path.exists()}")
    
    if not csv_path.exists():
        print("❌ Error: CSV file not found!")
        return None
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    print(f"\n✅ Successfully loaded {len(df)} structures/features")
    print(f"\n📊 Columns: {len(df.columns)}")
    print(f"\n📋 Column Names:")
    for col in df.columns:
        print(f"  - {col}")
    
    return df

# ============================================================================
# 3. READ PARQUET (FASTEST FORMAT)
# ============================================================================

def read_parquet():
    """Read Parquet file (fastest for large datasets)"""
    parquet_path = DATA_DIR / "flood-risk-register-of-structures-and-features.parquet"
    
    print("=" * 80)
    print("READING PARQUET FILE")
    print("=" * 80)
    print(f"File: {parquet_path}")
    print(f"Exists: {parquet_path.exists()}")
    
    if not parquet_path.exists():
        print("❌ Error: Parquet file not found!")
        return None
    
    # Read Parquet
    df = pd.read_parquet(parquet_path)
    
    print(f"\n✅ Successfully loaded {len(df)} structures/features")
    
    return df

# ============================================================================
# 4. EXPLORE DATA STRUCTURE
# ============================================================================

def explore_data(gdf):
    """Explore and analyze the data structure"""
    print("=" * 80)
    print("DATA EXPLORATION")
    print("=" * 80)
    
    # Basic statistics
    print(f"\n📊 Total Records: {len(gdf)}")
    print(f"\n📐 Geometry Type: {gdf.geometry.type.unique()}")
    print(f"\n🗺️ Coordinate System: {gdf.crs}")
    
    # Column information
    print(f"\n📋 Columns ({len(gdf.columns)}):")
    for col in gdf.columns:
        dtype = gdf[col].dtype
        unique_count = gdf[col].nunique()
        null_count = gdf[col].isnull().sum()
        print(f"  • {col}")
        print(f"    - Type: {dtype}")
        print(f"    - Unique values: {unique_count}")
        print(f"    - Null values: {null_count}")
    
    # Sample data
    print(f"\n📝 First 5 Records:")
    print(gdf.head(5).to_string())
    
    # Geometry statistics
    print(f"\n📏 Geometry Statistics:")
    if 'Polygon' in gdf.geometry.type:
        areas = gdf[gdf.geometry.type == 'Polygon'].area
        print(f"  - Min Area: {areas.min():.2f} m²")
        print(f"  - Max Area: {areas.max():.2f} m²")
        print(f"  - Mean Area: {areas.mean():.2f} m²")
    
    if 'Point' in gdf.geometry.type:
        points = gdf[gdf.geometry.type == 'Point']
        print(f"  - Total Points: {len(points)}")
        print(f"  - Bounding Box:")
        print(f"    Min X: {points.geometry.x.min():.2f}")
        print(f"    Min Y: {points.geometry.y.min():.2f}")
        print(f"    Max X: {points.geometry.x.max():.2f}")
        print(f"    Max Y: {points.geometry.y.max():.2f}")

# ============================================================================
# 5. FILTER AND ANALYZE
# ============================================================================

def analyze_flood_risks(gdf):
    """Analyze flood risk patterns"""
    print("=" * 80)
    print("FLOOD RISK ANALYSIS")
    print("=" * 80)
    
    # Count by risk type (if column exists)
    risk_col = None
    for col in ['risk_type', 'Risk Type', 'risk', 'Risk']:
        if col in gdf.columns:
            risk_col = col
            break
    
    if risk_col:
        print(f"\n🔴 Risk Type Distribution:")
        risk_counts = gdf[risk_col].value_counts()
        for risk, count in risk_counts.items():
            print(f"  • {risk}: {count} structures ({count/len(gdf)*100:.1f}%)")
    
    # Count by structure type (if column exists)
    struct_col = None
    for col in ['structure_type', 'Structure Type', 'type', 'Type']:
        if col in gdf.columns:
            struct_col = col
            break
    
    if struct_col:
        print(f"\n🏗️ Structure Type Distribution:")
        struct_counts = gdf[struct_col].value_counts()
        for struct, count in struct_counts.items():
            print(f"  • {struct}: {count} structures ({count/len(gdf)*100:.1f}%)")
    
    # Spatial distribution
    print(f"\n📍 Spatial Distribution:")
    print(f"  - Total features: {len(gdf)}")
    
    # Bounding box
    bounds = gdf.total_bounds
    print(f"  - Bounding Box:")
    print(f"    Min X (Longitude): {bounds[0]:.2f}")
    print(f"    Min Y (Latitude): {bounds[1]:.2f}")
    print(f"    Max X (Longitude): {bounds[2]:.2f}")
    print(f"    Max Y (Latitude): {bounds[3]:.2f}")
    
    print(f"\n🗺️ Coordinate System Info:")
    if gdf.crs:
        print(f"  - CRS: {gdf.crs}")
        print(f"  - EPSG Code: {gdf.crs.to_epsg()}")

# ============================================================================
# 6. PREPARE FOR LEAFLET.JS
# ============================================================================

def prepare_for_leaflet(gdf):
    """Prepare GeoJSON for Leaflet.js mapping"""
    print("=" * 80)
    print("PREPARING FOR LEAFLET.JS")
    print("=" * 80)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to WGS84 (EPSG:4326) for Leaflet
    gdf_wgs84 = gdf.copy()
    if gdf.crs != 'EPSG:4326':
        print(f"\n🔄 Converting from {gdf.crs} to EPSG:4326 (WGS84)...")
        gdf_wgs84 = gdf.to_crs('EPSG:4326')
        print(f"✅ Converted to {gdf_wgs84.crs}")
    
    # Save simplified GeoJSON
    output_file = OUTPUT_DIR / "leicester-flood-data.geojson"
    print(f"\n💾 Saving to: {output_file}")
    
    # Save GeoJSON
    gdf_wgs84.to_file(output_file, driver='GeoJSON')
    
    file_size = output_file.stat().st_size
    print(f"✅ Saved {len(gdf_wgs84)} features")
    print(f"📁 File size: {file_size / 1024:.2f} KB")
    
    # Generate summary JSON
    summary = {
        'total_features': len(gdf_wgs84),
        'geometry_type': gdf_wgs84.geometry.type.unique().tolist(),
        'coordinate_system': str(gdf_wgs84.crs),
        'bounding_box': {
            'min_x': float(gdf_wgs84.total_bounds[0]),
            'min_y': float(gdf_wgs84.total_bounds[1]),
            'max_x': float(gdf_wgs84.total_bounds[2]),
            'max_y': float(gdf_wgs84.total_bounds[3])
        },
        'columns': gdf_wgs84.columns.tolist()
    }
    
    summary_file = OUTPUT_DIR / "leicester-flood-summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Summary saved to: {summary_file}")
    
    return gdf_wgs84, summary

# ============================================================================
# 7. CREATE VISUALIZATION
# ============================================================================

def create_visualization(gdf):
    """Create a basic map visualization"""
    print("=" * 80)
    print("CREATE VISUALIZATION")
    print("=" * 80)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Plot GeoDataFrame
    gdf.plot(ax=ax, color='blue', alpha=0.6, edgecolor='darkblue')
    
    # Set title
    ax.set_title('Leicester Flood Risk Register', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Save plot
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_file = OUTPUT_DIR / "leicester-flood-map.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    
    print(f"✅ Plot saved to: {plot_file}")
    print(f"📁 File size: {plot_file.stat().st_size / 1024:.2f} KB")
    
    plt.close()

# ============================================================================
# 8. GENERATE LEAFLET.JS CODE
# ============================================================================

def generate_leaflet_code(summary):
    """Generate Leaflet.js code snippet"""
    print("=" * 80)
    print("GENERATING LEAFLET.JS CODE")
    print("=" * 80)
    
    # Build JS code as regular string (not f-string to avoid syntax error)
    js_code = """// ============================================================================
// LEICESTER FLOOD RISK DATA - LEAFLET.JS CODE
// ============================================================================

// Load flood risk data
let floodLayer;
fetch('leicester-flood-data.geojson')
  .then(response => response.json())
  .then(data => {
    floodLayer = L.geoJSON(data, {
      style: {
        color: 'darkblue',
        fillColor: '#0066cc',
        fillOpacity: 0.6,
        weight: 2
      },
      onEachFeature: function(feature, layer) {
        // Add popup with feature information
        let popupContent = '<strong>Leicester Flood Risk</strong><br>';
        
        // Add all properties to popup
        for (let key in feature.properties) {
          if (key !== 'geometry') {
            popupContent += key + ': ' + feature.properties[key] + '<br>';
          }
        }
        
        layer.bindPopup(popupContent);
      }
    });
    
    // Add layer to map
    floodLayer.addTo(map);
    
    // Fit map to data bounds
    map.fitBounds(floodLayer.getBounds());
  })
  .catch(error => {
    console.error('Error loading flood data:', error);
  });

// ============================================================================
// SUMMARY DATA
// ============================================================================

"""
    
    # Add summary as JSON
    js_code += "const floodDataSummary = " + json.dumps(summary, indent=2) + ";"
    
    js_code += """
console.log('Total flood features:', floodDataSummary.total_features);
console.log('Bounding box:', floodDataSummary.bounding_box);
"""
    
    # Save JS file
    js_file = OUTPUT_DIR / "leaflet-flood-code.js"
    with open(js_file, 'w') as f:
        f.write(js_code)
    
    print(f"✅ Leaflet.js code saved to: {js_file}")
    
    return js_code

# ============================================================================
# 9. MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("LEICESTER CITY FLOOD RISK DATA READER")
    print("=" * 80 + "\n")
    
    # Step 1: Read GeoJSON (recommended)
    print("\n📂 STEP 1: READING DATA")
    gdf = read_geojson()
    
    if gdf is None:
        print("\n❌ Failed to load data. Exiting.")
        return
    
    # Step 2: Explore data structure
    print("\n📊 STEP 2: EXPLORING DATA")
    explore_data(gdf)
    
    # Step 3: Analyze flood risks
    print("\n🔍 STEP 3: ANALYZING RISKS")
    analyze_flood_risks(gdf)
    
    # Step 4: Prepare for Leaflet
    print("\n🗺️ STEP 4: PREPARING FOR LEAFLET")
    leaflet_gdf, summary = prepare_for_leaflet(gdf)
    
    # Step 5: Create visualization
    print("\n🎨 STEP 5: CREATE VISUALIZATION")
    create_visualization(gdf)
    
    # Step 6: Generate Leaflet.js code
    print("\n💻 STEP 6: GENERATE LEAFLET CODE")
    js_code = generate_leaflet_code(summary)
    
    print("\n" + "=" * 80)
    print("✅ ALL TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    print("\n📁 Generated Files:")
    print(f"  • {OUTPUT_DIR / 'leicester-flood-data.geojson'}")
    print(f"  • {OUTPUT_DIR / 'leicester-flood-summary.json'}")
    print(f"  • {OUTPUT_DIR / 'leicester-flood-map.png'}")
    print(f"  • {OUTPUT_DIR / 'leaflet-flood-code.js'}")
    
    print("\n🚀 Next Steps:")
    print("  1. Include 'leaflet-flood-code.js' in your index.html")
    print("  2. Load the GeoJSON file in your Leaflet map")
    print("  3. Test the map in your browser")

# ============================================================================
# RUN SCRIPT
# ============================================================================

if __name__ == "__main__":
    main()
