import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.video.cinematic_map import CinematicMapError
from app.video.cinematic_mp4 import (
    CinematicMP4Error, _frame_svg, _position_at, render_cinematic_mp4,
)


def fixture():
    return {
        "scene_id": "mp4-test", "title": "Frame renderer test", "mode": "educational",
        "duration_seconds": 2,
        "map": {"west": -10, "east": 10, "south": -10, "north": 10},
        "entities": [{"id": "unit-a", "label": "Illustrative marker"}],
        "routes": [{
            "entity_id": "unit-a", "illustrative": True,
            "points": [
                {"t": 0, "lon": -5, "lat": 0},
                {"t": 1, "lon": 0, "lat": 5},
                {"t": 2, "lon": 5, "lat": 0},
            ],
        }],
        "events": [{"t": 1, "lon": 0, "lat": 5, "label": "Test event", "illustrative": True}],
    }


class CinematicMP4Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / "scene.mp4"

    def tearDown(self):
        self.temp.cleanup()

    def test_interpolates_route_position_at_segment_midpoint(self):
        self.assertEqual(_position_at(fixture()["routes"][0], 0.5), (-2.5, 2.5))

    def test_clamps_marker_before_and_after_route(self):
        route = fixture()["routes"][0]
        self.assertEqual(_position_at(route, -1), (-5, 0))
        self.assertEqual(_position_at(route, 3), (5, 0))

    def test_frame_svg_replaces_smil_with_explicit_transform(self):
        from app.video.cinematic_map import render_animated_svg
        svg_path = self.root / "template.svg"
        render_animated_svg(fixture(), svg_path)
        frame = _frame_svg(svg_path.read_text(encoding="utf-8"), fixture(), 1)
        self.assertNotIn("<animateMotion", frame)
        self.assertIn('transform="translate(640.0 215.0)"', frame)
        self.assertIn("Illustrative marker", frame)


    def test_rejects_basemap_metadata_without_geojson(self):
        with self.assertRaisesRegex(CinematicMP4Error, "requires a local GeoJSON overlay"):
            render_cinematic_mp4(
                fixture(), self.output, basemap_attribution="Synthetic attribution"
            )

    def test_geojson_overlay_requires_complete_metadata_before_media_tools(self):
        geojson_path = self.root / "land.geojson"
        geojson_path.write_text(json.dumps({
            "type": "Polygon",
            "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
        }), encoding="utf-8")
        with self.assertRaisesRegex(CinematicMP4Error, "Basemap attribution is required"):
            render_cinematic_mp4(fixture(), self.output, geojson_path=geojson_path)

    def test_renders_geojson_overlay_into_every_mp4_frame(self):
        geojson_path = self.root / "land.geojson"
        geojson_path.write_text(json.dumps({
            "type": "Polygon",
            "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
        }), encoding="utf-8")
        rendered_frames = []

        def fake_svg2png(**kwargs):
            rendered_frames.append(kwargs["bytestring"].decode("utf-8"))
            Path(kwargs["write_to"]).write_bytes(b"png")

        def fake_ffmpeg(command, **kwargs):
            Path(command[-1]).write_bytes(b"synthetic mp4")
            return Mock(returncode=0, stderr="")

        with patch.dict(sys.modules, {"cairosvg": types.SimpleNamespace(svg2png=fake_svg2png)}):
            with patch("app.video.cinematic_mp4.shutil.which", return_value="/usr/bin/ffmpeg"):
                with patch("app.video.cinematic_mp4.subprocess.run", side_effect=fake_ffmpeg):
                    result = render_cinematic_mp4(
                        fixture(), self.output, fps=1, geojson_path=geojson_path,
                        basemap_attribution="Test & Attribution",
                        basemap_license="CC0-1.0",
                        basemap_source_url="https://example.org/synthetic-map",
                    )

        self.assertEqual(result, self.output.resolve())
        self.assertEqual(len(rendered_frames), fixture()["duration_seconds"])
        for frame in rendered_frames:
            self.assertIn('id="licensed-geojson-overlay"', frame)
            self.assertIn("GEOGRAPHIC BOUNDARIES", frame)
            self.assertIn("Test &amp; Attribution", frame)
            self.assertIn("CC0-1.0", frame)
            self.assertIn("https://example.org/synthetic-map", frame)

    def test_rejects_invalid_fps(self):
        with self.assertRaisesRegex(CinematicMP4Error, "fps must"):
            render_cinematic_mp4(fixture(), self.output, fps=0)

    def test_rejects_scene_over_sixty_seconds(self):
        scene = fixture()
        scene["duration_seconds"] = 61
        with self.assertRaisesRegex(CinematicMP4Error, "60 seconds"):
            render_cinematic_mp4(scene, self.output)

    def test_rejects_wrong_extension(self):
        with self.assertRaisesRegex(CinematicMP4Error, "mp4 extension"):
            render_cinematic_mp4(fixture(), self.root / "scene.mov")

    def test_refuses_overwrite_by_default(self):
        self.output.write_bytes(b"keep")
        with self.assertRaisesRegex(CinematicMP4Error, "already exists"):
            render_cinematic_mp4(fixture(), self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")

    @patch("app.video.cinematic_mp4.shutil.which", return_value=None)
    def test_requires_ffmpeg(self, _which):
        with self.assertRaisesRegex(CinematicMP4Error, "not found"):
            render_cinematic_mp4(fixture(), self.output)

    @patch.dict(sys.modules, {"cairosvg": types.SimpleNamespace(svg2png=lambda **kw: Path(kw["write_to"]).write_bytes(b"png"))})
    @patch("app.video.cinematic_mp4.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("app.video.cinematic_mp4.subprocess.run")
    def test_renders_frames_and_encodes_mp4(self, run, _which):
        def fake_ffmpeg(command, **kwargs):
            Path(command[-1]).write_bytes(b"synthetic mp4")
            return Mock(returncode=0, stderr="")
        run.side_effect = fake_ffmpeg
        result = render_cinematic_mp4(fixture(), self.output, fps=2)
        self.assertEqual(result, self.output.resolve())
        self.assertEqual(result.read_bytes(), b"synthetic mp4")
        command = run.call_args.args[0]
        self.assertIn("-framerate", command)
        self.assertIn("2", command)
        self.assertIn("-frames:v", command)
        self.assertEqual(command[command.index("-frames:v") + 1], "4")

    @patch.dict(sys.modules, {"cairosvg": types.SimpleNamespace(svg2png=lambda **kw: Path(kw["write_to"]).write_bytes(b"png"))})
    @patch("app.video.cinematic_mp4.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("app.video.cinematic_mp4.subprocess.run")
    def test_ffmpeg_failure_does_not_leave_output(self, run, _which):
        run.return_value = Mock(returncode=1, stderr="fixture failure")
        with self.assertRaisesRegex(CinematicMP4Error, "fixture failure"):
            render_cinematic_mp4(fixture(), self.output, fps=1)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".cinematic-mp4-*")), [])

    @patch.dict(sys.modules, {"cairosvg": types.SimpleNamespace(svg2png=lambda **kw: Path(kw["write_to"]).write_bytes(b"png"))})
    @patch("app.video.cinematic_mp4.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("app.video.cinematic_mp4.subprocess.run")
    def test_successful_render_does_not_overwrite_existing_output(self, run, _which):
        self.output.write_bytes(b"original")
        run.return_value = Mock(returncode=0, stderr="")
        with self.assertRaisesRegex(CinematicMP4Error, "already exists"):
            render_cinematic_mp4(fixture(), self.output, fps=1)
        self.assertEqual(self.output.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
