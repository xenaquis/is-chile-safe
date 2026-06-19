---
phase: 08-bug-fixes-data-correctness
plan: "01"
subsystem: frontend-templates
tags: [bugfix, rollout-gating, seo, ranking-tables]
dependency_graph:
  requires: []
  provides: [rollout-gated-region-ranking-EN, rollout-gated-region-ranking-ES, rollout-gated-crime-ranking-EN, rollout-gated-crime-ranking-ES]
  affects: [region/[slug].astro, es/region/[slug].astro, crime/[family].astro, es/delito/[family].astro]
tech_stack:
  added: []
  patterns: [loadRolloutCuts-as-Set-gate, displayedRows-filter-pattern, rollout-note-affordance]
key_files:
  created: []
  modified:
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
decisions:
  - displayedRows filter uses regionCommunes.find (region pages) or index.find (crime pages) to resolve slug→CUT; no slug list hardcoded
  - hiddenCount > 0 guard prevents empty affordance rendering when all rollout communes are visible
  - Per-table rank (#i+1) in crime pages is over displayedRows — intentional per D-03; national #N of 346 lives only on commune/panel pages
metrics:
  duration: "8m"
  completed: "2026-06-15"
  tasks: 2
  files: 4
---

# Phase 08 Plan 01: Rollout-Gate Ranking Tables Summary

**One-liner:** Gate all 4 ranking templates (region EN/ES, crime EN/ES) to rollout-CUT rows via `loadRolloutCuts()`, eliminating F-005 (ranking tables linking to non-rollout commune pages that 404).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Gate region ranking rows to rollout CUTs (EN + ES) | 451a61a | site/src/pages/region/[slug].astro, site/src/pages/es/region/[slug].astro |
| 2 | Gate crime ranking rows to rollout CUTs (EN + ES) | 1f2a925 | site/src/pages/crime/[family].astro, site/src/pages/es/delito/[family].astro |

## What Was Built

All 4 ranking templates now:

1. Import `loadRolloutCuts` from `lib/data.ts`
2. Build `const rolloutCuts = new Set(loadRolloutCuts())` after ranking assembly
3. Filter `displayedRows = rankingRows.filter(row => rolloutCuts.has(meta.cut))`
4. Pass `displayedRows` to `<CommuneRankingTable>` (region pages) or map `displayedRows` in `<tbody>` (crime pages)
5. Render `<p class="rollout-note">` affordance when `hiddenCount > 0` with locale-appropriate text

National rank denominators (`#N of 346`, `#N of 16 regions`) are untouched — only displayed rows are gated.

## Deviations from Plan

None — plan executed exactly as written. Added `.rollout-note` CSS class to all 4 templates (styling for the affordance element — implicitly required by the plan's D-03 affordance directive).

## Known Stubs

None. All data is wired from real `rollout.json` + `index.json` build-time sources.

## Threat Flags

None. No new network endpoints, auth paths, or trust boundaries introduced. Confirmed T-08-01 mitigation in place: only numeric expressions (`displayedRows.length`, `rankingRows.length`) and static string literals interpolated via Astro `{...}` (auto-escaped). No `set:html`, no user input.

## Self-Check: PASSED

- site/src/pages/region/[slug].astro — modified, contains loadRolloutCuts + displayedRows
- site/src/pages/es/region/[slug].astro — modified, contains loadRolloutCuts + displayedRows
- site/src/pages/crime/[family].astro — modified, contains loadRolloutCuts + displayedRows
- site/src/pages/es/delito/[family].astro — modified, contains loadRolloutCuts + displayedRows
- Commits 451a61a and 1f2a925 verified in git log
- Build passed (100 pages, 0 errors) on both task verifications
