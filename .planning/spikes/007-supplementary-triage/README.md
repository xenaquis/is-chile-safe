---
spike: 007
name: supplementary-triage
type: standard
validates: "Given 6 lower-priority sources, when triaged, then which (if any) clear the comuna + non-duplication + anti-infra-rep bar"
verdict: INVALIDATED as new signal (all duplicate CEAD or are national-only)
related: [004-enusc-victimization]
tags: [ine-aggregator, carabineros, pdi, sml, uaf, aduanas, datos-gob-cl, seed-002]
---

# Spike 007: Supplementary-Source Triage

## What This Validates
Given the 6 remaining inventoried sources, when triaged at feasibility-confirm depth, then do any clear all three bars (comuna-level + adds signal vs CEAD + anti-infra-representation)?

## Research

| Source | Comuna-level? | Adds signal vs CEAD? | Finding |
|--------|---------------|----------------------|---------|
| **INE — Estadísticas Policiales y Judiciales** | No (regional) | Partly (judicial+custody, but regional) | Original aggregation of Carabineros+PDI+PJUD+Gendarmería+SENAME+Reinserción; Excel 2013–Q1'25, annual boletines from 2023. The **police component duplicates CEAD's source**; the judicial/custody add-ons are **regional only**. Useful as a single clean Excel for a *regional* caveat layer, not comuna |
| **Carabineros / datos.gob.cl (Ley STOP, DMCS)** | **Yes** (CSV by comuna: homicidios, lesiones, violaciones, robos + VIF + Ley Drogas) | **No** | This is the *same* Carabineros DMCS that feeds CEAD (CEAD = Carabineros+PDI casos policiales). Clean comuna CSV — a potential **cleaner ingestion path for the existing CEAD component**, but zero new signal. (Secondary aggregator noted: `datoscomunales.pazciudadana.cl`) |
| **PDI / INE** | Via CEAD | No | Already integrated into CEAD/INE police statistics. Duplicate |
| **Servicio Médico Legal / datos.gob.cl** | Partial | Low (complementary) | Forensic datasets (homicide, sexual); many old/partial. Not a comuna-rate driver |
| **UAF (Unidad de Análisis Financiero)** | No (national) | Low | Money-laundering ROS; national, sectoral. Not street-crime, not comuna |
| **Servicio Nac. de Aduanas** | No (national/port) | Low | Seizures/contraband at borders & ports. National, not comuna street crime |

## Investigation Trail
1. WebFetch INE policiales-judiciales → confirmed aggregator scope + institutions + Excel cadence; police component overlaps CEAD source; judicial/custody regional.
2. WebSearch datos.gob.cl Carabineros → confirmed a **comuna-level DMCS CSV exists** (homicidios/lesiones/violaciones/robos), plus VIF and Ley Drogas datasets; same source as CEAD. Noted Paz Ciudadana comuna platform as a cross-check aggregator.
3. PDI, SML, UAF, Aduanas triaged from the source inventory + general posture: duplicate (PDI), complementary/dated (SML), or national-only (UAF, Aduanas).

## Results
**INVALIDATED as a source of new anti-infra-representation signal.** Every source here is one of:
- **Duplicative** of CEAD's existing police input (Carabineros datos.gob.cl, PDI, INE police component), or
- **Sub-comuna / national-only** (INE judicial-custody = regional; UAF, Aduanas = national; SML = partial/dated).

**One actionable byproduct (not a metric change):** the **Carabineros datos.gob.cl comuna CSV** is a candidate *cleaner/more-stable ingestion path* for the data the site already shows via CEAD — worth a separate tech-debt note (CEAD endpoints are the project's known single-point fragility), but it is **not** enrichment and out of scope for SEED-002's go/no-go.
