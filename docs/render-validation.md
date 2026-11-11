# Rendered-video technical validation

Use `ffprobe` to check that the final file has a video stream, audio stream, optional subtitle stream, positive duration, and minimum dimensions:

```sh
python scripts/validate_render.py \
  --video artifacts/renders/documentary.mp4 \
  --require-subtitles \
  --require-mp4 \
  --min-width 1280 \
  --min-height 720
```

When validating a release MP4, pass `--require-mp4`. This checks ffprobe's actual container format (`format_name`) as well as the `.mp4` filename, so a Matroska/WebM file renamed to `.mp4` is rejected. The flag is optional for generic media inspection.

The default minimum dimensions are permissive for synthetic tests; use an appropriate release target such as 1280×720 for a standard HD deliverable. The tool does not measure intelligibility, loudness, lip-sync, caption accuracy, factual correctness, or licensing. Those remain human review items.
