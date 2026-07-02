---
phase: 25
plan: "04"
subsystem: map
tags: [map, mobile, a11y, security, leaflet]
dependency_graph:
  requires: [25-02]
  provides: [map-framing, incident-pins, mobile-legend]
  affects: [MapIsland.tsx, IncidentPinLayer.ts, Legend.tsx, MapTopbar.tsx, map.css, global.css]
tech_stack:
  added: []
  patterns: [fitBounds, maxBounds, details/summary collapse, CSS static position at breakpoint]
key_files:
  created: []
  modified:
    - site/src/components/map/MapIsland.tsx
    - site/src/components/map/IncidentPinLayer.ts
    - site/src/components/map/Legend.tsx
    - site/src/components/map/MapTopbar.tsx
    - site/src/components/map/map.css
    - site/src/styles/global.css
decisions:
  - fitBounds continental Chile bbox replaces hard-coded setView zoom 5
  - Mode-toggle moved into MapTopbar modeToggle prop to enable CSS stacking at 480px
  - Legend uses dual desktop/mobile blocks (legend-desktop/legend-mobile) toggled by media query
metrics:
  duration: "~20m"
  completed: "2026-07-02"
  tasks: 3
  files: 6
---

# Phase 25 Plan 04: Map Framing, Incident Pins, Mobile Legend Summary

**One-liner:** fitBounds Chile continental bbox + purple `--pin` incident pins with aria-label + collapsible mobile legend and pills stacking row at ≤480px.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Map framing + ?cut= guard | 934b564 | MapIsland.tsx |
| 2 | Distinct incident pins + accessible name + legend pin row | f162d7f | global.css, map.css, IncidentPinLayer.ts, Legend.tsx |
| 3 | Collapsible mobile legend + pill stacking ≤480px | fb75244 | MapTopbar.tsx |

## What Was Built

**Task 1 — Map framing + security guard:**
- Replaced `map.setView([-35.7, -71.8], 5)` with `map.fitBounds([[-55.9, -75.7], [-17.5, -66.4]], { padding: [20, 20] })`
- Added `map.setMaxBounds([[-60, -80], [-14, -60]])` and `map.setMinZoom(4)`
- Guarded `?cut=` URL param with `/^\d{5}$/` regex before calling `selectCommune` — invalid params no longer trigger a 404 fetch (T-25-04-URL mitigated)

**Task 2 — Incident pin color + accessibility:**
- Added `--pin: #6d28d9` design token to `:root` in `global.css`
- Updated `.ev-dot` and `.ev-dot-mini` in `map.css` to use `var(--pin)` with white border
- Added `role="img" aria-label="${title}"` to incident `divIcon` html and `title: title` to marker options — XSS boundary held via existing `escHtml()` (T-25-04-XSS mitigated)
- Added `showIncidents` prop to `Legend` component; when active, appends a pin swatch row with "Reported incidents"/"Incidentes reportados" label below the choropleth bands

**Task 3 — Mobile responsive fixes:**
- Moved mode-toggle div from inline MapIsland.tsx into `MapTopbar` via `modeToggle?: React.ReactNode` prop so that CSS can stack it at ≤480px
- Added `legend-desktop`/`legend-mobile` dual-block approach: desktop shows expanded block, mobile shows `<details>`/`<summary>` collapsed view
- Summary toggle labels: "Crime Index ▸"/"Crime Index ▾" (EN) and "Índice delictivo ▸"/"Índice delictivo ▾" (ES)
- Added `@media (max-width: 480px)` rules: `.map-topbar-row1` column flex, `.mode-toggle` position:static

## Verification

`npm run build && npm run validate` — 14/14 validators passed. 834 pages built.

## Deviations from Plan

### Auto-added (Rule 2)

**1. [Rule 3 - Blocker] Mode-toggle moved into MapTopbar via prop**
- **Found during:** Task 3
- **Issue:** `.mode-toggle` was a sibling of `MapTopbar` in the DOM (not inside `.map-topbar-row1`), making a CSS-only stack impossible
- **Fix:** Added `modeToggle?: React.ReactNode` prop to MapTopbar and moved the div there; plan anticipated this ("Implement in map.css and MapTopbar.tsx markup only if the current structure prevents the CSS-only stack")
- **Files modified:** MapTopbar.tsx, MapIsland.tsx
- **Commit:** fb75244

## Threat Surface Scan

All threat register items from the plan were addressed:

| ID | Mitigation |
|----|-----------|
| T-25-04-URL | `/^\d{5}$/` guard in MapIsland.tsx before selectCommune |
| T-25-04-XSS | `escHtml()` applied to incident title; already escaped `title` variable reused for aria-label |
| T-25-SC | No new packages installed |

No new threat surface introduced.

## Self-Check: PASSED

- `site/src/components/map/MapIsland.tsx` — fitBounds, setMaxBounds, setMinZoom, /d{5}/ guard: present
- `site/src/styles/global.css` — `--pin: #6d28d9`: present
- `site/src/components/map/map.css` — `var(--pin)`, ≤480px media queries: present
- `site/src/components/map/IncidentPinLayer.ts` — `aria-label`, `escHtml`: present
- `site/src/components/map/Legend.tsx` — "Reported incidents"/"Incidentes reportados": present
- Commits 934b564, f162d7f, fb75244: verified in git log
