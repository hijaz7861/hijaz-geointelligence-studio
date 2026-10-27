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

The subtitle is embedded as a selectable MP4 `mov_text` track, not burned into the picture. Output is not overwritten unless `--overwrite` is explicitly provided. Rendering occurs to a temporary MP4 and replaces the destination only after success, preserving an existing destination if FFmpeg fails or times out. FFmpeg is called with an argument list (no shell) and a configurable timeout.

## Verification

Run `./scripts/validate.sh`. If FFmpeg is installed, the script creates tiny synthetic test media, renders a temporary MP4, and checks that video, audio, and subtitle streams exist. If FFmpeg is absent, that integration step is skipped. Unit tests still exercise command construction and failure handling.

A successful mux only verifies that the container was assembled. Editors must still review visual quality, audio levels, subtitle timing, licensing, factual accuracy, and the final rendered video before release.
