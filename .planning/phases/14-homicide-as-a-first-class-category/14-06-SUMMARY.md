---
phase: 14-homicide-as-a-first-class-category
plan: "06"
subsystem: map-panel
tags: [homicide, ResultPanel, bilingual, CEAD, HOM-02, D-06, D-07]
dependency_graph:
  requires: ["14-05"]
  provides: ["HOM-02 panel homicide figure"]
  affects: ["site/src/components/map/ResultPanel.tsx"]
tech_stack:
  added: []
  patterns: ["featured_rates !== undefined guard (Pitfall 5)", "IIFE panel section pattern"]
key_files:
  modified:
    - site/src/components/map/ResultPanel.tsx
decisions:
  - "Use !== undefined (not truthiness) to guard homRate and count — confirmed 0 shows as 0 not no-data (Pitfall 5)"
  - "Homicide section placed after PanelFamilyBars, before incidents — purely additive (HOM-02 no-regression)"
  - "IIFE pattern for homicide section (consistent with plan analog C)"
metrics:
  duration: "10m"
  completed: "2026-06-16"
  tasks_completed: 2
  tasks_total: 3
  files_modified: 1
---

# Phase 14 Plan 06: Homicide Breakdown in ResultPanel Summary

**One-liner:** Commune detail panel now shows a separate homicide figure (rate per 100k + absolute case count + CEAD year) reading `featured_rates.homicidios` / `homicidios_count`, bilingual + CEAD-cited, with an explicit non-alarmist zero state, distinct from the 7 family bars (HOM-02).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add homicide breakdown section to ResultPanel | e35c384 | site/src/components/map/ResultPanel.tsx |
| 2 | Chained build + map + forbidden-language validators green | e716ab2 | (validation only) |
| 3 | Human-verify end-to-end in browser | PENDING (checkpoint) | none |

## What Was Built

### Task 1: ResultPanel homicide section

Extended `CommuneData` interface to type `featured_rates` with:
- `homicidios?: Record<string, number>` — rate per 100k by year
- `homicidios_count?: Record<string, number>` — absolute case count by year
- `propiedad?: Record<string, number>` and `secuestros?: Record<string, number>` for completeness

Added homicide breakdown section (section 7, before incidents) using an IIFE pattern:
- `!== undefined` presence check (Pitfall 5 — confirmed 0 shows as 0, not "no data")
- When data present: `stat-mid` rate + `stat-sub` count with singular/plural (caso/casos, case/cases)
- When year absent (no data): explicit non-alarmist `Sin casos reportados — CEAD {year}` / `No reported cases — CEAD {year}` in `var(--muted)`
- `official-row` source line: `Fuente: CEAD, subgrupo 101 Delitos contra la Vida ({year})` / `Source: CEAD, subgroup 101 Life Crimes ({year})`
- Bilingual inline `{lang === 'es' ? ... : ...}` pattern
- `PanelFamilyBars` and `by_family` 7-element array untouched (HOM-02 no-regression)

### Task 2: Validators

- `npm run build`: 774 pages built in 16.87s, no errors
- `map.mjs`: all 13 checks PASS (includes Check 8 homicide_rate in map-payload + Check 9 homicidios in 13101.json)
- `forbidden-language.mjs`: 774 pages scanned, 0 forbidden terms (no "peligroso/seguro" in homicide copy)

## Deviations from Plan

None — plan executed exactly as written. Section numbers in ResultPanel comments updated (7→8 for Incidents, 8→9 for CTA, 9→10 for Official source row) as a minor housekeeping side effect of the insertion.

## Known Stubs

None. The homicide section reads real `featured_rates.homicidios` / `homicidios_count` from per-commune JSON populated by the pipeline in Phase 14-01/02.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes beyond what the threat model (T-14-13, T-14-14) already covers. Homicide values are React auto-escaped (JSX); `!== undefined` guard preserves editorial honesty; forbidden-language validator confirmed 0 violations.

## Self-Check

- [x] `site/src/components/map/ResultPanel.tsx` modified (feat commit e35c384 exists)
- [x] `npx tsc --noEmit` passes (no output = no errors)
- [x] Homicide section contains `homicidios_count`, `Sin casos reportados`, `No reported cases`
- [x] `npm run build` passes (774 pages)
- [x] `map.mjs` passes (13/13)
- [x] `forbidden-language.mjs` passes (0 violations)

## Self-Check: PASSED
