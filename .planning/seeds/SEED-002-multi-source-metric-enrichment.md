---
id: SEED-002
title: Multi-source crime-metric enrichment — feasibility research before go-live
planted_during: Phase 18 completion (v2.0), expert consultation on data sources
planted_date: 2026-06-19
trigger_when: before v2.0 go-live (Phase 22), or when planning a SPIKE/QUICK to evaluate enriching the composite index beyond CEAD-only data
status: planted
owner_intent: autonomous research via browseros, then present findings to user for a go/no-go on robustifying the metric before launch
---

# SEED-002: Multi-Source Crime-Metric Enrichment (feasibility research)

## Problem statement

The current composite crime-exposure index (Phase 18) is built **almost exclusively on
CEAD data** — i.e. police *casos policiales* (denuncias + detenciones from Carabineros/PDI),
plus the SPD VHC homicide switch (M1) and the SII exposure proxy (denominator). CEAD
captures **reported** crime only. A subject-matter expert flagged that this can
**under-represent reality** because it omits victimization (cifra negra / cifra oculta),
prosecutorial throughput, judicial outcomes, and custody populations — each of which
measures a *different stage* of the crime/justice funnel.

**Goal of this seed:** before going live, run an autonomous feasibility study to decide
whether (and how) to enrich the metric with one or more additional official Chilean
sources, producing a metric that is **more indicative of reality and does not
infra-represent**, under a **traceable methodological design that respects the site's
editorial inspiration** (never an absolute "seguro/peligroso" verdict; every figure
sourced + caveated; EN/ES parity; SEO-static).

## When to surface

- Before kicking off Phase 22 (Go-Live), as an intermediate **SPIKE** or **QUICK** phase.
- Whenever reconsidering the composite index inputs/weights.
- The user wants the conversation context cleared first; this seed + the linked memory
  (`[[multi-source-metric-enrichment-seed]]`) are the durable handoff.

## What the expert said — official source inventory

Different sources measure **different things**; comparison with CEAD requires care
(a drop in CEAD ≠ equivalent drop in victimization, convictions, or prison population).

| # | Fuente oficial | Qué publica | Mide (etapa del embudo) | Para qué sirve |
|---|----------------|-------------|--------------------------|----------------|
| 1 | **INE — Estadísticas de Seguridad Pública y Justicia Penal** | Boletines, anuarios, cuadros Excel de estadísticas policiales y judiciales (incl. históricos) | Agregador estandarizado (policial + judicial) | Comparar Carabineros, PDI, Poder Judicial, Gendarmería, justicia penal en formato más estandarizado |
| 2 | **INE / Min. Seguridad — ENUSC** | Encuesta Nacional Urbana de Seguridad Ciudadana: victimización de hogares/personas, cifra oculta, percepción, exposición | **Victimización** (incl. no denunciados) | Estimar "cifra negra"; delitos sufridos no reportados. **Clave contra la infra-representación.** Probablemente NO por comuna (muestral, regional/urbana) |
| 3 | **Ministerio Público / Fiscalía (SAF)** | Estadística interactiva + boletines: casos, delitos, términos, salidas | **Ingresos al sistema penal** | Tipos de delito investigados, salidas, resultados de persecución |
| 4 | **Poder Judicial** ("PJUD en Números") | Estadísticas por cortes/juzgados, boletines, datos abiertos | **Causas tramitadas / sentencias** | Tramitación, términos, sentencias, desempeño de tribunales |
| 5 | **Defensoría Penal Pública (SIGDP)** | Informes de causas e imputados atendidos por defensa pública | Imputados con defensa pública (subconjunto) | No cubre todo el universo de imputados |
| 6 | **Gendarmería de Chile** | Estadística penitenciaria mensual: población vigente, subsistemas, compendios | **Personas privadas de libertad** | Prisión preventiva, condenados, ejecución de penas |
| 7 | **Servicio Nacional de Reinserción Social Juvenil** | Informes sobre adolescentes/jóvenes en conflicto con la justicia | Responsabilidad penal adolescente | Sanciones y programas juveniles |
| 8 | **Centro para la Prevención de Homicidios / Observatorio de Homicidios** | Cifras validadas interinstitucionalmente de homicidios consumados; distingue preliminar policial/Fiscalía/CEAD | **Homicidios consumados (validados)** | Fuente preferente para homicidios. **Ya usado parcialmente: SPD VHC = M1 del índice (F13).** |
| 9 | **SernamEG / Circuito Intersectorial de Femicidio** | Femicidios consumados/frustrados/tentados; informe anual usa Red de Asistencia a Víctimas | Violencia letal de género | Femicidios + respuesta institucional |
| 10 | **Carabineros / Ley STOP / datos.gob.cl** | Datos policiales DMCS, VIF, Ley Drogas, denuncias, detenciones | Policial-operativo | Revisar cobertura/vigencia/metodología por dataset |
| 11 | **PDI / INE** | Delitos investigados, denuncias, detenidos por PDI (integrados por INE) | Policial (PDI) | Delitos complejos: sexuales, drogas, económicos, homicidios |
| 12 | **Servicio Médico Legal / datos.gob.cl** | Datasets de homicidios, sexología forense, atenciones por delitos sexuales (varios antiguos/parciales) | Forense complementario | No reemplaza policial/fiscal/judicial |
| 13 | **Unidad de Análisis Financiero (UAF)** | Reportes de operaciones sospechosas, tipologías de lavado (base sentencias condenatorias) | Delito económico / crimen organizado financiero | Lavado de activos, financiamiento del terrorismo |
| 14 | **Servicio Nacional de Aduanas** | Incautaciones, contrabando, drogas, armas, divisas, fiscalización | Criminalidad transfronteriza | Contrabando, mercados ilícitos |

