# Editorial fact-check report

Generate a Markdown review report from the recorded claim and source ledgers:

```bash
python3 scripts/build_fact_check_report.py --output artifacts/fact-check-report.md
```

Use `--claims-file` and `--sources-file` to select alternate ledgers. Existing output is protected unless `--overwrite` is explicitly supplied.

The report lists each claim's recorded status, linked source metadata, and the current corroboration warnings. It flags unverified claims and cases with no or only one independent-reporting domain. A missing warning does not prove a claim is accurate. The tool does not fetch pages, evaluate the evidence text, identify copied reporting, or independently establish truth. An editor must open sources, assess context and contradictions, and approve the final script.
