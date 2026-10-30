"""Tamper-evident, project-bound editorial approval receipts.

HMAC proves receipt integrity and possession of a shared project key. It does not
independently authenticate a reviewer's legal identity or establish factual truth.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import stat
from typing import Any

APPROVAL_STAGES = (
    "script_reviewed",
    "translation_reviewed",
    "media_rights_reviewed",
    "final_video_reviewed",
)
DECISIONS = {"approved", "rejected"}


class ApprovalReceiptError(ValueError):
    """Raised when approval receipts or signing-key material is invalid."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).expanduser().resolve().open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_key(path: str | Path) -> bytes:
    key_path = Path(path).expanduser()
    if key_path.is_symlink() or not key_path.is_file():
        raise ApprovalReceiptError("Approval key must be an existing regular file, not a symlink.")
    if os.name == "posix":
        mode = stat.S_IMODE(key_path.stat().st_mode)
        if mode & 0o077:
            raise ApprovalReceiptError("Approval key permissions are too broad; restrict the key file to owner-only access (0600).")
    key = key_path.read_bytes()
    if len(key) < 32:
        raise ApprovalReceiptError("Approval key must contain at least 32 random bytes.")
    return key


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _project_id(project_path: str | Path) -> str:
    try:
        project = json.loads(Path(project_path).expanduser().read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ApprovalReceiptError(f"Cannot read project JSON: {exc}") from exc
    if not isinstance(project, dict) or not isinstance(project.get("project_id"), str) or not project["project_id"].strip():
        raise ApprovalReceiptError("Project must contain a non-empty project_id.")
    return project["project_id"]


def _validate_reviewed_at(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalReceiptError("reviewed_at must be an ISO-8601 timestamp with a timezone.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApprovalReceiptError("reviewed_at must be a valid ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ApprovalReceiptError("reviewed_at must include a timezone.")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_receipt_document(path: str | Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ApprovalReceiptError(f"Cannot read approval receipts JSON: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise ApprovalReceiptError("Approval receipts must use schema_version 1.0.")
    if not isinstance(document.get("receipts"), list):
        raise ApprovalReceiptError("Approval receipts document must contain a receipts array.")
    return document


def _write_receipt_document(path: str | Path, document: dict[str, Any]) -> Path:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.replace(output)
    except OSError as exc:
        raise ApprovalReceiptError(f"Cannot write approval receipts: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return output


def record_approval(
    project_path: str | Path,
    receipts_path: str | Path,
    key_path: str | Path,
    *,
    stage: str,
    decision: str,
    reviewer: str,
    reason: str,
    artifact_path: str | Path | None = None,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Append one signed review receipt without modifying the project or render."""
    if stage not in APPROVAL_STAGES:
        raise ApprovalReceiptError("Unsupported approval stage.")
    if decision not in DECISIONS:
        raise ApprovalReceiptError("decision must be approved or rejected.")
    if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer.strip()) > 120:
        raise ApprovalReceiptError("reviewer must be a non-empty string of at most 120 characters.")
    if not isinstance(reason, str) or len(reason.strip()) < 5 or len(reason.strip()) > 1000:
        raise ApprovalReceiptError("reason must contain 5 to 1000 characters.")
    if stage == "final_video_reviewed" and artifact_path is None:
        raise ApprovalReceiptError("final_video_reviewed requires --artifact pointing to the exact MP4 reviewed.")
    if stage != "final_video_reviewed" and artifact_path is not None:
        raise ApprovalReceiptError("Only final_video_reviewed accepts an --artifact path.")
    project = Path(project_path).expanduser().resolve()
    receipts = Path(receipts_path).expanduser().resolve()
    key_file = Path(key_path).expanduser().resolve()
    artifact = Path(artifact_path).expanduser().resolve() if artifact_path is not None else None
    if not project.is_file():
        raise ApprovalReceiptError("Project file does not exist.")
    if receipts in {project, key_file, artifact}:
        raise ApprovalReceiptError("Receipts output must differ from project, key, and artifact inputs.")
    key = _read_key(key_file)
    payload = {
        "schema_version": "1.0",
        "project_id": _project_id(project),
        "stage": stage,
        "decision": decision,
        "reviewer": reviewer.strip(),
        "reason": reason.strip(),
        "reviewed_at": _validate_reviewed_at(reviewed_at or datetime.now(timezone.utc).isoformat(timespec="seconds")),
        "project_sha256": sha256_file(project),
        "artifact_sha256": sha256_file(artifact) if artifact is not None else None,
    }
    document = _read_receipt_document(receipts) if receipts.exists() else {"schema_version": "1.0", "receipts": []}
    if any(isinstance(item, dict) and isinstance(item.get("payload"), dict) and item["payload"].get("stage") == stage for item in document["receipts"]):
        raise ApprovalReceiptError(f"A receipt already exists for {stage}; create a new receipts file for a revised review.")
    signature = hmac.new(key, _canonical_payload(payload), hashlib.sha256).hexdigest()
    signed = {"payload": payload, "signature": signature}
    document["receipts"].append(signed)
    _write_receipt_document(receipts, document)
    return {"stage": stage, "decision": decision, "reviewer": payload["reviewer"], "reviewed_at": payload["reviewed_at"], "receipt_sha256": hashlib.sha256(_canonical_payload(signed)).hexdigest()}


def verify_approval_receipts(
    project_path: str | Path,
    receipts_path: str | Path,
    key_path: str | Path,
    *,
    render_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify all four approved stages against the current project and reviewed MP4."""
    key = _read_key(key_path)
    project = Path(project_path).expanduser().resolve()
    document = _read_receipt_document(receipts_path)
    project_digest = sha256_file(project)
    project_id = _project_id(project)
    expected_render_digest = sha256_file(render_path) if render_path is not None and Path(render_path).expanduser().is_file() else None
    by_stage: dict[str, dict[str, Any]] = {}
    for item in document["receipts"]:
        if not isinstance(item, dict) or not isinstance(item.get("payload"), dict) or not isinstance(item.get("signature"), str):
            raise ApprovalReceiptError("Each receipt must contain a payload object and signature.")
        payload = item["payload"]
        signature = item["signature"]
        expected = hmac.new(key, _canonical_payload(payload), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ApprovalReceiptError("Approval receipt signature is invalid; the receipt may have been altered or signed with another key.")
        stage = payload.get("stage")
        if stage not in APPROVAL_STAGES:
            raise ApprovalReceiptError("Receipt contains an unsupported approval stage.")
        if stage in by_stage:
            raise ApprovalReceiptError(f"Duplicate approval receipts found for {stage}.")
        if payload.get("schema_version") != "1.0" or payload.get("project_id") != project_id:
            raise ApprovalReceiptError("Receipt project identity does not match the current project.")
        if payload.get("project_sha256") != project_digest:
            raise ApprovalReceiptError("Project changed after approval; obtain fresh review receipts.")
        if payload.get("decision") not in DECISIONS:
            raise ApprovalReceiptError("Receipt contains an invalid decision.")
        if not isinstance(payload.get("reviewer"), str) or not payload["reviewer"].strip():
            raise ApprovalReceiptError("Receipt reviewer is missing.")
        if not isinstance(payload.get("reason"), str) or len(payload["reason"].strip()) < 5:
            raise ApprovalReceiptError("Receipt review reason is missing or too short.")
        _validate_reviewed_at(payload.get("reviewed_at"))
        artifact_digest = payload.get("artifact_sha256")
        if stage == "final_video_reviewed":
            if expected_render_digest is None:
                raise ApprovalReceiptError("Final-video receipt cannot be verified without the current MP4.")
            if artifact_digest != expected_render_digest:
                raise ApprovalReceiptError("Reviewed MP4 changed after final-video approval; obtain a fresh review.")
        elif artifact_digest is not None:
            raise ApprovalReceiptError(f"{stage} must not include an artifact hash.")
        if payload.get("decision") != "approved":
            raise ApprovalReceiptError(f"Human review rejected stage {stage}.")
        by_stage[stage] = payload
    missing = [stage for stage in APPROVAL_STAGES if stage not in by_stage]
    if missing:
        raise ApprovalReceiptError("Missing approved receipt stages: " + ", ".join(missing))
    return {
        "validation": "PASS",
        "signature_algorithm": "HMAC-SHA256",
        "verified_stages": [
            {"stage": stage, "reviewer": by_stage[stage]["reviewer"], "reviewed_at": by_stage[stage]["reviewed_at"], "artifact_sha256": by_stage[stage]["artifact_sha256"]}
            for stage in APPROVAL_STAGES
        ],
        "identity_assurance": "Receipt integrity and shared-key possession only; reviewer identity is self-asserted, not independently authenticated.",
    }


def create_approval_key(path: str | Path) -> Path:
    """Create a new 256-bit key using owner-only permissions; never overwrite."""
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ApprovalReceiptError(f"Refusing to overwrite existing key file: {output}")
    fd = None
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, secrets.token_bytes(32))
        os.fsync(fd)
    except OSError as exc:
        raise ApprovalReceiptError(f"Cannot create approval key: {exc}") from exc
    finally:
        if fd is not None:
            os.close(fd)
    if os.name == "posix":
        output.chmod(0o600)
    return output
