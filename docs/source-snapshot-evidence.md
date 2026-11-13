# Offline source-snapshot evidence

The source-snapshot verifier records the integrity of a local copy of a source that
is already listed in the project's source ledger. It makes **no network requests**.

## Manifest format

Store a JSON array in a manifest file. Each entry must contain exactly these
fields:

```json
[
  {
    "url": "https://example.org/report",
    "snapshot_path": "snapshots/report.html",
    "sha256": "REPLACE_WITH_64_LOWERCASE_HEX_CHARACTERS",
    "captured_at": "2026-11-13T02:00:00Z"
  }
]
```

- `url` must exactly match a URL in the selected source ledger.
- `snapshot_path` is a relative POSIX path from the manifest's directory.
  Absolute paths, parent traversal, symlinks, non-regular files, empty files,
  and files over the configured size limit are rejected.
- `sha256` is the SHA-256 digest of the archived bytes.
- `captured_at` is an operator-supplied ISO-8601 timestamp and must include a
  timezone. The verifier does not independently establish when the file was
  captured.

Generate a digest locally, for example:

```sh
sha256sum snapshots/report.html
```

## Verify a manifest

```sh
python scripts/verify_source_snapshots.py \
  --manifest data/source-snapshots/manifest.json \
  --sources-file data/sources/sources.json
```

The command verifies the local bytes and exact URL linkage. It does not fetch,
resolve, or authenticate the URL.

## Include snapshot evidence in a release review bundle

```sh
python scripts/build_release_bundle.py \
  --project data/projects/sample_project.json \
  --sources-file data/sources/sources.json \
  --claims-file data/sources/claims.json \
  --source-snapshots data/source-snapshots/manifest.json \
  --output artifacts/review/release-evidence.json
```

A valid digest is reported as local snapshot integrity evidence. A missing
snapshot is reported as `NOT_PROVIDED`; an invalid manifest adds a release
blocker. Neither condition is converted into a factual-verification claim.

## Interpretation and safety

A matching digest proves only that the local file's bytes match the manifest.
It does not prove that the file was retrieved from the cited URL, that the
capture timestamp is accurate, that the publisher is authentic, that the
source supports a claim, or that the claim is true. It also does not verify
copyright, license terms, permissions, or media rights.

The release evidence bundle remains `publish_ready=false` and review-only.
No URL fetching, deployment, upload, or YouTube publication is performed.
