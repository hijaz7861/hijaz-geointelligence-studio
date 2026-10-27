# Documentary project package

A project package is a JSON record with a unique project ID, title, language (`ur`, `en`, `ru`, or `zh`), target duration in seconds, script draft, claim references, media asset manifest, and approval flags. See `data/projects/sample_project.json` for a non-publishable fixture.

The validator checks structural integrity and traceability: referenced claim text must exist in the claim ledger, and each media asset's origin URL must exist in the source ledger. It does not establish that a claim is true, that the source supports the wording, or that a rights declaration is legally valid.

## Script citation markers

Every script paragraph must either cite a claim included in the project's `claim_ids` list or be explicitly labelled as non-factual editorial/structural content. Use the exact claim text in a marker:

```text
[[claim:Exact claim text as recorded in the claim ledger]]
```

Paragraphs beginning with `[EDITORIAL]` or `[TRANSITION]` may be used for clearly identified framing or transitions. Markdown headings and blockquotes are also exempt from the paragraph marker check. These rules are mechanical safeguards; a human must still confirm that each citation genuinely supports its sentence.

## Media rights

Each asset records `asset_id`, `origin_url`, `rights_status`, and `notes`. Allowed statuses are `licensed`, `permission_granted`, `public_domain_verified`, `original`, `unknown`, and `restricted`. `unknown` and `restricted` are release blockers. Store actual license/permission evidence and attribution in notes or linked records; a status label alone is not proof of permission.

## Release gate

A structurally valid project is not automatically publishable. The release checklist also blocks unresolved `unverified` claims, uncleared media, and missing human review for the script, translation, rights, and final video. Public publishing must remain a separate explicit action after a human editor confirms the package.
