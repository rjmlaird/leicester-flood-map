#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


def parse_margin(value: str):
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("margin must be x,y")
    try:
        return tuple(float(p) for p in parts)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid margin values: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("docs/county-wards.geojson"),
        help="Ward GeoJSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for ward-bounds.json",
    )
    parser.add_argument(
        "--margin",
        type=parse_margin,
        default=(0.01, 0.01),
        help="Margin as x,y",
    )
    args = parser.parse_args()

    ward_file = args.input_file
    outdir = args.output_dir
    margin_x, margin_y = args.margin

    if not ward_file.exists():
        raise FileNotFoundError(f"Ward file not found: {ward_file}")

    gdf = gpd.read_file(ward_file)

    if gdf.crs is None:
        raise ValueError("Ward file has no CRS set")

    if str(gdf.crs) != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    minx, miny, maxx, maxy = gdf.total_bounds

    expanded = {
        "min_x": float(minx - margin_x),
        "min_y": float(miny - margin_y),
        "max_x": float(maxx + margin_x),
        "max_y": float(maxy + margin_y),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    out_file = outdir / "ward-bounds.json"

    with open(out_file, "w") as f:
        json.dump(
            {
                "input_file": str(ward_file),
                "original_bounds": {
                    "min_x": float(minx),
                    "min_y": float(miny),
                    "max_x": float(maxx),
                    "max_y": float(maxy),
                },
                "expanded_bounds": expanded,
                "margin": {
                    "x": margin_x,
                    "y": margin_y,
                },
                "crs": str(gdf.crs),
            },
            f,
            indent=2,
        )

    print(f"Original bounds: {minx}, {miny}, {maxx}, {maxy}")
    print(
        f"Expanded bounds: {expanded['min_x']}, {expanded['min_y']}, "
        f"{expanded['max_x']}, {expanded['max_y']}"
    )
    print(f"Saved to: {out_file}")


if __name__ == "__main__":
    main()
