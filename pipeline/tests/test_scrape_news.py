"""
pipeline/tests/test_scrape_news.py

Integration test for pipeline/scrape_news.py orchestrator.

Strategy:
- monkeypatch FEEDS to a single synthetic feed with 3 entries (2 crime, 1 non-crime)
- monkeypatch fetch_feed to return feedparser-compatible objects from fixture XML
- patch build_router_from_env with a FakeRouter returning typed ClassifyResults
  (NEVER a live LLM call - an autouse fixture makes any real completion/preflight raise)
- mock get_centroid() to return a known (lat, lng) for the test CUT
- assert main() returns 0 and current.json validates via IncidentsFile.model_validate
- assert attribution fields (outlet, url, date) are present (NEWS-05)
- assert dedup runs (injecting two near-identical items produces one incident)
- assert missing provider API key returns 0 (graceful exit) without raising
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

# Fixture pub dates must stay inside store.py's 30-day retention window relative
# to the real "today" — hardcoded dates silently expire and drop all incidents.
import datetime as _dt

def _recent_iso(hour: int) -> str:
    d = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=1)
    return d.strftime("%Y-%m-%d") + f"T{hour:02d}:00:00Z"

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
    pub_date=_recent_iso(8),
)

_CRIME_ENTRY_2 = _make_entry(
    title="Carabineros detiene banda narco en Puente Alto",
    link="https://www.biobiochile.cl/noticias/narco-puente-alto.shtml",
    guid="https://www.biobiochile.cl/?p=1002",
    description="La PDI detuvo a cinco imputados acusados de narcotráfico.",
    pub_date=_recent_iso(9),
)

_NON_CRIME_ENTRY = _make_entry(
    title="La Roja golea 3-0 a Paraguay en partido amistoso",
    link="https://www.biobiochile.cl/noticias/la-roja-goleada.shtml",
    guid="https://www.biobiochile.cl/?p=1003",
    description="La selección chilena venció a Paraguay en el estadio Nacional.",
    pub_date=_recent_iso(10),
)

# Duplicate of entry 1 (same URL → dedup by url should collapse)
_CRIME_ENTRY_1_DUP = _make_entry(
    title="Robo con violencia en Santiago deja un herido grave",
    link="https://www.biobiochile.cl/noticias/robo-santiago.shtml",  # same URL
    guid="https://www.biobiochile.cl/?p=1001",
    description="Un hombre resultó herido durante un asalto en plena vía pública.",
    pub_date=_recent_iso(8),
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
# Fake router (Phase 34-02): scrape_news classifies through
# pipeline.news.classifier.build_router_from_env() -> router.classify()
# ---------------------------------------------------------------------------

_EXHAUSTED = object()  # sentinel: router.classify returns None (exhausted / budget)


def _to_result(val):
    from pipeline.news.classifier import ClassifyResult, Outcome
    from pipeline.news.schema import ClassifierOutput

    if val is _EXHAUSTED:
        return None
    if isinstance(val, ClassifyResult):
        return val
    if isinstance(val, ClassifierOutput):
        return ClassifyResult(Outcome.OK, val, "openrouter", "fake/model", served_by="FakeProv")
    if val is None:
        return ClassifyResult(Outcome.NOT_CRIME, None, "openrouter", "fake/model", served_by="FakeProv")
    raise TypeError(f"unsupported fake result {val!r}")


def _api(error: str = "NotFoundError", code: int | None = 404):
    from pipeline.news.classifier import ClassifyResult, Outcome
    return ClassifyResult(Outcome.API_ERROR, None, "openrouter", "fake/model",
                          status_code=code, error=error)


def _parse_err():
    from pipeline.news.classifier import ClassifyResult, Outcome
    return ClassifyResult(Outcome.PARSE_ERROR, None, "openrouter", "fake/model", served_by="FakeProv")


class FakeRouter:
    """Duck-typed ProviderRouter. Never sleeps, never touches the network."""

    def __init__(self, results=None, *, default=None, redispatch=None):
        self.results = list(results) if results is not None else None
        self.default = default
        # {call_number: [results for the last len(list) keys]} — emulates R-04 re-dispatch
        self.redispatch = redispatch or {}
        self.calls: list[tuple[str, str | None]] = []
        self._pending_rd: list = []
        self.failovers = 0
        self.failover_reason = None
        self.backup_exhausted = False
        self.budget_exhausted = False
        self.active = "primary"
        self.preflight_status = "skipped"
        self.any_key_present = True
        self.key_env_names = ["OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"]
        self.primary_label = "openrouter:fake/model"
        self.backup_label = "deepseek:fake-backup"

    def preflight(self):
        from pipeline.news.classifier import PreflightResult
        return PreflightResult("skipped", None)

    def classify(self, title, description, key=None):
        self.calls.append((title, key))
        n = len(self.calls)
        if self.results is not None:
            val = self.results.pop(0) if self.results else self.default
        else:
            val = self.default
        if n in self.redispatch:
            rd = self.redispatch[n]
            keys = [k for _, k in self.calls[-len(rd):]]
            self._pending_rd = [(k, _to_result(v)) for k, v in zip(keys, rd)]
            self.failovers = 1
            self.failover_reason = "breaker"
            self.active = "backup"
        return _to_result(val)

    def pop_redispatched(self):
        out, self._pending_rd = self._pending_rd, []
        return out


def _patch_router(results=None, **kw):
    """Patch build_router_from_env to return a FakeRouter.

    results: a list (consumed per call) or a single value used for every call.
    ClassifierOutput -> OK, None -> NOT_CRIME, ClassifyResult passthrough,
    _EXHAUSTED -> classify() returns None.
    """
    if isinstance(results, list):
        fake = FakeRouter(results, **kw)
    else:
        fake = FakeRouter(None, default=results, **kw)
    return patch("pipeline.news.classifier.build_router_from_env", return_value=fake)


def _read_seen(data_dir) -> dict:
    p = pathlib.Path(data_dir) / "seen.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _rejected_stages(data_dir) -> dict:
    out = {}
    for f in (pathlib.Path(data_dir) / "rejected").glob("*.json"):
        for it in json.loads(f.read_text(encoding="utf-8"))["items"]:
            out[it["url"]] = it["rejection_stage"]
    return out


def _read_pending(data_dir) -> list:
    p = pathlib.Path(data_dir) / "pending.json"
    return json.loads(p.read_text(encoding="utf-8"))["items"] if p.exists() else []


@pytest.fixture(autouse=True)
def _no_live_llm(monkeypatch):
    """A missed retarget must fail loudly instead of calling the network."""
    def _boom(*a, **k):
        raise AssertionError("network call in test")

    monkeypatch.setattr("pipeline.news.classifier.preflight_openrouter", _boom)
    monkeypatch.setattr("pipeline.news.classifier._request_completion", _boom)
    for var in ("NEWS_RUN_SUMMARY_PATH", "GITHUB_OUTPUT", "NEWS_FORCE_BACKUP",
                "NEWS_RUN_BUDGET_S", "NEWS_PROVIDER", "NEWS_MODEL"):
        monkeypatch.delenv(var, raising=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def news_data_dir(tmp_path, monkeypatch):
    """Redirect NEWS_DATA_DIR to a tmp_path and return it."""
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture(autouse=False)
def openrouter_key(monkeypatch):
    """Set a fake OPENROUTER_API_KEY so the key-check passes (default provider)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake-test-key")


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
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    # Patch FEEDS registry to our synthetic single feed
    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed") as mock_fetch, \
         _patch_router([]) as mock_build, \
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
        mock_build.return_value.results = list(side_effects)

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
# Test: missing provider API key returns 0 (graceful exit) without raising
# ---------------------------------------------------------------------------

