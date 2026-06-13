---
phase: 03-leaflet-map-island
plan: "02"
subsystem: map-island-filters-panel
tags: [react, leaflet, choropleth, filters, panel, sparkline]
dependency_graph:
  requires: ["03-01"]
  provides: ["MAP-02", "MAP-03"]
  affects: ["site/src/components/map/MapIsland.tsx", "site/src/components/map/"]
tech_stack:
  added: []
  patterns:
    - setStyle-in-place recolor (D-12 — never re-mount L.geoJSON)
    - quantile-breaks client-side (D-10 — chroma-js, no extra fetch)
    - fetch-on-open panel (D-13 — comunas/{cut}.json loaded when panel opens)
    - inline-SVG sparkline (WR-05 — step derived from width, no charting lib)
key_files:
  created:
    - site/src/components/map/FiltersRow.tsx
    - site/src/components/map/SearchBox.tsx
    - site/src/components/map/MapTopbar.tsx
    - site/src/components/map/ResultPanel.tsx
    - site/src/components/map/PanelSparkline.tsx
    - site/src/components/map/PanelFamilyBars.tsx
    - site/src/components/map/IncidentsList.tsx
    - site/src/components/map/Toast.tsx
  modified:
    - site/src/components/map/MapIsland.tsx
    - site/src/components/map/ChoroplethLayer.ts
    - site/src/components/map/map.css
decisions:
  - "CHIP_DEFS carries both display order and catalog by_family index — chip order != array index"
  - "ResultPanel converts series.by_family RECORD to catalog-indexed ARRAY via CATALOG_KEY_ORDER"
  - "Year filter re-fetches map-payload-{year}.json then calls applyStyleMap in place (no layer remount)"
  - "Crime chip filter uses payloadRef.current (no extra fetch) and buildStyleMapFromFamily"
  - "Toast padding 10px 20px per UI-SPEC checker FLAG (not 8px)"
  - "12px mobile-legend font size is a named exception per UI-SPEC"
metrics:
  duration: "~45 min"
  completed: "2026-06-13"
  tasks: 3
  files: 11
---

# Phase 3 Plan 02: Filters + ResultPanel Summary

Year filter loads map-payload-{year}.json and recolors via setStyle-in-place; crime-type chips recolor from by_family[] client-side quantile breaks; commune click opens ResultPanel fetching comunas/{cut}.json with inline-SVG sparkline and 7-family breakdown.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | FiltersRow + SearchBox + MapTopbar + year/crime recolor wiring | 10b6418 | FiltersRow.tsx, SearchBox.tsx, MapTopbar.tsx, MapIsland.tsx, ChoroplethLayer.ts, map.css |
| 2 | PanelSparkline + PanelFamilyBars + IncidentsList + Toast | 86bb4d9 | PanelSparkline.tsx, PanelFamilyBars.tsx, IncidentsList.tsx, Toast.tsx, map.css |
| 3 | ResultPanel + wire into MapIsland; build + validators green | 20826b6 | ResultPanel.tsx, MapIsland.tsx |

## What Was Built

- **FiltersRow**: year `<select>` (2025→2005, newest-first), 8 chips (Todos + 7 families in UI-SPEC display order: vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas), events toggle chip. CHIP_DEFS carry both display order and catalog `by_family` array index (0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades).

- **SearchBox**: prefix-filter dropdown over data/cead/meta/index.json (346 communes). Client-side `Array.filter` only — no eval, no server query (T-03-02-03). Inline SVG SearchIcon and LocateIcon (no icon lib).

- **MapTopbar**: composes SearchBox + FiltersRow in the topbar overlay.

- **MapIsland extended**: year change fetches `/data/cead/map-payload-{year}.json` (graceful safeFetch; toast on null), rebuilds styleMapRef, calls `applyStyleMap` in place (D-12). Crime chip change rebuilds styleMapRef from `payloadRef.current` via `buildStyleMapFromFamily` — no extra fetch (D-10). `selectCommune` flies map to polygon bounds and highlights border. ResultPanel rendered when `selected` is set; close resets polygon style.

- **ChoroplethLayer**: `buildStyleMapFromFamily(comunas, familyIndex)` added — computes quantile breaks client-side, assigns INCIDENCE_COLORS by level.

- **PanelSparkline**: Exact React port of Sparkline.astro with WR-05 width/step logic; active-year bar uses `primaryColor` prop; partial-year at 0.5 opacity; aria-hidden.

- **PanelFamilyBars**: Ports FamilyBreakdownBars.astro. Receives catalog-indexed `byFamily: number[]`, maps index→key, reorders to FAMILY_ORDER (vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas). Bar width is CSS `%` string; bar fill `var(--s{level})`. Featured families (vida, propiedad) get `--primary` accent dot.

- **IncidentsList**: Event rows with `rel="noopener noreferrer"` external links (T-03-02-01). Empty state: em-dash.

- **Toast**: 3000ms auto-dismiss, `role="status"`, `aria-live="polite"`. Padding 10px 20px per UI-SPEC checker FLAG.

- **ResultPanel**: Fetches `comunas/{cut}.json` on `cut` change. Skeleton loading (aria-busy=true). Renders in UI-SPEC order: panel head (name h2, region, 44px close), level chip + CEAD badge, stat card (rate 28px/700, es-CL format), mini-stats (trend chip + national rank), sparkline section, family breakdown (converts series.by_family RECORD → catalog-indexed ARRAY), incidents, CTA link to Phase-2 commune page, official CEAD source row.

- **map.css**: Search box, dropdown, locate button, family bars, panel content, incidents, skeleton, toast styles added. 12px mobile-legend exception documented.

## Deviations from Plan

None — plan executed exactly as written.

## Checker FLAGs Folded

- **Toast padding**: UI-SPEC specifies `padding: 10px 20px` — implemented exactly. Comment in PATTERNS.md had "10px not 8px" — honored.
- **12px mobile legend**: Named exception comment added to map.css per UI-SPEC instruction.

## Known Stubs

- Events toggle chip is rendered and wired but no-op (fires toast "Geolocation coming soon") — Wave 3 will wire full behavior per plan design.
- LocateButton in SearchBox calls `onLocate` which shows placeholder toast — Wave 3 wires `UserLocationMarker`.
- These are intentional Wave-2 stubs; Wave 3 plan (03-03) resolves them.

## Threat Surface Scan

No new network endpoints or auth paths beyond what the plan's threat model covers:
- T-03-02-01 (XSS): ResultPanel/IncidentsList use React JSX auto-escaping; no dangerouslySetInnerHTML.
- T-03-02-02 (fetch paths): Only hardcoded same-origin `/data/cead/comunas/{cut}.json` and `/data/cead/map-payload-{year}.json`.
- T-03-02-03 (search): Client-side filter over known 346-commune index only.

## Self-Check: PASSED

Files created/verified:
- site/src/components/map/FiltersRow.tsx ✓
- site/src/components/map/SearchBox.tsx ✓
- site/src/components/map/MapTopbar.tsx ✓
- site/src/components/map/ResultPanel.tsx ✓
- site/src/components/map/PanelSparkline.tsx ✓
- site/src/components/map/PanelFamilyBars.tsx ✓
- site/src/components/map/IncidentsList.tsx ✓
- site/src/components/map/Toast.tsx ✓

Commits verified: 10b6418, 86bb4d9, 20826b6 — all present in git log.
Build: 74 pages, 0 errors.
Validators: 8/8 passed (structure, commune, rollout, region, crime, hreflang, schema, map).
