#!/bin/sh
# Repeatable local validation; intentionally avoids GitHub Actions minutes.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON=${PYTHON:-python3}
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM
printf '\n[1/12] Unit tests\n'
"$PYTHON" -m unittest discover -s tests -v
printf '\n[2/12] Syntax compilation\n'
"$PYTHON" -m compileall -q app scripts tests
printf 'PASS: compileall\n'
printf '\n[3/12] CLI help\n'
"$PYTHON" scripts/add_source.py --help > "$TMP_DIR/help.txt"
grep -q -- '--published-at' "$TMP_DIR/help.txt"
"$PYTHON" scripts/add_claim.py --help > "$TMP_DIR/claim-help.txt"
grep -q -- '--source-url' "$TMP_DIR/claim-help.txt"
"$PYTHON" scripts/validate_project.py --help > "$TMP_DIR/project-help.txt"
grep -q -- '--project' "$TMP_DIR/project-help.txt"
"$PYTHON" scripts/validate_srt.py --help > "$TMP_DIR/srt-help.txt"
grep -q -- '--max-chars-per-line' "$TMP_DIR/srt-help.txt"
"$PYTHON" scripts/render_video.py --help > "$TMP_DIR/render-help.txt"
grep -q -- '--subtitles' "$TMP_DIR/render-help.txt"
"$PYTHON" scripts/build_cited_draft.py --help > "$TMP_DIR/draft-help.txt"
grep -q -- '--claims-file' "$TMP_DIR/draft-help.txt"
"$PYTHON" scripts/build_release_metadata.py --help > "$TMP_DIR/metadata-help.txt"
grep -q -- '--project' "$TMP_DIR/metadata-help.txt"
"$PYTHON" scripts/generate_narration.py --help > "$TMP_DIR/narration-help.txt"
grep -q -- '--text-file' "$TMP_DIR/narration-help.txt"
printf 'PASS: all CLI help screens\n'
printf '\n[4/12] Source CLI add + duplicate rejection smoke test\n'
"$PYTHON" scripts/add_source.py \
  --title 'Validation fixture' \
  --url 'https://example.org/validation-fixture' \
  --published-at '2026-10-20' \
  --source-type independent_reporting \
  --claim-status independent_reporting \
  --notes 'Synthetic test fixture; not a factual claim.' \
  --ledger "$TMP_DIR/sources.json" > "$TMP_DIR/add.json"
if "$PYTHON" scripts/add_source.py \
  --title 'Validation fixture duplicate' \
  --url 'HTTPS://EXAMPLE.ORG/validation-fixture/' \
  --published-at '2026-10-20' \
  --source-type independent_reporting \
  --claim-status independent_reporting \
  --notes 'Synthetic duplicate test fixture.' \
  --ledger "$TMP_DIR/sources.json" > "$TMP_DIR/duplicate.out" 2> "$TMP_DIR/duplicate.err"; then
  printf 'FAIL: duplicate URL was accepted\n' >&2
  exit 1
fi
grep -q 'already exists' "$TMP_DIR/duplicate.err"
printf 'PASS: source add and duplicate rejection\n'
printf '\n[5/12] Claim CLI source-link validation smoke test\n'
"$PYTHON" scripts/add_claim.py --claim 'Validation claim' --status independent_reporting --source-url 'https://example.org/validation-fixture' --notes 'Synthetic fixture only.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null
if "$PYTHON" scripts/add_claim.py --claim 'Unlinked claim' --status analysis --source-url 'https://example.org/missing' --notes 'Must fail.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null 2> "$TMP_DIR/claim.err"; then
  printf 'FAIL: claim with unknown source was accepted\n' >&2
  exit 1
fi
grep -q 'absent from the source ledger' "$TMP_DIR/claim.err"
printf 'PASS: claim add and unknown-source rejection\n'
printf '\n[6/12] Project package and release gate smoke test\n'
"$PYTHON" scripts/validate_project.py --project data/projects/sample_project.json --sources-file "$TMP_DIR/empty-sources.json" --claims-file "$TMP_DIR/empty-claims.json" > "$TMP_DIR/project.json"
grep -q '"structural_validation": "PASS"' "$TMP_DIR/project.json"
grep -q '"publish_ready": false' "$TMP_DIR/project.json"
grep -q 'Human approval missing' "$TMP_DIR/project.json"
printf 'PASS: sample validates structurally and remains blocked from publishing\n'
printf '\n[7/12] Subtitle parser and CLI smoke test\n'
cat > "$TMP_DIR/captions.srt" <<'SRT'
1
00:00:00,000 --> 00:00:01,500
Synthetic subtitle fixture.

2
00:00:01,600 --> 00:00:03,000
Second test line.
SRT
"$PYTHON" scripts/validate_srt.py "$TMP_DIR/captions.srt" > "$TMP_DIR/subtitles.json"
grep -q '"validation": "PASS"' "$TMP_DIR/subtitles.json"
grep -q '"cue_count": 2' "$TMP_DIR/subtitles.json"
printf 'PASS: SRT validation CLI\n'

