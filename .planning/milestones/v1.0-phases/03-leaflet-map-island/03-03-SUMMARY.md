---
phase: 03-leaflet-map-island
plan: "03"
subsystem: map-island
tags: [geolocation, incident-pins, news-layer, point-in-polygon, wave-3]
dependency_graph:
  requires: ["03-02"]
  provides: ["MAP-04", "MAP-05"]
  affects: ["site/src/components/map/MapIsland.tsx"]
tech_stack:
  added: []
  patterns:
    - "Ray-cast point-in-polygon (Polygon + MultiPolygon) for geolocation commune identification"
    - "Graceful 404 fetch pattern for not-yet-deployed incidents/current.json"
    - "L.divIcon for DOM-based user-dot and ev-dot markers (no default marker icon)"
    - "HTML escaping before Leaflet bindPopup interpolation (XSS mitigation)"
key_files:
  created:
    - site/src/components/map/UserLocationMarker.ts
    - site/src/components/map/IncidentPinLayer.ts
  modified:
    - site/src/components/map/MapIsland.tsx
decisions:
  - "D-14 implemented: true ray-cast PiP replaces prototype centroid-distance nearestComuna"
  - "D-15 confirmed: absent incidents/current.json -> graceful toast, null return, no console error"
  - "D-16 confirmed: user-dot and ev-dot are DOM-based L.marker/L.divIcon (not canvas renderer)"
  - "incidents/current.json schema defined in IncidentPinLayer.ts JSDoc for Phase 5 contract"
metrics:
  duration: "25m"
  completed: "2026-06-13"
  tasks_automated: 2
  tasks_checkpoint: 1
  files_created: 2
  files_modified: 1
---

# Phase 3 Plan 03: Geolocation + Incident Pin Layer Summary

**One-liner:** Geolocation via Geolocation API + ray-cast PiP for commune highlight (MAP-05), and graceful NEWS incident-pin layer with HTML-escaped divIcon popups (MAP-04); build and all 8 validators green.

## What Was Built

### Task 1 — UserLocationMarker.ts + MapIsland wiring (committed d6f1d62)

Created `site/src/components/map/UserLocationMarker.ts` with:

- `locate(map, geoFeatures, userRef, onSelectCut, onToast, lang)` — triggers `navigator.geolocation.getCurrentPosition` with 5000 ms timeout. On success: Chile bounds check (lat -56.5 to -17, lng -76.5 to -66); inside → PiP → `onSelectCut(cut)` + `flyTo` zoom 12 + success toast. Outside → simulate Santiago + approximate toast. Permission denied → graceful toast, no crash. Geolocation unavailable → silent Santiago simulation.
- `pointInPolygon(lat, lng, features)` — O(features × rings) ray-cast; handles `Polygon` and `MultiPolygon` via `ringContains` and `containsPoint`. GeoJSON coordinate convention [lng, lat] respected.
- `ringContains(ring, pt)` — classic ray-cast algorithm.
- User-dot uses `L.divIcon({ className:'', html:'<div class="user-dot"></div>', iconSize:[18,18] })` — Pitfall 7 compliance; no default marker icon 404.

MapIsland.tsx changes:
- Added `eventsRef` and `userRef` to refs.
- `onLocate` now calls `locate()` with `featuresRef.current`, `userRef`, `selectCommune`, `setToast`, `lang` — replacing the Wave-2 placeholder toast.
- Locate button aria-label `"Show my location"` / `"Mostrar mi ubicación"` already in static hidden sentinel (present from Wave 1; validator passes).

### Task 2 — IncidentPinLayer.ts + events toggle wiring (committed 90a4552)

Created `site/src/components/map/IncidentPinLayer.ts` with:

