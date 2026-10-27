import tempfile
import unittest
from pathlib import Path
from app.video.cinematic_map import CinematicMapError, render_animated_svg, validate_scene

def fixture():
    return {
        "scene_id": "test-scene", "title": "Historical route example", "mode": "educational",
        "duration_seconds": 20,
        "map": {"west": -10, "east": 10, "south": -10, "north": 10},
        "entities": [{"id": "aircraft-1", "label": "Aircraft 1"}],
        "routes": [{"entity_id": "aircraft-1", "illustrative": True, "points": [
            {"t": 0, "lon": -5, "lat": 0}, {"t": 10, "lon": 0, "lat": 5}, {"t": 20, "lon": 5, "lat": 0}
        ]}],
        "events": [{"t": 10, "lon": 0, "lat": 5, "label": "Illustrative event", "illustrative": True}]
    }

class CinematicMapTests(unittest.TestCase):
    def test_validates_and_renders_animated_svg(self):
        scene = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            output = render_animated_svg(scene, Path(tmp) / "scene.svg")
            text = output.read_text(encoding="utf-8")
            self.assertIn("<animateMotion", text)
            self.assertIn("SCHEMATIC MAP", text)
            self.assertIn("ILLUSTRATIVE ROUTE", text)
    def test_rejects_out_of_bounds_coordinate(self):
        scene = fixture()
        scene["routes"][0]["points"][1]["lon"] = 50
        with self.assertRaisesRegex(CinematicMapError, "outside map bounds"):
            validate_scene(scene)
    def test_factual_route_requires_sources(self):
        scene = fixture()
        scene["routes"][0]["illustrative"] = False
        with self.assertRaisesRegex(CinematicMapError, "source_refs"):
            validate_scene(scene)
    def test_rejects_unknown_entity(self):
        scene = fixture()
        scene["routes"][0]["entity_id"] = "missing"
        with self.assertRaisesRegex(CinematicMapError, "unknown entity"):
            validate_scene(scene)
    def test_rejects_non_monotonic_time(self):
        scene = fixture()
        scene["routes"][0]["points"][2]["t"] = 5
        with self.assertRaisesRegex(CinematicMapError, "timestamps must be ordered"):
            validate_scene(scene)
    def test_does_not_overwrite_without_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scene.svg"
            output.write_text("keep me", encoding="utf-8")
            with self.assertRaisesRegex(CinematicMapError, "already exists"):
                render_animated_svg(fixture(), output)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")

if __name__ == "__main__":
    unittest.main()
