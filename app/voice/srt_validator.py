"""Validate SubRip (.srt) subtitle structure and cue timing.

This checks file structure and timing only; it cannot assess translation quality.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3})$")
TIMING_RE = re.compile(r"^\s*(\d{2,}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2,}:\d{2}:\d{2},\d{3})(?:\s+.*)?$")

class SubtitleValidationError(ValueError):
    """Raised when subtitle text is malformed."""

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
                raise SubtitleValidationError(f"Cue {index} line {line_number} has {len(line)} characters; limit is {max_chars_per_line}.")
        cues.append(Cue(index, start, end, cue_text))
        previous_start, previous_end = start, end
    return cues

def validate_srt_file(path: str | Path, *, allow_overlaps: bool = False, max_chars_per_line: int = 42) -> list[Cue]:
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise SubtitleValidationError(f"Cannot read UTF-8 subtitle file: {exc}") from exc
    return parse_srt(content, allow_overlaps=allow_overlaps, max_chars_per_line=max_chars_per_line)
