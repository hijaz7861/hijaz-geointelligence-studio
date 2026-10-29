"""Generate a human-readable fact-check report from recorded ledgers.

This report summarizes recorded statuses and source metadata. It does not
fetch sources, independently verify claims, or decide whether a claim is true.
"""
from __future__ import annotations
from collections import Counter
import html
from typing import Any
from urllib.parse import urlparse
from app.research.corroboration import assess_corroboration

def _safe_source_link(title: Any, url: Any) -> str:
    label = html.escape(str(title), quote=False)
    raw_url = str(url)
    parsed = urlparse(raw_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or any(ch.isspace() for ch in raw_url):
        return html.escape(raw_url, quote=False)
    return f'<a href="{html.escape(raw_url, quote=True)}">{label}</a>'

def build_fact_check_report(claims: list[dict[str, Any]], sources: list[dict[str, Any]]) -> str:
    by_url = {source["url"]: source for source in sources if isinstance(source, dict) and isinstance(source.get("url"), str)}
    warnings = assess_corroboration(claims, sources)
    warning_map: dict[str, list[dict[str, str]]] = {}
    for warning in warnings:
        warning_map.setdefault(warning["claim"], []).append(warning)
    counts = Counter(claim.get("status", "unknown") for claim in claims if isinstance(claim, dict))
    lines = [
        "# Editorial fact-check report", "",
        "> Automated metadata summary only. This report does not establish truth or replace source review.", "",
        "## Summary", "",
        f"- Claims reviewed: {len(claims)}",
        f"- Sources recorded: {len(sources)}",
        f"- Claims labelled unverified: {counts.get('unverified', 0)}",
        f"- Editorial corroboration warnings: {len(warnings)}", "",
        "## Claim-by-claim review", ""
    ]
    if not claims:
        lines.append("No claims are recorded in the claim ledger.")
    for index, claim in enumerate(claims, 1):
        text = str(claim.get("claim", "(missing claim text)")).replace("\r", " ").replace("\n", " ")
        status = str(claim.get("status", "unknown"))
        refs = claim.get("source_urls", [])
        if not isinstance(refs, list):
            refs = []
        lines.extend([f"### {index}. {html.escape(text, quote=False)}", "", f"- Recorded status: **{html.escape(status, quote=False)}**", f"- Linked sources: {len(refs)}"])
        for url in refs:
            if not isinstance(url, str):
                lines.append("- Invalid non-text source reference in claim ledger.")
                continue
            source = by_url.get(url)
            if source:
                link = _safe_source_link(source.get("title", url), url)
                source_type = html.escape(str(source.get("source_type", "unknown source type")), quote=False)
                published = html.escape(str(source.get("published_at", "date unknown")), quote=False)
                lines.append(f"- Source: {link} — {source_type}; published {published}")
            else:
                lines.append(f"- Source reference not found in supplied source ledger: {html.escape(url, quote=False)}")
        claim_warnings = warning_map.get(str(claim.get("claim", "")).strip(), [])
        if claim_warnings:
            for warning in claim_warnings:
                lines.append(f"- **Review warning ({warning['code']}):** {warning['message']}")
        else:
            lines.append("- Corroboration check: no warning from the current metadata rules; this is not proof of truth.")
        lines.append("")
    lines.extend([
        "## Human review checklist", "",
        "- [ ] Open each source and confirm it directly supports the precise claim wording.",
        "- [ ] Check dates, context, contradictory evidence, and whether sources are genuinely independent.",
        "- [ ] Separate established facts, attributed official statements, analysis, and unresolved allegations.",
        "- [ ] Record editorial approval and resolve release blockers before publication.", ""
    ])
    return "\n".join(lines)
