"""
pipeline/tests/test_resolver.py

RED tests for pipeline/news/resolver.py — deterministic name→(cut, slug) lookup.
All expected CUTs are derived at test time from data/cead/meta/index.json to avoid
hardcoded codes that could drift.

Behaviors tested:
  - exact match
  - accent-insensitive match
  - unknown name → None
  - None input → None
  - case-insensitive match
  - slug_for_cut: known CUT → slug; unknown CUT → None
  - region_hint unused when name is unique
"""
from __future__ import annotations

import json
import pathlib

import pytest

from pipeline.news.resolver import resolve_cut, slug_for_cut

# ---------------------------------------------------------------------------
# Load index.json for expected values (avoids hardcoding CUT codes)
# ---------------------------------------------------------------------------

_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
_INDEX: list[dict] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
_BY_NAME: dict[str, dict] = {e["name"]: e for e in _INDEX}
_BY_CUT: dict[str, dict] = {e["cut"]: e for e in _INDEX}


def _entry(name: str) -> dict:
    """Return the index entry for an exact Spanish name (test helper)."""
    entry = _BY_NAME.get(name)
    assert entry is not None, f"Test setup error: {name!r} not found in index.json"
    return entry


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_exact_match():
    """resolve_cut with exact Spanish name returns correct (cut, slug)."""
    e = _entry("Las Condes")
    result = resolve_cut("Las Condes")
    assert result is not None
    cut, slug = result
    assert cut == e["cut"]
    assert slug == e["slug"]


def test_accent_insensitive():
    """resolve_cut without accent equals resolve_cut with accent (Cochamó / Cochamo)."""
    e = _entry("Cochamó")
    result_with = resolve_cut("Cochamó")
    result_without = resolve_cut("Cochamo")
    assert result_with is not None
    assert result_without is not None
    assert result_with == result_without
    cut, slug = result_without
    assert cut == e["cut"]
    assert slug == e["slug"]


def test_unknown_name_returns_none():
    """resolve_cut with an invented/unknown name returns None."""
    assert resolve_cut("Gotham") is None


def test_none_input_returns_none():
    """resolve_cut(None) returns None without raising."""
    assert resolve_cut(None) is None


def test_case_insensitive():
    """resolve_cut is case-insensitive: 'las condes' == 'Las Condes'."""
    result_lower = resolve_cut("las condes")
    result_title = resolve_cut("Las Condes")
    assert result_lower is not None
    assert result_lower == result_title


def test_slug_for_cut():
    """slug_for_cut returns correct slug for a valid CUT; None for unknown."""
    # Pick a known entry
    e = _INDEX[0]
    assert slug_for_cut(e["cut"]) == e["slug"]
    assert slug_for_cut("99999") is None


def test_region_hint_unused_when_unique():
    """A unique name resolves correctly regardless of region_hint value."""
    e = _entry("Las Condes")
    # Even with a nonsense region_hint, unique names resolve normally
    result = resolve_cut("Las Condes", region_hint="banana")
    assert result is not None
    cut, slug = result
    assert cut == e["cut"]
    assert slug == e["slug"]


def test_ambiguous_name_without_hint_returns_none():
    """CR-02: when a normalized name maps to multiple entries and region_hint does
    not resolve the collision, resolve_cut must return None (not the first entry).
    We simulate a collision by injecting a duplicate into the lookup table."""
    import pipeline.news.resolver as resolver_mod

    e = _entry("Las Condes")
    fake_entry = {"cut": "99001", "slug": "fake-las-condes", "region_id": "99", "name": "Las Condes"}
    original = resolver_mod._NAME_TO_ENTRIES.copy()
    try:
        resolver_mod._NAME_TO_ENTRIES["las condes"] = [e, fake_entry]
        # No region_hint — disambiguation fails
        result = resolve_cut("Las Condes")
        assert result is None, "Expected None when disambiguation fails (CR-02)"
    finally:
        resolver_mod._NAME_TO_ENTRIES.clear()
        resolver_mod._NAME_TO_ENTRIES.update(original)


def test_ambiguous_name_with_correct_hint_resolves():
    """CR-02: when region_hint matches one of the colliding entries, that entry is returned."""
    import pipeline.news.resolver as resolver_mod

    e = _entry("Las Condes")
    fake_entry = {"cut": "99001", "slug": "fake-las-condes", "region_id": "99", "name": "Las Condes"}
    original = resolver_mod._NAME_TO_ENTRIES.copy()
    try:
        resolver_mod._NAME_TO_ENTRIES["las condes"] = [e, fake_entry]
        # region_hint matches real entry's region_id
        result = resolve_cut("Las Condes", region_hint=str(e["region_id"]))
        assert result is not None
        assert result[0] == e["cut"]
    finally:
        resolver_mod._NAME_TO_ENTRIES.clear()
        resolver_mod._NAME_TO_ENTRIES.update(original)
