"""
pipeline/tests/test_feeds.py

Tests for pipeline/news/feeds.py — RSS fetch, keyword pre-filter, seen-ledger.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from pipeline.news.feeds import fetch_feed, is_crime_item, filter_seen  # type: ignore

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
