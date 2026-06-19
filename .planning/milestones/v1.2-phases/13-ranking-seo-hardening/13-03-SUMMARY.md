---
phase: 13-ranking-seo-hardening
plan: "03"
subsystem: seo-jsonld
tags: [seo, jsonld, itemlist, breadcrumblist, schema.org, xss, baselayout]
one_liner: "Array-of-scripts JSON-LD emission in BaseLayout with per-block XSS escape; ItemList on all 5 ranking surfaces and BreadcrumbList on commune/region/crime (EN+ES) — 12/12 validators green"

dependency_graph:
  requires: ["13-01", "13-02"]
  provides: ["RSEO-02 complete"]
  affects:
    - site/src/layouts/BaseLayout.astro
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
    - site/src/pages/rankings.astro
    - site/src/pages/es/rankings.astro

tech_stack:
  added: []
  patterns:
    - "array-of-scripts: (Array.isArray(jsonLd)?jsonLd:[jsonLd]).filter(Boolean).map() in BaseLayout — one <script> per block, NOT @graph"
    - "per-block XSS escape: .replace(/<\\//g,'<\\\\/') inside the .map() — T-13-01 mitigation preserved"
    - "jsonLd=[existing, breadcrumb, itemList] array pattern across 6 page templates"
    - "urlMode:full for /rankings/ links (not commune slugs); urlMode:commune default elsewhere"
    - "ES hardcoded URLs in BreadcrumbList item values — never getRelativeLocaleUrl (i18n-localized-slug-pitfall)"

key_files:
  created: []
  modified:
    - site/src/layouts/BaseLayout.astro
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/src/pages/index.astro
    - site/src/pages/es/index.astro
    - site/src/pages/rankings.astro
    - site/src/pages/es/rankings.astro

decisions:
  - "array-of-scripts (not @graph): one <script type=application/ld+json> per object — chosen in Plan 01 research, implemented here"
  - "similar-comunas ItemList order=Unordered — proximity is NOT a safety rank (T-13-05 / resolved A1)"
  - "BreadcrumbList strict 2-element mirror for region/crime (Assumption A2) — no trailing region/crime-type element added"
  - "crime page ItemList built from eligibleRankingRows only (filters low_population) — consistent with visual table ranking"
  - "rankings.astro ItemList uses urlMode:full with absolute url per row — links are crime-type index pages, not /commune/ slugs"

metrics:
  duration: "~30 min"
  completed: "2026-06-16"
  tasks_completed: 3
  files_modified: 11
---

# Phase 13 Plan 03: Structured Data (ItemList + BreadcrumbList + Array Emission) Summary

Array-of-scripts JSON-LD emission in BaseLayout with per-block XSS escape; ItemList on all 5 ranking surfaces and BreadcrumbList on commune/region/crime (EN+ES) — 12/12 validators green.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Widen BaseLayout JSON-LD emission to array-of-scripts (D-08) | 032c7ce | site/src/layouts/BaseLayout.astro |
| 2 | ItemList + BreadcrumbList on commune/region/crime (EN + ES) | 157d427 | 6 page template files |
| 3 | ItemList on home two lead tables + /rankings/ link list (no breadcrumb) | 77fbf17 | 4 page template files |

## What Was Built

**BaseLayout.astro (Task 1):**
- Widened single-object emission to `(Array.isArray(jsonLd)?jsonLd:[jsonLd]).filter(Boolean).map((block) => <script ... set:html={JSON.stringify(block).replace(/<\//g,'<\\/')} />)`
- One `<script type="application/ld+json">` per block (NOT @graph)
- XSS escape `.replace(/<\//g,'<\\/')` preserved per block inside the `.map` — T-13-01 mitigation
- Existing single-object callers unchanged (backward compatible via the Array.isArray branch)

**Commune pages EN + ES (Task 2):**
- 4-level BreadcrumbList mirrors visual `Home › Communes › {Region} › {Commune}` (last item omits `item`)
- Unordered ItemList for "similar comunas" — proximity order, NOT a safety rank (T-13-05)
- ES URLs hardcoded: `/es/`, `/es/comunas/`, `/es/region/${regionSlug}/`
- Existing Dataset+Place block kept as element 0

**Region pages EN + ES (Task 2):**
- 2-level BreadcrumbList mirrors visual `Home › Regions` (strict A2 mirror)
- Descending ItemList of communes in region by reported CEAD incidence
- Existing Dataset+Place block kept as element 0

**Crime pages EN + ES (Task 2):**
- 2-level BreadcrumbList mirrors visual `Home › Crime Types`
- Descending ItemList built from `eligibleRankingRows` (excludes low_population) — same rows the inline table ranks
- Existing Dataset block kept as element 0

**Home pages EN + ES (Task 3):**
- Two ItemLists: Ascending (lowest rows) + Descending (highest rows) — NO BreadcrumbList (D-07)
- Names use sober "reported CEAD incidence (ascending/descending)" phrasing (T-13-02)

**/rankings/ EN + ES (Task 3):**
- Single Unordered ItemList of ranking-page links with `urlMode: 'full'` (not /commune/ slugs)
- NO BreadcrumbList (D-07 — no visual breadcrumb on /rankings/)
- All link names sober (no "safest" or "dangerous" terms)

## Verification

Full chained gate (one command per OneDrive desync constraint):

- seo.mjs: PASSED — 44/44 assertions (ItemList shape on home/region/crime/ranking; BreadcrumbList shape on commune/region/crime; all blocks parse clean; no forbidden terms)
- schema.mjs: PASSED — existing Dataset/Place/FAQ blocks still valid (element 0 preserved)
- all.mjs: 12/12 PASSED

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all JSON-LD blocks emit real build-time data.

## Threat Surface Scan

No new network endpoints or auth paths introduced. All JSON-LD values flow from build-time static data (commune/region/crime names, slugs). The XSS escape `T-13-01` mitigation is applied per block inside the `.map` — verified by seo.mjs parse-clean assertions on every sampled page.

T-13-02 (editorial-rule leak in machine-readable form): all ItemList `name` strings use neutral "reported incidence (ascending/descending)" / "incidencia reportada" phrasing. `jsonld.ts` guard enforces at build time; seo.mjs scan found no forbidden terms.

T-13-05 (similar-comunas proximity misread as rank): `order: 'Unordered'` used — no Ascending/Descending on the similar-comunas ItemList.

## Self-Check: PASSED

- site/src/layouts/BaseLayout.astro: EXISTS, contains Array.isArray
- site/src/pages/commune/[slug].astro: EXISTS, contains buildBreadcrumb
- site/src/pages/region/[slug].astro: EXISTS, contains buildBreadcrumb
- site/src/pages/crime/[family].astro: EXISTS, contains buildBreadcrumb
- site/src/pages/rankings.astro: EXISTS, contains buildItemList
- site/src/pages/index.astro: EXISTS, contains buildItemList
- Commit 032c7ce: EXISTS
- Commit 157d427: EXISTS
- Commit 77fbf17: EXISTS
- seo.mjs: PASSED (44 assertions)
- all.mjs 12/12: PASSED

---
*Phase: 13-ranking-seo-hardening*
*Completed: 2026-06-16*
