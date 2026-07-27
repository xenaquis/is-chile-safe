"""
pipeline/tests/test_repair_sexual_family.py

Tests for pipeline/repair_sexual_family.py — deterministic keyword sweep for
re-classifying sexual-crime incidents from "vida" to "sexuales".

No LLM calls, no network, no R2 access required.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from pipeline.repair_sexual_family import determine_family, _VALID_NEWS_FAMILIES


# ---------------------------------------------------------------------------
# Unit tests for the core predicate
# ---------------------------------------------------------------------------

def test_sexual_title_vida_flips_to_sexuales():
    """An incident with a sexual-crime term and family 'vida' must flip to 'sexuales'."""
    result = determine_family(
        title_es="Hombre detenido por violacion en Valparaiso",
        title_en="Man arrested for rape in Valparaiso",
        summary="A man was arrested for sexual assault.",
        current_family="vida",
    )
    assert result == "sexuales"


def test_sexual_abuso_sexual_flips():
    """'abuso sexual' in title must trigger flip."""
    result = determine_family(
        title_es="Capturado por abuso sexual a menor en Santiago",
        title_en="Arrested for sexual abuse of a minor in Santiago",
        summary="",
        current_family="vida",
    )
    assert result == "sexuales"


def test_grooming_flips():
    """'grooming' in title must trigger flip."""
    result = determine_family(
        title_es="Detenido por grooming en Concepcion",
        title_en="Arrested for grooming in Concepcion",
        summary="",
        current_family="vida",
    )
    assert result == "sexuales"


def test_death_term_co_present_stays_vida():
    """When death term co-occurs with sexual term, family must remain 'vida' (death dominates)."""
    result = determine_family(
        title_es="Femicidio con violacion en La Serena",
        title_en="Femicide with rape in La Serena",
        summary="Woman was killed in a sexual assault.",
        current_family="vida",
    )
    assert result == "vida"


def test_homicidio_with_sexual_stays_vida():
    """Homicidio + sexual assault -> family stays 'vida'."""
    result = determine_family(
        title_es="Homicidio con agresion sexual en Antofagasta",
        title_en="Homicide with sexual assault in Antofagasta",
        summary="Victim died after sexual assault.",
        current_family="vida",
    )
    assert result == "vida"


def test_violento_does_not_false_positive():
    """'violento' or 'violencia' must NOT trigger a flip — only explicit sexual terms."""
    result = determine_family(
        title_es="Robo violento en Las Condes",
        title_en="Violent robbery in Las Condes",
        summary="A violent robbery occurred.",
        current_family="vida",
    )
    assert result == "vida"


def test_violencia_does_not_false_positive():
    """'violencia intrafamiliar' must NOT trigger flip."""
    result = determine_family(
        title_es="Detenido por violencia intrafamiliar grave",
        title_en="Arrested for serious domestic violence",
        summary="",
        current_family="vida",
    )
    assert result == "vida"


def test_non_vida_family_unchanged():
    """Only 'vida' incidents are candidates; other families must not be touched."""
    for family in ["propiedad", "robos_violentos", "drogas", "armas", "incivilidades", "vif"]:
        result = determine_family(
            title_es="Abuso sexual en Santiago",
            title_en="Sexual abuse in Santiago",
            summary="",
            current_family=family,
        )
        assert result == family, f"Family {family!r} must not change even with sexual term"


def test_already_sexuales_unchanged():
    """If family is already 'sexuales', determine_family must leave it unchanged."""
    result = determine_family(
        title_es="Abuso sexual en Santiago",
        title_en="Sexual abuse in Santiago",
        summary="",
        current_family="sexuales",
    )
    assert result == "sexuales"


# ---------------------------------------------------------------------------
# Integration: repaired current.json has nonzero sexuales + valid families
# ---------------------------------------------------------------------------

def test_repaired_current_json_has_sexuales():
    """After running repair, data/incidents/current.json must have sexuales count > 0."""
    current_json = (
        pathlib.Path(__file__).parents[2] / "data" / "incidents" / "current.json"
    )
    if not current_json.exists():
        pytest.skip("data/incidents/current.json not found — run repair first")

    data = json.loads(current_json.read_text(encoding="utf-8"))
    incidents = data["incidents"]
    families = [inc["family"] for inc in incidents]

    sexuales_count = families.count("sexuales")
    assert sexuales_count > 0, (
        f"Expected sexuales count > 0 after repair, got {sexuales_count}"
    )

    invalid = [f for f in families if f not in _VALID_NEWS_FAMILIES]
    assert not invalid, (
        f"Found incidents with invalid family values: {set(invalid)}"
    )
