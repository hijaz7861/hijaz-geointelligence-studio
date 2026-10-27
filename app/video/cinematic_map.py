"""Generate a deterministic animated SVG map from a reviewed scene plan."""
from __future__ import annotations
import json
import math
import os
import tempfile
import xml.sax.saxutils as xml
from pathlib import Path

class CinematicMapError(ValueError):
    """Invalid scene plan or unsafe output operation."""

def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CinematicMapError(f"{label} must be a finite number.")
    return float(value)

def validate_scene(scene):
    if not isinstance(scene, dict):
        raise CinematicMapError("Scene must be a JSON object.")
    for key in ("scene_id", "title", "mode", "duration_seconds", "map", "entities", "routes", "events"):
        if key not in scene:
            raise CinematicMapError(f"Missing required field: {key}")
    if scene["mode"] not in ("historical", "educational", "fictional"):
        raise CinematicMapError("mode must be historical, educational, or fictional.")
    duration = scene["duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 600:
        raise CinematicMapError("duration_seconds must be an integer from 1 to 600.")
    bounds = scene["map"]
    if not isinstance(bounds, dict):
        raise CinematicMapError("map must be an object.")
    west, east = _number(bounds.get("west"), "map.west"), _number(bounds.get("east"), "map.east")
    south, north = _number(bounds.get("south"), "map.south"), _number(bounds.get("north"), "map.north")
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise CinematicMapError("Map bounds are invalid.")
    entities = scene["entities"]
    if not isinstance(entities, list) or not entities:
        raise CinematicMapError("entities must be a non-empty list.")
    ids = set()
    for entity in entities:
        if not isinstance(entity, dict) or not isinstance(entity.get("id"), str) or not entity["id"].strip() or not isinstance(entity.get("label"), str) or not entity["label"].strip():
            raise CinematicMapError("Each entity needs non-empty string id and label.")
        if entity["id"] in ids:
            raise CinematicMapError(f"Duplicate entity id: {entity['id']}")
        ids.add(entity["id"])
    for group in ("routes", "events"):
        if not isinstance(scene[group], list):
            raise CinematicMapError(f"{group} must be a list.")
    for route in scene["routes"]:
        if not isinstance(route, dict):
            raise CinematicMapError("Each route must be an object.")
        entity_id = route.get("entity_id")
        if not isinstance(entity_id, str) or entity_id not in ids:
            raise CinematicMapError("Route references an unknown entity.")
        points = route.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise CinematicMapError("Each route needs at least two points.")
        last_t = -1
        for point in points:
            if not isinstance(point, dict):
                raise CinematicMapError("Each route point must be an object.")
            t = _number(point.get("t"), "route point t")
            lon, lat = _number(point.get("lon"), "route point lon"), _number(point.get("lat"), "route point lat")
            if not 0 <= t <= duration or t < last_t:
                raise CinematicMapError("Route timestamps must be ordered within scene duration.")
            if not west <= lon <= east or not south <= lat <= north:
                raise CinematicMapError("Route point lies outside map bounds.")
            last_t = t
        if not route.get("illustrative", False) and not route.get("source_refs"):
            raise CinematicMapError("Factual routes require source_refs; mark reconstructions illustrative.")
    for event in scene["events"]:
        if not isinstance(event, dict):
            raise CinematicMapError("Each event must be an object.")
        t = _number(event.get("t"), "event t")
        if not 0 <= t <= duration or not event.get("label"):
            raise CinematicMapError("Event timestamp or label is invalid.")
        if ("lon" in event) != ("lat" in event):
            raise CinematicMapError("Events must provide both lon and lat, or neither.")
        if "lon" in event and "lat" in event:
            lon, lat = _number(event["lon"], "event lon"), _number(event["lat"], "event lat")
            if not west <= lon <= east or not south <= lat <= north:
                raise CinematicMapError("Event lies outside map bounds.")
        if not event.get("illustrative", False) and not event.get("source_refs"):
            raise CinematicMapError("Factual events require source_refs; mark reconstructions illustrative.")
    return scene

def _xy(lon, lat, bounds, width=1280, height=720, margin=70):
    x = margin + (lon - bounds["west"]) / (bounds["east"] - bounds["west"]) * (width - 2 * margin)
    y = height - margin - (lat - bounds["south"]) / (bounds["north"] - bounds["south"]) * (height - 2 * margin)
    return round(x, 2), round(y, 2)

def render_animated_svg(scene, output_path, *, overwrite=False):
    validate_scene(scene)
    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() != ".svg":
        raise CinematicMapError("Output must have .svg extension.")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        raise CinematicMapError(f"Output already exists: {output}")
    bounds, duration = scene["map"], scene["duration_seconds"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img">',
        '<rect width="1280" height="720" fill="#071525"/>',
        '<g stroke="#18364b" stroke-width="1" opacity=".8">'
    ]
    for x in range(70, 1211, 80):
        parts.append(f'<line x1="{x}" y1="70" x2="{x}" y2="650"/>')
    for y in range(70, 651, 80):
        parts.append(f'<line x1="70" y1="{y}" x2="1210" y2="{y}"/>')
    parts.append('</g>')
    parts.append('<text x="70" y="42" fill="#f0f6fc" font-size="27" font-family="sans-serif" font-weight="700">' + xml.escape(str(scene["title"])) + '</text>')
    parts.append('<text x="70" y="680" fill="#9fb3c8" font-size="16" font-family="sans-serif">SCHEMATIC MAP • NOT TO SCALE</text>')
    for route in scene["routes"]:
        coords = [_xy(p["lon"], p["lat"], bounds) for p in route["points"]]
        path = " ".join(("M" if i == 0 else "L") + f" {x} {y}" for i, (x, y) in enumerate(coords))
        parts.append(f'<path d="{path}" fill="none" stroke="#46d9ff" stroke-width="4" stroke-linecap="round" stroke-dasharray="9 7"/>')
        start_t = route["points"][0]["t"]
        end_t = route["points"][-1]["t"]
        travel = max(0.5, end_t - start_t)
        entity_label = next(e["label"] for e in scene["entities"] if e["id"] == route["entity_id"])
        entity_label = xml.escape(str(entity_label))
        parts.append(f'<g><circle r="8" fill="#ffcc66" stroke="#fff" stroke-width="2"/><text x="13" y="-12" fill="#fff" font-size="18">{entity_label}</text><animateMotion dur="{travel}s" begin="{start_t}s" repeatCount="1" fill="freeze" path="{path}"/></g>')
        x, y = coords[-1]
        parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#ff6b6b"/>')
        if route.get("illustrative", False):
            x, y = coords[0]
            parts.append(f'<text x="{x}" y="{y+28}" fill="#ffcc66" font-size="13">ILLUSTRATIVE ROUTE</text>')
    for event in scene["events"]:
        if "lon" in event and "lat" in event:
            x, y = _xy(event["lon"], event["lat"], bounds)
            label = xml.escape(str(event["label"]))
            parts.append(f'<g><circle cx="{x}" cy="{y}" r="15" fill="none" stroke="#ff6b6b" stroke-width="3"><animate attributeName="r" values="9;24;9" dur="2s" begin="{event["t"]}s" repeatCount="indefinite"/></circle><text x="{x+20}" y="{y-16}" fill="#ffd5d5" font-size="17">{label}</text></g>')
            if event.get("illustrative", False):
                parts.append(f'<text x="{x+20}" y="{y+8}" fill="#ffcc66" font-size="12">ILLUSTRATIVE</text>')
    parts.append(f'<text x="1210" y="680" text-anchor="end" fill="#9fb3c8" font-size="15">{duration}s scene</text></svg>')
    data = "\n".join(parts)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.stem}.", suffix=".svg", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
        if output.exists() and not overwrite:
            raise CinematicMapError(f"Output appeared during render; refusing to overwrite: {output}")
        os.replace(temp_name, output)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return output

def load_scene(path):
    try:
        scene = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CinematicMapError(f"Could not read scene JSON: {exc}") from exc
    return validate_scene(scene)
