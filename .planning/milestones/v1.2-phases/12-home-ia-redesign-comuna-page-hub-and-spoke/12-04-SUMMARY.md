---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "04"
subsystem: commune-pages
tags: [commune, breadcrumb, hub-and-spoke, map-spoke, similar-comunas, crime-type, i18n]
dependency_graph:
  requires: ["12-01", "12-02"]
  provides: [commune-page-hub-spokes-EN, commune-page-hub-spokes-ES]
  affects: [commune-pages, es-commune-pages]
tech_stack:
  added: []
  patterns:
    - nearestComparables(cut, n) from data.ts (12-01) consumed for similar-comunas spoke
    - FAMILY_SLUGS from i18n.ts for crime-type spoke hrefs
    - CommuneRankingTable reused for similar-comunas table
    - Static anchor /map/?cut=<cut> pattern (consumes 12-02 focus param)
key_files:
  created: []
  modified:
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
decisions:
  - "MapPlaceholderSlot removed from both ficha templates; replaced by static map-spoke anchor"
  - "Crime-type spoke labels use FAMILY_SLUGS[key].en/.es — EN capitalized, ES lowercase per slug convention"
  - "regionCommuneCount computed via loadIndex().filter(c => c.region_id === data.region_id).length; BUGFIX-999.1 comment added"
metrics:
  duration: "18m"
  completed: "2026-06-16"
  tasks: 3
  files: 2
---

# Phase 12 Plan 04: Comuna Page Hub-and-Spoke Summary

Each EN and ES commune ficha is now a connected hub: 4-level breadcrumb with Communes directory link, static map-spoke CTA to /map/?cut=<cut>, same-region similar-comunas table via nearestComparables, per-crime-type spoke links to existing /crime/ pages, and regional-rank device showing #N of M communes in the region.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1+2 | Upgrade breadcrumb + add spokes on EN commune page | 714bc52 | site/src/pages/commune/[slug].astro |
| 3 | Mirror all spokes + breadcrumb on ES commune page | 1442ec2 | site/src/pages/es/comuna/[slug].astro |

## What Was Built

### EN commune page (`commune/[slug].astro`)

1. **Breadcrumb (D-09):** Upgraded from 2-level (Home › Region) to 4-level: Home › Communes (`/communes/`) › RegionName › `<span aria-current="page">CommuneName</span>`
2. **Regional-rank device:** StatCard value changed from `#N` to `#N of regionCommuneCount` where `regionCommuneCount = loadIndex().filter(c => c.region_id === data.region_id).length`
3. **Map spoke (D-08):** `MapPlaceholderSlot` removed; replaced with static `<a href="/map/?cut=${data.cut}">` — zero client JS, consumes the ?cut= focus param added in 12-02
4. **Similar-comunas spoke (D-07):** `nearestComparables(cut, 5)` → `CommuneRankingTable rows={similarComunas} locale="en"` under editorial-tone-compliant heading
5. **Crime-type spoke (D-10):** `Object.entries(byFamily).map()` → `<a href="/crime/${FAMILY_SLUGS[key]?.en ?? key}/">` for each crime family present that year

### ES commune page (`es/comuna/[slug].astro`) — full parity

All same changes, ES-localized:
- Breadcrumb: Inicio (`/es/`) › Comunas (`/es/comunas/`) › Region › aria-current name
- Regional rank: `#N de regionCommuneCount`
- Map spoke: `/es/mapa/?cut=${data.cut}` (hardcoded ES slug)
- Similar-comunas: `CommuneRankingTable locale="es"`
- Crime-type spoke: `/es/delito/${FAMILY_SLUGS[key]?.es ?? key}/`

## Verification

- `npm run build` exits 0 (772 pages)
- `commune.mjs` PASSED — 346 EN + 346 ES commune pages validated
- `hreflang.mjs` PASSED — 772 pages, all alternates reciprocal

## Deviations from Plan

None — plan executed exactly as written. Tasks 1 and 2 were committed together (single file, both changes cohesive).

## Known Stubs

None. All spokes wire to real data at build time.

## Self-Check: PASSED

- `site/src/pages/commune/[slug].astro` — exists and modified
- `site/src/pages/es/comuna/[slug].astro` — exists and modified
- Commit 714bc52 — verified in git log
- Commit 1442ec2 — verified in git log
