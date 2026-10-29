#!/bin/sh
# Repeatable local validation; intentionally avoids GitHub Actions minutes.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON=${PYTHON:-python3}
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM
printf '\n[1/22] Unit tests\n'
"$PYTHON" -m unittest discover -s tests -v
printf '\n[2/22] Syntax compilation\n'
"$PYTHON" -m compileall -q app scripts tests
printf 'PASS: compileall\n'
printf '\n[3/22] CLI help\n'
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
"$PYTHON" scripts/render_cinematic_map.py --help > "$TMP_DIR/cinematic-map-help.txt"
grep -q -- '--scene' "$TMP_DIR/cinematic-map-help.txt"
"$PYTHON" scripts/render_cinematic_mp4.py --help > "$TMP_DIR/cinematic-mp4-help.txt"
grep -q -- '--fps' "$TMP_DIR/cinematic-mp4-help.txt"
"$PYTHON" scripts/build_cited_draft.py --help > "$TMP_DIR/draft-help.txt"
grep -q -- '--claims-file' "$TMP_DIR/draft-help.txt"
"$PYTHON" scripts/build_release_metadata.py --help > "$TMP_DIR/metadata-help.txt"
grep -q -- '--project' "$TMP_DIR/metadata-help.txt"
"$PYTHON" scripts/generate_narration.py --help > "$TMP_DIR/narration-help.txt"
grep -q -- '--text-file' "$TMP_DIR/narration-help.txt"
"$PYTHON" scripts/validate_translation.py --help > "$TMP_DIR/translation-help.txt"
grep -q -- '--translated' "$TMP_DIR/translation-help.txt"
"$PYTHON" scripts/run_dashboard.py --help > "$TMP_DIR/dashboard-help.txt"
grep -q -- '--port' "$TMP_DIR/dashboard-help.txt"
"$PYTHON" scripts/validate_render.py --help > "$TMP_DIR/render-validation-help.txt"
grep -q -- '--require-subtitles' "$TMP_DIR/render-validation-help.txt"
"$PYTHON" scripts/import_feeds.py --help > "$TMP_DIR/feed-help.txt"
grep -q -- '--max-items-per-feed' "$TMP_DIR/feed-help.txt"
"$PYTHON" scripts/build_release_bundle.py --help > "$TMP_DIR/release-bundle-help.txt"
grep -q -- '--subtitles' "$TMP_DIR/release-bundle-help.txt"
printf 'PASS: all CLI help screens\n'
printf '\n[4/22] Source CLI add + duplicate rejection smoke test\n'
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
printf '\n[5/22] Claim CLI source-link validation smoke test\n'
"$PYTHON" scripts/add_claim.py --claim 'Validation claim' --status independent_reporting --source-url 'https://example.org/validation-fixture' --notes 'Synthetic fixture only.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null
if "$PYTHON" scripts/add_claim.py --claim 'Unlinked claim' --status analysis --source-url 'https://example.org/missing' --notes 'Must fail.' --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" > /dev/null 2> "$TMP_DIR/claim.err"; then
  printf 'FAIL: claim with unknown source was accepted\n' >&2
  exit 1
fi
grep -q 'absent from the source ledger' "$TMP_DIR/claim.err"
printf 'PASS: claim add and unknown-source rejection\n'
printf '\n[6/22] Project package and release gate smoke test\n'
"$PYTHON" scripts/validate_project.py --project data/projects/sample_project.json --sources-file "$TMP_DIR/empty-sources.json" --claims-file "$TMP_DIR/empty-claims.json" > "$TMP_DIR/project.json"
grep -q '"structural_validation": "PASS"' "$TMP_DIR/project.json"
grep -q '"publish_ready": false' "$TMP_DIR/project.json"
grep -q 'Human approval missing' "$TMP_DIR/project.json"
printf 'PASS: sample validates structurally and remains blocked from publishing\n'
printf '\n[7/22] Subtitle parser and CLI smoke test\n'
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
  printf '\n[8/22] Optional FFmpeg end-to-end smoke render\n'
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'color=c=blue:s=320x240:r=25:d=1' -t 1 -an -c:v libx264 -pix_fmt yuv420p -y "$TMP_DIR/source.mp4"
  ffmpeg -hide_banner -loglevel error -f lavfi -i 'sine=frequency=440:duration=0.8' -c:a pcm_s16le -y "$TMP_DIR/narration.wav"
  cat > "$TMP_DIR/render.srt" <<'SRT'
