"""Validate a structured documentary package for traceability and release readiness.

This is a deterministic checklist, not a fact-checking or editorial judgment engine.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
from app.research.claim_ledger import ClaimLedgerError, load_claims
from app.research.source_ledger import DEFAULT_LEDGER, SourceLedgerError, load_sources
DEFAULT_PROJECT = Path(__file__).resolve().parents[2] / "data" / "projects" / "sample_project.json"
REQUIRED_PROJECT_FIELDS = ("project_id", "title", "language", "target_duration_seconds", "script", "claim_ids", "media_assets", "approval")
SUPPORTED_LANGUAGES = {"ur", "en", "ru", "zh"}
APPROVAL_FIELDS = ("script_reviewed", "translation_reviewed", "media_rights_reviewed", "final_video_reviewed", "approved_by")
class ProjectValidationError(ValueError):
    """Raised when a documentary project is structurally invalid."""
def validate_project(project: dict[str, Any], claims: list[dict[str, Any]], source_urls: set[str]) -> dict[str, Any]:
    if not isinstance(project, dict): raise ProjectValidationError("Project must be a JSON object.")
    missing = [key for key in REQUIRED_PROJECT_FIELDS if key not in project]
    if missing: raise ProjectValidationError("Missing required project fields: " + ", ".join(missing))
    for key in ("project_id", "title", "language", "script"):
        if not isinstance(project[key], str) or not project[key].strip(): raise ProjectValidationError(f"Field '{key}' must be a non-empty string.")
    if project["language"] not in SUPPORTED_LANGUAGES: raise ProjectValidationError("language must be one of: en, ur, ru, zh.")
    duration = project["target_duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0: raise ProjectValidationError("target_duration_seconds must be a positive integer.")
    claim_ids = project["claim_ids"]
    if not isinstance(claim_ids, list) or any(not isinstance(x, str) or not x.strip() for x in claim_ids): raise ProjectValidationError("claim_ids must be an array of non-empty strings.")
    if len(set(claim_ids)) != len(claim_ids): raise ProjectValidationError("claim_ids must not contain duplicates.")
    known_claims = {c["claim"] for c in claims}
    missing_claims = [x for x in claim_ids if x not in known_claims]
    if missing_claims: raise ProjectValidationError("Project references claims absent from the claim ledger: " + "; ".join(missing_claims))
    # Every factual paragraph must cite a tracked claim or be explicitly labelled editorial/structural.
    for paragraph in (part.strip() for part in project["script"].split("\n\n") if part.strip()):
        if paragraph.startswith(("#", "[EDITORIAL]", "[TRANSITION]", ">")): continue
        markers = re.findall(r"\[\[claim:(.*?)\]\]", paragraph)
        if not markers: raise ProjectValidationError("Script paragraph lacks a claim citation marker or an [EDITORIAL]/[TRANSITION] label.")
        for marker in markers:
            if marker not in claim_ids: raise ProjectValidationError(f"Script cites a claim not listed in project claim_ids: {marker}")
    assets = project["media_assets"]
    if not isinstance(assets, list): raise ProjectValidationError("media_assets must be a JSON array.")
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict): raise ProjectValidationError(f"media_assets[{index}] must be an object.")
        for key in ("asset_id", "origin_url", "rights_status", "creator", "attribution", "usage_scope", "rights_evidence", "notes":
            if not isinstance(asset.get(key), str) or not asset[key].strip(): raise ProjectValidationError(f"media_assets[{index}].{key} must be a non-empty string.")
        if asset["origin_url"] not in source_urls: raise ProjectValidationError(f"Media asset origin URL is not in source ledger: {asset['origin_url']}")
        if asset["rights_status"] not in {"licensed", "permission_granted", "public_domain_verified", "original", "unknown", "restricted"}: raise ProjectValidationError(f"Unsupported rights_status for media_assets[{index}].")
    approval = project["approval"]
    if not isinstance(approval, dict): raise ProjectValidationError("approval must be a JSON object.")
    for key in APPROVAL_FIELDS[:-1]:
        if not isinstance(approval.get(key), bool): raise ProjectValidationError(f"approval.{key} must be a boolean.")
    if not isinstance(approval.get("approved_by"), str): raise ProjectValidationError("approval.approved_by must be a string.")
    return project
def validate_project_file(project_path: str | Path = DEFAULT_PROJECT, claims_path: str | Path | None = None, source_path: str | Path = DEFAULT_LEDGER) -> dict[str, Any]:
    try: project = json.loads(Path(project_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise ProjectValidationError(f"Cannot read project file: {exc}") from exc
    try:
        claims = load_claims(claims_path, source_path) if claims_path is not None else load_claims(source_path=source_path)
        sources = load_sources(source_path)
    except (ClaimLedgerError, SourceLedgerError) as exc: raise ProjectValidationError(f"Cannot load research ledgers: {exc}") from exc
    return validate_project(project, claims, {s["url"] for s in sources})
def release_blockers(project: dict[str, Any], claims: list[dict[str, Any]]) -> list[str]:
    """Return explicit blockers; passing structure does not itself authorize publishing."""
    blockers = []
    by_text = {c["claim"]: c for c in claims}
    for text in project.get("claim_ids", []):
        claim = by_text.get(text)
        if claim is None: blockers.append(f"Claim missing from ledger: {text}")
        elif claim.get("status") == "unverified": blockers.append(f"Unverified claim requires resolution or explicit removal: {text}")
        elif not claim.get("source_urls"): blockers.append(f"Claim has no source links: {text}")
    for index, asset in enumerate(project.get("media_assets", [])):
        if asset.get("rights_status") in {"unknown", "restricted"}: blockers.append(f"Media asset {asset.get('asset_id', index)} has uncleared rights.")
    approval = project.get("approval", {})
    for key in APPROVAL_FIELDS[:-1]:
        if approval.get(key) is not True: blockers.append(f"Human approval missing: {key}")
    if not str(approval.get("approved_by", "")).strip(): blockers.append("Human approval missing: approved_by")
    return blockers
