#!/usr/bin/env python3
"""Check video/audio/subtitle streams and basic output metadata with ffprobe."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.video.render_validator import RenderValidationError, inspect_rendered_video

def main() -> int:
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--video',required=True,type=Path); p.add_argument('--require-audio',action='store_true'); p.add_argument('--require-subtitles',action='store_true'); p.add_argument('--min-width',type=int,default=1); p.add_argument('--min-height',type=int,default=1); p.add_argument('--timeout-seconds',type=int,default=30); a=p.parse_args()
 try: report=inspect_rendered_video(a.video,require_audio=a.require_audio,require_subtitles=a.require_subtitles,min_width=a.min_width,min_height=a.min_height,timeout_seconds=a.timeout_seconds)
 except (RenderValidationError,OSError) as exc: print(f'ERROR: {exc}',file=sys.stderr); return 2
 print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
