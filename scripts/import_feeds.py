#!/usr/bin/env python3
"""Import source metadata from configured RSS/Atom feeds into the research ledger."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.research.feed_importer import DEFAULT_CONFIG, FeedImportError, import_feeds
from app.research.source_ledger import DEFAULT_LEDGER

def main() -> int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
 parser.add_argument('--ledger',type=Path,default=DEFAULT_LEDGER)
 parser.add_argument('--timeout-seconds',type=int,default=12)
 parser.add_argument('--max-items-per-feed',type=int,default=50)
 args=parser.parse_args()
 try: report=import_feeds(args.config,args.ledger,timeout_seconds=args.timeout_seconds,max_items_per_feed=args.max_items_per_feed)
 except (FeedImportError,OSError) as exc: print(f'ERROR: {exc}',file=sys.stderr); return 2
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return 1 if report['errors'] else 0
if __name__=='__main__': raise SystemExit(main())
