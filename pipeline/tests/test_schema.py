"""
pipeline/tests/test_schema.py

Tests for pipeline/shared/schema.py — Pydantic v2 models and validation gate.
"""
import copy

import pytest
from pydantic import ValidationError

from pipeline.shared.schema import (
    FAMILY_KEYS,
    FAMILY_KEYS_CANONICAL,
    ByFamily,
    MapPayload,
    MapPayloadEntry,
    validate_all_communes,
)


# ---------------------------------------------------------------------------
# FAMILY_KEYS order CI assertion (TD-07 / T-19-10)
# ---------------------------------------------------------------------------


def test_family_keys_order_matches_canonical():
    """CI gate: FAMILY_KEYS must equal FAMILY_KEYS_CANONICAL exactly.
    Reordering FAMILY_KEYS breaks the compact by_family list in map-payload.json
    and in FiltersRow chip indices. This test fails the build if order changes."""
    assert FAMILY_KEYS == list(FAMILY_KEYS_CANONICAL), (
        f"FAMILY_KEYS order changed!\n"
        f"  current:   {FAMILY_KEYS}\n"
        f"  canonical: {list(FAMILY_KEYS_CANONICAL)}"
    )


def test_family_keys_has_expected_members():
    """All seven crime-family keys must be present in FAMILY_KEYS."""
    expected = {"vida", "robos_violentos", "vif", "drogas", "armas", "propiedad", "incivilidades"}
    assert set(FAMILY_KEYS) == expected, (
        f"FAMILY_KEYS members changed: {set(FAMILY_KEYS)} != {expected}"
    )


def test_by_family_typed_dict_has_all_keys():
    """ByFamily TypedDict must declare all seven family keys."""
    import typing
    hints = typing.get_type_hints(ByFamily)
    assert set(hints.keys()) == set(FAMILY_KEYS), (
        f"ByFamily key mismatch: {set(hints.keys())} != {set(FAMILY_KEYS)}"
    )


# ---------------------------------------------------------------------------
# validate_all_communes — count gate (D-14)
# ---------------------------------------------------------------------------


def test_count_validation_accepts_exactly_346(sample_commune_dict):
    result = validate_all_communes([sample_commune_dict] * 346)
    assert len(result) == 346


def test_count_validation_rejects_less_than_346(sample_commune_dict):
    with pytest.raises(ValueError, match="Expected 346"):
        validate_all_communes([sample_commune_dict] * 200)


def test_count_validation_rejects_more_than_346(sample_commune_dict):
    with pytest.raises(ValueError, match="Expected 346"):
        validate_all_communes([sample_commune_dict] * 347)


# ---------------------------------------------------------------------------
# validate_all_communes — structural validation
# ---------------------------------------------------------------------------


def test_missing_name_key_is_rejected(sample_commune_dict):
    bad = {k: v for k, v in sample_commune_dict.items() if k != "name"}
    with pytest.raises(Exception):  # pydantic.ValidationError propagates
        validate_all_communes([bad] * 346)


def test_non_numeric_id_is_rejected(sample_commune_dict):
    bad = copy.deepcopy(sample_commune_dict)
    bad["id"] = "ABC"
    with pytest.raises(ValidationError):
        validate_all_communes([bad] * 346)


# ---------------------------------------------------------------------------
# validate_all_communes — plausibility checks (D-16)
# ---------------------------------------------------------------------------


def _make_communes_with_rate(sample: dict, rate: float) -> list[dict]:
    """Return 346 communes where the first one has the given rate."""
    records = [copy.deepcopy(sample) for _ in range(346)]
    records[0]["series"][0]["rate_per_100k"] = rate
    return records


def test_negative_rate_is_rejected(sample_commune_dict):
    communes = _make_communes_with_rate(sample_commune_dict, -5.0)
    with pytest.raises(ValueError, match="Negative"):
        validate_all_communes(communes)


def test_implausible_rate_is_rejected(sample_commune_dict):
    # Use a value well above the new 100k cap (decimal-parse corruption produces millions)
    communes = _make_communes_with_rate(sample_commune_dict, 150000.0)
    with pytest.raises(ValueError, match="Implausible"):
        validate_all_communes(communes)


def test_zero_rate_is_accepted(sample_commune_dict):
    communes = _make_communes_with_rate(sample_commune_dict, 0.0)
    result = validate_all_communes(communes)
    assert len(result) == 346


def test_boundary_rate_100000_is_accepted(sample_commune_dict):
    # Cap raised to 100k after first real run — micro-communes reach ~43k per-100k
    communes = _make_communes_with_rate(sample_commune_dict, 100000.0)
    result = validate_all_communes(communes)
    assert len(result) == 346


# ---------------------------------------------------------------------------
# MapPayload / MapPayloadEntry validation
# ---------------------------------------------------------------------------


def test_valid_map_payload_validates():
    # by_family is a compact ordered list matching FAMILY_KEYS (7 entries) for <30KB D-09
    entry = {
        "id": "13101",
        "rate": 11181.0,
        "level": 3,
        "by_family": [100.0, 50.0, None, 20.0, 5.0, 80.0, 15.0],  # 7 values per FAMILY_KEYS
    }
    payload = MapPayload.model_validate(
        {"generated": "2026-06-12T00:00:00Z", "year": 2024, "comunas": [entry]}
    )
    assert len(payload.comunas) == 1
    assert payload.comunas[0].level == 3


def test_map_payload_entry_level_out_of_range_rejected():
    with pytest.raises(ValidationError):
        MapPayloadEntry.model_validate(
            {"id": "13101", "rate": 100.0, "level": 6, "by_family": []}
        )


def test_map_payload_entry_level_zero_rejected():
    with pytest.raises(ValidationError):
        MapPayloadEntry.model_validate(
            {"id": "13101", "rate": 100.0, "level": 0, "by_family": []}
        )
