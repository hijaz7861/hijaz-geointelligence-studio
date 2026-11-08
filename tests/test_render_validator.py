import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.video.render_validator import RenderValidationError, inspect_rendered_video


PROBE = {
    "streams": [
        {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "start_time": "0.000000",
            "duration": "12.500000",
        },
        {
            "index": 1,
            "codec_type": "audio",
            "codec_name": "aac",
            "start_time": "0.000000",
            "duration": "12.000000",
        },
        {"index": 2, "codec_type": "subtitle", "codec_name": "mov_text"},
    ],
    "format": {"duration": "12.5"},
}


class RenderValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.file = Path(self.temp.name) / "render.mp4"
        self.file.write_bytes(b"fixture")

    def tearDown(self):
        self.temp.cleanup()

    def _probe(self, data=PROBE):
        return Mock(returncode=0, stdout=json.dumps(data), stderr="")

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_accepts_required_streams(self, run, _which):
        run.return_value = self._probe()
        result = inspect_rendered_video(
            self.file, require_subtitles=True, min_width=1280, min_height=720
        )
        self.assertEqual(result["validation"], "PASS")
        self.assertEqual(result["subtitle_stream_count"], 1)
        self.assertIsNone(result["video_audio_coverage"])

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_missing_audio(self, run, _which):
        data = {"streams": [PROBE["streams"][0]], "format": {"duration": "12"}}
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "no audio stream"):
            inspect_rendered_video(self.file)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_missing_subtitles_when_required(self, run, _which):
        data = {"streams": PROBE["streams"][:2], "format": {"duration": "12"}}
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "no subtitle stream"):
            inspect_rendered_video(self.file, require_subtitles=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_low_resolution(self, run, _which):
        data = {
            **PROBE,
            "streams": [
                dict(PROBE["streams"][0], width=320, height=240),
                *PROBE["streams"][1:],
            ],
        }
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "below required"):
            inspect_rendered_video(self.file, min_width=1280, min_height=720)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_invalid_container_duration(self, run, _which):
        run.return_value = self._probe({**PROBE, "format": {"duration": "NaN"}})
        with self.assertRaisesRegex(RenderValidationError, "positive duration"):
            inspect_rendered_video(self.file)

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(RenderValidationError, "does not exist"):
            inspect_rendered_video(self.file.parent / "missing.mp4")

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_accepts_video_covering_audio_within_tolerance(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        data["streams"][1]["duration"] = "12.650000"
        run.return_value = self._probe(data)
        result = inspect_rendered_video(self.file, require_video_cover_audio=True)
        coverage = result["video_audio_coverage"]
        self.assertEqual(coverage["validation"], "PASS")
        self.assertEqual(coverage["tolerance_seconds"], 0.25)
        self.assertEqual(coverage["audio_stream_count"], 1)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_video_starting_after_audio(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        data["streams"][0]["start_time"] = "0.500000"
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "starts after audio stream start"):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_video_ending_before_audio(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        data["streams"][0]["duration"] = "10.000000"
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "ends before audio stream end"):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_missing_video_timing_metadata(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        data["streams"][0].pop("start_time")
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, "Video stream duration/start time"):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_missing_audio_timing_metadata(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        data["streams"][1].pop("duration")
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(RenderValidationError, r"Audio stream duration/start time.*stream 1"):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_accepts_multiple_audio_streams_when_each_is_covered(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        second_audio = dict(
            PROBE["streams"][1], index=3, start_time="0.500000", duration="11.500000"
        )
        data["streams"].insert(2, second_audio)
        run.return_value = self._probe(data)
        result = inspect_rendered_video(self.file, require_video_cover_audio=True)
        coverage = result["video_audio_coverage"]
        self.assertEqual(coverage["audio_stream_count"], 2)
        self.assertEqual(len(coverage["audio_streams"]), 2)
        self.assertEqual(coverage["audio_streams"][1]["stream_index"], 3)
        self.assertEqual(coverage["audio_streams"][1]["end_time_seconds"], 12.0)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_secondary_audio_stream_ending_after_video(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        second_audio = dict(PROBE["streams"][1], index=3, duration="13.000000")
        data["streams"].insert(2, second_audio)
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(
            RenderValidationError, r"Video stream ends before audio stream end \(stream 2\)"
        ):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_secondary_audio_stream_missing_start_time(self, run, _which):
        data = json.loads(json.dumps(PROBE))
        second_audio = dict(PROBE["streams"][1], index=3, duration="11.500000")
        second_audio.pop("start_time")
        data["streams"].insert(2, second_audio)
        run.return_value = self._probe(data)
        with self.assertRaisesRegex(
            RenderValidationError, r"Audio stream duration/start time.*stream 2"
        ):
            inspect_rendered_video(self.file, require_video_cover_audio=True)

    @patch("app.video.render_validator.shutil.which", return_value="/usr/bin/ffprobe")
    @patch("app.video.render_validator.subprocess.run")
    def test_rejects_negative_or_non_finite_tolerance(self, run, _which):
        run.return_value = self._probe()
        for tolerance in (-0.1, float("nan"), float("inf")):
            with self.subTest(tolerance=tolerance):
                with self.assertRaisesRegex(RenderValidationError, "finite non-negative"):
                    inspect_rendered_video(
                        self.file,
                        require_video_cover_audio=True,
                        video_audio_tolerance_seconds=tolerance,
                    )


if __name__ == "__main__":
    unittest.main()
