"""
pipeline/composite_config.py

Module-level constants for the composite crime-exposure index.
All downstream modules import from here — weights and thresholds are canonical.

C-01: Exactly 7 metrics; incivilidades EXCLUDED (not a crime exposure signal).
      spd_homicide_rate = M1 (homicide is M1, NOT M5 — any older 'M5 homicide' phrasing is stale).
C-02: Weight vector is LOCKED (sum = 1.00) — copy verbatim; do not adjust without planning.
D-04: SII cap threshold = 5.0 (sii_workers / ine_population > 5.0 -> INE fallback).
D-10: REFERENCE_YEAR = 2024 (latest year where SPD VHC + CEAD + SII are all final).
"""

# D-10: index anchors to 2024 — the latest year where all three sources are final
REFERENCE_YEAR: int = 2024

# D-01: winsorize top+bottom 1% before min-max to [0, 100]
WINSORIZE_LIMITS: tuple[float, float] = (0.01, 0.01)

# D-04: SII workers / INE population ratio cap (only Providencia CUT 13123 = 5.19 exceeds this)
SII_CAP_RATIO: float = 5.0

# Total communes in Chile (used for rank display)
TOTAL_COMMUNES: int = 346

# C-02 LOCKED weight vector — sum = 1.00
# C-01: incivilidades is EXCLUDED; spd_homicide_rate is M1 (not M5)
METRIC_WEIGHTS: dict[str, float] = {
    "spd_homicide_rate":   0.30,   # M1 — SPD VHC homicide rate (primary severity anchor)
    "cead_robos_rate":     0.20,   # M2 — CEAD violent robbery (robos_violentos)
    "cead_vida_rate":      0.15,   # M3 — CEAD vida crimes (excluding homicide)
    "cead_propiedad_rate": 0.12,   # M4 — CEAD property crimes
    "cead_vif_rate":       0.10,   # M5 — CEAD domestic violence (VIF)
    "cead_drogas_rate":    0.08,   # M6 — CEAD drug crimes (Ley 20.000)
    "cead_armas_rate":     0.05,   # M7 — CEAD weapons crimes
}
