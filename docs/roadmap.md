# Implementation roadmap and completion gates

This repository is an evolving MVP, not a completed production system. A phase is complete only when its acceptance checks are implemented, run locally, and documented with evidence.

## Phase 1 — Research traceability
- [x] Validate source metadata, dates, URLs, and source categories.
- [x] Reject duplicate source URLs.
- [x] Track editorial claims with an allowed status label.
- [x] Reject claim references to URLs absent from the source ledger.
- [x] Warn when consequential claims lack independent reporting or rely on only one independent domain; warnings never automatically determine truth.
- [x] Run repeatable local unit, syntax, CLI, and smoke checks without GitHub Actions.
- [x] Add an opt-in RSS/Atom metadata importer with HTTPS-only feeds, same-host redirects, timeouts, response-size caps, private-IP checks, duplicate handling, and provenance notes.
- [ ] Add feed ranking/filtering, publisher terms review, and source-diversity selection before automatic intake.
- [ ] Add independent-source corroboration checks as warnings, not automatic truth judgments.

## Phase 2 — Cited editorial package (in progress)
- [x] Define a structured documentary-project package with language, duration, script, claim references, media manifest, and approval flags.
- [x] Reject project references to claims absent from the claim ledger.
- [x] Reject media assets whose origin URL is absent from the source ledger.
- [x] Add release blockers for unverified claims, unknown/restricted media rights, and missing human approvals.
- [x] Require each non-editorial script paragraph to cite a tracked claim marker and reject citations absent from the project's claim list.
- [x] Generate a traceable Markdown draft from recorded claim text, evidence labels, and source URLs; require human rewrite/review.
- [ ] Generate polished narration from research inputs and stable claim IDs/source URLs, with citation-preserving editorial review.
- [ ] Validate unsupported statements, contradictory dates, and uncited factual paragraphs.
- [x] Create a human-readable fact-check report from claim/source ledgers, including recorded status and corroboration warnings; the report explicitly states it does not verify truth. Full CI execution pending.
- [x] Add a structural translation validator that ensures claim markers and source URLs remain unchanged and in order.
- [ ] Add Urdu and English workflow first, then Russian and Chinese translation with glossary consistency checks and human linguistic review.

## Phase 3 — Media production
- [x] Require creator, attribution, usage scope, and rights-evidence metadata for every media asset.
- [ ] Add structured license/permission evidence URLs and expiry/review dates.
- [x] Block media with unknown or restricted rights at the release checklist stage.
- [x] Add optional offline eSpeak WAV narration for installed language voices with timeout, output-safety, and no-silent-fallback checks.
- [x] Add a repeatable synthetic integration check that assembles generated narration, video, and SRT into one MP4 and verifies all three streams.
- [ ] Add high-quality human/cloud narration provider for languages/voices not installed locally (Urdu is not available in the current validation environment).
- [x] Add first-stage schematic animated SVG route preview with scene-plan validation (not a licensed basemap or MP4 output).
- [ ] Build original graphics, licensed geographic maps, timelines, captions, and narration tracks.
- [x] Add an optional local FFmpeg adapter to mux existing video, narration, and selectable SRT subtitle streams; test command safety and failure handling.
- [x] Run a real synthetic MP4 smoke render and verify video/audio/subtitle streams in the assistant environment.
- [x] Validate SRT cue numbering, timestamp syntax/ranges, cue ordering, overlaps, empty text, and configurable line length.
- [x] Validate rendered output for video/audio/subtitle streams, positive duration, and minimum configured resolution using ffprobe.
- [ ] Verify subtitle-to-audio synchronization, audio quality/levels, and render errors.
- [ ] Add original graphics/timeline generation and a complete sample documentary render from a cited script.

## Phase 4 — Release safety and YouTube preparation
- [x] Add human-approval flags for script, translation, media rights, and final video review.
- [x] Generate a source-attributed YouTube title/description metadata draft with explicit release blockers and no upload action.
- [x] Add a deterministic release evidence bundle with input SHA-256 hashes, claim/source mapping, rights metadata, render/subtitle checks, human-approval record, and explicit blockers; repository validation and evidence-bundle smoke test passed in GitHub Actions on 2026-10-28.
- [ ] Extend release evidence bundle with verified license URLs/expiry dates, thumbnail evidence, audio-sync metrics, and a signed approval record.
- [ ] Prepare metadata and upload package; do not publish automatically by default.
- [ ] If YouTube API upload is later added, use least-privilege OAuth, secret-free logs, private/draft default, and a clear approval gate.

## Phase 5 — Usable application
- [x] Build a loopback-only read-only dashboard for source/claim counts, validation status, corroboration warnings, and release blockers.
- [ ] Expand dashboard to manage research, script drafts, assets, and review status after authentication and audit controls are designed.
- [ ] Add project-scoped storage, backup/restore, audit trail, and safe handling of credentials.
- [ ] Add integration tests, dependency/security checks, and reproducible packaging.
- [ ] Deploy only after local end-to-end tests pass and a hosting target is explicitly configured.

## Definition of complete
The project is not production-complete until a sample documentary can be traced end-to-end from sources to claims to a cited multilingual script to rights-cleared assets to a rendered video, with a human approval record and a reproducible test report. A passing unit-test suite alone is not completion.
