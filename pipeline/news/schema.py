"""
pipeline/news/schema.py

Pydantic v2 data contracts for the RSS news pipeline output.
Field names match IncidentPinLayer.ts Incident/IncidentsFile exactly (D-15).
"""
from __future__ import annotations

import json
import pathlib

from pydantic import BaseModel, field_validator

from pipeline.shared.schema import FAMILY_KEYS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# NEWS-ONLY extension: "sexuales" is not a CEAD quantitative family (no scraped rate).
# It exists only for news incident classification — keep pipeline/shared/schema.py untouched.
VALID_FAMILIES: set[str] = set(FAMILY_KEYS) | {"sexuales"}

# WR-02: derive VALID_CUTS from the same index.json that resolver.py uses so the
# validator and resolver are always aligned.  Using a separate cut_list.json created
# a dual source of truth: a CUT resolved by resolver.py could fail schema validation
# if cut_list.json was stale.  index.json is the single authoritative source.
_INDEX_FILE = pathlib.Path(__file__).parents[2] / "data" / "cead" / "meta" / "index.json"
if not _INDEX_FILE.exists():
    # Fail loud: an empty VALID_CUTS would silently reject EVERY incident
    # (any code `not in set()` is True) — indistinguishable from "no crime news".
    raise FileNotFoundError(
        f"index.json not found at {_INDEX_FILE}. "
        "data/cead/meta/index.json is required for CUT validation; "
        "refusing to run with an empty allow-list."
    )
VALID_CUTS: set[str] = {
    entry["cut"]
    for entry in json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class IncidentRecord(BaseModel):
    """Single incident — serializes to the Incident TS interface (D-15)."""

    id: str          # sha256(url)[:16]
    cut: str         # validated against VALID_CUTS
    lat: float
    lng: float
    # plain text only — IncidentPinLayer escapes on render (V5).
    # Rows with title_src: title_es mirrors title_src verbatim (G-28, FID-01).
    # Legacy rows (no title_src): the Granite/DeepSeek-era LLM headline.
    title_es: str
    title_en: str    # plain text only
    date: str        # YYYY-MM-DD
    outlet: str      # non-empty (NEWS-05 attribution)
    url: str         # non-empty (NEWS-05 attribution)
    family: str      # validated against VALID_FAMILIES
    slug: str | None = None  # resolved commune slug (NEWS-03); optional for back-compat
    # FID-01 (G-28): the outlet's verbatim headline (entity-decoded, one trailing
    # " - <outlet>" removed). Optional so legacy rows keep validating (Pitfall 1).
    title_src: str | None = None
    # FID-04: the Google News link when `url` is the decoded publisher URL. Optional.
    via_url: str | None = None

    @field_validator("cut")
    @classmethod
    def cut_must_be_valid(cls, v: str) -> str:
        if v not in VALID_CUTS:
            raise ValueError(f"CUT {v!r} not in 346-commune list")
        return v

    @field_validator("family")
    @classmethod
    def family_must_be_valid(cls, v: str) -> str:
        if v not in VALID_FAMILIES:
            raise ValueError(f"Invalid family: {v!r}")
        return v

    @field_validator("outlet")
    @classmethod
    def outlet_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("outlet must not be empty (NEWS-05)")
        return v

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty (NEWS-05)")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"url must be http/https scheme, got: {v!r} (NEWS-05)")
        return v

    @field_validator("title_src")
    @classmethod
    def title_src_must_be_nonblank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("title_src must not be blank when present (FID-01)")
        if len(v) > 400:
            raise ValueError(f"title_src too long ({len(v)} > 400 chars) (FID-01)")
        return v

    @field_validator("via_url")
    @classmethod
    def via_url_must_be_http(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"via_url must be http/https scheme, got: {v!r} (FID-04)")
        return v


class ClassifierOutput(BaseModel):
    """Raw response shape from DeepSeek classifier (D-06).

    commune_cut has been replaced by commune_name + region_hint (NEWS-01 redesign).
    The LLM emits a Spanish commune name; deterministic resolution to CUT happens in
    pipeline/news/resolver.py. This prevents hallucinated CUT codes from reaching the store.

    FID-01 (36-06, G-28): there is no title_es field. The LLM no longer authors a
    Spanish headline; the stored title_es mirrors the outlet headline (title_src).
    title_en is a faithful translation of the given HEADLINE. Extra keys (e.g. a
    stray "title_es" in G-18 cache lines) are ignored by Pydantic's default config.
    """

    commune_name: str | None
    region_hint: str | None = None

    @field_validator("region_hint", mode="before")
    @classmethod
    def coerce_region_hint_to_str(cls, v: object) -> str | None:
        """LLM may emit region_hint as an integer (e.g. 6); coerce to string."""
        if v is None:
            return None
        return str(v)
    family: str
    title_en: str    # plain text: faithful translation of the source HEADLINE (FID-01)
    summary: str     # plain text
    confidence: float

    @field_validator("family")
    @classmethod
    def family_must_be_valid(cls, v: str) -> str:
        if v not in VALID_FAMILIES:
            raise ValueError(f"Invalid family: {v!r}")
        return v


class IncidentsFile(BaseModel):
    """Top-level output file — serializes to the IncidentsFile TS interface (D-15)."""

    generated: str        # ISO-8601 timestamp
    window_days: int      # = 30
    incidents: list[IncidentRecord]
    last_new_incident_at: str | None = None  # G-05 freshness evidence (NEWS-08)


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------


def validate_incidents_file(data: dict) -> IncidentsFile:
    """Validate all-or-nothing. Raises ValidationError on any field failure (D-15)."""
    return IncidentsFile.model_validate(data)
