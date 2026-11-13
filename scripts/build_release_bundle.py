#!/usr/bin/env python3
"""Build a non-publishing release evidence bundle for editorial review."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.publishing.release_bundle import ReleaseBundleError, build_release_bundle, write_release_bundle
from app.research.claim_ledger import DEFAULT_CLAIMS
from app.research.source_ledger import DEFAULT_LEDGER


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--sources-file", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--claims-file", type=Path)
    parser.add_argument("--render", type=Path)
    parser.add_argument("--subtitles", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument(
        "--source-snapshots",
        type=Path,
        help="Optional offline snapshot manifest; local hashes do not authenticate sources or claims",
    )
    parser.add_argument("--min-width", type=int, default=1280)
    parser.add_argument("--min-height", type=int, default=720)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.min_width < 1 or args.min_height < 1:
        parser.error("--min-width and --min-height must be positive")

    output = args.output.expanduser().resolve()
    protected = [
        args.project.expanduser().resolve(),
        args.sources_file.expanduser().resolve(),
        (args.claims_file or DEFAULT_CLAIMS).expanduser().resolve(),
    ]
    for candidate in (args.render, args.subtitles, args.metadata, args.source_snapshots):
        if candidate is not None:
            protected.append(candidate.expanduser().resolve())
    if output in protected:
        parser.error("--output must not overwrite a project, ledger, render, subtitle, metadata, or snapshot-manifest input")

    try:
        bundle = build_release_bundle(
            args.project,
            source_path=args.sources_file,
            claims_path=args.claims_file,
            render_path=args.render,
            subtitle_path=args.subtitles,
            metadata_path=args.metadata,
            snapshot_manifest_path=args.source_snapshots,
            min_width=args.min_width,
            min_height=args.min_height,
        )
        output = write_release_bundle(bundle, args.output, overwrite=args.overwrite)
    except (ReleaseBundleError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "created": True,
        "output": str(output),
        "structural_validation": bundle["structural_validation"],
        "publish_ready": False,
        "source_snapshot_validation": bundle["source_snapshot_validation"]["validation"],
        "release_blocker_count": len(bundle["release_blockers"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
