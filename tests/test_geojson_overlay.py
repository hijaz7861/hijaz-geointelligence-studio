import json
import tempfile
import unittest
from pathlib import Path
from app.video.geojson_overlay import GeoJSONOverlayError, load_geojson_polygons, render_geojson_overlay

BOUNDS = {"west": -10, "east": 10, "south": -10, "north": 10}
POLYGON = {"type": "Polygon", "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]]}

def project(lon, lat, bounds):
    return round(640 + lon * 10, 2), round(360 - lat * 10, 2)

class GeoJSONOverlayTests(unittest.TestCase):
    def write_geojson(self, folder, data):
        path = Path(folder) / "land.geojson"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_loads_polygon_and_renders_visible_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": POLYGON}]})
            svg = render_geojson_overlay(path, BOUNDS, attribution="Example data provider", license_name="CC BY 4.0", source_url="https://example.org/data", project=project)
        self.assertIn('id="licensed-geojson-overlay"', svg)
        self.assertIn("Example data provider", svg)
        self.assertIn("CC BY 4.0", svg)
        self.assertIn("https://example.org/data", svg)
        self.assertIn("<path", svg)

    def test_accepts_multipolygon(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, {"type": "MultiPolygon", "coordinates": [POLYGON["coordinates"], POLYGON["coordinates"]]})
            self.assertEqual(len(load_geojson_polygons(path)), 2)

    def test_rejects_open_ring(self):
        bad = {"type": "Polygon", "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5]]]}
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, bad)
            with self.assertRaisesRegex(GeoJSONOverlayError, "must be closed"):
                load_geojson_polygons(path)

    def test_rejects_non_finite_or_out_of_range_coordinates(self):
        bad = {"type": "Polygon", "coordinates": [[[200, 0], [5, -5], [5, 5], [-5, 5], [200, 0]]]}
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, bad)
            with self.assertRaisesRegex(GeoJSONOverlayError, "outside geographic bounds"):
                load_geojson_polygons(path)

    def test_rejects_line_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, {"type": "LineString", "coordinates": [[0, 0], [1, 1]]})
            with self.assertRaisesRegex(GeoJSONOverlayError, "root must be"):
                load_geojson_polygons(path)

    def test_requires_https_source_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, POLYGON)
            with self.assertRaisesRegex(GeoJSONOverlayError, "HTTPS URL"):
                render_geojson_overlay(path, BOUNDS, attribution="Provider", license_name="Open license", source_url="http://example.org/data", project=project)

    def test_escapes_attribution_markup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_geojson(tmp, POLYGON)
            svg = render_geojson_overlay(path, BOUNDS, attribution="Provider <script>", license_name="CC BY", source_url="https://example.org/data?a=1&b=2", project=project)
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)

if __name__ == "__main__":
    unittest.main()
