---
phase: 18-composite-crime-index
plan: "01"
subsystem: pipeline
tags: [composite-index, scipy, normalization, data-pipeline]
dependency_graph:
  requires: [data/snapshots/spd_homicide.json, data/snapshots/sii_exposure.json, data/ine/poblacion_comunal.json, data/cead/comunas/]
  provides: [pipeline/composite_config.py, pipeline/composite_index.py, pipeline/build_composite_index.py, data/cead/comparator_table.json, composite_index[2024] in all 346 commune JSON files]
  affects: [data/cead/comunas/*.json, data/cead/comparator_table.json]
tech_stack:
  added: [scipy>=1.13,<2]
  patterns: [winsorized-min-max normalization, SII-cap-fallback, year-alignment-assertion, TDD-scaffold, atomic-write-json]
key_files:
  created:
    - pipeline/composite_config.py
    - pipeline/composite_index.py
    - pipeline/build_composite_index.py
    - pipeline/tests/test_composite.py
    - data/cead/comparator_table.json
  modified:
    - pipeline/requirements.txt
    - data/cead/comunas/*.json (346 files — additive composite_index[2024] enrichment)
decisions:
  - "SII-absent commune available_metrics decremented by 1 (data quality signal, not compute failure)"
  - "sys.path self-fix added to entrypoint for `python pipeline/build_composite_index.py` invocation pattern"
  - "Level 1-5 assigned via pd.qcut with duplicates=drop fallback to percentile-rank"
metrics:
  duration: "~30 minutes"
  completed: "2026-06-19T17:39:00Z"
  tasks_completed: 3
  files_created: 5
  files_modified: 348
---

# Phase 18 Plan 01: Composite Crime Index Core Summary

**One-liner:** Scipy-winsorized 7-metric composite crime index (C-01/C-02 locked) with SII cap fallback and year-alignment assertion, enriching all 346 commune JSON files for 2024 and emitting comparator_table.json.

## What Was Built

### Task 1: scipy pin + composite_config.py + TDD scaffold
- Added `scipy>=1.13,<2` to `pipeline/requirements.txt` (pipeline-only).
- Created `pipeline/composite_config.py` with C-02-locked METRIC_WEIGHTS (sum=1.00, 7 metrics, incivilidades excluded per C-01, spd_homicide_rate documented as M1).
- Created `pipeline/tests/test_composite.py` with 2 GREEN config tests and 6 behavioral stubs (RED until Tasks 2-3).

### Task 2: Pure compute functions in composite_index.py
- `normalize_metric(series)`: scipy winsorize + min-max to [0,100] with NaN re-injection (D-01, T-18-01).
- `get_exposure_denominator(cut, sii, ine)`: SII cap at 5.0 with INE fallback; null-vs-zero guard (D-04, T-18-02).
- `assert_year_alignment(cead, spd, sii)`: raises ValueError on mismatch (D-10, T-18-04).
- `compute_composite(per_metric, weights)`: weighted sum with absent-metric redistribution.
- Confirmed: Providencia CUT 13123 ratio = 5.186 (cap triggered), Las Condes CUT 13114 ratio = 4.034 (SII used).

### Task 3: build_composite_index.py entrypoint
- Reads 4 sources: SPD VHC snapshot, SII exposure snapshot, INE population, 346 commune JSON files.
- Asserts year alignment (CEAD=SPD=SII=2024) before any compute.
- Computes per-commune: SPD homicide rate via SII-capped denominator, 6 CEAD family rates.
- Normalizes each metric across all 346 communes (winsorized min-max).
- Assigns national rank and regional_rank via `region_id_from_cut` (Tarapaca-collision-safe, C-03).
- Assigns level 1-5 via pd.qcut.
- Enriches all 346 commune JSON files additively: `composite_index[str(2024)]`, `spd_homicide_rate[str(2024)]`, `sii_exposure_index[str(2024)]` (featured_rates untouched, D-12).
- Writes `data/cead/comparator_table.json` with 346 entries (Phase 21 handoff).
- All 8 test_composite.py tests GREEN; 187 pipeline tests pass (8 new, no regressions).

## Key Numbers

- Communes enriched: 346
- Metrics: 7 (spd_homicide_rate, cead_robos_rate, cead_vida_rate, cead_propiedad_rate, cead_vif_rate, cead_drogas_rate, cead_armas_rate)
- SII-capped communes: Providencia (13123, ratio 5.186) only
- SII-absent communes: 5 (11201, 11101, 13303, 16207, 4105) — available_metrics decremented to 6
- SPD-absent communes: 141 — assigned spd_homicide_rate = 0.0

## Deviations from Plan

### Auto-adjusted Implementation Details

**1. [Rule 1 - Bug] sys.path self-fix for script invocation**
- Found during: Task 3
- Issue: `python pipeline/build_composite_index.py` failed with `ModuleNotFoundError: No module named 'pipeline'` since script directory (pipeline/) is on sys.path but not repo root.
- Fix: Added sys.path insert at module top (mirrors the pattern pytest.ini uses via `pythonpath = ..`).
- Files modified: pipeline/build_composite_index.py

**2. [Rule 2 - Missing critical functionality] SII-absent available_metrics decrement**
- Found during: Task 3 test_output_schema (RED revealed the gap)
- Issue: SII-absent communes used INE fallback for denominators but the RESEARCH explicitly says available_metrics should be decremented for SII-absent communes.
- Fix: Track `sii_absent_cuts` set and decrement available_metrics by 1 for those communes.
- Files modified: pipeline/build_composite_index.py

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes at trust boundaries introduced. All outputs are static JSON files written via atomic_write_json. Mitigations T-18-01 through T-18-04 implemented as specified.

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| pipeline/composite_config.py | FOUND |
| pipeline/composite_index.py | FOUND |
| pipeline/build_composite_index.py | FOUND |
| pipeline/tests/test_composite.py | FOUND |
| data/cead/comparator_table.json | FOUND |
| Commit 43065a8 (test scaffold) | FOUND |
| Commit 04c249d (pure functions) | FOUND |
| Commit c1672b4 (entrypoint + data) | FOUND |
| 187 pytest pipeline tests | PASSED |
