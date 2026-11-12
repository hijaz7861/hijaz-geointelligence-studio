# Offline narration

The optional eSpeak adapter creates WAV narration using an installed local voice. It writes to a temporary file first, preserves existing output on failure, uses stdin for text, and enforces a timeout.

## Example

```sh
python scripts/generate_narration.py \
  --text-file artifacts/drafts/narration.txt \
  --language en \
  --output artifacts/drafts/narration.wav
```

Supported language labels are Urdu (`ur`), English (`en`), Russian (`ru`), and Chinese (`zh`), but generation only works if an exact matching voice is installed. The adapter does not silently substitute another language. In the current assistant validation environment, eSpeak voices were found for English, Russian, and Mandarin Chinese; an Urdu voice was not installed, so Urdu generation correctly fails with a clear error.

eSpeak voices are synthetic and may have poor pronunciation, prosody, names, or technical terms. Always review the generated audio. This tool does not translate a script, verify its facts, or grant media rights. A high-quality Urdu voice provider or human narration remains a future integration.

Run `./scripts/validate.sh` to run mocked unit tests and, when eSpeak is installed, an optional real English WAV smoke test.


## Subtitle reading-speed review

The SRT validator reports approximate per-cue characters-per-second (CPS) metrics. Use an explicit threshold when a project has an editorial standard, for example:

```sh
python scripts/validate_srt.py artifacts/drafts/documentary.srt --max-cps 17
```

The threshold is opt-in because acceptable reading speed depends on language, audience, typography, and editorial policy. A failed threshold identifies dense cues for editing; passing it is not proof of subtitle/audio synchronization. The metric counts spaces and punctuation, excludes nonspacing marks and Unicode format controls, and is not a font-aware glyph measurement. It does not assess translation accuracy, pronunciation, or whether each word appears at the moment it is spoken. Review Urdu and other complex-script captions visually and against the actual narration.
