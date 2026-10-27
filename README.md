# Hijaz GeoIntelligence Studio

AI-powered geopolitical research and multilingual documentary production.

## Mission
Build a source-grounded workflow for researching public geopolitical events
and producing educational documentaries in Urdu, English, Russian, and Chinese.

## Initial MVP
- Collect and record public sources.
- Separate verified facts, official claims, independent reporting, and unverified claims.
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
- `app/research/` — source collection and verification
- `app/editorial/` — script and fact-check workflows
- `app/video/` — video assembly and graphics
- `app/voice/` — narration and subtitle workflows
- `app/publishing/` — YouTube publishing preparation
- `config/` — non-secret configuration
- `data/` — local research records and drafts
- `docs/` — project and editorial documentation
- `tests/` — automated tests

## Development
Python standard-library tests can be run with:

    python -m unittest discover -s tests -v

No GitHub Actions workflow is enabled by this initial setup.
