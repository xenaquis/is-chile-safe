"""
pipeline/news/resolver.py

Deterministic name→(cut, slug) lookup built from data/cead/meta/index.json.
Mirrors the accent-strip normalization used in site/src/pages/communes/index.astro:
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

Anti-hallucination: resolve_cut returns None for any name not in the closed 346-commune
set. LLM-emitted commune names MUST pass through this function before any CUT reaches
the incident store. No network calls; no LLM; pure dict lookup.
"""
from __future__ import annotations

import json
import pathlib
import unicodedata

# ---------------------------------------------------------------------------
# Load index.json once at import time
# ---------------------------------------------------------------------------

_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
if not _INDEX_FILE.exists():
    raise FileNotFoundError(
        f"index.json not found at {_INDEX_FILE}. "
        "data/cead/meta/index.json is required for deterministic name→CUT resolution."
    )

_INDEX: list[dict] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Normalization helper (accent-insensitive, case-insensitive)
# ---------------------------------------------------------------------------


def _norm(s: str) -> str:
    """Strip combining diacritics and lowercase — mirrors the Astro frontend NFD pattern."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


# ---------------------------------------------------------------------------
# Module-level lookup tables (built once)
# ---------------------------------------------------------------------------

# Maps normalized_name → list of entries (list handles theoretical duplicates safely)
_NAME_TO_ENTRIES: dict[str, list[dict]] = {}
_CUT_TO_SLUG: dict[str, str] = {}

for _entry in _INDEX:
    _key = _norm(_entry["name"])
    _NAME_TO_ENTRIES.setdefault(_key, []).append(_entry)
    _CUT_TO_SLUG[_entry["cut"]] = _entry["slug"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_cut(
    name: str | None,
    region_hint: str | None = None,
) -> tuple[str, str] | None:
    """Resolve a commune name to (cut, slug) from the closed 346-commune index.

    Parameters
    ----------
    name:
        Commune name as emitted by the classifier (Spanish, possibly with or without
        accent marks). Case-insensitive and accent-insensitive.
    region_hint:
        Optional region name or region_id hint from the classifier. Only consulted
        when the normalized name maps to multiple entries (rare/impossible in current
        346-commune set, but supported for API stability).

    Returns
    -------
    (cut, slug) tuple on match, or None when:
    - name is None or empty
    - name is not found in the 346-commune index (unknown/hallucinated name)
    """
    if not name:
        return None

    key = _norm(name)
    entries = _NAME_TO_ENTRIES.get(key)
    if not entries:
        return None

    if len(entries) == 1:
        entry = entries[0]
        return (entry["cut"], entry["slug"])

    # Disambiguation: multiple entries share the same normalized name.
    # Try to match region_hint against region_id or (normalized) region name.
    if region_hint is not None:
        hint_norm = _norm(str(region_hint))
        for entry in entries:
            if _norm(str(entry.get("region_id", ""))) == hint_norm:
                return (entry["cut"], entry["slug"])
        # Try partial match on hint in entry region_id string
        for entry in entries:
            if hint_norm in _norm(str(entry.get("region_id", ""))):
                return (entry["cut"], entry["slug"])

    # Disambiguation failed — returning a guess would assign the wrong commune.
    # Return None so the orchestrator drops the incident (anti-hallucination contract).
    import logging as _logging
    _logging.getLogger(__name__).debug(
        "Ambiguous commune name %r matched %d entries; region_hint=%r did not resolve — dropping",
        name, len(entries), region_hint,
    )
    return None


def slug_for_cut(cut: str) -> str | None:
    """Return the slug for a given CUT code, or None if the CUT is not in the index."""
    return _CUT_TO_SLUG.get(cut)
