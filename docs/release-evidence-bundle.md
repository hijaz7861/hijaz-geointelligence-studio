# Release evidence bundle

Create a JSON evidence report for editorial review:

    python scripts/build_release_bundle.py \
      --project data/projects/sample_project.json \
      --sources-file data/sources/sources.json \
      --claims-file data/sources/claims.json \
      --render artifacts/renders/final.mp4 \
      --subtitles artifacts/subtitles/final.srt \
      --metadata artifacts/drafts/youtube-metadata.json \
      --min-width 1280 --min-height 720 \
      --output artifacts/reports/release-evidence.json

The tool records SHA-256 hashes and sizes for provided input files, maps project claims to source metadata, captures media-rights fields, checks final render streams with ffprobe, requires the video stream to cover every audio stream's complete time interval (250 ms tolerance), validates the sidecar SRT structure, and bounds the SRT cue interval against the primary audio stream and container duration. Missing/non-finite video or audio timing, video ending before any audio stream, or subtitles outside the primary audio/container bounds become blockers.

The report includes approval fields recorded in the project JSON and always keeps `publish_ready=false`: this is an audit artifact, not authorization to publish or upload.

## Important limitations

- Hashes establish file identity, not truth or provenance authenticity.
- Source URLs and claim labels do not prove that sources support the claims.
- Rights evidence is recorded as supplied text; the tool does not verify licenses or permission.
- Stream and subtitle time bounds do not prove word-level synchronization, narration quality, or caption accuracy.
- Approval names and flags are copied from project metadata; they are not cryptographically signed or authenticated by this release-bundle layer.
- No YouTube API call or upload is performed.
