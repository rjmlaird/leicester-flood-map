#!/usr/bin/env python3
"""
Leicester City Flood Risk Data Reader
Reads and analyzes flood risk register data from Leicester Open Data
"""

import argparse
import json
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

warnings.filterwarnings("ignore")


def parse_bounds(value: str):
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bounds must be minx,miny,maxx,maxy")
    try:
        return tuple(float(p) for p in parts)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid bounds values: {e}")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bounds",
        type=parse_bounds,
        default=(-1.25, 52.58, -1.05, 52.72),
        help="Bounding box as minx,miny,maxx,miny",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("/Volumes/DevProjects/data/leicester-flood-map/leicester-city"),
        help="Directory containing flood risk source files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for output files",
    )
    return parser.parse_args()


def read_geojson(data_dir: Path):
    geojson_path = data_dir / "flood-risk-register-of-structures-and-features.geojson"
    print("=" * 80)
    print("READING GEOJSON FILE")
    print("=" * 80)
    print(f"File: {geojson_path}")
    print(f"Exists: {geojson_path.exists()}")

    if not geojson_path.exists():
        print("❌ Error: GeoJSON file not found!")
        return None

    gdf = gpd.read_file(geojson_path)
    print(f"\n✅ Successfully loaded {len(gdf)} structures/features")
    print(f"\n📊 Geometry Type: {gdf.geometry.type.unique()}")
    print(f"\n📍 Coordinate System: {gdf.crs}")
    return gdf


def explore_data(gdf):
    print("=" * 80)
    print("DATA EXPLORATION")
    print("=" * 80)

    print(f"\n📊 Total Records: {len(gdf)}")
    print(f"\n📐 Geometry Type: {gdf.geometry.type.unique()}")
    print(f"\n🗺️ Coordinate System: {gdf.crs}")

    print(f"\n📋 Columns ({len(gdf.columns)}):")
    for col in gdf.columns:
        dtype = gdf[col].dtype
        unique_count = gdf[col].nunique(dropna=True)
        null_count = gdf[col].isnull().sum()
        print(f"  • {col}")
        print(f"    - Type: {dtype}")
        print(f"    - Unique values: {unique_count}")
        print(f"    - Null values: {null_count}")

    print(f"\n📝 First 5 Records:")
    print(gdf.head(5).to_string())


def analyze_flood_risks(gdf):
    print("=" * 80)
    print("FLOOD RISK ANALYSIS")
    print("=" * 80)

    bounds = gdf.total_bounds
    print(f"\n📍 Spatial Distribution:")
    print(f"  - Total features: {len(gdf)}")
    print(f"  - Bounding Box:")
    print(f"    Min X (Longitude): {bounds[0]:.2f}")
    print(f"    Min Y (Latitude): {bounds[1]:.2f}")
    print(f"    Max X (Longitude): {bounds[2]:.2f}")
    print(f"    Max Y (Latitude): {bounds[3]:.2f}")

    print(f"\n🗺️ Coordinate System Info:")
    if gdf.crs:
        print(f"  - CRS: {gdf.crs}")
        print(f"  - EPSG Code: {gdf.crs.to_epsg()}")


def prepare_for_leaflet(gdf, output_dir: Path, bounds):
    print("=" * 80)
    print("PREPARING FOR LEAFLET.JS")
    print("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)

    gdf_wgs84 = gdf.copy()
    if gdf.crs is None:
        print("⚠️ No CRS set, assuming EPSG:27700 before converting")
        gdf_wgs84 = gdf_wgs84.set_crs("EPSG:27700")

    if str(gdf_wgs84.crs) != "EPSG:4326":
        print(f"\n🔄 Converting from {gdf_wgs84.crs} to EPSG:4326 (WGS84)...")
        gdf_wgs84 = gdf_wgs84.to_crs("EPSG:4326")
        print(f"✅ Converted to {gdf_wgs84.crs}")

    clip_box = box(*bounds)
    gdf_wgs84 = gdf_wgs84.clip(clip_box)
    gdf_wgs84 = gdf_wgs84[gdf_wgs84.geometry.notna() & ~gdf_wgs84.geometry.is_empty].copy()

    output_file = output_dir / "leicester-flood-data.geojson"
    print(f"\n💾 Saving to: {output_file}")
    gdf_wgs84.to_file(output_file, driver="GeoJSON")

    print(f"✅ Saved {len(gdf_wgs84)} features")
    print(f"📁 File size: {output_file.stat().st_size / 1024:.2f} KB")

    total_bounds = gdf_wgs84.total_bounds if len(gdf_wgs84) else [None, None, None, None]
    summary = {
        "total_features": int(len(gdf_wgs84)),
        "geometry_type": gdf_wgs84.geometry.type.unique().tolist(),
        "coordinate_system": str(gdf_wgs84.crs),
        "bounding_box": {
            "min_x": float(total_bounds[0]) if total_bounds[0] is not None else None,
            "min_y": float(total_bounds[1]) if total_bounds[1] is not None else None,
            "max_x": float(total_bounds[2]) if total_bounds[2] is not None else None,
            "max_y": float(total_bounds[3]) if total_bounds[3] is not None else None,
        },
        "clip_bbox_wgs84": {
            "min_x": bounds[0],
            "min_y": bounds[1],
            "max_x": bounds[2],
            "max_y": bounds[3],
        },
        "columns": gdf_wgs84.columns.tolist(),
    }

    summary_file = output_dir / "leicester-flood-summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary saved to: {summary_file}")
    return gdf_wgs84, summary


