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
def inspect_rendered_video(path: str | Path, *, require_audio: bool = True, require_subtitles: bool = False, min_width: int = 1, min_height: int = 1, timeout_seconds: int = 30) -> dict[str, Any]:
    video=Path(path).expanduser().resolve()
    if not video.is_file(): raise RenderValidationError(f"Rendered video does not exist: {video}")
    if min_width < 1 or min_height < 1: raise RenderValidationError("Minimum width and height must be positive.")
    if timeout_seconds < 1: raise RenderValidationError("timeout_seconds must be positive.")
    ffprobe=shutil.which('ffprobe')
    if not ffprobe: raise RenderValidationError("ffprobe executable was not found on PATH.")
    try:
        result=subprocess.run([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,timeout=timeout_seconds,check=False)
    except subprocess.TimeoutExpired as exc: raise RenderValidationError(f"ffprobe timed out after {timeout_seconds} seconds.") from exc
    if result.returncode != 0: raise RenderValidationError(f"ffprobe failed: {(result.stderr or '').strip()[-1500:]}")
    try: data=json.loads(result.stdout)
    except json.JSONDecodeError as exc: raise RenderValidationError("ffprobe returned invalid JSON.") from exc
    streams=data.get('streams')
    if not isinstance(streams,list): raise RenderValidationError("ffprobe output has no streams array.")
    videos=[s for s in streams if s.get('codec_type')=='video']
    audios=[s for s in streams if s.get('codec_type')=='audio']
    subtitles=[s for s in streams if s.get('codec_type')=='subtitle']
    if not videos: raise RenderValidationError("Rendered file has no video stream.")
    if require_audio and not audios: raise RenderValidationError("Rendered file has no audio stream.")
    if require_subtitles and not subtitles: raise RenderValidationError("Rendered file has no subtitle stream.")
    primary=videos[0]; width=primary.get('width'); height=primary.get('height')
    if not isinstance(width,int) or not isinstance(height,int): raise RenderValidationError("Video stream is missing valid width/height metadata.")
    if width < min_width or height < min_height: raise RenderValidationError(f"Video resolution {width}x{height} is below required {min_width}x{min_height}.")
    duration_value=(data.get('format') or {}).get('duration')
    try: duration=float(duration_value)
    except (TypeError,ValueError): duration=0.0
    if not math.isfinite(duration) or duration <= 0: raise RenderValidationError("Rendered file has no valid positive duration.")
    audio_duration = None
    if audios:
        try:
            candidate = float(audios[0].get("duration"))
            if math.isfinite(candidate) and candidate > 0:
                audio_duration = round(candidate, 3)
        except (TypeError, ValueError):
            audio_duration = None
    return {'validation':'PASS','file':str(video),'duration_seconds':round(duration,3),'audio_duration_seconds':audio_duration,'width':width,'height':height,'video_codec':primary.get('codec_name'),'audio_stream_count':len(audios),'subtitle_stream_count':len(subtitles),'note':'Technical stream validation only; audio-duration bounds do not prove speech/caption synchronization; editorial, factual, licensing, and audio-quality review remain required.'}
