# Hijaz GeoIntelligence Studio

AI-powered geopolitical research and multilingual documentary production.

## Mission
Build a source-grounded workflow for researching public geopolitical events and producing educational documentaries in Urdu, English, Russian, and Chinese.

## Initial MVP
- Collect and record public sources in a validated local ledger.
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
- `app/research/` — source collection and validation
- `app/editorial/` — script and fact-check workflows
- `app/video/` — video assembly and graphics
- `app/voice/` — narration and subtitle workflows
- `app/publishing/` — YouTube publishing preparation
- `config/` — non-secret configuration
- `data/` — local research records and drafts
- `docs/` — project and editorial documentation
- `scripts/` — developer utilities
- `tests/` — automated tests

## Development
Requires Python 3.10 or newer; no third-party package is required for the current MVP.

```sh
python -m unittest discover -s tests -v
python scripts/add_source.py --help
```

No GitHub Actions workflow is enabled; local test execution is the current validation path. The source ledger records metadata but does not automatically establish factual accuracy.
