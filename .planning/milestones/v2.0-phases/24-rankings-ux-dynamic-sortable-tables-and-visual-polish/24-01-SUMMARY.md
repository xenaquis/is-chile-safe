---
phase: 24-rankings-ux-dynamic-sortable-tables-and-visual-polish
plan: "01"
subsystem: frontend/rankings-ux
tags: [ranking-table, sort, progressive-enhancement, astro, bilingual]
dependency_graph:
  requires: []
  provides:
    - RankingTableEnhancer auto-sort on load (defaultSortDir)
    - safest-cities EN wired (data-ranking-table, data-rates, ascending override)
    - safest-cities ES wired (mirror)
  affects:
    - site/src/components/RankingTableEnhancer.astro
    - site/src/pages/safest-cities-in-chile.astro
    - site/src/pages/es/comunas-mas-seguras-chile.astro
tech_stack:
  added: []
  patterns:
    - data-default-sort-dir attribute on <table> drives initial sortDir in enhancer
    - ratesByYear built from data.series.filter(!partial) using rate_per_100k (total rate, not by_family)
    - updateAriaSort() + renderSort() called after seed loop to show arrow on load
key_files:
  created: []
  modified:
    - site/src/components/RankingTableEnhancer.astro
    - site/src/pages/safest-cities-in-chile.astro
    - site/src/pages/es/comunas-mas-seguras-chile.astro
decisions:
  - Initial sortKey changed from null to 'rate' so arrow renders without user interaction
  - data-default-sort-dir="asc" on safest-cities tables preserves editorial lowest-first intent
  - Caption sort hints added as inline .astro text (not i18n keys — per UI-SPEC)
metrics:
  duration: "12m"
  completed: "2026-06-20"
  tasks_completed: 2
  files_modified: 3
---

# Phase 24 Plan 01: Wire safest-cities ranking tables + auto-sort affordance on load — Summary

**One-liner:** Auto-initialized sort arrow (▼/▲) in RankingTableEnhancer via defaultSortDir + ratesByYear wiring of both safest-cities editorial pages (EN/ES) with ascending override.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Auto-show sort affordance on load; honor data-default-sort-dir | 28b6c02 | RankingTableEnhancer.astro |
| 2 | Wire EN + ES safest-cities pages into enhancer | 973dca5 | safest-cities-in-chile.astro, comunas-mas-seguras-chile.astro |

## What Was Built

### Task 1 — RankingTableEnhancer: auto-sort on load

Three changes to the per-table init block in `RankingTableEnhancer.astro`:

1. Read `table.dataset.defaultSortDir` after existing config reads → `defaultSortDir: 'asc' | 'desc'` with fallback `'desc'`.
2. Initialize `sortKey = 'rate'` (was `null`) and `sortDir = defaultSortDir` (was hardcoded `'desc'`).
3. After the existing numeric-rate seed loop, call `updateAriaSort()` then `renderSort()` — this makes the arrow glyph and aria-sort visible immediately on page load without user interaction.

All existing wired surfaces (home EN/ES, region, crime-family) keep their descending default via the absent-attribute fallback. No regression.

### Task 2 — Safest-cities pages wired

Applied to both `safest-cities-in-chile.astro` (EN) and `es/comunas-mas-seguras-chile.astro` (ES):

- **Frontmatter:** `ratesByYear: Record<number, number>` added to the `communeRates` map by iterating `data.series.filter(!s.partial)` and assigning `s.rate_per_100k`.
- **Import:** `RankingTableEnhancer` imported (EN: `../components/`, ES: `../../components/`).
- **Table attrs:** `data-ranking-table data-rate-col="3" data-name-col="1" data-rate-format="round" data-locale="en|es" data-default-sort-dir="asc"` added. Column mapping: col0=#, col1=commune name, col2=region, col3=rate, col4=national rank.
- **Rows:** `data-rates={JSON.stringify(c.ratesByYear)}` on each `<tr>` in `<tbody>`. No `data-low-pop` (all rows are non-low-population).
- **Caption:** Sort hint appended inline ("Click column headers to sort." / "Haga clic en los encabezados de columna para ordenar.").
- **Enhancer mount:** `<RankingTableEnhancer locale="en|es" />` placed after closing `</div>` of `.ranking-table-wrapper`.
- **Style:** `-webkit-overflow-scrolling: touch;` added to `.ranking-table-wrapper` in both pages.

## Verification

- `cd site && npm run build && npm run validate` — 13/13 validators PASS.
- `@astrojs/check` passed (types generated cleanly at build start).
- No new npm dependencies; `package.json` unchanged.
- `i18n.ts` untouched — all required string keys already present.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is live from CEAD build-time JSON.

## Threat Flags

None — no new network endpoints, auth paths, or trust-boundary schema changes.

## Self-Check: PASSED

- [x] `site/src/components/RankingTableEnhancer.astro` — modified, committed 28b6c02
- [x] `site/src/pages/safest-cities-in-chile.astro` — modified, committed 973dca5
- [x] `site/src/pages/es/comunas-mas-seguras-chile.astro` — modified, committed 973dca5
- [x] Build exits 0; 13/13 validators pass
- [x] `defaultSortDir` appears twice in enhancer (declaration + usage in sortDir init)
- [x] `updateAriaSort()` and `renderSort()` invoked once outside click/change handlers
- [x] `data-ranking-table` and `data-default-sort-dir="asc"` present on both safest-cities tables
- [x] `RankingTableEnhancer` present in both safest-cities files
