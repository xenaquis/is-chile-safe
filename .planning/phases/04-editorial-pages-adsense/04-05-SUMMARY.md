---
phase: 04-editorial-pages-adsense
plan: "05"
subsystem: editorial-pages-map-bearing
tags: [editorial, map, safest-cities, methodology, hreflang, cead, client-only]
dependency_graph:
  requires: [04-01, 04-03]
  provides:
    - site/src/pages/chile-crime-map.astro
    - site/src/pages/santiago-safety-map.astro
    - site/src/pages/safest-cities-in-chile.astro
    - site/src/pages/methodology.astro
    - site/src/pages/es/mapa-delito-chile.astro (hreflang stub)
    - site/src/pages/es/mapa-seguridad-santiago.astro (hreflang stub)
    - site/src/pages/es/comunas-mas-seguras-chile.astro (hreflang stub)
    - site/src/pages/es/metodologia.astro (hreflang stub)
  affects:
    - dist/ (91 pages built)
tech_stack:
  added: []
  patterns:
    - "Map-bearing pages use MapIsland client:only=react inside .map-island-block (100vw breakout from 720px prose column)"
    - "D-10: NO AdSlot inside/adjacent to MapIslandBlock — ads only in EditorialLayout bottom slot"
    - "safest-cities ranking: loadIndex + loadRolloutCuts + loadCommune sorted by rate ascending; low_population excluded (DATA-04)"
    - "loadNationalAverage() (MEAN) for all national callouts — SUM never used"
    - "Forbidden-language gate: avoid 'the safest', 'safest-cities ranking' — use 'lowest-reported-incidence ranking'"
    - "methodology.astro: 6 required H2 sections in order, 5% trend threshold (D-13), explicit non-claims section (D-15)"
key_files:
  created:
    - site/src/pages/chile-crime-map.astro
    - site/src/pages/santiago-safety-map.astro
    - site/src/pages/safest-cities-in-chile.astro
    - site/src/pages/methodology.astro
    - site/src/pages/es/mapa-delito-chile.astro
    - site/src/pages/es/mapa-seguridad-santiago.astro
    - site/src/pages/es/comunas-mas-seguras-chile.astro
    - site/src/pages/es/metodologia.astro
  modified: []
decisions:
  - "ES stub pages added for hreflang reciprocity (Rule 2): hreflang.mjs validator requires reciprocal pages; ES full content deferred to Plan 06"
  - "MapIslandBlock uses 100vw width + margin-left: calc(50% - 50vw) CSS breakout pattern to escape 720px prose column inside EditorialLayout"
  - "safest-cities ranking uses loadRolloutCuts() not loadIndex() to stay within published data only; excludes low_population communes"
  - "Phrase 'the safest' is a forbidden term — replaced with 'lowest-reported-incidence ranking' throughout methodology.astro (Rule 1 fix)"
  - "methodology.astro esPath=/es/metodologia/; 5% trend threshold per D-13 from 01-CONTEXT.md"
metrics:
  duration: "18m"
  completed: "2026-06-13"
  tasks: 3
  files: 8
---

# Phase 04 Plan 05: Map-Bearing Editorial Pages + Safest-Cities + Methodology Summary

Two EN map-bearing editorial pages embedding MapIsland with editorial prose, a CEAD-sourced lowest-reported-incidence ranking with strictly qualified comparatives, and the methodology credibility page documenting all six required H2 sections including explicit non-claims. Four ES stub pages created for hreflang reciprocity.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | chile-crime-map.astro + santiago-safety-map.astro (map-bearing) | 3d65129 | site/src/pages/chile-crime-map.astro, santiago-safety-map.astro, es/mapa-delito-chile.astro, es/mapa-seguridad-santiago.astro |
| 2 | safest-cities-in-chile.astro (CEAD ranking) | 2f3ed88 | site/src/pages/safest-cities-in-chile.astro, es/comunas-mas-seguras-chile.astro |
| 3 | methodology.astro (EDIT-03) | d5ff0b5 | site/src/pages/methodology.astro, es/metodologia.astro |

## Verification Results

- Build: 91 pages, forbidden-language PASS (91 pages scanned, 0 forbidden terms)
- map.mjs PASS (EN + ES map island markers, locate aria-label, zero-React guard, runtime data)
- hreflang PASS (all reciprocal pairs resolve)
- schema PASS, commune PASS, rollout PASS, region PASS, crime PASS
- MapIsland client:only=react confirmed in chile-crime-map and santiago-safety-map dist HTML
- safest-cities: CEAD source + per-100k present in built HTML
- methodology: all 6 required section strings present in built HTML (cead, rate is calculated, cifra negra, trend, comparison, does not say)
- structure.mjs: pre-existing FAIL on 9 pages from future plans (legal pages, contact, about, es/delitos-por-region) — not caused by this plan; deferred to Plans 07+

## Deviations from Plan

### Auto-added Missing Critical Functionality

**1. [Rule 2 - Missing] ES hreflang stub pages (x4)**
- **Found during:** Task 1, 2, 3 (hreflang.mjs requires reciprocal ES pages)
- **Issue:** All four EN pages created reference ES slugs that don't exist until Plan 06.
- **Fix:** Created 4 ES stub pages with DataCallouts + brief ES content + links to EN counterpart. Valid pages — not empty redirects.
- **Files:** es/mapa-delito-chile.astro, es/mapa-seguridad-santiago.astro, es/comunas-mas-seguras-chile.astro, es/metodologia.astro
- **Commits:** 3d65129, 2f3ed88, d5ff0b5

### Auto-fixed Bugs

**2. [Rule 1 - Bug] "the safest" forbidden term in methodology.astro**
- **Found during:** Task 3 first build (forbidden-language.mjs caught it)
- **Issue:** methodology.astro used "safest-cities ranking" in two places, which triggered the "the safest" forbidden term pattern.
- **Fix:** Replaced with "lowest-reported-incidence ranking" in both occurrences.
- **Files modified:** site/src/pages/methodology.astro
- **Commit:** d5ff0b5

## Known Stubs

Four ES pages are content stubs — DataCallouts + brief paragraphs — rather than full 900-1200 word editorial prose. Plan 06 will replace them with full ES content:
- es/mapa-delito-chile.astro
- es/mapa-seguridad-santiago.astro
- es/comunas-mas-seguras-chile.astro
- es/metodologia.astro (contains full methodology content in ES — more than a minimal stub, but shorter than the EN version)

## Threat Flags

No new threat surface beyond the plan's threat model:
- T-04-11: All comparatives on safest-cities page qualified with "according to CEAD data for {year}"; forbidden-language gate confirms 0 violations
- T-04-12: MapIslandBlock has no AdSlot in/around it — EditorialLayout bottom slot only
- T-04-10: loadNationalAverage() (MEAN) confirmed for all national callouts; SUM never used

## Self-Check: PASSED

- site/src/pages/chile-crime-map.astro: FOUND
- site/src/pages/santiago-safety-map.astro: FOUND
- site/src/pages/safest-cities-in-chile.astro: FOUND
- site/src/pages/methodology.astro: FOUND
- site/src/pages/es/mapa-delito-chile.astro: FOUND
- site/src/pages/es/mapa-seguridad-santiago.astro: FOUND
- site/src/pages/es/comunas-mas-seguras-chile.astro: FOUND
- site/src/pages/es/metodologia.astro: FOUND
- Commit 3d65129: FOUND
- Commit 2f3ed88: FOUND
- Commit d5ff0b5: FOUND
