import json
import tempfile
import unittest
from pathlib import Path

from app.video.geojson_overlay import GeoJSONOverlayError, render_geojson_overlay

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/geo/natural-earth-110m-countries.geojson"

class TestBundledNaturalEarthDataset(unittest.TestCase):
    def test_dataset_is_valid_bounded_geojson_with_polygon_features(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(payload.get("type"), "FeatureCollection")
        self.assertGreater(len(payload.get("features", [])), 100)
        types = {f.get("geometry", {}).get("type") for f in payload["features"]}
        self.assertTrue(types <= {"Polygon", "MultiPolygon"})
        self.assertTrue(types)
        for feature in payload["features"]:
            self.assertTrue(feature.get("properties"))
            self.assertIn(feature["geometry"]["type"], {"Polygon", "MultiPolygon"})

    def test_bundled_dataset_renders_with_explicit_provenance(self):
        # Use the same geographic bounds as the sample scene and assert real polygon output.
        bounds = {"min_lon": -180, "max_lon": 180, "min_lat": -85, "max_lat": 85}
        def project(lon, lat):
            return (20 + (lon + 180) / 360 * 960, 20 + (85 - lat) / 170 * 540)
        svg = render_geojson_overlay(
            DATA, bounds,
            attribution="Natural Earth (public-domain dataset; 1:110m Admin 0 Countries)",
            license_name="Public domain (Natural Earth; verify current terms)",
            source_url="https://github.com/martynafford/natural-earth-geojson/blob/0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e/110m/cultural/ne_110m_admin_0_countries.json",
            project=project,
        )
        self.assertIn("Natural Earth", svg)
        self.assertIn("<path", svg)
        self.assertIn("0b9a6ceb0a7032713abd9460ac1e995a9c60cd1e", svg)

if __name__ == "__main__":
    unittest.main()