def test_main_no_api_key_returns_0(tmp_path, monkeypatch):
    """Absent API key must produce return code 0 (graceful exit), not raise.

    The orchestrator degrades gracefully: no key → no data change → exit 0.
    (CLAUDE.md: 'pipeline debe fallar con gracia y alertar')
    """
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
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
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
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
         _patch_router(_make_classifier_output()), \
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
# Test: genuine rejections (NOT_CRIME) are skipped AND marked seen (CR-02)
# ---------------------------------------------------------------------------

def test_genuine_rejections_skipped_and_marked_seen(tmp_path, monkeypatch):
    """NOT_CRIME answers must not appear in output, but ARE marked seen (CR-02) and
    recorded in rejected/ with stage low_confidence - and never queued."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1, _CRIME_ENTRY_2]), \
         _patch_router(None), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert data["incidents"] == [], "All rejected items must produce an empty incidents list"
    seen = _read_seen(tmp_path)
    assert _CRIME_ENTRY_1.link in seen and _CRIME_ENTRY_2.link in seen
    stages = _rejected_stages(tmp_path)
    assert stages == {_CRIME_ENTRY_1.link: "low_confidence", _CRIME_ENTRY_2.link: "low_confidence"}
    assert not (tmp_path / "pending.json").exists()


# ---------------------------------------------------------------------------
# Test: centroid None skips the item
# ---------------------------------------------------------------------------

def test_centroid_none_items_skipped(tmp_path, monkeypatch):
    """Items with unknown centroid must be skipped."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output()), \
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
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        sn.main()

    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    required_fields = {"id", "cut", "lat", "lng", "title_es", "title_en", "date", "outlet", "url", "family"}
    incident = data["incidents"][0]
    missing = required_fields - set(incident.keys())
    assert not missing, f"Incident missing TS interface fields: {missing}"
    # FID-01 36-04: the stored Spanish headline is the outlet's verbatim headline
    assert incident["title_src"] == incident["title_es"] == _CRIME_ENTRY_1.title


