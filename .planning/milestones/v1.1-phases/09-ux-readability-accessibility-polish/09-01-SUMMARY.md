---
phase: 09-ux-readability-accessibility-polish
plan: "01"
subsystem: frontend-foundation
tags: [i18n, a11y, css, components, refactor]
dependency_graph:
  requires: []
  provides: [familyDefs-module, rate-tooltip-component, a11y-focus-css, phase9-i18n-strings]
  affects: [site/src/pages/crime, site/src/pages/es/delito, site/src/components/map, site/src/styles/global.css]
tech_stack:
  added: []
  patterns: [details-summary-disclosure, zero-js-tooltip, focus-visible-polyfill-pattern]
key_files:
  created:
    - site/src/lib/familyDefs.ts
    - site/src/components/RateTooltip.astro
    - site/src/components/map/RateTooltipReact.tsx
  modified:
    - site/src/pages/crime/[family].astro
    - site/src/pages/es/delito/[family].astro
    - site/src/config/i18n.ts
    - site/src/styles/global.css
decisions:
  - Tooltip CSS lives in global.css (not scoped) so one CSS block styles both Astro and React surfaces
  - FAMILY_ORDER canonical display order matches PanelFamilyBars.tsx existing order
  - focus-visible blanket rule covers summary, lang-btn, nav label without per-element overrides
metrics:
  duration: "~12m"
  completed: "2026-06-15"
  tasks: 3
  files: 7
---

# Phase 09 Plan 01: Shared Foundation Summary

**One-liner:** Hoisted crime-family constants into single lib module, added 10 bilingual i18n keys, and created dual-surface accessible tooltip with A11Y-01 focus-visible and READ-01 prose-rhythm CSS.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Hoist crime-family constants into familyDefs.ts | 76cf74a | familyDefs.ts, crime/[family].astro, es/delito/[family].astro |
| 2 | Add Phase-9 bilingual strings to i18n.ts | 3822e4e | i18n.ts |
| 3 | Create dual-surface RateTooltip + CSS | 37bd7cd | RateTooltip.astro, RateTooltipReact.tsx, global.css |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all new components are fully implemented. Tooltip tip text is supplied via props by callers (Plans 02 and 03 will wire the i18n strings as prop values).

## Threat Flags

No new network endpoints, auth paths, or trust boundaries introduced. All changes are authored static strings and presentational CSS rendered at build time.

## Self-Check: PASSED

- site/src/lib/familyDefs.ts: exists (created)
- site/src/components/RateTooltip.astro: exists (created)
- site/src/components/map/RateTooltipReact.tsx: exists (created)
- Commits 76cf74a, 3822e4e, 37bd7cd: verified in git log
- npm run build: exited 0 after each task (100 pages built)
