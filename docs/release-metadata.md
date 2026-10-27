# YouTube release metadata draft

Generate a JSON package containing a title, a source-attributed description, language, target duration, used source URLs, and release blockers:

```sh
python scripts/build_release_metadata.py \
  --project data/projects/sample_project.json \
  --output artifacts/drafts/youtube-metadata.json
```

Use `--sources-file` and `--claims-file` to select a specific project's ledgers. The tool validates project structure and citations, then reports why release is blocked. It always sets `publish_ready` to false because the package is a draft for editorial review; it does not call the YouTube API or upload content.

Before publication, an editor must verify factual wording and citations, clear all media rights, review translations and the final render, and record the required approvals. A title/description draft is not proof that a documentary is accurate, licensed, or ready to publish.
