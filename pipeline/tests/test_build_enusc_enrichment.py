"""
pipeline/tests/test_build_enusc_enrichment.py

Tests for pipeline/build_enusc_enrichment.py.

TDD structure (Phase 23-02):
  - test_missing_snapshot_graceful     — graceful sys.exit(0) when snapshot absent
  - test_coverage_assertion            — 136 records resolved == 136 enriched
  - test_additive_only                 — composite_index + featured_rates unchanged after enrich
  - test_phase18_byte_unchanged        — 10-commune byte-identical check on Phase-18 fields
  - test_duplicate_write_refuses_overwrite — idempotent re-run OK; divergent value → RuntimeError

Run:
    python -m pytest pipeline/tests/test_build_enusc_enrichment.py -x
"""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PHASE18_FIELDS = [
    "composite_index",
    "featured_rates",
    "series",
    "national_rank",
    "regional_rank",
    "trend",
    "spd_homicide_rate",
    "sii_exposure_index",
]


def _make_commune(cut: str, include_phase18: bool = True) -> dict:
    """Minimal commune JSON structure."""
    base: dict = {
        "id": cut,
        "name": f"Comuna-{cut}",
        "slug": f"comuna-{cut}",
        "region_id": "13",
    }
    if include_phase18:
        base["composite_index"] = {"2024": {"score": 42.5, "rank": 100, "level": 3}}
        base["featured_rates"] = {"vida": 1.23, "robos": 4.56}
        base["series"] = {"vida": [{"year": 2024, "rate": 1.23}]}
        base["national_rank"] = 100
        base["regional_rank"] = 10
        base["trend"] = "stable"
        base["spd_homicide_rate"] = {"2024": 2.1}
        base["sii_exposure_index"] = {"2024": 0.5}
    return base


def _make_snapshot(cuts: list[str]) -> dict:
    """Minimal enusc_vhdv.json fixture."""
    return {
        "source": "INE test",
        "source_url": "http://example.com",
        "vintage": "2024",
        "fetched": "2026-06-19T00:00:00Z",
        "caveat": "test",
        "records": [
            {
                "cut": cut,
                "name": f"Comuna-{cut}",
                "vhdv_rate": 0.05,
                "ci_lower": 0.04,
                "ci_upper": 0.06,
                "tipo_estimacion": "Directa y sintética",
                "cv": 0.1,
            }
            for cut in cuts
        ],
    }


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_module(monkeypatch, tmp_path: pathlib.Path):
    """Import build_enusc_enrichment with constants patched to tmp_path."""
    # Ensure fresh import every call
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    return mod


# ---------------------------------------------------------------------------
# Test 1: graceful degrade when snapshot is absent
# ---------------------------------------------------------------------------


def test_missing_snapshot_graceful(tmp_path, monkeypatch):
    """No enusc_vhdv.json present → sys.exit(0), no commune files touched."""
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    # Make sure REPO_ROOT points to tmp_path (no snapshots dir)
    sys.path.insert(0, str(REPO_ROOT))

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    # Create a dummy commune so we can verify it was NOT modified
    commune_dir = tmp_path / "data" / "cead" / "comunas"
    commune_dir.mkdir(parents=True)
    commune_path = commune_dir / "13101.json"
    original = _make_commune("13101")
    _write_json(commune_path, original)

    with pytest.raises(SystemExit) as exc_info:
        mod.main()

    assert exc_info.value.code == 0, f"Expected exit 0, got {exc_info.value.code}"

    # Commune must be untouched
    after = json.loads(commune_path.read_text(encoding="utf-8"))
    assert "enusc_vhdv" not in after


# ---------------------------------------------------------------------------
# Test 2: coverage assertion — 136 records, all CUTs present → resolved == 136
# ---------------------------------------------------------------------------


def test_coverage_assertion(tmp_path, monkeypatch):
    """136 snapshot records + 136 commune files → all enriched, no RuntimeError."""
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    # Patch EXPECTED_COVERAGE to 136 for real, but use 136 test CUTs
    monkeypatch.setattr(mod, "EXPECTED_COVERAGE", 136)

    # Create 136 minimal communes with fake CUTs
    cuts = [f"{10000 + i}" for i in range(136)]
    commune_dir = tmp_path / "data" / "cead" / "comunas"
    commune_dir.mkdir(parents=True)
    for cut in cuts:
        _write_json(commune_dir / f"{cut}.json", _make_commune(cut))

    # Write snapshot
    snapshot_dir = tmp_path / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True)
    _write_json(snapshot_dir / "enusc_vhdv.json", _make_snapshot(cuts))

    mod.main()

    # All 136 should have enusc_vhdv with vintage 2024
    for cut in cuts:
        data = json.loads((commune_dir / f"{cut}.json").read_text(encoding="utf-8"))
        assert "enusc_vhdv" in data, f"CUT {cut} missing enusc_vhdv"
        assert data["enusc_vhdv"]["vintage"] == 2024


