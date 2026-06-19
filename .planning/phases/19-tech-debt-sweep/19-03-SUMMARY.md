---
phase: 19-tech-debt-sweep
plan: "03"
subsystem: bilingual-content
tags: [bilingual, i18n, hreflang, BIL-01, BIL-02, BIL-03]
dependency_graph:
  requires: ["19-02"]
  provides: ["crimes-by-region EN page", "ES commune→comuna sweep", "hreflang reciprocity for delitos-por-region"]
  affects: ["ES editorial pages", "hreflang validator"]
tech_stack:
  added: []
  patterns: ["EditorialLayout enPath/esPath pair", "locale-safe prose replacement"]
key_files:
  created:
    - site/src/pages/crimes-by-region.astro
  modified:
    - site/src/pages/es/comunas-mas-seguras-chile.astro
    - site/src/pages/es/seguridad-vina-del-mar.astro
    - site/src/pages/es/seguridad-concepcion.astro
    - site/src/pages/es/seguridad-valparaiso.astro
    - site/src/pages/es/mapa-delito-chile.astro
    - site/src/pages/es/mapa-seguridad-santiago.astro
    - site/src/pages/es/delitos-por-region.astro
decisions:
  - "Replace commune→comuna only in user-visible text; JS identifiers (const commune, loadCommune, commune.series, .commune-link CSS) left untouched"
  - "BIL-03 fix: 'la adjacent ciudad costera' → 'la ciudad costera vecina' (natural Spanish word order)"
  - "crimes-by-region.astro mirrors delitos-por-region section structure; uses /region/{slug}/ and /map-crime-chile/ EN slugs directly (no getRelativeLocaleUrl — i18n-localized-slug-pitfall)"
metrics:
  duration: "~20 min"
  completed: "2026-06-19"
  tasks: 2
  files: 8
---

# Phase 19 Plan 03: Bilingual Integrity (BIL-01/02/03) Summary

**One-liner:** Replaced 25+ user-visible "commune" occurrences with "comuna" across 7 ES files, fixed "adjacent"→"vecina" in Valparaíso prose, and created the reciprocal EN /crimes-by-region/ page with correct bidirectional hreflang — eliminating the /es/delitos-por-region/ orphan.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | BIL-01/BIL-03: commune→comuna sweep + adjacent fix | 1f7a87b | 7 ES files |
| 2 | BIL-02: create /crimes-by-region/ + fix hreflang pair | c8077e3 | crimes-by-region.astro (new) |

## Verification

- Build: 793 pages built successfully
- Validators: **12/12 PASSED**
  - hreflang: 793 pages, reciprocity verified (crimes-by-region↔delitos-por-region)
  - forbidden-language: 0 forbidden terms across 793 pages
  - All other validators green
- `grep \bcommune\b site/src/pages/es/**/*.astro` → 0 user-visible matches (only JS identifiers remain)
- `grep adjacent site/src/pages/es/seguridad-valparaiso.astro` → 0 matches

## Deviations from Plan

None — plan executed exactly as written. All user-visible "commune" occurrences replaced without touching JS identifiers. "adjacent" removed. EN page created with full section parity. hreflang reciprocity confirmed by validator.

## Known Stubs

None — /crimes-by-region/ uses the same live data loaders (loadNationalAverage, loadIndex, loadCommune) as the ES counterpart.

## Threat Flags

No new threat surface. /crimes-by-region/ reuses existing trusted data.ts loaders; forbidden-language validator confirms legal-safe framing.

## Self-Check: PASSED

- `site/src/pages/crimes-by-region.astro` — FOUND
- `dist/crimes-by-region/index.html` — built (793 pages includes it)
- Commits 1f7a87b and c8077e3 — verified in git log
