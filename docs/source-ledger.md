# Source Ledger

The source ledger records source metadata locally. It is not an automated fact-verification system.

## Add a source

From the repository root:

```sh
python scripts/add_source.py \
  --title "Example public report" \
  --url "https://example.org/report" \
  --published-at "2026-10-20" \
  --source-type independent_reporting \
  --claim-status independent_reporting \
  --notes "Example fixture only; replace with real source notes."
```

Supported source types: `official_statement`, `primary_document`, `independent_reporting`, `analysis`.

Supported claim labels: `verified_fact`, `official_claim`, `independent_reporting`, `analysis`, `unverified`.

Every record requires a title, absolute HTTP(S) URL, ISO publication date, source type, claim label, and notes. Duplicate URLs are rejected after normalizing scheme/host case, removing fragments, and treating an empty root path as `/`. Trailing slashes on non-root paths are preserved: `/report` and `/report/` may identify distinct HTTP resources. Claim-to-source linkage uses the same conservative URL identity rules, while preserving the submitted claim URL and the matched ledger URL in release evidence. This is URL metadata matching only; it does not fetch sources, assess credibility, prove claim support, or verify factual truth. Keep notes explicit about corroboration, uncertainty, and whether a label describes a claim or merely the type of source. Do not label a claim verified merely because a source states it.

The default file is `data/sources/sources.json`; use `--ledger PATH` to test or write to a different file. Keep private notes and credentials out of the public repository.

## Test

```sh
./scripts/validate.sh
```