**Expert's recommended minimum academic combination:** CEAD + ENUSC + Fiscalía + Poder
Judicial + Gendarmería. For homicides add Observatorio de Homicidios (already in use as
SPD VHC); for femicides add SernamEG/Circuito Intersectorial; for adolescents add
Reinserción Social Juvenil.

## Research mission (for the future autonomous SPIKE/QUICK)

Run autonomously, primarily via **browseros** (MCP at `http://127.0.0.1:9200/mcp` — see
memory `[[browseros-mcp-port]]` and `[[browseros-review-gotchas]]`; browseros must run
**inline** in the main loop, not inside a gsd-executor subagent). For **each** of the 14
sources, investigate and score against the site's hard requirements, then recommend a
metric design.

### Per-source evaluation grid (fill one row per source)

1. **Scrapeable / obtainable?** — Is there a stable HTML endpoint, downloadable
   Excel/CSV, open-data API (datos.gob.cl), or interactive dashboard with an
   underlying data request? Robots/ToS posture. Auth required? Format stability.
2. **Geographic granularity** — Does it publish at **commune (comuna) level** (the
   site's unit, 346 comunas)? Or only region/national/urban? (Site needs commune
   granularity to drive the choropleth; coarser data may still feed a national/regional
   caveat layer but cannot drive per-comuna color.)
3. **Periodicity match** — Does its release cadence fit the site's standard (CEAD
   quarterly; news daily)? Annual-only sources (ENUSC, many anuarios) constrain how
   "current" the enriched metric can be.
4. **Metric compatibility** — Can it be normalized to a **per-100k rate** (note:
   existing CEAD rates are *already* per-100k — see memory `[[crime-rates-already-per-100k]]`)
   and fed into the composite pipeline (winsorized min-max → [0,100], 5-band levels)?
   Does it measure a funnel stage that **adds signal** vs. duplicating CEAD?
5. **Anti-infra-representation value** — Specifically, does it capture *unreported*
   crime (ENUSC cifra negra) or downstream confirmation (Fiscalía/PJUD/Gendarmería)?
   This is the whole point of the exercise.
6. **Editorial / legal fit** — Attributable to a named official source, citable, no
   absolute safety verdict, no defamation risk per comuna. Respects CLAUDE.md rules.
7. **Effort / risk** — Pipeline cost, brittleness, ~$0 infra constraint, fallback-on-fail.

### Methodological design deliverable

- Propose 1–3 candidate enriched-metric designs (e.g. keep CEAD core + add an ENUSC
  "cifra negra" adjustment factor at region level as a documented caveat; or a
  multi-stage funnel composite). Each must be **traceable**: every input mapped to a
  source row, a figure-registry entry (F-series), and a SOURCES.md canonical block —
  consistent with the existing zero-orphan figure-registry discipline.
- State explicitly where commune-level data is unavailable and how the design degrades
  (national/regional caveat vs. per-comuna value) without implying a safety verdict.
- Respect locked composite decisions from Phase 18 (D-03 SII fallback, locked weights,
  [0,100] normalization, SPD VHC as homicide truth) — propose changes as *additive* or
  *versioned*, not silent rewrites.

### Final output

A findings report (suggest `.planning/research/SEED-002-FINDINGS.md` or a SPIKE summary)
with: the filled 14-row grid, a shortlist of viable sources, the recommended metric
design(s) with methodology, effort estimate, and a clear **go / no-go recommendation on
robustifying the metric before Phase 22 go-live**. Present to the user for decision.

## Constraints to carry (from CLAUDE.md + project memory)

- **Never** label a territory absolutely "seguro/peligroso"; always attribute sources.
- Infra ~$0 (Cloudflare Pages + GitHub Actions free; only DeepSeek is variable cost).
- All content HTML-static, SEO-indexable, EN/ES parity.
- Scraping courtesy: delays for government servers; respect robots/ToS.
- Site unit = comuna (346); existing CEAD rates are already per-100k (do not rescale).
- Composite drug-family taxonomy quirk: see memory `[[cead-drug-family-taxonomy]]`.
- This is **research/feasibility only** — no production metric change without user sign-off.

## How to trigger next session (after /clear)

`/gsd-spike` (experiential research) or `/gsd-quick` for a lighter pass, pointing at this
seed: "Execute SEED-002 — autonomous browseros feasibility research on multi-source crime
metric enrichment; produce findings report and a go/no-go before go-live."
