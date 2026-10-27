"""Claim ledger that links editorial statements to recorded sources.

This validates traceability metadata only. It cannot prove a claim is true.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.research.source_ledger import DEFAULT_LEDGER, SourceLedgerError, load_sources

DEFAULT_CLAIMS = Path(__file__).resolve().parents[2] / "data" / "sources" / "claims.json"
CLAIM_STATUSES = {"verified_fact", "official_claim", "independent_reporting", "analysis", "unverified"}
REQUIRED_FIELDS = ("claim", "status", "source_urls", "notes")


class ClaimLedgerError(ValueError):
    """Raised when claim metadata or its source links are invalid."""


def validate_claim(claim: dict[str, Any], known_urls: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(claim, dict):
        raise ClaimLedgerError("Claim must be a JSON object.")
    missing = [field for field in REQUIRED_FIELDS if field not in claim]
    if missing:
        raise ClaimLedgerError("Missing required fields: " + ", ".join(missing))
    text_fields: dict[str, str] = {}
    for field in ("claim", "status", "notes"):
        value = claim[field]
        if not isinstance(value, str) or not value.strip():
            raise ClaimLedgerError(f"Field '{field}' must be a non-empty string.")
        text_fields[field] = value.strip()
    if text_fields["status"] not in CLAIM_STATUSES:
        raise ClaimLedgerError("Unsupported claim status.")
    urls = claim["source_urls"]
    if not isinstance(urls, list) or not urls:
        raise ClaimLedgerError("source_urls must be a non-empty JSON array.")
    clean_urls: list[str] = []
    for url in urls:
        if not isinstance(url, str) or not url.strip() or not re.match(r"^https?://", url.strip(), re.I):
            raise ClaimLedgerError("Each source URL must be an absolute HTTP or HTTPS URL.")
        normalized_url = url.strip()
        if normalized_url in clean_urls:
            raise ClaimLedgerError("Duplicate source URL in claim.")
        if known_urls is not None and normalized_url not in known_urls:
            raise ClaimLedgerError(f"Claim references a URL absent from the source ledger: {normalized_url}")
        clean_urls.append(normalized_url)
    return {**text_fields, "source_urls": clean_urls}


def load_claims(path: str | Path = DEFAULT_CLAIMS, source_path: str | Path = DEFAULT_LEDGER) -> list[dict[str, Any]]:
    claims_path = Path(path)
    if not claims_path.exists():
        return []
    try:
        raw = json.loads(claims_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimLedgerError(f"Cannot read claim ledger: {exc}") from exc
    if not isinstance(raw, list):
        raise ClaimLedgerError("Claim ledger must contain a JSON array.")
    try:
        known_urls = {item["url"] for item in load_sources(source_path)}
    except SourceLedgerError as exc:
        raise ClaimLedgerError(f"Cannot validate source references: {exc}") from exc
    claims = [validate_claim(item, known_urls) for item in raw]
    seen = set()
    for item in claims:
        key = item["claim"].casefold()
        if key in seen:
            raise ClaimLedgerError("Duplicate claim text is not allowed.")
        seen.add(key)
    return claims


def add_claim(claim: dict[str, Any], path: str | Path = DEFAULT_CLAIMS, source_path: str | Path = DEFAULT_LEDGER) -> dict[str, Any]:
    try:
        known_urls = {item["url"] for item in load_sources(source_path)}
    except SourceLedgerError as exc:
        raise ClaimLedgerError(f"Cannot validate source references: {exc}") from exc
    normalized = validate_claim(claim, known_urls)
    existing = load_claims(path, source_path)
    if any(item["claim"].casefold() == normalized["claim"].casefold() for item in existing):
        raise ClaimLedgerError("Duplicate claim text is not allowed.")
    claims_path = Path(path)
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    existing.append(normalized)
    temporary = claims_path.with_suffix(claims_path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(claims_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return normalized
