import tempfile
import unittest
from pathlib import Path

from app.voice.srt_validator import (
    SubtitleValidationError,
    analyze_readability,
    parse_srt,
    validate_srt_file,
)

VALID = """1
00:00:01,000 --> 00:00:02,000
Hello world.

2
00:00:02,100 --> 00:00:03,000
Second subtitle.
"""


class SrtValidatorTests(unittest.TestCase):
    def test_parses_valid_srt(self):
        cues = parse_srt(VALID)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start_ms, 1000)
        self.assertEqual(cues[1].end_ms, 3000)

    def test_accepts_utf8_bom_and_windows_newlines(self):
        self.assertEqual(len(parse_srt("\ufeff" + VALID.replace("\n", "\r\n"))), 2)

    def test_rejects_empty_file(self):
        with self.assertRaisesRegex(SubtitleValidationError, "empty"):
            parse_srt(" \n")

    def test_rejects_out_of_sequence_index(self):
        with self.assertRaisesRegex(SubtitleValidationError, "out of sequence"):
            parse_srt(VALID.replace("2\n00:00:02,100", "3\n00:00:02,100"))

    def test_rejects_invalid_timestamp_ranges(self):
        with self.assertRaisesRegex(SubtitleValidationError, "out of range"):
            parse_srt(VALID.replace("00:00:01,000", "00:61:01,000"))

    def test_rejects_end_before_start(self):
        with self.assertRaisesRegex(SubtitleValidationError, "after start"):
            parse_srt(VALID.replace("00:00:02,000", "00:00:00,500", 1))

    def test_rejects_overlapping_cues_by_default(self):
        with self.assertRaisesRegex(SubtitleValidationError, "overlaps"):
            parse_srt(VALID.replace("00:00:02,100", "00:00:01,900"))

    def test_can_explicitly_allow_overlaps(self):
        self.assertEqual(
            len(parse_srt(VALID.replace("00:00:02,100", "00:00:01,900"), allow_overlaps=True)),
            2,
        )

    def test_rejects_long_lines(self):
        with self.assertRaisesRegex(SubtitleValidationError, "characters"):
            parse_srt(VALID, max_chars_per_line=5)

    def test_rejects_invalid_line_length_limit(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(SubtitleValidationError, "positive integer"):
                    parse_srt(VALID, max_chars_per_line=value)

    def test_reads_utf8_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captions.srt"
            path.write_text(VALID, encoding="utf-8")
            self.assertEqual(len(validate_srt_file(path)), 2)

    def test_readability_reports_peak_and_mean_cps(self):
        report = analyze_readability(parse_srt(VALID))
        self.assertEqual(report["cue_count"], 2)
        self.assertEqual(report["peak_cue"], 2)
        self.assertAlmostEqual(report["peak_cps"], 16 / 0.9, places=1)
        self.assertIsNone(report["within_limit"])

    def test_readability_threshold_passes(self):
        report = analyze_readability(parse_srt(VALID), max_chars_per_second=20)
        self.assertTrue(report["within_limit"])
        self.assertEqual(report["over_limit_cues"], [])

    def test_readability_threshold_identifies_dense_cue(self):
        report = analyze_readability(parse_srt(VALID), max_chars_per_second=17)
        self.assertFalse(report["within_limit"])
        self.assertEqual(report["over_limit_cues"], [2])

    def test_readability_ignores_nonspacing_marks_and_format_controls(self):
        cues = parse_srt("1\n00:00:00,000 --> 00:00:01,000\nمَیں\u200c ہوں\n")
        report = analyze_readability(cues)
        self.assertEqual(report["peak_cps"], 7.0)

    def test_readability_rejects_invalid_limits(self):
        for value in (0, -1, float("nan"), float("inf"), True, "17"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(SubtitleValidationError, "finite positive"):
                    analyze_readability(parse_srt(VALID), max_chars_per_second=value)

    def test_readability_rejects_empty_cue_list(self):
        with self.assertRaisesRegex(SubtitleValidationError, "without subtitle cues"):
            analyze_readability([])


if __name__ == "__main__":
    unittest.main()
