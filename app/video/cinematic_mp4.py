"""Render deterministic, frame-based cinematic map MP4 previews with FFmpeg."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import xml.sax.saxutils as xml
from pathlib import Path

from app.video.cinematic_map import CinematicMapError, _xy, render_animated_svg, validate_scene


class CinematicMP4Error(RuntimeError):
    """Raised when cinematic map MP4 rendering cannot safely complete."""


def _position_at(route, seconds):
    points = route["points"]
    if seconds <= points[0]["t"]:
        return points[0]["lon"], points[0]["lat"]
    if seconds >= points[-1]["t"]:
        return points[-1]["lon"], points[-1]["lat"]
    for left, right in zip(points, points[1:]):
        if left["t"] <= seconds <= right["t"]:
            span = right["t"] - left["t"]
            ratio = 0.0 if span == 0 else (seconds - left["t"]) / span
            return (
                left["lon"] + (right["lon"] - left["lon"]) * ratio,
                left["lat"] + (right["lat"] - left["lat"]) * ratio,
            )
    return points[-1]["lon"], points[-1]["lat"]


def _frame_svg(template, scene, seconds):
    """Replace SVG SMIL motion with explicit per-frame marker transforms."""
    result = template
    bounds = scene["map"]
    pattern = re.compile(
        r'<g><circle r="8" fill="#ffcc66" stroke="#fff" stroke-width="2"/>'
        r'<text x="13" y="-12" fill="#fff" font-size="18">.*?</text>'
        r'<animateMotion\b[^>]*/></g>'
    )
    matches = list(pattern.finditer(template))
    if len(matches) != len(scene["routes"]):
        raise CinematicMP4Error("Could not match every route marker in generated SVG.")
    for match, route in reversed(list(zip(matches, scene["routes"]))):
        lon, lat = _position_at(route, seconds)
        x, y = _xy(lon, lat, bounds)
        label = next(entity["label"] for entity in scene["entities"] if entity["id"] == route["entity_id"])
        marker = (
            f'<g transform="translate({x} {y})">'
            '<circle r="8" fill="#ffcc66" stroke="#fff" stroke-width="2"/>'
            f'<text x="13" y="-12" fill="#fff" font-size="18">{xml.escape(label)}</text></g>'
        )
        result = result[:match.start()] + marker + result[match.end():]
    # Make event pulses visibly vary between frames without relying on SVG SMIL.
    pulse_index = int(seconds * 3) % 3
    pulse_radius = (9, 16, 24)[pulse_index]
    result = re.sub(
        r'(<circle cx="[^"]+" cy="[^"]+" )r="15"( fill="none" stroke="#ff6b6b" stroke-width="3">'
        r'<animate attributeName="r"[^>]*/>',
        lambda m: m.group(1) + f'r="{pulse_radius}"' + m.group(2),
        result,
    )
    return result


def render_cinematic_mp4(scene, output_path, *, fps=5, overwrite=False, timeout_seconds=300):
    """Render a reviewed scene to MP4; defaults are bounded for low-cost preview use."""
    try:
        validate_scene(scene)
    except CinematicMapError as exc:
        raise CinematicMP4Error(f"Invalid scene: {exc}") from exc
    if isinstance(fps, bool) or not isinstance(fps, int) or not 1 <= fps <= 12:
        raise CinematicMP4Error("fps must be an integer from 1 to 12.")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 1800:
        raise CinematicMP4Error("timeout_seconds must be an integer from 1 to 1800.")
    duration = scene["duration_seconds"]
    if duration > 60:
        raise CinematicMP4Error("Cinematic MP4 preview is limited to scenes of 60 seconds or less.")
    frame_count = duration * fps
    if frame_count > 720:
        raise CinematicMP4Error("Frame count exceeds the 720-frame safety limit.")
    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() != ".mp4":
        raise CinematicMP4Error("Output must use the .mp4 extension.")
    if output.exists() and not overwrite:
        raise CinematicMP4Error(f"Output already exists: {output}")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise CinematicMP4Error("FFmpeg executable was not found on PATH.")
    try:
        import cairosvg
    except ImportError as exc:
        raise CinematicMP4Error("CairoSVG is required for frame rasterization; install the project media extras.") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=".cinematic-mp4-", dir=output.parent))
    temp_output = temp_root / "render.mp4"
    try:
        template_path = temp_root / "template.svg"
        render_animated_svg(scene, template_path)
        template = template_path.read_text(encoding="utf-8")
        for index in range(frame_count):
            seconds = index / fps
            svg = _frame_svg(template, scene, seconds)
            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                write_to=str(temp_root / f"frame_{index:06d}.png"),
                output_width=1280,
                output_height=720,
            )
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-framerate", str(fps), "-i", str(temp_root / "frame_%06d.png"),
            "-frames:v", str(frame_count), "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temp_output),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise CinematicMP4Error(f"FFmpeg timed out after {timeout_seconds} seconds.") from exc
        if result.returncode != 0:
            detail = (result.stderr or "No FFmpeg diagnostic was provided.").strip()[-2000:]
            raise CinematicMP4Error(f"FFmpeg failed with exit code {result.returncode}: {detail}")
        if not temp_output.is_file() or temp_output.stat().st_size == 0:
            raise CinematicMP4Error("FFmpeg did not create a non-empty MP4.")
        if output.exists() and not overwrite:
            raise CinematicMP4Error(f"Output appeared during render; refusing to overwrite: {output}")
        os.replace(temp_output, output)
        return output
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
