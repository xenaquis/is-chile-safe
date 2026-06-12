"""
pipeline/tests/test_schema.py

Tests for pipeline/shared/schema.py — Pydantic v2 models and validation gate.
"""
import copy

import pytest
from pydantic import ValidationError

from pipeline.shared.schema import (
    MapPayload,
    MapPayloadEntry,
    validate_all_communes,
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
    communes = _make_communes_with_rate(sample_commune_dict, 25000.0)
    with pytest.raises(ValueError, match="Implausible"):
        validate_all_communes(communes)


def test_zero_rate_is_accepted(sample_commune_dict):
    communes = _make_communes_with_rate(sample_commune_dict, 0.0)
    result = validate_all_communes(communes)
    assert len(result) == 346


def test_boundary_rate_20000_is_accepted(sample_commune_dict):
    communes = _make_communes_with_rate(sample_commune_dict, 20000.0)
    result = validate_all_communes(communes)
    assert len(result) == 346


# ---------------------------------------------------------------------------
# MapPayload / MapPayloadEntry validation
# ---------------------------------------------------------------------------


def test_valid_map_payload_validates():
    entry = {
        "id": "13101",
        "rate": 11181.0,
        "level": 3,
        "by_family": {"vida": 100.0, "propiedad": None},
    }
    payload = MapPayload.model_validate(
        {"generated": "2026-06-12T00:00:00Z", "year": 2024, "comunas": [entry]}
    )
    assert len(payload.comunas) == 1
    assert payload.comunas[0].level == 3


def test_map_payload_entry_level_out_of_range_rejected():
    with pytest.raises(ValidationError):
        MapPayloadEntry.model_validate(
            {"id": "13101", "rate": 100.0, "level": 6, "by_family": {}}
        )


def test_map_payload_entry_level_zero_rejected():
    with pytest.raises(ValidationError):
        MapPayloadEntry.model_validate(
            {"id": "13101", "rate": 100.0, "level": 0, "by_family": {}}
        )
