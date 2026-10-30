# Release evidence bundle

Create a JSON evidence report for editorial review. The report is always blocked from publication:

    python scripts/build_release_bundle.py \
      --project data/projects/final-project.json \
      --sources-file data/sources/sources.json \
      --claims-file data/sources/claims.json \
      --render artifacts/renders/final.mp4 \
      --subtitles artifacts/subtitles/final.srt \
      --metadata artifacts/drafts/youtube-metadata.json \
      --approval-receipts artifacts/reports/approval-receipts.json \
      --approval-key-file ~/.config/hijaz/approval.key \
      --min-width 1280 --min-height 720 \
      --output artifacts/reports/release-evidence.json

The bundle records SHA-256 hashes and sizes for provided input files, maps project claims to source-ledger metadata, and emits a `citation_validation` summary with resolved/unresolved ledger references. It captures media-rights fields, checks video/audio/embedded-subtitle streams with ffprobe, validates the sidecar SRT, and compares the final cue end against both the container and audio-stream durations (250 ms tolerance). A missing audio-stream duration or a subtitle overrun becomes a blocker.

## Tamper-evident human review receipts

The project JSON approval booleans remain a checklist; they are not sufficient evidence by themselves. The sidecar receipt file adds HMAC-SHA256 integrity protection and binds all four review stages to the exact project-file bytes. The final-video review additionally binds to the exact MP4 bytes.

1. Finalize the project JSON first. Set the four approval booleans and `approved_by` only after the corresponding human review has actually occurred. Do not edit the project after receipts are recorded.
2. Create a key on a trusted local machine. Keep it outside the repository and never commit or upload it:

       python scripts/init_approval_key.py --output ~/.config/hijaz/approval.key

3. Record one receipt for each stage. Use the same receipts file and key for all four commands:

       python scripts/record_approval.py --project data/projects/final-project.json --receipts artifacts/reports/approval-receipts.json --key-file ~/.config/hijaz/approval.key --stage script_reviewed --decision approved --reviewer "Editor name" --reason "Reviewed the factual script and its citations."
       python scripts/record_approval.py --project data/projects/final-project.json --receipts artifacts/reports/approval-receipts.json --key-file ~/.config/hijaz/approval.key --stage translation_reviewed --decision approved --reviewer "Language reviewer" --reason "Reviewed the translated script and terminology."
       python scripts/record_approval.py --project data/projects/final-project.json --receipts artifacts/reports/approval-receipts.json --key-file ~/.config/hijaz/approval.key --stage media_rights_reviewed --decision approved --reviewer "Rights reviewer" --reason "Reviewed the actual media-rights evidence and permitted use."
       python scripts/record_approval.py --project data/projects/final-project.json --receipts artifacts/reports/approval-receipts.json --key-file ~/.config/hijaz/approval.key --stage final_video_reviewed --decision approved --reviewer "Video editor" --reason "Inspected the exact final MP4 for editorial release." --artifact artifacts/renders/final.mp4

4. Build the release evidence bundle using both `--approval-receipts` and `--approval-key-file`. A missing, altered, rejected, stale, or incomplete receipt set fails closed. If the project changes, obtain all four receipts again. If the MP4 changes, obtain a new final-video review in a new receipts file.

HMAC verifies receipt integrity and possession of a shared secret. The reviewer name is self-asserted; HMAC does not independently authenticate legal identity or provide non-repudiation between multiple people sharing the same key. Use a separately governed identity/signature system if that assurance is required. The key is never included in the evidence bundle.

## Citation and rights interpretation

- Claim/source entries preserve claim status and source-ledger URL, title, source type, and publication date. This proves ledger linkage only; it does not prove that a source supports the claim or that the claim is true.
- Hashes establish file identity, not factual truth or provenance authenticity.
- Rights evidence is recorded as supplied text; the software does not verify licenses, permissions, or legal suitability. Human review must inspect the actual publisher terms and evidence.
- The bundled Natural Earth overview layer and any supplied attribution/license strings are not independently certified by this report.

## Important limitations

- SRT structure and duration bounds do not prove that captions align with spoken words, that translation is accurate, or that narration is intelligible.
- Audio duration checks only detect captions extending beyond the audio stream; human listening and subtitle-to-speech review remain mandatory.
- The report always keeps `publish_ready=false` and includes a review-artifact blocker. It never authorizes, uploads, or publishes content.
- No YouTube API call or upload is performed.
