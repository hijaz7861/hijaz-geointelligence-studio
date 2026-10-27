#!/usr/bin/env python3
"""Add an editorial claim linked to sources already in the source ledger."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.research.claim_ledger import ClaimLedgerError, DEFAULT_CLAIMS, add_claim
from app.research.source_ledger import DEFAULT_LEDGER

def main() -> int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--claim",required=True,help="Exact claim or statement to track")
 parser.add_argument("--status",required=True,choices=("verified_fact","official_claim","independent_reporting","analysis","unverified"))
 parser.add_argument("--source-url",required=True,action="append",help="URL already in the source ledger; repeat for multiple sources")
 parser.add_argument("--notes",required=True,help="Editorial caveat, context, or verification note")
 parser.add_argument("--claims-file",type=Path,default=DEFAULT_CLAIMS)
 parser.add_argument("--sources-file",type=Path,default=DEFAULT_LEDGER)
 args=parser.parse_args()
 try: item=add_claim({"claim":args.claim,"status":args.status,"source_urls":args.source_url,"notes":args.notes},args.claims_file,args.sources_file)
 except (ClaimLedgerError,OSError) as exc:
  print(f"ERROR: {exc}",file=sys.stderr); return 2
 print(json.dumps(item,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
