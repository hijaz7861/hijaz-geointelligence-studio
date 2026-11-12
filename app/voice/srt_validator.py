"""Validate SubRip (.srt) structure, cue timing, and optional reading speed.

Reading-speed metrics are editorial heuristics. They do not establish speech alignment,
translation quality, accessibility compliance, or narration quality.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
import unicodedata
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3})$")
TIMING_RE = re.compile(r"^\s*(\d{2,}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2,}:\d{2}:\d{2},\d{3})(?:\s+.*)?$")


class SubtitleValidationError(ValueError):
    """Raised when subtitle text or timing is malformed."""


@dataclass(frozen=True)
class Cue:
    number: int
    start_ms: int
    end_ms: int
    text: str


def timestamp_to_ms(value: str) -> int:
    match = TIMESTAMP_RE.fullmatch(value)
    if not match:
        raise SubtitleValidationError(f"Invalid timestamp: {value!r}")
    hours, minutes, seconds, millis = map(int, match.groups())
    if minutes > 59 or seconds > 59:
        raise SubtitleValidationError(f"Timestamp minutes/seconds out of range: {value!r}")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def parse_srt(text: str, *, allow_overlaps: bool = False, max_chars_per_line: int = 42) -> list[Cue]:
    if not isinstance(text, str) or not text.strip():
        raise SubtitleValidationError("Subtitle file is empty.")
    if isinstance(max_chars_per_line, bool) or not isinstance(max_chars_per_line, int) or max_chars_per_line < 1:
        raise SubtitleValidationError("max_chars_per_line must be a positive integer.")
    if not isinstance(allow_overlaps, bool):
        raise SubtitleValidationError("allow_overlaps must be a boolean.")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks = re.split(r"\n\s*\n", normalized.strip())
    cues: list[Cue] = []
    previous_start = -1
    previous_end = -1
    for expected, block in enumerate(blocks, 1):
        lines = block.split("\n")
        if len(lines) < 3:
            raise SubtitleValidationError(f"Cue {expected} must contain an index, timing line, and subtitle text.")
        try:
            index = int(lines[0].strip())
        except ValueError as exc:
            raise SubtitleValidationError(f"Cue {expected} has a non-integer index.") from exc
        if index != expected:
            raise SubtitleValidationError(f"Cue index {index} is out of sequence; expected {expected}.")
        timing = TIMING_RE.fullmatch(lines[1])
        if not timing:
            raise SubtitleValidationError(f"Cue {index} has an invalid timing line.")
        start = timestamp_to_ms(timing.group(1))
        end = timestamp_to_ms(timing.group(2))
        if end <= start:
            raise SubtitleValidationError(f"Cue {index} end time must be after start time.")
        if start < previous_start:
            raise SubtitleValidationError(f"Cue {index} starts before the preceding cue; cues must be ordered.")
        if not allow_overlaps and cues and start < previous_end:
            raise SubtitleValidationError(f"Cue {index} overlaps the preceding cue.")
        cue_text = "\n".join(lines[2:]).strip()
        if not cue_text:
            raise SubtitleValidationError(f"Cue {index} has empty subtitle text.")
        for line_number, line in enumerate(cue_text.splitlines(), 1):
            if len(line) > max_chars_per_line:
                raise SubtitleValidationError(
                    f"Cue {index} line {line_number} has {len(line)} characters; limit is {max_chars_per_line}."
                )
        cues.append(Cue(index, start, end, cue_text))
        previous_start, previous_end = start, end
    return cues


def _readability_character_count(text: str) -> int:
    """Approximate visible characters while excluding nonspacing/format controls."""
    normalized = text.replace("\n", " ")
    return sum(
        1
        for character in normalized
        if unicodedata.category(character) not in {"Mn", "Cf"}
    )


def analyze_readability(
    cues: list[Cue],
    *,
    max_chars_per_second: float | None = None,
) -> dict:
    """Return per-cue CPS metrics and optionally flag cues above a supplied limit.

    The count includes spaces and punctuation, excludes nonspacing marks and Unicode
    format controls, and is an approximation rather than a font-aware glyph count.
    """
    if not cues:
        raise SubtitleValidationError("Cannot analyze readability without subtitle cues.")
    limit = None
    if max_chars_per_second is not None:
        if isinstance(max_chars_per_second, bool) or not isinstance(max_chars_per_second, (int, float)):
            raise SubtitleValidationError("max_chars_per_second must be a finite positive number.")
        try:
            limit = float(max_chars_per_second)
        except (OverflowError, ValueError) as exc:
            raise SubtitleValidationError("max_chars_per_second must be a finite positive number.") from exc
        if not math.isfinite(limit) or limit <= 0:
            raise SubtitleValidationError("max_chars_per_second must be a finite positive number.")

    metrics = []
    for cue in cues:
        duration_ms = cue.end_ms - cue.start_ms
        if duration_ms <= 0:
            raise SubtitleValidationError(f"Cue {cue.number} has no positive duration.")
        characters = _readability_character_count(cue.text)
        cps = characters / (duration_ms / 1000)
        metrics.append({
            "cue": cue.number,
            "visible_characters": characters,
            "duration_ms": duration_ms,
            "characters_per_second": round(cps, 2),
            "_raw_cps": cps,
        })

    peak = max(metrics, key=lambda item: item["_raw_cps"])
    over_limit = [
        item["cue"]
        for item in metrics
        if limit is not None and item["_raw_cps"] > limit
    ]
    return {
        "method": "Approximate Unicode visible-character count; spaces and punctuation count, nonspacing marks and format controls are excluded.",
        "cue_count": len(metrics),
        "mean_cue_cps": round(
            sum(item["_raw_cps"] for item in metrics) / len(metrics), 2
        ),
        "peak_cps": peak["characters_per_second"],
        "peak_cue": peak["cue"],
        "max_cps_limit": limit,
        "within_limit": None if limit is None else not over_limit,
        "over_limit_cues": over_limit,
    }


def validate_srt_file(
    path: str | Path,
    *,
    allow_overlaps: bool = False,
    max_chars_per_line: int = 42,
) -> list[Cue]:
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise SubtitleValidationError(f"Cannot read UTF-8 subtitle file: {exc}") from exc
    return parse_srt(content, allow_overlaps=allow_overlaps, max_chars_per_line=max_chars_per_line)
