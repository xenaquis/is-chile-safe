"""
pipeline/cead/normalizer.py

Normalization utilities for CEAD data:
  - compute_trend:   3-year trend (up/down/stable) per D-13
  - make_slug:       URL slug from commune name per D-17
  - compute_ranks:   national + regional rank by rate descending (low-pop → None) per D-12
  - compute_level:   1-5 quintile for map-payload per prototype data.js 'level' field
  - attach_featured: featured_rates dict for homicides/kidnappings/property per D-06
"""
from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Featured categories (D-06)
# ---------------------------------------------------------------------------

FEATURED_FAMILIES: set[str] = {"propiedad", "vida"}

# Subgroup IDs for featured crime types.
# homicidios: subgroup 101 (per CEAD taxonomy — assumed via 01-03 open question;
#             must be confirmed live in Plan 04 checkpoint).
# secuestros: None — subgroup ID not yet confirmed (Open Question 3, deferred from Plan 03).
FEATURED_SUBGROUPS: dict[str, int | None] = {
    "homicidios": 101,
    "secuestros": None,  # pending live confirmation
}


# ---------------------------------------------------------------------------
# compute_trend (D-13)
# ---------------------------------------------------------------------------

def compute_trend(series: list[dict], threshold_pct: float = 5.0) -> str:
    """
    Compute 3-year trend as 'up'/'down'/'stable' (D-13).

    Args:
        series: list of dicts with at least {'year': int, 'rate_per_100k': float}.
                Need not be sorted — function sorts internally.
        threshold_pct: ±5% is the default; adjust after validating against sample
                       communes (A5). Named param so it is tunable.

    Returns:
        'up'   if rate increased by more than threshold_pct% over the last 3 years
        'down' if rate decreased by more than threshold_pct% over the last 3 years
        'stable' otherwise (including insufficient data or zero starting rate)
    """
    if len(series) < 4:
        return "stable"

    recent = sorted(series, key=lambda x: x["year"])[-4:]  # last 4 years → 3-year delta
    rate_start = recent[0]["rate_per_100k"]
    rate_end = recent[-1]["rate_per_100k"]

    if rate_start == 0:
        return "stable"

    pct_change = (rate_end - rate_start) / rate_start * 100

    if pct_change > threshold_pct:
        return "up"
    elif pct_change < -threshold_pct:
        return "down"
    return "stable"


# ---------------------------------------------------------------------------
# make_slug (D-17)
# ---------------------------------------------------------------------------

def make_slug(name: str) -> str:
    """
    Convert a commune name to a URL-safe ASCII slug.

    Examples:
        'Ñuñoa'    → 'nunoa'
        "O'Higgins" → 'ohiggins'
        'Aysén'    → 'aysen'
        'Los Ángeles' → 'los-angeles'
    """
    # NFD decomposition separates base character from combining marks
    normalized = unicodedata.normalize("NFD", name)
    # Strip combining marks (category 'Mn' = Mark, Nonspacing)
    ascii_only = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Remove apostrophes/quotes entirely (so O'Higgins → ohiggins, not o-higgins)
    ascii_only = re.sub(r"[''`']", "", ascii_only)
    # Lowercase, replace non-alphanumeric runs with '-', strip edge hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug


# ---------------------------------------------------------------------------
# compute_ranks (D-12)
# ---------------------------------------------------------------------------

def _latest_rate(record: dict, year: int) -> float:
    """Return the rate_per_100k for the given year, or 0 if not found."""
    for yr in record.get("series", []):
        if yr["year"] == year:
            return yr["rate_per_100k"]
    # Fall back to the most recent year available
    sorted_series = sorted(record.get("series", []), key=lambda x: x["year"], reverse=True)
    if sorted_series:
        return sorted_series[0]["rate_per_100k"]
    return 0.0


def compute_ranks(records: list[dict], year: int) -> list[dict]:
    """
    Assign national_rank and regional_rank to every commune.

    Rules (D-12):
    - Eligible communes: low_population=False AND series is non-empty
    - Rank by rate_per_100k descending (highest rate = rank 1)
    - Ineligible communes get national_rank=None, regional_rank=None

    Args:
        records: list of commune dicts, each with:
                 id, region_id, low_population, national_rank, regional_rank, series
        year:    reference year for rate lookup

    Returns:
        The same list with national_rank and regional_rank set in-place.
    """
    # Build index map for mutation
    eligible_indices = [
        i for i, r in enumerate(records)
        if not r.get("low_population", True) and r.get("series")
    ]

    # --- National rank ---
    eligible_sorted = sorted(
        eligible_indices,
        key=lambda i: _latest_rate(records[i], year),
        reverse=True,
    )
    for rank, i in enumerate(eligible_sorted, start=1):
        records[i]["national_rank"] = rank

    # --- Regional rank (scoped per region_id) ---
    regions: dict[str, list[int]] = {}
    for i in eligible_indices:
        rid = records[i]["region_id"]
        regions.setdefault(rid, []).append(i)

    for rid, indices in regions.items():
        region_sorted = sorted(
            indices,
            key=lambda i: _latest_rate(records[i], year),
            reverse=True,
        )
        for rank, i in enumerate(region_sorted, start=1):
            records[i]["regional_rank"] = rank

    # Ensure ineligible communes have None ranks
    ineligible_indices = set(range(len(records))) - set(eligible_indices)
    for i in ineligible_indices:
        records[i]["national_rank"] = None
        records[i]["regional_rank"] = None

    return records


# ---------------------------------------------------------------------------
# compute_level (quintile, for map-payload)
# ---------------------------------------------------------------------------

def compute_level(rate: float, all_rates: list[float]) -> int:
    """
    Map a rate to its 1-5 quintile within all_rates.

    1 = lowest quintile (least crime), 5 = highest quintile (most crime).
    Matches the prototype data.js 'level' field.

    Args:
        rate:      the rate to classify
        all_rates: list of all commune rates for the same year (used to compute quintile boundaries)

    Returns:
        integer 1..5
    """
    if not all_rates:
        return 1

    sorted_rates = sorted(all_rates)
    n = len(sorted_rates)

    # Find percentile of 'rate' within sorted_rates
    # Count how many rates are strictly less than 'rate'
    below = sum(1 for r in sorted_rates if r < rate)
    percentile = below / n  # 0.0 to 1.0

    # Map percentile to quintile 1-5
    if percentile >= 0.8:
        return 5
    elif percentile >= 0.6:
        return 4
    elif percentile >= 0.4:
        return 3
    elif percentile >= 0.2:
        return 2
    else:
        return 1


# ---------------------------------------------------------------------------
# attach_featured (D-06)
# ---------------------------------------------------------------------------

def attach_featured(commune_data: dict) -> dict:
    """
    Build the featured_rates dict for a commune (D-06).

    Expects commune_data to contain optional per-year rate dicts:
        propiedad_by_year:  {year: rate_per_100k}
        vida_by_year:       {year: rate_per_100k}
        homicidios_by_year: {year: rate_per_100k}   (subgroup 101 if available)
        secuestros_by_year: {year: rate_per_100k}   (subgroup None — pending)

    Returns:
        dict with keys: 'propiedad', 'homicidios', 'secuestros'
        Each value is a dict {year: rate} or {} if no data available.
        Never fabricates data — only includes rates actually scraped from CEAD.
    """
    featured: dict[str, dict] = {
        "propiedad": dict(commune_data.get("propiedad_by_year", {})),
        "homicidios": dict(commune_data.get("homicidios_by_year", {})),
        "secuestros": dict(commune_data.get("secuestros_by_year", {})),
    }
    return featured
