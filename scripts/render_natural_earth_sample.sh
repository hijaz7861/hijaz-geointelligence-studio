#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="${1:-/tmp/hijaz-natural-earth-sample.svg}"
OVERWRITE_FLAG="${2:-}"
if [[ -e "$OUTPUT" && "$OVERWRITE_FLAG" != "--overwrite" ]]; then
  echo "Refusing to overwrite existing output: $OUTPUT" >&2
  echo "Choose another output path or pass --overwrite as the second argument." >&2
  exit 2
fi
ARGS=()
if [[ "$OVERWRITE_FLAG" == "--overwrite" ]]; then ARGS+=(--overwrite); fi
python3 "$ROOT_DIR/scripts/render_cinematic_map.py" \
  --scene "$ROOT_DIR/data/projects/sample_cinematic_scene.json" \
  --output "$OUTPUT" \
  --geojson "$ROOT_DIR/data/assets/natural_earth_110m_admin_0_countries.geojson" \
  --basemap-attribution "Made with Natural Earth; GeoJSON conversion by Martyn Afford" \
  --basemap-license "Public domain (Natural Earth); CC0-1.0 (GeoJSON conversion)" \
  --basemap-source-url "https://github.com/martynafford/natural-earth-geojson/blob/0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e/110m/cultural/ne_110m_admin_0_countries.json" \
  "${ARGS[@]}"
