#!/usr/bin/env python3
"""Build a Markdown editorial fact-check report from the local ledgers."""
from __future__ import annotations
import argparse
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.editorial.fact_check_report import build_fact_check_report
from app.research.claim_ledger import DEFAULT_CLAIMS, load_claims
from app.research.source_ledger import DEFAULT_LEDGER, load_sources

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims-file", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--sources-file", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        claims = load_claims(args.claims_file, args.sources_file)
        sources = load_sources(args.sources_file)
        report = build_fact_check_report(claims, sources)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        print(f"ERROR: Output already exists (pass --overwrite): {output}", file=sys.stderr)
        return 2
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, prefix=f".{output.stem}.", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(report)
        if output.exists() and not args.overwrite:
            print(f"ERROR: Output appeared during generation; refusing to overwrite: {output}", file=sys.stderr)
            return 2
        temp_path.replace(output)
    except OSError as exc:
        print(f"ERROR: Cannot write report: {exc}", file=sys.stderr)
        return 2
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    print(f"FACT-CHECK REPORT CREATED: {output}\nHUMAN SOURCE REVIEW REQUIRED; this report does not verify truth.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
