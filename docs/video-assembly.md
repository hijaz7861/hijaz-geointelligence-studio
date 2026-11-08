# Local video assembly

The optional FFmpeg adapter muxes an existing video/visual track, narration audio, and an optional SRT file into an MP4. It does not generate visuals, write narration, translate subtitles, or determine media rights.

## Requirements

- Python 3.10 or newer.
- FFmpeg installed and available on `PATH`.
- A video input containing a video stream, an audio/narration file, and optionally a valid SRT file.
- Permission to use all input media.

## Example

```sh
python scripts/validate_srt.py captions.srt
python scripts/render_video.py \
  --video visuals.mp4 \
  --audio narration.wav \
  --subtitles captions.srt \
  --output documentary.mp4
```

The subtitle is validated before rendering, then embedded as a selectable MP4 `mov_text` track, not burned into the picture. Output is not overwritten unless `--overwrite` is explicitly provided. Rendering occurs to a temporary MP4 and replaces the destination only after success, preserving an existing destination if FFmpeg fails or times out. FFmpeg is called with an argument list (no shell) and a configurable timeout.

The mux deliberately does not use FFmpeg `-shortest`: sparse subtitle packets can otherwise cause the video stream to end while buffered narration continues. The release gate instead probes the final file and requires the video interval to cover every audio stream within 250 ms. It also checks the sidecar SRT against the primary audio interval and container duration. A stream-bound pass does not prove word-level synchronization.

## Verification

Run `./scripts/validate.sh`. If FFmpeg is installed, the script creates synthetic test media, renders a temporary MP4, and checks video/audio/subtitle streams and video-to-audio coverage. If FFmpeg is absent, the integration step is skipped. Unit tests still exercise command construction and failure handling.

After muxing, run:

```sh
python scripts/validate_render.py \
  --video documentary.mp4 \
  --require-subtitles \
  --require-video-cover-audio \
  --min-width 1280 \
  --min-height 720
```

A successful mux only verifies that the container was assembled and its stream time bounds pass. Editors must still review visual quality, audio levels, pronunciation, subtitle timing, translation, licensing, factual accuracy, and the final rendered video before release.
