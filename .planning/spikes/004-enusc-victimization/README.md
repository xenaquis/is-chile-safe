---
spike: 004
name: enusc-victimization
type: standard
validates: "Given ENUSC is the only source measuring unreported crime (cifra negra), when we check its geographic granularity, then commune-level [0,100]-compatible data is feasible — or it degrades to a region-only caveat"
verdict: VALIDATED (partial coverage)
related: [008-observatorio-already-integrated]
tags: [enusc, victimization, cifra-negra, sae, ine, anti-infra-representation, seed-002]
---

# Spike 004: ENUSC Communal Victimization (the make-or-break source)

## What This Validates
Given ENUSC is the **only** inventoried source that captures *unreported* crime (victimization / cifra negra), when we check whether it publishes at the site's unit (comuna, 346), then either commune-level enrichment is feasible or the whole anti-infra-representation thesis collapses to a region-only caveat. Ran first because it could kill the design.

## Research
- **Method:** WebSearch + WebFetch over INE press + the experimental-statistics data page. (browseros confirmed live; static INE pages read faster via WebFetch.)
- **Headline finding (changes the expert's premise):** On **2026-01-21** INE published **communal** ENUSC 2024 victimization results using **Small Area Estimation (SAE)** models — the expert's brief assumed ENUSC was "probablemente NO por comuna." It now is, partially.

| Attribute | Finding |
|-----------|---------|
| Indicator | **Victimización a Hogares por Delitos Violentos (VHDV)** — one headline indicator only |
| Comuna coverage | **136 of 346 comunas** (~39%); survey applied to ~24k households across 136 comunas |
| Method | SAE = direct survey estimate + model-based prediction with auxiliary data (modeled, *not* direct measurement) → **"estadística experimental"** label |
| Download | Excel `tabulados-sae--enusc-2024-vhdv.xlsx` (Cuadros Estadísticos) + ArcGIS interactive map + metodología PDF |
| Data page | https://www.ine.gob.cl/estadisticas/estadisticas-experimentales/seguridad-ciudadana |
| Periodicity | National/regional ENUSC is annual (2024 results out Jul-2025); **communal SAE is brand-new (first run Jan-2026) — annual continuity not yet guaranteed** |
| National context | 8.5% households victims of violent crime; personal victimization 5.8% |

## How to Run
Open the INE experimental page above; download the `.xlsx`; the 136-comuna VHDV estimates are in the tabulado. ArcGIS map for visual confirmation of which comunas are covered.

## Investigation Trail
1. Searched ENUSC comuna data → hit the **Jan-2026 INE press release** announcing communal SAE results. Immediate flag: this overturns the seed's granularity assumption.
2. WebFetch press release → confirmed 136 comunas, single indicator (VHDV), SAE method, Excel + ArcGIS products.
3. WebFetch the experimental-statistics landing page → confirmed it hosts the ENUSC SAE product and the metodología SAE PDF; only experimental security product listed.
4. Did not download/parse the xlsx (feasibility-confirm depth, per session scope) — file existence + indicator + coverage are sufficient for go/no-go.

## Results
**VALIDATED — with three hard caveats.** Commune-level victimization enrichment **is feasible** and is the single most valuable anti-infra-representation move available, because no other source measures unreported crime at comuna level.

Caveats that shape the design:
- **Partial coverage:** 136/346 comunas. 210 comunas have *no* SAE estimate → the design must degrade gracefully (CEAD-only + "no victimization estimate" caveat).
- **Experimental + modeled:** SAE estimates carry model uncertainty; must be labeled "estadística experimental / estimación modelada," not presented as a hard count. Fits editorial rules (attributed, caveated, never absolute verdict).
- **Annual + continuity risk:** one indicator, annual at best, communal SAE continuity unproven → it's a context *layer*, not a replacement for the quarterly CEAD core.

**Impact on other spikes:** This is the only "new signal at comuna level" winner. It means the enrichment should be **narrow and additive** (one victimization layer), not a full multi-source funnel rebuild — which 005/007 then confirmed is infeasible anyway.
