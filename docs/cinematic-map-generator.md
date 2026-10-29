# Cinematic Map Generator — implementation contract

## Goal
Create a repeatable, local-first visual-production component for historical and public geopolitical documentaries. It converts a structured, source-linked scene plan into a map animation asset that can be reviewed and assembled with narration/subtitles.

## Scope and safety boundary
- Support historical, retrospective, educational, and fictional scenarios using user-supplied, source-linked facts.
- Visualize broad movement, formations, geographic regions, event markers, and timeline phases.
- Do not infer missing facts, fabricate routes, or label a scenario as verified merely because it renders.
- Do not generate real-time targeting, attack optimization, weapon aiming, interception prediction, or operationally useful military guidance. Missile/explosion effects, if ever used, must be clearly illustrative and non-operational.
- Every factual event and route needs a source/claim reference in the project package; unsupported details remain visibly marked as illustrative or unresolved.
- Never publish automatically. Keep human editorial approval as a hard gate.

## Intended pipeline
1. Research ledger and claim ledger
2. Human-reviewed scene plan (JSON)
3. Scene-plan validation (coordinates, timestamps, entities, sources, rights, safety labels)
4. Map projection and animated SVG/storyboard generation
5. Render adapter to MP4 (FFmpeg/browser renderer; implementation must check installed capabilities rather than assume them)
6. Visual QA: frame bounds, duration, readable labels, narration/subtitle synchronization
7. Release evidence bundle and explicit human approval

## Scene-plan data contract (v1)
- `scene_id`: stable ID
- `title`: documentary scene title
- `mode`: `historical`, `educational`, or `fictional`
- `duration_seconds`: bounded positive integer
- `map`: geographic bounds and projection (`equirectangular` in v1)
- `entities`: stable ID, display label, category, and starting coordinate
- `routes`: entity ID, ordered timestamped coordinates, claim IDs/source URLs, and an explicit `illustrative` flag
- `events`: timestamp, coordinate or region, short label, claim IDs/source URLs, and `illustrative` flag
- `disclaimer`: on-screen context text for illustrative reconstructions
- `approval`: human review flags; default false

## Acceptance gates
- Invalid or out-of-range coordinates and timestamps are rejected.
- Unknown entity/claim references are rejected.
- Every factual route/event has source traceability; illustrative elements are clearly labelled.
- Output generation is deterministic for the same input.
- Output path is never silently overwritten.
- Renderer failures and missing optional dependencies fail explicitly.
- Tests cover malformed input, bounds, missing references, timestamp ordering, and overwrite protection.
- At least one source-grounded, human-reviewed sample scene must be rendered and inspected before this feature is called production-ready.

## Delivery stages
- Stage A: schema, validator, deterministic animated vector/storyboard output, unit tests.
- Stage B: real map boundaries/assets with documented license and attribution.
- Stage C: MP4 renderer integration and stream/frame validation.
- Stage D: editorial preview/review UI and evidence-bundle integration.

## Current implementation status (main)
- [x] Initial Python scene validator and deterministic SVG animation CLI.
- [x] Illustrative sample scene and unit tests for bounds, references, timestamps, and overwrite protection.
- [x] CI execution verified on 2026-10-28: 126 unit tests and all 20 repository validation stages passed in GitHub Actions.
- [ ] Licensed geographic basemap, camera moves, richer aircraft/ship sprites, reusable effects library, narration/subtitle synchronization, and cinematic-map MP4 renderer integration remain unimplemented.
- [ ] A source-grounded, human-reviewed geographic sample still needs to be rendered and inspected.

The current renderer is an initial schematic graticule preview, not a complete cinematic map product. A passing CI run verifies the scripted checks, but does not make the cinematic map feature production-ready.


## Validation hardening note

The validator treats `illustrative` as a JSON boolean only; strings such as `"false"`, numbers, and null are invalid. If a route or event is factual (`illustrative: false`, or the flag is omitted), `source_refs` must be a non-empty JSON array of non-empty strings. Each reference should be a stable claim ID or a source URL recorded in the research ledger. This is structural validation only: it does not fetch URLs, assess source quality, or independently verify a claim. Human source review remains mandatory.


## Draft frame-based MP4 renderer (feature branch)

The separate `feature/deterministic-cinematic-mp4` branch adds `scripts/render_cinematic_mp4.py`. It rasterizes each scene frame with CairoSVG, explicitly positions route markers per frame (rather than relying on SVG SMIL support), and encodes a visuals-only MP4 with FFmpeg.

Example:

```bash
python3 -m pip install -r requirements-media.txt
python3 scripts/render_cinematic_mp4.py \
  --scene data/projects/sample_cinematic_scene.json \
  --output /tmp/cinematic-preview.mp4 \
  --fps 5
```

Safety and resource limits: 1–12 FPS, scene duration at most 60 seconds, at most 720 frames, explicit timeout, and no overwrite unless `--overwrite` is passed. The preview is schematic and labelled not to scale; it is not a licensed basemap and it contains no audio. Use `scripts/render_video.py` to mux separately reviewed narration and SRT subtitles. CairoSVG/FFmpeg integration, generated output quality, and the full CI run must be verified before this draft can be considered ready. A synthetic sample passing tests does not establish real-world geographic accuracy or production readiness.

## Optional local GeoJSON polygon overlay


The renderer can accept a local GeoJSON file containing a `Polygon` or `MultiPolygon` geometry, either directly or through `Feature`/`FeatureCollection`. It does not download remote data. The user must supply the data and provide all three metadata fields so the rendered SVG visibly includes attribution, license name, and an HTTPS source URL.

Example:

```bash
python3 scripts/render_cinematic_map.py \\
  --scene data/projects/sample_cinematic_scene.json \\
  --output /tmp/scene.svg \\
  --geojson /path/to/your-licensed-boundaries.geojson \\
  --basemap-attribution 'Publisher or dataset attribution' \\
  --basemap-license 'Exact license name/version' \\
  --basemap-source-url 'https://publisher.example/dataset-page'
```

Use the exact terms supplied by the dataset publisher; do not copy this placeholder attribution into a real release. The source URL is recorded visibly but is not fetched or independently verified. Supported geometry is intentionally limited to polygon boundaries; points, lines, tiles, reprojection, and automatic clipping/generalization are not implemented. Coordinates are projected into the current schematic scene bounds and the output is still an SVG, not a cinematic MP4. Validate the dataset's license, attribution requirements, geographic suitability, and rendering quality manually before release.
