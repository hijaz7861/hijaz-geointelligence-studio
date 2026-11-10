#!/usr/bin/env python3
"""Create a local 256-bit HMAC key for tamper-evident editorial approvals."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.publishing.approval_receipts import ApprovalReceiptError, create_approval_key

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Key path outside the repository, e.g. ~/.config/hijaz/approval.key")
    args = parser.parse_args()
    try:
        path = create_approval_key(args.output)
    except (ApprovalReceiptError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"created": True, "key_file": str(path), "permissions": "0600", "key_material_printed": False}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
