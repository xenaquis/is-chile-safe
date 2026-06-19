# Phase 10: High-Resolution Commune Geometry - Research

**Researched:** 2026-06-15
**Domain:** Geospatial data engineering — authoritative Chilean commune boundaries, topology-preserving simplification, TopoJSON build pipeline, Leaflet-canvas render budget
**Confidence:** HIGH (current asset + consumption path read directly; simplification measured empirically in this session; licensing verified against source pages)

## Summary

The map already ships a 346-commune TopoJSON (`data/cead/geo/communes.topo.json`, 87 KB raw / 21 KB gzip) produced by an existing, re-runnable Node script (`scripts/build-topojson.mjs`) that re-keys GADM 4.1 Chile Level-3 boundaries to CEAD CUT codes. The pipeline, join key (`feature.properties.id` = CUT string), the mirror mechanism (`site/scripts/sync-data.mjs` copies `data/cead/` → `site/public/data/cead/` on predev/prebuild), and the render path (native `L.geoJSON()` + `L.canvas()` in `ChoroplethLayer.ts`) are all correct and already follow the CLAUDE.md pitfalls. **Phase 10 is not a greenfield build — it is a re-tune of an existing, working pipeline plus a likely source swap.**

The blocky appearance has a measured root cause: the ship config is `visvalingam percentage=0.05% quantization=500`. Over Chile's ~43° N–S span that quantization grid is **~8 × 10 km per integer unit** — every coastline and border vertex snaps to an 8–10 km grid, which is what reads as "blocky." Fixing fidelity is primarily a **quantization** fix, secondarily a retention-% fix. Empirically (measured this session on the real CUT-keyed input): raising to `percentage=10% quantization=10000` yields a ~0.4 × 0.5 km grid, 35,885 arc points (vs 5,085 today), recognizable coastline — at **367 KB raw / 107 KB gzip**, still 346 features with **zero missing/orphan/duplicate CUTs**. TopoJSON shared-arc simplification preserves topology (no slivers/gaps) automatically.

Two source decisions need a human call and are the main open questions: (1) **Licensing** — the current GADM source **prohibits commercial use and redistribution without permission** (verified on gadm.org/license). This site runs AdSense (commercial) and commits the derived asset to a publicly-deployed repo (redistribution), so GADM is a licensing liability that should be replaced with an openly-licensed source. (2) **Size budget** — the existing `<100 KB raw` validator gate (`site/scripts/validate/map.mjs`, `TOPO_MAX_BYTES = 102400`) is an arbitrary Phase-3 carry-over and is **incompatible with any recognizable geometry**; it must be raised, and the budget re-expressed against gzip (Cloudflare serves gzip/brotli).

**Primary recommendation:** Keep the existing `scripts/build-topojson.mjs` architecture. Swap the boundary source from GADM to an openly-licensed INE-derived source (**chilemapas** `data_geojson`, GPL-3, INE/SUBDERE/BCN-sourced, already referenced in `.gitignore`; fallback **geoBoundaries CHL ADM3**, CC-BY 4.0). Re-tune simplification to `~10% visvalingam` + `quantization≈10000`. Raise the validator budget to ~**400 KB raw / ~130 KB gzip** and add a gzip-size assertion. Keep CUT-join verification (346 features, zero missing/orphan) as a hard build assertion — it already exists and must stay.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Source boundary acquisition | Build tooling (offline, one-time) | — | Run once at data-prep; raw source committed to `data/cead/geo/` so build is reproducible offline |
| CUT re-key + name canonicalization | Build tooling (`build-topojson.mjs`) | Data (`index.json`) | Join geometry to CEAD CUT source-of-truth; never at runtime |
| Simplification + TopoJSON encode | Build tooling (mapshaper CLI) | — | Offline; output committed; not an Astro build step |
| Mirror to public/ | Build tooling (`sync-data.mjs`) | — | predev/prebuild copy `data/cead/`→`site/public/data/cead/`; already automated |
| TopoJSON→GeoJSON decode | Browser (map island) | — | `topojson-client` `feature()` at runtime in `MapIsland.tsx` |
| Polygon render + hover/click | Browser (Leaflet canvas) | — | Native `L.geoJSON()` + `L.canvas()` in `ChoroplethLayer.ts` (Pitfall-6 compliant) |
| Choropleth color join | Browser | Data (`map-payload.json`) | Joins `properties.id` (CUT) → payload `comunas[].id` |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEO-01 | Regenerate `communes.topo.json` (+ public mirror) from an authoritative Chilean commune-boundary source (INE/BCN/IGM), covering every CEAD comuna, keyed by the same CUT code the map joins on (no comuna dropped/mis-joined); polygons read as real comuna shapes vs the blocky simplification. | Standard Stack (source comparison + licensing); Architecture Patterns (re-key + topology); Join-Key Integrity section; measured grid-resolution evidence proving the fidelity fix is a quantization change. |
| GEO-02 | Published asset respects a documented size/performance budget (fidelity↔KB tradeoff recorded); map keeps pan/zoom/hover fluid, no new console errors; reproducible regeneration procedure (script or documented steps). | Simplification + Size/Perf Budget section (measured raw+gzip matrix, recommended budget); Reproducible Regeneration section; Validation Architecture (size + join assertions); Common Pitfalls (validator gate, canvas render path). |
</phase_requirements>

