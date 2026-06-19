# Phase 10: High-Resolution Commune Geometry - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning
**Source:** plan-phase inline decisions (post-research), confirmed via AskUserQuestion

<domain>
## Phase Boundary

Re-tune the existing, working geometry build pipeline (`scripts/build-topojson.mjs`) so the shipped `data/cead/geo/communes.topo.json` renders as recognizable comuna shapes instead of the current blocky ~8×10 km snap grid — **and** swap the boundary source away from the license-incompatible GADM dataset. This is a **parameter + source change on an existing pipeline, not a greenfield build**. The render path, mirror mechanism, and join key are already correct (CLAUDE.md-compliant native `L.geoJSON()` + `L.canvas()`); do **not** rewrite them.

**In scope:** boundary-source swap (GADM → chilemapas), CUT re-key with zero-pad normalization, simplification/quantization re-tune, build-time integrity + size assertions, raising the stale validator gate, committing the raw source, attribution.

**Out of scope:** any change to the map render architecture, the choropleth color logic, the low-zoom dot layer, or react-leaflet usage. No new runtime npm deps. Phases 11–12 (homicide layer, SEO ranking pages) are separate.
</domain>

<decisions>
## Implementation Decisions

### Boundary Source (LOCKED)
- Replace GADM 4.1 L3 (non-commercial / no-redistribution — license-incompatible with this AdSense, public-repo site) with **chilemapas** (`data_geojson` comunas file). GPL-3, INE/SUBDERE/BCN-authoritative, ships a real `codigo_comuna` (CUT) property → robust **code-join** that retires the fragile name-matching path.
- Add a source-attribution line in the build-script header AND a visible credit in the site methodology/colophon (GPL-3 + good practice).
- Keep `geoBoundaries CHL ADM3` (CC-BY-4.0, name-match join) documented as the fallback only if chilemapas fidelity/coverage proves insufficient — not the default.

### CUT Join Integrity (LOCKED — #1 failure mode)
- chilemapas `codigo_comuna` is 5-char zero-padded; CEAD CUT (`index.json`, `properties.id`) is unpadded raw digits. Normalize source → CUT with `String(parseInt(code, 10))` (or strip leading zeros) before joining.
- Build MUST hard-assert against `data/cead/meta/index.json`: exactly **346 features, 0 missing, 0 orphan, 0 duplicate CUT**, Santiago `13101` present. Extend the existing Step-5 assertion (today it only checks count + Santiago) to cover missing/orphan/duplicate explicitly.
- If chilemapas lacks Antártica (12202) / oceanic islands, reuse the existing placeholder approach for just those CUTs. Keep `keep-shapes` so tiny coastal/island comunas don't collapse.

### Size / Performance Budget (LOCKED)
- Target config: **visvalingam ~10% + quantization≈10000** (measured: ~367 KB raw / ~107 KB gzip, ~0.4 km grid, recognizable coastline, integrity-clean).
- Budget gate: **≤140 KB gzip AND ≤420 KB raw.** Express the primary budget against **gzip** (Cloudflare serves gzip/brotli — that's what users download); keep a raw ceiling too.
- The stale `TOPO_MAX_BYTES = 102400` (100 KB raw) gate in `site/scripts/validate/map.mjs` is **the bug** — it hard-fails any recognizable geometry. Raise it to the new budget and ADD a gzip-size assertion. Also fix the matching `<100 KB` logic + the three over-aggressive fallback configs inside `build-topojson.mjs` so they can't silently re-over-simplify.
- Do NOT chase fidelity past what reads as recognizable (10% is plenty; don't go to 20%). Lowest retention that still looks right wins, for canvas hover/pan/zoom perf.

### Reproducibility (LOCKED — Success Criterion #5)
- **Commit the raw chilemapas source** (`data/cead/geo/communes-chilemapas.geojson`) so the build re-runs offline with no network. Update `.gitignore` accordingly. Document the exact source download URL + version/date in the build-script header anyway.
- Regeneration entry point stays `node scripts/build-topojson.mjs`. Chain build + sync + validate in a **single command** per the OneDrive build-artifact desync constraint.

### Verification (LOCKED)
- Automated: build-time integrity assertion (346/0/0/0) + raw & gzip size assertions; `cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs` chained; full `npm run build` green.
- Manual HUMAN-UAT gates (intrinsic to GEO-01/GEO-02): visual recognizability on `/map/` + `/es/mapa/` (compare to current), and smooth pan/zoom/hover + clean console on a throttled-mobile profile (Phase-3 used Moto G4 + Fast 3G).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Build pipeline (edit targets)
- `scripts/build-topojson.mjs` — the existing generator: source load → CUT re-key → mapshaper simplify → TopoJSON encode + assertions. Primary edit target (source swap, zero-pad normalize, simplify knobs, integrity + budget asserts).
- `site/scripts/validate/map.mjs` — structural validator; raise `TOPO_MAX_BYTES`, add gzip assertion.
- `site/scripts/sync-data.mjs` — mirror `data/cead/` → `site/public/data/cead/` (predev/prebuild). **No change needed** (generic copy).
- `data/cead/meta/index.json` — 346-CUT source of truth for the join-integrity assertion.

### Consumption (read-only — do NOT modify render architecture)
- `site/src/components/map/MapIsland.tsx` — `safeFetch('/data/cead/geo/communes.topo.json')` → `topojson-client` `feature()` → features.
- `site/src/components/map/ChoroplethLayer.ts` — native `L.geoJSON(data, { renderer: L.canvas() })`, mounted once; join on `f.properties.id` (CUT).
- `site/src/components/map/LowZoomDotLayer.ts` — low-zoom dot substitution (reduces canvas cost at country zoom).

### Decision evidence
- `.planning/phases/10-high-resolution-commune-geometry/10-RESEARCH.md` — measured simplification matrix, licensing verification, join-integrity findings, pitfalls.
- `CLAUDE.md` — "What NOT to Use" (no react-leaflet `<GeoJSON>`; native `L.geoJSON()`), stack versions, $0 budget.
</canonical_refs>

<specifics>
## Specific Ideas

- Measured matrix to anchor the budget choice: `0.05%/q=500`→87KB/21KB (current, blocky); `10%/q=10000`→367KB/107KB (target); `8%/q=10000`→335KB/99KB; `20%`→don't bother.
- Re-key normalization helper: `srcCodeToCut(code) => String(parseInt(code, 10))`.
- Gzip assertion via Node `zlib.gzipSync(readFileSync(TOPO_PATH)).length`.
- `mapshaper rekeyed.geojson -clean -simplify visvalingam percentage=10% keep-shapes -o format=topojson quantization=10000`.
</specifics>

<deferred>
## Deferred Ideas

- INE geoportal / BCN direct shapefile download (deeper fallback, may need UTM→WGS84 reproject) — only if both chilemapas and geoBoundaries prove insufficient. Not for this phase.
- Variable/interval-based simplification (`-simplify interval=`) to even out Chile's latitude span — optional tuning, only if percentage gives uneven coastlines.
- Retiring `communes-raw.geojson` (GADM) — keep for diff/QA this phase; don't delete.
</deferred>

---

*Phase: 10-high-resolution-commune-geometry*
*Context gathered: 2026-06-15 via plan-phase inline decisions (research-informed, user-confirmed)*
