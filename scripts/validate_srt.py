#!/usr/bin/env python3
"""Validate SRT subtitle structure and cue timing."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.voice.srt_validator import SubtitleValidationError, analyze_readability, validate_srt_file

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subtitle", type=Path, help="Path to UTF-8 .srt file")
    parser.add_argument("--allow-overlaps", action="store_true", help="Permit overlapping cues when intentional")
    parser.add_argument("--max-chars-per-line", type=int, default=42)
    parser.add_argument("--max-cps", type=float, default=None, help="Fail if any cue exceeds this approximate characters-per-second limit")
    args = parser.parse_args()
    if args.max_chars_per_line < 1:
        parser.error("--max-chars-per-line must be positive")
    try:
        cues = validate_srt_file(
            args.subtitle,
            allow_overlaps=args.allow_overlaps,
            max_chars_per_line=args.max_chars_per_line,
        )
        readability = analyze_readability(cues, max_chars_per_second=args.max_cps)
    except SubtitleValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    over_limit = readability["over_limit_cues"]
    failed = args.max_cps is not None and bool(over_limit)
    report = {
        "file": str(args.subtitle),
        "validation": "FAIL" if failed else "PASS",
        "cue_count": len(cues),
        "duration_ms": max(c.end_ms for c in cues),
        "readability": readability,
        "note": "Structure and optional reading-speed heuristic only; this does not prove speech synchronization, translation quality, or narration quality.",
    }
    if failed:
        report["error"] = (
            f"Cue(s) {', '.join(map(str, over_limit))} exceed the "
            f"{args.max_cps:g} characters-per-second limit."
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if failed else 0
if __name__ == "__main__":
    raise SystemExit(main())
