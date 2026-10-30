#!/usr/bin/env python3
"""Render a validated cinematic scene plan to a frame-based MP4 preview."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.video.cinematic_map import CinematicMapError, load_scene
from app.video.cinematic_mp4 import CinematicMP4Error, render_cinematic_mp4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path, help="Validated scene-plan JSON")
    parser.add_argument("--output", required=True, type=Path, help="Output MP4 path")
    parser.add_argument("--fps", type=int, default=5, help="Preview frame rate, 1-12 (default: 5)")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--geojson", type=Path, help="Optional local GeoJSON Polygon/MultiPolygon overlay")
    parser.add_argument("--basemap-attribution", help="Visible attribution required with --geojson")
    parser.add_argument("--basemap-license", help="License statement required with --geojson; not independently verified")
    parser.add_argument("--basemap-source-url", help="HTTPS source URL required with --geojson")
    args = parser.parse_args()
    try:
        scene = load_scene(args.scene)
        output = render_cinematic_mp4(
            scene, args.output, fps=args.fps, overwrite=args.overwrite,
            timeout_seconds=args.timeout_seconds, geojson_path=args.geojson,
            basemap_attribution=args.basemap_attribution,
            basemap_license=args.basemap_license,
            basemap_source_url=args.basemap_source_url,
        )
    except (CinematicMapError, CinematicMP4Error, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "render": "PASS",
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "duration_seconds": scene["duration_seconds"],
        "fps": args.fps,
        "frames": scene["duration_seconds"] * args.fps,
        "map_mode": "geojson_overlay" if args.geojson else "schematic",
        "map_notice": (
            "GEOGRAPHIC BOUNDARIES overlay; supplied attribution/license/source are visible but not independently verified."
            if args.geojson else "SCHEMATIC MAP • NOT TO SCALE"
        ),
        "basemap_metadata": ({
            "attribution": args.basemap_attribution,
            "license": args.basemap_license,
            "source_url": args.basemap_source_url,
            "independently_verified": False,
        } if args.geojson else None),
        "visual_notice": "Geographic overlay is generalized and requires human visual/legal review." if args.geojson else "Schematic map preview, not to scale; factual accuracy requires human review.",
        "audio_note": "Visuals-only MP4. Use scripts/render_video.py to mux separately reviewed narration and SRT subtitles.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
