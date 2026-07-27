"""
pipeline/tests/test_schema_incidents.py

Tests for pipeline/news/schema.py — IncidentRecord, ClassifierOutput, IncidentsFile.
No live API calls — pure Pydantic v2 model validation.
"""
import pytest
from pydantic import ValidationError

from pipeline.news.schema import (
    ClassifierOutput,
    IncidentRecord,
    IncidentsFile,
    validate_incidents_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_incident(**overrides) -> dict:
    base = {
        "id": "abc1234567890123",
        "cut": "13101",
        "lat": -33.456,
        "lng": -70.654,
        "title_es": "Robo en Santiago",
        "title_en": "Robbery in Santiago",
        "date": "2026-06-13",
        "outlet": "BioBio Chile",
        "url": "https://biobiochile.cl/article/123",
        "family": "propiedad",
    }
    base.update(overrides)
    return base


def _valid_incidents_file(**overrides) -> dict:
    base = {
        "generated": "2026-06-13T12:00:00Z",
        "window_days": 30,
        "incidents": [_valid_incident()],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# IncidentsFile round-trip — field names must match TS interface exactly
# ---------------------------------------------------------------------------

def test_incidents_file_valid_round_trip():
    data = _valid_incidents_file()
    obj = IncidentsFile.model_validate(data)
    dumped = obj.model_dump()
    assert set(dumped.keys()) == {"generated", "window_days", "incidents"}
    incident = dumped["incidents"][0]
    assert set(incident.keys()) == {
        "id", "cut", "lat", "lng",
        "title_es", "title_en",
        "date", "outlet", "url", "family",
        "slug",  # optional field, always serialized (None when absent)
    }


def test_validate_incidents_file_helper():
    obj = validate_incidents_file(_valid_incidents_file())
    assert isinstance(obj, IncidentsFile)
    assert len(obj.incidents) == 1


# ---------------------------------------------------------------------------
# IncidentRecord — CUT validation
# ---------------------------------------------------------------------------

def test_invalid_cut_raises_validation_error():
    with pytest.raises(ValidationError, match="CUT"):
        IncidentRecord.model_validate(_valid_incident(cut="99999"))


def test_valid_cut_accepted():
    record = IncidentRecord.model_validate(_valid_incident(cut="13101"))
    assert record.cut == "13101"


# ---------------------------------------------------------------------------
# IncidentRecord — family validation
# ---------------------------------------------------------------------------

def test_invalid_family_raises_validation_error():
    with pytest.raises(ValidationError, match="family"):
        IncidentRecord.model_validate(_valid_incident(family="banditry"))


def test_valid_families_accepted():
    for family in ["vida", "robos_violentos", "vif", "drogas", "armas", "propiedad", "incivilidades"]:
        record = IncidentRecord.model_validate(_valid_incident(family=family))
        assert record.family == family


def test_sexuales_family_accepted_by_incident_record():
    """IncidentRecord must accept news-only family 'sexuales' (j6z Task 1)."""
    record = IncidentRecord.model_validate(_valid_incident(family="sexuales"))
    assert record.family == "sexuales"


def test_sexuales_family_accepted_by_classifier_output():
    """ClassifierOutput must accept news-only family 'sexuales' (j6z Task 1)."""
    from pipeline.news.schema import ClassifierOutput
    output = ClassifierOutput.model_validate({
        "commune_name": "Santiago",
        "region_hint": "Metropolitana",
        "family": "sexuales",
        "title_es": "Hombre detenido por abuso sexual en Santiago",
        "title_en": "Man arrested for sexual abuse in Santiago",
        "summary": "A man was arrested for sexual abuse in Santiago.",
        "confidence": 0.9,
    })
    assert output.family == "sexuales"


# ---------------------------------------------------------------------------
# IncidentRecord — attribution (NEWS-05)
# ---------------------------------------------------------------------------

def test_empty_outlet_raises_validation_error():
    with pytest.raises(ValidationError, match="outlet"):
        IncidentRecord.model_validate(_valid_incident(outlet=""))


def test_whitespace_only_outlet_raises_validation_error():
    with pytest.raises(ValidationError, match="outlet"):
        IncidentRecord.model_validate(_valid_incident(outlet="   "))


def test_empty_url_raises_validation_error():
    with pytest.raises(ValidationError, match="url"):
        IncidentRecord.model_validate(_valid_incident(url=""))


def test_whitespace_only_url_raises_validation_error():
    with pytest.raises(ValidationError, match="url"):
        IncidentRecord.model_validate(_valid_incident(url="   "))


def test_javascript_url_raises_validation_error():
    """CR-01: javascript: scheme must be rejected to prevent XSS in Astro pages."""
    with pytest.raises(ValidationError, match="url"):
        IncidentRecord.model_validate(_valid_incident(url="javascript:alert(1)"))


def test_data_url_raises_validation_error():
    """CR-01: data: scheme must be rejected."""
    with pytest.raises(ValidationError, match="url"):
        IncidentRecord.model_validate(_valid_incident(url="data:text/html,<script>alert(1)</script>"))


def test_http_url_accepted():
    """CR-01: plain http:// URLs are accepted."""
    record = IncidentRecord.model_validate(_valid_incident(url="http://example.com/article"))
    assert record.url == "http://example.com/article"


# ---------------------------------------------------------------------------
# ClassifierOutput — commune_name + region_hint (NEWS-01 redesign)
# ---------------------------------------------------------------------------

def test_classifier_output_null_commune_name_accepted():
    """commune_name=null is valid (location unknown path)."""
    obj = ClassifierOutput.model_validate({
        "commune_name": None,
        "region_hint": None,
        "family": "propiedad",
        "title_es": "Título",
        "title_en": "Title",
        "summary": "Summary text",
        "confidence": 0.87,
    })
    assert obj.commune_name is None


def test_classifier_output_invalid_family_rejected():
    with pytest.raises(ValidationError, match="family"):
        ClassifierOutput.model_validate({
            "commune_name": "Santiago",
            "family": "banditry",
            "title_es": "Título",
            "title_en": "Title",
            "summary": "Summary text",
            "confidence": 0.87,
        })


def test_classifier_output_commune_name_accepted():
    """commune_name is stored as-is; CUT resolution happens in resolver.py."""
    obj = ClassifierOutput.model_validate({
        "commune_name": "Providencia",
        "region_hint": "Metropolitana",
        "family": "vida",
        "title_es": "Homicidio en Providencia",
        "title_en": "Homicide in Providencia",
        "summary": "A person was killed.",
        "confidence": 0.91,
    })
    assert obj.commune_name == "Providencia"
    assert obj.region_hint == "Metropolitana"
    assert obj.confidence == 0.91


# ---------------------------------------------------------------------------
# IncidentRecord — slug field (NEWS-03)
# ---------------------------------------------------------------------------

def test_incident_record_accepts_slug():
    """An IncidentRecord built with slug validates and exposes .slug."""
    record = IncidentRecord.model_validate(_valid_incident(slug="las-condes"))
    assert record.slug == "las-condes"


def test_incident_record_slug_optional():
    """An IncidentRecord without slug still validates (back-compat with existing current.json)."""
    data = _valid_incident()
    data.pop("slug", None)  # ensure slug is absent
    record = IncidentRecord.model_validate(data)
    assert record.slug is None