# ---------------------------------------------------------------------------
# Test: orchestrator resolves commune_name via resolve_cut (NEWS-03 / Task 2)
# ---------------------------------------------------------------------------

def test_orchestrator_resolves_name(tmp_path, monkeypatch):
    """With a valid commune_name, the built incident has the resolved cut + non-null slug."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
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
         _patch_router(classifier_output), \
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
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output("Gotham")), \
         patch("pipeline.news.resolver.resolve_cut", return_value=None), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    assert result == 0
    data = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert data["incidents"] == [], "Unresolved commune name must result in 0 incidents"


# ---------------------------------------------------------------------------
# Test: inter-feed courtesy delay (SEC-06, F-108/FM-12)
# ---------------------------------------------------------------------------

def test_inter_feed_courtesy_delay(tmp_path, monkeypatch):
    """A 3-entry FEEDS dict must sleep exactly twice, each call with the exact
    REQUEST_DELAY argument (FM-12: an ordered argument-list assertion, not a
    bare call_count -- an unrelated future sleep on an un-mocked path, e.g. a
    tenacity retry, would silently inflate a bare count into an off-by-N
    flake that still nominally "passes").

    FM-12: pipeline.scrape_news does `import time` (the module object), NOT
    `from time import sleep` -- so `pipeline.scrape_news.time` IS the global
    `time` module, the same object, not an isolated namespace. Patching
    `sn.time.sleep` therefore patches the process-global `time.sleep` for
    the duration of this test.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    three_feeds = {
        "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
        "Cooperativa": "https://www.cooperativa.cl/rss",
        "LaTercera": "https://www.latercera.com/rss",
    }

    import pipeline.scrape_news as sn
    from pipeline.news.fulltext import REQUEST_DELAY

    mock_sleep = MagicMock()
    monkeypatch.setattr(sn.time, "sleep", mock_sleep)

    with patch("pipeline.news.feeds.FEEDS", three_feeds), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        result = sn.main()

    assert result == 0
    assert [c.args[0] for c in mock_sleep.call_args_list] == [REQUEST_DELAY] * (len(three_feeds) - 1)


