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
VALID_CUTS: set[str] = set(json.loads(_CUT_FILE.read_text(encoding="utf-8")) if _CUT_FILE.exists() else [])


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
        return v


class ClassifierOutput(BaseModel):
    """Raw response shape from DeepSeek classifier (D-06)."""

    commune_cut: str | None
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
