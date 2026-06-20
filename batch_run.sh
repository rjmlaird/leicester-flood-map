#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${OUTDIR:-docs}"
mkdir -p "$OUTDIR"

run() {
  local -a cmd=("$@")
  printf 'Running:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  "${cmd[@]}"
}

run python3 scripts/calc_ward_bounds.py \
  --input-file "$OUTDIR/county-wards.geojson" \
  --output-dir "$OUTDIR"

WARD_BOUNDS_FILE="$OUTDIR/ward-bounds.json"

if [[ ! -f "$WARD_BOUNDS_FILE" ]]; then
  echo "❌ Missing ward bounds file: $WARD_BOUNDS_FILE"
  exit 1
fi

MIN_X=$(jq -r '.expanded_bounds.min_x // .original_bounds.min_x // .min_x' "$WARD_BOUNDS_FILE")
MIN_Y=$(jq -r '.expanded_bounds.min_y // .original_bounds.min_y // .min_y' "$WARD_BOUNDS_FILE")
MAX_X=$(jq -r '.expanded_bounds.max_x // .original_bounds.max_x // .max_x' "$WARD_BOUNDS_FILE")
MAX_Y=$(jq -r '.expanded_bounds.max_y // .original_bounds.max_y // .max_y' "$WARD_BOUNDS_FILE")

BOUNDS="${MIN_X},${MIN_Y},${MAX_X},${MAX_Y}"
echo "Using bounds from wards json: $BOUNDS"

run python3 scripts/read_leicester_data.py \
  --bounds="$BOUNDS" \
  --output-dir "$OUTDIR"

run python3 scripts/read_historic_data.py \
  --bounds="$BOUNDS" \
  --output-dir "$OUTDIR"

run python3 scripts/read_ea_flood_zones.py \
  --bounds="$BOUNDS" \
  --output-dir "$OUTDIR"

run python3 scripts/read_ea_flood_zones_cc.py \
  --bounds="$BOUNDS" \
  --output-dir "$OUTDIR"

echo "All scripts completed successfully."
