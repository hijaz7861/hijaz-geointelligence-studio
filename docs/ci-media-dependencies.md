# CI environment notes

The validation suite includes tests for error handling when media executables are
available. A minimal Ubuntu runner without FFmpeg and eSpeak can cause those
tests to fail before reaching the behavior they are intended to assert.

The repository validation workflow therefore installs `ffmpeg` (including
`ffprobe`) and `espeak-ng` before running `scripts/validate.sh`. This also
allows the optional video and offline narration integration checks to run in CI.
