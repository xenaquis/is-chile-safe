"""
pipeline/tests/test_dedup.py

Tests for pipeline/news/dedup.py — URL dedup + title-similarity dedup.
All fixtures are inline dicts — no file fixtures needed.
"""
from __future__ import annotations

import copy

import pytest

from pipeline.news.dedup import deduplicate, are_duplicates  # type: ignore


@pytest.fixture
def incident_a():
    return {
        "id": "abc1234567890123",
        "cut": "13101",
        "lat": -33.456,
        "lng": -70.654,
        "title_es": "Robo en Santiago deja un herido",
        "title_en": "Robbery in Santiago leaves one injured",
        "date": "2026-06-13",
        "outlet": "BioBio Chile",
        "url": "https://biobiochile.cl/article/1",
        "family": "propiedad",
    }


@pytest.fixture
def incident_b_near_duplicate(incident_a):
    d = copy.deepcopy(incident_a)
    d["id"] = "def4567890123456"
    d["url"] = "https://cooperativa.cl/article/2"
    d["title_es"] = "Robo en Santiago deja herido a hombre"  # near-dup
    d["outlet"] = "Cooperativa"
    return d


@pytest.fixture
def incident_c_distinct(incident_a):
    d = copy.deepcopy(incident_a)
    d["id"] = "ghi7890123456789"
    d["url"] = "https://latercera.com/article/3"
    d["title_es"] = "Festival de música en La Serena celebra 30 años"
    d["outlet"] = "La Tercera"
    d["family"] = "incivilidades"
    return d


# ---------------------------------------------------------------------------
# Test functions (exact names per 05-VALIDATION.md)
# ---------------------------------------------------------------------------


def test_url_dedup(incident_a):
    """Two incidents with the same URL must be deduplicated to one."""
    dup = copy.deepcopy(incident_a)
    dup["id"] = "dup9999999999999"
    result = deduplicate([incident_a, dup])
    assert len(result) == 1


def test_title_similarity(incident_a, incident_b_near_duplicate):
    """Two incidents with near-duplicate titles (ratio>=0.82) must deduplicate."""
    result = deduplicate([incident_a, incident_b_near_duplicate])
    assert len(result) == 1, (
        "Near-duplicate titles should be deduplicated to one incident"
    )


def test_no_false_positive(incident_a, incident_c_distinct):
    """Two incidents with clearly distinct titles must NOT be deduplicated."""
    result = deduplicate([incident_a, incident_c_distinct])
    assert len(result) == 2, (
        "Distinct incidents should not be removed by dedup"
    )
