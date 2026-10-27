# Hijaz GeoIntelligence Studio

AI-powered geopolitical research and multilingual documentary production.

## Mission
Build a source-grounded workflow for researching public geopolitical events and producing educational documentaries in Urdu, English, Russian, and Chinese.

## Current capabilities
- Validate public-source metadata, publication dates, source categories, and duplicate URLs.
- Track editorial claims and reject references to URLs absent from the source ledger.
- Flag missing or single-domain independent corroboration as editorial warnings, not automated truth judgments.
- Validate documentary project structure and trace project claims and media-origin URLs.
- Require every factual script paragraph to use a tracked `[[claim:Exact claim text]]` marker; clearly label non-factual framing as `[EDITORIAL]` or `[TRANSITION]`.
- Generate a traceable Markdown draft from recorded claims and source URLs; drafts are explicitly marked for human review.
- Check translated scripts for preserved claim markers and source URLs without pretending to evaluate linguistic quality.
- Prepare a YouTube title/description/source metadata package that stays blocked until release requirements pass; no upload action is implemented.
- View local source, claim, corroboration, and release-blocker status in a read-only loopback dashboard.
- Require media creator, attribution, usage scope, and rights-evidence notes.
- Validate SRT subtitle sequence, timestamps, cue overlap, text presence, and line length with a local CLI.
- Inspect rendered MP4 streams, duration, and resolution with `ffprobe` before editorial release review.
- Generate optional offline eSpeak narration WAVs when the requested language voice is installed; missing voices fail explicitly rather than silently switching languages.
- Produce release blockers for unresolved unverified claims, uncleared media rights, and missing human approvals.
- Run repeatable local validation without consuming GitHub Actions minutes.

## Editorial and safety rules
- Use public, non-operational information; do not generate real-time targeting or attack-optimization guidance.
- Distinguish verified facts, official claims, independent reporting, analysis, and unverified information.
- Respect copyright and document media permission/licensing evidence.
- Never present an allegation as established fact; metadata validation does not prove truth.
- Require human review before public release. The project validator does not publish videos.

## Project layout
- `app/research/` — source and claim ledgers
- `app/editorial/` — documentary package validation and release checks
- `app/video/` — FFmpeg muxing adapter; graphics generation remains planned
- `app/voice/` — SRT validation and optional offline eSpeak narration
- `app/publishing/` — planned YouTube publishing preparation
- `config/` — non-secret configuration
- `data/` — local research records and drafts
- `docs/` — policy, schema, and roadmap
- `scripts/` — command-line utilities and validation
- `tests/` — automated tests

## Local development
Requires Python 3.10 or newer; current modules use the Python standard library.

Run all local checks:

```sh
./scripts/validate.sh
```

Validate a documentary package:

```sh
python scripts/validate_project.py --project data/projects/sample_project.json
```

The sample package is intentionally not approved for publishing. The validator checks structure and traceability; it does not fact-check claims or certify copyright status. GitHub Actions are not required for these checks.

## Documentation
- [Claim ledger workflow](docs/claim-ledger.md)
- [Documentary project schema and release gate](docs/documentary-project-schema.md)
- [Cited draft generation](docs/cited-draft-generation.md)
- [Translation traceability validation](docs/translation-validation.md)
- [Read-only local dashboard](docs/dashboard.md)
- [YouTube release metadata draft](docs/release-metadata.md)
- [Local FFmpeg video assembly](docs/video-assembly.md)
- [Rendered-video technical validation](docs/render-validation.md)
- [Offline narration generation and language limitations](docs/narration.md)
- [Editorial policy](docs/editorial-policy.md)
- [Implementation roadmap and completion criteria](docs/roadmap.md)

## Completion status
This is an evolving MVP, not a completed production video-automation system. Completion requires a reproducible end-to-end sample from source research through reviewed script, rights-cleared assets, subtitles/narration, rendered video, and human approval. See the roadmap for remaining work.
