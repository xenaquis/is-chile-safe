"""
pipeline/tests/test_composite.py

Tests for the composite crime-exposure index pipeline.

TDD structure:
  - test_composite_config_weights_sum_to_one  — GREEN (Task 1 config test)
  - test_composite_config_constants           — GREEN (Task 1 config test)
  - test_year_alignment                       — RED until Task 2 (composite_index.py)
  - test_sii_cap_logic                        — RED until Task 2
  - test_composite_distribution               — RED until Task 3 (build_composite_index.py)
  - test_output_schema                        — RED until Task 3

Run:
    python -m pytest pipeline/tests/test_composite.py -x
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Task 1: Config tests (GREEN immediately)
# ---------------------------------------------------------------------------


def test_composite_config_weights_sum_to_one() -> None:
    from pipeline.composite_config import METRIC_WEIGHTS

    total = sum(METRIC_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"
    assert "incivilidades" not in METRIC_WEIGHTS, (
        "incivilidades must NOT be in METRIC_WEIGHTS (excluded per C-01)"
    )
    # C-01: homicide is M1 (spd_homicide_rate)
    assert "spd_homicide_rate" in METRIC_WEIGHTS, "spd_homicide_rate (M1) must be present"
    assert len(METRIC_WEIGHTS) == 7, f"Expected 7 metrics, got {len(METRIC_WEIGHTS)}"


def test_composite_config_constants() -> None:
    from pipeline.composite_config import (
        REFERENCE_YEAR,
        SII_CAP_RATIO,
        TOTAL_COMMUNES,
        WINSORIZE_LIMITS,
    )

    assert REFERENCE_YEAR == 2024
    assert WINSORIZE_LIMITS == (0.01, 0.01)
    assert SII_CAP_RATIO == 5.0
    assert TOTAL_COMMUNES == 346


# ---------------------------------------------------------------------------
# Fixtures (mirroring test_scrape_cead.py _make_records_with_homicide shape)
# ---------------------------------------------------------------------------


def _make_commune_record(
    cut: str,
    vida_rate: float,
    robos_rate: float,
    propiedad_rate: float,
    vif_rate: float,
    drogas_rate: float,
    armas_rate: float,
    spd_homicide_rate: float = 1.0,
    population: int = 50000,
    region_id: str = "13",
    year: int = 2024,
) -> dict:
    """Minimal commune record dict for composite index testing."""
    return {
        "id": cut,
        "name": f"Commune {cut}",
        "slug": f"commune-{cut}",
        "region_id": region_id,
        "population": population,
        "low_population": False,
        "national_rank": 1,
        "regional_rank": 1,
        "trend": "stable",
        "featured_rates": {
            "propiedad": {str(year): propiedad_rate},
            "homicidios": {str(year): spd_homicide_rate},
            "secuestros": {},
        },
        "series": [
            {
                "year": year,
                "rate_per_100k": vida_rate + robos_rate + propiedad_rate + vif_rate + drogas_rate + armas_rate,
                "by_family": {
                    "vida": vida_rate,
                    "robos_violentos": robos_rate,
                    "vif": vif_rate,
                    "drogas": drogas_rate,
                    "armas": armas_rate,
                    "propiedad": propiedad_rate,
                    "incivilidades": 10.0,
                },
                "partial": False,
            }
        ],
        "last_updated": "2026-06-19",
    }


def _make_fixture_commune_set(n: int = 50) -> list[dict]:
    """Generate n commune fixture records with varying rates (including one extreme outlier)."""
    records = []
    for i in range(n):
        cut = str(10000 + i)
        # Right-skewed: one extreme outlier at index 0
        multiplier = 500.0 if i == 0 else float(i + 1)
        records.append(
            _make_commune_record(
                cut=cut,
                vida_rate=round(multiplier * 0.5, 2),
                robos_rate=round(multiplier * 1.0, 2),
                propiedad_rate=round(multiplier * 2.0, 2),
                vif_rate=round(multiplier * 0.3, 2),
                drogas_rate=round(multiplier * 0.1, 2),
                armas_rate=round(multiplier * 0.05, 2),
                spd_homicide_rate=round(multiplier * 0.02, 2),
                population=50000,
                region_id=str((i % 16) + 1),
            )
        )
    return records


# ---------------------------------------------------------------------------
# Task 2: Pure function tests (RED until composite_index.py exists)
# ---------------------------------------------------------------------------


def test_year_alignment() -> None:
    from pipeline.composite_index import assert_year_alignment

    # Aligned years should return None (no exception)
    result = assert_year_alignment(2024, 2024, 2024)
    assert result is None

    # Misaligned years must raise ValueError
    with pytest.raises(ValueError, match="2025"):
        assert_year_alignment(2025, 2024, 2024)

    with pytest.raises(ValueError):
        assert_year_alignment(2024, 2023, 2024)


def test_sii_cap_logic() -> None:
    from pipeline.composite_index import get_exposure_denominator

    # Providencia CUT 13123: ratio 5.19 -> INE fallback (used_cap=True)
    sii_by_cut = {"13123": 603190, "13114": 267830}
    ine_pop = {"13123": 116202, "13114": 66494}

    denom_prov, capped_prov = get_exposure_denominator("13123", sii_by_cut, ine_pop)
    assert capped_prov is True, "Providencia ratio 5.19 must trigger SII cap"
    assert abs(denom_prov - 116202) < 1, "Providencia must use INE denominator when capped"

    # Las Condes CUT 13114: ratio 4.03 -> SII (used_cap=False)
    denom_lc, capped_lc = get_exposure_denominator("13114", sii_by_cut, ine_pop)
    assert capped_lc is False, "Las Condes ratio 4.03 must NOT trigger SII cap"
    assert abs(denom_lc - 267830) < 1, "Las Condes must use SII workers as denominator"

    # Commune absent from SII -> INE fallback (used_cap=False)
    denom_absent, capped_absent = get_exposure_denominator("11201", sii_by_cut, ine_pop)
    assert capped_absent is False
    # Absent from ine_pop too -> returns 0
    denom_no_ine, _ = get_exposure_denominator("99999", {}, {})
    assert denom_no_ine == 0.0


def test_normalize_spread() -> None:
    """Winsorized normalization: right-skewed series with one huge outlier must
    still yield 25th-pctile > 10% of max (D-01 spread guard)."""
    import numpy as np
    import pandas as pd
    from pipeline.composite_index import normalize_metric

    # Right-skewed series: one extreme outlier at 43000 (Sierra Gorda level)
    values = [float(i) for i in range(1, 346)]
    values[0] = 43000.0  # extreme outlier

    series = pd.Series(values)
    normalized = normalize_metric(series)

    # No NaN in output when input has no NaN
    assert not normalized.isna().any(), "No NaN expected when input has no NaN"

    # Spread guard: 25th pctile > 10% of max
    p25 = normalized.describe()["25%"]
    max_val = normalized.max()
    assert p25 > max_val * 0.10, (
        f"Spread guard failed: 25th pctile {p25:.2f} <= 10% of max {max_val:.2f}. "
        "Winsorization may not be working."
    )

    # NaN re-injection: NaN inputs must stay NaN in output
    values_with_nan = [float(i) for i in range(1, 346)]
    values_with_nan[5] = float("nan")
    series_nan = pd.Series(values_with_nan)
    normalized_nan = normalize_metric(series_nan)
    assert normalized_nan.isna().iloc[5], "NaN in input must produce NaN in output"


def test_normalize_nan_outlier_clip() -> None:
    """NaN commune coexisting with a large outlier must NOT corrupt the clip point.

    Regression for Gap 3 (CI-02): scipy winsorize sorts NaN to the high end, so
    without masking the upper 1% clip point is derived from NaN positions rather
    than real-data maxima. This test constructs a series with BOTH a NaN commune
    AND a Sierra-Gorda-scale outlier and asserts the clip point comes from real data.
    """
    import numpy as np
    import pandas as pd
    from pipeline.composite_index import normalize_metric

    # Build a series of 346 ascending values (mimicking 346 communes)
    values = [float(i) for i in range(1, 347)]
    # One commune is a large outlier (Sierra Gorda level)
    values[0] = 43000.0
    # A distinct commune is NaN (missing data)
    nan_idx = 10
    values[nan_idx] = float("nan")

    series = pd.Series(values)
    normalized = normalize_metric(series)

    # (1) NaN position must remain NaN in output
    assert normalized.isna().iloc[nan_idx], (
        f"Index {nan_idx} must stay NaN in output"
    )

    # (2) Non-NaN max of output must be exactly 100.0 (clip point from real data)
    non_nan_output = normalized.dropna()
    max_val = non_nan_output.max()
    assert np.isfinite(max_val), "Non-NaN output max must be finite"
    assert abs(max_val - 100.0) < 1e-9, (
        f"Non-NaN output max must be 100.0 (clip from real data), got {max_val:.6f}"
    )

    # (3) Spread guard: 25th pctile of non-NaN output > 10% of max
    p25 = non_nan_output.quantile(0.25)
    assert p25 > max_val * 0.10, (
        f"Spread guard failed: 25th pctile {p25:.2f} <= 10% of max {max_val:.2f}. "
        "Winsorization of non-NaN subset may not be working correctly."
    )


# ---------------------------------------------------------------------------
# Task 3: Entrypoint + distribution tests (RED until build_composite_index.py)
# ---------------------------------------------------------------------------


def _write_fixture_files(
    tmp_dir: pathlib.Path,
    commune_records: list[dict],
    spd_records: list[dict] | None = None,
    sii_records: list[dict] | None = None,
    ine_records: list[dict] | None = None,
) -> None:
    """Write fixture data files to a temp dir for testing build_composite_index."""
    # Write commune JSON files
    comunas_dir = tmp_dir / "comunas"
    comunas_dir.mkdir(parents=True, exist_ok=True)
    for rec in commune_records:
        (comunas_dir / f"{rec['id']}.json").write_text(
            json.dumps(rec, ensure_ascii=False), encoding="utf-8"
        )

    # Write SPD snapshot
    snapshots_dir = tmp_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    if spd_records is None:
        spd_records = [
            {"cut": rec["id"], "name": rec["name"], "year": 2024, "homicides": max(1, i)}
            for i, rec in enumerate(commune_records)
        ]

    (snapshots_dir / "spd_homicide.json").write_text(
        json.dumps({
            "source": "SPD VHC",
            "source_url": "https://prevenciondehomicidios.cl",
            "vintage": "2018-2024",
            "fetched": "2026-06-19T00:00:00Z",
            "caveat": "",
            "records": spd_records,
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    if sii_records is None:
        sii_records = [
            {"cut": rec["id"], "name": rec["name"], "year": 2024,
             "empresas": 1000, "trabajadores": 30000}
            for rec in commune_records
        ]

    (snapshots_dir / "sii_exposure.json").write_text(
        json.dumps({
            "source": "SII",
            "source_url": "https://www.sii.cl",
            "vintage": "2005-2024",
            "fetched": "2026-06-19T00:00:00Z",
            "caveat": "",
            "records": sii_records,
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    if ine_records is None:
        ine_records = [
            {"cut": rec["id"], "name": rec["name"], "population_2024": rec["population"]}
            for rec in commune_records
        ]

    ine_dir = tmp_dir / "ine"
    ine_dir.mkdir(parents=True, exist_ok=True)
    (ine_dir / "poblacion_comunal.json").write_text(
        json.dumps(ine_records, ensure_ascii=False),
        encoding="utf-8",
    )


def test_build_composite_index(tmp_path: pathlib.Path) -> None:
    """Running build_composite_index against fixture data enriches commune files."""
    from pipeline.build_composite_index import run_composite_index

    commune_records = _make_fixture_commune_set(n=50)
    _write_fixture_files(tmp_path, commune_records)

    run_composite_index(data_dir=tmp_path)

    # Check first commune was enriched
    first_cut = commune_records[0]["id"]
    enriched = json.loads(
        (tmp_path / "comunas" / f"{first_cut}.json").read_text(encoding="utf-8")
    )
    ci = enriched.get("composite_index", {}).get("2024")
    assert ci is not None, "composite_index['2024'] must be present after enrichment"
    assert "score" in ci
    assert "rank" in ci
    assert "regional_rank" in ci
    assert "level" in ci
    assert "available_metrics" in ci

    # Scores are in range 0-100
    assert 0 <= ci["score"] <= 100, f"Score out of range: {ci['score']}"
    assert 1 <= ci["level"] <= 5, f"Level out of range: {ci['level']}"

    # comparator_table.json written
    comparator = json.loads(
        (tmp_path / "comparator_table.json").read_text(encoding="utf-8")
    )
    assert isinstance(comparator, list), "comparator_table.json must be a list"
    assert len(comparator) == 50
    assert "composite_index" in comparator[0]


def test_composite_distribution(tmp_path: pathlib.Path) -> None:
    """D-01 spread guard: 25th pctile > 10% of max after winsorization."""
    import pandas as pd
    from pipeline.build_composite_index import run_composite_index

    commune_records = _make_fixture_commune_set(n=50)
    _write_fixture_files(tmp_path, commune_records)

    run_composite_index(data_dir=tmp_path)

    # Collect all scores
    scores = []
    for rec in commune_records:
        cut = rec["id"]
        enriched = json.loads(
            (tmp_path / "comunas" / f"{cut}.json").read_text(encoding="utf-8")
        )
        ci = enriched["composite_index"]["2024"]
        scores.append(ci["score"])

    series = pd.Series(scores)
    p25 = series.describe()["25%"]
    max_val = series.max()
    assert p25 > max_val * 0.10, (
        f"Distribution spread guard failed: 25th pctile {p25:.2f} <= 10% of max {max_val:.2f}"
    )


def test_output_schema(tmp_path: pathlib.Path) -> None:
    """Output schema: score roundable to int 0-100, level 1-5, ranks present."""
    from pipeline.build_composite_index import run_composite_index

    commune_records = _make_fixture_commune_set(n=50)

    # Make commune at index 5 absent from SPD (zero-homicide commune)
    absent_cut = commune_records[5]["id"]
    spd_records = [
        {"cut": rec["id"], "name": rec["name"], "year": 2024, "homicides": 1}
        for rec in commune_records
        if rec["id"] != absent_cut  # absent = 0 homicides
    ]

    # Make commune at index 10 absent from SII
    absent_sii_cut = commune_records[10]["id"]
    sii_records = [
        {"cut": rec["id"], "name": rec["name"], "year": 2024,
         "empresas": 1000, "trabajadores": 30000}
        for rec in commune_records
        if rec["id"] != absent_sii_cut
    ]

    _write_fixture_files(tmp_path, commune_records, spd_records=spd_records, sii_records=sii_records)
    run_composite_index(data_dir=tmp_path)

    for rec in commune_records:
        cut = rec["id"]
        enriched = json.loads(
            (tmp_path / "comunas" / f"{cut}.json").read_text(encoding="utf-8")
        )
        ci = enriched["composite_index"]["2024"]

        # Score roundable to int 0-100
        score_int = round(ci["score"])
        assert 0 <= score_int <= 100, f"CUT {cut}: score {ci['score']} out of 0-100"

        # Level 1-5
        assert 1 <= ci["level"] <= 5, f"CUT {cut}: level {ci['level']} out of 1-5"

        # Rank in 1..N (not necessarily 346 in fixture)
        assert ci["rank"] >= 1

        # Regional rank present and >= 1
        assert "regional_rank" in ci, f"CUT {cut}: regional_rank missing"
        assert ci["regional_rank"] >= 1

        # featured_rates preserved (D-12 non-breaking)
        assert "featured_rates" in enriched
        assert "homicidios" in enriched["featured_rates"]

    # SPD-absent commune has spd_homicide_rate 0.0
    enriched_absent = json.loads(
        (tmp_path / "comunas" / f"{absent_cut}.json").read_text(encoding="utf-8")
    )
    assert enriched_absent.get("spd_homicide_rate", {}).get("2024") == 0.0

    # SII-absent commune has sii_exposure_index null and available_metrics == 6
    enriched_no_sii = json.loads(
        (tmp_path / "comunas" / f"{absent_sii_cut}.json").read_text(encoding="utf-8")
    )
    sii_idx = enriched_no_sii.get("sii_exposure_index", {})
    assert sii_idx.get("2024") is None, f"SII-absent commune must have sii_exposure_index null, got {sii_idx}"
    assert enriched_no_sii["composite_index"]["2024"]["available_metrics"] == 6
