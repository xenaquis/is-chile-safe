---
phase: 10-high-resolution-commune-geometry
plan: "02"
subsystem: geo-build-pipeline
tags: [geospatial, build-tooling, source-swap, chilemapas, cut-join, topojson, gpl3]
dependency_graph:
  requires: [GEO-01-join-gate, GEO-02-budget-gate]
  provides: [GEO-01, GEO-02]
  affects:
    - data/cead/geo/communes-chilemapas.geojson
    - data/cead/geo/communes.topo.json
    - scripts/build-topojson.mjs
    - .gitignore
tech_stack:
  added: []
  patterns: [chilemapas-code-join, srcCodeToCut-zero-pad-normalization, single-command-build-sync-validate]
key_files:
  created:
    - data/cead/geo/communes-chilemapas.geojson
  modified:
    - data/cead/geo/communes.topo.json
    - scripts/build-topojson.mjs
    - .gitignore
decisions:
  - chilemapas (GPL-3, INE/SUBDERE/BCN) confirmed as boundary source; 16 region files merged
  - codigo_comuna property confirmed as 5-char zero-padded CUT string (e.g. "01401")
  - srcCodeToCut = String(parseInt(code,10)) strips leading zeros correctly
  - Antártica 12202 placeholder kept — chilemapas lacks it (only 345 features downloaded)
  - GADM name-match machinery (MANUAL_FIXES/norm/indexByNorm) fully retired
metrics:
  duration: 25m
  completed: "2026-06-15"
  tasks: 3
  files: 4
---

# Phase 10 Plan 02: High-Resolution Commune Geometry (Source Swap) Summary

Swapped the boundary source from GADM (license-incompatible) to chilemapas (GPL-3, INE/SUBDERE/BCN-authoritative), committed the raw merged source, added `srcCodeToCut` zero-pad normalization for the code-join, retired the fragile name-matching path, and regenerated `communes.topo.json` at recognizable fidelity — 345.4 KB raw / 85.6 KB gzip, all 346 CEAD CUTs joined with zero missing/orphan/dup.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Acquire + commit chilemapas raw source; un-ignore it | d854b90 | data/cead/geo/communes-chilemapas.geojson, .gitignore |
| 2 | Swap source load + add srcCodeToCut zero-pad normalization in build script | 36e1d4e | scripts/build-topojson.mjs |
| 3 | Retune simplification, regenerate, sync, validate | 8c46505 | data/cead/geo/communes.topo.json |

## What Was Built

**Task 1 — chilemapas raw source:**
- Downloaded 16 per-region GeoJSONs from `pachadotdev/chilemapas` (`data_geojson/comunas/r01.geojson` … `r16.geojson`) and merged into a single FeatureCollection.
- **345 features** (Antártica 12202 absent — expected; placeholder injected in Step 4).
- **CUT property confirmed:** `codigo_comuna`, 5-char zero-padded (e.g. `"01401"` for Arica region 15, `"13101"` for Santiago). A1/A2 assumptions VERIFIED.
- Removed `data/cead/geo/communes-chilemapas.geojson` from `.gitignore`; GADM (`communes-raw.geojson`) and fcorrea (`communes-fcorrea.geojson`) ignore lines unchanged.

**Task 2 — build script source swap + code-join:**
- Changed `RAW_GEOJSON` path to `communes-chilemapas.geojson`.
- Added `srcCodeToCut(code) => String(parseInt(code, 10))` helper.
- Replaced GADM name-match re-key (Step 2/3: `MANUAL_FIXES`, `norm()`, `indexByNorm`) with direct code-join: for each chilemapas feature, normalize `codigo_comuna` via `srcCodeToCut`, look up in `indexByCut` Map keyed by unpadded CUT, re-key to `{ id, name }`.
- Step-4 Antártica placeholder kept conditional — chilemapas lacks 12202, so it is still injected.
- Build ran and printed `346 features, 0 missing, 0 orphan, 0 dup`.

**Task 3 — regenerate + sync + validate:**
- Mapshaper config unchanged from Plan-01 hardening: `visvalingam percentage=10% keep-shapes`, `quantization=10000`.
- Single chained command `node scripts/build-topojson.mjs && cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs` exited 0.
- All 16 validator checks passed.

## Verification Results

```
node scripts/build-topojson.mjs
→ chilemapas features: 345
→ Joined: 345, Skipped: 0
→ Adding Antártica (12202) placeholder polygon...
→ 346 features, 0 missing, 0 orphan, 0 dup
→ mapshaper: [clean] Removed 1199/1200 slivers; [simplify] Repaired 90 intersections
→ Raw: 353696 bytes (345.4 KB) | Gzip: 87672 bytes (85.6 KB)
→ Budget OK: ≤ 420 KB raw AND ≤ 140 KB gzip
→ Step-8: 346 geometries, 0 missing, 0 orphan, 0 dup — TopoJSON integrity OK
→ Santiago (13101): "Santiago" — join verified

cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs
→ PASS [TopoJSON raw budget (353696 bytes < 420 KB)]
→ PASS [TopoJSON gzip budget (87672 B < 140 KB)]
→ PASS [TopoJSON features (346)]
→ PASS [TopoJSON CUT join (Santiago 13101 present)]
→ ... (12 additional structural checks all PASS)
→ map.mjs: PASSED — all map validator checks passed (16/16)
```

**Final asset size:** 353,696 bytes raw (345.4 KB) / 87,672 bytes gzip (85.6 KB)
**Previous asset:** 232,945 bytes raw (227.5 KB) / 62,652 bytes gzip (61.2 KB) [GADM, 10%/q=10000, post-clean — both still blocky due to GADM quality; chilemapas is higher fidelity INE source]

## Deviations from Plan

None — plan executed exactly as written.

**Antártica 12202 note:** chilemapas lacks Antártica as expected. The existing conditional placeholder (`if (!coveredCuts.has('12202'))`) correctly injected a placeholder polygon, satisfying Pitfall 4 guidance.

**A1/A2 Assumption verification:** Both confirmed on the downloaded file. `codigo_comuna` is the correct property name; codes are 5-char zero-padded for regions 01–09 (e.g. `"01401"`, `"02101"`, `"09101"`); no-op for regions 10–16. `parseInt` normalization works correctly.

## Known Stubs

None. The committed `communes.topo.json` is the fully regenerated production asset with all 346 CEAD CUTs joined.

## Threat Flags

None. No new network endpoints or auth surfaces introduced. T-10-03 (tampered source) mitigated by committing exact bytes to the repo + 346/0/0/0 build assertion. T-10-04 (re-key correctness) mitigated by four-way CUT integrity gate that rejects any join miss/orphan/duplicate before the asset is written.

## Self-Check: PASSED

- `data/cead/geo/communes-chilemapas.geojson` committed — `git log d854b90` confirms
- `scripts/build-topojson.mjs` modified — `git log 36e1d4e` confirms; grep "chilemapas" returns match; grep "MANUAL_FIXES" returns only retirement comment
- `data/cead/geo/communes.topo.json` regenerated — `git log 8c46505` confirms
- `.gitignore` no longer contains `communes-chilemapas.geojson` line
- Chained command exits 0, all 16 validator checks pass
- Raw 353,696 B (≤ 430,080 B budget) | Gzip 87,672 B (≤ 143,360 B budget)
