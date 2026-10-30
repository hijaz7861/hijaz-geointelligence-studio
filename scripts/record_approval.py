#!/usr/bin/env python3
"""Record one project-bound, tamper-evident editorial approval or rejection."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.publishing.approval_receipts import APPROVAL_STAGES, ApprovalReceiptError, record_approval

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--key-file", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=APPROVAL_STAGES)
    parser.add_argument("--decision", required=True, choices=("approved", "rejected"))
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reason", required=True, help="Short human review note, 5-1000 characters")
    parser.add_argument("--artifact", type=Path, help="Required for final_video_reviewed; exact MP4 reviewed")
    args = parser.parse_args()
    try:
        result = record_approval(
            args.project, args.receipts, args.key_file,
            stage=args.stage, decision=args.decision, reviewer=args.reviewer,
            reason=args.reason, artifact_path=args.artifact,
        )
    except (ApprovalReceiptError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"recorded": True, **result}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
