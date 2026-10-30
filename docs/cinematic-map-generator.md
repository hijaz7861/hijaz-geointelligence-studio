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
- [x] Bundled generalized Natural Earth 1:110m GeoJSON and optional local Polygon/MultiPolygon overlays in SVG and frame-based MP4 renders; supplied rights statements remain subject to human legal review.
- [x] Deterministic bounded 1280×720 MP4 renderer with visible overlay attribution/license/source footer; narration and SRT remain separate mux inputs.
- [ ] Camera moves, richer sprites, reusable effects, subtitle/audio synchronization metrics, a source-grounded editorial sample, and human visual/legal review remain outstanding.
- [ ] Human visual inspection of the generated Natural Earth MP4 and a source-grounded, human-reviewed scene remain outstanding.

The renderer supports schematic graticule previews and optional local GeoJSON overlays in SVG and MP4. Neither mode is a complete cinematic map product until factual, visual, licensing, narration, subtitle, and human-approval gates are satisfied. A passing CI run verifies the scripted checks, but does not make the cinematic map feature production-ready.


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

## Ready-to-run real-boundary sample

The repository includes a pinned Natural Earth 1:110m Admin-0 Countries GeoJSON file at `data/assets/natural_earth_110m_admin_0_countries.geojson`. The source and rights evidence are recorded in [NATURAL_EARTH_110M_NOTICE.md](../data/assets/NATURAL_EARTH_110M_NOTICE.md). The upstream dataset is pinned to commit `0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e`; its source file Git blob SHA is `e3d3723ae0c5c6e89757f748ef91efcbcbd33ccd`.

Run from the repository root:

```bash
bash scripts/render_natural_earth_sample.sh
```

This produces `/tmp/hijaz-natural-earth-sample.svg` using only Python's standard library. To choose an output path, pass it as the first argument. Existing outputs are not overwritten unless `--overwrite` is passed as the second argument.

### Rights and accuracy gate

Natural Earth's official terms describe its data as public domain and allow commercial use. The upstream conversion repository states that its GeoJSON conversion is CC0. The sample visibly credits Natural Earth and the conversion source even though the official terms say credit is not required. These are source-published rights statements, not legal advice.

The 1:110m layer is generalized, not a detailed boundary dataset. Natural Earth uses de facto boundary representation and warns that data may contain errors or omissions. The renderer labels this output as generalized and not for navigation. A person must still inspect the rendered SVG and confirm that the chosen map extent and political-boundary treatment are appropriate before publication. The bundled sample route remains illustrative, not factual.

## Ready-to-run world map preview

The repository bundles a generalized Natural Earth 1:110m world-country GeoJSON dataset at `data/assets/natural_earth_110m_admin_0_countries.geojson`; source and terms are documented in `data/assets/NATURAL_EARTH_110M_NOTICE.md`. It is appropriate for illustrative world-scale previews, not navigation, surveying, or legal-boundary analysis.

From the repository root, install the Python dependencies and render the bundled sample:

```sh
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-media.txt
python3 scripts/render_cinematic_map.py --scene data/projects/sample_cinematic_scene.json --output artifacts/natural-earth-world-preview.svg --overwrite --geojson data/assets/natural_earth_110m_admin_0_countries.geojson --basemap-attribution "Natural Earth (public-domain dataset; 1:110m Admin 0 Countries)" --basemap-license "Public domain (Natural Earth; verify current terms)" --basemap-source-url "https://github.com/martynafford/natural-earth-geojson/blob/0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e/110m/cultural/ne_110m_admin_0_countries.json"
```

The data is checked into the repository and is not downloaded at run time. Attribution is rendered into the SVG. Verify current source terms before external redistribution; the bundled map is generalized and illustrative, not an authoritative GIS product.
