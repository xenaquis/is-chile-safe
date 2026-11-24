---
quick_id: 261124-bmp
status: complete (uncommitted — orchestrator commits and pushes)
---

# Quick 261124-bmp: Own basemap, no API key — Summary

## What was done

The third-party raster tile layer is gone. The map now draws its own background from
same-origin `/data/*` files: no map, tile or sprite service, no API key, no new npm dependency.
The site-wide web font (Google Fonts, pre-existing) is the only external request on the page;
it is optional and the labels fall back to a system font.

| Layer | Source | Where |
|---|---|---|
| Sea | CSS background `--bm-ocean` on `.map-canvas.leaflet-container` | `map.css` |
| Neighbouring land | Natural Earth admin-0 1:10m v5.1.2 (public domain), one dissolved shape, Chile erased | `data/cead/geo/basemap.topo.json` |
| Chile silhouette | `topojson.merge` of the commune topology already loaded | `BasemapLayer.ts` |
| Choropleth, dots, pins | unchanged | — |
| Place names | commune names; anchor = the city for the 16 regional capitals, an interior point of the polygon for the rest; country/ocean names hard-coded EN/ES | `lib/basemapLabels.ts`, `src/data/commune-label-points.json` |

### Geometry (`scripts/build-basemap.mjs`, run on 2026-11-24)
- Output: **117,126 B raw / 45,338 B gzip**, 171 polygons, bbox `[-180, -85, 45, 14]`
  (geometry unchanged by the review round; +92 B is the `meta.gaps` record).
- Knobs: weighted Visvalingam 12 % (6 % gave 75 KB but a visibly angular Atlantic coast at
  zoom 7), islands < 30 km² dropped, `quantization=1e7`.
- Clip is a world-context bbox, not `maxBounds`: at min zoom 4 a 1440 px viewport shows about
  lng -134..-8, so a tight clip would end the continent in a straight cut.
- No-sliver construction: land = all countries (Chile and the "SPI" ice-field feature included)
  minus the dissolved commune union, then only the pieces that contain an inner point of a
  non-Chile polygon are kept. Border slivers stay (fused to Argentina/Bolivia/Peru); detached
  Natural-Earth-Chile coast slivers and islands are dropped, so there is no double coast.
- Residual gaps over the WHOLE border (review round 1, see below): 946 hairlines, **1.169 km²
  in total, largest 0.045 km²**. The script now really fails above 0.5 km² per piece or 5 km²
  total, before writing anything, and stores the figures in `meta.gaps`. At runtime the outline
  stroke of the Chile silhouette covers them.

### Runtime
- Panes: `basemap` z 200 (below overlayPane 400), `basemapLabels` z 450 (below markerPane 600);
  both `pointer-events: none`, labels pane `aria-hidden`.
- SVG renderer bound to the basemap pane with `padding: 1`; paths styled by class with CSS
  tokens. `L.canvas()` still appears only in `ChoroplethLayer.ts`.
- Zoom: `L.map(..., { minZoom: 4, maxZoom: 13 })` from `MAP_MIN_ZOOM` / `MAP_MAX_ZOOM`.
  Audit of every call: national `fitBounds`, `?region=` `fitBounds` (clamped by the cap),
  `flyToBounds` maxZoom 12, locate `flyTo` 12, `ZoomControl` zoomIn/zoomOut (clamped). Nothing
  asks for more than 12.
- Progressive: the land fetch has its own effect keyed on `[mapReady]`, sets no state, and
  returns silently on failure. The Chile silhouette and labels are mounted in a separate task
  AFTER the choropleth, inside one try/catch (review round 1).
- Labels: z 4-5 seven anchor cities + country/ocean names; z 6-7 the 16 regional capitals;
  z 8-9 capitals + communes ≥ 100k; z 10+ all communes by population. Greedy collision
  culling, at most 40 commune labels. Antártica and Isla de Pascua are never labelled; no
  label for Antarctica or the Falkland/Malvinas islands; no country borders are drawn.
- Attribution control: "Boundaries: chilemapas (INE/SUBDERE/BCN)" always; ", Natural Earth"
  once the land file has loaded. EN/ES.
- Small extras: `ZoomControl` aria-labels are now bilingual; the "near me" toast shows the
  commune name instead of the numeric CUT (and no longer leaks the Spanish fallback into English).

### Defect found by the browser check
First headless screenshot showed labels and attribution but **no land**. Cause: the site-wide
`svg { max-width: 100% }` reset in `global.css` collapses an SVG renderer in a custom pane to
zero width (Leaflet only exempts its own overlay pane). Fixed in `map.css`
(`.leaflet-container .leaflet-basemap-pane svg { max-width: none !important }`) and pinned by a
validator assertion, since no other gate would have noticed.

