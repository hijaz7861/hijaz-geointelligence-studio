# Implementation roadmap and completion gates

This repository is an evolving MVP, not a completed production system. A phase is complete only when its acceptance checks are implemented, run locally, and documented with evidence.

## Phase 1 — Research traceability (in progress)
- [x] Validate source metadata, dates, URLs, and source categories.
- [x] Reject duplicate source URLs.
- [x] Track editorial claims with an allowed status label.
- [x] Reject claim references to URLs absent from the source ledger.
- [x] Run repeatable local unit, syntax, CLI, and smoke checks without GitHub Actions.
- [ ] Add a reviewed-source discovery/import adapter with timeouts, URL allow/deny safeguards, and explicit provenance.
- [ ] Add independent-source corroboration checks as warnings, not automatic truth judgments.

## Phase 2 — Cited editorial package
- [ ] Define a versioned documentary-project schema: topic, audience, language, target duration, claims, citations, media rights, and editor status.
- [ ] Generate a script draft where each factual paragraph references recorded claim IDs.
- [ ] Validate missing citations, unsupported claims, contradictory dates, and unreviewed high-impact statements.
- [ ] Create a fact-check report that distinguishes confirmed facts, attributed claims, analysis, and unresolved questions.
- [ ] Add Urdu and English first, then Russian and Chinese translation with glossary consistency checks.

## Phase 3 — Media production
- [ ] Add a media asset manifest with origin URL, creator, license/permission evidence, attribution, and intended usage.
- [ ] Validate assets before assembly; block assets with unknown rights from release packages.
- [ ] Build original graphics, timelines, maps, captions, and narration tracks.
- [ ] Add an optional local FFmpeg assembly adapter, with dependency detection and a small test fixture.
- [ ] Verify subtitle timing, audio duration, output resolution, and render errors.

## Phase 4 — Release safety and YouTube preparation
- [ ] Generate a release checklist and evidence bundle.
- [ ] Require explicit human approval for script, translations, rights, thumbnail, title, and final render.
- [ ] Prepare metadata and upload package; do not publish automatically by default.
- [ ] If YouTube API upload is later added, use least-privilege OAuth, secret-free logs, draft/private default, and a clear approval gate.

## Phase 5 — Usable application
- [ ] Build a local-first dashboard for research, claims, script drafts, assets, and review status.
- [ ] Add project-scoped storage, backup/restore, audit trail, and safe handling of credentials.
- [ ] Add integration tests, dependency/security checks, and reproducible packaging.
- [ ] Deploy only after local end-to-end tests pass and a hosting target is explicitly configured.

## Definition of complete
The project is not production-complete until a sample documentary can be traced end-to-end from sources to claims to cited multilingual script to rights-cleared assets to a rendered video, with a human approval record and a reproducible test report. A passing unit-test suite alone is not completion.