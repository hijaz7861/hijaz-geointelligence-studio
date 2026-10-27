import tempfile
import unittest
from pathlib import Path
from app.voice.srt_validator import SubtitleValidationError, parse_srt, validate_srt_file
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
        self.assertEqual(len(parse_srt(VALID.replace("00:00:02,100", "00:00:01,900"), allow_overlaps=True)), 2)
    def test_rejects_long_lines(self):
        with self.assertRaisesRegex(SubtitleValidationError, "characters"):
            parse_srt(VALID, max_chars_per_line=5)
    def test_reads_utf8_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captions.srt"
            path.write_text(VALID, encoding="utf-8")
            self.assertEqual(len(validate_srt_file(path)), 2)
if __name__ == "__main__":
    unittest.main()