### Guards
- `validate/map.mjs` check 11 (asset): exists, Topology + `land`, raw ≤ 150 KB, gzip ≤ 60 KB,
  `meta.communesSha256` equals the current `communes.topo.json`, 348 Chilean probes outside,
  5 neighbour probes inside, bbox coverage.
- Check 12 (source): no `tileLayer(`, no tile host or `{z}` template, host allow-list, zoom cap
  present, basemap not in the choropleth `Promise.all`, SVG reset exemption present.
- Check 13 (bundle): scans `dist/_astro/*.js|css` only; tile-host regex + host allow-list;
  island chunk named by both map pages must be among the scanned files; bundle credits both
  sources. Proven against the previous build: it failed on `basemaps.`, `www.openstreetmap.org`
  and `carto.com`.
- vitest `basemapLabels.test.ts` (17 tests): zoom cap, no tile call in source, capitals present
  in `index.json`, tiers, collision culling.
- `figure-registry.mjs` F12 now requires `## Natural Earth` in `data/SOURCES.md`.

## Gates
| Gate | Result |
|---|---|
| `npx astro check` | 0 errors, 0 warnings, 48 hints |
| `npm test` | 17 files, 212 tests passed |
| `npm run build` | 834 pages, complete; `postbuild` map validator PASSED (45 checks) |
| `npm run validate` | 18/19 — `map` PASS; `freshness` FAIL (un-synced checkout, see below) |

(Figures after review round 1.)

`freshness` fails because `last_new_incident_at` is 2026-09-26 (1417 h old) in the local
checkout's news data. This change touches nothing under `data/incidents/` or `pipeline/`.
Proof that it is the checkout and not the change: the same validator run against
`origin/master`'s `data/incidents/current.json` (`FRESHNESS_CURRENT_JSON` override) passes,
"last_new_incident_at: 2026-11-24T16:56:31Z is 5.4h old".

## Visual check
Headless Chrome against `astro preview` of the build, `/es/mapa/` at 1440×900 and 390×800 and
`/es/mapa/?cut=13101`: land, silhouette, labels and attribution render; `?cut=` focus and the
result panel still work. Hover, drag and pinch were not exercised (BrowserOS MCP was down).

## Deviations
- `CLAUDE.md` was NOT edited (stack note / "What NOT to use" line about tile hosts). The
  executor may not change project instructions on a workflow's say-so; left for the owner.
- `DEPLOYMENT.md` needed no change: it never mentioned the old basemap.
- Single-tier geometry (1:10m everywhere, simplified) instead of the two-tier 10m + 110m
  variant some reviewers proposed: the validated single pipeline already fits the budget.

## Follow-ups (out of scope)
- `sync-data.mjs` still publishes `communes-chilemapas.geojson` (11 MB) to `dist/`.
- Displays wider than 4096 px at zoom 4 see the world repeat without the vector land.
- The `+` zoom button is not disabled at the cap.

## Review round 1 (3 adversarial reviewers, 18 findings: 1 HIGH, 7 MEDIUM, 10 LOW)

Several findings overlap; grouped by what was done.

