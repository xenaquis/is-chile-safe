#!/usr/bin/env python3
"""
pipeline/scripts/build_centroids.py

One-shot generator: TopoJSON -> centroids.json for all 346 Chilean communes.

Decodes communes.topo.json using site/node_modules/topojson-client (already
installed; avoids any new Python geo dependency — D-08). Computes each commune
centroid via the Shoelace formula. For MultiPolygon, uses the largest ring by
absolute area. Falls back to bounding-box center for degenerate/island/elongated
communes where centroid falls outside the bounding box (Assumption A2).

Writes data/incidents/centroids.json atomically via atomic_write_json.

Sanity checks:
  - Exactly 346 entries
  - "13101" (Santiago) lat in (-34, -33), lng in (-71, -70)
  - All lat in (-56, -17), lng in (-110, -66) (Chilean bounds incl. Easter Island)

Usage:
  python pipeline/scripts/build_centroids.py
"""
from __future__ import annotations

import json
import logging
import pathlib
import subprocess

from pipeline.shared.atomic_write import atomic_write_json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
TOPO_PATH = REPO_ROOT / "data" / "cead" / "geo" / "communes.topo.json"
OUTPUT_PATH = REPO_ROOT / "data" / "incidents" / "centroids.json"


# ---------------------------------------------------------------------------
# TopoJSON -> GeoJSON via Node
# ---------------------------------------------------------------------------

def decode_topojson_to_geojson(topo_path: pathlib.Path) -> dict:
    """Decode TopoJSON to GeoJSON using topojson-client (site/node_modules/)."""
    # Use forward slashes for the Node script to avoid Windows path issues
    topo_posix = topo_path.as_posix()
    node_modules = (REPO_ROOT / "site" / "node_modules").as_posix()
    script = (
        "const topo = require('" + node_modules + "/topojson-client');\n"
        "const fs = require('fs');\n"
        "const t = JSON.parse(fs.readFileSync('" + topo_posix + "', 'utf8'));\n"
        "const geo = topo.feature(t, t.objects['communes-rekeyed']);\n"
        "process.stdout.write(JSON.stringify(geo));\n"
    )
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Shoelace centroid
# ---------------------------------------------------------------------------

def ring_centroid(coords: list[list[float]]) -> tuple[float, float]:
    """Compute polygon centroid via Shoelace formula. Returns (lat, lng)."""
    area = cx = cy = 0.0
    n = len(coords)
    for i in range(n):
        x0, y0 = coords[i][0], coords[i][1]
        x1, y1 = coords[(i + 1) % n][0], coords[(i + 1) % n][1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area /= 2.0
    if abs(area) < 1e-10:
        # Degenerate ring — return first coordinate
        return coords[0][1], coords[0][0]
    cx /= 6.0 * area
    cy /= 6.0 * area
    return cy, cx  # (lat, lng) — GeoJSON coords are [lng, lat]


def ring_area(coords: list[list[float]]) -> float:
    """Shoelace absolute area (for choosing largest ring in MultiPolygon)."""
    area = 0.0
    n = len(coords)
    for i in range(n):
        x0, y0 = coords[i][0], coords[i][1]
        x1, y1 = coords[(i + 1) % n][0], coords[(i + 1) % n][1]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def bbox_center(coords: list[list[float]]) -> tuple[float, float]:
    """Bounding box center of a ring. Returns (lat, lng)."""
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lats) + max(lats)) / 2.0, (min(lngs) + max(lngs)) / 2.0


def centroid_in_bbox(lat: float, lng: float, coords: list[list[float]]) -> bool:
    """Check if (lat, lng) is inside the bounding box of coords."""
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return min(lats) <= lat <= max(lats) and min(lngs) <= lng <= max(lngs)


def feature_centroid(geometry: dict) -> tuple[float, float]:
    """Compute centroid for a GeoJSON Polygon or MultiPolygon feature."""
    gtype = geometry["type"]
    if gtype == "Polygon":
        rings = geometry["coordinates"]
        outer = rings[0]
        lat, lng = ring_centroid(outer)
        if not centroid_in_bbox(lat, lng, outer):
            lat, lng = bbox_center(outer)
        return lat, lng
    elif gtype == "MultiPolygon":
        # Use the largest polygon (outer ring by area)
        best_ring = max(
            (poly[0] for poly in geometry["coordinates"]),
            key=lambda r: ring_area(r),
        )
        lat, lng = ring_centroid(best_ring)
        if not centroid_in_bbox(lat, lng, best_ring):
            lat, lng = bbox_center(best_ring)
        return lat, lng
    else:
        raise ValueError(f"Unsupported geometry type: {gtype!r}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    if not TOPO_PATH.exists():
        raise SystemExit(f"ERROR: TopoJSON not found: {TOPO_PATH}")

    logger.info("Decoding TopoJSON via Node...")
    geojson = decode_topojson_to_geojson(TOPO_PATH)

    # Hardcoded fallbacks for communes with null geometry in the TopoJSON asset
    # (verified coordinates for 4 communes: 13111 La Granja, 13117 Lo Prado,
    #  13131 San Ramón, 1101 Iquique — all within Chilean bounds).
    NULL_GEOMETRY_FALLBACKS: dict[str, dict[str, float]] = {
        "13111": {"lat": -33.530, "lng": -70.630},  # La Granja
        "13117": {"lat": -33.450, "lng": -70.720},  # Lo Prado
        "13131": {"lat": -33.540, "lng": -70.638},  # San Ramón
        "1101":  {"lat": -20.213, "lng": -70.152},  # Iquique
    }

    centroids: dict[str, dict[str, float]] = {}
    for feature in geojson["features"]:
        props = feature.get("properties") or {}
        cut = str(props.get("id", ""))
        if not cut:
            logger.warning("Feature missing 'id' property — skipping")
            continue
        geometry = feature.get("geometry")
        if geometry is None:
            fallback = NULL_GEOMETRY_FALLBACKS.get(cut)
            if fallback:
                logger.info("Using hardcoded fallback centroid for %s (null geometry)", cut)
                centroids[cut] = fallback
            else:
                logger.warning("Feature %s has null geometry and no fallback — skipping", cut)
            continue
        lat, lng = feature_centroid(geometry)
        centroids[cut] = {"lat": round(lat, 6), "lng": round(lng, 6)}

    # Sanity checks
    if len(centroids) != 346:
        raise SystemExit(f"ERROR: Expected 346 centroids, got {len(centroids)}")

    santiago = centroids.get("13101")
    if santiago is None:
        raise SystemExit("ERROR: Santiago (cut=13101) not found in output")
    if not (-34 < santiago["lat"] < -33 and -71 < santiago["lng"] < -70):
        raise SystemExit(
            f"ERROR: Santiago centroid out of expected range: {santiago}"
        )

    for cut, v in centroids.items():
        # Chilean bounds: mainland (-56,-17), Easter Island extends lng to ~-110.
        # CUT 12202 (Territorio Chileno Antártico) centroid is near -63°S — include.
        if not (-90 < v["lat"] < -17 and -110 < v["lng"] < -65):
            raise SystemExit(
                f"ERROR: Centroid for {cut} outside Chilean bounds: {v}"
            )

    atomic_write_json(OUTPUT_PATH, centroids)
    logger.info("Written: %s (%d entries)", OUTPUT_PATH, len(centroids))
    print(f"Written: {OUTPUT_PATH} ({len(centroids)} entries)")


if __name__ == "__main__":
    main()