## Current Asset + Consumption Path (verified this session)

**Current asset:** `data/cead/geo/communes.topo.json`, 89,266 bytes (87 KB) raw, **~21 KB gzip**.
- TopoJSON `Topology`; single object **`communes-rekeyed`**, `GeometryCollection`, **346 geometries**.
- Per-geometry `properties = { id, name }`. **`id` is the CEAD CUT code as a raw string** (e.g. `"2101"` Antofagasta, `"13101"` Santiago) — no zero-padding (matches STATE.md decision "CUT codes stored as raw string digits without zero-padding").
- `transform.scale = [0.0861, 0.0922]` deg/unit → **quantization grid ≈ 7.9 × 10.2 km** (the blockiness root cause).
- 2,365 arcs / **5,085 total arc points** (extremely low — confirms over-simplification).

**Raw source on disk:** `data/cead/geo/communes-raw.geojson` (5.3 MB) = **GADM 4.1 Chile Level-3**, 345 features, props `GID_3`/`NAME_3`/`CC_3=NA` (GADM carries **no** commune code — hence the name-match re-key). `.gitignore` lists this plus two **already-evaluated alternative sources**: `communes-chilemapas.geojson` and `communes-fcorrea.geojson` (not currently present on disk).

**Generator script:** `scripts/build-topojson.mjs` (Node ESM, repo root). Steps: load GADM GeoJSON → load `data/cead/meta/index.json` (346-CUT source of truth) → name-normalized match + 3 `MANUAL_FIXES` → re-key `properties.id=CUT`, `properties.name=canonical` (drop all else) → add Antártica (CUT 12202) placeholder polygon (GADM lacks Antarctic territory; pop 151, zero crime) → write temp rekeyed GeoJSON → `mapshaper -simplify visvalingam percentage=0.05% keep-shapes -o format=topojson quantization=500` (with two more-aggressive fallback configs if >100 KB) → assert `type=Topology`, 346 features, CUT 13101 present, <100 KB → copy to `data/cead/geo/communes.topo.json`. **Re-runnable today**: `node scripts/build-topojson.mjs` (requires global `mapshaper`).

**Mirror path:** `site/scripts/sync-data.mjs` runs on `predev`+`prebuild`; `rmSync` then `cpSync` of `data/cead/`→`site/public/data/cead/` (plain recursive copy — no symlinks, OneDrive/Windows-safe). `public/data/` is gitignored and regenerated on every build incl. Cloudflare's. → Therefore **Phase 10 only needs to update `data/cead/geo/communes.topo.json`; the public mirror and `dist/` emission are automatic.**

**Consumption:** `site/src/components/map/MapIsland.tsx` L156-180: `safeFetch('/data/cead/geo/communes.topo.json')` (graceful, never throws) → `topojson-client` `feature(topo, topo.objects[firstKey])` → `geoData.features` stored in `featuresRef` (also used for the low-zoom dot-layer centroids). `ChoroplethLayer.ts` `mountChoroplethLayer()` uses **native `L.geoJSON(geoData, { renderer: L.canvas(), … })`** — mounted once, never re-mounted on filter change (`applyStyleMap` restyles in place). Join: `f.properties.id` (CUT) → style map / payload. **This is exactly the CLAUDE.md-mandated pattern; no react-leaflet `<GeoJSON>`, no per-hover re-render.** Higher vertex counts will NOT trigger React re-renders — only canvas redraw cost rises (addressed in Pitfalls).

## Standard Stack

### Core (already installed — no new runtime deps)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mapshaper (CLI) | 0.7.22 installed / 0.7.25 latest | Topology-preserving Visvalingam simplification + TopoJSON encode/quantization | De-facto standard for boundary simplification; `keep-shapes` prevents tiny-polygon collapse; shares arcs so borders simplify identically on both sides. [VERIFIED: npm registry — `npm view mapshaper version` → 0.7.25; local `mapshaper --version` → 0.7.22] |
| topojson-client | 3.1.0 | Runtime TopoJSON→GeoJSON decode in browser (`feature()`) | Already a sanctioned dep (`site/package.json`); CLAUDE.md-approved. [VERIFIED: npm registry → 3.1.0; present in `site/package.json`] |
| Leaflet | 1.9.x | Canvas polygon render | Already wired; `L.canvas()` renderer scoped to the geoJSON layer (Pitfall-6). [CITED: CLAUDE.md] |

