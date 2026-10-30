# Natural Earth cinematic MP4 preview

This guide renders the bundled Natural Earth 1:110m country-boundary GeoJSON layer into every frame of a deterministic cinematic MP4 preview.

## Requirements

- Python 3.10 or newer.
- FFmpeg and FFprobe available on `PATH`.
- CairoSVG's system prerequisites installed (including Cairo), then:

```sh
python3 -m pip install -r requirements-media.txt
```

The repository's core modules otherwise use the Python standard library.

## Render a geographic MP4 preview

Run from the repository root:

```sh
python3 scripts/render_cinematic_mp4.py \
  --scene data/projects/sample_cinematic_scene.json \
  --output artifacts/natural-earth-cinematic-preview.mp4 \
  --fps 2 \
  --geojson data/assets/natural_earth_110m_admin_0_countries.geojson \
  --basemap-attribution "Made with Natural Earth; GeoJSON conversion by Martyn Afford" \
  --basemap-license "Natural Earth public domain; conversion CC0-1.0 (review publisher terms)" \
  --basemap-source-url "https://github.com/martynafford/natural-earth-geojson/blob/0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e/110m/cultural/ne_110m_admin_0_countries.json"
```

The renderer validates the scene and bounded local GeoJSON input, renders the geographic overlay and supplied metadata into each SVG frame, rasterizes frames, and encodes the MP4. The footer places attribution, license, and source on separate lines; overlong metadata is rejected instead of silently clipped. The overlay path is local-only; the renderer does not download data from the source URL. Attribution, license text, and an HTTPS source URL are required when `--geojson` is supplied. Metadata without a GeoJSON file is rejected.

The renderer remains bounded (1–12 FPS, at most 60 seconds and 720 frames) and refuses to overwrite an existing output unless `--overwrite` is explicitly supplied. The output is visuals-only. To add separately reviewed narration and selectable SRT subtitles, use `scripts/render_video.py`, then run `scripts/validate_render.py --require-subtitles`.

## Rights, accuracy, and editorial limitations

- The bundled 1:110m Natural Earth dataset is generalized for world/overview maps, not local precision or navigation.
- The notice records publisher statements and a pinned upstream conversion revision. It is not legal advice and this code does not independently verify the current license, attribution obligations, dataset integrity, political-boundary suitability, or downstream use.
- The sample route/event data is illustrative. Do not present it as a real event.
- A passing render or CI test proves only that the software generated and technically encoded the preview. It does not verify the map visually, prove facts, establish rights, or approve release.
- Human review of the actual rendered frames, source claims, attribution, audio, subtitles, and final cut remains mandatory.
- This tool does not upload or publish to YouTube. The release evidence bundle deliberately keeps `publish_ready=false`.

## CI evidence

The repository validation workflow renders the bundled Natural Earth overlay through the MP4 path, muxes synthetic audio and SRT test data, validates video/audio/subtitle streams with FFprobe, and uploads the resulting review artifacts. Inspect the workflow run and artifact for each draft PR; do not infer visual approval from a green check.
