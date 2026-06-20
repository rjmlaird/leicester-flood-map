#!/usr/bin/env python3
"""
Prepare Environment Agency Flood Zones for Planning (without Climate Change)
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


def load_ea_data(ea_dir: Path):
    geojson_files = list(ea_dir.glob("*.geojson"))

    if not geojson_files:
        print("❌ No GeoJSON file found. Extracting...")
        zip_file = ea_dir / "Flood_Map_for_Planning_Flood_Zones.geojson.zip"
        if zip_file.exists():
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(ea_dir)
            geojson_files = list(ea_dir.glob("*.geojson"))

    if not geojson_files:
        raise FileNotFoundError("No GeoJSON found in input directory")

    print(f"Reading: {geojson_files[0]}")
    return gpd.read_file(geojson_files[0])


def to_wgs84_clip_bounds(bounds_wgs84, src_crs):
    if str(src_crs) == "EPSG:4326":
        return bounds_wgs84
    return gpd.GeoSeries([box(*bounds_wgs84)], crs="EPSG:4326").to_crs(src_crs).total_bounds


def simplify_gdf(gdf, tolerance):
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.simplify(tolerance=tolerance, preserve_topology=True)
    return gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()


def make_geometries_valid(gdf):
    gdf = gdf.copy()
    try:
        gdf["geometry"] = gdf.geometry.make_valid()
    except Exception:
        gdf["geometry"] = gdf.geometry.buffer(0)
    return gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()


def normalize_zone_column(gdf):
    gdf = gdf.copy()
    if "flood_zone" not in gdf.columns:
        if "flood_source" in gdf.columns:
            gdf = gdf.rename(columns={"flood_source": "flood_zone"})
        elif "name" in gdf.columns:
            gdf = gdf.rename(columns={"name": "flood_zone"})
        else:
            gdf["flood_zone"] = "unknown"
    gdf["flood_zone"] = gdf["flood_zone"].fillna("unknown").astype(str)
    return gdf


def write_summary(gdf_detailed, gdf_dissolved, docs_dir, bounds_wgs84, tolerance):
    detailed_bounds = gdf_detailed.total_bounds if len(gdf_detailed) else [None, None, None, None]
    dissolved_bounds = gdf_dissolved.total_bounds if len(gdf_dissolved) else [None, None, None, None]

    summary = {
        "detailed_features": int(len(gdf_detailed)),
        "dissolved_features": int(len(gdf_dissolved)),
        "original_features": int(gdf_detailed.attrs.get("original_features", len(gdf_detailed))),
        "geometry_type_detailed": gdf_detailed.geometry.type.unique().tolist(),
        "geometry_type_dissolved": gdf_dissolved.geometry.type.unique().tolist(),
        "coordinate_system": str(gdf_detailed.crs),
        "simplify_tolerance": tolerance,
        "detailed_bounding_box": {
            "min_x": float(detailed_bounds[0]) if detailed_bounds[0] is not None else None,
            "min_y": float(detailed_bounds[1]) if detailed_bounds[1] is not None else None,
            "max_x": float(detailed_bounds[2]) if detailed_bounds[2] is not None else None,
            "max_y": float(detailed_bounds[3]) if detailed_bounds[3] is not None else None,
        },
        "dissolved_bounding_box": {
            "min_x": float(dissolved_bounds[0]) if dissolved_bounds[0] is not None else None,
            "min_y": float(dissolved_bounds[1]) if dissolved_bounds[1] is not None else None,
            "max_x": float(dissolved_bounds[2]) if dissolved_bounds[2] is not None else None,
            "max_y": float(dissolved_bounds[3]) if dissolved_bounds[3] is not None else None,
        },
        "columns_detailed": gdf_detailed.columns.tolist(),
        "columns_dissolved": gdf_dissolved.columns.tolist(),
        "requested_bounds_wgs84": {
            "min_x": bounds_wgs84[0],
            "min_y": bounds_wgs84[1],
            "max_x": bounds_wgs84[2],
            "max_y": bounds_wgs84[3],
        },
    }

    summary_file = docs_dir / "ea-flood-zones-summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary saved to: {summary_file}")


def compact_dissolved(dissolved, precision_grid=0.00001):
    dissolved = dissolved.copy()
    if "flood_zone" not in dissolved.columns:
        dissolved["flood_zone"] = "unknown"

    dissolved = dissolved[["flood_zone", "geometry"]].copy()

    try:
        dissolved["geometry"] = dissolved.geometry.set_precision(precision_grid)
    except Exception:
        pass

    dissolved = make_geometries_valid(dissolved)
    return dissolved[dissolved.geometry.notna() & ~dissolved.geometry.is_empty].copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bounds",
        type=parse_bounds,
        default=(-1.25, 52.55, -1.05, 52.70),
        help="Bounding box as minx,miny,maxx,maxy",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/Volumes/DevProjects/data/leicester-flood-map/ea-flood-zones"),
        help="Directory containing the EA GeoJSON/zip",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "../docs",
        help="Directory for output GeoJSON and summary",
    )
    parser.add_argument(
        "--simplify-tolerance",
        type=float,
        default=0.1,
        help="Simplification tolerance in degrees for output geometries",
    )
    parser.add_argument(
        "--precision-grid",
        type=float,
        default=0.00001,
        help="Precision grid in degrees for dissolved geometries",
    )
    parser.add_argument(
        "--geojson-precision",
        type=int,
        default=5,
        help="Coordinate precision when writing GeoJSON",
    )
    args = parser.parse_args()

    ea_dir = args.input_dir
    docs_dir = args.output_dir
    bounds_wgs84 = args.bounds
    tolerance = args.simplify_tolerance
    precision_grid = args.precision_grid
    geojson_precision = args.geojson_precision

    gdf = load_ea_data(ea_dir)

    print(f"✅ Loaded {len(gdf)} flood zone polygons")
    print(f"📍 CRS: {gdf.crs}")
    print(f"📊 Columns: {gdf.columns.tolist()}")

    if gdf.crs is None:
        raise ValueError("Input data has no CRS set")

    gdf = normalize_zone_column(gdf)

    clip_bounds = to_wgs84_clip_bounds(bounds_wgs84, gdf.crs)

    print("\n✂️ Clipping to Leicester bounds...")
    gdf_clip = gpd.clip(gdf, clip_bounds)
    gdf_clip = gdf_clip[gdf_clip.geometry.notna() & ~gdf_clip.geometry.is_empty].copy()

    print(f"\n📍 Filtered to Leicester: {len(gdf_clip)} polygons")

    if str(gdf_clip.crs) != "EPSG:4326":
        print("\n🔄 Converting clipped result to EPSG:4326...")
        gdf_clip = gdf_clip.to_crs("EPSG:4326")
        print(f"✅ Converted to {gdf_clip.crs}")

    keep_cols = [c for c in ["flood_zone", "geometry"] if c in gdf_clip.columns]
    gdf_clip = gdf_clip[keep_cols].copy()

    print(f"\n🪶 Simplifying geometries with tolerance={tolerance}...")
    gdf_clip = simplify_gdf(gdf_clip, tolerance)

    print("\n🧱 Repairing invalid geometries before dissolve...")
    gdf_clip = make_geometries_valid(gdf_clip)

    docs_dir.mkdir(parents=True, exist_ok=True)

    detailed_file = docs_dir / "ea-flood-zones-detailed.geojson"
    gdf_clip.to_file(
        detailed_file,
        driver="GeoJSON",
        coordinate_precision=geojson_precision,
    )
    print(f"\n✅ Saved detailed file to: {detailed_file}")
    print(f"📁 File size: {detailed_file.stat().st_size / 1024:.2f} KB")

    print("\n🧩 Dissolving by flood_zone...")
    dissolved = gdf_clip[["flood_zone", "geometry"]].copy()
    dissolved = dissolved.dissolve(by="flood_zone", as_index=False)
    dissolved = compact_dissolved(dissolved, precision_grid=precision_grid)

    dissolved_file = docs_dir / "ea-flood-zones.geojson"
    dissolved.to_file(
        dissolved_file,
        driver="GeoJSON",
        coordinate_precision=geojson_precision,
    )
    print(f"✅ Saved dissolved file to: {dissolved_file}")
    print(f"📁 File size: {dissolved_file.stat().st_size / 1024:.2f} KB")

    write_summary(gdf_clip, dissolved, docs_dir, bounds_wgs84, tolerance)


if __name__ == "__main__":
    main()
