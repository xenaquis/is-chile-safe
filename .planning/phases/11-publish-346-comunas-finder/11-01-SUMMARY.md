---
phase: 11-publish-346-comunas-finder
plan: "01"
subsystem: build-pipeline
tags: [memoization, validation, rollout, data-loader, coverage]
dependency_graph:
  requires: []
  provides: [memoized-data-loaders, coverage-validator, rollout-346-default]
  affects: [site/src/lib/data.ts, site/scripts/validate/coverage.mjs, site/scripts/validate/rollout.mjs]
tech_stack:
  added: []
  patterns: [module-level-memoization, dist-only-validator, index-json-as-single-source-of-truth]
key_files:
  modified:
    - site/src/lib/data.ts
    - site/scripts/validate/rollout.mjs
  created:
    - site/scripts/validate/coverage.mjs
decisions:
  - "_indexCache / _communeCache / _regionCache / _natAvg / _regAvg — five module-level caches in data.ts; zero behavior change; no TTL (build is single-pass)"
  - "coverage.mjs derives expected count from data/cead/meta/index.json — same source as updated rollout.mjs; both validators share one source of truth"
  - "rollout.mjs default expectation is now index.length (346); EXPECT_ALL is kept as alias; === 12 config assertion relaxed to >= 1 && <= 346"
metrics:
  duration: "~20m"
  completed: "2026-06-15"
  tasks: 3
  files: 3
---

# Phase 11 Plan 01: Wave-0 Foundation (Memoization + Coverage Validator + Rollout Fix) Summary

Build-time memoization in data.ts (five module-level caches) removes the O(n^2) readFileSync pattern that risked CI/Cloudflare timeout at 346×2 pages; coverage.mjs scaffolds the four COMU-03 assertions derived from index.json; rollout.mjs now defaults to 346/locale without EXPECT_ALL.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add build-time memoization to data.ts loaders | ba9f9e3 | site/src/lib/data.ts |
| 2 | Scaffold coverage.mjs validator (A-D) | 7ebf132 | site/scripts/validate/coverage.mjs |
| 3 | Update rollout.mjs default expectation | a985c16 | site/scripts/validate/rollout.mjs |

## What Was Built

### Task 1 — data.ts memoization
Five module-level caches added at the top of the Core Loaders section:
- `_indexCache: CommuneMeta[] | null` — loadIndex() reads once
- `_communeCache: Map<string, CommuneData>` — loadCommune(cut) cached per CUT
- `_regionCache: Map<string, RegionData>` — loadRegion(regionId) cached per region file ID
- `_natAvg: number | null` — loadNationalAverage() computed once
- `_regAvg: Map<string, number>` — loadRegionalAverage(regionId) computed once per region

No exported signatures changed. nearestComparable() inherits the speedup automatically. The CR-fix (cut populated from argument, lines ~152-158) is preserved in the enriched object.

### Task 2 — coverage.mjs
New validator at `site/scripts/validate/coverage.mjs`:
- Assertion A: route-count — dist/commune/* === dist/es/comuna/* === index.length
- Assertion B: no-orphan-link — scans all dist/*.html, asserts each /commune/{slug}/ href has a page
- Assertion C: sitemap-coverage — parses dist/sitemap-0.xml, counts EN + ES commune <loc> entries and checks directory URLs
- Assertion D: directory-completeness — dist/communes/index.html and dist/es/comunas/index.html contain >=346 distinct commune hrefs

Expected count from `data/cead/meta/index.json` (not hardcoded). Not wired into all.mjs (Plan 04 job). Allowed to report failures at Wave 0 since rollout flip and directory pages are not yet built.

### Task 3 — rollout.mjs update
- `expectedCount` now resolves to `indexData.length` (346) in both default and EXPECT_ALL=true paths
- Config assertion changed from `=== 12` to `>= 1 && <= 346`
- Santiago/Maipú includes() sanity checks preserved
- Reciprocity and parity assertions (b) unchanged

## Verification

- `npx tsc --noEmit` — zero new errors in data.ts
- `node -c scripts/validate/coverage.mjs` — parses OK
- `node -c scripts/validate/rollout.mjs` — parses OK
- `grep "strictEqual(rollout.enabled.length, 12"` — returns nothing (assertion gone)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. coverage.mjs intentionally reports FAIL at Wave 0 (directory pages and 346 rollout not yet built); this is documented in the file header comment and is expected behavior.

## Threat Flags

No new security-relevant surface introduced. All changes are build-time validators and memoization caches over trusted repo JSON.

## Self-Check: PASSED

- site/src/lib/data.ts: confirmed modified (ba9f9e3)
- site/scripts/validate/coverage.mjs: confirmed created (7ebf132)
- site/scripts/validate/rollout.mjs: confirmed modified (a985c16)
- All three commit hashes present in git log
