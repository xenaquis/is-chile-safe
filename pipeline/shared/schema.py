"""
pipeline/shared/schema.py

Pydantic v2 data contracts for the Chile Safety Map pipeline.
All downstream plans import from this module — field names are canonical.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

PLAUSIBILITY_MAX_RATE: float = 100000  # Raised from 20000 after first real run confirmed
# micro-communes (Sierra Gorda pop ~2k, Juan Fernandez pop ~900) reach 43k per-100k due to
# transient populations not reflected in INE estimates; 100k is >2x the observed max of 43,369
# and still catches decimal-parse corruption which produces values in the millions.

FAMILY_KEYS: list[str] = [
    "vida",
    "robos_violentos",
    "vif",
    "drogas",
    "armas",
    "propiedad",
    "incivilidades",
]

FEATURED_FAMILIES: set[str] = {"propiedad", "vida"}  # D-06


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class YearRecord(BaseModel):
    year: int
    rate_per_100k: float
    by_family: dict[str, float | None]  # keys match FAMILY_KEYS values
    partial: bool = False  # True if scrape date is before Dec 31 of that year


# ---------------------------------------------------------------------------
# Commune-level model
# ---------------------------------------------------------------------------


class ComunaRecord(BaseModel):
    id: str  # CUT code e.g. "13101" (D-17)
    name: str
    slug: str  # e.g. "santiago"
    region_id: str  # e.g. "13"
    population: int
    low_population: bool  # True if population < 10,000 (D-12)
    national_rank: int | None  # null if low_population (D-12)
    regional_rank: int | None
    trend: Literal["up", "down", "stable"]  # D-13
    featured_rates: dict  # homicides, kidnappings, property rates by year
    series: list[YearRecord]
    last_updated: str  # ISO date

    @field_validator("id")
    @classmethod
    def id_must_be_cut(cls, v: str) -> str:
        if not (v.isdigit() and 4 <= len(v) <= 5):
            raise ValueError(f"Invalid CUT code: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Region and National models
# ---------------------------------------------------------------------------


class RegionRecord(BaseModel):
    id: str  # region code e.g. "13"
    name: str
    slug: str
    series: list[YearRecord]
    comuna_ranking: list[dict]
    last_updated: str  # ISO date


class NationalRecord(BaseModel):
    name: str
    series: list[YearRecord]
    last_updated: str  # ISO date


# ---------------------------------------------------------------------------
# Map payload models
# ---------------------------------------------------------------------------


class MapPayloadEntry(BaseModel):
    id: str  # CUT code
    rate: float  # total rate_per_100k for the reference year
    level: int  # 1–5 quintile (1=lowest, 5=highest) — matches prototype data.js field
    by_family: list[float | None]  # 7 family rates ordered per FAMILY_KEYS (compact list for <30KB, D-09)
    homicide_rate: int | None = None  # homicide rate per 100k (subgroup 101, rounded int) — Phase 14
    homicide_count: int | None = None  # absolute homicide count (subgroup 101) — Phase 14

    @field_validator("level")
    @classmethod
    def level_must_be_1_to_5(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError(f"level must be 1–5, got {v}")
        return v


class MapPayload(BaseModel):
    generated: str  # ISO datetime
    year: int
    comunas: list[MapPayloadEntry]


# ---------------------------------------------------------------------------
# Meta index model
# ---------------------------------------------------------------------------


class MetaIndexEntry(BaseModel):
    cut: str
    name: str
    slug: str
    region_id: str
    population: int
    low_population: bool


# ---------------------------------------------------------------------------
# All-or-nothing validation gate (D-14, D-16)
# ---------------------------------------------------------------------------


def validate_all_communes(all_communes: list[dict]) -> list[ComunaRecord]:
    """
    Validate all commune records. Raise on ANY error — do not write partial output (D-14).

    Raises:
        ValueError: if commune count != 346, or any rate is outside [0, PLAUSIBILITY_MAX_RATE].
        pydantic.ValidationError: if any record fails structural validation.
    """
    n = len(all_communes)
    if n != 346:
        raise ValueError(f"Expected 346 communes, got {n}")

    records = [ComunaRecord.model_validate(c) for c in all_communes]

    # Plausibility range check (D-16) — first run uses broad absolute limits
    for r in records:
        for yr in r.series:
            if yr.rate_per_100k < 0:
                raise ValueError(f"Negative rate for {r.id} in {yr.year}")
            if yr.rate_per_100k > PLAUSIBILITY_MAX_RATE:
                raise ValueError(
                    f"Implausible rate {yr.rate_per_100k} for {r.id} in {yr.year}"
                )

    return records