- `fetchAndMountIncidents(map, lang, onToast)` — fetches `/data/incidents/current.json` (not yet deployed). `res.ok === false` (404) or fetch throw → localized "Capa de noticias próximamente"/"News layer coming soon" toast, returns `null`, no `console.error` (D-15). When file present: builds `L.layerGroup` of `.ev-dot` divIcon markers; each `bindPopup` with CEAD badge, approx-location badge, localized title, date, outlet, and source link `target="_blank" rel="noopener noreferrer"`.
- HTML escaping via `escHtml()` applied to title, outlet, date before popup interpolation (T-03-03-02).
- `safeUrl()` rejects non-http/https schemes to prevent `javascript:` injection.
- Incidents schema contract documented in JSDoc for Phase 5 producer.

MapIsland.tsx changes:
- Added `showEvents` useEffect: toggle on → `fetchAndMountIncidents` → store layer in `eventsRef`; toggle off → remove layer from map and clear ref.

### incidents/current.json schema (Phase 5 contract)

```json
{
  "generated": "ISO-8601 timestamp",
  "window_days": 7,
  "incidents": [
    {
      "id": "unique-id",
      "cut": "13101",
      "lat": -33.44,
      "lng": -70.65,
      "title_es": "Titular en español",
      "title_en": "Headline in English",
      "date": "YYYY-MM-DD",
      "outlet": "BioBio Chile",
      "url": "https://...",
      "family": "propiedad"
    }
  ]
}
```

## Verification

- `npx astro check`: 0 errors (Task 1).
- `npm run build && node scripts/validate/all.mjs`: 8/8 validators pass (Task 2).
  - map.mjs: TopoJSON budget, 346 features, CUT join, EN/ES map pages, island marker, locate aria-labels, zero-React + zero-Leaflet guard on content pages — all PASS.

## Task 3 — Human UAT Checkpoint (OPEN / PENDING)

**Status: OPEN — awaiting manual browser + device verification.**

The automated tasks are complete and committed. Task 3 is a `checkpoint:human-verify` requiring manual interaction checks that static assertions cannot cover:

1. MAP-01: All 346 communes render colored; no white/transparent polygons.
2. MAP-02: Year selector + crime-type chip recolor with no page reload.
3. MAP-03: Clicking 3 communes shows panel with rate, trend, rank, sparkline, family breakdown.
4. MAP-04: Events toggle with absent incidents/current.json → graceful "coming soon" toast, no console error.
5. MAP-05: Locate button → correct commune highlighted + user-dot + success toast; deny → graceful denied toast, no crash.
6. MAP-06 (SC3): Moto G4 + Fast 3G emulation in DevTools → choropleth renders within ~4s, no jank.
7. Zero-React regression: a content page (e.g. /commune/santiago/) shows no leaflet/react JS in DevTools Network.

**To verify:** Run `cd site && npm run dev` and open http://localhost:4321/map/ (and /es/mapa/).

**Resume signal:** Type "approved" to sign off Phase 3, or describe any issue (which MAP requirement, what you saw) so it can be fixed before sign-off.

## Deviations from Plan

None — plan executed exactly as written. Both files implement the interfaces and copy the exact patterns specified in 03-PATTERNS.md.

## Known Stubs

None. IncidentPinLayer gracefully handles the absent `incidents/current.json` with a toast — this is the designed behavior for Phase 5 not yet built, not a stub.

## Threat Surface Scan

No new network endpoints or auth paths introduced beyond those in the plan's threat model. All three threats addressed:

- T-03-03-01: coordinates stay client-side; never transmitted; denial handled gracefully.
- T-03-03-02: `escHtml()` + `safeUrl()` applied to all incident strings before popup HTML.
- T-03-03-03: all incident source links use `rel="noopener noreferrer"`.
- T-03-03-04: PiP is O(features × rings) ≈ 2ms on locate only — accepted.

## Self-Check: PASSED

- `site/src/components/map/UserLocationMarker.ts`: EXISTS (created this session)
- `site/src/components/map/IncidentPinLayer.ts`: EXISTS (created this session)
- Task 1 commit d6f1d62: git log confirms present
- Task 2 commit 90a4552: git log confirms present
- 8/8 validators: confirmed PASSED in build output above
