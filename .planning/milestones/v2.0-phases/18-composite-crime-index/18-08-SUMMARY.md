---
phase: 18-composite-crime-index
plan: "08"
subsystem: pipeline
tags: [composite-index, winsorization, nan-masking, bug-fix, pytest]
dependency_graph:
  requires: []
  provides: [CI-02]
  affects: [pipeline/composite_index.py, pipeline/tests/test_composite.py]
tech_stack:
  added: []
  patterns: [nan-mask-scatter pattern for scipy winsorize]
key_files:
  created: []
  modified:
    - pipeline/composite_index.py
    - pipeline/tests/test_composite.py
decisions:
  - "normalize_metric masks NaN before winsorize using boolean mask; winsorize runs on arr[mask] only; results scattered back to arr_w[mask]; NaN positions stay NaN throughout"
  - "All-NaN/empty guard returns all-NaN Series of original length and index"
  - "WR-01 dead arithmetic (score = (...) * 100.0 / 100.0 * 100.0) removed; sole assignment is score = weighted_sum / total_weight"
metrics:
  duration: "8 minutes"
  completed: "2026-06-19"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 18 Plan 08: NaN-Safe Winsorization Fix Summary

NaN masking applied before scipy winsorize in normalize_metric so extreme outlier clip points are derived from real-data maxima, not NaN positions; locked by a new NaN+outlier regression test.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Mask NaN before winsorizing in normalize_metric | ecc8aaa | pipeline/composite_index.py |
| 2 | Add NaN+outlier winsorization correctness test | bf49e26 | pipeline/tests/test_composite.py |

## What Was Built

**Task 1 — normalize_metric fix (pipeline/composite_index.py)**

- Built `mask = ~np.isnan(arr)` and guarded all-NaN/empty input (returns all-NaN Series).
- Initialised `arr_w = np.full_like(arr, np.nan)` then ran `winsorize(arr[mask], ...)` on non-NaN values only, scattering results back to `arr_w[mask]`.
- Min-max scaling computed via `np.nanmin`/`np.nanmax` on `arr_w`, result array initialised to NaN, then filled only at `mask` positions.
- Replaced the false comment "scipy masked array handles this" with an accurate explanation.
- Removed the WR-01 dead line `score = (weighted_sum / total_weight) * 100.0 / 100.0 * 100.0` and its stale comments; the sole assignment is now `score = weighted_sum / total_weight`.
- All 8 pre-existing tests still pass.

**Task 2 — NaN+outlier regression test (pipeline/tests/test_composite.py)**

- Added `test_normalize_nan_outlier_clip`: 346-value series with a 43,000-level outlier at index 0 and NaN at index 10.
- Three assertions: (1) NaN position stays NaN, (2) non-NaN output max == 100.0 proving clip from real data, (3) spread guard holds (25th pctile > 10% of max).
- Full suite: 9 tests pass.

## Deviations from Plan

None — plan executed exactly as written. WR-01 dead arithmetic removal was conditionally specified and was safe to apply (line 146 was the correct sole assignment).

## Known Stubs

None.

## Threat Flags

None — pure Python compute function fix; no new network endpoints, auth paths, or schema changes.

## Self-Check: PASSED

- pipeline/composite_index.py — modified, NaN mask present
- pipeline/tests/test_composite.py — modified, new test present
- Commit ecc8aaa exists (Task 1)
- Commit bf49e26 exists (Task 2)
- Full suite: 9/9 tests pass