# ---------------------------------------------------------------------------
# Test 3: additive-only — Phase-18 fields byte-unchanged after enrichment
# ---------------------------------------------------------------------------


def test_additive_only(tmp_path, monkeypatch):
    """Pre-existing composite_index + featured_rates unchanged; enusc_vhdv added."""
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "EXPECTED_COVERAGE", 1)

    cut = "13101"
    commune_dir = tmp_path / "data" / "cead" / "comunas"
    commune_dir.mkdir(parents=True)
    original = _make_commune(cut, include_phase18=True)
    _write_json(commune_dir / f"{cut}.json", original)

    snapshot_dir = tmp_path / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True)
    _write_json(snapshot_dir / "enusc_vhdv.json", _make_snapshot([cut]))

    mod.main()

    after = json.loads((commune_dir / f"{cut}.json").read_text(encoding="utf-8"))

    # enusc_vhdv was added
    assert "enusc_vhdv" in after

    # Phase-18 fields byte-identical
    assert json.dumps(after["composite_index"], sort_keys=True) == json.dumps(
        original["composite_index"], sort_keys=True
    )
    assert json.dumps(after["featured_rates"], sort_keys=True) == json.dumps(
        original["featured_rates"], sort_keys=True
    )


# ---------------------------------------------------------------------------
# Test 4: Phase-18 byte-unchanged — 10-commune sample
# ---------------------------------------------------------------------------


def test_phase18_byte_unchanged(tmp_path, monkeypatch):
    """10-commune sample: all Phase-18 fields identical before/after enrichment."""
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "EXPECTED_COVERAGE", 10)

    cuts = [f"{20000 + i}" for i in range(10)]
    commune_dir = tmp_path / "data" / "cead" / "comunas"
    commune_dir.mkdir(parents=True)

    originals = {}
    for cut in cuts:
        commune = _make_commune(cut, include_phase18=True)
        _write_json(commune_dir / f"{cut}.json", commune)
        originals[cut] = commune

    snapshot_dir = tmp_path / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True)
    _write_json(snapshot_dir / "enusc_vhdv.json", _make_snapshot(cuts))

    mod.main()

    for cut in cuts:
        after = json.loads((commune_dir / f"{cut}.json").read_text(encoding="utf-8"))
        orig = originals[cut]
        for field in PHASE18_FIELDS:
            if field in orig:
                assert json.dumps(after.get(field), sort_keys=True) == json.dumps(
                    orig[field], sort_keys=True
                ), f"Phase-18 field {field!r} changed for CUT {cut}"


# ---------------------------------------------------------------------------
# Test 5: idempotent re-run + divergent overwrite raises RuntimeError
# ---------------------------------------------------------------------------


def test_duplicate_write_refuses_overwrite(tmp_path, monkeypatch):
    """
    Run 1: enrich.
    Run 2: identical snapshot → idempotent (no error).
    Run 3: mutated vhdv_rate for one CUT → RuntimeError containing 'refusing overwrite'.
    """
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]

    import build_enusc_enrichment as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "EXPECTED_COVERAGE", 2)

    cuts = ["13101", "13102"]
    commune_dir = tmp_path / "data" / "cead" / "comunas"
    commune_dir.mkdir(parents=True)
    for cut in cuts:
        _write_json(commune_dir / f"{cut}.json", _make_commune(cut))

    snapshot_dir = tmp_path / "data" / "snapshots"
    snapshot_dir.mkdir(parents=True)
    snapshot_path = snapshot_dir / "enusc_vhdv.json"
    _write_json(snapshot_path, _make_snapshot(cuts))

    # Run 1: initial enrichment
    mod.main()

    # Run 2: identical snapshot → no error (idempotent)
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]
    import build_enusc_enrichment as mod2  # noqa: F811

    monkeypatch.setattr(mod2, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod2, "EXPECTED_COVERAGE", 2)
    mod2.main()  # must not raise

    # Run 3: mutated vhdv_rate for 13101
    if "build_enusc_enrichment" in sys.modules:
        del sys.modules["build_enusc_enrichment"]
    import build_enusc_enrichment as mod3  # noqa: F811

    monkeypatch.setattr(mod3, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod3, "EXPECTED_COVERAGE", 2)

    mutated = _make_snapshot(cuts)
    mutated["records"][0]["vhdv_rate"] = 0.99  # differs from written 0.05
    _write_json(snapshot_path, mutated)

    with pytest.raises(RuntimeError, match="refusing overwrite"):
        mod3.main()
