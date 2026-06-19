"""
pipeline/tests/test_scrape_news.py

Integration test for pipeline/scrape_news.py orchestrator.

Strategy:
- monkeypatch FEEDS to a single synthetic feed with 3 entries (2 crime, 1 non-crime)
- monkeypatch fetch_feed to return feedparser-compatible objects from fixture XML
- mock classify() to return deterministic ClassifierOutput (NEVER live DeepSeek)
- mock get_centroid() to return a known (lat, lng) for the test CUT
- assert main() returns 0 and current.json validates via IncidentsFile.model_validate
- assert attribution fields (outlet, url, date) are present (NEWS-05)
- assert dedup runs (injecting two near-identical items produces one incident)
- assert missing DEEPSEEK_API_KEY returns 1 without raising
"""
from __future__ import annotations

import json
import os
import pathlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A real valid CUT from the 346-commune list
_VALID_CUT = "13101"  # Santiago

# Minimal feedparser-like entry object
def _make_entry(title: str, link: str, guid: str, description: str, pub_date: str) -> SimpleNamespace:
    entry = SimpleNamespace()
    entry.title = title
    entry.link = link
    entry.id = guid
    entry.summary = description
    entry.description = description
    # feedparser normalises pubDate into published_parsed (time.struct_time 9-tuple)
    import time
    entry.published_parsed = time.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
    return entry


_CRIME_ENTRY_1 = _make_entry(
    title="Robo con violencia en Santiago deja un herido grave",
    link="https://www.biobiochile.cl/noticias/robo-santiago.shtml",
    guid="https://www.biobiochile.cl/?p=1001",
    description="Un hombre resultó herido durante un asalto en plena vía pública.",
    pub_date="2026-06-13T08:00:00Z",
)

_CRIME_ENTRY_2 = _make_entry(
    title="Carabineros detiene banda narco en Puente Alto",
    link="https://www.biobiochile.cl/noticias/narco-puente-alto.shtml",
    guid="https://www.biobiochile.cl/?p=1002",
    description="La PDI detuvo a cinco imputados acusados de narcotráfico.",
    pub_date="2026-06-13T09:00:00Z",
)

_NON_CRIME_ENTRY = _make_entry(
    title="La Roja golea 3-0 a Paraguay en partido amistoso",
    link="https://www.biobiochile.cl/noticias/la-roja-goleada.shtml",
    guid="https://www.biobiochile.cl/?p=1003",
    description="La selección chilena venció a Paraguay en el estadio Nacional.",
    pub_date="2026-06-13T10:00:00Z",
)

# Duplicate of entry 1 (same URL → dedup by url should collapse)
_CRIME_ENTRY_1_DUP = _make_entry(
    title="Robo con violencia en Santiago deja un herido grave",
    link="https://www.biobiochile.cl/noticias/robo-santiago.shtml",  # same URL
    guid="https://www.biobiochile.cl/?p=1001",
    description="Un hombre resultó herido durante un asalto en plena vía pública.",
    pub_date="2026-06-13T08:00:00Z",
)

_TEST_FEEDS = {
    "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
}


