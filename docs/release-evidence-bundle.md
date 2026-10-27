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

The tool records SHA-256 hashes and sizes for provided input files, maps project claims to source metadata, captures media-rights fields, checks final render streams with ffprobe, validates subtitle structure, and includes the approval fields recorded in the project JSON.

Missing render, subtitles, metadata, unclear media rights, unresolved claims, and missing approvals become release blockers. The report always keeps publish_ready set to false: this is an audit artifact, not authorization to publish or upload.

## Important limitations

- Hashes establish file identity, not truth or provenance authenticity.
- Source URLs and claim labels do not prove that sources support the claims.
- Rights evidence is recorded as supplied text; the tool does not verify licenses or permission.
- Subtitle structure does not prove translation quality or synchronization to audio.
- Approval names and flags are copied from project metadata; they are not cryptographically signed or authenticated.
- No YouTube API call or upload is performed.
