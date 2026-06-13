"""
pipeline/news/centroids.py

Deterministic CUT → (lat, lng) lookup from precomputed centroids.json (D-08).
LLM never emits coordinates — pin lat/lng come ONLY from this module.
"""
from __future__ import annotations

import json
import logging
import pathlib

logger = logging.getLogger(__name__)

# Module-level cache — exposed for monkeypatching in tests
_CENTROIDS: dict[str, dict] | None = None
_CENTROID_PATH: pathlib.Path = (
    pathlib.Path(__file__).parents[2] / "data" / "incidents" / "centroids.json"
)


def get_centroid(cut: str) -> tuple[float, float] | None:
    """Return (lat, lng) for the given CUT code, or None if unknown.

    Lazy-loads centroids.json on first call.  Thread-safe for single-threaded
    pipeline use; no lock needed.
    """
    global _CENTROIDS
    if _CENTROIDS is None:
        path = _CENTROID_PATH
        if path.exists():
            try:
                _CENTROIDS = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error("Failed to load centroids from %s: %s", path, exc)
                _CENTROIDS = {}
        else:
            logger.warning("centroids.json not found at %s", path)
            _CENTROIDS = {}
    entry = _CENTROIDS.get(cut)
    if entry is None:
        return None
    return (entry["lat"], entry["lng"])
