# Read-only local dashboard

Start the dashboard with:

```sh
python scripts/run_dashboard.py
```

Open `http://127.0.0.1:8765/` in the same device. The dashboard shows source/claim counts, project validation, corroboration warnings, and release blockers. Machine-readable status is available at `/api/status`.

## Safety boundaries

- The server binds only to loopback (`127.0.0.1` or `localhost`); non-loopback binding is rejected.
- The interface is read-only: GET endpoints only, POST returns 405, unknown paths return 404.
- It sends no-store, nosniff, and restrictive Content Security Policy headers.
- Project title and all displayed values are HTML-escaped.
- It has no upload, publish, source-edit, or secret-management controls.

This is a small local MVP dashboard, not a multi-user or production web application. Do not expose it through a reverse proxy or public tunnel. Authentication, audit controls, project editing, and production deployment are still future work.
