#!/usr/bin/env python3
"""
Prepare historic flood data for Leaflet.js
Writes:
- historic-flood-data-original.geojson
- historic-flood-data.geojson  (EPSG:4326 for Leaflet, clipped to Leicester)
- historic-flood-summary.json
"""

import argparse
import json
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


def parse_bounds(value: str):
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bounds must be minx,miny,maxx,maxy")
    try:
        return tuple(float(p) for p in parts)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid bounds values: {e}")


def load_historic_gdf(historic_dir: Path):
    geojson_files = list(historic_dir.glob("*.geojson"))

    if not geojson_files:
        print("❌ No GeoJSON found. Extracting zip...")
        zip_file = historic_dir / "Historic_Flood_Map.geojson.zip"
        if zip_file.exists():
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(historic_dir)
            geojson_files = list(historic_dir.glob("*.geojson"))

    if geojson_files:
        return gpd.read_file(geojson_files[0])

    shp_files = list(historic_dir.glob("*.shp"))
    if shp_files:
        return gpd.read_file(shp_files[0])

    raise FileNotFoundError("No supported historic flood data file found")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bounds",
        type=parse_bounds,
        default=(-1.25, 52.58, -1.05, 52.72),
        help="Bounding box as minx,miny,maxx,miny",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/Volumes/DevProjects/data/leicester-flood-map/NDL-historic"),
        help="Directory containing historic flood source data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "../docs",
        help="Directory for output GeoJSON and summary",
    )
    parser.add_argument(
        "--assume-crs",
        default="EPSG:27700",
        help="CRS to assign if input file has none",
    )
    args = parser.parse_args()

    historic_dir = args.input_dir
    docs_dir = args.output_dir
    bounds = args.bounds

    gdf = load_historic_gdf(historic_dir)

    print(f"✅ Loaded {len(gdf)} historic flood outlines")
    print(f"📍 CRS: {gdf.crs}")
    print(f"📊 Columns: {gdf.columns.tolist()}")

    docs_dir.mkdir(parents=True, exist_ok=True)

    original_file = docs_dir / "historic-flood-data-original.geojson"
    gdf.to_file(original_file, driver="GeoJSON")
    print(f"✅ Saved original CRS file: {original_file}")
    print(f"📁 Original file size: {original_file.stat().st_size / 1024:.2f} KB")

    if gdf.crs is None:
        print(f"⚠️ No CRS set, assuming {args.assume_crs} before converting")
        gdf = gdf.set_crs(args.assume_crs)

    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    clip_box = box(*bounds)
    gdf_wgs84 = gdf_wgs84.clip(clip_box)
    gdf_wgs84 = gdf_wgs84[gdf_wgs84.geometry.notna() & ~gdf_wgs84.geometry.is_empty].copy()

    wgs84_file = docs_dir / "historic-flood-data.geojson"
    gdf_wgs84.to_file(wgs84_file, driver="GeoJSON")
    print(f"✅ Saved clipped Leaflet-ready file: {wgs84_file}")
    print(f"📁 WGS84 clipped file size: {wgs84_file.stat().st_size / 1024:.2f} KB")

    total_bounds = gdf.total_bounds if len(gdf) else [None, None, None, None]
    clipped_bounds = gdf_wgs84.total_bounds if len(gdf_wgs84) else [None, None, None, None]

    summary = {
        "total_features_original": int(len(gdf)),
        "total_features_wgs84_clipped": int(len(gdf_wgs84)),
        "geometry_type": gdf.geometry.type.unique().tolist(),
        "coordinate_system": str(gdf.crs),
        "bounding_box": {
            "min_x": float(total_bounds[0]) if total_bounds[0] is not None else None,
            "min_y": float(total_bounds[1]) if total_bounds[1] is not None else None,
            "max_x": float(total_bounds[2]) if total_bounds[2] is not None else None,
            "max_y": float(total_bounds[3]) if total_bounds[3] is not None else None,
        },
        "wgs84_coordinate_system": str(gdf_wgs84.crs),
        "wgs84_bounding_box": {
            "min_x": float(clipped_bounds[0]) if clipped_bounds[0] is not None else None,
            "min_y": float(clipped_bounds[1]) if clipped_bounds[1] is not None else None,
            "max_x": float(clipped_bounds[2]) if clipped_bounds[2] is not None else None,
            "max_y": float(clipped_bounds[3]) if clipped_bounds[3] is not None else None,
        },
        "clip_bbox_wgs84": {
            "min_x": bounds[0],
            "min_y": bounds[1],
            "max_x": bounds[2],
            "max_y": bounds[3],
        },
        "columns": gdf.columns.tolist(),
        "input_dir": str(historic_dir),
        "output_dir": str(docs_dir),
    }

    summary_file = docs_dir / "historic-flood-summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
