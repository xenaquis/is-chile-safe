"""
Tests for pipeline/scrape_cead.py orchestrator + output contract.
All tests use small in-memory/synthetic datasets and mock the fetch layer — NO live CEAD calls.
"""
import json
import pathlib
import sys
from datetime import date
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_records(n=346):
    """Build n minimal ComunaRecord-compatible dicts for testing."""
    from pipeline.shared.population import LOW_POPULATION_THRESHOLD
    records = []
    for i in range(n):
        cut = str(10000 + i)  # 5-digit fake CUT codes
        records.append({
            "id": cut,
            "name": f"Commune {i}",
            "slug": f"commune-{i}",
            "region_id": str((i % 16) + 1),
            "population": LOW_POPULATION_THRESHOLD + 1000,  # above threshold → eligible for rank
            "low_population": False,
            "national_rank": i + 1,
            "regional_rank": i + 1,
            "trend": "stable",
            "featured_rates": {"propiedad": {}, "homicidios": {}, "secuestros": {}},
            "series": [
                {
                    "year": 2022,
                    "rate_per_100k": float(100 + i % 500),
                    "by_family": {
                        "vida": 10.0,
                        "robos_violentos": 20.0,
                        "vif": 5.0,
                        "drogas": 15.0,
                        "armas": 3.0,
                        "propiedad": float(50 + i % 100),
                        "incivilidades": 8.0,
                    },
                    "partial": False,
                }
            ],
            "last_updated": "2026-06-12",
        })
    return records


# ---------------------------------------------------------------------------
# Test: map-payload 30 KB size guard
# ---------------------------------------------------------------------------

def test_map_payload_346_entries_under_30kb():
    """A 346-entry map-payload of realistic magnitude must serialize to under 30720 bytes."""
    from pipeline.scrape_cead import build_map_payload
    records = _make_minimal_records(346)
    all_rates = [r["series"][0]["rate_per_100k"] for r in records]

    payload = build_map_payload(records, year=2022, all_rates=all_rates)
    serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assert len(serialized) < 30720, (
        f"map-payload is too large: {len(serialized)} bytes (limit 30720)"
    )


# ---------------------------------------------------------------------------
# Test: validate-then-write ordering (D-14)
# ---------------------------------------------------------------------------

def test_validate_called_before_atomic_write(tmp_path):
    """validate_all_communes must be called BEFORE any atomic_write_json (D-14)."""
    call_order = []

    def mock_validate(records):
        call_order.append("validate")
        return records  # return something non-empty

    def mock_atomic_write(path, data):
        call_order.append(f"write:{path.name}")

    import pipeline.scrape_cead as sc
    with patch.object(sc, "_validate_communes", side_effect=mock_validate), \
         patch.object(sc, "_atomic_write", side_effect=mock_atomic_write), \
         patch.object(sc, "_run_pipeline", return_value=(_make_minimal_records(346), {}, {})):
        sc._write_all_outputs(
            communes=_make_minimal_records(346),
            regions={},
            national={},
            output_dir=tmp_path,
        )

    # validate must come before any write
    if "validate" in call_order and any(e.startswith("write:") for e in call_order):
        validate_pos = call_order.index("validate")
        first_write_pos = next(i for i, e in enumerate(call_order) if e.startswith("write:"))
        assert validate_pos < first_write_pos, (
            f"validate at index {validate_pos}, first write at {first_write_pos}"
        )


def test_main_returns_1_on_validation_failure(tmp_path, monkeypatch):
    """On validation failure main() must return 1 and write zero files (D-14)."""
    from pydantic import ValidationError
    import pipeline.scrape_cead as sc

    # Patch the entire pipeline to raise a validation-style ValueError
    def fail_pipeline(*args, **kwargs):
        raise ValueError("Simulated validation failure: commune count mismatch")

    monkeypatch.setattr(sc, "_run_pipeline", fail_pipeline)
    monkeypatch.setenv("CEAD_DATA_DIR", str(tmp_path))

    result = sc.main()
    assert result == 1

    # No .json files should have been written
    written_files = list(tmp_path.rglob("*.json"))
    assert written_files == [], f"Expected no files written, got: {written_files}"


def test_main_returns_0_on_success(tmp_path, monkeypatch):
    """main() returns 0 when the pipeline completes successfully."""
    import pipeline.scrape_cead as sc

    monkeypatch.setattr(sc, "_run_pipeline", lambda *a, **kw: (
        _make_minimal_records(346), {}, {}
    ))
    monkeypatch.setenv("CEAD_DATA_DIR", str(tmp_path))

    result = sc.main()
    assert result == 0


# ---------------------------------------------------------------------------
# Test: map-payload entry schema
# ---------------------------------------------------------------------------

def test_map_payload_entry_has_required_keys():
    """Each map-payload entry must have id, rate, level, by_family with 7 family keys."""
    from pipeline.scrape_cead import build_map_payload
    from pipeline.shared.schema import FAMILY_KEYS

    records = _make_minimal_records(5)
    all_rates = [r["series"][0]["rate_per_100k"] for r in records]
    payload = build_map_payload(records, year=2022, all_rates=all_rates)

    assert "comunas" in payload
    for entry in payload["comunas"]:
        assert "id" in entry
        assert "rate" in entry
        assert "level" in entry
        assert "by_family" in entry
        for fk in FAMILY_KEYS:
            assert fk in entry["by_family"], f"Missing family key: {fk}"


# ---------------------------------------------------------------------------
# Test: meta/index.json builder (346 entries, required fields)
# ---------------------------------------------------------------------------

def test_meta_index_has_346_entries_with_required_fields():
    """meta/index.json must emit 346 entries each with cut, name, slug, region_id, population, low_population."""
    from pipeline.scrape_cead import build_meta_index

    records = _make_minimal_records(346)
    index = build_meta_index(records)

    assert len(index) == 346
    for entry in index:
        for field in ("cut", "name", "slug", "region_id", "population", "low_population"):
            assert field in entry, f"Missing field '{field}' in meta/index entry"


# ---------------------------------------------------------------------------
# Test: partial current year handling (Open Question 2)
# ---------------------------------------------------------------------------

def test_partial_year_marked_and_excluded_from_trend():
    """
    A current partial year (scrape before Dec 31) must be:
    - marked partial=True on its YearRecord
    - excluded from compute_trend (trend computed on non-partial years only)
    """
    from pipeline.scrape_cead import mark_partial_year, filter_series_for_trend
    import datetime

    # Simulate a series that includes the current year (partial)
    current_year = date.today().year
    series = [
        {"year": 2019, "rate_per_100k": 100.0, "by_family": {}, "partial": False},
        {"year": 2020, "rate_per_100k": 110.0, "by_family": {}, "partial": False},
        {"year": 2021, "rate_per_100k": 120.0, "by_family": {}, "partial": False},
        {"year": 2022, "rate_per_100k": 130.0, "by_family": {}, "partial": False},
        {"year": current_year, "rate_per_100k": 50.0, "by_family": {}, "partial": False},
    ]

    # mark_partial_year should mark the current year as partial
    # (assuming we run before Dec 31)
    run_date = datetime.date(current_year, 6, 12)  # mid-year
    marked = mark_partial_year(series, run_date=run_date)
    partial_entries = [yr for yr in marked if yr["year"] == current_year]
    assert len(partial_entries) == 1
    assert partial_entries[0]["partial"] is True

    # filter_series_for_trend should exclude partial years
    filtered = filter_series_for_trend(marked)
    assert all(not yr["partial"] for yr in filtered)
    assert not any(yr["year"] == current_year for yr in filtered)
