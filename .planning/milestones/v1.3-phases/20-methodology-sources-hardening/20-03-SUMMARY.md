---
phase: 20-methodology-sources-hardening
plan: "03"
status: complete
subsystem: methodology-pages
tags: [citations, enusc, ine, sources, trend-deep-link, parity]
dependency_graph:
  requires: [20-01, 20-02]
  provides: [inline-enusc-citation, ine-citation, trend-deep-link, en-es-parity]
  affects: [methodology.astro, es/metodologia.astro, MethodologyCaveat.astro]
tech_stack:
  added: []
  patterns: [inline-anchor-citation, locale-aware-deep-link]
key_files:
  modified:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - site/src/components/MethodologyCaveat.astro
decisions:
  - Used https://www.ine.gob.cl/enusc as ENUSC citation URL (matches SOURCES.md entry with [verify URL] discipline)
  - Used https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion for INE denominator link
  - MethodologyCaveat gets a new trendHref variable + locale-aware sentence; existing methodHref and glossaryHref unchanged
metrics:
  duration: "~10 min"
  completed: "2026-06-19"
  tasks_completed: 3
  files_modified: 3
---

# Phase 20 Plan 03: Inline Source Citations + Trend Deep-link Summary

Wired inline ENUSC citation links (SRC-02) and INE denominator links (per-figure sourcing) into both methodology pages, added trend deep-link to MethodologyCaveat (MC-06), and confirmed 7-H2 EN/ES structural parity (MTH-04).

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Inline ENUSC + INE citation links in EN/ES methodology pages (SRC-02) | fd4e079 |
| 2 | MethodologyCaveat trend deep-link to #trend-formula; 7-H2 parity confirmed (MTH-04, MC-06) | fd4e079 |
| 3 | Build + validate gate: 12/12 validators pass (OneDrive-safe chained) | fd4e079 |

## What Was Done

### SRC-02 — ENUSC inline citation link
In the "Underreporting (cifra negra)" / "Subregistro (cifra negra)" H2 of both pages, the plain text mention of "Encuesta Nacional Urbana de Seguridad Ciudadana — ENUSC" is now wrapped in `<a href="https://www.ine.gob.cl/enusc" rel="noopener noreferrer" target="_blank">`. URL taken from data/SOURCES.md ENUSC entry with `[verify URL]` discipline intact.

### Per-figure source attribution
INE population projections mention in the "How the rate is calculated" / "Cómo se calcula la tasa" H2 now links to `https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/proyecciones-de-poblacion` in both EN and ES pages. CEAD, chilemapas, SPD, SII, and Fiscalía were already linked from plan 20-02 work.

### MC-06 — Trend deep-link in MethodologyCaveat
`MethodologyCaveat.astro` now defines `trendHref` (`/methodology/#trend-formula` for EN, `/es/metodologia/#trend-formula` for ES) and renders a locale-aware sentence: "Trend indicators use a 3-year window — see [trend formula]." linking to the `#trend-formula` anchor created in plan 20-02. Component remains static (zero `client:*` directives).

### MTH-04 — EN/ES H2 parity
Both pages confirmed at 7 H2 each:
1. Data source: CEAD / Fuente de datos: CEAD
2. Map boundaries: chilemapas / Geometría del mapa: chilemapas
3. How the rate is calculated / Cómo se calcula la tasa
4. Underreporting (cifra negra) / Subregistro (cifra negra)
5. Trend formula / Fórmula de tendencia
6. Comparison criteria / Criterios de comparación
7. What this site does NOT say / Lo que este sitio NO afirma

## Deviations from Plan

None — plan executed exactly as written.

## Verification

- `grep -Eq 'href="[^"]*(ine\.gob\.cl/enusc)' site/src/pages/methodology.astro` → PASS
- `grep -Eq 'href="[^"]*(ine\.gob\.cl/enusc)' site/src/pages/es/metodologia.astro` → PASS
- `grep -c '<h2' methodology.astro` = 7, `grep -c '<h2' metodologia.astro` = 7 → PASS
- `grep -q "#trend-formula" site/src/components/MethodologyCaveat.astro` → PASS
- `npm run build && npm run validate` → 12/12 validators PASSED (including forbidden-language #9)

## Self-Check: PASSED

- site/src/pages/methodology.astro — exists, ENUSC link present
- site/src/pages/es/metodologia.astro — exists, ENUSC link present
- site/src/components/MethodologyCaveat.astro — exists, #trend-formula present
- Commit fd4e079 — confirmed in git log
