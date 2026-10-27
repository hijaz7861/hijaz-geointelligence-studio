"""Create a source-attributed, non-publishing YouTube metadata draft."""
from __future__ import annotations
from typing import Any
from app.editorial.script_validator import ProjectValidationError, release_blockers, validate_project
from app.research.corroboration import assess_corroboration

class MetadataBuildError(ValueError):
    """Raised when metadata cannot be safely prepared from the project package."""

def build_metadata_package(project: dict[str, Any], claims: list[dict[str, Any]], source_urls: set[str], sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    try:
        validate_project(project, claims, source_urls)
    except ProjectValidationError as exc:
        raise MetadataBuildError(str(exc)) from exc
    blockers = release_blockers(project, claims)
    corroboration_warnings = assess_corroboration([item for item in claims if item.get("claim") in project["claim_ids"]], sources or [])
    claim_by_text = {item["claim"]: item for item in claims}
    used_sources = []
    for claim_text in project["claim_ids"]:
        for url in claim_by_text[claim_text]["source_urls"]:
            if url not in used_sources:
                used_sources.append(url)
    description_lines = [
        project["title"], "",
        "Educational documentary draft. This metadata package was generated from the project's research ledger and has not been published.",
        "", "Key statements covered:",
    ]
    for claim_text in project["claim_ids"]:
        claim = claim_by_text[claim_text]
        description_lines.append(f"- {claim_text} (evidence label: {claim['status']})")
    description_lines.extend(["", "Sources and further reading:"])
    if used_sources:
        description_lines.extend(f"- {url}" for url in used_sources)
    else:
        description_lines.append("- No source URLs are recorded for this project; this draft must not be published.")
    if corroboration_warnings:
        description_lines.extend(["", "Corroboration review notes:"])
        for warning in corroboration_warnings:
            description_lines.append(f"- {warning['claim']}: {warning['message']}")
    description_lines.extend(["", "Editorial note: verify every statement, resolve uncertainty, confirm media rights, and obtain human approval before publication."])
    return {
        "title": project["title"],
        "description": "\n".join(description_lines),
        "language": project["language"],
        "target_duration_seconds": project["target_duration_seconds"],
        "source_urls": used_sources,
        "release_status": "draft_blocked" if blockers else "draft_review_required",
        "publish_ready": False,
        "release_blockers": blockers,
        "corroboration_warnings": corroboration_warnings,
        "note": "This tool creates metadata only; it never uploads or publishes content.",
    }
