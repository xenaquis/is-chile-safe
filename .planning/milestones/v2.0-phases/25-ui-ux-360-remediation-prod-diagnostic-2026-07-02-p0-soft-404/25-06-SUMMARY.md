---
phase: 25
plan: "06"
subsystem: frontend/compare-island
tags: [comparator, i18n, url-sync, editorial, numbers]
dependency_graph:
  requires: [25-02]
  provides: [comparator-attribution, comparator-url-sync, comparator-chips]
  affects: [site/src/islands/ComparatorIsland.tsx, site/src/config/i18n.ts]
tech_stack:
  added: []
  patterns: [formatDecimal, history.replaceState, URLSearchParams, CUT regex validation]
key_files:
  modified:
    - site/src/islands/ComparatorIsland.tsx
    - site/src/config/i18n.ts
    - site/src/pages/compare/index.astro
    - site/src/pages/es/comparar/index.astro
decisions:
  - CUT validation regex is /^\d{4,5}$/ (4 OR 5 digits) because Valparaíso (5101) and Viña del Mar (5109) have 4-digit CUTs; plan specified 5-digit only which would have broken pre-selection for those communes
  - Composite Crime Index label shown in both loaded and "no data" states of the avg card (shows "—" for the index value, never blank)
  - Per-family trend column removed from table; single trend indicator shown once in the composite index header card
metrics:
  duration: "~20m"
  completed: "2026-07-02"
  tasks: 2
  files: 4
---

# Phase 25 Plan 06: ComparatorIsland — Composite Crime Index Label, URL Sync, Popular Chips, Number Formatting

One-liner: Composite Crime Index label + methodology link, ?a=&b= URL sync (CUT codes), popular-comparison chips, formatDecimal wiring (no toFixed(2)), per-row trend removed, plural fix — all on ComparatorIsland.tsx.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Composite Crime Index label + methodology link + Chile-avg value + trend cleanup + numbers/plural | b55526f | ComparatorIsland.tsx, i18n.ts, compare/index.astro, es/comparar/index.astro |
| 2 | URL sync (?a=&b=) + popular-comparison chips in empty state | b55526f | ComparatorIsland.tsx (same commit) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CUT validation regex widened to 4–5 digits**
- **Found during:** Task 2 — when researching popular chip CUT codes
- **Issue:** The plan specified `/^\d{5}$/` for URL param validation, but Valparaíso (CUT 5101) and Viña del Mar (CUT 5109) are 4-digit CUTs. The 5-digit-only regex would silently reject them on mount read, breaking pre-selection for two of the three popular comparison chips.
- **Fix:** Changed validation to `/^\d{4,5}$/` to accept both 4 and 5 digit CUTs (the full range used by CEAD).
- **Files modified:** site/src/islands/ComparatorIsland.tsx
- **Commit:** b55526f

## What Was Built

### Task 1 — Label, numbers, trend cleanup
- Added "Composite Crime Index" / "Índice Compuesto de Criminalidad" label (bold) + methodology link "(what is this?)" / "(¿qué es esto?)" above the big score in each commune card. Band chip ("Very High" / "Muy Alto") only appears in this labeled context — never standalone.
- When no composite index data: shows "—" with the label still present (not blank, not "Sin índice compuesto").
- Chile-avg card now shows "Composite Crime Index: —" header (always visible; national average doesn't have a composite index value).
- Replaced all `rate.toFixed(1)` → `formatDecimal(rate, lang)` (thousands separators).
- Replaced `homRate!.toFixed(2)` → `formatDecimal(homRate!, lang)` (1 decimal, consistent).
- Added plural fix: `(n case)` / `(n cases)`, `(n caso)` / `(n casos)`.
- Removed per-family "Trend" column from the breakdown table. Trend is shown once in the composite index header card with the correct `trendColor` styling.
- Added 7 new `cmp_*` i18n keys in both EN and ES blocks and in the I18nStrings type.

### Task 2 — URL sync + popular chips
- `useEffect` watching `selected` calls `history.replaceState(null, '', '?a={cut}&b={cut}')` on every selection change.
- Mount effect reads `?a=` and `?b=` params, validates each with `/^\d{4,5}$/`, finds matching communes in the prop index, and pre-selects them (calls `fetchCommune` for each).
- Empty state now shows heading + body paragraph + a row of `.compare-chip` buttons for: Santiago vs Las Condes, Providencia vs Ñuñoa, Viña del Mar vs Valparaíso. Clicking a chip selects both communes and triggers data fetch.

## Threat Model Compliance

| Threat ID | Status | Notes |
|-----------|--------|-------|
| T-25-06-URL | Mitigated | `/^\d{4,5}$/` validation before preselect/fetch |
| T-25-06-EDIT | Mitigated | Band chip only inside labeled context; forbidden-language validator passed |
| T-25-SC | N/A | No new packages |

## Known Stubs

None — all data is wired from real commune JSON; no placeholders in rendered output.

## Threat Flags

None — no new network endpoints or auth paths introduced.

## Self-Check: PASSED

- `b55526f` exists in git log: confirmed
- ComparatorIsland.tsx modified: confirmed
- i18n.ts modified with 7 new cmp_* keys: confirmed
- Build 834 pages: confirmed
- 14/14 validators passed: confirmed
- No toFixed(2) in ComparatorIsland.tsx: confirmed
- replaceState present: confirmed
- compare-chip present: confirmed
- CUT regex /^\d{4,5}$/ present: confirmed