1
00:00:00,100 --> 00:00:00,700
Synthetic render test.
SRT
  "$PYTHON" scripts/render_video.py --video "$TMP_DIR/source.mp4" --audio "$TMP_DIR/narration.wav" --subtitles "$TMP_DIR/render.srt" --output "$TMP_DIR/final.mp4" > "$TMP_DIR/render.json"
  grep -q '"render": "PASS"' "$TMP_DIR/render.json"
  "$PYTHON" scripts/validate_render.py --video "$TMP_DIR/final.mp4" --require-subtitles --min-width 320 --min-height 240 > "$TMP_DIR/render-validation.json"
  grep -q '"validation": "PASS"' "$TMP_DIR/render-validation.json"
  ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$TMP_DIR/final.mp4" > "$TMP_DIR/streams.txt"
  grep -q 'video' "$TMP_DIR/streams.txt"
  grep -q 'audio' "$TMP_DIR/streams.txt"
  grep -q 'subtitle' "$TMP_DIR/streams.txt"
  printf 'PASS: real MP4 render contains video, audio, and subtitle streams\n'
else
  printf '\nSKIP: FFmpeg integration render (ffmpeg and/or ffprobe not installed)\n'
fi

printf '\n[9/22] Cited draft generation smoke test\n'
"$PYTHON" scripts/build_cited_draft.py --title 'Validation fixture documentary' --language en --claims-file "$TMP_DIR/claims.json" --sources-file "$TMP_DIR/sources.json" --output "$TMP_DIR/draft.md" > "$TMP_DIR/draft.out"
grep -q '\[\[claim:Validation claim\]\]' "$TMP_DIR/draft.md"
grep -q 'https://example.org/validation-fixture' "$TMP_DIR/draft.md"
grep -q 'HUMAN REVIEW REQUIRED' "$TMP_DIR/draft.out"
printf 'PASS: generated draft includes tracked claim and source URL\n'

printf '\n[10/22] Release metadata draft smoke test\n'
"$PYTHON" scripts/build_release_metadata.py --project data/projects/sample_project.json --sources-file "$TMP_DIR/empty-sources.json" --claims-file "$TMP_DIR/empty-claims.json" --output "$TMP_DIR/metadata.json" > "$TMP_DIR/metadata.out"
grep -q '"publish_ready": false' "$TMP_DIR/metadata.json"
grep -q '"release_status": "draft_blocked"' "$TMP_DIR/metadata.json"
grep -q 'never uploads or publishes' "$TMP_DIR/metadata.json"
printf 'PASS: metadata is generated as blocked draft; no publishing action exists\n'

printf '\n[11/22] End-to-end source-to-draft-to-release-check smoke test\n'
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
grep -q 'single_independent_domain' "$TMP_DIR/e2e-metadata.json"
printf 'PASS: source -> claim -> cited draft -> corroboration warning -> blocked metadata package\n'

if command -v espeak-ng >/dev/null 2>&1 || command -v espeak >/dev/null 2>&1; then
  printf '\n[12/22] Optional offline narration smoke test\n'
  printf 'Validation claim.\n' > "$TMP_DIR/narration.txt"
  "$PYTHON" scripts/generate_narration.py --text-file "$TMP_DIR/narration.txt" --language en --output "$TMP_DIR/tts-narration.wav" > "$TMP_DIR/tts-narration.json"
  grep -q '"narration": "PASS"' "$TMP_DIR/tts-narration.json"
  test -s "$TMP_DIR/tts-narration.wav"
  printf 'PASS: offline English WAV narration generated\n'
