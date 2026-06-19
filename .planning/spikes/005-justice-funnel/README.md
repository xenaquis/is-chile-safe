---
spike: 005
name: justice-funnel
type: standard
validates: "Given the downstream funnel stages (prosecution → courts → custody), when checked, then which are commune-level + per-100k compatible + additive vs CEAD"
verdict: INVALIDATED for comuna-level (regional caveat only)
related: [004-enusc-victimization]
tags: [fiscalia, poder-judicial, gendarmeria, funnel, prosecution, custody, seed-002]
---

# Spike 005: Justice Funnel — Fiscalía + Poder Judicial + Gendarmería

## What This Validates
Given the expert's recommended downstream trio (ingresos al sistema penal → causas/sentencias → población privada de libertad), when each is checked against comuna granularity + per-100k + non-duplication of CEAD, then can any drive per-comuna color?

## Research

| Source | Endpoint / format | Comuna-level? | Periodicity | Finding |
|--------|-------------------|---------------|-------------|---------|
| **Fiscalía (SAF)** | "Estadística Interactiva" = **Power BI embed** (`app.powerbi.com/view?r=…`) + Excel boletines | **No** (regional / fiscalía regional standard; comuna not exposed) | Semestral + annual from 2026 (quarterly dropped) | Data is rich (casos, delitos, términos) but the only machine path is a Power BI `view` iframe — brittle to scrape, no clean comuna export |
| **Poder Judicial** | DECS "Bases de Datos" = **one-off study Excel files**; PJUD en Números = PDF boletines | **No** (tribunal/court jurisdiction) | Irregular / static date ranges (e.g. Oct'19–Jan'20) | No sustained, regularly-updated comuna open-data feed exists. Datasets are research snapshots, not a pipeline source |
| **Gendarmería** | Interactive region map + tables | **No** (region only) | Monthly | Two disqualifiers: region-only **and** the unit is the **prison establishment location, not the crime location** — wrong axis for "where is exposure higher" |

## Investigation Trail
1. browseros → Fiscalía interactive app: page is an iframe "Reportes Estadísticos MP - Externo"; `evaluate_script` extracted the src = a Power BI `app.powerbi.com/view` report. Confirms interactive-but-brittle; boletines remain the only file export (Excel/PDF, regional).
2. WebFetch Fiscalía estadísticas overview → confirmed SAF source, Excel boletines, no comuna granularity stated, 2026 cadence cut to semestral/annual.
3. WebFetch PJUD DECS bases-de-datos → 9 Excel datasets, tribunal-level, static one-offs, no comuna breakdown, not regularly maintained.
4. WebFetch Gendarmería est_general → region-only interactive tables, monthly, prison-location semantics.

## Results
**INVALIDATED for comuna-level enrichment.** None of the three can drive the 346-comuna choropleth:
- **Fiscalía** — regional, and the interactive is a Power BI embed (high effort, brittle, violates ~$0/low-effort + fail-gracefully constraints). Prosecution stage *would* add funnel signal, but only regionally.
- **Poder Judicial** — no sustainable comuna open data at all; study snapshots only.
- **Gendarmería** — region-only and conceptually wrong unit (custody location ≠ crime location).

**Salvage value:** all three can feed an optional **regional "reality context" band** (prosecution / custody context, explicitly regional, never driving comuna color) — but that is a nice-to-have, not a go-live blocker, and Fiscalía's Power BI dependency makes even that brittle. **Recommend deferring the regional funnel band post-launch.**
