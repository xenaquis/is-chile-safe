---
phase: 3
slug: leaflet-map-island
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 3 — Validation Strategy

> Interactive client-only React/Leaflet island. Build-output structural assertions verify the static shell, island mount, TopoJSON budget, and data wiring; interaction/geolocation/render-jank are manual-only (browser + device). See `03-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Node.js `node:test` + `assert` (build-output assertions, reuse Phase-2 `scripts/validate/`); `@astrojs/check` for typecheck |
| **Config file** | `site/astro.config.mjs` (add `@astrojs/react`); validators under `site/scripts/validate/` |
| **Quick run command** | `cd site && npx astro check` |
| **Full suite command** | `cd site && npm run build && node scripts/validate/all.mjs && node scripts/validate/map.mjs` |
| **Estimated runtime** | ~30–90 s (build + assertions) |

---

## Sampling Rate

- **After every task commit:** `cd site && npx astro check`
- **After every plan wave:** `npm run build && node scripts/validate/map.mjs`
- **Before `/gsd:verify-work`:** full build green + all assertions exit 0 + manual device pass (SC3)
- **Max feedback latency:** 90 s (automated); manual UAT separate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command / Assertion | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------------------|-------------|--------|
| 3-00-01 | 00 | 0 | (infra) | build | `@astrojs/react` + react/leaflet installed; `astro check` exits 0; content pages still ship zero React JS | ❌ W0 | ⬜ pending |
| 3-00-02 | 00 | 0 | MAP-06 | size | `data/cead/geo/communes.topo.json` exists and is < 100 KB | ❌ W0 | ⬜ pending |
| 3-01-01 | 01 | 1 | MAP-01 | structure | `/map/` + `/es/mapa/` built; each contains the island mount + `client:only` script ref; TopoJSON + payload fetched at runtime (referenced in island bundle) | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | MAP-02 | structure | year + crime-type filter controls present in island markup; 21 payload files (2005–2025) resolvable | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | MAP-03 | structure | commune-panel component present; fetches `comunas/{cut}.json`; inline SVG sparkline element present | ❌ W0 | ⬜ pending |
| 3-04-01 | 04 | 2 | MAP-04 | structure | incident-pins layer present; reads `incidents/current.json`; empty-state path when file absent (it is absent until Phase 5) | ❌ W0 | ⬜ pending |
| 3-04-02 | 04 | 2 | MAP-05 | structure | locate control present; Geolocation API + point-in-polygon code path present | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `@astrojs/react` integration added to `astro.config.mjs`; react@19, react-dom@19, leaflet@1.9.x, @types/leaflet installed (NO react-leaflet — incompatible with React 19; use pure `L.map()` per RESEARCH)
- [ ] GeoJSON→TopoJSON build step: simplify `ischilesafe.com/geo-data.js` (~222 KB) via mapshaper (visvalingam 12% keep-shapes) → `data/cead/geo/communes.topo.json` < 100 KB, features keyed by CUT (`id`)
- [ ] `site/scripts/validate/map.mjs` — assertions: /map/ + /es/mapa/ exist, island mount present, TopoJSON < 100 KB, content pages still zero-React-JS
- [ ] Confirm content pages (commune/region/crime) ship NO Leaflet/React after adding the integration (regression guard)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Choropleth renders 346 communes colored by incidence; year/crime filter recolors without reload | MAP-01, MAP-02 | Interactive canvas render not assertable from static HTML | `npm run dev`, open `/map/`, switch year + crime type, confirm recolor with no navigation |
| Click commune → panel with tasa/trend/rank/sparkline/family bars | MAP-03 | Click-driven fetch + render | Click 3 communes (high/low/low-pop), confirm panel data matches commune JSON |
| "Mostrar mi ubicación" highlights user commune | MAP-05 | Requires real geolocation permission | Grant location, confirm correct commune highlighted; deny → graceful toast |
| No jank on mid-range Android over 3G | MAP-06 (SC3) | Device + network throttle | Chrome DevTools 3G + mid-tier device or CPU 4× throttle; pan/zoom/filter must stay responsive |
| Incident pins empty state (Phase 5 absent) | MAP-04 | Depends on absent file | Confirm map shows graceful empty state, no console error, when `incidents/current.json` missing |

---

## Validation Sign-Off

- [ ] All tasks have automated build-assertion verify or Wave 0 dependencies (or are explicitly manual-only)
- [ ] Manual-only set is minimal and documented (interaction/geo/jank only)
- [ ] Wave 0 covers React/Leaflet integration + TopoJSON pipeline + map validator
- [ ] No watch-mode flags
- [ ] `nyquist_compliant: true` set after planner maps final task IDs

**Approval:** pending