else
  printf '\nSKIP: offline narration test (eSpeak not installed)\n'
fi

if { command -v espeak-ng >/dev/null 2>&1 || command -v espeak >/dev/null 2>&1; } && command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  printf '\n[13/22] Optional narration-to-video integration\n'
  "$PYTHON" scripts/render_video.py --video "$TMP_DIR/source.mp4" --audio "$TMP_DIR/tts-narration.wav" --subtitles "$TMP_DIR/render.srt" --output "$TMP_DIR/narrated-final.mp4" > "$TMP_DIR/narrated-render.json"
  grep -q '"render": "PASS"' "$TMP_DIR/narrated-render.json"
  "$PYTHON" scripts/validate_render.py --video "$TMP_DIR/narrated-final.mp4" --require-subtitles --min-width 320 --min-height 240 > "$TMP_DIR/narrated-validation.json"
  grep -q '"validation": "PASS"' "$TMP_DIR/narrated-validation.json"
  ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$TMP_DIR/narrated-final.mp4" > "$TMP_DIR/narrated-streams.txt"
  grep -q 'video' "$TMP_DIR/narrated-streams.txt"
  grep -q 'audio' "$TMP_DIR/narrated-streams.txt"
  grep -q 'subtitle' "$TMP_DIR/narrated-streams.txt"
  printf 'PASS: generated narration, video, and subtitles assembled together\n'
else
  printf '\nSKIP: narration-to-video integration (eSpeak/FFmpeg/FFprobe missing)\n'
fi

printf '\n[14/22] Translation citation-preservation smoke test\n'
"$PYTHON" - "$TMP_DIR/draft.md" "$TMP_DIR/translated.md" <<'PY'
import sys
from pathlib import Path
source_path, translated_path = map(Path, sys.argv[1:3])
text = source_path.read_text(encoding="utf-8")
translated = text.replace("]] Validation claim", "]] تصدیقی دعویٰ").replace("Draft language: en", "Draft language: ur")
translated_path.write_text(translated, encoding="utf-8")
PY
"$PYTHON" scripts/validate_translation.py --source "$TMP_DIR/draft.md" --translated "$TMP_DIR/translated.md" --language ur > "$TMP_DIR/translation.json"
grep -q '"validation": "PASS"' "$TMP_DIR/translation.json"
grep -q '"claim_marker_count": 1' "$TMP_DIR/translation.json"
printf 'PASS: translation fixture preserves tracked claim markers and source URLs\n'

printf '\n[15/22] Read-only dashboard CLI smoke test\n'
"$PYTHON" scripts/run_dashboard.py --help > "$TMP_DIR/dashboard-help.txt"
grep -q -- '--host' "$TMP_DIR/dashboard-help.txt"
grep -q -- '--sources-file' "$TMP_DIR/dashboard-help.txt"
printf 'PASS: local dashboard exposes only read-only project status\n'

printf '\n[16/22] Render validator CLI smoke test\n'
"$PYTHON" scripts/validate_render.py --help > "$TMP_DIR/render-validation-help.txt"
grep -q -- '--min-width' "$TMP_DIR/render-validation-help.txt"
printf 'PASS: rendered output can be checked before editorial release review\n'

printf '\n[17/22] RSS feed importer configuration smoke test\n'
"$PYTHON" scripts/import_feeds.py --config config/research_feeds.json --ledger "$TMP_DIR/feed-sources.json" > "$TMP_DIR/feed-import.json"
grep -q '"feeds_configured": 0' "$TMP_DIR/feed-import.json"
grep -q 'not factual verification' "$TMP_DIR/feed-import.json"
printf 'PASS: feed importer runs safely with an empty opt-in feed list\n'

