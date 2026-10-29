#!/usr/bin/env python3
"""Validate a cinematic map scene JSON and render a schematic animated SVG."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.video.cinematic_map import CinematicMapError, load_scene, render_animated_svg
from app.video.geojson_overlay import GeoJSONOverlayError

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path, help="Scene-plan JSON file")
    parser.add_argument("--output", required=True, type=Path, help="Output .svg path")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--geojson", type=Path, help="Optional local GeoJSON Polygon/MultiPolygon basemap overlay")
    parser.add_argument("--basemap-attribution", help="Required visible attribution when --geojson is used")
    parser.add_argument("--basemap-license", help="Required license name when --geojson is used")
    parser.add_argument("--basemap-source-url", help="Required HTTPS source URL when --geojson is used")
    parser.add_argument("--validate-only", action="store_true", help="Validate the scene without rendering")
    args = parser.parse_args()
    try:
        scene = load_scene(args.scene)
        if not args.validate_only:
            output = render_animated_svg(scene, args.output, overwrite=args.overwrite, geojson_path=args.geojson, basemap_attribution=args.basemap_attribution, basemap_license=args.basemap_license, basemap_source_url=args.basemap_source_url)
            print(json.dumps({"status": "RENDERED_SVG", "output": str(output), "bytes": output.stat().st_size, "map_notice": "Schematic graticule only; not a geographic basemap."}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"status": "VALID", "scene_id": scene["scene_id"], "duration_seconds": scene["duration_seconds"]}, ensure_ascii=False, indent=2))
    except (CinematicMapError, GeoJSONOverlayError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
