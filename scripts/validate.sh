#!/bin/sh
# Repeatable local validation; intentionally avoids GitHub Actions minutes.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON=${PYTHON:-python3}
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM
printf '\n[1/6] Unit tests\n'
"$PYTHON" -m unittest discover -s tests -v
printf '\n[2/6] Syntax compilation\n'
"$PYTHON" -m compileall -q app scripts tests
printf 'PASS: compileall\n'
printf '\n[3/6] CLI help\n'
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
printf 'PASS: all CLI help screens\n'
printf '\n[4/6] Source CLI add + duplicate rejection smoke test\n'
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
printf '\n[5/6] Claim CLI source-link validation smoke test\n'
"$PYTHON" scripts/add_claim.py --claim 'Validation claim' --status independent_reporting --source-url 'https://example.org/validation-fixture' --notes 'Synthetic fixture only.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null
if "$PYTHON" scripts/add_claim.py --claim 'Unlinked claim' --status analysis --source-url 'https://example.org/missing' --notes 'Must fail.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null 2> "$TMP_DIR/claim.err"; then
  printf 'FAIL: claim with unknown source was accepted\n' >&2
  exit 1
fi
grep -q 'absent from the source ledger' "$TMP_DIR/claim.err"
printf 'PASS: claim add and unknown-source rejection\n'
printf '\n[6/6] Project package and release gate smoke test\n'
"$PYTHON" scripts/validate_project.py --project data/projects/sample_project.json --sources-file "$TMP_DIR/empty-sources.json" --claims-file "$TMP_DIR/empty-claims.json" > "$TMP_DIR/project.json"
grep -q '"structural_validation": "PASS"' "$TMP_DIR/project.json"
grep -q '"publish_ready": false' "$TMP_DIR/project.json"
grep -q 'Human approval missing' "$TMP_DIR/project.json"
printf 'PASS: sample validates structurally and remains blocked from publishing\n'
printf '\n[7/7] Subtitle parser and CLI smoke test\n'
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

if command -v ffmpeg >/dev/null 2>&1; then
  printf '\n[8/8] Optional FFmpeg end-to-end smoke render\n'
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'color=c=blue:s=320x240:r=25:d=1' -t 1 -an -c:v libx264 -pix_fmt yuv420p -y "$TMP_DIR/source.mp4"
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'sine=frequency=440:duration=0.8' -c:a pcm_s16le -y "$TMP_DIR/narration.wav"
  cat > "$TMP_DIR/render.srt" <<'SRT'
1
00:00:00,100 --> 00:00:00,700
Synthetic render test.
SRT
  "$PYTHON" scripts/render_video.py --video "$TMP_DIR/source.mp4" --audio "$TMP_DIR/narration.wav" --subtitles "$TMP_DIR/render.srt" --output "$TMP_DIR/final.mp4" > "$TMP_DIR/render.json"
  grep -q '"render": "PASS"' "$TMP_DIR/render.json"
  ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$TMP_DIR/final.mp4" > "$TMP_DIR/streams.txt"
  grep -q 'video' "$TMP_DIR/streams.txt"
  grep -q 'audio' "$TMP_DIR/streams.txt"
  grep -q 'subtitle' "$TMP_DIR/streams.txt"
  printf 'PASS: real MP4 render contains video, audio, and subtitle streams\n'
else
  printf '\nSKIP: FFmpeg integration render (ffmpeg not installed)\n'
fi

printf '\nALL LOCAL VALIDATION CHECKS PASSED\n'
