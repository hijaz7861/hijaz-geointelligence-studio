#!/bin/sh
# Repeatable local validation; intentionally avoids GitHub Actions minutes.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON=${PYTHON:-python3}
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

printf '\n[1/4] Unit tests\n'
"$PYTHON" -m unittest discover -s tests -v
printf '\n[2/4] Syntax compilation\n'
"$PYTHON" -m compileall -q app scripts tests
printf 'PASS: compileall\n'
printf '\n[3/4] CLI help\n'
"$PYTHON" scripts/add_source.py --help > "$TMP_DIR/help.txt"
grep -q -- '--published-at' "$TMP_DIR/help.txt"
printf 'PASS: CLI help\n'
printf '\n[4/4] CLI add + duplicate rejection smoke test\n'
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
printf 'PASS: add and duplicate rejection\n'
printf '\nALL LOCAL VALIDATION CHECKS PASSED\n'
