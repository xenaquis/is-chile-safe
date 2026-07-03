---
phase: quick-260703-cvd
plan: "01"
subsystem: i18n / commune-page copy
tags: [copy, i18n, commune, percentile, ux]
dependency_graph:
  requires: []
  provides: [CVD-01]
  affects: [commune-page EN, commune-page ES]
tech_stack:
  added: []
  patterns: []
key_files:
  modified:
    - site/src/config/i18n.ts
decisions:
  - Move compared quantity ("reported crime") into rank_pct_value so value+label read as one sentence; drop parenthetical from rank_national_label
metrics:
  duration: "~8 min"
  completed: "2026-07-03"
  tasks_completed: 1
  files_changed: 1
---

# Quick 260703-cvd: Clarify Commune Page Percentile Copy Summary

**One-liner:** Rewrote commune percentile card copy in EN and ES so "More reported crime than {pct}%" reads as one explicit directional sentence, removing the ambiguous "Higher than X%" phrasing.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Rephrase percentile card copy directionally in EN and ES | aafffa4 | site/src/config/i18n.ts |

## Changes Made

### EN_STRINGS (site/src/config/i18n.ts)

| Key | Before | After |
|-----|--------|-------|
| rank_pct_value | `'Higher than {pct}%'` | `'More reported crime than {pct}%'` |
| rank_national_label | `"of Chile's communes (reported incidence)"` | `"of Chile's communes"` |

### ES_STRINGS (site/src/config/i18n.ts)

| Key | Before | After |
|-----|--------|-------|
| rank_pct_value | `'Mayor que el {pct}%'` | `'Más delitos reportados que el {pct}%'` |
| rank_national_label | `'de las comunas de Chile (incidencia reportada)'` | `'de las comunas de Chile'` |

Regional label and sublabel unchanged — regional label reads coherently with the new value; sublabel retains CEAD attribution and direction note.

## Verification

- Build: 1882+ pages generated, no errors
- Validate: 15/15 validators passed (including forbidden-language validator — no safe/dangerous/seguro/peligroso introduced)
- Pushed to master; deploy-on-code hook triggered

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — copy-only change, no new network surface, endpoints, or schema changes.

## Self-Check: PASSED

- site/src/config/i18n.ts: modified (verified via edit)
- Commit aafffa4: confirmed in git log
- Build + validate: 15/15 green
