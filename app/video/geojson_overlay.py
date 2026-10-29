"""Validate and render a user-supplied, license-documented GeoJSON overlay."""
from __future__ import annotations
import json
import math
import xml.sax.saxutils as xml
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES = 20 * 1024 * 1024
MAX_FEATURES = 1000
MAX_COORDINATES = 100_000

class GeoJSONOverlayError(ValueError):
    """Invalid or unsafe local GeoJSON overlay metadata/data."""

def _position(value, count):
    if not isinstance(value, list) or len(value) < 2:
        raise GeoJSONOverlayError("Each GeoJSON position must contain longitude and latitude.")
    lon, lat = value[0], value[1]
    if (isinstance(lon, bool) or not isinstance(lon, (int, float)) or not math.isfinite(lon)
            or isinstance(lat, bool) or not isinstance(lat, (int, float)) or not math.isfinite(lat)):
        raise GeoJSONOverlayError("GeoJSON longitude/latitude must be finite numbers.")
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise GeoJSONOverlayError("GeoJSON coordinate is outside geographic bounds.")
    count[0] += 1
    if count[0] > MAX_COORDINATES:
        raise GeoJSONOverlayError(f"GeoJSON exceeds the {MAX_COORDINATES} coordinate limit.")
    return float(lon), float(lat)

def _ring(value, count):
    if not isinstance(value, list) or len(value) < 4:
        raise GeoJSONOverlayError("GeoJSON polygon rings must contain at least four positions.")
    positions = [_position(item, count) for item in value]
    if positions[0] != positions[-1]:
        raise GeoJSONOverlayError("GeoJSON polygon rings must be closed.")
    return positions

def _polygon(value, count):
    if not isinstance(value, list) or not value:
        raise GeoJSONOverlayError("GeoJSON Polygon coordinates must contain rings.")
    return [_ring(ring, count) for ring in value]

def _geometry(value, count):
    if not isinstance(value, dict):
        raise GeoJSONOverlayError("GeoJSON geometry must be an object.")
    kind = value.get("type")
    coordinates = value.get("coordinates")
    if kind == "Polygon":
        return [_polygon(coordinates, count)]
    if kind == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise GeoJSONOverlayError("GeoJSON MultiPolygon coordinates must be non-empty.")
        return [_polygon(poly, count) for poly in coordinates]
    raise GeoJSONOverlayError("Only GeoJSON Polygon and MultiPolygon geometries are supported.")

def load_geojson_polygons(path):
    """Read bounded local GeoJSON; no remote URLs or implicit downloads are used."""
    source = Path(path).expanduser()
    try:
        if source.stat().st_size > MAX_BYTES:
            raise GeoJSONOverlayError(f"GeoJSON file exceeds the {MAX_BYTES}-byte limit.")
        raw = json.loads(source.read_text(encoding="utf-8"))
    except GeoJSONOverlayError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GeoJSONOverlayError(f"Could not read GeoJSON overlay: {exc}") from exc
    if not isinstance(raw, dict):
        raise GeoJSONOverlayError("GeoJSON root must be an object.")
    if raw.get("type") == "FeatureCollection":
        features = raw.get("features")
        if not isinstance(features, list) or not features or len(features) > MAX_FEATURES:
            raise GeoJSONOverlayError(f"FeatureCollection must contain 1 to {MAX_FEATURES} features.")
    elif raw.get("type") == "Feature":
        features = [raw]
    elif raw.get("type") in ("Polygon", "MultiPolygon"):
        features = [{"type": "Feature", "geometry": raw}]
    else:
        raise GeoJSONOverlayError("GeoJSON root must be FeatureCollection, Feature, Polygon, or MultiPolygon.")
    count = [0]
    polygons = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise GeoJSONOverlayError("Each GeoJSON feature must be a Feature object.")
        polygons.extend(_geometry(feature.get("geometry"), count))
    return polygons

def render_geojson_overlay(path, bounds, *, attribution, license_name, source_url, project):
    """Return SVG for local polygon data and a visible, escaped attribution footer."""
    for label, value in (("attribution", attribution), ("license", license_name), ("source URL", source_url)):
        if not isinstance(value, str) or not value.strip():
            raise GeoJSONOverlayError(f"Basemap {label} is required when GeoJSON is enabled.")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise GeoJSONOverlayError("Basemap source URL must be an HTTPS URL without embedded credentials.")
    if not isinstance(bounds, dict):
        raise GeoJSONOverlayError("Map bounds must be an object.")
    try:
        west, east, south, north = (bounds[key] for key in ("west", "east", "south", "north"))
    except (KeyError, TypeError) as exc:
        raise GeoJSONOverlayError("Map bounds must define west, east, south, and north.") from exc
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in (west, east, south, north)):
        raise GeoJSONOverlayError("Map bounds must be finite numbers.")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise GeoJSONOverlayError("Map bounds must be ordered and within geographic limits.")
    polygons = load_geojson_polygons(path)
    paths = []
    for polygon in polygons:
        ring_paths = []
        for ring in polygon:
            coords = [project(lon, lat, bounds) for lon, lat in ring]
            commands = " ".join(("M" if i == 0 else "L") + f" {x} {y}" for i, (x, y) in enumerate(coords)) + " Z"
            ring_paths.append(commands)
        # Clip at the scene viewport; valid global polygons may cross the selected bounds.
        paths.append('<path d="' + xml.escape(" ".join(ring_paths)) + '" fill="#173d45" stroke="#5b9b91" stroke-width="1.5" fill-rule="evenodd"/>')
    if not paths:
        raise GeoJSONOverlayError("GeoJSON overlay contains no polygon geometry.")
    footer = xml.escape(f"Basemap: {attribution} | {license_name} | {source_url}")
    return ('<defs><clipPath id="geojson-map-viewport"><rect x="70" y="70" width="1140" height="580"/></clipPath></defs>'
            + '<g id="licensed-geojson-overlay" clip-path="url(#geojson-map-viewport)">'
            + "".join(paths) + '</g>'
            + f'<text x="70" y="704" fill="#c1d7d3" font-size="10" font-family="sans-serif">{footer}</text>')
