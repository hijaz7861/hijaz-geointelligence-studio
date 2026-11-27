#!/usr/bin/env python3
"""Verify local source-snapshot hashes against a source ledger; never fetch URLs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.source_ledger import DEFAULT_LEDGER, SourceLedgerError, load_sources
from app.research.source_snapshots import (
    DEFAULT_MAX_SNAPSHOT_BYTES,
    SourceSnapshotError,
    verify_source_snapshots,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="JSON manifest; snapshot paths are relative to its directory")
    parser.add_argument("--sources-file", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--max-snapshot-bytes", type=int, default=DEFAULT_MAX_SNAPSHOT_BYTES)
    args = parser.parse_args()
    if args.max_snapshot_bytes < 1:
        parser.error("--max-snapshot-bytes must be positive")
    try:
        sources = load_sources(args.sources_file)
        report = verify_source_snapshots(
            args.manifest,
            (source["url"] for source in sources),
            max_snapshot_bytes=args.max_snapshot_bytes,
        )
    except (SourceLedgerError, SourceSnapshotError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
