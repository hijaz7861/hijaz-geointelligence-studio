# Implementation roadmap and completion gates

This repository is an evolving MVP, not a completed production system. A phase is complete only when its acceptance checks are implemented, run locally, and documented with evidence.

## Phase 1 — Research traceability
- [x] Validate source metadata, dates, URLs, and source categories.
- [x] Reject duplicate source URLs.
- [x] Track editorial claims with an allowed status label.
- [x] Reject claim references to URLs absent from the source ledger.
- [x] Run repeatable local unit, syntax, CLI, and smoke checks without GitHub Actions.
- [ ] Add a reviewed-source discovery/import adapter with timeouts, URL allow/deny safeguards, and explicit provenance.
- [ ] Add independent-source corroboration checks as warnings, not automatic truth judgments.

## Phase 2 — Cited editorial package (in progress)
- [x] Define a structured documentary-project package with language, duration, script, claim references, media manifest, and approval flags.
- [x] Reject project references to claims absent from the claim ledger.
- [x] Reject media assets whose origin URL is absent from the source ledger.
- [x] Add release blockers for unverified claims, unknown/restricted media rights, and missing human approvals.
- [x] Require each non-editorial script paragraph to cite a tracked claim marker and reject citations absent from the project's claim list.
- [ ] Generate full script drafts from research inputs and stable claim IDs/source URLs.
- [ ] Validate unsupported statements, contradictory dates, and uncited factual paragraphs.
- [ ] Create a human-readable fact-check report distinguishing facts, attributed claims, analysis, and unresolved questions.
- [ ] Add Urdu and English workflow first, then Russian and Chinese translation with glossary consistency checks.

## Phase 3 — Media production
- [x] Require creator, attribution, usage scope, and rights-evidence metadata for every media asset.
- [ ] Add structured license/permission evidence URLs and expiry/review dates.
- [x] Block media with unknown or restricted rights at the release checklist stage.
- [ ] Build original graphics, timelines, maps, captions, and narration tracks.
- [x] Add an optional local FFmpeg adapter to mux existing video, narration, and selectable SRT subtitle streams; test command safety and failure handling.
- [x] Run a real synthetic MP4 smoke render and verify video/audio/subtitle streams in the assistant environment.
- [x] Validate SRT cue numbering, timestamp syntax/ranges, cue ordering, overlaps, empty text, and configurable line length.
- [ ] Verify subtitle-to-audio synchronization, audio duration, output resolution, and render errors.
- [ ] Add original graphics/timeline generation and a complete sample documentary render from a cited script.

## Phase 4 — Release safety and YouTube preparation
- [x] Add human-approval flags for script, translation, media rights, and final video review.
- [ ] Generate a complete release checklist and evidence bundle including title, description, thumbnail, sources, and media attributions.
- [ ] Prepare metadata and upload package; do not publish automatically by default.
- [ ] If YouTube API upload is later added, use least-privilege OAuth, secret-free logs, private/draft default, and a clear approval gate.

## Phase 5 — Usable application
- [ ] Build a local-first dashboard for research, claims, script drafts, assets, and review status.
- [ ] Add project-scoped storage, backup/restore, audit trail, and safe handling of credentials.
- [ ] Add integration tests, dependency/security checks, and reproducible packaging.
- [ ] Deploy only after local end-to-end tests pass and a hosting target is explicitly configured.

## Definition of complete
The project is not production-complete until a sample documentary can be traced end-to-end from sources to claims to a cited multilingual script to rights-cleared assets to a rendered video, with a human approval record and a reproducible test report. A passing unit-test suite alone is not completion.
