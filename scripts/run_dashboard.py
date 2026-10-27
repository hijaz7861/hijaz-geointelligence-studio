#!/usr/bin/env python3
"""Run the read-only local dashboard; binds to loopback only."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.dashboard.server import DEFAULT_PROJECT, create_server
from app.research.source_ledger import DEFAULT_LEDGER
from app.research.claim_ledger import DEFAULT_CLAIMS

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=('127.0.0.1','localhost'),default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--project',type=Path,default=DEFAULT_PROJECT)
    parser.add_argument('--sources-file',type=Path,default=DEFAULT_LEDGER)
    parser.add_argument('--claims-file',type=Path,default=DEFAULT_CLAIMS)
    args=parser.parse_args()
    try: server=create_server(args.host,args.port,args.project,args.sources_file,args.claims_file)
    except (OSError,ValueError) as exc: print(f'ERROR: {exc}',file=sys.stderr); return 2
    print(f'Read-only dashboard: http://{args.host}:{server.server_address[1]}/ (Ctrl+C to stop)')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0
if __name__=='__main__': raise SystemExit(main())
