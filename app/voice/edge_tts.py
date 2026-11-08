"""Optional online neural narration through the edge-tts command-line client.

Text is sent to Microsoft's Edge online TTS service. Use only for content approved
for external processing; this is not an offline or guaranteed-availability provider.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class EdgeNarrationError(RuntimeError):
    """Raised when optional online neural narration cannot safely complete."""


VOICE_IDS = {
    "ur-PK-AsadNeural", "ur-PK-UzmaNeural",
    "ur-IN-GulNeural", "ur-IN-SalmanNeural",
    "en-US-AriaNeural", "en-US-GuyNeural",
    "ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural",
    "zh-CN-XiaoxiaoNeural", "zh-CN-YunyangNeural",
}
MAX_TEXT_BYTES = 3500
_RATE_RE = re.compile(r"^[+-](?:[0-9]|[1-9][0-9]|100)%$")


def generate_edge_narration(
    text: str,
    voice: str,
    output_path: str | Path,
    *,
    rate: str = "+0%",
    overwrite: bool = False,
    timeout_seconds: int = 180,
) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise EdgeNarrationError("Narration text must be non-empty.")
    if voice not in VOICE_IDS:
        raise EdgeNarrationError("Unsupported voice ID; choose a documented Urdu, English, Russian, or Chinese voice.")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise EdgeNarrationError(f"Text exceeds the {MAX_TEXT_BYTES}-byte per-request safety limit; split narration by scene.")
    if not isinstance(rate, str) or not _RATE_RE.fullmatch(rate):
        raise EdgeNarrationError("rate must be a signed percentage from +0% to +100% or -0% to -100%.")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 900:
        raise EdgeNarrationError("timeout_seconds must be an integer from 1 to 900.")
    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() != ".mp3":
        raise EdgeNarrationError("Output file must use the .mp3 extension.")
    if output.exists() and not overwrite:
        raise EdgeNarrationError(f"Output already exists: {output}")
    executable = shutil.which("edge-tts")
    if not executable:
        raise EdgeNarrationError("edge-tts CLI not found; install requirements-edge-tts.txt.")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".mp3", dir=output.parent)
    os.close(fd)
    temp_output = Path(temp_name)
    temp_output.unlink()
    command = [
        executable, "--voice", voice, "--rate", rate,
        "--text", text.strip(), "--write-media", str(temp_output), "--no-progress",
    ]
    try:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise EdgeNarrationError(f"Online narration timed out after {timeout_seconds} seconds.") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "No edge-tts diagnostic was provided.").strip()[-1500:]
            raise EdgeNarrationError(f"edge-tts failed with exit code {result.returncode}: {detail}")
        if not temp_output.is_file() or temp_output.stat().st_size < 128:
            raise EdgeNarrationError("edge-tts returned success but did not create a valid-looking MP3.")
        with temp_output.open("rb") as stream:
            header = stream.read(4)
        if not (header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)):
            raise EdgeNarrationError("edge-tts output does not have an MP3 ID3/frame signature.")
        if output.exists() and not overwrite:
            raise EdgeNarrationError(f"Output appeared during synthesis; refusing to overwrite: {output}")
        temp_output.replace(output)
        return output
    finally:
        if temp_output.exists():
            temp_output.unlink()