if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  printf '\n[8/12] Optional FFmpeg end-to-end smoke render\n'
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'color=c=blue:s=320x240:r=25:d=1' -t 1 -an -c:v libx264 -pix_fmt yuv420p -y "$TMP_DIR/source.mp4"
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'sine=frequency=440:duration=0.8' -c:a pcm_s16le -y "$TMP_DIR/voice-narration.wav"
  cat > "$TMP_DIR/render.srt" <<'SRT'
1
00:00:00,100 --> 00:00:00,700
Synthetic render test.
SRT
  "$PYTHON" scripts/render_video.py --video "$TMP_DIR/source.mp4" --audio "$TMP_DIR/voice-narration.wav" --subtitles "$TMP_DIR/render.srt" --output "$TMP_DIR/final.mp4" > "$TMP_DIR/render.json"
  grep -q '"render": "PASS"' "$TMP_DIR/render.json"
  ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$TMP_DIR/final.mp4" > "$TMP_DIR/streams.txt"
  grep -q 'video' "$TMP_DIR/streams.txt"
  grep -q 'audio' "$TMP_DIR/streams.txt"
  grep -q 'subtitle' "$TMP_DIR/streams.txt"
  printf 'PASS: real MP4 render contains video, audio, and subtitle streams\n'
else
  printf '\nSKIP: FFmpeg integration render (ffmpeg and/or ffprobe not installed)\n'
fi

printf '\n[9/12] Cited draft generation smoke test\n'
"$PYTHON" scripts/build_cited_draft.py --title 'Validation fixture documentary' --language en --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" --output "$TMP_DIR/draft.md" > "$TMP_DIR/draft.out"
grep -q '\[\[claim:Validation claim\]\]' "$TMP_DIR/draft.md"
grep -q 'https://example.org/validation-fixture' "$TMP_DIR/draft.md"
grep -q 'HUMAN REVIEW REQUIRED' "$TMP_DIR/draft.out"
printf 'PASS: generated draft includes tracked claim and source URL\n'

printf '\n[10/12] Release metadata draft smoke test\n'
"$PYTHON" scripts/build_release_metadata.py --project data/projects/sample_project.json --sources-file "$TMP_DIR/empty-sources.json" --claims-file "$TMP_DIR/empty-claims.json" --output "$TMP_DIR/metadata.json" > "$TMP_DIR/metadata.out"
grep -q '"publish_ready": false' "$TMP_DIR/metadata.json"
grep -q '"release_status": "draft_blocked"' "$TMP_DIR/metadata.json"
grep -q 'never uploads or publishes' "$TMP_DIR/metadata.json"
printf 'PASS: metadata is generated as blocked draft; no publishing action exists\n'

printf '\n[11/12] End-to-end source-to-draft-to-release-check smoke test\n'
"$PYTHON" - "$TMP_DIR/draft.md" "$TMP_DIR/e2e-project.json" <<'PY'
import json
import sys
from pathlib import Path
draft_path, project_path = map(Path, sys.argv[1:3])
project = {
    "project_id": "synthetic-e2e-fixture",
    "title": "Synthetic end-to-end fixture",
    "language": "en",
    "target_duration_seconds": 60,
    "script": draft_path.read_text(encoding="utf-8"),
    "claim_ids": ["Validation claim"],
    "media_assets": [],
    "approval": {
        "script_reviewed": False,
        "translation_reviewed": False,
        "media_rights_reviewed": False,
        "final_video_reviewed": False,
        "approved_by": ""
    }
}
project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
"$PYTHON" scripts/validate_project.py --project "$TMP_DIR/e2e-project.json" --sources-file "$TMP_DIR/sources.json" --claims-file "$TMP_DIR/claims.json" > "$TMP_DIR/e2e-validation.json"
grep -q '"structural_validation": "PASS"' "$TMP_DIR/e2e-validation.json"
grep -q '"publish_ready": false' "$TMP_DIR/e2e-validation.json"
"$PYTHON" scripts/build_release_metadata.py --project "$TMP_DIR/e2e-project.json" --sources-file "$TMP_DIR/sources.json" --claims-file "$TMP_DIR/claims.json" --output "$TMP_DIR/e2e-metadata.json" > "$TMP_DIR/e2e-metadata.out"
grep -q 'https://example.org/validation-fixture' "$TMP_DIR/e2e-metadata.json"
grep -q '"publish_ready": false' "$TMP_DIR/e2e-metadata.json"
printf 'PASS: source -> claim -> cited draft -> project validator -> blocked metadata package\n'

if command -v espeak-ng >/dev/null 2>&1 || command -v espeak >/dev/null 2>&1; then
  printf '\n[12/12] Optional offline narration smoke test\n'
  printf 'Synthetic narration test.\n' > "$TMP_DIR/narration.txt"
  "$PYTHON" scripts/generate_narration.py --text-file "$TMP_DIR/narration.txt" --language en --output "$TMP_DIR/voice-narration.wav" > "$TMP_DIR/voice-narration.json"
  grep -q '"narration": "PASS"' "$TMP_DIR/voice-narration.json"
  test -s "$TMP_DIR/voice-narration.wav"
  printf 'PASS: offline English WAV narration generated\n'
else
  printf '\nSKIP: offline narration test (eSpeak not installed)\n'
fi

printf '\nALL LOCAL VALIDATION CHECKS PASSED\n'
