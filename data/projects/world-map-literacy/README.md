# World-map literacy documentary sample (English narration, Urdu subtitles)

This is a reproducible editorial sample, not an approved publication.

## Inputs
- Official Natural Earth Admin 0 Countries page: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/
- Official Natural Earth terms: https://www.naturalearthdata.com/about/terms-of-use/
- Pinned GeoJSON conversion and dataset notice: `../../assets/NATURAL_EARTH_110M_NOTICE.md`
- English narration, English/Urdu script, bilingual SRT, scene plan, source/claim ledgers, and project manifest are stored in this folder.

## Build
From repository root, install `requirements.txt`, `requirements-media.txt`, FFmpeg, and eSpeak NG. Run the same commands used in CI:
1. Validate project and translation traceability.
2. Generate English offline WAV narration (synthetic voice; review pronunciation).
3. Render Natural Earth GeoJSON into a frame-based MP4.
4. Mux English narration and bilingual selectable SRT subtitles.
5. Validate video/audio/subtitle streams and build a non-publishing release evidence bundle.

The sample intentionally leaves all approval flags false and metadata `publish_ready=false`. Passing technical validation does not approve the script, translation, rights, or final video.
