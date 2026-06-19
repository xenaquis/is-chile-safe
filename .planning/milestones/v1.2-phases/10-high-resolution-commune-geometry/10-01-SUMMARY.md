---
phase: 10-high-resolution-commune-geometry
plan: "01"
subsystem: geo-build-pipeline
tags: [geospatial, build-tooling, validation, integrity-gates]
dependency_graph:
  requires: []
  provides: [GEO-01-join-gate, GEO-02-budget-gate]
  affects: [scripts/build-topojson.mjs, site/scripts/validate/map.mjs]
tech_stack:
  added: []
  patterns: [four-way-cut-integrity-assertion, dual-raw-gzip-budget-gate]
key_files:
  modified:
    - scripts/build-topojson.mjs
    - site/scripts/validate/map.mjs
decisions:
  - Budget expressed as dual gate: raw ≤ 420 KB (430080 B) AND gzip ≤ 140 KB (143360 B)
  - Single mapshaper config (10% visvalingam / q=10000) replaces three-config retry loop
  - Four-way CUT assertion (missing/orphan/dup/Santiago) replaces count-only check in both Step-5 and Step-8
metrics:
  duration: 18m
  completed: "2026-06-15"
  tasks: 2
  files: 2
---

# Phase 10 Plan 01: Build-Gate Hardening (Integrity + Budget) Summary

Extended `scripts/build-topojson.mjs` Step-5 and Step-8 with explicit four-way CUT integrity assertion (missing/orphan/dup/Santiago vs `index.json`) and replaced the stale 100 KB raw blocker with a dual ≤ 420 KB raw + ≤ 140 KB gzip budget in both the build script and `site/scripts/validate/map.mjs`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend Step-5 + Step-8 integrity assertion to missing/orphan/dup CUTs | c79c58e | scripts/build-topojson.mjs |
| 2 | Replace 100 KB gate with dual raw+gzip budget (build + validator) | fe4015d | scripts/build-topojson.mjs, site/scripts/validate/map.mjs |

## What Was Built

**Task 1 — Four-way CUT integrity assertion:**
- Step-5 block (pre-mapshaper): builds `wantCuts` from `index.json`; computes `missing`, `orphan`, `dup` from `features.map(f => f.properties.id)`; fails with `process.exit(1)` and logs `{ count, missing, orphan, dup }` if any are non-zero. Prints `"346 features, 0 missing, 0 orphan, 0 dup"` on success.
- Step-8 block (post-mapshaper, on encoded TopoJSON geometries): mirrors the same four-way check. Santiago 13101 presence asserted in both blocks.

**Task 2 — Dual budget gate:**
- `scripts/build-topojson.mjs`: removed the three-config `SIMPLIFY_CONFIGS` retry loop and `< 102400` guard. Replaced with a single `mapshaper` call (`visvalingam 10%, quantization=10000`) plus a dual assertion (`finalSize < 430080 && gzipSize < 143360`). Added `gzipSync` import. Updated header comment to document new budget and config.
- `site/scripts/validate/map.mjs`: raised `TOPO_MAX_BYTES` from 102400 to 430080. Added `import { gzipSync } from 'node:zlib'`. Check 1 now reads file bytes once, asserts raw size < 430080 (PASS label "TopoJSON raw budget … < 420 KB"), then asserts `gzipSync(topoBytes).length <= 143360` (PASS label "TopoJSON gzip budget … < 140 KB").

## Verification Results

```
node scripts/build-topojson.mjs
→ exits 0, prints "346 features, 0 missing, 0 orphan, 0 dup"
→ Raw: 232945 bytes (227.5 KB) | Gzip: 62652 bytes (61.2 KB)
→ Budget OK: ≤ 420 KB raw AND ≤ 140 KB gzip
→ Step-8: 346 geometries, 0 missing, 0 orphan, 0 dup — TopoJSON integrity OK

cd site && node scripts/sync-data.mjs && node scripts/validate/map.mjs
→ PASS [TopoJSON raw budget (232945 bytes < 420 KB)]
→ PASS [TopoJSON gzip budget (62652 B < 140 KB)]
→ PASS [TopoJSON features (346)]
→ PASS [TopoJSON CUT join (Santiago 13101 present)]
→ map.mjs: PASSED — all map validator checks passed (16/16)
```

Note: The GADM source at `10%/q=10000` yields 227 KB raw / 61 KB gzip — smaller than the research matrix's 367/107 KB because mapshaper's `-clean` step removed 3,233 slivers before simplification. Well within budget.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Both scripts operate fully against the current committed asset.

## Threat Flags

None. No new network endpoints, auth paths, or trust boundaries introduced. The hardened assertions directly mitigate T-10-01 (build-time integrity tampering) and T-10-02 (over-budget/malformed asset) as specified in the plan threat register.

## Self-Check: PASSED

- `scripts/build-topojson.mjs` modified — verified (git log c79c58e, fe4015d)
- `site/scripts/validate/map.mjs` modified — verified (git log fe4015d)
- Build passes exits 0 with "346 features, 0 missing, 0 orphan, 0 dup"
- Validator passes all 16 checks including "TopoJSON gzip budget"
- Neither file contains "102400" or "trying more aggressive simplification"
