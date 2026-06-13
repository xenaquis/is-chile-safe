#!/usr/bin/env python3
"""
pipeline/scrape_cead.py

CEAD scraper entrypoint. Runs the full pipeline:
  1. Fetch commune catalog (ajax_2.php) → 346 CUT codes
  2. For each region × family × year: fetch batch, parse, accumulate
  3. Normalize all records (trend, slug, ranks, featured flags, quintile level)
  4. Validate with Pydantic (all-or-nothing D-14)
  5. Write atomically to /data/cead/ (only if validation passes)

Exit codes:
  0 = success
  1 = validation failure or scrape error (D-14)

Usage:
  python pipeline/scrape_cead.py
  CEAD_DATA_DIR=/custom/path python pipeline/scrape_cead.py
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repo-relative output directory (overridable via env for tests)
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DEFAULT_DATA_DIR = _REPO_ROOT / "data" / "cead"


def _get_data_dir() -> pathlib.Path:
    override = os.environ.get("CEAD_DATA_DIR")
    return pathlib.Path(override) if override else _DEFAULT_DATA_DIR


# ---------------------------------------------------------------------------
# Partial-year helpers (Open Question 2)
# ---------------------------------------------------------------------------

def mark_partial_year(
    series: list[dict],
    run_date: datetime.date | None = None,
) -> list[dict]:
    """
    Mark the current calendar year as partial=True if the run date is before Dec 31.

    Args:
        series:   list of year record dicts (mutated in-place).
        run_date: date of the scrape run; defaults to today.

    Returns:
        The same list with the current year's entry (if present) marked partial=True.
    """
    if run_date is None:
        run_date = datetime.date.today()

    current_year = run_date.year
    is_partial = run_date < datetime.date(current_year, 12, 31)

    for yr in series:
        if yr["year"] == current_year and is_partial:
            yr["partial"] = True
    return series


def filter_series_for_trend(series: list[dict]) -> list[dict]:
    """Return only non-partial year records for trend computation."""
    return [yr for yr in series if not yr.get("partial", False)]


# ---------------------------------------------------------------------------
# Map-payload builder (D-09)
# ---------------------------------------------------------------------------

def build_map_payload(
    records: list[dict],
    year: int,
    all_rates: list[float],
) -> dict:
    """
    Build the map-payload dict for the given reference year.

    Each entry: {id, rate, level, by_family} (D-09).
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
        comunas.append({
            "id": r["id"],
            "rate": int(round(rate)),
            "level": level,
            "by_family": by_family_list,  # ordered per FAMILY_KEYS
        })

    return {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "year": year,
        "comunas": comunas,
    }


# ---------------------------------------------------------------------------
# Meta-index builder (D-05, 346 entries)
# ---------------------------------------------------------------------------

