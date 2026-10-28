# CI validation

The GitHub Actions workflow at `.github/workflows/validate.yml` runs
`bash scripts/validate.sh` for pull requests that touch application code,
tests, scripts, project data, documentation, the workflow itself, or README.

The workflow is read-only, uses Python 3.12, cancels superseded runs for the
same pull request, and has a 10-minute job timeout. It does not publish videos,
deploy services, or upload project content.

A green workflow means the repository's scripted validation checks passed in
that runner environment. Optional checks (such as FFmpeg integration) may be
skipped when their tools are not installed; inspect the job log before treating
a skipped check as verified.