### Fixed
| Finding | Fix |
|---|---|
| MEDIUM ×2: 16 of 346 names anchored outside their commune ("Chillán" on Chillán Viejo, "Talcahuano" in the sea); capital names up to 143 km from the city | Names no longer use the dot layer's vertex average. `build-basemap.mjs` step 8 writes one interior point per commune (`mapshaper -points inner`) to `site/src/data/commune-label-points.json` (9.6 KB, sha256-stamped, each asserted inside its own polygon). The 16 regional capitals use hand-checked city coordinates (`CAPITAL_LABEL_POINTS`). Below zoom 8, where the name sits beside the low-zoom dot, it still follows the dot. `LowZoomDotLayer.ts` untouched. Guarded by vitest (346/346 inside, capitals inside their commune and within 10 km of an independent reference) and by `map.mjs` check 11b. |
| MEDIUM ×2: the gap check only logged, ran after the write and skipped the border south of 36°S | Rewritten: runs against the temp output before any write, covers the whole border, classifies every sea-coloured piece (open water / Chile water / land water / border gap = enclosed and sharing a vertex with the neighbour land), exits 1 above 0.5 km² per piece or 5 km² total, records `meta.gaps`; `map.mjs` re-checks `meta.gaps`. Header comment corrected. Measured: 946 hairlines, 1.169 km², largest 0.045 km². |
| MEDIUM: lowest choropleth class almost the colour of neighbour land and sea (deltaE ≈ 4) | Land `#dcdad2` (warm grey), sea `#c9d7dd`, plus a thin cool outline (`#b3bfc3`) around the commune union, drawn with `paint-order: stroke fill` so only its outer half shows. Lowest class vs land deltaE 8.4, vs sea 7.0; no-data vs land 5.2. The reviewer's target of 10 was not reached with fills alone without making the background heavier than the data; the outline carries the rest. Checked in headless Chrome at zoom 4, 7, 9, 11. |
| MEDIUM: the tile-host guard did not run on the production deploy path | `site/package.json` gained `"postbuild": "node scripts/validate/map.mjs"`, so `npm run build` (Cloudflare's build command) fails on a regression. `map.mjs` also asserts the numeric cap (`MAP_MAX_ZOOM <= 13`) and that no literal zoom request exceeds it, since vitest is not part of the build. DEPLOYMENT.md documents the step. |
| LOW: three guard bypasses | Source scan now rejects any `tileLayer/TileLayer/gridLayer/GridLayer/imageOverlay/videoOverlay` identifier; host scan also matches quoted protocol-relative URLs; the two map pages' HTML resource tags are checked against a host allow-list. Mutation-tested on a scratch copy: `.wms('//…')`, `new L.TileLayer(…)`, injected `<link preconnect>` + `<script src>`, cap 19, an anchor moved outside its commune and `meta.gaps` over the limit all fail with exit 1; baseline exits 0. |
| LOW: silhouette merge and label loop ran before the choropleth mount, loop outside try/catch | Moved after `mountChoroplethLayer`, into `setTimeout(0)` and one try/catch. |
| LOW: ocean labels 2.9:1 | Ocean label `#40596a` (5.0:1 on the new sea), country label `#4d5a5b` (5.1:1 on the new land). |
| LOW: size figures inconsistent, "page colour" | SOURCES.md uses exact bytes; "map background colour". |
| LOW ×2: "only same-origin requests" not literally true (web font) | Reworded here, in SOURCES.md and in the `BasemapLayer.ts` header. Self-hosting the font is a separate task. |
| LOW: STATE.md frontmatter stale | `last_updated` / `last_activity` bumped; the row's commit column stays `pending` for the orchestrator. |

### Knowingly left
- **HIGH — local `master` is not in sync with `origin/master`.** Verified after `git fetch`:
  local is 3 commits ahead and 187 behind; the branches have diverged, so integrating needs a
  rebase or merge, which creates commits and is outside this step (no commit, no push). The
  187 upstream commits touch only `data/incidents/*` (9 files); the 3 local commits touch
  `.planning/**` and `site/scripts/validate/all.mjs`; `communes.topo.json` is unchanged
  upstream. So `git pull --rebase --autostash` should apply cleanly, the basemap does not need
  a re-run, and `freshness` turns green on the rebased tree (shown above). **The orchestrator
  must rebase, then re-run `cd site && npm run build && npm run validate` in one command,
  before pushing.**
- LOW — animated multi-level zoom-outs briefly show bare sea around the shrinking land layer
  (SVG renderer holds 3× the viewport). Raising the padding to 2-3 means a 5-7× viewport SVG
  on every device for a sub-second effect; not done.
- LOW — land cut at 14°N on very tall viewports. A min-zoom-5 rule for tall containers was
  implemented, seen in a 1200×1500 screenshot to leave northern Chile stuck under the topbar
  (the view is pinned to `maxBounds`), and reverted. The opaque topbar covers the top
  225-350 px of the stage, so the cut only shows above roughly 1850 px of viewport height.
  Script header comment corrected.
- LOW ×2 — about 2,800 km² of Natural Earth's Chile drawn as neighbour land and about
  17,800 km² as sea: by design (the commune edge is the edge of Chile). Now stated in
  SOURCES.md § Natural Earth.
- The 100k+ non-capital communes use the polygon's interior point, which for a large commune
  (Calama, Los Ángeles) is not the city. Only the 16 capitals have hand-checked coordinates.
- `CLAUDE.md` still not edited (same reason as before).

### Files added or changed in this round
`scripts/build-basemap.mjs`, `data/cead/geo/basemap.topo.json` (meta only),
`site/src/data/commune-label-points.json` (new), `site/src/lib/basemapLabels.ts` + test,
`site/src/components/map/{BasemapLayer.ts,MapIsland.tsx,map.css}`,
`site/scripts/validate/map.mjs`, `site/package.json`, `data/SOURCES.md`, `DEPLOYMENT.md`,
`scripts/build-topojson.mjs` (comment), `.planning/STATE.md`.
