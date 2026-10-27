# Hijaz GeoIntelligence Studio

AI-powered geopolitical research and multilingual documentary production.

## Mission
Build a source-grounded workflow for researching public geopolitical events and producing educational documentaries in Urdu, English, Russian, and Chinese.

## Initial MVP
- Collect and record public sources in a validated local ledger.
- Track editorial claims and reject references to URLs absent from the source ledger.
- Separate verified facts, official claims, independent reporting, analysis, and unverified claims.
- Draft cited documentary scripts.
- Prepare original narration, subtitles, and video-production assets.
- Require human approval before publishing.

## Editorial and Safety Rules
- Use public, non-operational information.
- Do not produce real-time targeting or attack-optimization guidance.
- Respect copyright and footage licensing.
- Preserve source URLs and publication dates.
- Never present an allegation as an established fact.
- Require human review before public release.

## Project Layout
- `app/research/` — source and claim collection, validation, and traceability
- `app/editorial/` — script and fact-check workflows
- `app/video/` — video assembly and graphics
- `app/voice/` — narration and subtitle workflows
- `app/publishing/` — YouTube publishing preparation
- `config/` — non-secret configuration
- `data/` — local research records and drafts
- `docs/` — project and editorial documentation
- `scripts/` — developer utilities and local validation
- `tests/` — automated tests

## Development
Requires Python 3.10 or newer; no third-party package is required for the current MVP.

Run the full local validation sequence (unit tests, syntax compilation, CLI help, and source/claim smoke tests):

```sh
./scripts/validate.sh
```

You can also run individual checks:

```sh
python -m unittest discover -s tests -v
python scripts/add_source.py --help
python scripts/add_claim.py --help
```

No GitHub Actions workflow is enabled; this validation script runs locally and does not consume Actions minutes. The source and claim ledgers validate metadata and traceability but do not automatically establish factual accuracy.

## Claim traceability

See [`docs/claim-ledger.md`](docs/claim-ledger.md) for adding claims linked to recorded sources. The ledger is a workflow safeguard, not an automated fact-checker.

## Project completion plan

See [`docs/roadmap.md`](docs/roadmap.md) for the phased roadmap and explicit completion criteria. This project is not yet production-complete; code and test coverage will be expanded phase by phase.
