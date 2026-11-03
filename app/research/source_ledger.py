"""Validated local source ledger for public-interest geopolitical research.

This module records source metadata; it does not independently verify the truth
of a source or claim. It uses only Python's standard library.
"""
from __future__ import annotations

import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit, urlunparse, urlunsplit

DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "data" / "sources" / "sources.json"
SOURCE_TYPES = {"official_statement", "primary_document", "independent_reporting", "analysis"}
CLAIM_STATUSES = {"verified_fact", "official_claim", "independent_reporting", "analysis", "unverified"}
REQUIRED_FIELDS = ("title", "url", "published_at", "source_type", "claim_status", "notes")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SourceLedgerError(ValueError):
    """Raised when source metadata is incomplete or invalid."""


def _canonical_host(hostname: str) -> str:
    """Return a stable ASCII host representation or reject malformed hosts."""
    if "%" in hostname:
        raise SourceLedgerError("Citation URL host must not contain an escaped or scoped address.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            ascii_host = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise SourceLedgerError("Citation URL hostname is not valid IDNA.") from exc
        if ascii_host.endswith("."):
            ascii_host = ascii_host[:-1]
        labels = ascii_host.split(".")
        if not ascii_host or len(ascii_host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in labels
        ):
            raise SourceLedgerError("Citation URL hostname contains an invalid DNS label.")
        return ascii_host
    if address.version == 6:
        return f"[{address.compressed.lower()}]"
    return address.compressed


def validate_http_url(url: str) -> str:
    """Validate an absolute HTTP(S) citation URL without fetching it."""
    if not isinstance(url, str) or not url.strip():
        raise SourceLedgerError("URL must be an absolute HTTP or HTTPS URL.")
    candidate = url.strip()
    if any(ch.isspace() or ord(ch) < 0x20 for ch in candidate) or "\\" in candidate:
        raise SourceLedgerError("URL must not contain whitespace, control characters, or backslashes.")
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise SourceLedgerError("URL must be a syntactically valid absolute HTTP or HTTPS URL.") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname:
        raise SourceLedgerError("URL must be an absolute HTTP or HTTPS URL with a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise SourceLedgerError("Citation URLs must not contain embedded username or password credentials.")
    if parsed.netloc.endswith(":"):
        raise SourceLedgerError("Citation URL must not contain an empty port.")
    if port is not None and not 1 <= port <= 65535:
        raise SourceLedgerError("Citation URL port must be between 1 and 65535.")
    _canonical_host(hostname)
    return candidate


def canonicalize_http_url(url: str) -> str:
    """Build a comparison key; preserve the submitted URL in ledger output."""
    candidate = validate_http_url(url)
    parsed = urlsplit(candidate)
    scheme = parsed.scheme.lower()
    host = _canonical_host(parsed.hostname or "")
    port = parsed.port
    if port == (443 if scheme == "https" else 80):
        port = None
    netloc = host if port is None else f"{host}:{port}"
    return urlunsplit((scheme, netloc, parsed.path.rstrip("/"), parsed.query, ""))


def _canonical_url(url: str) -> str:
    """Backward-compatible internal alias for source duplicate detection."""
    return canonicalize_http_url(url)


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
    normalized["url"] = validate_http_url(normalized["url"])
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
    canonical = canonicalize_http_url(normalized["url"])
    if any(canonicalize_http_url(item["url"]) == canonical for item in existing):
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
