---
phase: 10-high-resolution-commune-geometry
verified: 2026-06-15T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: null
  note: Initial verification (no prior VERIFICATION.md)
---

# Phase 10: High-Resolution Commune Geometry Verification Report

**Phase Goal:** Replace the heavily-simplified `communes.topo.json` (88KB) with real Chilean commune boundaries so polygons render as recognizable comuna shapes for visual comparison on the map — while keeping the shipped asset within a file-size/performance budget that preserves smooth Leaflet-canvas rendering of all ~346 comuna polygons.
**Verified:** 2026-06-15
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (Success Criterion) | Status | Evidence |
|---|---------------------------|--------|----------|
| 1 | Asset regenerated from authoritative Chilean source, every CEAD comuna keyed by commune code, no comuna dropped/mis-joined | ✓ VERIFIED | Parsed shipped `data/cead/geo/communes.topo.json`: object `communes-rekeyed`, **346 geometries, 346 unique ids, 0 dup**, Santiago `13101` present. Cross-checked against `data/cead/meta/index.json` (346 CUTs): **0 missing, 0 orphan**. `site/public/` mirror byte-identical (353,696 B). Source is chilemapas (`build-topojson.mjs` header + `RAW_GEOJSON = communes-chilemapas.geojson`, line 54). |
| 2 | Polygons visually recognizable as real comuna shapes (coastline/borders) — browser-verified | ✓ VERIFIED (manual gate) | 10-HUMAN-UAT.md Gate 1 signed PASS by xenaquis 2026-06-15 (dev server :4324). Recognizability is an intrinsic visual judgment with no automatable assertion (per 10-VALIDATION.md Manual-Only table). |
| 3 | Asset within size/performance budget; smooth pan/zoom/hover, no regression | ✓ VERIFIED | Asset = **353,696 B raw / 87,672 B gzip** (measured by verifier). Validator `site/scripts/validate/map.mjs` asserts raw < 430,080 (≤420 KB, line 48) AND gzip ≤ 143,360 (≤140 KB, line 49) — both PASS. Build script `build-topojson.mjs` enforces same dual budget (lines 195-220). Perf = manual gate, 10-HUMAN-UAT.md Gate 2 PASS. |
| 4 | Choropleth colours every comuna, panel opens, zero new console errors | ✓ VERIFIED | Render path untouched: `ChoroplethLayer.ts` joins on `feature.properties.id` (CUT) via native `L.geoJSON`+`L.canvas()`; `MapIsland.tsx:157` still fetches same `/data/cead/geo/communes.topo.json`. CONTEXT confirms no render-architecture change. Console/colour confirmed in 10-HUMAN-UAT.md regression checks (PASS). |
| 5 | Reproducible regeneration — script/documented procedure from committed source | ✓ VERIFIED | Raw source `data/cead/geo/communes-chilemapas.geojson` is git-tracked (`git ls-files` confirms); removed from `.gitignore`. `build-topojson.mjs` header documents source URL, download date, and 8-step procedure; entry point `node scripts/build-topojson.mjs`. `srcCodeToCut` zero-pad helper (line 67) handles the code-join. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/cead/geo/communes.topo.json` | 346 features keyed by CUT, recognizable geometry | ✓ VERIFIED | 346 geometries, 0 missing/orphan/dup vs index.json, Santiago present, 353,696 B raw |
| `site/public/data/cead/geo/communes.topo.json` | Byte-identical mirror | ✓ VERIFIED | Same 353,696 B raw / 87,672 B gzip; served to `dist/` (validator PASS) |
| `data/cead/geo/communes-chilemapas.geojson` | Committed raw source for reproducibility | ✓ VERIFIED | git-tracked; un-ignored in `.gitignore` |
| `scripts/build-topojson.mjs` | Source swap + srcCodeToCut + 4-way integrity + dual budget asserts | ✓ VERIFIED | chilemapas source, `srcCodeToCut`, missing/orphan/dup asserts in Step-5 (162-178) and Step-8 (238-253), dual budget (195-220) |
| `site/scripts/validate/map.mjs` | Raised gate + gzip assertion | ✓ VERIFIED | `TOPO_MAX_BYTES=430080` (line 48), `TOPO_GZIP_MAX=143360` (line 49), gzip assertion (62-66); no functional `102400` gate remains |
| `site/src/pages/methodology.astro` | chilemapas GPL-3 attribution | ✓ VERIFIED | `<h2>Map boundaries: chilemapas</h2>` + GPL-3 + INE/SUBDERE/BCN + geometry-vs-stats separation |
| `site/src/pages/es/metodologia.astro` | ES attribution parity | ✓ VERIFIED | `<h2>Geometría del mapa: chilemapas</h2>` + GPL-3 ES + matching links |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `MapIsland.tsx` | `communes.topo.json` | `safeFetch('/data/cead/geo/communes.topo.json')` | ✓ WIRED | line 157, asset path unchanged |
| `ChoroplethLayer.ts` | topo features | `L.geoJSON` join on `properties.id` (CUT) | ✓ WIRED | join key matches the topo `properties.id` (verified 346 ids present) |
| `build-topojson.mjs` | `index.json` | 4-way CUT integrity assert | ✓ WIRED | missing/orphan/dup computed from `wantCuts` (index.json) — verifier reproduced 0/0/0 |
| `sync-data.mjs` | `dist/` mirror | predev/prebuild copy | ✓ WIRED | validator confirms `dist/data/cead/geo/communes.topo.json` served |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Structural validator passes | `node site/scripts/validate/map.mjs` | exit 0, all checks PASS (raw budget, gzip budget, 346 features, Santiago join, dist served) | ✓ PASS |
| Topo feature integrity | Node parse of shipped asset vs index.json | 346/346 unique, 0 missing, 0 orphan, 0 dup, 13101 present | ✓ PASS |
| Asset size budget | gzip/raw byte measure | 353,696 B raw / 87,672 B gzip — both within 420 KB / 140 KB | ✓ PASS |
| Raw source reproducibility | `git ls-files communes-chilemapas.geojson` | tracked | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GEO-01 | 10-01, 10-02, 10-03 | Asset regenerated from official source, all CEAD comunas, same join key, recognizable shapes | ✓ SATISFIED | SC-1 + SC-2 verified; marked `[x]` in REQUIREMENTS.md |
| GEO-02 | 10-01, 10-02, 10-03 | Size/perf budget, smooth interaction, no new console errors, reproducible regeneration | ✓ SATISFIED | SC-3 + SC-4 + SC-5 verified; marked `[x]` in REQUIREMENTS.md |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `site/scripts/validate/map.mjs` | 5 | Stale docstring comment says `size < 102400 bytes` | ℹ️ Info | Cosmetic only — actual gate (line 48) uses 430080; the comment describes the old budget. No functional effect; not a blocker. |

No `TBD`/`FIXME`/`XXX` debt markers in any phase-modified file.

### Human Verification Required

None outstanding. Both intrinsic manual gates were harvested into 10-HUMAN-UAT.md and signed PASS by xenaquis on 2026-06-15:
- Gate 1 — Visual Recognizability (GEO-01 SC-2): PASS
- Gate 2 — Throttled-Mobile Perf + console (GEO-02 SC-3/SC-4): PASS
- Regression checks (choropleth all-346, attribution pages, nav): PASS

### Gaps Summary

No gaps. All 5 Success Criteria are observably true in the shipped artifacts:
- SC-1, SC-3 (size), SC-5 verified directly against the committed data and scripts (346/0/0/0 integrity, 353,696 B/87,672 B within dual budget, git-tracked raw source + documented build procedure).
- SC-2, SC-3 (perf), SC-4 (console) are intrinsic manual gates, human-approved in 10-HUMAN-UAT.md.
- SC-4 (choropleth/panel) is additionally protected by the unchanged render path (`properties.id` join, native `L.geoJSON`/`L.canvas()`, same fetch path).
- GEO-01 and GEO-02 both satisfied.

One info-level cosmetic note: a stale docstring comment in `map.mjs` line 5 still references the old 102400-byte budget while the actual gate uses 430080. Non-blocking; optional cleanup.

---

_Verified: 2026-06-15_
_Verifier: Claude (gsd-verifier)_
