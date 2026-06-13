---
phase: 01-data-foundation
plan: "02"
subsystem: pipeline/data
tags: [population, INE, data-asset, DATA-04]
dependency_graph:
  requires: [01-01]
  provides: [population-json, population-module]
  affects: [01-04-normalizer]
tech_stack:
  added: []
  patterns: [lru_cache-static-asset, one-time-fetch-script, tdd-red-green]
key_files:
  created:
    - data/ine/poblacion_comunal.json
    - pipeline/shared/population.py
    - pipeline/scripts/fetch_ine_population.py
    - pipeline/scripts/__init__.py
    - pipeline/tests/test_population.py
  modified: []
decisions:
  - CUT codes stored as raw string digits without zero-padding (matches CEAD catalog)
  - Name field preserved from source CSV; data correctness verified by human checkpoint
  - is_low_population defaults to True for unknown CUT codes (safe exclusion from rankings)
metrics:
  duration: "~20 min"
  completed_date: "2026-06-12"
  tasks_completed: 3
  tasks_total: 3
  tests_added: 10
---

# Phase 01 Plan 02: INE Population Data Asset + Lookup Module Summary

**One-liner:** Static INE 2024 communal population JSON (346 entries) with lru_cached lookup and 10,000-threshold low-population filter for DATA-04 ranking exclusions.

## What Was Built

### Task 1: INE Population JSON Asset
- `pipeline/scripts/fetch_ine_population.py` — one-time reproducible script that downloads the bastianolea processed INE projections CSV, filters to year 2024, and writes `data/ine/poblacion_comunal.json`
- Source: `https://github.com/bastianolea/censo_proyecciones_poblacion/raw/main/datos/datos_procesados/censo_proyecciones_año.csv`
- Script guards: raises on column-name mismatch (prints actual column names); raises if output count != 346
- `data/ine/poblacion_comunal.json` committed as static versioned asset — 346 entries, shape `{"cut": "13101", "name": "Santiago", "population_2024": 544388}`

### Task 2: Population Lookup Module (TDD)
- `pipeline/shared/population.py` — `load_population()` lru_cached, `LOW_POPULATION_THRESHOLD = 10_000`, `is_low_population(cut_code)`
- `pipeline/tests/test_population.py` — 10 tests covering dict type/length, key/value types, high/low population assertions against real data, unknown CUT default, threshold constant
- All 10 tests green

### Task 3: Human Checkpoint — APPROVED
User confirmed all 5 sampled commune values match official INE 2024 projections.

## Sampled Values for Checkpoint Verification

| CUT | Name | population_2024 (our data) |
|-----|------|---------------------------|
| 13101 | Santiago | 544,388 |
| 13201 | Puente Alto | 667,904 |
| 2101 | Antofagasta | 444,276 |
| 5101 | Valparaíso | 320,816 |
| 12104 | San Gregorio | 651 |

San Gregorio (12104) has population 651 — well below 10,000 threshold, confirming the low_population path is exercised by real data.

There are 90 communes with population < 10,000 in the dataset.

## Commits

| Hash | Description |
|------|-------------|
| 4311283 | feat(01-02): fetch INE population CSV and commit 346-commune JSON asset |
| a39995e | test(01-02): add failing tests for population lookup module (RED) |
| e64ef72 | feat(01-02): implement population lookup module (DATA-04 filter substrate) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CSV delimiter and encoding mismatch**
- **Found during:** Task 1 execution
- **Issue:** The bastianolea CSV uses semicolons as delimiter (not commas) and Latin-1 encoding. The initial fetch attempt used UTF-8/comma defaults, causing column resolution failure.
- **Fix:** Added auto-delimiter detection (checks first line for `;`) and encoding fallback loop (utf-8-sig → utf-8 → latin-1, skipping if replacement chars found).
- **Files modified:** `pipeline/scripts/fetch_ine_population.py`
- **Commit:** 4311283

## Known Stubs

None — the population JSON contains real INE data, not placeholder values.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes at trust boundaries beyond what the plan's threat model documents (T-02-01, T-02-02, T-02-03).

## Self-Check: PASSED

- data/ine/poblacion_comunal.json: FOUND (346 entries, verified)
- pipeline/shared/population.py: FOUND
- pipeline/scripts/fetch_ine_population.py: FOUND
- pipeline/tests/test_population.py: FOUND (10 tests green)
- Commits 4311283, a39995e, e64ef72: FOUND in git log
- Human checkpoint (Task 3): APPROVED — user confirmed 5 sampled values match official INE 2024 projections; Assumption A6 closed
