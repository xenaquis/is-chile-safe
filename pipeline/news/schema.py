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

VALID_FAMILIES: set[str] = set(FAMILY_KEYS)

_CUT_FILE = pathlib.Path(__file__).parents[2] / "data" / "incidents" / "cut_list.json"
if not _CUT_FILE.exists():
    # CR-03: fail loud. An empty VALID_CUTS would silently reject EVERY incident
    # (any code `not in set()` is True) — indistinguishable from "no crime news".
    raise FileNotFoundError(
        f"cut_list.json not found at {_CUT_FILE}. The 346-commune CUT list is required "
        "for classification; refusing to run with an empty allow-list."
    )
VALID_CUTS: set[str] = set(json.loads(_CUT_FILE.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class IncidentRecord(BaseModel):
    """Single incident — serializes to the Incident TS interface (D-15)."""

    id: str          # sha256(url)[:16]
    cut: str         # validated against VALID_CUTS
    lat: float
    lng: float
    title_es: str    # plain text only — IncidentPinLayer escapes on render (V5)
    title_en: str    # plain text only
    date: str        # YYYY-MM-DD
    outlet: str      # non-empty (NEWS-05 attribution)
    url: str         # non-empty (NEWS-05 attribution)
    family: str      # validated against VALID_FAMILIES
    slug: str | None = None  # resolved commune slug (NEWS-03); optional for back-compat

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


class ClassifierOutput(BaseModel):
    """Raw response shape from DeepSeek classifier (D-06).

    commune_cut has been replaced by commune_name + region_hint (NEWS-01 redesign).
    The LLM emits a Spanish commune name; deterministic resolution to CUT happens in
    pipeline/news/resolver.py. This prevents hallucinated CUT codes from reaching the store.
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
    title_es: str    # plain text
    title_en: str    # plain text
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


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------


def validate_incidents_file(data: dict) -> IncidentsFile:
    """Validate all-or-nothing. Raises ValidationError on any field failure (D-15)."""
    return IncidentsFile.model_validate(data)
