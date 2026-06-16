---
phase: quick-260616-lu4
plan: "01"
subsystem: frontend
tags: [progressive-enhancement, ranking-tables, i18n, vanilla-js, seo]
dependency_graph:
  requires: []
  provides: [sortable-ranking-tables, year-selector-ranking]
  affects: [region-pages, crime-ranking-pages]
tech_stack:
  added: []
  patterns: [progressive-enhancement, data-attributes, vanilla-js-iife]
key_files:
  created:
    - site/src/components/RankingTableEnhancer.astro
  modified:
    - site/src/config/i18n.ts
    - site/src/components/CommuneRankingTable.astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
decisions:
  - Vanilla JS IIFE in RankingTableEnhancer; zero new dependencies
  - rte-strings JSON blob pattern for bilingual strings (no bundler magic)
  - data-rates stores complete-year map server-side; client never re-filters partial
metrics:
  duration: ~25m
  completed: "2026-06-16"
  tasks: 4
  files: 7
---

# Phase quick-260616-lu4 Plan 01: Dynamic Ranking Tables Summary

**One-liner:** Vanilla JS progressive-enhancement adds year selector and column sort (rate + name, asc/desc) to all four ranking table contexts (region EN/ES, crime EN/ES) via a single shared `RankingTableEnhancer.astro` component with embedded `data-*` hooks.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add bilingual control strings to i18n.ts | 602b1d7 | site/src/config/i18n.ts |
| 2 | Create RankingTableEnhancer.astro | d36c0e0 | site/src/components/RankingTableEnhancer.astro |
| 3 | Wire region commune table | 3ae418d | CommuneRankingTable.astro, region/[slug].astro (EN+ES) |
| 4 | Wire crime-ranking pages + final build validation | 2a550bd | crime-ranking/[crime].astro (EN+ES) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is wired from live CEAD series entries via `data-rates` attributes.

## Threat Flags

No new network endpoints, auth paths, or trust-boundary surface introduced. All changes are static HTML generation + client-side DOM manipulation.

## Self-Check: PASSED

- RankingTableEnhancer.astro: exists, 325+ lines, exports Props {locale}
- i18n.ts: sort_label, sort_ascending, sort_descending, year_select_label, year_select_aria in both EN_STRINGS and ES_STRINGS
- Built HTML: 8 crime-EN pages + 8 crime-ES pages carry data-ranking-table; 16 region-EN + 16 region-ES carry data-rates
- tsc --noEmit: passes with exit 0
- npm run build: passes with exit 0, no errors
- Static rate cells unchanged: region=Math.round (integer), crime=1 decimal