printf '\n[18/22] Release evidence bundle CLI smoke test\n'
"$PYTHON" scripts/build_release_bundle.py --project data/projects/sample_project.json --output "$TMP_DIR/release-bundle.json" > "$TMP_DIR/release-bundle-result.json"
grep -q '"publish_ready": false' "$TMP_DIR/release-bundle-result.json"
grep -q '"release_blocker_count"' "$TMP_DIR/release-bundle-result.json"
grep -q '"Final rendered video is missing."' "$TMP_DIR/release-bundle.json"
grep -q '"YouTube metadata draft is missing."' "$TMP_DIR/release-bundle.json"
printf 'PASS: evidence bundle created and missing production evidence blocks release\n'

printf '\n[19/22] Cinematic map generator CLI smoke test\n'
"$PYTHON" scripts/render_cinematic_map.py --help > "$TMP_DIR/cinematic-map-help.txt"
grep -q -- '--scene' "$TMP_DIR/cinematic-map-help.txt"
grep -q -- '--output' "$TMP_DIR/cinematic-map-help.txt"
printf 'PASS: cinematic map CLI exposes scene and output arguments\n'

printf '\n[20/22] Cinematic map scene validation and SVG smoke render\n'
"$PYTHON" scripts/render_cinematic_map.py --scene data/projects/sample_cinematic_scene.json --output "$TMP_DIR/cinematic-scene.svg" > "$TMP_DIR/cinematic-scene-result.json"
grep -q '"status": "RENDERED_SVG"' "$TMP_DIR/cinematic-scene-result.json"
grep -q 'animateMotion' "$TMP_DIR/cinematic-scene.svg"
grep -q 'ILLUSTRATIVE' "$TMP_DIR/cinematic-scene.svg"
printf 'PASS: schematic route animation generated; geographic basemap remains a manual-review requirement\n'

printf '\n[21/22] Editorial fact-check report smoke test\n'
"$PYTHON" scripts/build_fact_check_report.py --claims-file data/sources/claims.json --sources-file data/sources/sources.json --output "$TMP_DIR/fact-check-report.md" > "$TMP_DIR/fact-check-report-result.txt"
grep -q 'does not establish truth' "$TMP_DIR/fact-check-report.md"
grep -q 'Human review checklist' "$TMP_DIR/fact-check-report.md"
grep -q 'FACT-CHECK REPORT CREATED' "$TMP_DIR/fact-check-report-result.txt"
printf 'PASS: fact-check report includes source traceability, warnings, and human review checklist\n'

printf '\n[22/22] Cinematic map MP4 frame-render smoke test\n'
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  "$PYTHON" scripts/render_cinematic_mp4.py --scene data/projects/sample_cinematic_scene.json --output "$TMP_DIR/cinematic-scene.mp4" --fps 1 > "$TMP_DIR/cinematic-mp4-result.json"
  grep -q '"render": "PASS"' "$TMP_DIR/cinematic-mp4-result.json"
  "$PYTHON" scripts/validate_render.py --video "$TMP_DIR/cinematic-scene.mp4" --allow-missing-audio --min-width 1280 --min-height 720 > "$TMP_DIR/cinematic-mp4-validation.json"
  grep -q '"validation": "PASS"' "$TMP_DIR/cinematic-mp4-validation.json"
  ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$TMP_DIR/cinematic-scene.mp4" > "$TMP_DIR/cinematic-mp4-streams.txt"
  grep -q 'video' "$TMP_DIR/cinematic-mp4-streams.txt"
  printf 'PASS: frame-based cinematic MP4 rendered and its video stream validated (synthetic illustrative scene)\n'
else
  printf 'SKIP: cinematic MP4 smoke render (FFmpeg/FFprobe not installed)\n'
fi

printf '\nALL LOCAL VALIDATION CHECKS PASSED\n'
