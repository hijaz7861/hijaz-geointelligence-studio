# Rendered-video technical validation

Use `ffprobe` to check required streams, positive duration, and minimum dimensions:

```sh
python scripts/validate_render.py \
  --video artifacts/renders/documentary.mp4 \
  --require-subtitles \
  --require-video-cover-audio \
  --min-width 1280 \
  --min-height 720
```

`--require-video-cover-audio` checks that the video stream begins no later than the audio stream (within a 250 ms default tolerance) and ends no earlier than the audio stream. This catches muxing cases where sparse subtitle packets or other FFmpeg behavior leave audio playing after the last video frame. The flag is optional for general inspection; the release evidence bundle enables it.

The default minimum dimensions are permissive for synthetic tests; use an appropriate release target such as 1280×720 for a standard HD deliverable. These checks do not measure intelligibility, loudness, lip-sync, caption accuracy, factual correctness, or licensing. Subtitle structure and stream time bounds do not prove word-level synchronization; human review remains mandatory.
