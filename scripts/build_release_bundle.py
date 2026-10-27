#!/usr/bin/env python3
"""Build a non-publishing release evidence bundle for editorial review."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.publishing.release_bundle import ReleaseBundleError, build_release_bundle, write_release_bundle
from app.research.source_ledger import DEFAULT_LEDGER
def main() -> int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--project',required=True,type=Path); p.add_argument('--sources-file',type=Path,default=DEFAULT_LEDGER); p.add_argument('--claims-file',type=Path)
 p.add_argument('--render',type=Path); p.add_argument('--subtitles',type=Path); p.add_argument('--metadata',type=Path)
 p.add_argument('--min-width',type=int,default=1280); p.add_argument('--min-height',type=int,default=720)
 p.add_argument('--output',required=True,type=Path); p.add_argument('--overwrite',action='store_true')
 a=p.parse_args()
 try:
  bundle=build_release_bundle(a.project,source_path=a.sources_file,claims_path=a.claims_file,render_path=a.render,subtitle_path=a.subtitles,metadata_path=a.metadata,min_width=a.min_width,min_height=a.min_height)
  output=write_release_bundle(bundle,a.output,overwrite=a.overwrite)
 except (ReleaseBundleError,OSError,ValueError) as exc:
  print(f'ERROR: {exc}',file=sys.stderr); return 2
 print(json.dumps({'created':True,'output':str(output),'structural_validation':bundle['structural_validation'],'publish_ready':False,'release_blocker_count':len(bundle['release_blockers'])},ensure_ascii=False,indent=2))
 return 0
if __name__=='__main__': raise SystemExit(main())
