#!/usr/bin/env python3
"""Check video/audio/subtitle streams and basic output metadata with ffprobe."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.video.render_validator import (
    VIDEO_AUDIO_COVERAGE_TOLERANCE_SECONDS,
    RenderValidationError,
    inspect_rendered_video,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument(
        "--allow-missing-audio",
        action="store_true",
        help="Permit a video without an audio stream.",
    )
    parser.add_argument("--require-subtitles", action="store_true")
    parser.add_argument(
        "--require-video-cover-audio",
        action="store_true",
        help="Require the video stream to cover every audio stream's full time interval.",
    )
    parser.add_argument(
        "--video-audio-tolerance-seconds",
        type=float,
        default=VIDEO_AUDIO_COVERAGE_TOLERANCE_SECONDS,
        help="Allowed video/audio boundary difference when coverage validation is enabled.",
    )
    parser.add_argument("--min-width", type=int, default=1)
    parser.add_argument("--min-height", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    try:
        report = inspect_rendered_video(
            args.video,
            require_audio=not args.allow_missing_audio,
            require_subtitles=args.require_subtitles,
            require_video_cover_audio=args.require_video_cover_audio,
            min_width=args.min_width,
            min_height=args.min_height,
            timeout_seconds=args.timeout_seconds,
            video_audio_tolerance_seconds=args.video_audio_tolerance_seconds,
        )
    except (RenderValidationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
