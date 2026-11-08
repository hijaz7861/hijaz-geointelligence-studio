# Rendered-video technical validation

Use `ffprobe` to check required streams, positive container duration, and minimum dimensions:

```sh
python scripts/validate_render.py \
  --video artifacts/renders/documentary.mp4 \
  --require-subtitles \
  --require-video-cover-audio \
  --min-width 1280 \
  --min-height 720
```

`--require-video-cover-audio` checks the primary video stream against every audio stream. The video must start no later than each audio stream and end no earlier than each audio stream, within a configurable 250 ms default tolerance. Missing or non-finite stream timing metadata fails closed. The JSON report records each checked audio stream and its interval.

The release evidence bundle enables this check automatically. It also bounds the sidecar SRT against the primary audio stream and the container duration. These checks establish stream/cue time bounds only; they do not establish word-level subtitle-to-speech synchronization.

The default minimum dimensions are permissive for synthetic tests; use an appropriate release target such as 1280×720 for a standard HD deliverable. The tool does not measure intelligibility, loudness, pronunciation, translation quality, caption accuracy, factual correctness, or licensing. Those remain human review items.