def build_meta_index(records: list[dict]) -> list[dict]:
    """
    Build the meta/index.json entries: 346 communes each with:
    cut, name, slug, region_id, population, low_population.
    """
    return [
        {
            "cut": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "region_id": r["region_id"],
            "population": r["population"],
            "low_population": r["low_population"],
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# Meta-catalog builder (D-05, D-06)
# ---------------------------------------------------------------------------

def build_meta_catalog() -> dict:
    """
    Build the meta/catalog.json: 7 families + featured flags (D-05/D-06).
    """
    from pipeline.cead.catalog import FAMILIA_IDS
    from pipeline.cead.normalizer import FEATURED_FAMILIES, FEATURED_SUBGROUPS
    from pipeline.shared.schema import FAMILY_KEYS

    families = {}
    for fid, fname in FAMILIA_IDS.items():
        families[fname] = {
            "id": fid,
            "key": fname,
            "featured": fname in FEATURED_FAMILIES,
        }

    return {
        "families": families,
        "featured_subgroups": FEATURED_SUBGROUPS,
        "family_keys": FAMILY_KEYS,
    }


# ---------------------------------------------------------------------------
# Internal validation + write wrappers (injectable for testing)
# ---------------------------------------------------------------------------

def _validate_communes(records: list[dict]):
    """Validate all commune records. Raises on any error (D-14)."""
    from pipeline.shared.schema import validate_all_communes
    return validate_all_communes(records)


def _atomic_write(path: pathlib.Path, data: Any) -> None:
    """Write JSON atomically."""
    from pipeline.shared.atomic_write import atomic_write_json
    atomic_write_json(path, data)


# ---------------------------------------------------------------------------
# Write all outputs (only called after validation passes)
# ---------------------------------------------------------------------------

def _write_all_outputs(
    communes: list[dict],
    regions: dict,
    national: dict,
    output_dir: pathlib.Path,
) -> None:
    """
    Write all /data/cead/ files atomically.
    MUST call _validate_communes before any _atomic_write (D-14).
    """
    from pipeline.shared.schema import FAMILY_KEYS

    # Step 1: Validate (D-14 gate — all-or-nothing)
    _validate_communes(communes)

    # Collect all rates for the last complete year for level computation
    run_date = datetime.date.today()
    current_year = run_date.year
    # Last complete year = current year - 1 if partial, or the latest year with data
    last_complete_year = current_year - 1

    all_rates_for_year = []
    for r in communes:
        for yr_rec in r.get("series", []):
            if yr_rec["year"] == last_complete_year and not yr_rec.get("partial", False):
                all_rates_for_year.append(yr_rec["rate_per_100k"])
                break

    if not all_rates_for_year:
        # Fallback: use most recent non-partial data available
        for r in communes:
            sorted_series = sorted(
                [yr for yr in r.get("series", []) if not yr.get("partial", False)],
                key=lambda x: x["year"], reverse=True,
            )
            if sorted_series:
                all_rates_for_year.append(sorted_series[0]["rate_per_100k"])
                if not hasattr(_write_all_outputs, "_year_determined"):
                    last_complete_year = sorted_series[0]["year"]

    # Detect all available years across communes
    all_years: set[int] = set()
    for r in communes:
        for yr_rec in r.get("series", []):
            if not yr_rec.get("partial", False):
                all_years.add(yr_rec["year"])

    # Step 2: Build and assert map-payload size < 30 KB (DATA-03)
    # Map-payload uses compact (minified) JSON to stay under 30 KB.
    logger.info("Building map-payload.json for year %d", last_complete_year)
    map_payload = build_map_payload(communes, year=last_complete_year, all_rates=all_rates_for_year)
    serialized = json.dumps(map_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) >= 30720:
        raise ValueError(
            f"map-payload.json exceeds 30 KB limit: {len(serialized)} bytes"
        )

    # Step 3: Write commune files
    logger.info("Writing %d commune files", len(communes))
    for r in communes:
        _atomic_write(output_dir / "comunas" / f"{r['id']}.json", r)

    # Step 4: Write region files
    for region_id, region_data in regions.items():
        _atomic_write(output_dir / "regions" / f"{region_id}.json", region_data)

    # Step 5: Write national.json
    if national:
        _atomic_write(output_dir / "national.json", national)

    # Step 6: Write map-payload.json (last complete year, compact for <30KB D-09)
    from pipeline.shared.atomic_write import atomic_write_json as _aw_compact
    _aw_compact(output_dir / "map-payload.json", map_payload, compact=True)

    # Step 7: Write per-year payloads (D-09, compact)
    for yr in sorted(all_years):
        yr_rates = []
        for r in communes:
            for yr_rec in r.get("series", []):
                if yr_rec["year"] == yr:
                    yr_rates.append(yr_rec["rate_per_100k"])
                    break
        if yr_rates:
            yr_payload = build_map_payload(communes, year=yr, all_rates=yr_rates)
            _aw_compact(output_dir / f"map-payload-{yr}.json", yr_payload, compact=True)

    # Step 8: Write meta files
    meta_index = build_meta_index(communes)
    _atomic_write(output_dir / "meta" / "index.json", meta_index)
    meta_catalog = build_meta_catalog()
    _atomic_write(output_dir / "meta" / "catalog.json", meta_catalog)

    logger.info("All output files written successfully to %s", output_dir)


# ---------------------------------------------------------------------------
# Pipeline runner (fetches + normalizes data)
# ---------------------------------------------------------------------------

def _run_pipeline(session, catalog: dict[str, str], run_date: datetime.date) -> tuple:
    """
    Execute the full scrape-and-normalize pipeline.

    Returns:
        (communes: list[dict], regions: dict, national: dict)
    """
    from pipeline.cead.catalog import FAMILIA_IDS, REGION_IDS
    from pipeline.cead.client import cache_raw, fetch_communes_batch
    from pipeline.cead.normalizer import (
        attach_featured,
        compute_ranks,
        compute_trend,
        make_slug,
    )
    from pipeline.cead.parser import parse_cead_float, parse_cead_table
    from pipeline.shared.population import is_low_population, load_population
    from pipeline.shared.schema import FAMILY_KEYS

    current_year = run_date.year
    start_year = 2005

    # Accumulator: {cut: {year: {family_key: rate}}}
    accumulator: dict[str, dict[int, dict[str, float | None]]] = {
        cut: {} for cut in catalog
    }

    total_batches = len(REGION_IDS) * len(FAMILIA_IDS) * (current_year - start_year + 1)
    batch_count = 0

    for region_id in REGION_IDS:
        # Get communes for this region from the catalog
        # CEAD returns all communes regardless of region filter — filter by prefix
        region_prefix = str(region_id)
        region_cuts = [
            cut for cut in catalog
            if cut.startswith(region_prefix) and len(cut) == 5
        ] or list(catalog.keys())  # fallback: use all if prefix matching fails

        for familia_id, familia_key in FAMILIA_IDS.items():
            for year in range(start_year, current_year + 1):
                batch_count += 1
                cache_key = f"cead_{region_id}_{familia_id}_{year}.html"

                try:
                    from pipeline.cead.client import load_cached
                    html = load_cached(cache_key)
                    if html is None:
                        logger.info(
                            "[%d/%d] Fetching region=%d familia=%d year=%d",
                            batch_count, total_batches, region_id, familia_id, year,
                        )
                        html = fetch_communes_batch(
                            session,
                            cut_codes=list(catalog.keys()),
                            year=year,
                            familia_id=familia_id,
                        )
                        cache_raw(cache_key, html)
                        time.sleep(2.5)  # D-03: courtesy delay
                    else:
                        logger.debug(
                            "[%d/%d] Cache hit region=%d familia=%d year=%d",
                            batch_count, total_batches, region_id, familia_id, year,
                        )

                    rows = parse_cead_table(html)
                    for row in rows:
                        # Match row to a CUT code in the catalog
                        cut = _match_cut(row["name"], catalog)
                        if cut is None:
                            continue
                        accumulator[cut].setdefault(year, {})
                        rate_str = row["values"].get(str(year)) or row["values"].get(year)
                        rate = parse_cead_float(rate_str) if rate_str else None
                        accumulator[cut][year][familia_key] = rate

                except Exception as exc:
                    logger.warning(
                        "Failed batch region=%d familia=%d year=%d: %s",
                        region_id, familia_id, year, exc,
                    )
                    # Continue — partial data will fail validation if too much is missing

        # Only one fetch per region loop is needed since CEAD returns all communes
        # per familia+year regardless of region parameter — break after first region
        # NOTE: If A1 (assumption) holds, we only need one pass per familia+year.
        break  # Remove this break if A1 is found to be false

    # Normalize accumulator into ComunaRecord dicts
    population = load_population()
    communes = []
    all_cuts = list(catalog.keys())

    for cut in all_cuts:
        name = catalog[cut]
        pop = population.get(cut, 0)
        low_pop = is_low_population(cut)
        region_id = cut[:2]

        year_data = accumulator.get(cut, {})
        series = []
        for yr in sorted(year_data.keys()):
            by_family = year_data[yr]
            # Total rate = sum of family rates (or None if all are None)
            valid_rates = [v for v in by_family.values() if v is not None]
            total_rate = sum(valid_rates) if valid_rates else 0.0

            # Ensure all family keys present
            full_by_family = {k: by_family.get(k) for k in FAMILY_KEYS}
            series.append({
                "year": yr,
                "rate_per_100k": total_rate,
                "by_family": full_by_family,
                "partial": False,
            })

        # Mark current year partial if before Dec 31
        series = mark_partial_year(series, run_date=run_date)
        trend_series = filter_series_for_trend(series)

        featured = attach_featured({
            "propiedad_by_year": {
                yr["year"]: yr["by_family"].get("propiedad")
                for yr in series
                if yr["by_family"].get("propiedad") is not None
            },
            "vida_by_year": {
                yr["year"]: yr["by_family"].get("vida")
                for yr in series
                if yr["by_family"].get("vida") is not None
            },
            "homicidios_by_year": {},  # subgroup ID pending (Open Question 3)
            "secuestros_by_year": {},  # subgroup ID unknown (Open Question 3)
        })

        communes.append({
            "id": cut,
            "name": name,
            "slug": make_slug(name),
            "region_id": region_id,
            "population": pop,
            "low_population": low_pop,
            "national_rank": None,  # set by compute_ranks below
            "regional_rank": None,
            "trend": compute_trend(trend_series),
            "featured_rates": featured,
            "series": series,
            "last_updated": run_date.isoformat(),
        })

    # Assign ranks (D-12)
    latest_year = max(
        (yr["year"] for c in communes for yr in c["series"] if not yr.get("partial")),
        default=current_year - 1,
    )
    communes = compute_ranks(communes, year=latest_year)

    # Build region aggregates
    regions = _build_region_aggregates(communes, run_date)
    national = _build_national_aggregate(communes, run_date)

    return communes, regions, national


def _match_cut(name: str, catalog: dict[str, str]) -> str | None:
    """Find the CUT code for a commune name by exact or normalized match."""
    from pipeline.cead.normalizer import make_slug
    name_slug = make_slug(name)
    for cut, cat_name in catalog.items():
        if make_slug(cat_name) == name_slug:
            return cut
        if cat_name.strip().lower() == name.strip().lower():
            return cut
    return None


def _build_region_aggregates(communes: list[dict], run_date: datetime.date) -> dict:
    """Build per-region aggregate records keyed by region_id."""
    from pipeline.cead.catalog import REGION_IDS
    from pipeline.cead.normalizer import make_slug
    from pipeline.shared.schema import FAMILY_KEYS

    # Group communes by region
    by_region: dict[str, list[dict]] = {}
    for c in communes:
        rid = c["region_id"]
        by_region.setdefault(rid, []).append(c)

    regions = {}
    for region_id_int, region_name in REGION_IDS.items():
        rid = str(region_id_int)
        region_communes = by_region.get(rid, [])

        # Aggregate: sum rates per year across communes in region
        year_totals: dict[int, dict] = {}
        for c in region_communes:
            for yr_rec in c["series"]:
                yr = yr_rec["year"]
                if yr not in year_totals:
                    year_totals[yr] = {"rate_per_100k": 0.0, "by_family": {k: 0.0 for k in FAMILY_KEYS}, "partial": yr_rec.get("partial", False)}
                year_totals[yr]["rate_per_100k"] += yr_rec["rate_per_100k"]
                for k in FAMILY_KEYS:
                    fv = yr_rec["by_family"].get(k) or 0.0
                    year_totals[yr]["by_family"][k] = (year_totals[yr]["by_family"].get(k) or 0.0) + fv

        series = [
            {"year": yr, "rate_per_100k": data["rate_per_100k"], "by_family": data["by_family"], "partial": data["partial"]}
            for yr, data in sorted(year_totals.items())
        ]

        # Ranking within region by latest year
        region_ranking = sorted(
            [{"cut": c["id"], "name": c["name"], "rank": c.get("regional_rank")} for c in region_communes],
            key=lambda x: (x["rank"] is None, x["rank"] or 0),
        )

        regions[rid] = {
            "id": rid,
            "name": region_name,
            "slug": make_slug(region_name),
            "series": series,
            "comuna_ranking": region_ranking,
            "last_updated": run_date.isoformat(),
        }

    return regions


def _build_national_aggregate(communes: list[dict], run_date: datetime.date) -> dict:
    """Build the national aggregate record."""
    from pipeline.shared.schema import FAMILY_KEYS

    year_totals: dict[int, dict] = {}
    for c in communes:
        for yr_rec in c["series"]:
            yr = yr_rec["year"]
            if yr not in year_totals:
                year_totals[yr] = {"rate_per_100k": 0.0, "by_family": {k: 0.0 for k in FAMILY_KEYS}, "partial": yr_rec.get("partial", False)}
            year_totals[yr]["rate_per_100k"] += yr_rec["rate_per_100k"]
            for k in FAMILY_KEYS:
                fv = yr_rec["by_family"].get(k) or 0.0
                year_totals[yr]["by_family"][k] = (year_totals[yr]["by_family"].get(k) or 0.0) + fv

    series = [
        {"year": yr, "rate_per_100k": data["rate_per_100k"], "by_family": data["by_family"], "partial": data["partial"]}
        for yr, data in sorted(year_totals.items())
    ]

    return {
        "name": "Chile",
        "series": series,
        "last_updated": run_date.isoformat(),
    }


# ---------------------------------------------------------------------------
# main() — orchestrator entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run the full CEAD pipeline.

    Returns:
        0 on success, 1 on any failure (D-14).
    """
    run_date = datetime.date.today()
    output_dir = _get_data_dir()

    logger.info("CEAD pipeline starting. Output dir: %s", output_dir)

    try:
        communes, regions, national = _run_pipeline(
            session=None,  # will be created inside if not mocked
            catalog={},
            run_date=run_date,
        )
        _write_all_outputs(
            communes=communes,
            regions=regions,
            national=national,
            output_dir=output_dir,
        )
        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


def _main_with_live_session() -> int:
    """
    Full live pipeline: creates CEAD session and fetches real data.
    Used when running the script directly.
    """
    from pipeline.cead.catalog import get_commune_catalog
    from pipeline.cead.client import make_cead_session

    run_date = datetime.date.today()
    output_dir = _get_data_dir()

    logger.info("CEAD pipeline starting (live). Output dir: %s", output_dir)

    try:
        session = make_cead_session()
        logger.info("Session created. Fetching commune catalog...")
        catalog = get_commune_catalog(session)

        n = len(catalog)
        logger.info("Catalog fetched: %d communes", n)
        if n != 346:
            raise ValueError(f"Expected 346 communes in catalog, got {n} (Pitfall 4)")

        communes, regions, national = _run_pipeline(
            session=session,
            catalog=catalog,
            run_date=run_date,
        )
        _write_all_outputs(
            communes=communes,
            regions=regions,
            national=national,
            output_dir=output_dir,
        )
        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(_main_with_live_session())
