---
phase: 18-composite-crime-index
plan: "05"
subsystem: validators-and-docs
tags: [forbidden-language, figure-registry, methodology, CI-08, CI-09, CI-10]
dependency_graph:
  requires: [18-03, 18-04]
  provides: [editorial-guard, documentation-gate, schema-migration-verified]
  affects: [site/scripts/validate/, data/SOURCES.md, site/src/pages/methodology.astro, site/src/pages/es/metodologia.astro]
tech_stack:
  added: []
  patterns: [token-group figure registry, NFD accent normalization, winsorized min-max composite]
key_files:
  created: []
  modified:
    - site/scripts/validate/forbidden-language.mjs
    - site/scripts/validate/figure-registry.mjs
    - data/SOURCES.md
    - site/src/pages/methodology.astro
    - site/src/pages/es/metodologia.astro
decisions:
  - "F13/F14 use accent-free token substrings in both registry and SOURCES.md to prevent NFD drift"
  - "Homicide labeled M1 (spd_homicide_rate) everywhere; no M5 reference"
  - "figure-registry scope expanded from F1-F12+F15 to F1-F15 (all in-scope figures)"
metrics:
  duration: "~20 min"
  completed: "2026-06-19"
  tasks_completed: 3
  files_modified: 5
---

# Phase 18 Plan 05: Editorial Guard and Documentation — Summary

Extended the forbidden-language validator with unqualified-superlative terms and a reported/reportado allow-list; registered F13 (SPD VHC homicide, M1) and F14 (SII exposure) in the figure-registry with accent-free tokens anchored to SOURCES.md; documented the full composite methodology in SOURCES.md and both methodology pages; proved the additive schema migration non-breaking (13/13 validators + full build green).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend forbidden-language validator | e25b872 | forbidden-language.mjs |
| 2 | Document SOURCES.md + register F13/F14 | d78a5b9 | data/SOURCES.md, figure-registry.mjs |
| 3 | Methodology pages (EN+ES) + full gate | 6915dfe | methodology.astro, es/metodologia.astro |

## What Was Built

### Task 1 — Forbidden-language validator extension (CI-09)

Added four new `FORBIDDEN_TERMS`: `most dangerous`, `mas peligrosa`, `mas peligroso`, `el mas seguro`. The NFD accent normalization pass already maps accented variants to these normalized forms. Added two `ALLOW_LIST` regexes permitting reported/reportado-qualified phrasings (`/according to reported (crime|incidents)/i` and `/segun (delitos|incidentes) reportados/i`). Validator passed on the existing dist/ (793 pages, 0 forbidden terms).

### Task 2 — SOURCES.md composite methodology + F13/F14 registration (CI-08)

Added a `## Composite Crime Index — methodology` section to `data/SOURCES.md` documenting:
- Composite formula (weighted sum of 7 winsorized metrics)
- Locked C-02 weight vector verbatim (`spd_homicide_rate 0.30` through `cead_armas_rate 0.05`)
- Winsorized min-max normalization with `limits=[0.01, 0.01]`
- SPD VHC switch: M1 (`spd_homicide_rate`) uses SPD; CEAD grupo-101 preserved for display
- SII exposure caveat: HQ-domicile artifact, `cap 5.0` applied
- Reference year 2024
- All required accent-free token substrings present verbatim: `Subsecretaria de Prevencion`, `exposicion`, `trabajadores`, `homicidio`, `SPD`, `SII`

Updated `figure-registry.mjs`: removed F13/F14 exclusion comment; added F13 (SPD VHC homicide, M1 — tokens `[SPD, homicidio]` and `[Subsecretaria de Prevencion, homicidio]`) and F14 (SII exposure — tokens `[SII, trabajadores]` and `[SII, exposicion]`); updated scope annotation and console messages from F1-F12+F15 to F1-F15. Registry passed: 15/15 zero orphans.

### Task 3 — Methodology pages + non-breaking migration gate (CI-08, CI-10)

Added composite-index methodology section to `methodology.astro` (EN) and `es/metodologia.astro` (ES) documenting: formula, C-02 weight vector, winsorized min-max normalization [0.01,0.01], SPD VHC homicide switch (M1), SII exposure caveat (cap 5.0), reference year 2024. F13 and F14 cited by name, enabling figure-registry resolution. ES section is a full translation of EN with hardcoded ES internal links.

Full migration gate: `cd site && npm run build && npm run validate` → **13/13 validators PASS** (CI-10). All 6 consumers verified non-breaking: ChoroplethLayer, ResultPanel, both commune page templates, figure-registry, and pipeline tests.

## Acceptance Criteria — Verification

| Criterion | Status |
|-----------|--------|
| FORBIDDEN_TERMS contains most dangerous, mas peligrosa, mas peligroso, el mas seguro | PASS |
| ALLOW_LIST contains two qualified-usage regexes | PASS |
| node scripts/validate/forbidden-language.mjs exits 0 | PASS (793 pages, 0 failures) |
| data/SOURCES.md contains C-02 weight vector + winsorized, limits [0.01, 0.01], 2024, cap 5.0 | PASS |
| data/SOURCES.md labels homicide as M1 (no M5) | PASS |
| grep Subsecretaria de Prevencion succeeds | PASS |
| grep exposicion succeeds | PASS |
| grep trabajadores + grep homicidio succeed | PASS |
| figure-registry.mjs contains F13 + F14 entries | PASS |
| F13/F14 exclusion comment removed | PASS |
| node scripts/validate/figure-registry.mjs exits 0 (zero orphans) | PASS (15/15) |
| methodology.astro + es/metodologia.astro document formula, normalization, SPD switch (M1), SII caveat | PASS |
| cd site && npm run build && npm run validate exits 0 | PASS (13/13 validators) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all documented methodology facts are real (C-02 weight vector locked in Phase 18-01; SII cap=5.0 confirmed in Phase 18-01; SPD VHC switch implemented in Phase 18-02).

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. Validators enforce the T-18-13/T-18-14/T-18-15 mitigations (forbidden-language, figure-registry zero-orphan, schema migration non-breaking).

## Self-Check: PASSED

- `site/scripts/validate/forbidden-language.mjs` — exists, contains `most dangerous`
- `site/scripts/validate/figure-registry.mjs` — exists, contains `F13`
- `data/SOURCES.md` — exists, contains `spd_homicide_rate`, `Subsecretaria de Prevencion`, `exposicion`
- `site/src/pages/methodology.astro` — exists, contains composite-index section
- `site/src/pages/es/metodologia.astro` — exists, contains indice-compuesto section
- Commits e25b872, d78a5b9, 6915dfe confirmed in git log
