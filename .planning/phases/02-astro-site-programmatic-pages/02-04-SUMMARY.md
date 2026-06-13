---
phase: 02-astro-site-programmatic-pages
plan: "04"
subsystem: frontend/pages
tags: [astro, region-pages, i18n, seo, ranking-table, validators]
dependency_graph:
  requires: [02-02, 02-03]
  provides: [region-pages-en, region-pages-es, region-validator, structure-validator]
  affects: [sitemap, commune-pages-breadcrumb]
tech_stack:
  added: []
  patterns:
    - "getStaticPaths iterating region files 1..16 (no rollout gate)"
    - "Regional aggregate = MEAN of non-low-pop commune rates (not SUM series)"
    - "National position among 16 regions via all-region rate comparison"
key_files:
  created:
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/scripts/validate/region.mjs
  modified:
    - site/scripts/validate/structure.mjs
decisions:
  - "loadRegionalAverage pattern reused inline in getStaticPaths — avoided calling loadRegionalAverage() 16 times in a loop by computing all 16 region rates inline for national-position derivation"
  - "loadNationalAverage() called once at page render time for the national-avg StatCard"
  - "structure.mjs stub fully replaced: now checks <title>, canonical, 3x hreflang, non-empty body on sampled commune + region pages; safe no-op when dist/ absent"
metrics:
  duration: "~12 minutes"
  completed: "2026-06-13"
  tasks_completed: 2
  files_changed: 4
---

# Phase 02 Plan 04: Region Pages (EN + ES) — Summary

**One-liner:** 16×2 bilingual region pages with regional-mean aggregates, sorted commune ranking tables, reciprocal hreflang, and Dataset+Place JSON-LD; region and structure validators green.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | EN + ES region page routes with aggregates + ranking table | 78597b0 | site/src/pages/region/[slug].astro, site/src/pages/es/region/[slug].astro |
| 2 | Region validator + structure validator fill | 78597b0 | site/scripts/validate/region.mjs, site/scripts/validate/structure.mjs |

## What Was Built

### Task 1: Bilingual Region Pages

- `site/src/pages/region/[slug].astro` — EN pages at `/region/{slug}/`
- `site/src/pages/es/region/[slug].astro` — ES pages at `/es/region/{slug}/`

Both iterate region files 1–16 via `loadRegion()` in `getStaticPaths()`. No rollout gate (D-26).

**Data derivations implemented:**
- `aggregatePopulation` = sum of all communes' populations for that region
- `thisRegionRate` = MEAN of non-low-pop commune rates (never the SUM series)
- `nationalPosition` = count of regions with strictly higher mean rate + 1
- `rankingRows` = all communes in region loaded via `loadCommune()`, sorted by rate descending

**Page structure per UI-SPEC Page Type 2:**
1. RegionHero (h1 + population + commune count)
2. RegionKeyStats (3 StatCards: avg rate, national position, national avg)
3. RegionSparkline (regional aggregate series via existing `Sparkline` component)
4. CommuneRankingTable (sorted by rate desc, low-pop marked *, names link to commune pages)
5. MapPlaceholderSlot (data-phase3-mount="region-map")
6. MethodologyCaveat

Each page has reciprocal hreflang (en/es/x-default), self-canonical, and Dataset+AdministrativeArea JSON-LD. Zero client:* directives.

### Task 2: Validators

- `region.mjs`: asserts 16 EN + 16 ES region dirs; checks table row count >= commune count; checks hreflang, canonical, JSON-LD on Metropolitana + Aysen samples; checks low-pop * marker.
- `structure.mjs`: replaced stub with sampler checking `<title>`, `rel="canonical"`, 3 hreflang tags, non-empty body on one EN commune + one ES commune + EN region/metropolitana + ES region/metropolitana; exits 0 when dist/ absent.

## Verification Results

- `npx astro check`: 0 errors, 0 warnings
- `npm run build`: 57 pages built (16 EN region + 16 ES region + commune pages + index); exit 0
- `node scripts/validate/region.mjs`: PASSED — all 22 assertions green
- `node scripts/validate/structure.mjs`: PASSED — 4 sample pages validated

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written.

**Note:** `t` (i18n strings) variable was declared but never used since all strings are inline English/Spanish in the templates. Removed the unused import to eliminate astro check hints.

## Known Stubs

None. All region pages render real CEAD data. No placeholder content.

## Threat Surface Scan

No new security-relevant surface introduced beyond what the plan's threat model covers:
- T-02-10: region JSON-LD emitted via `JSON.stringify` in BaseLayout — mitigated.
- T-02-11: commune slugs in ranking-table links come from trusted Phase-1 meta; Astro auto-escapes expressions — mitigated.
- T-02-12: only public CEAD aggregates rendered — accepted.

## Self-Check: PASSED

Files exist:
- site/src/pages/region/[slug].astro — FOUND
- site/src/pages/es/region/[slug].astro — FOUND
- site/scripts/validate/region.mjs — FOUND
- site/scripts/validate/structure.mjs — FOUND (modified)

Commits:
- 78597b0 feat(02-04): add 16×2 region pages with aggregates + commune ranking — FOUND
