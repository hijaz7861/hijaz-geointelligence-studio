"""Loopback-only, read-only dashboard for source and documentary release status."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
import json
from pathlib import Path
from typing import Any
from app.editorial.script_validator import ProjectValidationError, release_blockers, validate_project_file
from app.research.claim_ledger import ClaimLedgerError, load_claims
from app.research.corroboration import assess_corroboration
from app.research.source_ledger import DEFAULT_LEDGER, SourceLedgerError, load_sources
DEFAULT_PROJECT = Path(__file__).resolve().parents[2] / "data" / "projects" / "sample_project.json"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}

def build_status(project_path: str | Path = DEFAULT_PROJECT, source_path: str | Path = DEFAULT_LEDGER, claims_path: str | Path | None = None) -> dict[str, Any]:
    try:
        project = validate_project_file(project_path, claims_path, source_path)
        sources = load_sources(source_path)
        claims = load_claims(claims_path, source_path) if claims_path is not None else load_claims(source_path=source_path)
        blockers = release_blockers(project, claims)
        warnings = assess_corroboration([c for c in claims if c["claim"] in project["claim_ids"]], sources)
        return {"status": "PASS", "project_id": project["project_id"], "title": project["title"], "language": project["language"], "source_count": len(sources), "claim_count": len(claims), "linked_claim_count": len(project["claim_ids"]), "structural_validation": "PASS", "publish_ready": False, "release_blockers": blockers, "corroboration_warnings": warnings, "note": "Read-only local dashboard. Publish-ready remains false until a separate release review."}
    except (ProjectValidationError, ClaimLedgerError, SourceLedgerError, OSError, ValueError) as exc:
        return {"status": "ERROR", "structural_validation": "FAIL", "publish_ready": False, "error": str(exc), "note": "Correct the project or ledger data and re-run validation."}

def render_dashboard_html(status: dict[str, Any]) -> str:
    title = escape(str(status.get("title", "Hijaz GeoIntelligence Studio")))
    status_text = escape(str(status.get("status", "UNKNOWN")))
    source_count = escape(str(status.get("source_count", 0)))
    claim_count = escape(str(status.get("claim_count", 0)))
    linked_count = escape(str(status.get("linked_claim_count", 0)))
    blockers = status.get("release_blockers", [])
    warnings = status.get("corroboration_warnings", [])
    error = status.get("error")
    def list_items(items: list[Any]) -> str:
        return "".join(f"<li>{escape(str(item))}</li>" for item in items) or "<li>None reported</li>"
    warning_items = list_items([f"{w.get('claim', '')}: {w.get('message', '')}" for w in warnings])
    error_html = f"<p class='error'>{escape(str(error))}</p>" if error else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>body{{font:16px system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;background:#f6f7f9;color:#17202a}}h1{{font-size:1.7rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem}}.card{{background:white;border:1px solid #d9dee5;border-radius:12px;padding:1rem}}.muted{{color:#52616b}}.error{{color:#8b1e1e}}code{{overflow-wrap:anywhere}}</style></head><body><h1>{title}</h1><p class="muted">Read-only local status dashboard · no upload/publish controls</p>{error_html}<section class="grid"><div class="card"><div class="muted">Validation</div><strong>{status_text}</strong></div><div class="card"><div class="muted">Sources</div><strong>{source_count}</strong></div><div class="card"><div class="muted">Claims in ledger</div><strong>{claim_count}</strong></div><div class="card"><div class="muted">Claims linked to project</div><strong>{linked_count}</strong></div></section><section class="card"><h2>Release blockers</h2><ul>{list_items(blockers)}</ul></section><section class="card"><h2>Corroboration warnings</h2><ul>{warning_items}</ul></section><p class="muted">{escape(str(status.get('note','')))}</p><p><a href="/api/status">View machine-readable status</a></p></body></html>'''

def make_handler(project_path: str | Path = DEFAULT_PROJECT, source_path: str | Path = DEFAULT_LEDGER, claims_path: str | Path | None = None):
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self) -> None:
            if self.path == "/api/status":
                payload = json.dumps(build_status(project_path, source_path, claims_path), ensure_ascii=False).encode("utf-8")
                self._send(payload, "application/json; charset=utf-8")
            elif self.path == "/":
                payload = render_dashboard_html(build_status(project_path, source_path, claims_path)).encode("utf-8")
                self._send(payload, "text/html; charset=utf-8")
            else:
                self._send(b"Not found", "text/plain; charset=utf-8", 404)
        def do_POST(self) -> None:
            self._send(b"Read-only dashboard", "text/plain; charset=utf-8", 405)
        def log_message(self, format: str, *args: Any) -> None:
            return
    return DashboardHandler

def create_server(host: str = "127.0.0.1", port: int = 8765, project_path: str | Path = DEFAULT_PROJECT, source_path: str | Path = DEFAULT_LEDGER, claims_path: str | Path | None = None) -> ThreadingHTTPServer:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("Dashboard must bind to localhost/loopback only.")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535.")
    handler = make_handler(project_path, source_path, claims_path)
    return ThreadingHTTPServer((host, port), handler)
