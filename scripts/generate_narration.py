#!/usr/bin/env python3
"""Generate offline WAV narration with an installed eSpeak voice."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.voice.espeak_tts import NarrationError, generate_narration

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text-file',required=True,type=Path,help='UTF-8 narration text file')
    parser.add_argument('--language',required=True,choices=('ur','en','ru','zh'))
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--overwrite',action='store_true')
    parser.add_argument('--timeout-seconds',type=int,default=120)
    args=parser.parse_args()
    try:
        text=args.text_file.read_text(encoding='utf-8')
        output=generate_narration(text,args.language,args.output,overwrite=args.overwrite,timeout_seconds=args.timeout_seconds)
    except (NarrationError,OSError,UnicodeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr); return 2
    print(json.dumps({'narration':'PASS','language':args.language,'output':str(output),'size_bytes':output.stat().st_size,'note':'Offline synthetic voice; editor must review pronunciation and language quality.'},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
