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

The tool records SHA-256 hashes and sizes for provided input files, maps project claims to source metadata, captures media-rights fields, checks final render streams with ffprobe (video, audio, and an embedded subtitle stream are required), validates the sidecar SRT structure, and blocks subtitle cues that extend more than 250 ms beyond the rendered container duration. It includes the approval fields recorded in the project JSON and a separate `human_approval_authentication` object. Project flags and `approved_by` are self-reported metadata only; the report explicitly marks authentication as `NOT_AUTHENTICATED` and adds a release blocker even when every flag is true.

Missing render, subtitles, metadata, unclear media rights, unresolved claims, and missing approvals become release blockers. The report always keeps publish_ready set to false: this is an audit artifact, not authorization to publish or upload.


## Tamper-evident human approval receipts

Project approval booleans and `approved_by` remain self-reported checklist metadata. The sidecar receipt workflow adds HMAC-SHA256 integrity protection and binds all four review stages to the exact project-file bytes. The final-video review also binds to the exact MP4 bytes. A valid receipt set does **not** authenticate a person's legal identity.

1. Finalize the project JSON before recording approvals. If the project file changes, all receipts become stale.
2. Create the key on a trusted local machine. Keep it outside the repository and never commit, email, or upload it:

       python scripts/init_approval_key.py --output ~/.config/hijaz/approval.key

3. Record one decision for each stage, using the same receipts file and key. Example:

       python scripts/record_approval.py --project data/projects/sample_project.json --receipts artifacts/reports/approval-receipts.json --key-file ~/.config/hijaz/approval.key --stage script_reviewed --decision approved --reviewer "Editor name" --reason "Reviewed the factual script and citations."

   Repeat with `translation_reviewed`, `media_rights_reviewed`, and `final_video_reviewed`. The final-video command must also include `--artifact artifacts/renders/final.mp4`. Record a new receipt file if a stage needs a fresh decision; duplicate stages are rejected.

4. Build the evidence bundle with both receipt inputs:

       python scripts/build_release_bundle.py --project data/projects/sample_project.json --sources-file data/sources/sources.json --claims-file data/sources/claims.json --render artifacts/renders/final.mp4 --subtitles artifacts/subtitles/final.srt --metadata artifacts/drafts/youtube-metadata.json --approval-receipts artifacts/reports/approval-receipts.json --approval-key-file ~/.config/hijaz/approval.key --output artifacts/reports/release-evidence.json

A missing, altered, rejected, incomplete, wrong-project, or stale receipt set fails closed. The key is never included in the evidence bundle. Keep the receipts file private if it contains reviewer names or sensitive review notes.

HMAC verifies receipt integrity and possession of a shared secret. The reviewer name is still self-asserted; HMAC does not independently authenticate identity or provide non-repudiation between people sharing the same key. Use a separately governed identity/signature system if stronger reviewer identity assurance is required. Even a valid receipt set leaves `human_approval_authentication.status=NOT_AUTHENTICATED`, `publish_ready=false`, and the review-artifact blocker in place.

## Important limitations

- Hashes establish file identity, not truth or provenance authenticity.
- Source URLs and claim labels do not prove that sources support the claims.
- Rights evidence is recorded as supplied text; the tool does not verify licenses or permission.
- Subtitle structure and a duration-bound check do not prove translation quality or synchronization to the spoken audio.
- Approval names and flags are copied from project metadata; they are not cryptographically signed or authenticated. The report marks this state as `NOT_AUTHENTICATED` and lists the controls needed for trusted review.
- No YouTube API call or upload is performed.
