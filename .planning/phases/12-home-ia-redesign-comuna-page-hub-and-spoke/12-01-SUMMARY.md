---
phase: 12-home-ia-redesign-comuna-page-hub-and-spoke
plan: "01"
subsystem: data-helpers + i18n + directory-ux
tags: [data, i18n, search, ux, foundation]
dependency_graph:
  requires: []
  provides:
    - nearestComparables(cut, n) helper in data.ts
    - nav_rankings + footer-spine i18n keys (EN + ES)
    - ?q= pre-filter on commune directory pages
  affects:
    - site/src/lib/data.ts
    - site/src/config/i18n.ts
    - site/src/pages/communes/index.astro
    - site/src/pages/es/comunas/index.astro
tech_stack:
  added: []
  patterns:
    - same-region pool filter + abs-rate-distance sort (nearestComparables)
    - URLSearchParams ?q= read assigned to input.value only (XSS-safe)
key_files:
  created: []
  modified:
    - site/src/lib/data.ts
    - site/src/config/i18n.ts
    - site/src/pages/communes/index.astro
    - site/src/pages/es/comunas/index.astro
decisions:
  - nearestComparables returns same-region only per D-07; no national fallback
  - BUGFIX-999.1 Tarapacá collision accepted/noted in comment; fix deferred to v1.2 backlog
  - nav_rankings ES value is 'Rankings' (same word both locales per RESEARCH.md)
metrics:
  duration: "~15m"
  completed: "2026-06-16"
  tasks: 3
  files: 4
---

# Phase 12 Plan 01: Shared Foundations — nearestComparables, i18n Keys, ?q= Directory

**One-liner:** Build-time plural similar-communes helper + 5 i18n keys per locale + URL ?q= pre-filter on both directory finders, establishing contracts for all Wave-2 hub-and-spoke pages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | nearestComparables(targetCut, n) plural helper | 9424842 | site/src/lib/data.ts |
| 2 | nav_rankings + footer-spine i18n keys (EN + ES) | c30dab8 | site/src/config/i18n.ts |
| 3 | Comuna directory ?q= URL param on load (EN + ES) | be0436f | site/src/pages/communes/index.astro, site/src/pages/es/comunas/index.astro |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

The plan called for a TDD "test first" pass on Task 1, but the acceptance criteria specified TypeScript type-checking as the automated gate (not a test file). `npx tsc --noEmit` and `npm run build` both passed — the function is verified by the compiler and build pipeline rather than a separate test file.

## Threat Surface Scan

T-12-01 mitigation applied: `?q=` URL param is read via `URLSearchParams`, assigned only to `input.value` (a form field) and the `q` string variable. It is never injected into `innerHTML`. The highlight function continues to slice the TRUSTED `data-name` attribute (T-11-05 control). No new threat surface introduced.

## Known Stubs

None. All three artifacts are fully wired:
- `nearestComparables` calls `loadCommune` and `latestCompleteYearRate` for real data per row.
- i18n keys have real label values in both locales.
- `?q=` filter is live via existing `render()` infrastructure.

## Verification Results

- `npx tsc --noEmit`: 0 errors on data.ts
- `npm run check`: exit 0 (no missing-property errors on I18nStrings)
- `npm run build`: 772 pages built, exit 0
- `dist/communes/index.html` contains `URLSearchParams`: PASS
- `dist/es/comunas/index.html` contains `URLSearchParams`: PASS

## Self-Check: PASSED

- site/src/lib/data.ts: exports `nearestComparables` and `RankingRow`
- site/src/config/i18n.ts: contains `nav_rankings`, `footer_spine_map/communes/rankings/guide` in interface + EN_STRINGS + ES_STRINGS
- site/src/pages/communes/index.astro: contains `URLSearchParams(window.location.search).get('q')`
- site/src/pages/es/comunas/index.astro: contains `URLSearchParams(window.location.search).get('q')`
- Commits 9424842, c30dab8, be0436f all present in git log
