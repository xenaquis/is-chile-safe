---
phase: 24-rankings-ux-dynamic-sortable-tables-and-visual-polish
plan: "03"
subsystem: frontend
tags: [rankings, ux, gap-closure, static-html, home]
dependency_graph:
  requires: [24-02]
  provides: [GAP-24A-closed]
  affects: [CommuneRankingTable, home-EN, home-ES]
tech_stack:
  added: []
  patterns:
    - "Optional boolean prop gating data-attrs and enhancer mount in Astro component"
key_files:
  created: []
  modified:
    - site/src/components/CommuneRankingTable.astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
decisions:
  - "Home ranking previews are static pre-sorted teasers (sortable=false); no implied sort affordance"
  - "sortable prop defaults to true so all existing callers (region pages) are unchanged without modification"
metrics:
  duration: "~8m"
  completed: "2026-06-20"
  tasks: 2
  files_modified: 3
---

# Phase 24 Plan 03: GAP-24A Closure — Home Teaser Tables as Static HTML Summary

One-liner: Added `sortable` boolean prop to CommuneRankingTable (default true) and passed `sortable={false}` on the four home preview tables, eliminating the vestigial `data-ranking-table` flag from the home page and closing GAP-24A.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add sortable prop; gate flag + enhancer behind it | 5fbf92a | site/src/components/CommuneRankingTable.astro |
| 2 | Pass sortable={false} on four home teaser tables | d713b24 | site/src/pages/index.astro, site/src/pages/es/index.astro |

## What Was Built

**Task 1 — CommuneRankingTable.astro sortable prop:**
- Added `sortable?: boolean` to the Props interface with default `true`
- When `sortable=false`: the `<table>` emits no `data-ranking-table`, no `data-rate-col`, no `data-name-col`, no `data-rate-format`; rows omit `data-rates` and `data-low-pop`; `<RankingTableEnhancer>` is not mounted
- When `sortable=true` (default): markup is byte-identical to prior behavior — all existing callers (region pages, crime-ranking pages, safest-cities) required no changes

**Task 2 — Home teaser tables:**
- `index.astro` (EN): lowestRows and highestRows tables now pass `sortable={false}`
- `es/index.astro` (ES): lowestRows and highestRows tables now pass `sortable={false}`
- The "See full ranking" / "Ver ranking completo" links remain intact pointing to the full sortable pages

## Verification

- Build + validate: 13/13 validators PASS on both tasks
- `dist/index.html`: 0 occurrences of `data-ranking-table` (confirmed)
- `dist/es/index.html`: 0 occurrences of `data-ranking-table` (confirmed)
- `dist/region/los-lagos/index.html`: 1 occurrence of `data-ranking-table` (regression guard — unchanged)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — changes are purely presentational HTML attribute gating; no new network endpoints, auth paths, or data flows introduced.

## Self-Check: PASSED

- [x] CommuneRankingTable.astro modified with sortable prop (5fbf92a)
- [x] index.astro modified (d713b24)
- [x] es/index.astro modified (d713b24)
- [x] Build passes (13/13 validators)
- [x] Home emits no data-ranking-table
- [x] Region pages still emit data-ranking-table
