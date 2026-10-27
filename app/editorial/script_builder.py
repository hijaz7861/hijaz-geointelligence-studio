"""Build a traceable, human-review-required script scaffold from recorded claims."""
from __future__ import annotations
from pathlib import Path
from app.research.claim_ledger import ClaimLedgerError, load_claims

class ScriptBuildError(ValueError):
    """Raised when a cited draft cannot be generated safely."""

def build_cited_draft(claims: list[dict], *, title: str, language: str = "en") -> str:
    if not isinstance(title, str) or not title.strip():
        raise ScriptBuildError("title must be a non-empty string.")
    if language not in {"ur", "en", "ru", "zh"}:
        raise ScriptBuildError("language must be one of: ur, en, ru, zh.")
    if not claims:
        raise ScriptBuildError("No claims available; add reviewed claims before building a draft.")
    lines = [f"# {title.strip()}", "", f"[EDITORIAL] Draft language: {language}. This is a traceability scaffold, not publication-ready narration. A human editor must verify every source and rewrite for clarity and context.", ""]
    for index, item in enumerate(claims, 1):
        claim = item.get("claim", "").strip()
        status = item.get("status", "unverified")
        urls = item.get("source_urls", [])
        if not claim or not urls:
            raise ScriptBuildError(f"Claim {index} is missing its text or source URLs.")
        if "\n" in claim or "\r" in claim or "[[claim:" in claim or "]]" in claim:
            raise ScriptBuildError(f"Claim {index} must be a single line without citation-marker delimiters.")
        lines.append(f"## Segment {index}")
        lines.append("")
        lines.append(f"[[claim:{claim}]] {claim}")
        lines.append("")
        lines.append(f"[EDITORIAL] Evidence label: {status}. Confirm that each linked source directly supports the exact wording before narration.")
        lines.append("")
        for url in urls:
            lines.append(f"[EDITORIAL] Source: {url}")
        lines.append("")
    lines.append("[EDITORIAL] End of draft. Resolve unverified claims, check contradictory evidence, confirm media rights, and obtain human approval before release.")
    return "\n".join(lines).rstrip() + "\n"

def build_from_ledger(*, title: str, language: str = "en", claims_path: str | Path | None = None, source_path: str | Path | None = None) -> str:
    try:
        if claims_path is None and source_path is None:
            claims = load_claims()
        elif claims_path is None:
            claims = load_claims(source_path=source_path)
        else:
            claims = load_claims(claims_path, source_path) if source_path is not None else load_claims(claims_path)
    except ClaimLedgerError as exc:
        raise ScriptBuildError(f"Cannot load claims for draft: {exc}") from exc
    return build_cited_draft(claims, title=title, language=language)
