---
phase: 15-crime-type-seo-ranking-pages
plan: "02"
subsystem: pages, seo
tags: [crime-ranking, seo, hreflang, jsonld, featured_rates, itemlist]
dependency_graph:
  requires: [15-01]
  provides: [crime-ranking-en-pages, crime-ranking-es-pages, homicide-reciprocal-spoke]
  affects:
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
tech_stack:
  added: []
  patterns:
    - featured_rates.homicidios dataSource branch (Pitfall 1 fix)
    - Astro.params for route param + Astro.props for data props (hreflang fix)
    - ES_CRIME_SLUGS hardcoded Record (i18n-localized-slug-pitfall avoidance)
    - CRIME_RANKING_DEFS defined inside getStaticPaths (Astro hoisting requirement)
key_files:
  created:
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
  modified:
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
decisions:
  - crime param read from Astro.params (not Astro.props) so hreflang enPath/esPath resolve correctly
  - CRIME_RANKING_DEFS defined inside getStaticPaths to avoid Astro module-level hoisting isolation
  - ES slug is the route param for the ES page; enParam passed via props for enPath wiring
  - homicide reads featured_rates.homicidios not by_family (by_family returns 0 for all communes)
metrics:
  duration: "25m"
  completed: "2026-06-16"
  tasks: 3
  files: 4
---

# Phase 15 Plan 02: Bilingual Crime-Type Ranking Pages Summary

**One-liner:** Bilingual crime-ranking SSG pages (8 types x 2 locales = 16 new pages) with homicide via featured_rates branch, ItemList+BreadcrumbList+Dataset JSON-LD, sober H1, reciprocal hreflang, and homicide-ranking spoke added to all 346 EN+ES comuna pages.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Create EN crime-ranking/[crime].astro | 523b699 | site/src/pages/crime-ranking/[crime].astro |
| 2 | Create ES ranking-delito/[crime].astro | 71d0393 | site/src/pages/es/ranking-delito/[crime].astro |
| 3 | Reciprocal homicide-ranking spoke + chained build/validate | 8acc4b8 | site/src/pages/commune/[slug].astro, site/src/pages/es/comuna/[slug].astro (+ Astro.params fix to both new files) |

## What Was Built

**Task 1 — EN crime-ranking/[crime].astro:**
- 8 EN pages: /crime-ranking/homicide/, /crime-ranking/violent-robbery/, /crime-ranking/drug-crimes/, /crime-ranking/property/, /crime-ranking/domestic-violence/, /crime-ranking/weapons/, /crime-ranking/disorder/, /crime-ranking/life-crimes/
- homicide reads `commune.featured_rates?.homicidios?.[commune.latestCompleteYear]` (Pitfall 1 fix — by_family returns 0)
- CRIME_RANKING_DEFS defined inside getStaticPaths (Astro hoisting)
- ES_CRIME_SLUGS hardcoded Record for esPath (i18n-localized-slug-pitfall)
- Dataset + BreadcrumbList + ItemList JSON-LD; sober H1; RANKING_METHODOLOGY_EN methodology note
- pageType="crime", mountType="crime-type-map"

**Task 2 — ES ranking-delito/[crime].astro:**
- 8 ES pages: /es/ranking-delito/homicidios/, /es/ranking-delito/robos-violentos/, /es/ranking-delito/drogas/, /es/ranking-delito/propiedad/, /es/ranking-delito/violencia-intrafamiliar/, /es/ranking-delito/armas/, /es/ranking-delito/incivilidades/, /es/ranking-delito/delitos-contra-la-vida/
- ES slug as route param; enParam in props for enPath
- Same featured_rates.homicidios branch; /es/comuna/ links; RANKING_METHODOLOGY_ES

**Task 3 — Reciprocal spokes + build/validate gate:**
- EN [slug].astro: hardcoded `<li><a href="/crime-ranking/homicide/">homicide ranking</a></li>` in crime-type-list
- ES [slug].astro: hardcoded `<li><a href="/es/ranking-delito/homicidios/">ranking de homicidios</a></li>`
- Fix applied to both new [crime].astro files: `crime` from `Astro.params` not `Astro.props` (props has `param` not `crime` — caused hreflang to emit `undefined` URLs)
- Full chained build + validate: 790 pages built; 12/12 validators PASS

## Verification

- 790 pages built (782 → +8 EN crime-ranking + 0 (already built pre-fix) → 790 total)
- dist/crime-ranking/homicide/index.html: non-uniform rates (24, 21, 21, 19...) confirming featured_rates branch
- dist/es/ranking-delito/homicidios/index.html: /es/comuna/ links present; hreflang → /crime-ranking/homicide/
- All 8 EN + 8 ES ranking pages exist; 7 ES family slugs built
- 12/12 validators PASS: structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo
- EN and ES comuna pages contain reciprocal homicide-ranking links (verified in built HTML)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Astro getStaticPaths hoisting — CRIME_RANKING_DEFS not accessible**
- **Found during:** Task 1 first build attempt
- **Issue:** `CRIME_RANKING_DEFS is not defined` — Astro isolates `getStaticPaths` execution context; module-level constants defined outside the function are not accessible
- **Fix:** Moved `CRIME_RANKING_DEFS` definition inside `getStaticPaths`
- **Files modified:** site/src/pages/crime-ranking/[crime].astro
- **Commit:** Included in Task 1 commit (523b699) after fix

**2. [Rule 1 - Bug] Astro.props.crime was undefined — hreflang emitted undefined URLs**
- **Found during:** Task 3 full validate (hreflang validator)
- **Issue:** getStaticPaths passes `props: def` where `def` has key `param`, not `crime`; page body destructured `crime` from props — got `undefined`; hreflang href="https://ischilesafe.com/crime-ranking/undefined/"
- **Fix:** Read `crime` from `Astro.params` (the route param) instead of `Astro.props`; same fix applied to ES page (crime is the ES slug param, enParam from props)
- **Files modified:** site/src/pages/crime-ranking/[crime].astro, site/src/pages/es/ranking-delito/[crime].astro
- **Commit:** 8acc4b8

## Known Stubs

None — all 16 pages render real CEAD data from committed JSON; homicide rates are non-uniform (confirmed in built HTML).

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries. T-15-03 (editorial-guard bypass) mitigated: assertSafeName passes on all ItemList names; forbidden-language.mjs PASS. T-15-04 (homicide data integrity) mitigated: featured_rates branch confirmed non-uniform rates.

## Self-Check: PASSED

- site/src/pages/crime-ranking/[crime].astro: exists, created
- site/src/pages/es/ranking-delito/[crime].astro: exists, created
- site/src/pages/commune/[slug].astro: exists, modified
- site/src/pages/es/comuna/[slug].astro: exists, modified
- Commit 523b699 exists: feat(15-02): create EN crime-ranking/[crime].astro
- Commit 71d0393 exists: feat(15-02): create ES ranking-delito/[crime].astro
- Commit 8acc4b8 exists: feat(15-02): add homicide-ranking reciprocal spoke
