# Cited draft generation

The draft builder turns existing claim-ledger records into a Markdown scaffold. Each factual segment contains the exact tracked claim marker, its evidence label, and one or more source URLs. The output is intentionally labelled as a draft requiring human review.

## Example

```sh
python scripts/build_cited_draft.py \
  --title "Public geopolitical briefing" \
  --language en \
  --output artifacts/drafts/briefing.md
```

Use `--claims-file` and `--sources-file` for a specific research project. Supported language labels are Urdu (`ur`), English (`en`), Russian (`ru`), and Chinese (`zh`). The current builder does not translate or generate polished narration; the language flag labels the draft only.

## Editorial checks before reuse

- Confirm that each source supports the exact claim wording and context.
- Separate official statements from independently established facts.
- Resolve or remove unverified claims; investigate conflicting accounts.
- Rewrite the scaffold into natural narration without dropping its claim markers.
- Run the documentary project validator and obtain the required human approvals.
- Do not publish the scaffold as a finished script.