def _make_classifier_output(commune_name: str = "Santiago"):
    from pipeline.news.schema import ClassifierOutput
    return ClassifierOutput(
        commune_name=commune_name,
        region_hint="Metropolitana",
        family="propiedad",
        title_es="Robo con violencia en Santiago",
        title_en="Violent robbery in Santiago",
        summary="A man was injured during a robbery.",
        confidence=0.9,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def news_data_dir(tmp_path, monkeypatch):
    """Redirect NEWS_DATA_DIR to a tmp_path and return it."""
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture(autouse=False)
def deepseek_key(monkeypatch):
    """Set a fake DEEPSEEK_API_KEY so the key-check passes."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake-test-key")


# ---------------------------------------------------------------------------
# Test: full pipeline happy path
# ---------------------------------------------------------------------------

def test_main_happy_path(tmp_path, monkeypatch):
    """
    Full pipeline with mocked feeds + mocked DeepSeek.
    Asserts:
    - main() returns 0
    - current.json validates via IncidentsFile.model_validate
    - incidents have attribution fields (outlet, url, date)
    - dedup collapses the duplicate URL (3 crime-matching entries → 2 unique URLs → 2 incidents)
    - centroid lat/lng are present
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    # Patch FEEDS registry to our synthetic single feed
    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed") as mock_fetch, \
         patch("pipeline.news.classifier.classify") as mock_classify, \
         patch("pipeline.news.resolver.resolve_cut") as mock_resolve, \
         patch("pipeline.news.centroids.get_centroid") as mock_centroid:

        # Feed returns 3 entries: 2 crime + 1 non-crime + 1 duplicate crime URL
        mock_fetch.return_value = [
            _CRIME_ENTRY_1,
            _CRIME_ENTRY_1_DUP,   # duplicate URL — should be collapsed
            _CRIME_ENTRY_2,
            _NON_CRIME_ENTRY,
        ]

        # classifier returns different output per call (different title_es prevents title dedup)
        from pipeline.news.schema import ClassifierOutput
        side_effects = [
            ClassifierOutput(
                commune_name="Santiago", region_hint="Metropolitana", family="propiedad",
                title_es="Robo con violencia en Santiago",
                title_en="Violent robbery in Santiago",
                summary="A man was injured during a robbery.",
                confidence=0.9,
            ),
            ClassifierOutput(
                commune_name="Puente Alto", region_hint="Metropolitana", family="drogas",
                title_es="Carabineros detiene banda narco en Puente Alto",
                title_en="Police arrest drug gang in Puente Alto",
                summary="Five suspects arrested for drug trafficking.",
                confidence=0.85,
            ),
        ]
        mock_classify.side_effect = side_effects

        # resolve_cut returns (cut, slug) for any valid commune name
        mock_resolve.return_value = (_VALID_CUT, "santiago")

        # centroid returns known coords for the valid CUT
        mock_centroid.return_value = (-33.45, -70.67)

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0, "main() should return 0 on success"

    current_path = tmp_path / "current.json"
    assert current_path.exists(), "current.json must exist after a successful run"

    data = json.loads(current_path.read_text(encoding="utf-8"))

    # Schema validation: must pass IncidentsFile.model_validate
    from pipeline.news.schema import IncidentsFile
    incidents_file = IncidentsFile.model_validate(data)

    incidents = incidents_file.incidents
    # 2 unique crime URLs should produce 2 classified incidents (duplicate URL collapsed)
    assert len(incidents) == 2, (
        f"Expected 2 incidents after dedup, got {len(incidents)}: {incidents}"
    )

    # Each incident must have attribution fields (NEWS-05)
    for inc in incidents:
        assert inc.outlet, "outlet must not be empty (NEWS-05)"
        assert inc.url, "url must not be empty (NEWS-05)"
        assert inc.date, "date must be present"
        assert inc.lat != 0.0, "lat must be non-zero"
        assert inc.lng != 0.0, "lng must be non-zero"
        assert inc.cut == _VALID_CUT, f"cut must be {_VALID_CUT}"

    # Window metadata
    assert data["window_days"] == 30
    assert "generated" in data


# ---------------------------------------------------------------------------
# Test: missing DEEPSEEK_API_KEY returns 1 without raising
# ---------------------------------------------------------------------------

def test_main_no_api_key_returns_0(tmp_path, monkeypatch):
    """Absent API key must produce return code 0 (graceful exit), not raise.

    The orchestrator degrades gracefully: no key → no data change → exit 0.
    (CLAUDE.md: 'pipeline debe fallar con gracia y alertar')
    """
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    import pipeline.scrape_news as sn
    result = sn.main()
    assert result == 0, "main() must return 0 (graceful exit) when API key is absent"

    # No files should be written
    written = list(tmp_path.rglob("*.json"))
    assert written == [], f"No files should be written when key is absent: {written}"


# ---------------------------------------------------------------------------
# Test: per-feed failure is isolated (one bad feed does not stop others)
# ---------------------------------------------------------------------------

def test_per_feed_failure_isolated(tmp_path, monkeypatch):
    """If one feed raises, main() continues with the others and still returns 0."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    two_feeds = {
        "BadFeed": "https://broken.example.com/feed",
        "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
    }

    def _mock_fetch(name, url):
        if name == "BadFeed":
            raise RuntimeError("Connection refused")
        return [_CRIME_ENTRY_1]

    with patch("pipeline.news.feeds.FEEDS", two_feeds), \
         patch("pipeline.news.feeds.fetch_feed", side_effect=_mock_fetch), \
         patch("pipeline.news.classifier.classify", return_value=_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    # Pipeline should succeed using the good feed
    assert result == 0, "Per-feed failure must not abort the pipeline"

    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    from pipeline.news.schema import IncidentsFile
    IncidentsFile.model_validate(data)
    assert len(data["incidents"]) == 1


# ---------------------------------------------------------------------------
# Test: classifier returning None skips the item
# ---------------------------------------------------------------------------

def test_classifier_none_items_skipped(tmp_path, monkeypatch):
    """Items rejected by classify() (returns None) must not appear in output."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1, _CRIME_ENTRY_2]), \
         patch("pipeline.news.classifier.classify", return_value=None), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert data["incidents"] == [], "All rejected items must produce an empty incidents list"


# ---------------------------------------------------------------------------
# Test: centroid None skips the item
# ---------------------------------------------------------------------------

def test_centroid_none_items_skipped(tmp_path, monkeypatch):
    """Items with unknown centroid must be skipped."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         patch("pipeline.news.classifier.classify", return_value=_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=None):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert data["incidents"] == []


# ---------------------------------------------------------------------------
# Test: IncidentPinLayer.ts field name compatibility (D-15)
# ---------------------------------------------------------------------------

def test_incident_field_names_match_ts_interface(tmp_path, monkeypatch):
    """
    IncidentRecord fields must match the TypeScript Incident interface exactly (D-15):
    id, cut, lat, lng, title_es, title_en, date, outlet, url, family.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         patch("pipeline.news.classifier.classify", return_value=_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        sn.main()

    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    required_fields = {"id", "cut", "lat", "lng", "title_es", "title_en", "date", "outlet", "url", "family"}
    incident = data["incidents"][0]
    missing = required_fields - set(incident.keys())
    assert not missing, f"Incident missing TS interface fields: {missing}"


# ---------------------------------------------------------------------------
# Test: orchestrator resolves commune_name via resolve_cut (NEWS-03 / Task 2)
# ---------------------------------------------------------------------------

def test_orchestrator_resolves_name(tmp_path, monkeypatch):
    """With a valid commune_name, the built incident has the resolved cut + non-null slug."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    from pipeline.news.schema import ClassifierOutput
    classifier_output = ClassifierOutput(
        commune_name="Las Condes",
        region_hint="Metropolitana",
        family="propiedad",
        title_es="Robo en Las Condes",
        title_en="Robbery in Las Condes",
        summary="A robbery occurred.",
        confidence=0.9,
    )
    _LAS_CONDES_CUT = "13110"

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         patch("pipeline.news.classifier.classify", return_value=classifier_output), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_LAS_CONDES_CUT, "las-condes")) as mock_resolve, \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.41, -70.58)):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    mock_resolve.assert_called_once_with("Las Condes", "Metropolitana")
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert len(data["incidents"]) == 1
    inc = data["incidents"][0]
    assert inc["cut"] == _LAS_CONDES_CUT
    assert inc["slug"] == "las-condes"


def test_orchestrator_drops_unresolved_name(tmp_path, monkeypatch):
    """When resolve_cut returns None (unknown commune name), the incident is dropped — no crash."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         patch("pipeline.news.classifier.classify", return_value=_make_classifier_output("Gotham")), \
         patch("pipeline.news.resolver.resolve_cut", return_value=None), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert data["incidents"] == [], "Unresolved commune name must result in 0 incidents"


def test_key_check_provider_aware(tmp_path, monkeypatch):
    """With NEWS_PROVIDER=minimax and MINIMAX_API_KEY set, orchestrator does not early-exit."""
    monkeypatch.setenv("NEWS_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "mm-fake-key")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         patch("pipeline.news.classifier.classify", return_value=_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    # Pipeline must proceed (not early-exit) when minimax key is present
    assert result == 0
    current_path = tmp_path / "current.json"
    assert current_path.exists(), "current.json must be written when minimax key is present"
