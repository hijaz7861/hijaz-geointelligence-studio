# Source Ledger

The source ledger is a local JSON record of sources used during research. It is metadata management, not an automated fact-verification system.

## Add a source

From the repository root, run:

```sh
python scripts/add_source.py \\
  --title "Example public report" \\
  --url "https://example.org/report" \\
  --published-at "2026-10-20" \\
  --source-type independent_reporting \\
  --claim-status independent_reporting \\
  --notes "Example fixture only; replace with real source notes."
```

Supported source types: `official_statement`, `primary_document`, `independent_reporting`, `analysis`.

Supported claim labels: `verified_fact`, `official_claim`, `independent_reporting`, `analysis`, `unverified`.

Every record requires a title, absolute HTTP(S) URL, ISO publication date, source type, claim label, and notes. Duplicate URLs are rejected. Keep notes explicit about corroboration, uncertainty, and whether a label describes a claim or merely the type of source. Do not label a claim verified merely because a source states it.

The default file is `data/sources/sources.json`; use `--ledger PATH` to test or write to a different file. Keep private notes and credentials out of the public repository.

## Test

```sh
python -m unittest discover -s tests -v
```
