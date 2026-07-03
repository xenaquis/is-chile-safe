"""
pipeline/tests/test_feeds.py

Tests for pipeline/news/feeds.py — RSS fetch, keyword pre-filter, seen-ledger.
"""
from __future__ import annotations

import pytest
import feedparser
from pathlib import Path

from pipeline.news.feeds import (  # type: ignore
    fetch_feed,
    is_crime_item,
    filter_seen,
    canonical_url,
    resolve_outlet,
    google_news_url,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def googlenews_xml():
    p = FIXTURES_DIR / "feed_googlenews_sample.xml"
    if not p.exists():
        pytest.skip("feed_googlenews_sample.xml not present")
    return p.read_text(encoding="utf-8")


@pytest.fixture
def biobio_xml():
    p = FIXTURES_DIR / "feed_biobio_sample.xml"
    if not p.exists():
        pytest.skip("feed_biobio_sample.xml not present")
    return p.read_text(encoding="utf-8")


@pytest.fixture
def cooperativa_xml():
    p = FIXTURES_DIR / "feed_cooperativa_sample.xml"
    if not p.exists():
        pytest.skip("feed_cooperativa_sample.xml not present")
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test functions (exact names per 05-VALIDATION.md)
# ---------------------------------------------------------------------------


def test_keyword_filter_crime_passes():
    """An item with crime keywords in title must pass is_crime_item."""
    item = {
        "title": "Robo con violencia en Santiago deja un herido grave",
        "description": "Un hombre resultó herido durante un asalto.",
    }
    assert is_crime_item(item) is True


def test_keyword_filter_noncrime_skipped():
    """An item with no crime keywords must be rejected by is_crime_item."""
    item = {
        "title": "La Roja golea 3-0 a Paraguay en partido amistoso",
        "description": "La selección chilena venció a Paraguay.",
    }
    assert is_crime_item(item) is False


def test_seen_ledger_known_url_skipped():
    """An item whose URL is already in the seen ledger must be filtered out."""
    known_url = "https://www.biobiochile.cl/noticias/already-seen.shtml"
    item = {"link": known_url, "title": "Robo en Santiago"}
    seen: set[str] = {known_url}
    result = filter_seen([item], seen)
    assert len(result) == 0


def test_fetch_feed_failure_returns_empty():
    """A feed URL that is unreachable must return [] without raising."""
    result = fetch_feed("test_feed", "http://localhost:19999/nonexistent.xml")
    assert result == []


def test_biobio_uses_link_not_guid(biobio_xml):
    """BioBio feed uses <link> as canonical URL, not <guid> (Pitfall 2).

    Verifies that the parser extracts the <link> element (article URL)
    rather than the WordPress <guid> (?p= form) for dedup ledger keying.
    """
    import feedparser
    feed = feedparser.parse(biobio_xml)
    entry = feed.entries[0]
    # <link> should be the article URL; <id> (guid) should be the ?p= form
    assert entry.link != entry.id, (
        f"BioBio link and id should differ: link={entry.link!r}, id={entry.id!r}"
    )
    assert "?p=" in entry.id, f"Expected WordPress ?p= guid, got: {entry.id!r}"


# ---------------------------------------------------------------------------
# Google News tests
# ---------------------------------------------------------------------------


def test_googlenews_outlet_from_source(googlenews_xml):
    """resolve_outlet extracts the <source> outlet name for Google News entries."""
    feed = feedparser.parse(googlenews_xml)
    # First entry has <source>Puranoticia</source>
    entry = feed.entries[0]
    assert resolve_outlet(entry, "GoogleNews-Nacional") == "Puranoticia"


def test_googlenews_outlet_fallback(googlenews_xml):
    """resolve_outlet falls back to 'Google News' when no <source> tag present."""
    feed = feedparser.parse(googlenews_xml)
    # Last entry has no <source> tag
    no_source_entry = feed.entries[-1]
    assert resolve_outlet(no_source_entry, "GoogleNews-Nacional") == "Google News"


def test_googlenews_canonical_url_is_link(googlenews_xml):
    """canonical_url for Google News returns the redirect link, not the guid."""
    feed = feedparser.parse(googlenews_xml)
    entry = feed.entries[0]
    url = canonical_url(entry, "GoogleNews-Nacional")
    assert url == entry.link
    assert url.startswith("https://news.google.com/rss/")


def test_non_google_outlet_passthrough(googlenews_xml):
    """resolve_outlet returns the feed_name unchanged for non-Google feeds."""
    feed = feedparser.parse(googlenews_xml)
    entry = feed.entries[0]
    assert resolve_outlet(entry, "LaCuarta") == "LaCuarta"
    assert resolve_outlet(entry, "BioBioChile") == "BioBioChile"


def test_google_news_url_format():
    """google_news_url produces a correctly encoded Google News RSS URL."""
    url = google_news_url("homicidio chile when:2d")
    assert url.startswith("https://news.google.com/rss/search?q=")
    assert "&hl=es-419&gl=CL&ceid=CL:es-419" in url
    # query must be percent-encoded (spaces -> %20)
    assert "homicidio%20chile%20when%3A2d" in url or "homicidio+chile" in url or "homicidio%20chile" in url


def test_feeds_contains_lacuarta_and_googlenews():
    """FEEDS registry contains LaCuarta + 5 Google News keys."""
    from pipeline.news.feeds import FEEDS  # type: ignore
    assert "LaCuarta" in FEEDS
    gn_keys = [k for k in FEEDS if k.startswith("GoogleNews-")]
    assert len(gn_keys) == 5
    for url in FEEDS.values():
        assert isinstance(url, str) and url.startswith("https://"), f"Bad URL: {url}"
