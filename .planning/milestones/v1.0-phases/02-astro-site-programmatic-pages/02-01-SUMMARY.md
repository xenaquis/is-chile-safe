---
phase: 02-astro-site-programmatic-pages
plan: "01"
subsystem: site-foundation
tags: [astro, data-loader, i18n, color-scale, slug-maps, rollout, validation]
dependency_graph:
  requires:
    - "01-data-foundation/01-04-PLAN.md (data/cead/ JSON output)"
  provides:
    - "site/ Astro 6.4.6 project with pinned deps"
    - "site/src/lib/data.ts build-time data loader"
    - "site/src/lib/colorScale.ts 5-level chroma-js scale"
    - "site/src/lib/slugMaps.ts EN/ES URL pair maps"
    - "site/src/config/i18n.ts EN+ES strings + FAMILY_SLUGS"
    - "site/src/config/rollout.json 12-commune priority batch"
    - "site/scripts/validate/*.mjs runnable stubs"
  affects:
    - "All downstream 02-02..02-06 plans import from site/src/lib/ and site/src/config/"
tech_stack:
  added:
    - "astro@6.4.6"
    - "@astrojs/sitemap@3.7.3"
    - "chroma-js@3.2.0"
    - "topojson-client@3.1.0"
    - "@astrojs/check (devDep)"
    - "@types/chroma-js@^2.4.4"
    - "typescript@^5.0.0"
  patterns:
    - "fileURLToPath(import.meta.url) parent traversal for cross-platform data path (no process.cwd, no symlink)"
    - "regionFileId() mapping: CEAD sub-regional codes (21..99) -> Chilean region numbers (1-16)"
    - "loadNationalAverage() / loadRegionalAverage(): MEAN of non-low-pop commune rates (not JSON sum)"
    - "prefixDefaultLocale:false — EN at root, ES under /es/"
    - "Scoped CSS custom properties from UI-SPEC (no Tailwind)"
key_files:
  created:
    - "site/package.json"
    - "site/astro.config.mjs"
    - "site/tsconfig.json"
    - "site/.nvmrc"
    - "site/src/env.d.ts"
    - "site/src/pages/index.astro"
    - "site/src/lib/data.ts"
    - "site/src/lib/colorScale.ts"
    - "site/src/lib/slugMaps.ts"
    - "site/src/config/i18n.ts"
    - "site/src/config/rollout.json"
    - "site/scripts/validate/structure.mjs"
    - "site/scripts/validate/commune.mjs"
    - "site/scripts/validate/rollout.mjs"
    - "site/scripts/validate/hreflang.mjs"
    - "site/scripts/validate/schema.mjs"
    - "site/scripts/validate/all.mjs"
  modified: []
decisions:
  - "DATA_ROOT uses 4-level parent traversal (../../../../) from site/src/lib/data.ts — RESEARCH.md said 3 levels ('../../..') which only reaches site/, not repo root"
  - "regionFileId() helper added to map CEAD sub-regional codes (e.g. region_id=56 for Algarrobo) to Chilean region files (5.json) — not documented in RESEARCH.md but required by actual data"
  - "loadNationalAverage() returns 5807.84 for 2025 (plausible hundreds-to-low-thousands range, NOT the million-scale sum in national.json)"
metrics:
  duration: "~35min"
  completed: "2026-06-13"
  tasks_completed: 3
  files_created: 17
---

# Phase 02 Plan 01: Astro Foundation + Data Loader Summary

Scaffolded the Astro 6.4.6 static site at `site/` with pinned deps, i18n config, CWD-safe data loader, national/regional average helpers, color scale, slug maps, i18n strings, rollout config, and six runnable validation stub scripts.

## Outcome

All 3 tasks complete, all acceptance criteria verified:
- `npx astro check` exits 0 (0 errors, 0 warnings, 0 hints)
- `node site/scripts/validate/all.mjs` exits 0
- `loadIndex()` returns 346 entries via fileURLToPath parent traversal (no symlink, no process.cwd)
- `loadNationalAverage()` returns 5807.84 (plausible per-capita mean, NOT the national.json sum in the millions)
- `astro.config.mjs` contains `prefixDefaultLocale`, `fileURLToPath`, `@data`, no `process.cwd`, no tailwind
- `rollout.json` has exactly 12 CUT codes including 13101 and 13119
- `i18n.ts` has no forbidden terms; exports EN_STRINGS, ES_STRINGS, FAMILY_SLUGS (7 keys)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 84bcb57 | Scaffold Astro project, pinned deps, i18n config |
| Task 2 | faa8df5 | Data loader, color scale, slug maps, rollout config |
| Task 3 | 49318ba | i18n strings, family slugs, validation stubs |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] DATA_ROOT path depth was 3 levels in RESEARCH.md but needs 4**

- **Found during:** Task 2
- **Issue:** RESEARCH.md Pattern 2 showed `path.resolve(fileURLToPath(import.meta.url), '../../..', 'data', 'cead')` (3 levels). Executing this resolves to `site/` not repo root — `site/src/lib/data.ts` is 4 levels deep: lib -> src -> site -> repo-root.
- **Fix:** Changed traversal to `'../../../..'` (4 levels). Verified with node: correctly resolves to repo root, `loadIndex()` returns 346 entries.
- **Files modified:** site/src/lib/data.ts
- **Commit:** faa8df5

**2. [Rule 2 - Missing Critical Functionality] regionFileId() mapping helper**

- **Found during:** Task 2 (loadNationalAverage() ENOENT on region 56.json)
- **Issue:** CEAD sub-regional codes in `meta/index.json` (e.g. region_id=56 for Algarrobo, 21 for Antofagasta) do not match the region file names (5.json, 2.json). Plan did not document this discrepancy.
- **Fix:** Added `regionFileId()` helper that maps sub-regional codes to parent region numbers: n<=16 kept as-is, n>=20 uses `Math.floor(n/10)`. Verified all 36 unique region_ids map correctly to existing files.
- **Files modified:** site/src/lib/data.ts
- **Commit:** faa8df5

**3. [Rule 1 - Bug] Forbidden terms in i18n.ts JSDoc comment**

- **Found during:** Task 3 acceptance criteria check
- **Issue:** JSDoc comment explaining D-05 included the actual forbidden strings ("zona peligrosa", etc.) which would fail the acceptance criterion grep.
- **Fix:** Rewrote comment to reference CONTEXT.md without repeating the forbidden terms.
- **Files modified:** site/src/config/i18n.ts
- **Commit:** 49318ba

## Self-Check

- site/package.json: FOUND
- site/astro.config.mjs: FOUND
- site/src/lib/data.ts: FOUND
- site/src/lib/colorScale.ts: FOUND
- site/src/lib/slugMaps.ts: FOUND
- site/src/config/i18n.ts: FOUND
- site/src/config/rollout.json: FOUND
- site/scripts/validate/all.mjs: FOUND
- Commits 84bcb57, faa8df5, 49318ba: FOUND

## Self-Check: PASSED
