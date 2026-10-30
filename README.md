# Hijaz GeoIntelligence Studio

AI-powered geopolitical research and multilingual documentary production.

## Mission
Build a source-grounded workflow for researching public geopolitical events and producing educational documentaries in Urdu, English, Russian, and Chinese.

## Current capabilities
- Validate public-source metadata, publication dates, source categories, and duplicate URLs.
- Import RSS/Atom discovery metadata from explicitly configured HTTPS feeds with size/time limits and private-network protections.
- Track editorial claims and reject references to URLs absent from the source ledger.
- Flag missing or single-domain independent corroboration as editorial warnings, not automated truth judgments.
- Validate documentary project structure and trace project claims and media-origin URLs.
- Require every factual script paragraph to use a tracked `[[claim:Exact claim text]]` marker; clearly label non-factual framing as `[EDITORIAL]` or `[TRANSITION]`.
- Generate a traceable Markdown draft from recorded claims and source URLs; drafts are explicitly marked for human review.
- Generate a human-readable fact-check report with claim statuses, linked source metadata, and corroboration warnings; report output requires human source review and does not claim to establish truth.
- Check translated scripts for preserved claim markers and source URLs without pretending to evaluate linguistic quality.
- Prepare a YouTube title/description/source metadata package that stays blocked until release requirements pass; no upload action is implemented.
- View local source, claim, corroboration, and release-blocker status in a read-only loopback dashboard.
- Require media creator, attribution, usage scope, and rights-evidence notes.
- Validate SRT subtitle sequence, timestamps, cue overlap, text presence, and line length with a local CLI.
- Inspect rendered MP4 streams, duration, and resolution with `ffprobe` before editorial release review.
- Generate optional offline eSpeak narration WAVs when the requested language voice is installed; missing voices fail explicitly rather than silently switching languages.
- Produce release blockers for unresolved unverified claims, uncleared media rights, and missing human approvals.
- Build a deterministic release evidence bundle with SHA-256 input hashes, claim/source traceability, media-rights metadata, render/subtitle checks, approval records, and fail-closed release blockers.
- Generate deterministic, bounded 1280×720 MP4 previews from validated scene plans, with frame-by-frame route motion and optional local GeoJSON Polygon/MultiPolygon overlays.
- Render a bundled, generalized Natural Earth 1:110m country-boundary layer into SVG and MP4 previews with visible supplied attribution/license/source metadata; this software does not independently verify legal rights or geographic suitability.
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
- `app/video/` — deterministic SVG/MP4 map rendering, optional local GeoJSON overlays, and FFmpeg narration/subtitle muxing
- `app/voice/` — SRT validation and optional offline eSpeak narration
- `app/publishing/` — YouTube metadata drafts and release evidence bundles; publishing/upload remains unimplemented
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

## Ready-to-run geographic map sample

The repository bundles a pinned Natural Earth 1:110m Admin-0 country-boundary GeoJSON dataset under `data/assets/`. The publisher's official terms identify Natural Earth data as public domain; the upstream GeoJSON conversion repository identifies its conversion as CC0. Source revision, upstream blob SHA, attribution guidance, and boundary caveats are recorded in [the dataset notice](data/assets/NATURAL_EARTH_110M_NOTICE.md).

Requirements: Python 3.10+ (standard library only for SVG output).

From the repository root:

```bash
bash scripts/render_natural_earth_sample.sh
```

Output: `/tmp/hijaz-natural-earth-sample.svg`. Open that SVG in a browser or image viewer that supports SVG. To choose a different path, pass it as the first argument. To intentionally replace an existing output, pass `--overwrite` as the second argument.

The bundled boundaries are generalized for world/overview maps, not local precision or navigation. The sample's moving route is explicitly illustrative and must not be interpreted as a real event. Inspect the map visually before using it in a release.

## Documentation
- [Claim ledger workflow](docs/claim-ledger.md)
- [Safe RSS/Atom feed importer](docs/feed-importer.md)
- [Documentary project schema and release gate](docs/documentary-project-schema.md)
- [Cited draft generation](docs/cited-draft-generation.md)
- [Translation traceability validation](docs/translation-validation.md)
- [Read-only local dashboard](docs/dashboard.md)
- [YouTube release metadata draft](docs/release-metadata.md)
- [Cinematic map generator and GeoJSON-aware MP4 preview](docs/cinematic-map-generator.md)
- [Natural Earth cinematic MP4 preview guide](docs/natural-earth-cinematic-mp4.md)
- [Local FFmpeg video assembly](docs/video-assembly.md)
- [Rendered-video technical validation](docs/render-validation.md)
- [Release evidence bundle](docs/release-evidence-bundle.md)
- [Offline narration generation and language limitations](docs/narration.md)
- [Editorial policy](docs/editorial-policy.md)
- [Implementation roadmap and completion criteria](docs/roadmap.md)
- [Production readiness and customer handoff gates](docs/production-readiness.md)

## Completion status
This is an evolving MVP, not a completed production video-automation system. The current dashboard is loopback-only and read-only; secure multi-user collaboration is not implemented. Completion requires a reproducible end-to-end sample from source research through reviewed script, rights-cleared assets, subtitles/narration, rendered video, and human approval. See the roadmap and [production readiness gates](docs/production-readiness.md) before relying on it for customer delivery.


## Project ownership

Project owner and maintainer: **Muhammad Naeem Khan** (`hijaz7861`).

## Ready-to-run real-world map preview

A generalized Natural Earth world-country GeoJSON dataset is bundled locally at `data/assets/natural_earth_110m_admin_0_countries.geojson`. See [dataset provenance and terms](data/assets/NATURAL_EARTH_110M_NOTICE.md) and the [cinematic map run guide](docs/cinematic-map-generator.md).

```sh
python3 -m pip install -r requirements-media.txt
python3 scripts/render_cinematic_map.py --scene data/projects/sample_cinematic_scene.json --output artifacts/natural-earth-world-preview.svg --overwrite --geojson data/assets/natural_earth_110m_admin_0_countries.geojson --basemap-attribution "Natural Earth (public-domain dataset; 1:110m Admin 0 Countries)" --basemap-license "Public domain (Natural Earth; verify current terms)" --basemap-source-url "https://github.com/martynafford/natural-earth-geojson/blob/0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e/110m/cultural/ne_110m_admin_0_countries.json"
```
