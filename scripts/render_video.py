#!/usr/bin/env python3
"""Mux a video, narration audio, and optional SRT subtitle track using FFmpeg."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.video.ffmpeg_assembler import VideoAssemblyError, assemble_video

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path, help="Input video or visuals-only MP4")
    parser.add_argument("--audio", required=True, type=Path, help="Narration/audio file")
    parser.add_argument("--subtitles", type=Path, help="Optional SRT file to embed as a selectable subtitle track")
    parser.add_argument("--output", required=True, type=Path, help="Output MP4 path")
    parser.add_argument("--overwrite", action="store_true", help="Replace output if it already exists")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    try:
        result = assemble_video(args.video, args.audio, args.output, args.subtitles, overwrite=args.overwrite, timeout_seconds=args.timeout_seconds)
    except (VideoAssemblyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"render": "PASS", "output": str(result), "size_bytes": result.stat().st_size, "subtitle_track": args.subtitles is not None, "note": "This muxes existing media; it does not create visuals, narration, or translate captions."}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
