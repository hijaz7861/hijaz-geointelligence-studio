"""Validated local source ledger for public-interest geopolitical research.

This module records source metadata; it does not independently verify the truth
of a source or claim. It uses only Python's standard library.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "data" / "sources" / "sources.json"
SOURCE_TYPES = {"official_statement", "primary_document", "independent_reporting", "analysis"}
CLAIM_STATUSES = {"verified_fact", "official_claim", "independent_reporting", "analysis", "unverified"}
REQUIRED_FIELDS = ("title", "url", "published_at", "source_type", "claim_status", "notes")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SourceLedgerError(ValueError):
    """Raised when source metadata is incomplete or invalid."""


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.params, parsed.query, ""))


def validate_source(source: dict[str, Any]) -> dict[str, str]:
    if not isinstance(source, dict):
        raise SourceLedgerError("Source must be a JSON object.")
    missing = [field for field in REQUIRED_FIELDS if field not in source]
    if missing:
        raise SourceLedgerError("Missing required fields: " + ", ".join(missing))
    normalized: dict[str, str] = {}
    for field in REQUIRED_FIELDS:
        value = source[field]
        if not isinstance(value, str) or not value.strip():
            raise SourceLedgerError(f"Field '{field}' must be a non-empty string.")
        normalized[field] = value.strip()
    parsed = urlparse(normalized["url"])
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or any(ch.isspace() for ch in normalized["url"]):
        raise SourceLedgerError("URL must be an absolute HTTP or HTTPS URL without whitespace.")
    if not _DATE_RE.fullmatch(normalized["published_at"]):
        raise SourceLedgerError("published_at must be an ISO date (YYYY-MM-DD).")
    try:
        date.fromisoformat(normalized["published_at"])
    except ValueError as exc:
        raise SourceLedgerError("published_at must be a valid calendar date (YYYY-MM-DD).") from exc
    if normalized["source_type"] not in SOURCE_TYPES:
        raise SourceLedgerError("Unsupported source_type.")
    if normalized["claim_status"] not in CLAIM_STATUSES:
        raise SourceLedgerError("Unsupported claim_status.")
    return normalized


def load_sources(path: str | Path = DEFAULT_LEDGER) -> list[dict[str, str]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceLedgerError(f"Cannot read source ledger: {exc}") from exc
    if not isinstance(data, list):
        raise SourceLedgerError("Source ledger must contain a JSON array.")
    return [validate_source(item) for item in data]


def add_source(source: dict[str, Any], path: str | Path = DEFAULT_LEDGER) -> dict[str, str]:
    normalized = validate_source(source)
    existing = load_sources(path)
    canonical = _canonical_url(normalized["url"])
    if any(_canonical_url(item["url"]) == canonical for item in existing):
        raise SourceLedgerError("A source with this URL already exists.")
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    existing.append(normalized)
    temporary = ledger_path.with_suffix(ledger_path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(ledger_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return normalized
