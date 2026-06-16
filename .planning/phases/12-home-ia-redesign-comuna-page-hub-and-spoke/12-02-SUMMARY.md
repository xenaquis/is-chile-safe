---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "02"
subsystem: map-island
tags: [map, deeplink, url-params, leaflet]
dependency_graph:
  requires: []
  provides: [map-focus-param-D-08]
  affects: [site/src/components/map/MapIsland.tsx]
tech_stack:
  added: []
  patterns: [URLSearchParams, setTimeout-for-Leaflet-getBounds]
key_files:
  modified:
    - site/src/components/map/MapIsland.tsx
decisions:
  - "Use setTimeout(100ms) after mountChoroplethLayer rather than a separate useEffect so polyIdxRef is guaranteed populated"
  - "focusCut treated as opaque string passed only to Map.get lookup — no DOM injection (T-12-02 mitigated)"
metrics:
  duration: "~5 minutes"
  completed: "2026-06-15"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
---

# Phase 12 Plan 02: Map Island ?cut= Focus Param Summary

**One-liner:** Added `?cut=<CUT>` deep-link focus to Leaflet MapIsland by reading URLSearchParams inside `loadData()` after `mountChoroplethLayer()` completes, calling `selectCommune` via `setTimeout(100ms)`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Read ?cut= and select commune at end of loadData() | 305558d | site/src/components/map/MapIsland.tsx (+6 lines) |

## Implementation Details

Inside the existing `if (!cancelled && mapRef.current)` guard in `loadData()`, immediately after `layerRef.current = mountChoroplethLayer(...)` completes:

```typescript
// D-08: focus commune from ?cut= URL param (opaque string — Map lookup only, no DOM injection)
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut) {
  setTimeout(() => selectCommune(focusCut), 100);
}
```

Placement rationale: `polyIdxRef` (indexed by CUT string) is only populated after `mountChoroplethLayer()` returns. A separate `useEffect([mapReady])` would fire before polygons are loaded. The `setTimeout(100ms)` allows Leaflet to finish rendering polygons so `getBounds` is valid (RESEARCH Pitfall 2).

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface

T-12-02 mitigated as planned: `focusCut` passed only to `selectCommune` which does `polyIdxRef.current.get(cut)` (Map lookup) + conditional `flyToBounds`. No innerHTML, no eval, no server round-trip. Unknown CUT → `get` returns `undefined` → no flight (safe no-op).

## Known Stubs

None.

## Verification

- `npm run check`: 0 errors, 0 warnings (17 hints pre-existing)
- `npm run build`: 772 pages built successfully in 34.9s
- Manual smoke deferred to 12-06 phase gate: `/map/?cut=13101` should fly to Santiago; `/map/` unchanged; `/map/?cut=zzz` no crash

## Self-Check: PASSED

- site/src/components/map/MapIsland.tsx — modified and contains `URLSearchParams(window.location.search).get('cut')` inside `loadData()`
- Commit 305558d exists in git log
