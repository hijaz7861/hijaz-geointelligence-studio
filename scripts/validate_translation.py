#!/usr/bin/env python3
"""Check that a translated script preserves claim markers and source URLs."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.editorial.translation_validator import TranslationValidationError, validate_translation

def main() -> int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source',required=True,type=Path)
 parser.add_argument('--translated',required=True,type=Path)
 parser.add_argument('--language',required=True,choices=('ur','en','ru','zh'))
 args=parser.parse_args()
 try:
  source=args.source.read_text(encoding='utf-8'); translated=args.translated.read_text(encoding='utf-8')
  report=validate_translation(source,translated,language=args.language)
 except (TranslationValidationError,OSError,UnicodeError) as exc:
  print(f'ERROR: {exc}',file=sys.stderr); return 2
 print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
