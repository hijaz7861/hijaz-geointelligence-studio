#!/usr/bin/env python3
"""Generate optional online neural narration MP3 with an explicit voice selection."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.voice.edge_tts import EdgeNarrationError, VOICE_IDS, generate_edge_narration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-file", required=True, type=Path)
    parser.add_argument("--voice", required=True, choices=sorted(VOICE_IDS))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rate", default="+0%", help="Signed percentage, e.g. +0%% or -10%%")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        text = args.text_file.read_text(encoding="utf-8")
        output = generate_edge_narration(
            text, args.voice, args.output, rate=args.rate,
            timeout_seconds=args.timeout_seconds, overwrite=args.overwrite,
        )
    except (EdgeNarrationError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "narration": "PASS",
        "provider": "edge-tts (online Microsoft Edge TTS service)",
        "voice": args.voice,
        "output": str(output),
        "size_bytes": output.stat().st_size,
        "external_processing": True,
        "note": "Narration text was sent to an online TTS service. Review pronunciation, quality, service terms, and content rights before publication.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
