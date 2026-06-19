#!/usr/bin/env python3
"""
pipeline/build_composite_index.py

Composite crime-exposure index entrypoint.

Steps (D-11 order — runs AFTER scrape_cead.py, BEFORE build_map_payload.py):
  1. Read 4 sources: SPD homicide snapshot, SII exposure snapshot, INE population, all comunas/{CUT}.json
  2. Assert year alignment (CEAD=SPD=SII=2024) before any compute (D-10)
  3. Compute per-commune: SPD homicide rate, SII-capped exposure denominator, 7 metric rates
  4. Normalize each metric across all communes (winsorized min-max, D-01)
  5. Compute composite score per commune (weighted sum with absent-metric redistribution)
  6. Assign national rank and regional_rank (C-03; region via region_id_from_cut)
  7. Assign level 1-5 from score quintile
  8. Enrich each comunas/{CUT}.json additively with composite_index, spd_homicide_rate,
     sii_exposure_index (D-12: existing featured_rates unchanged)
  9. Write data/cead/comparator_table.json (Phase 21 handoff)

Anti-patterns AVOIDED:
  - Does NOT call build_map_payload() (separate step, PATTERNS.md anti-pattern)
  - Does NOT re-derive region_id by slicing CUT (uses region_id_from_cut, Tarapaca-safe)

Exit codes:
  0 = success
  1 = year misalignment or data error

Usage:
  python pipeline/build_composite_index.py
  CEAD_DATA_DIR=/custom/path python pipeline/build_composite_index.py
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import sys
from typing import Any

# Ensure repo root is on sys.path when running as a script (python pipeline/build_composite_index.py)
# This mirrors the pytest.ini pythonpath=.. approach.
_SCRIPT_DIR = pathlib.Path(__file__).parent
_REPO_ROOT_CANDIDATE = _SCRIPT_DIR.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repo-relative data dir (overridable via env for tests — mirrors scrape_cead.py)
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "cead"


def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("CEAD_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR


# ---------------------------------------------------------------------------
# Source loaders
# ---------------------------------------------------------------------------


def _load_spd_homicide(repo_root: pathlib.Path) -> tuple[dict[str, int], int]:
    """Load SPD VHC homicide snapshot. Returns ({cut: homicides}, year).

    SPD year is derived from the records themselves (max year with data).
    Communes absent from the 2024 set = zero-homicide (Pitfall 2: absent != zero in record).
    """
    path = repo_root / "data" / "snapshots" / "spd_homicide.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["records"]

    # Find latest year
    years = {r["year"] for r in records}
    # Use 2024 — D-10 locks REFERENCE_YEAR; 2025 is partial/unconsolidated
    from pipeline.composite_config import REFERENCE_YEAR

    year_to_use = REFERENCE_YEAR
    if year_to_use not in years:
        raise ValueError(
            f"SPD snapshot does not contain year {year_to_use}. "
            f"Available years: {sorted(years)}"
        )

    by_cut = {r["cut"]: r["homicides"] for r in records if r["year"] == year_to_use}
    return by_cut, year_to_use


def _load_sii_exposure(repo_root: pathlib.Path) -> tuple[dict[str, float], int]:
    """Load SII exposure snapshot. Returns ({cut: trabajadores}, year).

    None means absent (Pitfall 1 guard: only include cuts present in 2024 data).
    """
    path = repo_root / "data" / "snapshots" / "sii_exposure.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["records"]

    from pipeline.composite_config import REFERENCE_YEAR

    year_to_use = REFERENCE_YEAR
    by_cut: dict[str, float] = {
        r["cut"]: float(r["trabajadores"])
        for r in records
        if r["year"] == year_to_use
    }
    return by_cut, year_to_use


def _load_ine_population(repo_root: pathlib.Path) -> dict[str, float]:
    """Load INE communal population estimates. Returns {cut: population_2024}."""
    path = repo_root / "data" / "ine" / "poblacion_comunal.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    return {r["cut"]: float(r["population_2024"]) for r in records}


def _load_all_communes(data_dir: pathlib.Path) -> list[dict]:
    """Load all comunas/{CUT}.json files from data_dir."""
    comunas_dir = data_dir / "comunas"
    communes = []
    for path in sorted(comunas_dir.glob("*.json")):
        communes.append(json.loads(path.read_text(encoding="utf-8")))
    return communes


# ---------------------------------------------------------------------------
# Rate extraction helpers
# ---------------------------------------------------------------------------


def _get_family_rate(commune: dict, family_key: str, year: int) -> float | None:
    """Extract CEAD family rate for a given year from commune series.

    Maps METRIC_WEIGHTS keys to CEAD family keys:
      cead_vida_rate      -> by_family['vida']
      cead_robos_rate     -> by_family['robos_violentos']
      cead_propiedad_rate -> by_family['propiedad']
      cead_vif_rate       -> by_family['vif']
      cead_drogas_rate    -> by_family['drogas']
      cead_armas_rate     -> by_family['armas']
    """
    # Find the series entry for REFERENCE_YEAR
    # JSON round-trip: year keys may be str — check both (Pitfall 3)
    for entry in commune.get("series", []):
        entry_year = entry.get("year")
        if entry_year == year or entry_year == str(year):
            by_family = entry.get("by_family", {})
            val = by_family.get(family_key)
            return float(val) if val is not None else None
    return None


# Mapping from METRIC_WEIGHTS keys to CEAD by_family keys (C-01)
_METRIC_TO_FAMILY: dict[str, str] = {
    "cead_vida_rate":      "vida",
    "cead_robos_rate":     "robos_violentos",
    "cead_propiedad_rate": "propiedad",
    "cead_vif_rate":       "vif",
    "cead_drogas_rate":    "drogas",
    "cead_armas_rate":     "armas",
}


# ---------------------------------------------------------------------------
# Level assignment (quintile 1-5 from score)
# ---------------------------------------------------------------------------


def _assign_levels(scores: list[float]) -> list[int]:
    """Assign level 1-5 by quintile of scores. Level 1 = lowest, 5 = highest.

    Uses pd.qcut with 5 equal-frequency bins.
    """
    s = pd.Series(scores)
    # Use rank-based assignment for robustness with tied values
    try:
        labels = pd.qcut(s, q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")
        # If qcut drops duplicates, re-map
        if labels.isna().any():
            # Fallback: percentile-based
            pcts = s.rank(pct=True)
            labels = pd.cut(pcts, bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                           labels=[1, 2, 3, 4, 5], include_lowest=True)
    except ValueError:
        # All same value — assign level 3
        return [3] * len(scores)
    return [int(l) if not pd.isna(l) else 3 for l in labels]


# ---------------------------------------------------------------------------
# Main pipeline function (testable — accepts data_dir param)
# ---------------------------------------------------------------------------


def run_composite_index(data_dir: pathlib.Path | None = None) -> None:
    """Run the composite index pipeline.

    Args:
        data_dir: Override data directory (for tests). If None, uses _get_data_dir().
    """
    from pipeline.composite_config import (
        METRIC_WEIGHTS,
        REFERENCE_YEAR,
        TOTAL_COMMUNES,
    )
    from pipeline.composite_index import (
        assert_year_alignment,
        compute_composite,
        get_exposure_denominator,
        normalize_metric,
    )
    from pipeline.scrape_cead import region_id_from_cut
    from pipeline.shared.atomic_write import atomic_write_json

    if data_dir is None:
        data_dir = _get_data_dir()

    # Snapshot + INE files: test fixture puts them under data_dir (not data_dir/parent)
    # In production: data_dir = data/cead; snapshots at data/snapshots; ine at data/ine
    # In tests: data_dir = tmp_path; snapshots at tmp_path/snapshots; ine at tmp_path/ine
    if (data_dir / "snapshots").exists():
        repo_root_snapshots = data_dir
        ine_root = data_dir
    else:
        # Production layout: data/cead -> data/ is the parent
        repo_root_snapshots = data_dir.parent
        ine_root = data_dir.parent

    logger.info("Loading source data ...")

    # --- Load 4 sources ---
    spd_by_cut, spd_year = _load_spd_homicide_from(repo_root_snapshots)
    sii_by_cut, sii_year = _load_sii_exposure_from(repo_root_snapshots)
    ine_pop = _load_ine_population_from(ine_root)
    communes = _load_all_communes(data_dir)

    n = len(communes)
    logger.info(f"Loaded {n} communes")

    # --- Determine CEAD year ---
    # Use REFERENCE_YEAR for CEAD lookup
    cead_year = REFERENCE_YEAR

    # --- Assert year alignment BEFORE any compute (D-10, T-18-04) ---
    assert_year_alignment(cead_year, spd_year, sii_year)
    logger.info(f"Year alignment OK: CEAD={cead_year}, SPD={spd_year}, SII={sii_year}")

    # --- Build SPD homicide rates per commune ---
    # Communes absent from SPD 2024 set = zero-homicide (Pitfall 2)
    logger.info("Computing SPD homicide rates ...")
    spd_rates: dict[str, float] = {}
    sii_absent_cuts: set[str] = set()  # track SII-absent communes for available_metrics

    for commune in communes:
        cut = commune["id"]
        spd_homicides = spd_by_cut.get(cut)  # None if absent = 0 homicides

        # Get exposure denominator
        denom, _capped = get_exposure_denominator(cut, sii_by_cut, ine_pop)

        # Track SII-absent communes (reduces data quality -> decrement available_metrics)
        if sii_by_cut.get(cut) is None:
            sii_absent_cuts.add(cut)

        if denom > 0 and spd_homicides is not None:
            spd_rates[cut] = float(spd_homicides) / denom * 100000.0
        else:
            # Absent from SPD 2024 -> 0.0 (Pitfall 2)
            spd_rates[cut] = 0.0

    # --- Build raw metric series for each commune ---
    logger.info("Extracting CEAD metric rates ...")
    raw_metrics: dict[str, dict[str, float | None]] = {cut: {} for cut in (c["id"] for c in communes)}

    for commune in communes:
        cut = commune["id"]
        # SPD homicide rate (M1)
        raw_metrics[cut]["spd_homicide_rate"] = spd_rates[cut]

        # CEAD family rates
        for metric_key, family_key in _METRIC_TO_FAMILY.items():
            raw_metrics[cut][metric_key] = _get_family_rate(commune, family_key, REFERENCE_YEAR)

    # --- Normalize each metric across all communes ---
    logger.info("Normalizing metrics ...")
    cuts = [c["id"] for c in communes]

    normalized: dict[str, dict[str, float | None]] = {cut: {} for cut in cuts}

    for metric_key in METRIC_WEIGHTS:
        values = [raw_metrics[cut].get(metric_key) for cut in cuts]
        series = pd.Series(
            [v if v is not None else np.nan for v in values],
            index=cuts,
        )
        norm_series = normalize_metric(series)
        for cut in cuts:
            val = norm_series[cut]
            normalized[cut][metric_key] = None if np.isnan(val) else float(val)

    # --- Compute composite scores ---
    logger.info("Computing composite scores ...")
    scores: dict[str, float] = {}
    available_metrics_map: dict[str, int] = {}

    for cut in cuts:
        score, available = compute_composite(normalized[cut])
        scores[cut] = score
        # Decrement available_metrics for SII-absent communes (D-12 data quality signal)
        if cut in sii_absent_cuts:
            available = max(0, available - 1)
        available_metrics_map[cut] = available

    # --- Assign national ranks (score descending) ---
    sorted_cuts = sorted(cuts, key=lambda c: scores[c], reverse=True)
    national_ranks: dict[str, int] = {cut: rank for rank, cut in enumerate(sorted_cuts, start=1)}

    # --- Assign regional ranks (C-03) using region_id_from_cut (Tarapaca-safe) ---
    by_region: dict[str, list[str]] = {}
    for cut in cuts:
        rid = region_id_from_cut(cut)
        by_region.setdefault(rid, []).append(cut)

    regional_ranks: dict[str, int] = {}
    for rid, region_cuts in by_region.items():
        region_sorted = sorted(region_cuts, key=lambda c: scores[c], reverse=True)
        for rank, cut in enumerate(region_sorted, start=1):
            regional_ranks[cut] = rank

    # --- Assign levels 1-5 ---
    all_scores_list = [scores[cut] for cut in cuts]
    levels_list = _assign_levels(all_scores_list)
    levels_map: dict[str, int] = {cut: lev for cut, lev in zip(cuts, levels_list)}

    # --- Enrich commune files additively (D-12: existing fields unchanged) ---
    logger.info("Enriching commune JSON files ...")
    comparator_table = []

    for commune in communes:
        cut = commune["id"]

        # SII exposure index for display
        sii_val = sii_by_cut.get(cut)  # None if absent
        denom, _capped = get_exposure_denominator(cut, sii_by_cut, ine_pop)

        composite_entry = {
            "score": scores[cut],
            "rank": national_ranks[cut],
            "regional_rank": regional_ranks[cut],
            "level": levels_map[cut],
            "available_metrics": available_metrics_map[cut],
        }

        # Additive enrichment (D-12) — do NOT touch existing fields
        commune.setdefault("composite_index", {})[str(REFERENCE_YEAR)] = composite_entry

        # Add spd_homicide_rate keyed by year (additive)
        commune.setdefault("spd_homicide_rate", {})[str(REFERENCE_YEAR)] = spd_rates[cut]

        # Add sii_exposure_index keyed by year (null for absent communes)
        commune.setdefault("sii_exposure_index", {})[str(REFERENCE_YEAR)] = (
            float(sii_val) if sii_val is not None else None
        )

        # Write enriched commune file
        commune_path = data_dir / "comunas" / f"{cut}.json"
        atomic_write_json(commune_path, commune)

        # Accumulate comparator_table entry (Phase 21 handoff)
        comparator_table.append({
            "id": cut,
            "name": commune["name"],
            "slug": commune.get("slug", ""),
            "region_id": commune.get("region_id", ""),
            "composite_index": {str(REFERENCE_YEAR): composite_entry},
        })

    logger.info(f"Enriched {len(communes)} commune files")

    # --- Write comparator_table.json ---
    comparator_path = data_dir / "comparator_table.json"
    atomic_write_json(comparator_path, comparator_table)
    logger.info(f"Written {comparator_path}")

    logger.info("Composite index pipeline complete.")


# ---------------------------------------------------------------------------
# Alternative loaders that accept a root path (for test isolation)
# ---------------------------------------------------------------------------


def _load_spd_homicide_from(root: pathlib.Path) -> tuple[dict[str, int], int]:
    path = root / "snapshots" / "spd_homicide.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["records"]
    from pipeline.composite_config import REFERENCE_YEAR
    year_to_use = REFERENCE_YEAR
    available_years = {r["year"] for r in records}
    if year_to_use not in available_years:
        raise ValueError(
            f"SPD snapshot missing year {year_to_use}. Available: {sorted(available_years)}"
        )
    by_cut = {r["cut"]: r["homicides"] for r in records if r["year"] == year_to_use}
    return by_cut, year_to_use


def _load_sii_exposure_from(root: pathlib.Path) -> tuple[dict[str, float], int]:
    path = root / "snapshots" / "sii_exposure.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data["records"]
    from pipeline.composite_config import REFERENCE_YEAR
    year_to_use = REFERENCE_YEAR
    by_cut = {
        r["cut"]: float(r["trabajadores"])
        for r in records
        if r["year"] == year_to_use
    }
    return by_cut, year_to_use


def _load_ine_population_from(root: pathlib.Path) -> dict[str, float]:
    path = root / "ine" / "poblacion_comunal.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    return {r["cut"]: float(r["population_2024"]) for r in records}


# ---------------------------------------------------------------------------
# __main__ entry point (runs against real data dir)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_composite_index()
    except Exception as exc:
        logger.error(f"Composite index pipeline failed: {exc}", exc_info=True)
        sys.exit(1)
