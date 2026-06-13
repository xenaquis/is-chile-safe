---
phase: 03-leaflet-map-island
plan: "00"
subsystem: map-infrastructure
tags: [react, leaflet, topojson, geojson, validation, wave-0]
dependency_graph:
  requires: [02-astro-site-programmatic-pages]
  provides: [react-island-toolchain, commune-boundary-topojson, map-validator]
  affects: [site/astro.config.mjs, site/package.json, data/cead/geo/, site/scripts/validate/]
tech_stack:
  added:
    - "@astrojs/react@5.0.7"
    - "react@19.2.7 + react-dom@19.2.7"
    - "leaflet@1.9.4"
    - "@types/leaflet, @types/react, @types/react-dom"
  patterns:
    - "react() first in integrations array before sitemap()"
    - "GADM 4.1 L3 → mapshaper simplify → TopoJSON CUT-rekey pipeline"
    - "validator: TopoJSON budget + zero-React regression guard pattern"
key_files:
  created:
    - "site/scripts/validate/map.mjs"
    - "scripts/build-topojson.mjs"
    - "data/cead/geo/communes.topo.json"
  modified:
    - "site/astro.config.mjs"
    - "site/package.json"
    - "site/scripts/validate/all.mjs"
decisions:
  - "Skip react-leaflet entirely (React 19 incompatible with v4; v5 adds MapContainer only; D-05 mandates native L.geoJSON anyway)"
  - "Source GADM 4.1 Chile L3 (D-02 escape hatch: prototype had 56 slug-keyed features, unusable)"
  - "Antártica (12202) placeholder polygon at ~63°S Drake Passage (GADM lacks Antarctic territory; zero CEAD crime rates)"
  - "mapshaper visvalingam 0.05% + quantization=500 → 87.2 KB (under 100KB target)"
  - "map.mjs warns on absent map pages (Wave 1 creates them) rather than failing"
metrics:
  duration_minutes: 73
  completed: "2026-06-13T16:13:35Z"
  tasks_completed: 3
  files_created: 3
  files_modified: 3
---

# Phase 03 Plan 00: Map Infrastructure (Wave 0) Summary

React 19 + Leaflet 1.9 toolchain installed, 346-commune CUT-keyed TopoJSON committed at 87 KB, and map.mjs validator suite wired — Wave 0 infra gate cleared.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install React/Leaflet toolchain + react() integration | f4457b0 | site/package.json, site/astro.config.mjs |
| 2 | Build 346-commune CUT-keyed TopoJSON | c94b9fe | data/cead/geo/communes.topo.json, scripts/build-topojson.mjs |
| 3 | Add map.mjs validator + register in suite | 04ee116 | site/scripts/validate/map.mjs, site/scripts/validate/all.mjs |

## Verification Results

- `npx astro check` — 0 errors, 0 warnings, 4 hints (pre-existing)
- `node scripts/validate/map.mjs` — PASSED (TopoJSON budget + 346 features + CUT join + zero-React guard)
- `node scripts/validate/all.mjs` — 8/8 validators PASSED

## Deviations from Plan

### D-02 Override — Prototype geometry unusable (planned deviation per escape hatch)

**Rule: None (planned per PLAN.md critical_finding)**
- **Found during:** Task 2 planning
- **Issue:** `ischilesafe.com/geo-data.js` contains only 56 slug-keyed features. The plan explicitly noted this was the D-02 escape hatch condition: "Do NOT re-download a fresh dataset unless the prototype geometry proves unusable" — it is provably unusable.
- **Fix:** Downloaded GADM 4.1 Chile Level-3 (https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_CHL_3.json). Applied 3 manual name fixes and 1 placeholder polygon for Antártica.
- **Files modified:** scripts/build-topojson.mjs (documents source URL + pipeline), data/cead/geo/communes.topo.json (output)

### GADM Data Quality Fixes (3 issues + 1 missing commune)

| Issue | Fix |
|-------|-----|
| GADM "Calera" (Quillota, Valparaíso) | → La Calera CUT 5502 |
| GADM "Paihuano" (Elqui, Coquimbo) | → Paiguano CUT 4105 (CEAD canonical spelling) |
| GADM duplicate "Tocopilla" in Tarapacá/Tamarugal | → Pozo Almonte CUT 1401 (GADM data error) |
| Antártica (12202) absent from GADM entirely | → Placeholder polygon at ~63°S (population 151, zero crime rates) |

### react-leaflet intentionally omitted

**Rule: None (planned per PLAN.md + RESEARCH correction)**
- CLAUDE.md says "Pin to v4 for React 19 compat" — this is incorrect per RESEARCH.
- react-leaflet@4 peerDep is `"react": "^18.0.0"` — incompatible with React 19.
- react-leaflet@5.0.0 is React 19 compatible but adds only `<MapContainer>` wrapper.
- Decision: skip react-leaflet entirely; D-05 mandates native `L.geoJSON()` anyway.
- No functional impact: island will use `L.map(divRef.current)` directly.

### map.mjs Wave-1 tolerance

**Rule: None (design decision)**
- Map pages (map.astro, mapa.astro) are Wave 1 work. The validator warns (not fails) when those pages are absent.
- Wave 1 validators will upgrade these to hard failures once the pages are built.

## Known Stubs

None — this plan creates infrastructure only (no UI stubs). Map island UI is Wave 1.

## Threat Flags

None — no new network endpoints or auth paths introduced. TopoJSON sourced from public GADM dataset, re-keyed only with id + name from index.json (T-03-00-02 mitigated).

## Self-Check

- [x] `data/cead/geo/communes.topo.json` exists: 89,266 bytes, 346 features, Santiago CUT 13101 verified
- [x] `scripts/build-topojson.mjs` exists (47+ lines, documents source URL, re-runnable)
- [x] `site/scripts/validate/map.mjs` exists (passes exit 0)
- [x] `map.mjs` in VALIDATORS array of all.mjs
- [x] `site/astro.config.mjs` has `react()` before `sitemap()`; sitemap filter includes `/map/` and `/es/mapa/`
- [x] `site/package.json` has @astrojs/react, react, react-dom, leaflet; react-leaflet absent
- [x] Commits: f4457b0 (Task 1), c94b9fe (Task 2), 04ee116 (Task 3)

## Self-Check: PASSED
