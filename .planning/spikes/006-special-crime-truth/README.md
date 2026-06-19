---
spike: 006
name: special-crime-truth
type: standard
validates: "Given validated/special-crime sources, when checked, then which beat CEAD as the truth-source for a specific crime type at comuna level"
verdict: PARTIAL (homicide already integrated; femicide/juvenile not comuna-viable)
related: [004-enusc-victimization, 005-justice-funnel]
tags: [observatorio-homicidios, spd-vhc, femicidio, sernameg, reinsercion-juvenil, seed-002]
---

# Spike 006: Special-Crime Truth Sources

## What This Validates
Given sources that are *preferred truth* for a specific crime type (homicide, femicide, juvenile), when checked, then which should override CEAD for that type — and is any usable at comuna level?

## Research

| Source | Product | Comuna-level? | Anti-infra-rep value | Status |
|--------|---------|---------------|----------------------|--------|
| **Observatorio de Homicidios / Centro Prevención de Homicidios (SPD)** | "Informe Nacional de Víctimas de Homicidios Consumados 2024" — interinstitutionally validated (SPD+Carabineros+PDI+Fiscalía+SML) | **Yes** (homicide at comuna via SPD VHC) | HIGH — homicide truth-source | **ALREADY INTEGRATED** as SPD VHC = M1 of the Phase-18 index |
| **SernamEG / Circuito Intersectorial de Femicidio (CIF)** | Annual femicide report; region + rate/100k by region | Region (some comuna in reports, but **counts tiny**: ~43 consummated/yr nationally) | MED (gendered lethal violence) | ✗ comuna — sub-comuna noise; national/regional context only |
| **Servicio Nac. de Reinserción Social Juvenil** | Semestral statistical reports (PDF), by zone/region; new service (Law 21.527, 2024), gradual rollout | **No** (zone/region) | LOW — measures *sanctioned youth*, not crime incidence | ✗ — wrong measure + new unstable series |

## Investigation Trail
1. WebSearch Observatorio → confirmed it's the same SPD Centro de Prevención de Homicidios the site already uses; 2024 national rate 6.0/100k; validated multi-institution. No new integration needed — it's M1 already.
2. WebSearch SernamEG/CIF → annual report, regional rates/100k; femicide counts so small that per-comuna rates over 346 comunas would be statistically meaningless (mostly zeros, a few undefined-spike rates).
3. WebSearch Reinserción Juvenil → semestral PDF by zone, brand-new service, measures program population not incidence.

## Results
**PARTIAL.** The one high-value member of this cluster (**Observatorio homicidios**) is *already* the index's homicide truth-source — so this spike mostly **confirms an existing good decision** rather than unlocking new data.
- **Femicide (SernamEG/CIF)** — viable only as a **national/regional gendered-violence context note**, never a comuna driver (count too small). Editorial caution: gendered lethal violence per comuna is both noisy and sensitive.
- **Reinserción Juvenil** — not usable: not incidence, not comuna, unstable new series.

**Impact:** no new comuna-level integration from this cluster. Reinforces that the only fresh comuna signal is ENUSC (Spike 004).
