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
- [x] Create a human-readable fact-check report from claim/source ledgers, including recorded status and corroboration warnings; report output escapes untrusted text and restricts clickable links to valid HTTP(S) URLs. GitHub Actions verified 2026-10-29: 132 unit tests and all 21 validation stages passed. Human source review is still required.
- [x] Add a structural translation validator that ensures claim markers and source URLs remain unchanged and in order.
- [ ] Add Urdu and English workflow first, then Russian and Chinese translation with glossary consistency checks and human linguistic review.

## Phase 3 — Media production
- [x] Require creator, attribution, usage scope, and rights-evidence metadata for every media asset.
- [ ] Add structured license/permission evidence URLs and expiry/review dates.
- [x] Block media with unknown or restricted rights at the release checklist stage.
- [x] Add optional offline eSpeak WAV narration for installed language voices with timeout, output-safety, and no-silent-fallback checks.
- [x] Add a repeatable synthetic integration check that assembles generated narration, video, and SRT into one MP4 and verifies all three streams.
- [x] Add an optional, explicitly online Edge neural TTS adapter with Pakistan Urdu Asad/Uzma voice IDs, English/Russian/Mandarin choices, byte/time limits, safe temporary outputs, and mocked tests.
- [ ] Run a live Urdu voice sample and obtain human pronunciation/dialect review; external service availability and terms remain outside CI guarantees.
- [x] Add a deterministic frame-based MP4 renderer with optional Natural Earth GeoJSON overlay, visible attribution/license metadata, and CI-rendered review artifacts.
- [x] Bundle a generalized Natural Earth public-domain/CC0 world-country map layer with source notice and attribution.
- [x] Add a reproducible source-linked English documentary sample with Urdu translation, bilingual subtitles, offline English narration, Natural Earth MP4 render, and non-publishing release evidence bundle.
- [ ] Add original camera moves, richer vehicle/ship sprites, advanced timeline graphics, and high-quality Urdu/Russian/Chinese narration.
- [x] Add an optional local FFmpeg adapter to mux existing video, narration, and selectable SRT subtitle streams; test command safety and failure handling.
- [x] Run a real synthetic MP4 smoke render and verify video/audio/subtitle streams in the assistant environment.
- [x] Validate SRT cue numbering, timestamp syntax/ranges, cue ordering, overlaps, empty text, and configurable line length.
- [x] Validate rendered output for video/audio/subtitle streams, positive duration, and minimum configured resolution using ffprobe.
- [ ] Verify subtitle-to-audio synchronization, audio quality/levels, and render errors.
- [x] Render a cited-script sample documentary end-to-end in CI; technical validation passes but the sample remains an unapproved editorial draft.

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


## Verified implementation milestones (2026-11-08)

- [x] PR #7 merged: deterministic frame-based MP4 renderer, CLI, bounded resource limits, and CI media smoke test. Merge commit: `ca94f5a20980f0731e8594a10b67f605b10b603f`.
- [x] PR #24 merged: Natural Earth GeoJSON overlay supported directly in MP4 frames; CI renders a 1280×720 map, muxes test audio/SRT, and uploads review artifacts. Merge commit: `1812a53d2517aa246b718ec6b7cfe36b93a190ce`.
- [x] PR #25 draft branch: source-grounded English/Urdu sample documentary; CI generated a 35-second H.264 MP4 with English eSpeak narration and bilingual subtitles, validated all streams, and created a blocked release evidence bundle. **159 unit tests and all 23 validation stages passed** on the current PR head.
- [ ] Human editor must review the actual sample script, Urdu translation, English synthetic voice, map treatment, rights evidence, and final MP4 before approving publication.
- [ ] Human-approved Urdu voice sample, robust audio/subtitle synchronization metrics, advanced camera moves/graphics, richer timeline, secure authenticated editorial dashboard, and YouTube upload integration remain unfinished.


## Optional Urdu neural TTS branch

- [x] Add `edge-tts` as an opt-in dependency (not part of the default install).
- [x] Add explicit Pakistan Urdu neural voices `ur-PK-AsadNeural` and `ur-PK-UzmaNeural` plus English, Russian, and Mandarin voice choices.
- [x] Add output-path, voice allowlist, text-size, rate, timeout, and no-overwrite safeguards with unit tests.
- [ ] Run a live Urdu sample only after an explicit decision to send the script to the online provider; review voice quality before production use.
