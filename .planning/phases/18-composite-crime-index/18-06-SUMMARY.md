---
phase: 18-composite-crime-index
plan: "06"
subsystem: map-ui
tags: [composite-index, result-panel, bug-fix, gap-closure]
dependency_graph:
  requires: [18-01, 18-02, 18-03, 18-04, 18-05]
  provides: [CI-05-popup]
  affects: [site/src/components/map/ResultPanel.tsx]
tech_stack:
  added: []
  patterns: [COMPOSITE_YEAR constant mirrors commune/[slug].astro pattern]
key_files:
  modified:
    - site/src/components/map/ResultPanel.tsx
decisions:
  - "COMPOSITE_YEAR = 2024 added as module-level constant; must be updated alongside commune/[slug].astro when new index vintages are published"
metrics:
  duration: "5 minutes"
  completed: "2026-06-19"
  tasks_completed: 1
  tasks_total: 1
---

# Phase 18 Plan 06: Composite Block Year-Key Fix Summary

**One-liner:** Fixed ResultPanel composite block reading wrong year key (2025) — now reads COMPOSITE_YEAR=2024 constant, making score/band/rank/caveat visible on commune click in default view.

## What Was Built

Single surgical change to `site/src/components/map/ResultPanel.tsx`:

1. Added module-level constant `const COMPOSITE_YEAR = 2024` (with comment linking to commune/[slug].astro:COMPOSITE_YEAR as the source of truth to keep in sync).
2. Changed line 267 from `data.composite_index?.[String(year)]` to `data.composite_index?.[String(COMPOSITE_YEAR)]`.

The `year` variable (active rate-series year, initialised to 2025 in MapIsland.tsx) is untouched — it continues to drive the rate stat card at lines 303-304.

## Gap Closed

**Gap 1 (CI-05):** The composite section in ResultPanel was guarded by `if (!ci) return null`. Since `year` starts at 2025 and commune JSON stores composite data only under key "2024", the lookup always returned `undefined`, the guard fired, and clicking any commune in the default composite view showed no score, band, rank, or caveat. The fix makes `ci` resolve correctly, so the full composite block renders.

## Verification

- `COMPOSITE_YEAR` present in file: confirmed (line 41).
- `String(COMPOSITE_YEAR)` used in composite block: confirmed (line 267).
- No remaining `composite_index?.[String(year)]` in file: confirmed.
- `npx astro check`: 9 pre-existing errors (none in ResultPanel.tsx); 0 new errors.
- Rate stat card `year` usages at lines 303-304: unchanged.

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | d203030 | fix(18-06): key composite block on COMPOSITE_YEAR=2024 not active series year |

## Self-Check: PASSED

- `site/src/components/map/ResultPanel.tsx` modified and committed at d203030.
- Grep confirms `COMPOSITE_YEAR = 2024` and `String(COMPOSITE_YEAR)` present; no `composite_index?.[String(year)]` remains.
