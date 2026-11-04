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

## URL identity and matching

Source-to-claim and media-origin references use a conservative comparison key: scheme and hostname case, IDNA hostname form, compressed IPv6 literals, default HTTP(S) ports, URL fragments, and an empty root path are normalized. A non-root path's trailing slash is preserved because `/report` and `/report/` can identify different HTTP resources. The submitted URL remains in the ledger and evidence output.

This is syntax and reference matching only. URLs are not fetched, redirects are not followed, and canonical matching does not prove that a page exists, supports a claim, or is legally reusable.

## Editorial review checklist

- Does each source actually support the wording of the claim?
- Is an official statement distinguished from independently established fact?
- For consequential claims, is there independent corroboration where available?
- Are dates, attribution, uncertainty, and conflicting evidence represented fairly?
- Has a human editor approved the claim before it appears in a published script?
