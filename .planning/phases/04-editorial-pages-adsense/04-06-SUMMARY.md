---
phase: 04-editorial-pages-adsense
plan: "06"
subsystem: editorial-pages-es
tags: [editorial, es, seo, hreflang, data-callout, json-ld, cead, map, faq]
dependency_graph:
  requires: [04-01, 04-03, 04-04, 04-05]
  provides:
    - site/src/pages/es/index.astro (extended)
    - site/src/pages/es/mapa-delito-chile.astro (full content)
    - site/src/pages/es/mapa-seguridad-santiago.astro (full content)
    - site/src/pages/es/delitos-por-comuna.astro (full content + FAQPage JSON-LD)
    - site/src/pages/es/delitos-por-region.astro (new — no EN pair, self-referencing enPath)
    - site/src/pages/es/comunas-mas-seguras-chile.astro (full content + ranking table)
    - site/src/pages/es/seguridad-valparaiso.astro (full content)
    - site/src/pages/es/seguridad-vina-del-mar.astro (full content)
    - site/src/pages/es/seguridad-concepcion.astro (full content)
    - site/src/pages/es/metodologia.astro (H2 fixed to pass gate)
  affects:
    - dist/ (92 pages built)
tech_stack:
  added: []
  patterns:
    - "All ES editorial pages use EditorialLayout (lang=es) with reciprocal hreflang to EN pairs"
    - "Map-bearing ES pages embed MapIsland client:only=react inside .map-island-block (100vw breakout)"
    - "FAQBlock + FAQPage JSON-LD in es/delitos-por-comuna (mirrors is-chile-safe EN pattern)"
    - "Ranking table in es/comunas-mas-seguras-chile mirrors safest-cities-in-chile EN pattern"
    - "loadNationalAverage() (MEAN) for all national callouts — SUM never used"
    - "es/delitos-por-region enPath self-references per slug_flag (no EN pair in EDIT-01)"
    - "Accent-insensitive forbidden-language gate: 92 pages, 0 violations"
key_files:
  created:
    - site/src/pages/es/delitos-por-region.astro
  modified:
    - site/src/pages/es/index.astro
    - site/src/pages/es/mapa-delito-chile.astro
    - site/src/pages/es/mapa-seguridad-santiago.astro
    - site/src/pages/es/delitos-por-comuna.astro
    - site/src/pages/es/comunas-mas-seguras-chile.astro
    - site/src/pages/es/seguridad-valparaiso.astro
    - site/src/pages/es/seguridad-vina-del-mar.astro
    - site/src/pages/es/seguridad-concepcion.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - "es/delitos-por-region.astro created new (no EN pair in EDIT-01); enPath=/es/delitos-por-region/ (self) per slug_flag"
  - "es/metodologia.astro H2 renamed from 'Lo que este sitio NO afirma' to 'Lo que este sitio NO dice' to pass Task 3 gate check"
  - "All 10 ES pages replace previous stubs with sober qualified Spanish prose (800-1100 words each)"
metrics:
  duration: "25m"
  completed: "2026-06-13"
  tasks: 3
  files: 10
---

# Phase 04 Plan 06: ES Editorial Pages (All 10 EDIT-02 Slugs) Summary

All 10 ES priority editorial pages (EDIT-02) authored with sober, CEAD-sourced Spanish prose, replacing stubs from Plans 04-04 and 04-05. Two ES map-bearing pages embed MapIsland(lang=es), the ES methodology page has all 6 required H2 sections, and the ES lowest-incidence ranking uses the same data-driven CEAD approach as its EN counterpart.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ES home extended + two ES map-bearing pages | 7a95575 | es/index.astro, es/mapa-delito-chile.astro, es/mapa-seguridad-santiago.astro |
| 2 | delitos-por-comuna FAQ + delitos-por-region (new) + comunas-mas-seguras ranking | a4e9a33 | es/delitos-por-comuna.astro, es/delitos-por-region.astro (new), es/comunas-mas-seguras-chile.astro |
| 3 | Three ES city pages + fix metodologia H2 | 9fdecef | es/seguridad-valparaiso.astro, es/seguridad-vina-del-mar.astro, es/seguridad-concepcion.astro, es/metodologia.astro |

## Verification Results

- Build: 92 pages (one new: es/delitos-por-region/)
- forbidden-language: PASS — 92 pages scanned, 0 forbidden terms
- hreflang: PASS — 92 pages, all reciprocal pairs resolve; es/delitos-por-region self-referencing enPath accepted
- map.mjs: PASS — ES map island markers, locate aria-label, runtime data confirmed
- schema.mjs, commune, rollout, region, crime: PASS
- structure.mjs: pre-existing FAIL on 8 pages from Plan 07 (legal + contact pages) — not caused by this plan; deferred to Plan 07
- Task-3 gate: metodologia HTML contains all 6 check strings (cead, se calcula, cifra negra, tendencia, comparaci, no dice)
- Two ES map pages embed MapIsland client:only=react with data-map-locate-label=es
- FAQPage JSON-LD confirmed in es/delitos-por-comuna built HTML
- CEAD source + qualified comparatives in es/comunas-mas-seguras-chile

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Metodologia H2 "Lo que este sitio NO afirma" failed the Task 3 gate**
- **Found during:** Task 3 pre-commit gate check (verified string 'no dice' not in HTML)
- **Issue:** The existing es/metodologia.astro stub used "NO afirma" instead of "NO dice" — the Task 3 acceptance verification checks for "no dice" in the built HTML.
- **Fix:** Renamed H2 from "Lo que este sitio NO afirma" to "Lo que este sitio NO dice".
- **Files modified:** site/src/pages/es/metodologia.astro
- **Commit:** 9fdecef

### New File Created (not in plan's files_modified)

**2. [Rule 2 - Missing] es/delitos-por-region.astro was absent from disk**
- The plan's files list showed it as a file to modify, but it didn't exist on disk (stubs from Plans 04 and 05 covered 8 of the 10 ES pages; delitos-por-region was never created as a stub because it has no EN pair). Created from scratch with full ~1000-word content.
- **Commit:** a4e9a33

## Known Stubs

None — all 10 ES pages now have full editorial content (800-1100 words each). Previous stubs replaced.

## Threat Flags

No new threat surface beyond the plan's threat model:
- T-04-13: forbidden-language gate confirmed 0 violations across 92 pages
- T-04-12: MapIslandBlock has no AdSlot in/around it — confirmed in both ES map pages
- T-04-10: loadNationalAverage() (MEAN) confirmed for all national callouts; SUM never used

## Self-Check: PASSED

- site/src/pages/es/index.astro: FOUND (modified)
- site/src/pages/es/mapa-delito-chile.astro: FOUND (modified)
- site/src/pages/es/mapa-seguridad-santiago.astro: FOUND (modified)
- site/src/pages/es/delitos-por-comuna.astro: FOUND (modified)
- site/src/pages/es/delitos-por-region.astro: FOUND (created)
- site/src/pages/es/comunas-mas-seguras-chile.astro: FOUND (modified)
- site/src/pages/es/seguridad-valparaiso.astro: FOUND (modified)
- site/src/pages/es/seguridad-vina-del-mar.astro: FOUND (modified)
- site/src/pages/es/seguridad-concepcion.astro: FOUND (modified)
- site/src/pages/es/metodologia.astro: FOUND (modified)
- Commit 7a95575: FOUND
- Commit a4e9a33: FOUND
- Commit 9fdecef: FOUND
