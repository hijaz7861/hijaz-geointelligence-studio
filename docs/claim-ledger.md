# Claim ledger

The claim ledger records editorial statements and requires each statement to link to one or more URLs already present in the source ledger. This makes source traceability testable; it does **not** prove a claim is true, independently corroborated, or correctly interpreted.

## Add a claim

First add its source using `scripts/add_source.py`. Then run:

```sh
python scripts/add_claim.py \
  --claim "The statement being evaluated" \
  --status independent_reporting \
  --source-url "https://example.org/report" \
  --notes "State what the source supports and any uncertainty."
```

Repeat `--source-url` for each additional source. A URL must already be recorded in `data/sources/sources.json`; unknown URLs are rejected. Claim status must be one of `verified_fact`, `official_claim`, `independent_reporting`, `analysis`, or `unverified`. Use `verified_fact` only after editorial review; the program does not assign truth status automatically.

By default, claims are stored in `data/sources/claims.json`. Use `--sources-file` and `--claims-file` for isolated fixtures or alternate ledgers.

## Editorial review checklist

- Does each source actually support the wording of the claim?
- Is an official statement distinguished from independently established fact?
- For consequential claims, is there independent corroboration where available?
- Are dates, attribution, uncertainty, and conflicting evidence represented fairly?
- Has a human editor approved the claim before it appears in a published script?
