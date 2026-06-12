"""
Population lookup module (D-11, D-12, DATA-04).

Provides:
    load_population() -> dict[str, int]
        Loads INE 2024 communal population from the committed static asset.
        Keyed by CUT code (string). lru_cached — reads file once per process.

    LOW_POPULATION_THRESHOLD = 10_000  (D-12)

    is_low_population(cut_code: str) -> bool
        Returns True if the commune's 2024 population is below the threshold,
        or if the CUT code is not found (safe default: exclude unknowns from rankings).

Source file: data/ine/poblacion_comunal.json (346 entries, committed static asset).
"""

import json
import pathlib
from functools import lru_cache

DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "data"

LOW_POPULATION_THRESHOLD = 10_000  # D-12


@lru_cache(maxsize=1)
def load_population() -> dict[str, int]:
    """
    Load INE communal population projections from /data/ine/poblacion_comunal.json.
    Returns {cut_code: population_2024}.
    File is a static committed asset — no scraping (D-11).
    """
    path = DATA_DIR / "ine" / "poblacion_comunal.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(entry["cut"]): int(entry["population_2024"]) for entry in data}


def is_low_population(cut_code: str) -> bool:
    """
    Return True if the commune has fewer than LOW_POPULATION_THRESHOLD (10,000)
    inhabitants in 2024, or if the CUT code is unknown.

    Unknown CUT codes default to population 0 — this excludes them from rankings,
    which is safer than accidentally including a commune with no data (D-12).
    """
    pop = load_population()
    return pop.get(cut_code, 0) < LOW_POPULATION_THRESHOLD
