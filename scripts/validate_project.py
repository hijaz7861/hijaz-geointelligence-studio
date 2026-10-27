#!/usr/bin/env python3
"""Validate a documentary project and print structural results and release blockers."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.editorial.script_validator import ProjectValidationError, release_blockers, validate_project_file
from app.research.claim_ledger import load_claims
from app.research.source_ledger import DEFAULT_LEDGER

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--sources-file",type=Path)
    parser.add_argument("--claims-file",type=Path)
    args=parser.parse_args()
    try:
        sources=args.sources_file or DEFAULT_LEDGER
        project=validate_project_file(args.project,args.claims_file,sources)
        claims=load_claims(args.claims_file,sources) if args.claims_file else load_claims(source_path=sources)
        blockers=release_blockers(project,claims)
        report={"project_id":project["project_id"],"structural_validation":"PASS","publish_ready":not blockers,"release_blockers":blockers,"note":"Structural validation is not factual verification or legal advice."}
    except (ProjectValidationError,ValueError,OSError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