def test_inter_feed_courtesy_delay_never_before_first_feed(tmp_path, monkeypatch):
    """With a 2-entry FEEDS dict, time.sleep must be called exactly ONCE, with
    the exact REQUEST_DELAY argument (LO-01: a single-entry dict can only
    prove the `if i > 0` guard exists once removed entirely, since an
    always-sleep implementation and a never-sleep-before-first-feed
    implementation are indistinguishable on one feed. A 2-feed dict with an
    explicit [REQUEST_DELAY] expectation subsumes both properties -- 'no
    delay before the first feed' AND 'a delay before the second' -- in one
    non-vacuous assertion, matching the archive_r2.py `if i > 0` precedent)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    two_feeds = {
        "BioBioChile": "https://www.biobiochile.cl/static/feed-rss",
        "Cooperativa": "https://www.cooperativa.cl/rss",
    }

    import pipeline.scrape_news as sn
    from pipeline.news.fulltext import REQUEST_DELAY

    mock_sleep = MagicMock()
    monkeypatch.setattr(sn.time, "sleep", mock_sleep)

    with patch("pipeline.news.feeds.FEEDS", two_feeds), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        result = sn.main()

    assert result == 0
    assert [c.args[0] for c in mock_sleep.call_args_list] == [REQUEST_DELAY]


def test_key_check_provider_aware(tmp_path, monkeypatch):
    """With NEWS_PROVIDER=minimax and MINIMAX_API_KEY set, orchestrator does not early-exit."""
    monkeypatch.setenv("NEWS_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "mm-fake-key")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))

    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=[_CRIME_ENTRY_1]), \
         _patch_router(_make_classifier_output()), \
         patch("pipeline.news.resolver.resolve_cut", return_value=(_VALID_CUT, "santiago")), \
         patch("pipeline.news.centroids.get_centroid", return_value=(-33.45, -70.67)):

        import pipeline.scrape_news as sn
        result = sn.main()

    # Pipeline must proceed (not early-exit) when minimax key is present
    assert result == 0
    current_path = tmp_path / "current.json"
    assert current_path.exists(), "current.json must be written when minimax key is present"


def test_key_check_real_router_minimax_key_counts(monkeypatch):
    """The real build_router_from_env sees the minimax key (provider-aware check)."""
    monkeypatch.setenv("NEWS_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "mm-fake-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    from pipeline.news.classifier import build_router_from_env
    r = build_router_from_env()
    assert r.primary.provider == "minimax" and r.any_key_present is True


# ---------------------------------------------------------------------------
# Phase 34-02: typed-outcome loop, retry queue, run summary (NREC-04/05, G-03/G-09)
# ---------------------------------------------------------------------------

def _entries(n: int, prefix: str = "robo") -> list:
    return [
        _make_entry(
            title=f"Robo con violencia número {i} en Santiago ({prefix})",
            link=f"https://www.biobiochile.cl/noticias/{prefix}-{i}.shtml",
            guid=f"https://www.biobiochile.cl/?p={prefix}{i}",
            description="Un hombre resultó herido durante un asalto en plena vía pública.",
            pub_date=_recent_iso(8),
        )
        for i in range(n)
    ]


def _run(tmp_path, monkeypatch, entries, router_cm, resolve=(_VALID_CUT, "santiago"),
         centroid=(-33.45, -70.67)):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))
    resolve_kw = {"side_effect": resolve} if callable(resolve) else {"return_value": resolve}
    with patch("pipeline.news.feeds.FEEDS", _TEST_FEEDS), \
         patch("pipeline.news.feeds.fetch_feed", return_value=list(entries)), \
         router_cm as build, \
         patch("pipeline.news.resolver.resolve_cut", **resolve_kw), \
         patch("pipeline.news.centroids.get_centroid", return_value=centroid):
        import pipeline.scrape_news as sn
        rc = sn.main()
    return rc, build.return_value


def _summary(tmp_path) -> dict:
    return json.loads((tmp_path / "run-summary.json").read_text(encoding="utf-8"))


def test_api_error_404_not_seen_not_rejected_queued(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1, _CRIME_ENTRY_2], _patch_router(_api()))
    assert rc == 0
    seen = _read_seen(tmp_path)
    assert _CRIME_ENTRY_1.link not in seen and _CRIME_ENTRY_2.link not in seen
    assert _rejected_stages(tmp_path) == {}  # in particular no classifier_none
    pend = _read_pending(tmp_path)
    assert {p["url"] for p in pend} == {_CRIME_ENTRY_1.link, _CRIME_ENTRY_2.link}
    assert all(p["attempts"] == 1 and p["last_error"] == "NotFoundError:404" for p in pend)
    s = _summary(tmp_path)
    assert s["api_errors"] == 2 and s["responded"] == 0 and s["attempted"] == 2
    assert s["queued"] == 2


def test_parse_error_marked_seen_and_rejected(tmp_path, monkeypatch):
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_parse_err()))
    assert rc == 0
    assert _CRIME_ENTRY_1.link in _read_seen(tmp_path)
    assert _rejected_stages(tmp_path) == {_CRIME_ENTRY_1.link: "parse_error"}
    assert _read_pending(tmp_path) == []


@pytest.mark.parametrize(
    "commune,resolve,centroid,stage",
    [
        (None, (_VALID_CUT, "santiago"), (-33.45, -70.67), "commune_null"),
        ("Gotham", None, (-33.45, -70.67), "resolver_fail"),
        ("Santiago", (_VALID_CUT, "santiago"), None, "centroid_fail"),
    ],
)
def test_ok_downstream_reject_stages(tmp_path, monkeypatch, commune, resolve, centroid, stage):
    out = _make_classifier_output("Santiago").model_copy(update={"commune_name": commune})
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(out),
                 resolve=resolve, centroid=centroid)
    assert rc == 0
    assert _CRIME_ENTRY_1.link in _read_seen(tmp_path)
    assert _rejected_stages(tmp_path) == {_CRIME_ENTRY_1.link: stage}


def test_queued_item_recovers_on_next_run(tmp_path, monkeypatch):
    rc1, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_api()))
    assert rc1 == 0 and len(_read_pending(tmp_path)) == 1
    # Run 2: the item is no longer in the feed; the router answers OK.
    rc2, fake = _run(tmp_path, monkeypatch, [], _patch_router(_make_classifier_output()))
    assert rc2 == 0
    assert len(fake.calls) == 1
    cur = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert [i["url"] for i in cur["incidents"]] == [_CRIME_ENTRY_1.link]
    assert _read_pending(tmp_path) == []
    assert _CRIME_ENTRY_1.link in _read_seen(tmp_path)


def test_pending_item_also_in_feed_classified_once(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_api()))
    rc, fake = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1, _CRIME_ENTRY_2],
                    _patch_router(_make_classifier_output()))
    assert rc == 0
    titles = [t for t, _ in fake.calls]
    assert len(titles) == 2
    assert titles.count(_CRIME_ENTRY_1.title) == 1


def test_empty_content_and_finish_length_are_queued_not_seen(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1, _CRIME_ENTRY_2],
                 _patch_router([_api("empty_content", None), _api("finish_length", None)]))
    assert rc == 0
    seen = _read_seen(tmp_path)
    assert _CRIME_ENTRY_1.link not in seen and _CRIME_ENTRY_2.link not in seen
    assert _rejected_stages(tmp_path) == {}
    assert {p["last_error"] for p in _read_pending(tmp_path)} == {
        "empty_content:None", "finish_length:None"}
    s = _summary(tmp_path)
    assert s["empty_content"] == 1 and s["finish_length"] == 1 and s["api_errors"] == 2


def test_redispatch_recovers_tripping_streak(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    entries = _entries(5)
    outs = [
        _make_classifier_output().model_copy(update={"title_es": f"Robo distinto {i}"})
        for i in range(5)
    ]
    rc, fake = _run(tmp_path, monkeypatch, entries,
                    _patch_router([_api()] * 5, redispatch={5: outs}))
    assert rc == 0
    assert len(fake.calls) == 5
    assert _read_pending(tmp_path) == []
    assert not (tmp_path / "pending.json").exists()
    seen = _read_seen(tmp_path)
    assert all(e.link in seen for e in entries)
    s = _summary(tmp_path)
    assert s["redispatched"] == 5 and s["recovered_by_redispatch"] == 5
    assert s["api_errors"] == 0 and s["failovers"] == 1 and s["failover_reason"] == "breaker"
    assert s["accepted"] == 5 and s["attempted"] == 5 and s["responded"] == 5


def test_redispatch_backup_also_failing_keeps_single_increment(tmp_path, monkeypatch):
    entries = _entries(5)
    rc, _ = _run(tmp_path, monkeypatch, entries,
                 _patch_router([_api()] * 5, redispatch={5: [_api()] * 5}))
    assert rc == 0
    pend = _read_pending(tmp_path)
    assert len(pend) == 5 and all(p["attempts"] == 1 for p in pend)


def test_run_budget_real_router_queues_rest(tmp_path, monkeypatch):
    """R-11: a REAL ProviderRouter with a fake clock and intermittent 30 s timeouts
    stops at budget_s=1200; the rest is queued without an attempt increment."""
    import httpx
    from openai import APITimeoutError
    from pipeline.news import classifier as C

    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    now = [0.0]
    ncalls = [0]
    ok_body = json.dumps({
        "commune_name": "Santiago", "region_hint": "Metropolitana", "family": "propiedad",
        "title_es": "Robo en Santiago", "title_en": "Robbery in Santiago",
        "summary": "A robbery.", "confidence": 0.9,
    })

    def fake_request(client_, model, provider, user_content, extra_body=None):
        ncalls[0] += 1
        now[0] += 30.0
        if ncalls[0] % 3 == 0:
            raise APITimeoutError(request=httpx.Request("POST", "https://x"))
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=ok_body), finish_reason="stop")],
            model="m", provider="FakeProv", usage=None,
        )

    monkeypatch.setattr(C, "_request_completion", fake_request)
    monkeypatch.setattr(C, "_sleep", lambda s: now.__setitem__(0, now[0] + s))
    spec = C.ProviderSpec("deepseek", "m", lambda: MagicMock(), None, True)
    router = C.ProviderRouter(spec, None, clock=lambda: now[0], budget_s=1200)

    entries = _entries(30)
    rc, _ = _run(tmp_path, monkeypatch, entries,
                 patch("pipeline.news.classifier.build_router_from_env", return_value=router))
    assert rc == 0
    for name in ("current.json", "seen.json", "pending.json"):
        assert (tmp_path / name).exists(), name
    s = _summary(tmp_path)
    assert s["budget_exhausted"] is True
    assert 0 < s["not_attempted"] < 30
    assert s["attempted"] + s["not_attempted"] == 30
    pend = _read_pending(tmp_path)
    assert len(pend) == s["not_attempted"]
    assert all(p["attempts"] == 0 for p in pend)
    assert s["served_by_counts"] == {"FakeProv": s["attempted"]}


def _write_pending(tmp_path, items):
    (tmp_path / "pending.json").write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8")


def _pending_entry(entry, *, attempts, first_queued):
    from pipeline.news.pending import item_id
    return {
        "id": item_id(entry.link), "url": entry.link, "title": entry.title,
        "description": entry.summary, "date": _recent_iso(8)[:10], "outlet": "BioBioChile",
        "first_queued": first_queued, "attempts": attempts, "last_error": "NotFoundError:404",
    }


def _iso_days_ago(days: float) -> str:
    return (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days)).isoformat(timespec="seconds")


def test_attempt_cap_expires_to_rejected_and_seen(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    _write_pending(tmp_path, [_pending_entry(_CRIME_ENTRY_1, attempts=4, first_queued=_iso_days_ago(1))])
    rc, fake = _run(tmp_path, monkeypatch, [], _patch_router(_api()))
    assert rc == 0
    assert len(fake.calls) == 1
    assert _read_pending(tmp_path) == []
    assert _rejected_stages(tmp_path) == {_CRIME_ENTRY_1.link: "api_error_expired"}
    assert _CRIME_ENTRY_1.link in _read_seen(tmp_path)
    assert _summary(tmp_path)["expired"] == 1


def test_age_expiry_before_classification(tmp_path, monkeypatch):
    _write_pending(tmp_path, [_pending_entry(_CRIME_ENTRY_1, attempts=1, first_queued=_iso_days_ago(15))])
    rc, fake = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_make_classifier_output()))
    assert rc == 0
    assert fake.calls == []  # not attempted; the feed copy is now seen
    assert _rejected_stages(tmp_path) == {_CRIME_ENTRY_1.link: "api_error_expired"}
    assert _CRIME_ENTRY_1.link in _read_seen(tmp_path)
    assert _read_pending(tmp_path) == []


def test_router_exhausted_queues_unattempted(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    _write_pending(tmp_path, [_pending_entry(_CRIME_ENTRY_2, attempts=2, first_queued=_iso_days_ago(1))])
    cm = _patch_router(_EXHAUSTED)
    cm_fake = cm.kwargs["return_value"]
    cm_fake.backup_exhausted = True
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], cm)
    assert rc == 0
    pend = {p["url"]: p for p in _read_pending(tmp_path)}
    assert pend[_CRIME_ENTRY_2.link]["attempts"] == 2
    assert pend[_CRIME_ENTRY_1.link]["attempts"] == 0
    assert _CRIME_ENTRY_1.link not in _read_seen(tmp_path)
    s = _summary(tmp_path)
    assert s["not_attempted"] == 2 and s["backup_exhausted"] is True and s["attempted"] == 0


def test_pending_first_and_combined_cap(tmp_path, monkeypatch):
    import pipeline.scrape_news as sn
    monkeypatch.setattr(sn, "MAX_CLASSIFICATIONS_PER_RUN", 3)
    queued = _entries(2, prefix="queued")
    _write_pending(tmp_path, [
        _pending_entry(queued[1], attempts=1, first_queued=_iso_days_ago(1)),
        _pending_entry(queued[0], attempts=1, first_queued=_iso_days_ago(2)),
    ])
    fresh = _entries(3, prefix="fresh")
    rc, fake = _run(tmp_path, monkeypatch, fresh, _patch_router(_make_classifier_output()))
    assert rc == 0
    titles = [t for t, _ in fake.calls]
    assert titles == [queued[0].title, queued[1].title, fresh[0].title]


def test_mixed_run_summary_schema_and_github_output(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "out" / "run-summary.json"))
    gh = tmp_path / "gh_output.txt"
    gh.write_text("existing=1\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh))
    entries = _entries(5)
    results = [
        _make_classifier_output("Santiago"),   # OK → accepted
        None,                                    # NOT_CRIME
        _parse_err(),                            # PARSE_ERROR
        _api(),                                  # API_ERROR
        _make_classifier_output("Gotham"),     # OK → resolver_fail
    ]

    def resolve(name, hint):
        return None if name == "Gotham" else (_VALID_CUT, "santiago")

    with caplog.at_level("INFO"):
        rc, _ = _run(tmp_path, monkeypatch, entries, _patch_router(results), resolve=resolve)
    assert rc == 0
    s = json.loads((tmp_path / "out" / "run-summary.json").read_text(encoding="utf-8"))
    assert set(s) == {
        "schema", "attempted", "responded", "accepted", "genuine_rejects", "parse_errors",
        "api_errors", "failovers", "failover_reason", "backup_exhausted", "queued", "expired",
        "not_attempted", "downstream_rejects", "preflight", "primary", "backup",
        "skipped_reason", "empty_content", "finish_length", "redispatched",
        "recovered_by_redispatch", "budget_exhausted", "served_by_counts",
        "fidelity",  # FID-01 36-04 (dict -> never a GITHUB_OUTPUT line)
    }
    assert s["schema"] == 1
    assert (s["attempted"], s["responded"], s["accepted"], s["genuine_rejects"],
            s["parse_errors"], s["api_errors"], s["downstream_rejects"], s["queued"],
            s["expired"], s["not_attempted"]) == (5, 3, 1, 1, 1, 1, 1, 1, 0, 0)
    assert s["failovers"] == 0 and s["failover_reason"] is None
    assert s["backup_exhausted"] is False and s["budget_exhausted"] is False
    assert s["preflight"] == "skipped" and s["skipped_reason"] is None
    assert s["primary"] == "openrouter:fake/model" and s["backup"] == "deepseek:fake-backup"
    assert s["served_by_counts"] == {"FakeProv": 4}

    lines = gh.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "existing=1"
    for expected in ("attempted=5", "responded=3", "api_errors=1", "backup_exhausted=false",
                     "failover_reason=", "schema=1", "preflight=skipped"):
        assert expected in lines, expected
    assert not any(l.startswith("served_by_counts") for l in lines)
    assert not any(l.startswith("fidelity") for l in lines)  # FID-01 36-04

    assert "Classification summary: classified=1, rejected=3" in caplog.text
    assert '"preflight": "skipped"' in caplog.text  # Run summary log line (sort_keys JSON)


def test_pending_not_rewritten_when_unchanged(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_api()))
    p = tmp_path / "pending.json"
    before_bytes, before_mtime = p.read_bytes(), p.stat().st_mtime_ns
    import time as _time
    _time.sleep(0.05)
    rc, _ = _run(tmp_path, monkeypatch, [], _patch_router(_EXHAUSTED))
    assert rc == 0
    assert p.read_bytes() == before_bytes
    assert p.stat().st_mtime_ns == before_mtime


def test_summary_write_failure_is_loud(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(blocker / "sub" / "run-summary.json"))
    rc, _ = _run(tmp_path, monkeypatch, [_CRIME_ENTRY_1], _patch_router(_make_classifier_output()))
    assert rc == 1


def test_no_api_key_summary_only_when_path_set(tmp_path, monkeypatch):
    for k in ("OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "MINIMAX_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    data_dir = tmp_path / "data"
    monkeypatch.setenv("NEWS_DATA_DIR", str(data_dir))
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    import pipeline.scrape_news as sn
    assert sn.main() == 0
    s = _summary(tmp_path)
    assert s["skipped_reason"] == "no_api_key" and s["attempted"] == 0
    assert not data_dir.exists() or list(data_dir.rglob("*.json")) == []


# ---------------------------------------------------------------------------
# 36-04 (FID-01 / FID-06 / FID-07, G-28, G-29, premortem R-14): verbatim
# headline, guarded title_en, editorial filter, per-row safety in the OK path
# ---------------------------------------------------------------------------

_GNEWS_FEEDS = {"GoogleNewsCalama": "https://news.google.com/rss/search?q=calama"}


def _gnews_entry(title, link, description="Robo con violencia en Calama.", outlet="soychile.cl"):
    e = _make_entry(title=title, link=link, guid=link, description=description,
                    pub_date=_recent_iso(8))
    e.source = {"title": outlet}
    return e


def _run_feeds(tmp_path, monkeypatch, feeds, entries, router_cm, *, patches=()):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NEWS_RUN_SUMMARY_PATH", str(tmp_path / "run-summary.json"))
    from contextlib import ExitStack
    with ExitStack() as stack:
        stack.enter_context(patch("pipeline.news.feeds.FEEDS", feeds))
        stack.enter_context(patch("pipeline.news.feeds.fetch_feed", return_value=list(entries)))
        build = stack.enter_context(router_cm)
        stack.enter_context(patch("pipeline.news.resolver.resolve_cut",
                                  return_value=(_VALID_CUT, "santiago")))
        stack.enter_context(patch("pipeline.news.centroids.get_centroid",
                                  return_value=(-33.45, -70.67)))
        for p in patches:
            stack.enter_context(p)
        import pipeline.scrape_news as sn
        rc = sn.main()
    return rc, build.return_value


def _current(tmp_path) -> list:
    p = tmp_path / "current.json"
    return json.loads(p.read_text(encoding="utf-8"))["incidents"] if p.exists() else []


def _out(title_en: str):
    return _make_classifier_output().model_copy(update={"title_en": title_en})


def test_fid01_gnews_title_src_stored_verbatim(tmp_path, monkeypatch):
    e = _gnews_entry("Detienen a sujeto en Calama - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-calama-1")
    rc, fake = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e],
                          _patch_router(_out("Man arrested in Calama")))
    assert rc == 0
    [inc] = _current(tmp_path)
    assert inc["title_src"] == inc["title_es"] == "Detienen a sujeto en Calama"
    assert inc["title_en"] == "Man arrested in Calama"
    assert inc["outlet"] == "soychile.cl"
    # classify input stays the raw feed title (G-16 / 36-02 format)
    assert fake.calls[0][0] == "Detienen a sujeto en Calama - soychile.cl"
    assert _summary(tmp_path)["fidelity"] == {"title_en_fallbacks": 0, "editorial_filtered": 0}


def test_fid07_kinship_mismatch_falls_back_to_title_src(tmp_path, monkeypatch):
    e = _gnews_entry("Detienen a yerno de Rosamel Fierro por robo - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-yerno-1")
    rc, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e],
                       _patch_router(_out("Grandfather of Rosamel Fierro arrested for robbery")))
    assert rc == 0
    [inc] = _current(tmp_path)
    assert inc["title_src"] == "Detienen a yerno de Rosamel Fierro por robo"
    assert inc["title_en"] == inc["title_src"]
    assert _summary(tmp_path)["fidelity"]["title_en_fallbacks"] == 1


def test_g29_editorial_filter_rejects_forbidden_headline(tmp_path, monkeypatch):
    e = _gnews_entry("Balacera en la comuna más peligrosa de Santiago - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-forbidden-1")
    rc, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e],
                       _patch_router(_out("Shooting in Santiago")))
    assert rc == 0
    assert _current(tmp_path) == []
    assert _rejected_stages(tmp_path) == {e.link: "editorial_filter"}
    assert e.link in _read_seen(tmp_path)
    s = _summary(tmp_path)
    assert s["downstream_rejects"] == 1 and s["accepted"] == 0
    assert s["fidelity"] == {"title_en_fallbacks": 0, "editorial_filtered": 1}


def test_g29_editorial_filter_on_title_en(tmp_path, monkeypatch):
    e = _gnews_entry("Balacera en Santiago - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-forbidden-2")
    rc, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e],
                       _patch_router(_out("Shooting in the most dangerous commune")))
    assert rc == 0 and _current(tmp_path) == []
    assert _rejected_stages(tmp_path) == {e.link: "editorial_filter"}


def test_fid06_classify_receives_entity_free_description(tmp_path, monkeypatch):
    e = _gnews_entry("Detienen a sujeto por homicidio - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-keffe-1",
                     description="Duane &#8220;Keffe D&#8221; Davis&nbsp;fue detenido por homicidio")
    cm = _patch_router(_out("Man arrested for homicide"))
    fake = cm.kwargs["return_value"]
    seen_desc: list[str] = []
    real_classify = fake.classify

    def capture(title, description, key=None):
        seen_desc.append(description)
        return real_classify(title, description, key=key)

    fake.classify = capture
    rc, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e], cm)
    assert rc == 0
    assert len(seen_desc) == 1
    assert "“Keffe D”" in seen_desc[0]
    assert "&#" not in seen_desc[0] and "&nbsp;" not in seen_desc[0]


def test_queued_item_derives_title_src_and_pending_never_stores_it(tmp_path, monkeypatch):
    e = _gnews_entry("Detienen a sujeto en Calama - soychile.cl",
                     "https://news.google.com/rss/articles/CBMi-queued-1")
    rc1, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [e], _patch_router(_api()))
    assert rc1 == 0
    [pend] = _read_pending(tmp_path)
    assert "title_src" not in pend
    assert pend["title"] == "Detienen a sujeto en Calama - soychile.cl"
    rc2, _ = _run_feeds(tmp_path, monkeypatch, _GNEWS_FEEDS, [],
                        _patch_router(_out("Man arrested in Calama")))
    assert rc2 == 0
    [inc] = _current(tmp_path)
    assert inc["title_src"] == inc["title_es"] == "Detienen a sujeto en Calama"


def test_r14_invalid_record_rejected_per_row(tmp_path, monkeypatch):
    long_title = ("Robo con violencia en Santiago " * 20)[:401]
    assert len(long_title) == 401
    bad = _make_entry(title=long_title, link="https://www.biobiochile.cl/noticias/long.shtml",
                      guid="https://www.biobiochile.cl/?p=long",
                      description="Asalto en la vía pública.", pub_date=_recent_iso(8))
    rc, _ = _run_feeds(tmp_path, monkeypatch, _TEST_FEEDS, [bad, _CRIME_ENTRY_2],
                       _patch_router(_make_classifier_output()))
    assert rc == 0
    assert [i["url"] for i in _current(tmp_path)] == [_CRIME_ENTRY_2.link]
    assert _rejected_stages(tmp_path) == {bad.link: "invalid_record"}
    assert bad.link in _read_seen(tmp_path)
    assert _summary(tmp_path)["downstream_rejects"] == 1


def test_r14_build_incident_none_rejected_per_row(tmp_path, monkeypatch):
    rc, _ = _run_feeds(tmp_path, monkeypatch, _TEST_FEEDS, [_CRIME_ENTRY_1],
                       _patch_router(_make_classifier_output()),
                       patches=[patch("pipeline.news.store.build_incident", return_value=None)])
    assert rc == 0
    assert _current(tmp_path) == []
    assert _rejected_stages(tmp_path) == {_CRIME_ENTRY_1.link: "url_rejected"}
    assert _summary(tmp_path)["downstream_rejects"] == 1
