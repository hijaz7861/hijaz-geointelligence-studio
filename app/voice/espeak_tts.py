"""Optional offline narration generation with eSpeak; never silently substitutes voices."""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

class NarrationError(RuntimeError):
    """Raised when a requested offline voice is unavailable or generation fails."""

LANGUAGE_VOICES = {"en": ("en", "en-us", "en-gb"), "ur": ("ur",), "ru": ("ru",), "zh": ("zh", "cmn")}

def available_voices(executable: str | None = None, timeout_seconds: int = 15) -> set[str]:
    binary = executable or shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise NarrationError("Neither espeak-ng nor espeak was found on PATH.")
    try:
        result = subprocess.run([binary, "--voices"], capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NarrationError(f"Could not list installed eSpeak voices: {exc}") from exc
    if result.returncode != 0:
        raise NarrationError(f"Could not list installed eSpeak voices: {(result.stderr or '').strip()[-1000:]}")
    voices = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0].isdigit():
            voices.add(fields[1])
    return voices

def generate_narration(text: str, language: str, output_path: str | Path, *, overwrite: bool = False, timeout_seconds: int = 120) -> Path:
    if not isinstance(text, str) or not text.strip():
        raise NarrationError("Narration text must be non-empty.")
    if language not in LANGUAGE_VOICES:
        raise NarrationError("language must be one of: en, ur, ru, zh.")
    if timeout_seconds < 1:
        raise NarrationError("timeout_seconds must be positive.")
    # Validate deterministic caller input before checking optional host tools.
    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() != ".wav":
        raise NarrationError("Output file must use the .wav extension.")
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise NarrationError("Neither espeak-ng nor espeak was found on PATH.")
    voices = available_voices(binary, min(timeout_seconds, 15))
    voice_candidates = LANGUAGE_VOICES[language]
    voice = next((candidate for candidate in voice_candidates if candidate in voices), None)
    if voice is None:
        raise NarrationError(f"Requested language voice '{language}' is not installed. Available voices include: {', '.join(sorted(voices)[:20])}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        raise NarrationError(f"Output already exists (pass overwrite=True to replace): {output}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".wav", dir=output.parent)
    os.close(fd)
    temp_output = Path(temp_name)
    temp_output.unlink()
    try:
        try:
            result = subprocess.run([binary, "-v", voice, "-w", str(temp_output), "--stdin"], input=text.strip(), capture_output=True, text=True, timeout=timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise NarrationError(f"Narration generation timed out after {timeout_seconds} seconds.") from exc
        if result.returncode != 0:
            detail = (result.stderr or "No eSpeak diagnostic was provided.").strip()[-1500:]
            raise NarrationError(f"eSpeak failed with exit code {result.returncode}: {detail}")
        if not temp_output.is_file() or temp_output.stat().st_size < 44:
            raise NarrationError("eSpeak returned success but did not create a valid-looking WAV file.")
        try:
            with wave.open(str(temp_output), "rb") as wav_file:
                if wav_file.getnframes() <= 0 or wav_file.getframerate() <= 0 or wav_file.getnchannels() <= 0:
                    raise NarrationError("eSpeak created a WAV file with invalid audio metadata.")
        except (wave.Error, EOFError, OSError) as exc:
            raise NarrationError(f"eSpeak output is not a valid WAV file: {exc}") from exc
        if output.exists() and not overwrite:
            raise NarrationError(f"Output appeared during generation; refusing to overwrite: {output}")
        temp_output.replace(output)
        return output
    finally:
        if temp_output.exists(): temp_output.unlink()
