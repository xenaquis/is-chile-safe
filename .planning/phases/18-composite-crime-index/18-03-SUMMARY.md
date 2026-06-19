---
phase: 18-composite-crime-index
plan: "03"
subsystem: frontend/map
tags: [composite-index, choropleth, mode-toggle, leaflet, D-05, D-06, CI-07]
dependency_graph:
  requires: [data/cead/map-payload.json (ci field from plan 02), site/src/components/map/ChoroplethLayer.ts, site/src/components/map/MapIsland.tsx]
  provides: [buildStyleMapFromCompositeIndex(), mode toggle UI, mode prop seam for Plan 04]
  affects: [site/src/components/map/ChoroplethLayer.ts, site/src/components/map/MapIsland.tsx, site/src/components/map/map.css, site/src/components/map/Legend.tsx, site/src/components/map/ResultPanel.tsx]
tech_stack:
  added: []
  patterns: [precomputed-ci-level (no client quantile recompute), applyStyleMap restyle (never re-mount), mode-state-owned-by-MapIsland (D-06 seam)]
key_files:
  created: []
  modified:
    - site/src/components/map/ChoroplethLayer.ts (ci field on CommunaPayload; buildStyleMapFromCompositeIndex)
    - site/src/components/map/MapIsland.tsx (mode toggle state; composite default; mode prop to ResultPanel; legend title)
    - site/src/components/map/map.css (.mode-toggle class)
    - site/src/components/map/Legend.tsx (optional title prop)
    - site/src/components/map/ResultPanel.tsx (optional mode prop added to Props interface)
decisions:
  - "Map defaults to composite index mode (D-05) — buildStyleMapFromCompositeIndex called on initial data load, not buildStyleMapFromLevel"
  - "Legend title controlled via optional title prop on Legend component — MapIsland passes Crime Index / Indice Delictivo in composite mode, undefined in family mode (falls back to Reported incidence)"
  - "mode-toggle positioned absolute top-right (z-index 801) outside MapTopbar to avoid layout impact on existing filters-row"
  - "ResultPanel.mode typed as optional ('composite' | 'family') — Plan 04 reads it; current ResultPanel ignores it until Plan 04 implements the composite block"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-19T20:30:00Z"
  tasks_completed: 2
  files_created: 0
  files_modified: 5
---

# Phase 18 Plan 03: Composite Index Choropleth Mode Summary

**One-liner:** Added composite index choropleth mode (default) with a two-chip toggle in MapIsland, building styles from precomputed ci levels (no client recompute), mode-aware legend title, and mode prop seam to ResultPanel for Plan 04.

## What Was Built

### Task 1: ci field on CommunaPayload + buildStyleMapFromCompositeIndex()

- Extended `CommunaPayload` interface: added `ci: number | null` after `homicide_count`.
- Added `buildStyleMapFromCompositeIndex(comunas)` in `ChoroplethLayer.ts`:
  - Reads `c.ci` directly — no client-side quantile recompute (pipeline pre-computed the level).
  - `level = c.ci ?? 3` fallback for null communes.
  - `fillOpacity c.ci === null ? 0.25 : 0.55` visually distinguishes no-data communes (T-18-09).
  - Reuses `INCIDENCE_COLORS` palette unchanged.

### Task 2: MapIsland toggle + mode prop + legend title + map.css

- Added `mode` state (`'composite' | 'family'`) defaulting to `'composite'` (D-05).
- Initial data load now calls `buildStyleMapFromCompositeIndex` instead of `buildStyleMapFromLevel`.
- Two `.chip` toggle buttons rendered in a `.mode-toggle` div:
  - EN labels: "Index" / "By crime"; ES labels: "Índice" / "Por delito".
  - Active chip gets `.chip.active` (background `var(--primary)`, color `#fff`; 44px height via existing `.chip`).
  - Toggle calls `applyStyleMap()` — never re-mounts the layer (D-12).
- Year filter and crime-family effects updated to branch on `mode` first.
- `Legend` component: added optional `title` prop; MapIsland passes "Crime Index" / "Índice Delictivo" in composite mode.
- In composite mode legend `breaks` are passed as `undefined` (no numeric bands — the legend shows qualitative levels).
- `ResultPanel` Props interface: added optional `mode?: 'composite' | 'family'` prop — Plan 04 reads this to gate the composite score block (D-06 wiring seam).
- `map.css`: added `.mode-toggle { display: flex; gap: 4px; }` (no new CSS file).

## Key Numbers

- Files modified: 5
- New functions exported: 1 (buildStyleMapFromCompositeIndex)
- astro check: 9 pre-existing errors (RankingRow / news.astro — unchanged from baseline); 0 new errors
- Build: 791 pages, completed in ~22s

## Deviations from Plan

### Auto-adjusted Implementation Details

**1. [Rule 2 - Missing critical functionality] Legend numeric bands suppressed in composite mode**
- **Found during:** Task 2
- **Issue:** The composite index levels (1-5) are ordinal ranks, not quantile rate ranges. Showing the existing rate-range bands (computed from `breaks`) when in composite mode would be misleading — the bands describe per-100k rates not index levels.
- **Fix:** Pass `breaks={mode === 'composite' ? undefined : breaks}` to Legend. In composite mode the legend shows only qualitative swatch labels without numeric ranges.
- **Files modified:** site/src/components/map/MapIsland.tsx
- **Commit:** 4c044f5

**2. [Rule 2 - Missing functionality] Legend title prop added to Legend component**
- **Found during:** Task 2
- **Issue:** Legend hardcoded its title string internally; no way for MapIsland to override it per mode without prop drilling or lifting.
- **Fix:** Added optional `title?: string` prop to Legend; falls back to existing default title when undefined. MapIsland passes the composite title only when in composite mode.
- **Files modified:** site/src/components/map/Legend.tsx
- **Commit:** 4c044f5

## Threat Surface Scan

No new network endpoints or auth paths introduced. All changes are pure client-side UI state.

Mitigations applied:
- T-18-08: Uses neutral 5-level incidence palette (not red/green ramp); legend titled "Crime Index" not "Safety Index".
- T-18-09: `level = c.ci ?? 3` fallback; null → dimmed 0.25 opacity; INCIDENCE_COLORS index bounded 0-4.

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| site/src/components/map/ChoroplethLayer.ts contains buildStyleMapFromCompositeIndex | FOUND |
| CommunaPayload declares ci: number \| null | FOUND |
| MapIsland default mode is 'composite' | FOUND |
| mode prop passed to ResultPanel | FOUND |
| .mode-toggle in map.css | FOUND |
| Commit b133569 (Task 1) | FOUND |
| Commit 4c044f5 (Task 2) | FOUND |
| npx astro check: 0 new errors | PASSED |
| npm run build: 791 pages | PASSED |
