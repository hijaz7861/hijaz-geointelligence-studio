"""Inspect a rendered media file with ffprobe before editorial release review."""
from __future__ import annotations
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any


class RenderValidationError(ValueError):
    """Raised when a render is missing required streams or has invalid metadata."""


def inspect_rendered_video(
    path: str | Path,
    *,
    require_audio: bool = True,
    require_subtitles: bool = False,
    require_mp4: bool = False,
    min_width: int = 1,
    min_height: int = 1,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Validate media streams and, when requested, the actual MP4 container.

    A filename ending in .mp4 is not proof that the bytes use an MP4 container.
    The optional container gate checks ffprobe's format_name tokens as well.
    """
    if not isinstance(require_mp4, bool):
        raise RenderValidationError("require_mp4 must be a boolean.")
    video = Path(path).expanduser().resolve()
    if not video.is_file():
        raise RenderValidationError(f"Rendered video does not exist: {video}")
    if require_mp4 and video.suffix.lower() != ".mp4":
        raise RenderValidationError("Rendered MP4 must use the .mp4 file extension.")
    if min_width < 1 or min_height < 1:
        raise RenderValidationError("Minimum width and height must be positive.")
    if timeout_seconds < 1:
        raise RenderValidationError("timeout_seconds must be positive.")
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
    if not isinstance(data, dict):
        raise RenderValidationError("ffprobe output must be a JSON object.")
    streams = data.get("streams")
    if not isinstance(streams, list):
        raise RenderValidationError("ffprobe output has no streams array.")
    format_info = data.get("format")
    if not isinstance(format_info, dict):
        raise RenderValidationError("ffprobe output has no format object.")
    format_name = format_info.get("format_name")
    if require_mp4:
        if not isinstance(format_name, str) or not format_name.strip():
            raise RenderValidationError("ffprobe output is missing container format metadata.")
        format_tokens = {token.strip().lower() for token in format_name.split(",") if token.strip()}
        if "mp4" not in format_tokens:
            raise RenderValidationError(
                f"Rendered container is not MP4 (ffprobe format_name={format_name!r})."
            )
    videos = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "audio"]
    subtitles = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "subtitle"]
    if not videos:
        raise RenderValidationError("Rendered file has no video stream.")
    if require_audio and not audios:
        raise RenderValidationError("Rendered file has no audio stream.")
    if require_subtitles and not subtitles:
        raise RenderValidationError("Rendered file has no subtitle stream.")
    primary = videos[0]
    width = primary.get("width")
    height = primary.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or not isinstance(height, int) or isinstance(height, bool):
        raise RenderValidationError("Video stream is missing valid width/height metadata.")
    if width < min_width or height < min_height:
        raise RenderValidationError(
            f"Video resolution {width}x{height} is below required {min_width}x{min_height}."
        )
    duration_value = format_info.get("duration")
    try:
        duration = float(duration_value)
    except (TypeError, ValueError):
        duration = 0.0
    if not math.isfinite(duration) or duration <= 0:
        raise RenderValidationError("Rendered file has no valid positive duration.")
    return {
        "validation": "PASS",
        "file": str(video),
        "duration_seconds": round(duration, 3),
        "width": width,
        "height": height,
        "video_codec": primary.get("codec_name"),
        "container_format": format_name,
        "audio_stream_count": len(audios),
        "subtitle_stream_count": len(subtitles),
        "note": "Technical stream validation only; editorial, factual, licensing, and audio-quality review remain required.",
    }
