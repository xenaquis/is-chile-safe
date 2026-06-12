"""
Tests for pipeline.shared.population module (DATA-04 filter substrate).

These tests exercise the real committed data/ine/poblacion_comunal.json —
no mocking needed since it is a static versioned asset.
"""
import json
import pathlib

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_raw() -> list[dict]:
    """Load the raw JSON directly to find real CUT codes for assertions."""
    path = pathlib.Path(__file__).parent.parent.parent / "data" / "ine" / "poblacion_comunal.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_low_pop_cut(data: list[dict], threshold: int = 10_000) -> str:
    """Return the first CUT code whose population is below threshold."""
    for entry in data:
        if entry["population_2024"] < threshold:
            return str(entry["cut"])
    raise AssertionError("No commune with population < 10000 found in dataset")


def _pick_high_pop_cut(data: list[dict], threshold: int = 10_000) -> str:
    """Return the first CUT code whose population is at or above threshold."""
    for entry in data:
        if entry["population_2024"] >= threshold:
            return str(entry["cut"])
    raise AssertionError("No commune with population >= 10000 found in dataset")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadPopulation:
    def test_returns_dict(self):
        from pipeline.shared.population import load_population
        result = load_population()
        assert isinstance(result, dict)

    def test_keys_are_strings(self):
        from pipeline.shared.population import load_population
        result = load_population()
        for key in list(result.keys())[:10]:
            assert isinstance(key, str), f"Expected str key, got {type(key)}: {key}"

    def test_values_are_ints(self):
        from pipeline.shared.population import load_population
        result = load_population()
        for val in list(result.values())[:10]:
            assert isinstance(val, int), f"Expected int value, got {type(val)}: {val}"

    def test_contains_exactly_346_entries(self):
        from pipeline.shared.population import load_population
        result = load_population()
        assert len(result) == 346, f"Expected 346 entries, got {len(result)}"


class TestIsLowPopulation:
    def test_high_population_commune_returns_false(self):
        from pipeline.shared.population import is_low_population
        data = _load_raw()
        cut = _pick_high_pop_cut(data)
        assert is_low_population(cut) is False, (
            f"Expected is_low_population({cut!r}) == False "
            f"(population >= 10000)"
        )

    def test_low_population_commune_returns_true(self):
        from pipeline.shared.population import is_low_population
        data = _load_raw()
        cut = _pick_low_pop_cut(data)
        assert is_low_population(cut) is True, (
            f"Expected is_low_population({cut!r}) == True "
            f"(population < 10000)"
        )

    def test_unknown_cut_returns_true(self):
        """Unknown communes default to population 0 — excluded from rankings (safer)."""
        from pipeline.shared.population import is_low_population
        assert is_low_population("99999") is True

    def test_santiago_is_not_low_population(self):
        """Santiago (13101) must never be flagged as low-population."""
        from pipeline.shared.population import is_low_population
        assert is_low_population("13101") is False


class TestLowPopulationThreshold:
    def test_threshold_constant_exists(self):
        from pipeline.shared import population
        assert hasattr(population, "LOW_POPULATION_THRESHOLD")

    def test_threshold_is_10000(self):
        from pipeline.shared.population import LOW_POPULATION_THRESHOLD
        assert LOW_POPULATION_THRESHOLD == 10_000