### Boundary Source — Recommendation (the real Phase-10 decision)
| Source | License | Commercial OK? | Commune code | CRS | Format | Verdict |
|--------|---------|---------------|--------------|-----|--------|---------|
| **chilemapas** (pacha.dev / github.com/pachadotdev/chilemapas) | **GPL-3** | **Yes (with attribution)** | INE `codigo_comuna` (CUT), 5-char zero-padded string | EPSG:4326 (geojson export) | GeoJSON + TopoJSON, 346 comunas, ships `data_geojson/` | **PRIMARY** — INE/SUBDERE/BCN-sourced (authoritative), already pre-simplified, has a real commune code (removes name-matching fragility), already referenced in `.gitignore`. [CITED: cran chilemapas.pdf; github.com/pachadotdev/chilemapas] |
| **geoBoundaries CHL ADM3** | **CC-BY 4.0** | **Yes (attribution only)** | shapeID (not CUT) — needs name/shape join | EPSG:4326 | GeoJSON/Shapefile | **FALLBACK** — cleanest license, but no CUT code → keep the name-match re-key step. [CITED: geoboundaries.org; CC-BY 4.0] |
| INE geoportal / BCN "división política administrativa" | INE/BCN open (gov) | Generally yes | INE CUT | usually EPSG:4326 or SIRGAS UTM (reproject) | Shapefile/GeoJSON | Authoritative upstream of chilemapas; heavier to handle (Shapefile, possible UTM reproject). Use only if chilemapas/geoBoundaries fidelity is insufficient. [ASSUMED — not fetched this session] |
| **GADM 4.1 L3 (current)** | **Non-commercial, no redistribution w/o permission** | **NO** | none (`CC_3=NA`) | EPSG:4326 | GeoJSON | **REPLACE** — license incompatible with an AdSense site committing the derived asset to a public-deploy repo. [VERIFIED: gadm.org/license — "Redistribution or commercial use is not allowed without prior permission"] |

**Recommendation:** Primary **chilemapas** (`data_geojson` comunas file), fallback **geoBoundaries CHL ADM3**. Both are openly licensed for a commercial site. Add a source-attribution line to the build-script header and (for CC-BY/GPL compliance) a credit in the site's methodology/colophon. **Flag the GADM license issue to the human explicitly — it is a real risk on the currently-shipped asset, independent of fidelity.**

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mapshaper Visvalingam | topojson-server + topojson-simplify (JS lib) | Equivalent topology-aware result, but mapshaper CLI is already in the pipeline and `keep-shapes` is more ergonomic than wiring topojson-simplify by hand. No reason to switch. |
| Per-source pre-simplified file | Re-simplify from full-resolution INE shapefile | Full INE shapefile gives max fidelity headroom but is larger/heavier and may need UTM→WGS84 reproject; chilemapas already did this work acceptably. |
| Single global simplification % | Variable simplification (mapshaper `-simplify interval=`) | Interval-based (meters) can be more uniform across Chile's latitude span than percentage; worth trying if percentage gives uneven coastlines. Optional tuning, not required. |

**Installation:** No new npm runtime deps. Build tooling already present:
```bash
# already installed globally; verify before regeneration
mapshaper --version   # expect >= 0.7.22
```

**Version verification (this session):** `npm view mapshaper version` → **0.7.25** (latest); local install **0.7.22** (works — script is version-agnostic). `npm view topojson-client version` → **3.1.0** (matches `site/package.json`).

## Package Legitimacy Audit

> No new package installs are required for this phase. mapshaper (build-only, global) and topojson-client (already a project dep) are the only tools. Source datasets are data, not packages.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| mapshaper | npm | ~10 yrs | high (industry standard) | github.com/mbloch/mapshaper | not run (already installed, pre-vetted Phase 3) | Approved — build-only, global, no postinstall network use |
| topojson-client | npm | ~9 yrs | very high | github.com/topojson/topojson-client | not run (existing dep) | Approved — existing sanctioned dep |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.
**Data-source provenance (not packages):** chilemapas [CITED: cran + github], geoBoundaries [CITED: geoboundaries.org]. Both must be human-confirmed for license/CUT-scheme before the source swap is locked (see Assumptions Log).

## Architecture Patterns

