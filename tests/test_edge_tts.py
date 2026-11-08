import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.voice.edge_tts import EdgeNarrationError, generate_edge_narration


class EdgeNarrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / "urdu.mp3"

    def tearDown(self):
        self.temp.cleanup()

    def test_rejects_empty_text(self):
        with self.assertRaisesRegex(EdgeNarrationError, "non-empty"):
            generate_edge_narration("", "ur-PK-AsadNeural", self.output)

    def test_rejects_unapproved_voice_id(self):
        with self.assertRaisesRegex(EdgeNarrationError, "Unsupported voice"):
            generate_edge_narration("سلام", "ur-PK-FakeNeural", self.output)

    def test_rejects_text_above_provider_request_limit(self):
        with self.assertRaisesRegex(EdgeNarrationError, "3500-byte"):
            generate_edge_narration("ا" * 1200, "ur-PK-AsadNeural", self.output)

    def test_rejects_invalid_rate(self):
        with self.assertRaisesRegex(EdgeNarrationError, "signed percentage"):
            generate_edge_narration("Hello", "en-US-AriaNeural", self.output, rate="fast")

    def test_rejects_wrong_extension(self):
        with self.assertRaisesRegex(EdgeNarrationError, "mp3 extension"):
            generate_edge_narration("Hello", "en-US-AriaNeural", self.root / "audio.wav")

    def test_refuses_overwrite_by_default(self):
        self.output.write_bytes(b"original")
        with self.assertRaisesRegex(EdgeNarrationError, "already exists"):
            generate_edge_narration("سلام", "ur-PK-AsadNeural", self.output)
        self.assertEqual(self.output.read_bytes(), b"original")

    @patch("app.voice.edge_tts.shutil.which", return_value=None)
    def test_requires_optional_cli(self, _which):
        with self.assertRaisesRegex(EdgeNarrationError, "not found"):
            generate_edge_narration("سلام", "ur-PK-AsadNeural", self.output)

    @patch("app.voice.edge_tts.shutil.which", return_value="/usr/bin/edge-tts")
    @patch("app.voice.edge_tts.subprocess.run")
    def test_generates_mp3_atomically_with_explicit_voice(self, run, _which):
        def fake_run(command, **kwargs):
            Path(command[command.index("--write-media") + 1]).write_bytes(b"ID3" + b"0" * 200)
            return Mock(returncode=0, stderr="")
        run.side_effect = fake_run
        result = generate_edge_narration("السلام علیکم", "ur-PK-AsadNeural", self.output, rate="-5%")
        self.assertEqual(result, self.output.resolve())
        self.assertTrue(self.output.read_bytes().startswith(b"ID3"))
        command = run.call_args.args[0]
        self.assertIn("ur-PK-AsadNeural", command)
        self.assertIn("-5%", command)
        self.assertNotIn("shell", run.call_args.kwargs)

    @patch("app.voice.edge_tts.shutil.which", return_value="/usr/bin/edge-tts")
    @patch("app.voice.edge_tts.subprocess.run")
    def test_timeout_does_not_leave_output(self, run, _which):
        import subprocess
        run.side_effect = subprocess.TimeoutExpired("edge-tts", 1)
        with self.assertRaisesRegex(EdgeNarrationError, "timed out"):
            generate_edge_narration("سلام", "ur-PK-AsadNeural", self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".urdu.*.mp3")), [])

    @patch("app.voice.edge_tts.shutil.which", return_value="/usr/bin/edge-tts")
    @patch("app.voice.edge_tts.subprocess.run")
    def test_rejects_success_without_valid_mp3(self, run, _which):
        def fake_run(command, **kwargs):
            Path(command[command.index("--write-media") + 1]).write_bytes(b"not audio")
            return Mock(returncode=0, stderr="")
        run.side_effect = fake_run
        with self.assertRaisesRegex(EdgeNarrationError, "MP3"):
            generate_edge_narration("سلام", "ur-PK-AsadNeural", self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