def create_visualization(gdf, output_dir: Path):
    print("=" * 80)
    print("CREATE VISUALIZATION")
    print("=" * 80)

    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(ax=ax, color="blue", alpha=0.6, edgecolor="darkblue")
    ax.set_title("Leicester Flood Risk Register", fontsize=16, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.3)

    output_dir.mkdir(parents=True, exist_ok=True)
    plot_file = output_dir / "leicester-flood-map.png"
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    print(f"✅ Plot saved to: {plot_file}")
    print(f"📁 File size: {plot_file.stat().st_size / 1024:.2f} KB")
    plt.close()


def generate_leaflet_code(summary, output_dir: Path):
    print("=" * 80)
    print("GENERATING LEAFLET.JS CODE")
    print("=" * 80)

    js_code = f"""// ============================================================================
// LEICESTER FLOOD RISK DATA - LEAFLET.JS CODE
// ============================================================================

let floodLayer;
fetch('leicester-flood-data.geojson')
  .then(response => response.json())
  .then(data => {{
    floodLayer = L.geoJSON(data, {{
      style: {{
        color: 'darkblue',
        fillColor: '#0066cc',
        fillOpacity: 0.6,
        weight: 2
      }},
      onEachFeature: function(feature, layer) {{
        let popupContent = '<strong>Leicester Flood Risk</strong><br>';
        for (let key in feature.properties) {{
          if (key !== 'geometry') {{
            popupContent += key + ': ' + feature.properties[key] + '<br>';
          }}
        }}
        layer.bindPopup(popupContent);
      }}
    }});

    floodLayer.addTo(map);
    map.fitBounds(floodLayer.getBounds());
  }})
  .catch(error => {{
    console.error('Error loading flood data:', error);
  }});

// ============================================================================
// SUMMARY DATA
// ============================================================================

const floodDataSummary = {json.dumps(summary, indent=2)};

console.log('Total flood features:', floodDataSummary.total_features);
console.log('Bounding box:', floodDataSummary.bounding_box);
"""

    output_dir.mkdir(parents=True, exist_ok=True)
    js_file = output_dir / "leaflet-flood-code.js"
    with open(js_file, "w") as f:
        f.write(js_code)

    print(f"✅ Leaflet.js code saved to: {js_file}")
    return js_code


def main():
    args = get_args()
    print("\n" + "=" * 80)
    print("LEICESTER CITY FLOOD RISK DATA READER")
    print("=" * 80 + "\n")

    print("\n📂 STEP 1: READING DATA")
    gdf = read_geojson(args.data_dir)
    if gdf is None:
        print("\n❌ Failed to load data. Exiting.")
        return

    print("\n📊 STEP 2: EXPLORING DATA")
    explore_data(gdf)

    print("\n🔍 STEP 3: ANALYZING RISKS")
    analyze_flood_risks(gdf)

    print("\n🗺️ STEP 4: PREPARING FOR LEAFLET")
    leaflet_gdf, summary = prepare_for_leaflet(gdf, args.output_dir, args.bounds)

    print("\n🎨 STEP 5: CREATE VISUALIZATION")
    create_visualization(leaflet_gdf, args.output_dir)

    print("\n💻 STEP 6: GENERATE LEAFLET CODE")
    generate_leaflet_code(summary, args.output_dir)

    print("\n" + "=" * 80)
    print("✅ ALL TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

    print("\n📁 Generated Files:")
    print(f"  • {args.output_dir / 'leicester-flood-data.geojson'}")
    print(f"  • {args.output_dir / 'leicester-flood-summary.json'}")
    print(f"  • {args.output_dir / 'leicester-flood-map.png'}")
    print(f"  • {args.output_dir / 'leaflet-flood-code.js'}")


if __name__ == "__main__":
    main()
