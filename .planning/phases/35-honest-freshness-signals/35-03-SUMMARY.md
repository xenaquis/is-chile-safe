---
phase: 35-honest-freshness-signals
plan: 03
subsystem: ui
tags: [astro, i18n, cead, freshness, vintage, methodology]

# Dependency graph
requires:
  - phase: 35-01
    provides: shared freshness/evidence conventions (G-05 helper pattern) reused as a model for ceadVintage
provides:
  - "ceadVintage(series, lastUpdated) + formatCeadDate(iso, locale) pure helper"
  - "cead_as_of / cead_as_of_note / cead_partial_cutoff i18n keys (EN+ES)"
  - "Data-derived .cead-vintage paragraph on /methodology/, /es/metodologia/, every commune page (EN+ES), every region page (EN+ES)"
  - "Corrected ResultPanel.tsx yearMismatchTip copy (2024 vs 2025 no longer both called 'latest complete CEAD year')"
affects: [35-05, 35-06, 35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure vintage-derivation helper (no fs) consumed by five different page types, mirroring the newsEvidence.mjs pattern from 35-01/35-02"
    - "data-* attributes (data-cead-last-updated, data-partial-year, data-latest-complete-year) on a machine-checkable .cead-vintage paragraph for the 35-05 validator"

key-files:
  created:
    - site/src/lib/ceadVintage.ts
    - site/src/lib/ceadVintage.test.ts
  modified:
    - site/src/config/i18n.ts
    - site/src/lib/data.ts
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - site/src/pages/commune/[slug].astro
    - site/src/pages/es/comuna/[slug].astro
    - site/src/pages/region/[slug].astro
    - site/src/pages/es/region/[slug].astro
    - site/src/components/map/ResultPanel.tsx

key-decisions:
  - "No month-level cutoff is ever claimed (V-13 correction): copy says only 'what CEAD had published by {date}', never a Jan-Jun range."
  - "yearMismatchTip rewritten per gate condition 3 (F35-R1-03): 2024 = year all composite sources (CEAD, SPD, SII) are final; 2025 = latest complete CEAD year. The two years are no longer both called 'latest complete CEAD year'."
  - "Region pages: removed the invented '* 2025: partial year data (Jan-Jun)' / 'año parcial (ene-jun)' footnote and the '*' in the evolution heading (R-02), replaced by the same data-derived .cead-vintage paragraph used elsewhere."

patterns-established:
  - "Vintage/date-of-record disclosure paragraph: <p class='cead-vintage' data-cead-last-updated=... data-partial-year=... data-latest-complete-year=...> — reusable markup contract for the 35-05 validator."

requirements-completed: [FRESH-05]

# Metrics
duration: 65min
completed: 2026-09-24
---

# Phase 35 Plan 03: CEAD vintage + partial-year disclosure Summary

**Data-derived "CEAD data as of {date}" stamp and partial-year cutoff label on methodology, commune and region pages (EN+ES), replacing invented Jan-Jun footnotes and a self-contradictory ResultPanel tooltip.**

## Performance

- **Duration:** ~65 min
- **Started:** 2026-09-24T~20:20Z (task 1 start)
- **Completed:** 2026-09-24T20:28:01-03:00
- **Tasks:** 2/2
- **Files modified:** 9 (2 created, 7 modified)

## Accomplishments
- New pure helper `ceadVintage()` / `formatCeadDate()` derives the download date, partial year and latest complete year from any commune/region/national series — no fs, fully unit tested (8 tests, green under both UTC and `TZ=America/Santiago`).
- `/methodology/` and `/es/metodologia/` now show "CEAD data as of June 16, 2026" / "Datos CEAD al 16 de junio de 2026" sourced from `data/cead/national.json`, and the "(currently 2025)" text is computed, not typed.
- All 346 commune pages (both locales) show the same stamp from the commune's own `last_updated`, falling back to national.
- All 16 region pages (both locales) carry the same `.cead-vintage` paragraph; the invented "* 2025: partial year data (Jan–Jun)" / "año parcial (ene–jun)" footnotes and the `*` in the heading are gone.
- The partial-year copy no longer denies what the trend chart draws: it explicitly says the partial year is excluded only from the headline rate and rankings, and appears as a faded point in the trend charts.
- `ResultPanel.tsx` `yearMismatchTip` no longer calls both 2024 and 2025 "latest complete CEAD year" — 2024 is now described as the year all composite sources (CEAD, SPD, SII) are final; 2025 is the latest complete CEAD year.

## Task Commits

1. **Task 1: ceadVintage helper + i18n strings** - `0ae4940` (feat)
2. **Task 2: Render vintage + partial-year label on methodology/commune/region pages; fix ResultPanel** - `52c631e` (feat)

_No plan-metadata-only commit was required beyond this SUMMARY; both tasks were `type="auto"` and each covers its own scope fully._

## Files Created/Modified
- `site/src/lib/ceadVintage.ts` - Pure `ceadVintage(series, lastUpdated)` + `formatCeadDate(iso, locale)` helper
- `site/src/lib/ceadVintage.test.ts` - 8 unit tests incl. UTC vs America/Santiago TZ negative control
- `site/src/config/i18n.ts` - Adds `cead_as_of`, `cead_as_of_note`, `cead_partial_cutoff` (EN+ES)
- `site/src/lib/data.ts` - Adds `last_updated?: string` to `NationalData` and `RegionData`
- `site/src/pages/methodology.astro` - Renders `.cead-vintage` paragraph; "(currently 2025)" now data-driven
- `site/src/pages/es/metodologia.astro` - Same, ES
- `site/src/pages/commune/[slug].astro` - Renders `.cead-vintage` after `.chart-partial-note`, own `last_updated` with national fallback
- `site/src/pages/es/comuna/[slug].astro` - Same, ES
- `site/src/pages/region/[slug].astro` - Removes `*`/footnote invention, adds `.cead-vintage` paragraph, own `last_updated` with national fallback
- `site/src/pages/es/region/[slug].astro` - Same, ES
- `site/src/components/map/ResultPanel.tsx` - Rewrites `yearMismatchTip` EN+ES per gate condition 3 (F35-R1-03)

## Decisions Made
- Followed the plan's Revision R1/R2 text literally: the full `yearMismatchTip` rewrite (gate condition 3 / F35-R1-03) was applied exactly as specified in the plan, since the gate had already resolved this contradiction before this plan ran.
- Used `<> {text}</>` Astro fragment shorthand to conditionally append the partial-year sentence to the vintage paragraph without introducing a stray literal `{` in the HTML (all tokens substituted server-side per the plan's markup contract).

## Deviations from Plan

None - plan executed exactly as written, including the R1/R2 revisions already baked into the plan text (region twin, ResultPanel rewrite, wording).

## Issues Encountered

Ran a manual negative control per the Task 1 verify step: temporarily removed `timeZone: 'UTC'` from `formatCeadDate` and re-ran the suite under `TZ=America/Santiago` — 3 tests failed as expected (e.g. `formatCeadDate('2026-01-01','en')` produced `'December 31, 2025'` instead of `'January 1, 2026'`), confirming the UTC guard is load-bearing. Restored immediately; full suite green again under both UTC and Santiago TZ.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The `.cead-vintage` markup contract (`data-cead-last-updated`, `data-partial-year`, `data-latest-complete-year`) is in place across methodology, commune and region pages in both locales, ready for the 35-05 validator to check mechanically.
- `ceadVintage.ts` / `formatCeadDate()` are reusable by any future page needing the same disclosure (e.g. crime-family ranking pages), without re-deriving the logic.
- No blockers for 35-04/35-05/35-06/35-07.

---
*Phase: 35-honest-freshness-signals*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: site/src/lib/ceadVintage.ts
- FOUND: site/src/lib/ceadVintage.test.ts
- FOUND: .planning/phases/35-honest-freshness-signals/35-03-SUMMARY.md
- FOUND commit: 0ae4940
- FOUND commit: 52c631e
