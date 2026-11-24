---
quick_id: 261124-bmp
type: hotfix
owner_approved: 2026-11-24 (owner request: "explora una manera de evitarlo… no puedes modelar tu mismo el mapa de Chile?… dejarlo resuelto y pushed")
requirements: [live map covered by a third-party "API KEY REQUIRED" tile watermark; no API key, $0 infra, no external runtime dependency]
must_haves:
  truths:
    - "The map island requests NO third-party tile/basemap/font/sprite host at runtime and needs no API key"
    - "Sea = container colour; neighbouring land = one non-interactive vector layer below the choropleth; Chile = the 346 commune polygons"
    - "No ocean-coloured slivers along the Andes border and no double coast"
    - "Map zoom is capped on L.map itself (13); nothing requests a higher zoom"
    - "If basemap.topo.json fails to load the choropleth still works (no loadError)"
    - "D-12 (choropleth never re-mounted) and the single central restyle effect are untouched"
    - "The build FAILS if a tile host comes back (source or bundle) or the basemap asset is missing / over budget / stale / contains Chile"
  artifacts:
    - scripts/build-basemap.mjs
    - data/cead/geo/basemap.topo.json
    - site/src/components/map/BasemapLayer.ts
    - site/src/lib/basemapLabels.ts (+ .test.ts)
    - site/src/components/map/MapIsland.tsx, map.css
    - site/scripts/validate/map.mjs
---

# Quick 261124-bmp: Own basemap — no API key

## Why
`MapIsland.tsx` mounted a CARTO Positron raster tile layer. On 2026-11-24 CARTO answers every
tile (all styles, with or without referer) with a 256 px watermark "API KEY REQUIRED". The live
map is covered by it. The owner does not want to obtain or manage a key.

## Locked design
1. Delete the tile layer. No external host at runtime, no new npm dependency.
2. Own basemap: (a) sea = Leaflet container background; (b) non-Chile land as ONE
   non-interactive SVG layer in a pane below the choropleth; (c) Chile = commune polygons plus a
   runtime silhouette merged from the same topology; (d) light non-interactive place names.
3. Land source: Natural Earth admin-0 1:10m (public domain), pinned tag + sha256, built by the
   re-runnable offline `scripts/build-basemap.mjs`; only the small output is committed.
4. Zoom cap 13 on the map; audit every setView/flyTo/fitBounds/maxZoom.
5. Attribution: chilemapas (INE/SUBDERE/BCN) + Natural Earth; docs/methodology bilingual.
6. Regression guards in `validate/map.mjs` + vitest.
7. Progressive: basemap fetch outside the choropleth `Promise.all`; no state that feeds the
   restyle effect.

## Tasks
### Task 1 — Geometry
`scripts/build-basemap.mjs`: download (os.tmpdir, sha256-verified) → dissolve ALL countries
clipped to a world-context bbox (`-180,-85,45,14`, NOT maxBounds) → simplify BEFORE the erase →
`-erase` the dissolved commune union → `-explode`, keep only pieces holding an inner point of a
non-Chile polygon → dissolve → TopoJSON `quantization=1e7` → inject `meta.communesSha256` →
assert budget, probes, bbox and residual gaps. Run it.

### Task 2 — Runtime
`BasemapLayer.ts` (panes z 200 / 450, SVG renderer padding 1, land, Chile silhouette, labels),
`lib/basemapLabels.ts` (zoom constants, tiers, collision culling). `MapIsland.tsx`: remove
`tileRef` + tile layer, `maxZoom` on `L.map`, attribution, separate basemap effect.

### Task 3 — Guards, docs, record
`validate/map.mjs` checks 11-13, vitest, `data/SOURCES.md`, figure-registry F12, methodology
EN/ES, STATE.md row.

### Task 4 — Gates (one chained command; repo is inside OneDrive)
`npx astro check` · `npm test` · `npm run build && npm run validate`.

Do NOT commit or push — the orchestrator does that.
