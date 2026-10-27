# Order Submission Pack — Hijaz Geointelligence Studio

**Delivery classification:** Review/demo package; not a verified final production release.  
**Repository:** https://github.com/hijaz7861/hijaz-geointelligence-studio  
**Reviewed source revision:** `8ac32ce7f45a1208a60c33526ec141b8051e3ed6` (main at time of review)

## What is included

- A modular project structure for research and documentary-production workflows.
- Source/claim ledger inputs and editorial traceability conventions.
- A release-evidence bundle generator that records input hashes, file sizes, claim/source references, media-rights metadata, subtitle structure, render checks, and approval metadata.
- Fail-closed release status: the evidence bundle is review-only and sets `publish_ready=false` and `release_status=draft_blocked`.
- Regression coverage for malformed UTF-8 metadata and placeholder evidence for media marked as original.
- A validation script at `scripts/validate.sh`.

## Current acceptance status

| Area | Status | Evidence / limitation |
|---|---|---|
| Repository source snapshot | Verified remotely | Main revision listed above |
| Release-bundle safeguards | Static review only | Relevant source and regression-test files were inspected remotely |
| Python regression suite | Not verified for this revision | Must run locally; GitHub Actions has intentionally not been triggered |
| End-to-end render/subtitle/evidence bundle | Not verified | Requires real render, subtitle, and reviewed metadata inputs |
| Actual documentary content | Not supplied/verified | Current sample project is explicitly a synthetic fixture |
| Media rights and factual sourcing | Not approved | Requires asset-by-asset rights evidence and human editorial review |
| Final export and client delivery | Not complete/verified | No finished video export has been validated in this review |
| YouTube upload/publication | Not implemented/authorized | The evidence bundle never authorizes upload or publication |

## Local verification procedure

Run from the repository root:

```bash
bash scripts/validate.sh
```

Save the complete terminal output as the test evidence for this handoff. Resolve any failure and rerun the full validation script. Do not describe the build as passing until the actual output is available.

## Required inputs before final production

1. Approved documentary topic, audience, language, target duration, and delivery format.
2. Editor-reviewed script with sourced claims and source access dates.
3. Media manifest with asset origins, licenses/permissions, and evidence; do not infer rights from a filename or from “original” status alone.
4. Final render and matching subtitle file.
5. Completed script, translation, rights, and final-video approvals.
6. Validation output and generated release-evidence JSON.

## Delivery statement for the requester

The repository contains a review-oriented production workflow and evidence-bundle safeguards. The current code has not been runtime-validated in this handoff, and the sample project is a placeholder. Therefore this package should be submitted as a **technical progress / review package**, not represented as a completed final documentary or a production-certified release. A final production claim is appropriate only after the missing inputs, approvals, render, and tests are complete.
