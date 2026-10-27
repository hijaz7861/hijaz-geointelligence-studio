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
    def test_rejects_non_object_route_cleanly(self):
        scene = fixture()
        scene["routes"][0] = None
        with self.assertRaisesRegex(CinematicMapError, "route must be an object"):
            validate_scene(scene)
    def test_rejects_non_object_route_point_cleanly(self):
        scene = fixture()
        scene["routes"][0]["points"][0] = None
        with self.assertRaisesRegex(CinematicMapError, "route point must be an object"):
            validate_scene(scene)
    def test_rejects_non_object_event_cleanly(self):
        scene = fixture()
        scene["events"][0] = None
        with self.assertRaisesRegex(CinematicMapError, "event must be an object"):
            validate_scene(scene)
    def test_rejects_partial_event_coordinate(self):
        scene = fixture()
        scene["events"][0].pop("lat")
        with self.assertRaisesRegex(CinematicMapError, "both lon and lat"):
            validate_scene(scene)
    def test_does_not_overwrite_without_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scene.svg"
            output.write_text("keep me", encoding="utf-8")
            with self.assertRaisesRegex(CinematicMapError, "already exists"):
                render_animated_svg(fixture(), output)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")


    def test_rejects_non_boolean_illustrative_flag(self):
        scene = fixture()
        scene["routes"][0]["illustrative"] = "false"
        with self.assertRaisesRegex(CinematicMapError, "illustrative must be a boolean"):
            validate_scene(scene)
    def test_factual_route_requires_nonempty_list_of_source_refs(self):
        scene = fixture()
        scene["routes"][0]["illustrative"] = False
        scene["routes"][0]["source_refs"] = "not-a-reference-list"
        with self.assertRaisesRegex(CinematicMapError, "source_refs must be a non-empty list"):
            validate_scene(scene)
    def test_factual_event_requires_source_refs(self):
        scene = fixture()
        scene["events"][0]["illustrative"] = False
        with self.assertRaisesRegex(CinematicMapError, "source_refs must be a non-empty list"):
            validate_scene(scene)
    def test_rejects_non_string_event_label(self):
        scene = fixture()
        scene["events"][0]["label"] = {"unexpected": "object"}
        with self.assertRaisesRegex(CinematicMapError, "Event timestamp or label is invalid"):
            validate_scene(scene)
    def test_rejects_empty_scene_title(self):
        scene = fixture()
        scene["title"] = "  "
        with self.assertRaisesRegex(CinematicMapError, "title must be a non-empty string"):
            validate_scene(scene)

if __name__ == "__main__":
    unittest.main()
