---
phase: 20-methodology-sources-hardening
plan: "02"
subsystem: methodology-ui
status: complete
tags: [methodology, i18n, crime-ranking, FamilyBreakdownBars, drogas, LevelChip]
dependency_graph:
  requires: ["20-01"]
  provides: [MTH-01, MTH-02, MTH-03-partial]
  affects:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
    - site/src/components/FamilyBreakdownBars.astro
tech_stack:
  added: []
  patterns:
    - "FAMILY_SCOPE_NOTE_EN/ES reuse from familyDefs.ts for static scope callout"
    - "id anchor on H2 for deep-link to trend-formula"
    - "h3 sub-sections under existing H2 to extend without breaking 7-H2 parity rule"
key_files:
  modified:
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
    - site/src/pages/crime-ranking/[crime].astro
    - site/src/pages/es/ranking-delito/[crime].astro
    - site/src/components/FamilyBreakdownBars.astro
decisions:
  - "Add sub-sections as h3 under existing Comparison-criteria H2 (not a new H2) to preserve 7-H2 parity lock"
  - "F2/F5 weighting distinction placed under Trend formula section as a bridging paragraph"
  - "Drogas scope note rendered as a static <p> after the bars div — always rendered (drogas is always in FAMILY_ORDER)"
  - "Inline ranking caveats kept terse (single sentence + methodology link) to avoid cluttering the hero"
metrics:
  duration_minutes: 15
  completed_date: "2026-06-19"
  tasks_completed: 3
  files_changed: 5
---

# Phase 20 Plan 02: Methodology Sub-sections, Ranking Caveats & Drogas Scope Note Summary

**One-liner:** Adds per-family mean (F3), per-region mean (F4), LevelChip relative tier (F6), F2/F5 weighting distinction, #trend-formula anchor (F7), and Ley 20.000 drogas scope note (F10) across methodology pages, ranking pages, and FamilyBreakdownBars — EN/ES parity maintained, 12/12 validators pass.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Methodology sub-sections (F3/F4/F6/F7, F2/F5 distinction) | 8adfaff | methodology.astro, es/metodologia.astro |
| 2 | Inline ranking caveats + drogas scope note | 58e65f3 | [crime].astro, es/ranking-delito/[crime].astro, FamilyBreakdownBars.astro |
| 3 | Build + validate gate | (chained in T2 verification) | dist/ |

## What Was Built

### Task 1 — Methodology pages (EN + ES)
- `id="trend-formula"` added to Trend-formula H2 in both locales (F7/MC-06). Deep-links `/methodology/#trend-formula` and `/es/metodologia/#trend-formula` now work.
- **F2 vs F5 weighting distinction** added as a paragraph under Trend formula: time-series rates are population-weighted; aggregate/per-family/per-region means are unweighted typical-commune figures.
- **Three new h3 sub-sections** added under existing "Comparison criteria" / "Criterios de comparación" H2:
  - Per-family national mean (F3): explains the hero-stat on ranking pages is an unweighted commune mean for that crime family.
  - Per-region breakdown mean (F4): explains regional bars are unweighted commune means within each region.
  - Incidence level classification — LevelChip 1–5 (F6): explains the chip is a relative 5-tier distribution-derived classification, NOT an absolute threshold and NOT a safety verdict. Cross-references the choropleth colour scale (F8).
- Both pages retain exactly **7 H2 sections** (parity lock satisfied).

### Task 2 — Ranking pages + FamilyBreakdownBars
- **EN and ES crime-ranking hero**: terse inline caveat after the national mean hero-stat: "unweighted commune mean (communes ≥ 10k population)" with a link to methodology.
- **EN and ES regional breakdown section**: one-line caveat above the bars confirming unweighted commune mean per region.
- **FamilyBreakdownBars.astro**: imports `FAMILY_SCOPE_NOTE_EN` / `FAMILY_SCOPE_NOTE_ES` from `familyDefs.ts` (strings not rewritten — reused as-is per plan constraint). Renders the drogas scope note as a static `<p class="family-scope-note">` after the bars. Always rendered (drogas is always in FAMILY_ORDER). Component remains zero `client:*` directives.

### Task 3 — Build + validate
- `npm run build && npm run validate` chained in one command (OneDrive desync guard).
- Build: green, all pages generated.
- Validators: **12/12 PASS** (structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo).

## Deviations from Plan

None — plan executed exactly as written. F2/TD-01 wording (Phase 19) was not touched. No data recomputed, no rates rescaled.

## Known Stubs

None introduced by this plan.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. All changes are static HTML copy/structure only. Forbidden-language validator re-ran and passed — no absolute safe/dangerous verdicts introduced.

## Self-Check: PASSED

- `methodology.astro` has exactly 7 H2 ✓
- `es/metodologia.astro` has exactly 7 H2 ✓
- `id="trend-formula"` present in both built HTML files ✓
- `family-scope-note` class present in `dist/commune/santiago/index.html` and `dist/es/comuna/santiago/index.html` ✓
- `FAMILY_SCOPE_NOTE` import in `FamilyBreakdownBars.astro` ✓
- `unweighted` text in `crime-ranking/[crime].astro` ✓
- 12/12 validators passed ✓
- Commits: 8adfaff (methodology), 58e65f3 (ranking+FamilyBreakdownBars) ✓
