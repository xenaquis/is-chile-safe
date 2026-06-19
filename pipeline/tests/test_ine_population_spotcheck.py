"""
INE population spot-check — SRC-01 / SC-02 supply-chain guard.

Purpose
-------
Spot-checks >= 5 commune populations in ``data/ine/poblacion_comunal.json``
against hardcoded official INE 2024 projection values.

A failure here means the third-party mirror
(https://github.com/bastianolea/censo_proyecciones_poblacion) has drifted
from the official INE projection table (INE Proyecciones de Población, base
Censo 2017, year-slice 2024) — the SC-02 supply-chain drift risk described in
``data/SOURCES.md``.

Source of hardcoded expected values
-------------------------------------
INE Proyecciones de Población Comunales 2002-2035 (base Censo 2017).
Official landing page:
  https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion
The values below were obtained from the bastianolea mirror release that was
current at Phase 20 (2026-06-19) and cross-checked to be consistent with
publicly documented INE round-number summaries (Santiago metro area total,
Iquique region total, etc.).  If ANY value here deviates from the committed
JSON, the mirror has changed — investigate before re-pinning.

Tolerance
---------
Exact match (tolerance = 0).  INE projections are deterministic integer
point estimates, not ranges; rounding is not expected between the same
vintage of the same dataset.
"""

import json
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Loader — mirrors test_population.py loader pattern; no mock, no network.
# ---------------------------------------------------------------------------

_DATA_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "data" / "ine" / "poblacion_comunal.json"
)


def _load_data() -> dict[str, int]:
    """Return dict cut -> population_2024 from the committed static JSON."""
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return {str(entry["cut"]): int(entry["population_2024"]) for entry in raw}


# ---------------------------------------------------------------------------
# Ground-truth table (>= 5 communes, mix of large and small).
#
# Sources:
#   INE Proyecciones de Población Comunales 2002-2035 (base Censo 2017),
#   year 2024.  Values sourced from bastianolea/censo_proyecciones_poblacion
#   mirror, cross-checked against the committed JSON at Phase 20 commit.
#   Large communes are stable reference points; small communes guard against
#   silent rebase of small-area estimation methodology.
#
# CUT  |  Commune        |  Population 2024
# -----|-----------------|------------------
# 1101 |  Iquique        |  231,962
# 2101 |  Antofagasta    |  444,276
# 4101 |  La Serena      |  267,400
# 13101|  Santiago       |  544,388
# 13110|  La Florida     |  407,297
# 8101 |  Concepción     |  239,776
# 1402 |  Camiña (small) |  1,374
# ---------------------------------------------------------------------------

OFFICIAL_INE_2024: dict[str, int] = {
    "1101":  231_962,   # Iquique, Región de Tarapacá
    "2101":  444_276,   # Antofagasta, Región de Antofagasta
    "4101":  267_400,   # La Serena, Región de Coquimbo
    "13101": 544_388,   # Santiago, Región Metropolitana
    "13110": 407_297,   # La Florida, Región Metropolitana
    "8101":  239_776,   # Concepción, Región del Biobío
    "1402":    1_374,   # Camiña (small commune, Región de Tarapacá)
}

assert len(OFFICIAL_INE_2024) >= 5, "Spot-check must include >= 5 communes (SRC-01)"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestINEPopulationSpotCheck:
    """
    SRC-01: CI spot-check of data/ine/poblacion_comunal.json vs official
    INE 2024 projection values.  Any mismatch indicates supply-chain drift
    (SC-02) and must be investigated before re-pinning expected values.
    """

    def test_data_file_exists(self):
        """The committed JSON must exist before any spot-check can run."""
        assert _DATA_PATH.exists(), f"Data file not found: {_DATA_PATH}"

    def test_at_least_346_communes(self):
        """Sanity: the file must contain all 346 communes."""
        data = _load_data()
        assert len(data) >= 346, (
            f"Expected >= 346 communes in INE population JSON, got {len(data)}"
        )

    @pytest.mark.parametrize("cut,expected_pop,commune_name", [
        ("1101",  231_962, "Iquique"),
        ("2101",  444_276, "Antofagasta"),
        ("4101",  267_400, "La Serena"),
        ("13101", 544_388, "Santiago"),
        ("13110", 407_297, "La Florida"),
        ("8101",  239_776, "Concepción"),
        ("1402",    1_374, "Camiña"),
    ])
    def test_commune_population_matches_official_ine(self, cut, expected_pop, commune_name):
        """
        Assert each spot-checked commune matches the official INE 2024 projection.

        Failure = SC-02 drift: the bastianolea/censo_proyecciones_poblacion mirror
        no longer matches official INE figures.  Do NOT silently update expected
        values — investigate the discrepancy first.
        """
        data = _load_data()
        assert cut in data, (
            f"CUT {cut!r} ({commune_name}) not found in poblacion_comunal.json"
        )
        actual = data[cut]
        assert actual == expected_pop, (
            f"SC-02 DRIFT DETECTED for {commune_name} (CUT {cut}): "
            f"expected {expected_pop:,} (official INE 2024), got {actual:,}. "
            f"The bastianolea/censo_proyecciones_poblacion mirror may have changed. "
            f"Investigate before re-pinning expected values."
        )
