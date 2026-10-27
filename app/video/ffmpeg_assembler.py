"""Safely mux a video, narration track, and optional SRT subtitle track with FFmpeg."""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from app.voice.srt_validator import SubtitleValidationError, validate_srt_file

class VideoAssemblyError(RuntimeError):
    """Raised when inputs or FFmpeg assembly fail validation."""

def assemble_video(video_path: str | Path, audio_path: str | Path, output_path: str | Path,
                   subtitle_path: str | Path | None = None, *, overwrite: bool = False,
                   timeout_seconds: int = 900) -> Path:
    video = Path(video_path).expanduser().resolve()
    audio = Path(audio_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    subtitles = Path(subtitle_path).expanduser().resolve() if subtitle_path is not None else None
    if timeout_seconds < 1:
        raise VideoAssemblyError("timeout_seconds must be positive.")
    if output.suffix.lower() != ".mp4":
        raise VideoAssemblyError("Output file must use the .mp4 extension.")
    if not video.is_file(): raise VideoAssemblyError(f"Video input does not exist: {video}")
    if not audio.is_file(): raise VideoAssemblyError(f"Audio input does not exist: {audio}")
    if subtitles is not None and not subtitles.is_file(): raise VideoAssemblyError(f"Subtitle input does not exist: {subtitles}")
    if subtitles is not None:
        try:
            validate_srt_file(subtitles)
        except SubtitleValidationError as exc:
            raise VideoAssemblyError(f"Subtitle validation failed: {exc}") from exc
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg: raise VideoAssemblyError("FFmpeg executable was not found on PATH.")
    if output in {video, audio, subtitles}:
        raise VideoAssemblyError("Output path must differ from every input path.")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        raise VideoAssemblyError(f"Output already exists (pass overwrite=True to replace): {output}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".mp4", dir=output.parent)
    os.close(fd)
    temp_output = Path(temp_name)
    temp_output.unlink()
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(video), "-i", str(audio)]
    if subtitles is not None:
        command += ["-i", str(subtitles)]
    command += ["-map", "0:v:0", "-map", "1:a:0"]
    if subtitles is not None:
        command += ["-map", "2:s:0", "-c:s", "mov_text"]
    command += ["-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(temp_output)]
    try:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise VideoAssemblyError(f"FFmpeg timed out after {timeout_seconds} seconds.") from exc
        if result.returncode != 0:
            detail = (result.stderr or "No FFmpeg diagnostic was provided.").strip()[-2000:]
            raise VideoAssemblyError(f"FFmpeg failed with exit code {result.returncode}: {detail}")
        if not temp_output.is_file() or temp_output.stat().st_size == 0:
            raise VideoAssemblyError("FFmpeg returned success but did not create a non-empty output file.")
        if output.exists() and not overwrite:
            raise VideoAssemblyError(f"Output appeared during render; refusing to overwrite: {output}")
        temp_output.replace(output)
        return output
    finally:
        if temp_output.exists():
            temp_output.unlink()
