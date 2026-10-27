"""Validate translation traceability without claiming to judge translation quality."""
from __future__ import annotations
import re
from typing import Any
CLAIM_MARKER_RE = re.compile(r"\[\[claim:(.*?)\]\]")
URL_RE = re.compile(r"https?://[^\s)\]>]+", re.IGNORECASE)
class TranslationValidationError(ValueError):
    """Raised when a translated script loses traceability markers or source URLs."""
def validate_translation(source_script: str, translated_script: str, *, language: str) -> dict[str, Any]:
    if not isinstance(source_script, str) or not source_script.strip():
        raise TranslationValidationError("Source script must be non-empty.")
    if not isinstance(translated_script, str) or not translated_script.strip():
        raise TranslationValidationError("Translated script must be non-empty.")
    if language not in {"ur", "en", "ru", "zh"}:
        raise TranslationValidationError("language must be one of: en, ur, ru, zh.")
    source_markers = CLAIM_MARKER_RE.findall(source_script)
    translated_markers = CLAIM_MARKER_RE.findall(translated_script)
    if source_markers != translated_markers:
        missing = [marker for marker in source_markers if marker not in translated_markers]
        added = [marker for marker in translated_markers if marker not in source_markers]
        if missing or added:
            raise TranslationValidationError(f"Claim markers changed or were lost; missing={missing!r}, added={added!r}.")
        raise TranslationValidationError("Claim marker order changed in translation.")
    source_urls = URL_RE.findall(source_script)
    translated_urls = URL_RE.findall(translated_script)
    if source_urls != translated_urls:
        raise TranslationValidationError("Source URLs must be preserved exactly and in order in the translation.")
    return {"validation": "PASS", "language": language, "claim_marker_count": len(source_markers), "source_url_count": len(source_urls), "note": "Structural traceability only; human review is still required for meaning, terminology, and accuracy."}
