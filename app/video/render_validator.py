"""Inspect rendered media streams and optional audio/video timeline coverage."""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

VIDEO_AUDIO_COVERAGE_TOLERANCE_SECONDS = 0.25


class RenderValidationError(ValueError):
    """Raised when a render is missing required streams or has invalid metadata."""


def _finite_seconds(value: Any) -> float | None:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    return candidate if math.isfinite(candidate) else None


def inspect_rendered_video(
    path: str | Path,
    *,
    require_audio: bool = True,
    require_subtitles: bool = False,
    require_video_cover_audio: bool = False,
    min_width: int = 1,
    min_height: int = 1,
    timeout_seconds: int = 30,
    video_audio_tolerance_seconds: float = VIDEO_AUDIO_COVERAGE_TOLERANCE_SECONDS,
) -> dict[str, Any]:
    """Check streams and optionally require video to cover the complete audio interval."""
    video = Path(path).expanduser().resolve()
    if not video.is_file():
        raise RenderValidationError(f"Rendered video does not exist: {video}")
    if min_width < 1 or min_height < 1:
        raise RenderValidationError("Minimum width and height must be positive.")
    if timeout_seconds < 1:
        raise RenderValidationError("timeout_seconds must be positive.")
    if (
        isinstance(video_audio_tolerance_seconds, bool)
        or not isinstance(video_audio_tolerance_seconds, (int, float))
        or not math.isfinite(float(video_audio_tolerance_seconds))
        or video_audio_tolerance_seconds < 0
    ):
        raise RenderValidationError("Video/audio coverage tolerance must be a finite non-negative number.")

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RenderValidationError("ffprobe executable was not found on PATH.")
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderValidationError(f"ffprobe timed out after {timeout_seconds} seconds.") from exc
    if result.returncode != 0:
        raise RenderValidationError(f"ffprobe failed: {(result.stderr or '').strip()[-1500:]}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RenderValidationError("ffprobe returned invalid JSON.") from exc

    streams = data.get("streams")
    if not isinstance(streams, list):
        raise RenderValidationError("ffprobe output has no streams array.")
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    subtitles = [stream for stream in streams if stream.get("codec_type") == "subtitle"]
    if not videos:
        raise RenderValidationError("Rendered file has no video stream.")
    if require_audio and not audios:
        raise RenderValidationError("Rendered file has no audio stream.")
    if require_subtitles and not subtitles:
        raise RenderValidationError("Rendered file has no subtitle stream.")

    primary = videos[0]
    width = primary.get("width")
    height = primary.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        raise RenderValidationError("Video stream is missing valid width/height metadata.")
    if width < min_width or height < min_height:
        raise RenderValidationError(
            f"Video resolution {width}x{height} is below required {min_width}x{min_height}."
        )

    format_duration = _finite_seconds((data.get("format") or {}).get("duration"))
    if format_duration is None or format_duration <= 0:
        raise RenderValidationError("Rendered file has no valid positive duration.")

    video_duration = _finite_seconds(primary.get("duration"))
    video_start = _finite_seconds(primary.get("start_time"))
    audio_duration = _finite_seconds(audios[0].get("duration")) if audios else None
    audio_start = _finite_seconds(audios[0].get("start_time")) if audios else None
    if video_duration is not None and video_duration <= 0:
        video_duration = None
    if audio_duration is not None and audio_duration <= 0:
        audio_duration = None

    coverage_report = None
    if require_video_cover_audio:
        if not audios:
            raise RenderValidationError("Video/audio coverage requires an audio stream.")
        if video_duration is None or video_start is None:
            raise RenderValidationError("Video stream duration/start time is unavailable for audio coverage validation.")
        if audio_duration is None or audio_start is None:
            raise RenderValidationError("Audio stream duration/start time is unavailable for video coverage validation.")

        video_end = video_start + video_duration
        audio_end = audio_start + audio_duration
        tolerance = float(video_audio_tolerance_seconds)
        if video_start > audio_start + tolerance:
            gap = video_start - audio_start
            raise RenderValidationError(
                f"Video stream starts after audio stream start by {gap:.3f} seconds."
            )
        if video_end + tolerance < audio_end:
            overrun = audio_end - video_end
            raise RenderValidationError(
                f"Video stream ends before audio stream end by {overrun:.3f} seconds."
            )
        coverage_report = {
            "validation": "PASS",
            "tolerance_seconds": round(tolerance, 3),
            "video_end_seconds": round(video_end, 3),
            "audio_end_seconds": round(audio_end, 3),
        }

    return {
        "validation": "PASS",
        "file": str(video),
        "duration_seconds": round(format_duration, 3),
        "video_duration_seconds": round(video_duration, 3) if video_duration is not None else None,
        "video_start_time_seconds": round(video_start, 3) if video_start is not None else None,
        "audio_duration_seconds": round(audio_duration, 3) if audio_duration is not None else None,
        "audio_start_time_seconds": round(audio_start, 3) if audio_start is not None else None,
        "video_audio_coverage": coverage_report,
        "width": width,
        "height": height,
        "video_codec": primary.get("codec_name"),
        "audio_stream_count": len(audios),
        "subtitle_stream_count": len(subtitles),
        "note": (
            "Technical stream validation only; optional video/audio coverage checks compare stream time bounds "
            "and do not prove subtitle-to-speech synchronization, editorial accuracy, factual truth, licensing, "
            "or audio quality."
        ),
    }
