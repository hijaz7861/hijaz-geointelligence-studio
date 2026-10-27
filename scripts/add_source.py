#!/usr/bin/env python3
"""Add a public source to the local research ledger."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.source_ledger import (  # noqa: E402
    CLAIM_STATUSES,
    DEFAULT_LEDGER,
    SOURCE_TYPES,
    SourceLedgerError,
    add_source,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Source/document title")
    parser.add_argument("--url", required=True, help="Absolute HTTP(S) source URL")
    parser.add_argument("--published-at", required=True, help="Publication date YYYY-MM-DD")
    parser.add_argument("--source-type", required=True, choices=sorted(SOURCE_TYPES))
    parser.add_argument("--claim-status", required=True, choices=sorted(CLAIM_STATUSES))
    parser.add_argument("--notes", required=True, help="Context, caveats, and corroboration notes")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help="Ledger JSON path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    record = {
        "title": args.title,
        "url": args.url,
        "published_at": args.published_at,
        "source_type": args.source_type,
        "claim_status": args.claim_status,
        "notes": args.notes,
    }
    try:
        add_source(record, args.ledger)
    except SourceLedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"added": True, "ledger": str(args.ledger), "source": record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
