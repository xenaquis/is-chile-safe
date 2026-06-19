"""
pipeline/tests/conftest.py

Shared pytest fixtures for the pipeline test suite.
"""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_cead_html():
    """Fixture: real CEAD response HTML captured from live endpoint.

    Skipped if the fixture file is not present (requires live data capture).
    """
    html_path = FIXTURES_DIR / "cead_response_sample.html"
    if not html_path.exists():
        pytest.skip("cead_response_sample.html not present — run live capture first")
    return html_path.read_text(encoding="utf-8")


@pytest.fixture
def sample_commune_dict():
    """Fixture: minimal valid commune dict for Pydantic validation tests."""
    return {
        "id": "13101",
        "name": "Santiago",
        "slug": "santiago",
        "region_id": "13",
        "population": 404495,
        "low_population": False,
        "national_rank": 1,
        "regional_rank": 1,
        "trend": "down",
        "featured_rates": {},
        "series": [
            {
                "year": 2024,
                "rate_per_100k": 11181.0,
                "by_family": {
                    "vida": None,
                    "robos_violentos": None,
                    "vif": None,
                    "drogas": None,
                    "armas": None,
                    "propiedad": None,
                    "incivilidades": None,
                },
                "partial": False,
            }
        ],
        "last_updated": "2026-06-12",
    }
