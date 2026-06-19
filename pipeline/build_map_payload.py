#!/usr/bin/env python3
"""
pipeline/build_map_payload.py

Standalone entrypoint that reads enriched commune JSON files (written by
scrape_cead.py and optionally enriched by build_composite_index.py) and
produces:
  - data/cead/map-payload.json  (last complete year, compact < 30 KB)
  - data/cead/map-payload-{year}.json  (one per year, compact)

Run:
  python pipeline/build_map_payload.py
  CEAD_DATA_DIR=/custom/path python pipeline/build_map_payload.py

D-11: This script is called AFTER build_composite_index.py in the GitHub
Actions workflow.  If the index step fails, the workflow proceeds here via
continue-on-error; ci fields will simply be absent from the payload (graceful
degrade — the old behaviour of no composite level is preserved).
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import pathlib
import sys

# ---------------------------------------------------------------------------
# sys.path bootstrap (mirrors scrape_cead.py pattern so `python pipeline/…`
# invocation works without PYTHONPATH set)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# D-10: reference year — composite_index keyed on str(REFERENCE_YEAR)
# ---------------------------------------------------------------------------
from pipeline.composite_config import REFERENCE_YEAR  # noqa: E402

_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "cead"


def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("CEAD_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR


# ---------------------------------------------------------------------------
# Payload builder (moved verbatim from scrape_cead.py lines 102-204)
# Two additions: ci field (A3) and 30 KB size assertion (moved from _write_all_outputs)
# ---------------------------------------------------------------------------

def build_map_payload(
    records: list[dict],
    year: int,
    all_rates: list[float],
) -> dict:
    """
    Build the map-payload dict for the given reference year.

    Each entry: {id, rate, level, by_family, ci?} (D-09, A3).
    ci = composite_index[str(REFERENCE_YEAR)].level (int 1-5); omitted when absent
    (A3 encoding: level not raw score; omit-when-null protects 30 KB budget, Pitfall 4).

    Only includes communes that have a series entry for the requested year.
    Falls back to the most recent year if the exact year is missing.
    """
    from pipeline.cead.normalizer import compute_level
    from pipeline.shared.schema import FAMILY_KEYS

    comunas = []
    for r in records:
        # Find the rate for the reference year
        rate = None
        by_family: dict[str, float | None] = {k: None for k in FAMILY_KEYS}
        for yr_rec in r.get("series", []):
            if yr_rec["year"] == year:
                rate = yr_rec["rate_per_100k"]
                bf = yr_rec.get("by_family", {})
                for k in FAMILY_KEYS:
                    by_family[k] = bf.get(k)
                break

        if rate is None:
            # Fall back to most recent year
            sorted_series = sorted(r.get("series", []), key=lambda x: x["year"], reverse=True)
            if sorted_series:
                rate = sorted_series[0]["rate_per_100k"]
                bf = sorted_series[0].get("by_family", {})
                for k in FAMILY_KEYS:
                    by_family[k] = bf.get(k)

        if rate is None:
            continue  # No data for this commune

        level = compute_level(rate, all_rates)
        # by_family stored as ordered list matching FAMILY_KEYS for compactness (<30KB D-09)
        from pipeline.shared.schema import FAMILY_KEYS as _FK
        # Round to integers (no decimal) to keep map-payload under 30 KB (D-09)
        # Full precision is preserved in the per-commune JSON files.
        by_family_list = [int(round(by_family[k])) if by_family[k] is not None else None for k in _FK]

        # Homicide fields: read from the record's homicide_rate/homicide_count (set by accumulator)
        # or from featured_rates.homicidios for the active year (null-vs-0 invariant preserved)
        h_rate_raw = r.get("homicide_rate")
        h_count_raw = r.get("homicide_count")
        homicide_rate_val = int(round(h_rate_raw)) if h_rate_raw is not None else None
        homicide_count_val = int(h_count_raw) if h_count_raw is not None else None

        # Fallback: look up from featured_rates.homicidios for the active year.
        # Keys may be int (in-memory pipeline dicts) or str (after JSON round-trip).
        if homicide_rate_val is None:
            fr = r.get("featured_rates", {})
            homicidios = fr.get("homicidios", {}) if isinstance(fr, dict) else {}
            # Try both int and str key (int from pipeline accumulator, str after JSON round-trip)
            raw = homicidios.get(year) if homicidios.get(year) is not None else homicidios.get(str(year))
            if raw is not None:
                homicide_rate_val = int(round(raw))
        if homicide_count_val is None:
            fr = r.get("featured_rates", {})
            homicidios_count = fr.get("homicidios_count", {}) if isinstance(fr, dict) else {}
            raw_count = homicidios_count.get(year) if homicidios_count.get(year) is not None else homicidios_count.get(str(year))
            if raw_count is not None:
                homicide_count_val = int(raw_count)

        # Build compact entry — omit None homicide fields to stay under 30KB (Pitfall 3).
        # When homicide data exists the keys are present; when absent they're omitted entirely.
        # homicide_count is also preserved in per-commune JSON via featured_rates.homicidios_count.
        entry: dict = {
            "id": r["id"],
            "rate": int(round(rate)),
            "level": level,
            "by_family": by_family_list,  # ordered per FAMILY_KEYS
        }
        if homicide_rate_val is not None:
            # Use abbreviated key "hr" (vs "homicide_rate") to stay under 30KB — saves ~10B per entry
            # (D-09 compact encoding: same pattern as by_family compact list).
            # Downstream (Half B UI) reads "hr" from map-payload; full name in per-commune JSON.
            entry["hr"] = homicide_rate_val
        # homicide_count intentionally dropped from the payload (Pitfall 3 budget escape):
        # adding it would exceed 30KB with 346 communes. It lives in per-commune JSON
        # via featured_rates.homicidios_count for downstream consumers that need it.

        # A3: composite level (1-5) — read from enriched commune file.
        # Omit entirely when absent (null/missing key) to protect 30 KB budget (Pitfall 4).
        ci_data = r.get("composite_index", {})
        ci_year_data = ci_data.get(str(REFERENCE_YEAR)) if isinstance(ci_data, dict) else None
        if isinstance(ci_year_data, dict):
            ci_level = ci_year_data.get("level")
            if ci_level is not None:
                entry["ci"] = int(ci_level)
        # If composite_index absent or level None: key omitted (Pitfall 4 graceful degrade)

        comunas.append(entry)

    # Determine partial_year: True if any commune's series entry for this year is partial
    partial_year = any(
        yr_rec.get("partial", False)
        for r in records
        for yr_rec in r.get("series", [])
        if yr_rec["year"] == year
    )

    return {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "year": year,
        "partial_year": partial_year,
        "comunas": comunas,
    }


# ---------------------------------------------------------------------------
# Entrypoint: read commune files from disk and write map-payload
# ---------------------------------------------------------------------------

def main() -> None:
    data_dir = _get_data_dir()
    comunas_dir = data_dir / "comunas"

    if not comunas_dir.exists():
        raise FileNotFoundError(f"Commune directory not found: {comunas_dir}")

    commune_files = sorted(comunas_dir.glob("*.json"))
    if not commune_files:
        raise FileNotFoundError(f"No commune JSON files found in {comunas_dir}")

    logger.info("Reading %d commune files from %s", len(commune_files), comunas_dir)
    records = []
    for f in commune_files:
        with open(f, encoding="utf-8") as fh:
            records.append(json.load(fh))

    # Determine last complete year from the data
    last_complete_year: int | None = None
    all_years: set[int] = set()
    for r in records:
        for yr_rec in r.get("series", []):
            if not yr_rec.get("partial", False):
                all_years.add(yr_rec["year"])

    if not all_years:
        raise ValueError("No non-partial years found in commune data")

    last_complete_year = max(all_years)

    # Collect all rates for the last complete year
    all_rates_for_year: list[float] = []
    for r in records:
        for yr_rec in r.get("series", []):
            if yr_rec["year"] == last_complete_year and not yr_rec.get("partial", False):
                all_rates_for_year.append(yr_rec["rate_per_100k"])
                break

    logger.info("Building map-payload.json for year %d (%d commune rates)", last_complete_year, len(all_rates_for_year))
    map_payload = build_map_payload(records, year=last_complete_year, all_rates=all_rates_for_year)

    # Size assertion (T-18-05: moved here from scrape_cead.py).
    # Limit raised from 30720 (30 KB) to 35840 (35 KB) to accommodate the additive
    # ci field (7 bytes × 346 communes = ~2.4 KB) introduced in plan 18-02.
    # All 346 communes were enriched with composite_index in plan 18-01, so
    # the "omit-when-null" path (Pitfall 4) provides no savings here.
    # CF Pages limit is 25 MiB per file — 35 KB is well within bounds.
    from pipeline.shared.atomic_write import atomic_write_json
    serialized = json.dumps(map_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) >= 35840:
        raise ValueError(
            f"map-payload.json exceeds 35 KB limit: {len(serialized)} bytes"
        )
    logger.info("map-payload.json size: %d bytes (< 30720 limit OK)", len(serialized))

    # Write map-payload.json (compact)
    atomic_write_json(data_dir / "map-payload.json", map_payload, compact=True)
    logger.info("Written: %s", data_dir / "map-payload.json")

    # Write per-year payloads (D-09, compact)
    for yr in sorted(all_years):
        yr_rates: list[float] = []
        for r in records:
            for yr_rec in r.get("series", []):
                if yr_rec["year"] == yr and not yr_rec.get("partial", False):
                    yr_rates.append(yr_rec["rate_per_100k"])
                    break
        if yr_rates:
            yr_payload = build_map_payload(records, year=yr, all_rates=yr_rates)
            atomic_write_json(data_dir / f"map-payload-{yr}.json", yr_payload, compact=True)
            logger.info("Written: map-payload-%d.json", yr)

    logger.info("build_map_payload complete.")


if __name__ == "__main__":
    main()
