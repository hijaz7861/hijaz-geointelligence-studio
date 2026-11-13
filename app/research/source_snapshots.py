"""Offline integrity checks for locally archived citation snapshots.

A matching digest proves only that local bytes match a supplied manifest. It does
not prove the archive came from the cited URL, that the publisher is authentic,
that the source supports a claim, or that the claim is true.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlparse

MAX_MANIFEST_BYTES = 1_048_576
DEFAULT_MAX_SNAPSHOT_BYTES = 25 * 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_FIELDS = {"url", "snapshot_path", "sha256", "captured_at"}


class SourceSnapshotError(ValueError):
    """Raised when a local source-snapshot manifest or archive is invalid."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceSnapshotError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str):
    raise SourceSnapshotError(f"Non-standard JSON constant is not allowed: {value}")


def _parse_capture_time(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceSnapshotError("captured_at must be an ISO-8601 timestamp with a timezone.")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate)
    except ValueError as exc:
        raise SourceSnapshotError("captured_at must be a valid ISO-8601 timestamp with a timezone.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceSnapshotError("captured_at must include an explicit timezone or UTC offset.")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_http_url(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SourceSnapshotError("Snapshot URL must exactly match a non-empty source-ledger URL.")
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise SourceSnapshotError("Snapshot URL is malformed.") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname:
        raise SourceSnapshotError("Snapshot URL must be an absolute HTTP(S) URL with a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise SourceSnapshotError("Snapshot URL must not contain embedded credentials.")
    if any(character.isspace() or ord(character) < 0x20 for character in value) or "\\" in value:
        raise SourceSnapshotError("Snapshot URL must not contain whitespace, controls, or backslashes.")
    return value


def _safe_relative_path(root: Path, value: object) -> tuple[Path, str]:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SourceSnapshotError("snapshot_path must be a non-empty relative POSIX path.")
    if "\\" in value or "\x00" in value:
        raise SourceSnapshotError("snapshot_path must use relative POSIX separators only.")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SourceSnapshotError("snapshot_path must not contain empty, dot, or parent-traversal segments.")
    relative = PurePosixPath(value)
    if relative.is_absolute():
        raise SourceSnapshotError("snapshot_path must be relative to the manifest directory.")

    candidate = root
    for index, part in enumerate(parts):
        candidate = candidate / part
        try:
            info = candidate.lstat()
        except OSError as exc:
            raise SourceSnapshotError(f"Cannot inspect snapshot_path {value!r}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise SourceSnapshotError(f"Symlinks are not allowed in snapshot_path: {value!r}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise SourceSnapshotError(f"snapshot_path parent is not a directory: {value!r}")
        if index == len(parts) - 1 and not stat.S_ISREG(info.st_mode):
            raise SourceSnapshotError(f"snapshot_path must identify a regular file: {value!r}")
    return candidate, value


def _hash_snapshot(path: Path, max_bytes: int) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SourceSnapshotError(f"Cannot safely open source snapshot {path.name!r}: {exc}") from exc
    digest = hashlib.sha256()
    total = 0
    try:
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise SourceSnapshotError("Source snapshot must be a regular file.")
            if info.st_size <= 0:
                raise SourceSnapshotError("Source snapshot must not be empty.")
            if info.st_size > max_bytes:
                raise SourceSnapshotError(f"Source snapshot exceeds the {max_bytes}-byte size limit.")
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                total += len(chunk)
                if total > max_bytes:
                    raise SourceSnapshotError(f"Source snapshot exceeds the {max_bytes}-byte size limit.")
                digest.update(chunk)
    except OSError as exc:
        raise SourceSnapshotError(f"Cannot read source snapshot: {exc}") from exc
    return digest.hexdigest(), total


def verify_source_snapshots(
    manifest_path: str | Path,
    known_source_urls: Iterable[str],
    *,
    max_snapshot_bytes: int = DEFAULT_MAX_SNAPSHOT_BYTES,
) -> dict:
    """Verify local snapshot bytes against a strict manifest and source ledger.

    Manifest schema: a JSON array of objects containing exactly url,
    snapshot_path, sha256, and captured_at. Paths are relative to the manifest.
    No network requests are made.
    """
    if isinstance(max_snapshot_bytes, bool) or not isinstance(max_snapshot_bytes, int) or max_snapshot_bytes < 1:
        raise SourceSnapshotError("max_snapshot_bytes must be a positive integer.")
    path = Path(manifest_path).expanduser()
    try:
        manifest_info = path.lstat()
    except OSError as exc:
        raise SourceSnapshotError(f"Cannot inspect snapshot manifest: {exc}") from exc
    if stat.S_ISLNK(manifest_info.st_mode) or not stat.S_ISREG(manifest_info.st_mode):
        raise SourceSnapshotError("Snapshot manifest must be a regular, non-symlink file.")
    if manifest_info.st_size > MAX_MANIFEST_BYTES:
        raise SourceSnapshotError(f"Snapshot manifest exceeds the {MAX_MANIFEST_BYTES}-byte size limit.")
    try:
        raw = path.read_bytes()
        manifest = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except SourceSnapshotError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceSnapshotError(f"Cannot read UTF-8 JSON snapshot manifest: {exc}") from exc
    if not isinstance(manifest, list):
        raise SourceSnapshotError("Snapshot manifest must contain a JSON array.")

    root = path.parent.resolve()
    known = set(known_source_urls)
    seen_urls: set[str] = set()
    seen_paths: set[str] = set()
    entries = []
    for index, item in enumerate(manifest):
        if not isinstance(item, dict):
            raise SourceSnapshotError(f"Manifest entry {index + 1} must be a JSON object.")
        if set(item) != _REQUIRED_FIELDS:
            missing = sorted(_REQUIRED_FIELDS - set(item))
            extra = sorted(set(item) - _REQUIRED_FIELDS)
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("unknown: " + ", ".join(extra))
            raise SourceSnapshotError(f"Manifest entry {index + 1} has invalid fields ({'; '.join(details)}).")

        url = _validate_http_url(item["url"])
        if url not in known:
            raise SourceSnapshotError(f"Snapshot URL is absent from the source ledger: {url}")
        if url in seen_urls:
            raise SourceSnapshotError(f"Duplicate snapshot URL: {url}")
        seen_urls.add(url)

        expected_digest = item["sha256"]
        if not isinstance(expected_digest, str) or not _SHA256_RE.fullmatch(expected_digest):
            raise SourceSnapshotError(f"Manifest entry {index + 1} sha256 must be 64 lowercase hexadecimal characters.")
        captured_at = _parse_capture_time(item["captured_at"])
        snapshot_path, relative_path = _safe_relative_path(root, item["snapshot_path"])
        if relative_path in seen_paths:
            raise SourceSnapshotError(f"Duplicate snapshot_path: {relative_path}")
        seen_paths.add(relative_path)

        actual_digest, size_bytes = _hash_snapshot(snapshot_path, max_snapshot_bytes)
        if actual_digest != expected_digest:
            raise SourceSnapshotError(f"SHA-256 mismatch for source snapshot: {relative_path}")
        entries.append({
            "url": url,
            "snapshot_path": relative_path,
            "captured_at": captured_at,
            "sha256": actual_digest,
            "size_bytes": size_bytes,
            "integrity": "PASS",
            "url_match": "EXACT_SOURCE_LEDGER_URL",
        })

    return {
        "validation": "PASS",
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "entry_count": len(entries),
        "verified_count": len(entries),
        "entries": entries,
        "method": "Local byte-level SHA-256 comparison; no network retrieval or source-authenticity check.",
        "limitations": [
            "A matching digest proves only that local bytes match this manifest.",
            "It does not prove the archive was retrieved from the cited URL or at the stated time.",
            "It does not prove publisher identity, source credibility, claim support, factual truth, or licensing.",
        ],
    }