### System Architecture Diagram (data flow)
```
[Authoritative source: chilemapas data_geojson (INE/SUBDERE/BCN) | fallback geoBoundaries ADM3]
        │  download once → commit to data/cead/geo/communes-<source>.geojson
        ▼
scripts/build-topojson.mjs  (offline, re-runnable)
        │  1. load source GeoJSON
        │  2. load data/cead/meta/index.json  (346 CUT source of truth)
        │  3. re-key: properties.id = CUT (normalized, unpadded);  ← JOIN-INTEGRITY GATE
        │     properties.name = canonical; drop all other props
        │       • chilemapas: map codigo_comuna → CUT (strip zero-pad)
        │       • geoBoundaries/GADM: name-normalized match + MANUAL_FIXES
        │  4. inject Antártica 12202 placeholder if source lacks it
        │  5. ASSERT 346 features, 0 missing, 0 orphan, 0 dup CUT, 13101 present
        │  6. mapshaper -simplify visvalingam percentage≈10% keep-shapes
        │     -o format=topojson quantization≈10000           ← FIDELITY KNOBS
        │  7. ASSERT Topology, 346 geoms, size within budget (raw + gzip)
        ▼
data/cead/geo/communes.topo.json   (committed asset)
        │  predev/prebuild
        ▼
site/scripts/sync-data.mjs  →  site/public/data/cead/geo/communes.topo.json  → dist/
        │  runtime fetch (browser)
        ▼
MapIsland.tsx: safeFetch → topojson-client feature() → GeoJSON.FeatureCollection
        ▼
ChoroplethLayer.ts: L.geoJSON(data, { renderer: L.canvas() })  (mounted once)
        │  join f.properties.id (CUT) → style map / map-payload comunas[]
        ▼
[Leaflet canvas: 346 colored comuna polygons, hover tooltip, click→panel]
```

### Recommended Project Structure (no change — reuse existing)
```
data/cead/geo/
├── communes-chilemapas.geojson   # NEW raw source (gitignored — committed-once decision below)
├── communes-raw.geojson          # OLD GADM source (retire/keep for diff)
└── communes.topo.json            # OUTPUT (committed, ~tunable budget)
scripts/build-topojson.mjs        # EDIT: source-load + re-key + simplify knobs + budget assert
site/scripts/validate/map.mjs     # EDIT: raise TOPO_MAX_BYTES, add gzip assert
site/scripts/sync-data.mjs        # NO CHANGE (mirror is generic)
```

### Pattern 1: Quantization is the dominant fidelity lever (not just retention %)
**What:** TopoJSON `quantization=N` lays an N×N integer grid over the bounding box; all coordinates snap to it. Over Chile's ~43° N–S extent, `q=500` ⇒ ~8–10 km cells (blocky). `q≈10000` ⇒ ~0.4–0.5 km cells (smooth coast).
**When:** Always set quantization explicitly and high enough that the cell is finer than the smallest feature you care about. For Chile, target sub-kilometer.
**Evidence (measured this session on real CUT-keyed input):**
```
config                         raw        gzip    arc-pts  grid          CUT integrity
0.05% / q=500  (CURRENT)        87 KB      21 KB    5,085   7.9×10.2 km   346, 0 miss/orphan/dup
10%   / q=10000                367 KB     107 KB   35,885   0.40×0.51 km  346, 0 miss/orphan/dup
10%   / q=20000                397 KB     120 KB   36,001   0.20×0.26 km  346, 0 miss/orphan/dup
8%    / q=10000                335 KB      99 KB     —        —            (size only)
5%    / q=10000                287 KB      86 KB     —        —            (size only)
```

### Pattern 2: TopoJSON shared-arc simplification preserves topology for free
**What:** Because TopoJSON stores shared borders as single arcs, simplifying the arc moves both adjacent comunas' borders identically → **no gaps, no slivers, no overlaps**. Simplifying per-polygon GeoJSON instead would crack shared borders apart.
**When:** Always simplify in TopoJSON/topology mode (mapshaper does this natively when output is topojson, and even simplifies in topology space for geojson input). The current script already gets this right — preserve it.
**Anti-pattern:** Simplifying each comuna's GeoJSON ring independently (e.g. turf/simplify per feature) — produces visible gaps along borders.

### Pattern 3: `keep-shapes` to protect tiny coastal/island comunas
**What:** `mapshaper -simplify … keep-shapes` prevents small polygons (e.g. Juan Fernández, Isla de Pascua, tiny coastal comunas) from collapsing to nothing at aggressive %.
**When:** Always keep this flag (the current script already has it). Verify the tiny-comuna CUTs survive in the post-build 346-feature assertion.

