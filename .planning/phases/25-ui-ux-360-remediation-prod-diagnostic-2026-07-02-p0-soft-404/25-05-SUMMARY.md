---
phase: 25
plan: "05"
subsystem: editorial-pages
tags: [seo, editorial, static-visuals, sparkline, rate-table]
dependency_graph:
  requires: [25-02]
  provides: [static-rate-tables, sparklines, editorial-visuals]
  affects: [is-santiago-safe, is-chile-safe, safest-cities-in-chile]
tech_stack:
  added: []
  patterns: [CommuneRankingTable-reuse, Sparkline-reuse, loadIndex-filter-pattern]
key_files:
  created: []
  modified:
    - site/src/pages/is-santiago-safe.astro
    - site/src/pages/is-chile-safe.astro
    - site/src/pages/safest-cities-in-chile.astro
decisions:
  - "Used CommuneRankingTable(sortable=false) instead of custom table markup to reuse existing component and avoid duplicating table styles"
  - "Used loadNational().series for national sparkline (pop-weighted national rate) on is-chile-safe and safest-cities"
  - "rmBottom10 uses slice(-10).reverse() to show lowest RM communes ascending (most readable direction)"
metrics:
  duration: "12m"
  completed: "2026-07-02"
  tasks: 2
  files: 3
---

# Phase 25 Plan 05: Static Editorial Visuals (P1-5) Summary

**One-liner:** Static RM top/bottom-10 commune rate tables + sparklines added to three high-traffic editorial pages, all pre-rendered HTML from CEAD CEAD data at build time.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Static rate table + sparkline on is-santiago-safe.astro | 541579b | is-santiago-safe.astro |
| 2 | Static rate tables + sparklines on is-chile-safe + safest-cities | 9d8f8a0 | is-chile-safe.astro, safest-cities-in-chile.astro |

## What Was Built

- **is-santiago-safe.astro**: imported `loadIndex`, `CommuneRankingTable`, `Sparkline`; built `rmRows` from index filtered to `region_id=13 && !low_population`; rendered top-10 and bottom-10 `CommuneRankingTable` blocks (sortable=false) plus a Santiago commune sparkline (480×44, activeYear); added `.rate-table-figure` CSS from UI-SPEC.
- **is-chile-safe.astro**: added national top-10 and bottom-10 `CommuneRankingTable` blocks (from `loadIndex()` all non-low-population communes) + national trend sparkline using `loadNational().series`.
- **safest-cities-in-chile.astro**: added national trend sparkline after existing ranking table as context; page already had a `<table>` so sparkline is additive.

## Verification

- `npm run build` → 834 pages built, 0 errors
- `npm run validate` → 14/14 validators passed (including forbidden-language green)
- `grep -c '<table' dist/is-santiago-safe/index.html` > 0 ✓
- `grep -c '<table' dist/is-chile-safe/index.html` > 0 ✓
- `grep -c '<table' dist/safest-cities-in-chile/index.html` > 0 ✓
- SVG sparkline present in all three dist pages ✓
- CEAD attribution in all three pages ✓

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All data sourced from `loadIndex()` / `loadCommune()` / `loadNational()` at build time.

## Threat Flags

None. No new network endpoints or auth paths introduced. All data is build-time trusted local JSON.

## Self-Check: PASSED

- `site/src/pages/is-santiago-safe.astro` — modified ✓
- `site/src/pages/is-chile-safe.astro` — modified ✓
- `site/src/pages/safest-cities-in-chile.astro` — modified ✓
- Commit 541579b — exists ✓
- Commit 9d8f8a0 — exists ✓
