#!/usr/bin/env python3
"""Create a source-attributed YouTube metadata draft without publishing it."""
from __future__ import annotations
import argparse
import json
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.editorial.script_validator import validate_project_file
from app.publishing.metadata_builder import MetadataBuildError, build_metadata_package
from app.research.claim_ledger import load_claims
from app.research.source_ledger import DEFAULT_LEDGER, load_sources

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--sources-file',type=Path,default=DEFAULT_LEDGER)
    parser.add_argument('--claims-file',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    try:
        project=validate_project_file(args.project,args.claims_file,args.sources_file)
        claims=load_claims(args.claims_file,args.sources_file) if args.claims_file else load_claims(source_path=args.sources_file)
        source_urls={item['url'] for item in load_sources(args.sources_file)}
        package=build_metadata_package(project,claims,source_urls)
    except (MetadataBuildError,ValueError,OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr); return 2
    output=args.output.expanduser().resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        print(f'ERROR: Output already exists: {output}',file=sys.stderr); return 2
    temporary=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=output.parent,prefix=f'.{output.stem}.',suffix='.tmp',delete=False) as handle:
            temporary=Path(handle.name); json.dump(package,handle,ensure_ascii=False,indent=2); handle.write('\n')
        if output.exists():
            print(f'ERROR: Output appeared during generation: {output}',file=sys.stderr); return 2
        temporary.replace(output)
    except OSError as exc:
        print(f'ERROR: Cannot write metadata package: {exc}',file=sys.stderr); return 2
    finally:
        if temporary is not None and temporary.exists(): temporary.unlink()
    print(json.dumps({'created':True,'output':str(output),'publish_ready':package['publish_ready'],'release_status':package['release_status']},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