### Anti-Patterns to Avoid
- **Lowering the validator budget to "pass":** The 100 KB raw gate is the bug, not a target. Raise it; do not re-over-simplify to satisfy it.
- **Switching to react-leaflet `<GeoJSON>`:** Forbidden by CLAUDE.md; re-introduces per-hover re-render. The current native `L.geoJSON()` path is correct — do not touch the render architecture.
- **Joining geometry to CEAD by name only when a real CUT code exists:** chilemapas ships `codigo_comuna` — prefer code-join (after zero-pad normalization) over fragile name-matching.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polygon simplification | Custom Douglas-Peucker / vertex decimation | mapshaper `-simplify visvalingam keep-shapes` | Topology-aware shared-arc simplification; handles MultiPolygon, tiny-shape protection, quantization |
| Topology preservation | Manual border-stitching/sliver removal | TopoJSON shared arcs (mapshaper `-o format=topojson`) | Shared borders simplify identically by construction |
| TopoJSON decode in browser | Hand-written arc/delta decoder | `topojson-client` `feature()` | Already a dep; correct delta+quantization decoding |
| Shapefile→GeoJSON / reproject | Custom parser / proj math | mapshaper (reads .shp, `-proj wgs84`) | If using raw INE shapefile, mapshaper reprojects in one flag |
| Geometry validity (self-intersection) | Manual geometry fixing | mapshaper `-clean` | Fixes overlaps/gaps/invalid rings before encode |

**Key insight:** Every step of this pipeline already exists in `scripts/build-topojson.mjs` and is correct. Phase 10 is a **parameter + source change**, not new machinery. The biggest risk is *over-engineering a rewrite* of a working script.

## Runtime State Inventory

> This phase replaces a committed data artifact. No live-service/OS-registered/secret state is involved. Audited explicitly below.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | The asset itself: `data/cead/geo/communes.topo.json` (committed) + `data/cead/geo/communes-raw.geojson` (committed GADM source). New source file `communes-chilemapas.geojson` to be committed/decided. | Regenerate `.topo.json`; decide whether to commit the new raw source (see note). |
| Live service config | None — no external service stores this geometry. Cloudflare Pages serves whatever is in `dist/`. | None. |
| OS-registered state | None. | None — verified: no scheduler/cron references the geometry; GitHub Actions cron jobs (`scrape-cead`, `scrape-news`) touch CEAD/RSS JSON, not geo. |
| Secrets / env vars | None — geometry build uses no API key. | None. |
| Build artifacts | `site/public/data/cead/geo/communes.topo.json` (gitignored, regenerated by `sync-data.mjs`); `dist/` copy (regenerated on build). Stale public copy possible on OneDrive desync (see MEMORY). | Re-run build+validate **in one chained command** (OneDrive desync mitigation). |

