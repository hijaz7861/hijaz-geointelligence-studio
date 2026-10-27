# Rendered-video technical validation

Use `ffprobe` to check that the final file has a video stream, audio stream, optional subtitle stream, positive duration, and minimum dimensions:

```sh
python scripts/validate_render.py \
  --video artifacts/renders/documentary.mp4 \
  --require-subtitles \
  --min-width 1280 \
  --min-height 720
```

The default minimum dimensions are permissive for synthetic tests; use an appropriate release target such as 1280×720 for a standard HD deliverable. The tool does not measure intelligibility, loudness, lip-sync, caption accuracy, factual correctness, or licensing. Those remain human review items.
