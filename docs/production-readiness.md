# Production readiness and delivery plan

## Purpose

This project is intended for the owner's regular use and controlled sharing with a trusted collaborator. It must not be described as production-complete merely because a demo fixture or unit test passes.

## Current verified repository capabilities

- Source and claim ledgers with URL traceability and metadata validation.
- Optional guarded RSS/Atom metadata intake.
- Cited draft and translation-structure checks.
- Local subtitle validation, optional local narration, and FFmpeg/ffprobe adapters.
- Release metadata and a deterministic release-evidence report that never grants publish permission.
- A loopback-only, read-only dashboard.

These are repository-level capabilities. This document does not claim the latest commit has passed a fresh runtime test in this environment.

## Production blockers before relying on this for a paid/customer deliverable

1. **Runtime verification:** run `bash scripts/validate.sh` on the target environment and preserve the full output. The latest release-bundle changes have not been runtime-verified here.
2. **Real end-to-end sample:** create one explicitly labelled test documentary using verifiable sources, stable claim references, original/licensed assets, reviewed narration, subtitles, an actual MP4 render, metadata draft, and release evidence. Do not use the synthetic sample fixture as customer content.
3. **Usable project workflow:** dashboard is currently read-only. Project creation/editing, review queues, asset management, and job status are not implemented as a secure multi-user application.
4. **Collaboration/security:** before sharing over a network, implement authentication, user roles, project isolation, audit logging, safe secret handling, backups/restore, and deployment security. Do not expose the current loopback dashboard publicly.
5. **Media quality:** validate Urdu voice availability/provider, subtitle/audio synchronization, loudness, caption quality, render failures, and original graphics. English/Russian/Chinese local eSpeak availability does not establish broadcast quality.
6. **Editorial assurance:** add a human-readable fact-check report and stronger unsupported-claim/contradiction review. Metadata links alone cannot prove claims.
7. **Rights evidence:** record actual license/permission URLs, usage scope, expiry/review dates, and attribution. Rights status alone is not legal proof.
8. **Release workflow:** keep final script, translation, rights, and video approval explicit. YouTube upload/publishing is not implemented and must remain a separate approved action.
9. **Operational packaging:** document a clean setup, dependency checks, backups, recovery, logs, and a repeatable local runbook. Deployment should follow—not precede—successful end-to-end tests.

## Safe local validation

From the repository root:

```sh
bash scripts/validate.sh
```

This intentionally avoids GitHub Actions minutes. On Android/Termux, first confirm Python 3.10+ and any optional FFmpeg/ffprobe/eSpeak binaries required by the desired workflow. Optional integrations may be skipped when tools are unavailable; record those skips.

## Release decision

**Current status: NOT PRODUCTION-READY / INTERNAL DEVELOPMENT.**

The codebase has useful implemented components, but the full production workflow and secure collaboration layer are incomplete. Do not represent the sample project as a finished documentary or claim the system is fully tested until the above evidence exists.