**Commit-source note:** `communes-raw.geojson` (GADM, 5.3 MB) IS committed today despite `.gitignore` listing it — verify with `git ls-files`. For chilemapas, decide: commit the raw source for offline reproducibility (recommended — the build script header already documents a download URL pattern) vs. gitignore + document the download URL. Reproducibility (SC #5) favors committing the raw source or pinning an exact download URL in the script header.

## Common Pitfalls

### Pitfall 1: The validator size gate blocks any real geometry
**What goes wrong:** `site/scripts/validate/map.mjs` hard-fails the build at `size >= 102400` (100 KB raw). Every recognizable config measured here is 287–397 KB raw. The build will fail CI until this is raised.
**Why it happens:** The 100 KB number was a Phase-3 carry-over from a 222 KB prototype, never a perf-derived budget.
**How to avoid:** Raise `TOPO_MAX_BYTES` to the agreed budget (recommend ~**420000** ≈ 410 KB raw) AND add a gzip-size assertion (recommend ≤ ~140 KB gzip) since that's what users actually download. Update the matching assertion inside `build-topojson.mjs` (it shares the `<100 KB` logic and three fallback configs — those fallbacks would silently re-over-simplify).
**Warning signs:** Build prints "Over 100 KB — trying more aggressive simplification" and ships a blocky asset anyway.

### Pitfall 2: Zero-padding CUT mismatch on source swap (the #1 join failure)
**What goes wrong:** chilemapas `codigo_comuna` is canonically a **5-char zero-padded** string; regions 1–9 produce leading-zero codes (e.g. Antofagasta region 2 → comuna `"02101"`). CEAD CUT is stored **unpadded** (`"2101"`). A naive code-join then misses/duplicates and drops comunas or paints them default-grey.
**Why it happens:** INE codigo_comuna formatting differs from CEAD's raw-digit storage (STATE.md: "CUT codes stored as raw string digits without zero-padding").
**How to avoid:** In the re-key step, normalize source code → CUT with `String(Number(code))` (strips leading zeros) OR `code.replace(/^0+/,'')`, then assert against `index.json` CUTs. Keep the existing 346/0-missing/0-orphan assertion as the gate.
**Warning signs:** Build assertion reports missing CUTs for all region-1..9 comunas, or feature count ≠ 346.

### Pitfall 3: Canvas hover/redraw cost with 7× more vertices
**What goes wrong:** 36k arc points vs 5k means more canvas geometry to redraw on hover restyle and pan/zoom. On mid-range mobile this *could* introduce jank — the perf side of GEO-02.
**Why it happens:** Higher fidelity = more vertices to rasterize. (Note: it does NOT cause React re-renders — render path is native `L.geoJSON()`, confirmed.)
**How to avoid:** (a) Keep `L.canvas()` (already done). (b) Pick the *lowest* retention % that still reads as recognizable (10% is plenty; don't chase 20%). (c) Verify hover/pan/zoom on a throttled mobile profile (Phase-3 used Moto G4 + Fast 3G as the manual gate). (d) A low-zoom dot layer already exists (`LowZoomDotLayer.ts`) — at country zoom the polygons may already be substituted by dots, reducing cost.
**Warning signs:** Hover restyle visibly lags; pan stutters on mobile profile.

### Pitfall 4: Tiny island/coastal comunas collapse or land in the sea
**What goes wrong:** Isla de Pascua, Juan Fernández, and slivered coastal comunas can vanish at aggressive simplification or, with the Antártica-style placeholder approach, sit at an arbitrary location.
**How to avoid:** Keep `keep-shapes`. If chilemapas/geoBoundaries actually include Antártica (12202) and offshore islands, drop the GADM placeholder hack. Verify each oceanic-territory CUT appears post-build.
**Warning signs:** A region's island comuna missing from the 346 count or rendering as a degenerate dot.

### Pitfall 5: OneDrive build-artifact desync (known env issue)
**What goes wrong:** Repo lives inside OneDrive; `dist/`/`public/data/` can desync between separate processes (MEMORY: onedrive-build-artifacts-desync).
**How to avoid:** Run regeneration + sync + validate in a single chained command; don't split build and validate across tool calls.

## Code Examples

### Re-tuned mapshaper invocation (replace the SIMPLIFY_CONFIGS loop)
```bash
# Source: mapshaper CLI (github.com/mbloch/mapshaper) — measured this session
mapshaper rekeyed.geojson \
  -clean \
  -simplify visvalingam percentage=10% keep-shapes \
  -o format=topojson quantization=10000 communes.topo.json
# → ~367 KB raw / ~107 KB gzip, 346 features, ~0.4 km grid, 0 missing/orphan CUTs
```

### CUT zero-pad normalization in the re-key step (chilemapas path)
```js
// Source: derived from index.json CUT scheme (unpadded) vs INE codigo_comuna (5-char padded)
function srcCodeToCut(code) {
  // "02101" -> "2101" ; "13101" -> "13101"
  return String(parseInt(code, 10));
}
// then: assert indexByCut.has(srcCodeToCut(feature.properties.codigo_comuna))
```

### Join-integrity assertion (keep/extend the existing one)
```js
// Source: existing build-topojson.mjs Step 5, generalized
const wantCuts = new Set(indexEntries.map(c => c.cut));
const gotCuts  = features.map(f => f.properties.id);
const missing  = [...wantCuts].filter(c => !gotCuts.includes(c));
const orphan   = gotCuts.filter(c => !wantCuts.has(c));
const dup      = gotCuts.filter((c,i) => gotCuts.indexOf(c) !== i);
if (features.length !== 346 || missing.length || orphan.length || dup.length) {
  console.error({ count: features.length, missing, orphan, dup });
  process.exit(1);
}
```

### Gzip-size assertion to add to validate/map.mjs
```js
// Source: Node zlib — assert the user-facing (compressed) size
import { gzipSync } from 'node:zlib';
const gz = gzipSync(readFileSync(TOPO_PATH)).length;
if (gz > 143360) fail('TopoJSON gzip budget', `${gz} B > 140 KB gzip`);
else pass(`TopoJSON gzip budget (${gz} B < 140 KB)`);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GADM-derived geometry (current ship) | INE-derived openly-licensed source (chilemapas / geoBoundaries) | Phase 10 | Removes commercial/redistribution license risk; gains a real commune code (`codigo_comuna`) for robust join |
| `q=500` (8–10 km grid) | `q≈10000` (sub-km grid) | Phase 10 | Recognizable coastline/borders |
| `<100 KB raw` validator gate | ~410 KB raw / ~140 KB gzip, dual assertion | Phase 10 | Gate stops blocking real geometry; budget expressed against what users download |

**Deprecated/outdated:**
- The `<100 KB raw` budget and the `0.05% / q=500` config: artifacts of a Phase-3 prototype constraint, not perf-derived. Retire both.
- GADM source: retire for license reasons (keep `communes-raw.geojson` only for diff/QA, not as the ship source).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | chilemapas `data_geojson` comunas file uses `codigo_comuna` (INE CUT) as the code property, EPSG:4326, 346 comunas | Standard Stack / Pitfall 2 | If property name differs, re-key needs a name-match fallback (same as GADM); not fatal but changes the join code |
| A2 | chilemapas codes are 5-char zero-padded (region 1–9 → leading zero) | Pitfall 2 | If already unpadded, the `parseInt` normalization is a harmless no-op |
| A3 | GPL-3 (chilemapas) and CC-BY-4.0 (geoBoundaries) are acceptable for this AdSense commercial site with attribution | Standard Stack | If the user wants to avoid GPL-3 "derived data" interpretation, fall back to CC-BY geoBoundaries; user must confirm licensing posture |
| A4 | Recommended budget ~410 KB raw / ~140 KB gzip is acceptable to the project | Size/Perf Budget | If stricter, drop to 8%/q=10k (~335 KB / ~99 KB gzip) — still recognizable; user/perf test decides |
| A5 | chilemapas/geoBoundaries include or can substitute Antártica (12202) + oceanic islands; if not, reuse the existing placeholder | Pitfall 4 | If absent, keep the GADM-style placeholder approach for those CUTs |
| A6 | INE geoportal/BCN direct download as a deeper fallback is open-licensed and EPSG:4326-or-reprojectable | Standard Stack | Not fetched this session — verify before relying on it |

**This table is non-empty:** the source swap (A1–A3, A5) and the budget number (A4) need human confirmation in discuss-phase before being locked. The *fidelity mechanism* (quantization) and *join-integrity* findings are VERIFIED/measured, not assumed.

## Open Questions

1. **Which boundary source, given licensing?**
   - Known: GADM (current) is non-commercial/no-redistribution → a real risk for an AdSense public-repo site. chilemapas (GPL-3, INE) and geoBoundaries (CC-BY-4.0) are open.
   - Unclear: User's tolerance for GPL-3 on *derived data* vs preferring permissive CC-BY.
   - Recommendation: Default to **chilemapas** (authoritative INE + real CUT code); offer geoBoundaries as the permissive-license fallback. Confirm in discuss-phase.

2. **Exact size/perf budget number.**
   - Known: 10%/q=10k = 367 KB raw / 107 KB gzip is recognizable and integrity-clean. Cloudflare serves gzip/brotli, so gzip is the user-facing number.
   - Unclear: Whether ~107 KB gzip transfer is acceptable on the map page's perf budget (the map island already loads Leaflet + payload).
   - Recommendation: Set budget at **≤140 KB gzip / ≤420 KB raw**; verify cold map render on a throttled mobile profile (Phase-3's Moto G4 + Fast 3G gate) as the GEO-02 perf check.

3. **Commit the raw source or pin a download URL?**
   - Recommendation: Commit `communes-chilemapas.geojson` (or pin an exact, dated download URL in the script header) so SC #5 reproducibility holds without network access. Update `.gitignore` accordingly.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| mapshaper (global CLI) | Simplification + TopoJSON encode | ✓ | 0.7.22 (latest 0.7.25) | `npm i -g mapshaper` |
| Node.js | build-topojson.mjs + sync-data.mjs | ✓ | v22.21.1 | — |
| topojson-client | Runtime decode | ✓ | 3.1.0 (in site deps) | — |
| Python 3.12 | (optional) source inspection/normalization | ✓ | present | Node can do all of it |
| Source dataset (chilemapas/geoBoundaries) | New geometry | ✗ (not yet downloaded) | — | GADM already on disk (license-blocked for ship) |
| Internet (one-time source download) | Acquire new source | assume ✓ at dev time | — | If offline, must use a committed source |

**Missing dependencies with no fallback:** none blocking — toolchain is fully present.
**Missing dependencies with fallback:** the new boundary source must be downloaded once (one-time, dev-time); commit it for reproducibility.

## Validation Architecture

> nyquist_validation is enabled (config: `workflow.nyquist_validation = true`). This phase is data/build, not feature code — validation is build-assertion + structural-validator based, with one manual perf/visual gate.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Repo structural validators (`site/scripts/validate/*.mjs`) + in-script build assertions (`scripts/build-topojson.mjs`). No unit-test runner needed for a data artifact. |
| Config file | none (validators are standalone Node scripts run in CI) |
| Quick run command | `node scripts/build-topojson.mjs` (asserts 346 / integrity / budget during regeneration) |
| Full suite command | `cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs` (chain to avoid OneDrive desync) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEO-01 | 346 features, keyed by CUT, 0 missing/orphan/dup vs `index.json`; Santiago 13101 present | structural | extend assertion in `scripts/build-topojson.mjs` + `validate/map.mjs` feature-count check | ✅ exists (extend for orphan/dup/missing) |
| GEO-01 | Polygons recognizable as real comuna shapes (coastline/borders) | visual / manual | open `/map/` + `/es/mapa/` in browser; compare to current | ❌ manual gate (HUMAN-UAT) |
| GEO-02 | Asset within size budget (raw + gzip) | structural | raise `TOPO_MAX_BYTES`; add gzip assertion in `validate/map.mjs` (see code example) | ✅ exists (modify) |
| GEO-02 | Smooth pan/zoom/hover, no new console errors | performance / manual | throttled-mobile profile (Moto G4 + Fast 3G); console check on map pages | ❌ manual gate (HUMAN-UAT) |
| GEO-02 | Reproducible regeneration | structural | `node scripts/build-topojson.mjs` runs clean and re-emits identical-shape asset | ✅ exists |

### Sampling Rate
- **Per task commit:** `node scripts/build-topojson.mjs` (fails fast on integrity/budget).
- **Per wave merge:** `cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs` (single chained command — OneDrive desync mitigation).
- **Phase gate:** full `cd site && npm run build` green + manual browser visual+perf check on `/map/` and `/es/mapa/` before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `scripts/build-topojson.mjs` — extend Step-5 assertion to explicitly check **missing + orphan + duplicate** CUTs (currently only checks count + Santiago) — covers GEO-01.
- [ ] `scripts/build-topojson.mjs` + `site/scripts/validate/map.mjs` — raise the 100 KB gate and add a **gzip-size assertion** — covers GEO-02.
- [ ] No new test framework needed — existing validators + build assertions cover the automatable requirements; visual/perf are human gates by nature.

## Security Domain

> `security_enforcement` is not set in config (treat as enabled). This phase introduces no auth/session/access-control/crypto surface. Input is a static, offline-processed geometry file. ASVS surface is minimal.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth touched) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (low) | Build-time: validate source GeoJSON is well-formed JSON + expected schema before re-key; runtime `safeFetch` already guards decode (never `eval`, graceful 404/parse failure). Geometry is build-time data, not user input. |
| V6 Cryptography | no | — |

### Known Threat Patterns for static-geometry pipeline
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Tampered/corrupt source dataset shipped | Tampering | Commit raw source (or pin dated URL) + build assertions (346/integrity) reject bad geometry before it ships |
| License non-compliance (current GADM) | (Legal, not STRIDE) | Swap to chilemapas/geoBoundaries; add attribution |
| Malformed TopoJSON crashing the island | Denial of Service (client) | Existing `safeFetch` + `loadError` graceful path in `MapIsland.tsx` already handles fetch/parse failure without throwing |

## Sources

### Primary (HIGH confidence)
- Repo files read directly: `scripts/build-topojson.mjs`, `site/src/components/map/MapIsland.tsx`, `site/src/components/map/ChoroplethLayer.ts`, `site/scripts/sync-data.mjs`, `site/scripts/validate/map.mjs`, `data/cead/geo/communes.topo.json`, `data/cead/geo/communes-raw.geojson`, `data/cead/meta/index.json`, `.gitignore` — current asset, join key, mirror, render path, validator gate.
- Empirical mapshaper simplification matrix (raw+gzip sizes, arc counts, grid resolution, CUT integrity) measured this session on the real CUT-keyed input — `mapshaper 0.7.22`.
- `npm view mapshaper version` → 0.7.25; `npm view topojson-client version` → 3.1.0.
- [gadm.org/license](https://gadm.org/license.html) — GADM non-commercial / no-redistribution license (verified).

### Secondary (MEDIUM confidence)
- [github.com/pachadotdev/chilemapas](https://github.com/pachadotdev/chilemapas) + [cran chilemapas.pdf](https://cran.r-project.org/web/packages/chilemapas/chilemapas.pdf) + [pacha.dev/chilemapas](https://pacha.dev/chilemapas/) — GPL-3, INE/SUBDERE/BCN source, 346 comunas, `data_geojson`/`data_topojson`.
- [geoboundaries.org](https://www.geoboundaries.org/countryDownloads.html) + Google Earth Engine catalog — CC-BY 4.0, CHL ADM3 available.

### Tertiary (LOW confidence)
- chilemapas exact property name / zero-pad format (A1, A2) — inferred from INE codigo_comuna convention; verify on actual file before locking.
- INE geoportal/BCN direct download (A6) — not fetched this session.

## Metadata

**Confidence breakdown:**
- Current asset + consumption + mirror + render path: HIGH — read directly from repo.
- Fidelity mechanism (quantization) + size/perf matrix + join integrity: HIGH — measured empirically this session.
- Source recommendation: MEDIUM — licensing verified; exact chilemapas property/padding needs file-level confirmation (A1, A2).
- Size budget number: MEDIUM — measured, but the chosen ceiling is a project decision (A4) plus a manual mobile-perf gate.

**Research date:** 2026-06-15
**Valid until:** ~2026-07-15 (stable domain; mapshaper/topojson-client are mature; only the source-dataset URLs/licenses could drift)
