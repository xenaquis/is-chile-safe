---
phase: 02-astro-site-programmatic-pages
plan: 05
subsystem: frontend-pages
tags: [crime-type-pages, i18n, national-ranking, seo, static-generation]
dependency_graph:
  requires: [02-02]
  provides: [crime-type-EN-pages, crime-type-ES-pages, crime-validator]
  affects: [dist/crime, dist/es/delito]
tech_stack:
  added: []
  patterns: [build-time-national-family-ranking, region-breakdown-bars, translated-slug-routing]
key_files:
  created:
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/scripts/validate/crime.mjs
  modified: []
decisions:
  - "Ranking table shows all 346 communes (low-pop rows rendered at bottom with * marker and suppressed rank number) — all communes shown, not paginated; ~346 rows is acceptable per plan"
  - "latestYear for page metadata derived from the top-ranking eligible commune rather than a separate national.json lookup (simpler; same result)"
  - "Dataset-only JSON-LD on crime-type pages — no Place type (UI-SPEC line 288)"
metrics:
  duration: 18m
  completed: "2026-06-13"
  tasks: 2
  files: 3
---

# Phase 02 Plan 05: Crime-Type Pages (EN + ES) Summary

**One-liner:** 14 bilingual crime-type pages (7 families × 2 locales) with build-time national commune ranking by family rate, translated URL slugs, and Dataset-only JSON-LD.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | EN + ES crime-type page routes with national family ranking | c6936ef | site/src/pages/crime/[family].astro, site/src/pages/es/delito/[family].astro |
| 2 | Crime-type validator | f0e449d | site/scripts/validate/crime.mjs |

## What Was Built

**Task 1 — Crime-type pages:**

- `site/src/pages/crime/[family].astro` — 7 EN pages at `/crime/{slug}/` (homicide, violent-robbery, domestic-violence, drug-crimes, weapons, property, disorder)
- `site/src/pages/es/delito/[family].astro` — 7 ES pages at `/es/delito/{slug}/` (homicidios, robos-violentos, violencia-intrafamiliar, drogas, armas, propiedad, incivilidades)
- Both pages compute the national family ranking at build time: iterate all 346 communes, read `by_family[familyKey]` at each commune's `latestCompleteYear`, sort descending; low-pop communes rendered at bottom with `*` marker and suppressed rank number
- Region breakdown: 16-region mean of eligible commune rates, rendered as CSS percentage bars
- Featured badge for `vida` (Life Crimes) and `propiedad` (Property Crimes) per D-12
- `MapPlaceholderSlot` with `mountType="crime-type-map"` per D-13
- Dataset-only JSON-LD (no Place type) per UI-SPEC line 288
- Reciprocal hreflang (en / es / x-default) + self-canonical on all 14 pages

**Task 2 — Validator:**

- `site/scripts/validate/crime.mjs` — asserts 7 EN + 7 ES crime dirs, slug names match `FAMILY_SLUGS` en/es values exactly, sample pages have ranking table (346 rows), Dataset JSON-LD, no Place type, hreflang, canonical
- All 15 assertions pass, exits 0

## Deviations from Plan

None — plan executed exactly as written.

## Verification

- `cd site && npx astro check` — 0 errors, 0 warnings (2 minor hints only)
- `cd site && npm run build` — exits 0, 71 pages built (14 new crime pages + prior commune/region pages)
- `node site/scripts/validate/crime.mjs` — all 15 assertions PASSED

## Known Stubs

None — all 14 pages render real CEAD data from Phase 1 output.

## Self-Check: PASSED

- site/src/pages/crime/[family].astro — FOUND
- site/src/pages/es/delito/[family].astro — FOUND
- site/scripts/validate/crime.mjs — FOUND
- Commit c6936ef — FOUND
- Commit f0e449d — FOUND
- dist/crime contains 7 dirs — VERIFIED (validator PASSED)
- dist/es/delito contains 7 dirs — VERIFIED (validator PASSED)
