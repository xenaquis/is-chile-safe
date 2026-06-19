---
phase: 23-enusc-communal-victimization-layer
plan: "01"
subsystem: pipeline/snapshots
tags: [enusc, vhdv, ingestion, snapshot, sha256, tdd]
dependency_graph:
  requires: []
  provides: [data/snapshots/enusc_vhdv.json, pipeline/snapshots/fetch_enusc_vhdv.py]
  affects: [data/cead/comunas/{cut}.json (via Phase 23-02 enrichment)]
tech_stack:
  added: []
  patterns: [sha256-before-parse, accent-normalized-column-match, CACHE_ONLY-mode, atomic-write-json]
key_files:
  created:
    - pipeline/snapshots/fetch_enusc_vhdv.py
    - pipeline/tests/test_fetch_enusc_vhdv.py
    - data/snapshots/enusc_vhdv.json
  modified:
    - data/snapshots/ATTRIBUTION.md
decisions:
  - "Column header matching uses accent-normalized comparison (NFD strip) — real XLSX uses 'victimas'/'logaritmico' without accent, differing from SEED-002 profile"
  - "vhdv_rate stored as proportion 0-1, never rescaled to per-100k — explicit guard in caveat and ATTRIBUTION"
  - "ATTRIBUTION.md REFERENCE-ONLY preamble preserved; enusc_vhdv.json block notes WIRED departure explicitly"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_created: 3
  files_modified: 2
---

# Phase 23 Plan 01: ENUSC VHDV Fetcher + Snapshot Summary

**One-liner:** SHA256-guarded INE ENUSC 2024 VHDV ingestion producing a 136-record versioned snapshot with accent-normalized column matching and full provenance.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Write failing pytest (RED) | b555489 | pipeline/tests/test_fetch_enusc_vhdv.py |
| 2 | Implement fetch_enusc_vhdv.py (GREEN) | 181ec2a | pipeline/snapshots/fetch_enusc_vhdv.py |
| 3 | Generate snapshot + ATTRIBUTION row | 91733c8 | data/snapshots/enusc_vhdv.json, ATTRIBUTION.md, fetch_enusc_vhdv.py (accent fix) |

## Verification

- `python -m pytest pipeline/tests/test_fetch_enusc_vhdv.py -x -q` — 5 passed
- `data/snapshots/enusc_vhdv.json` — 136 records, all vhdv_rate in (0,1), required keys present
- `pipeline/cache/enusc_vhdv.xlsx` — NOT tracked (git-ignored per pipeline/cache/*)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Accent-normalized column matching**
- **Found during:** Task 3 (running fetcher against real cache)
- **Issue:** Real XLSX uses "Porcentaje de hogares victimas de delitos violentos 2024" (no accent on "i" in victimas) and "Coeficiente de variacion logaritmico" (no accent), while SEED-002 profile showed accented versions. Exact string match failed.
- **Fix:** Added NFD accent normalization function `_norm()` in `main()` to match column names by accent-stripped lowercase form. Robust against minor INE encoding variations on future republish.
- **Files modified:** pipeline/snapshots/fetch_enusc_vhdv.py
- **Commit:** 91733c8

## Success Criteria Verification

- [x] VL-01 (source half): isolated fetcher writes a provenance-bearing versioned snapshot from a sha256-verified cache; never downloads in CI (CACHE_ONLY=1 skips download)
- [x] VL-02 (source half): all 136 parsed rows carry CUT raw digits from col A; make_slug cross-check logs discrepancies without failing
- [x] No Phase-18 file touched

## Known Stubs

None — all 136 records have real data from the INE XLSX.

## Threat Surface Scan

No new network endpoints, auth paths, or trust-boundary changes beyond what the plan's threat model documented. T-23-01 (XLSX tampering) fully mitigated by sha256 assertion before parse.

## Self-Check: PASSED

- pipeline/tests/test_fetch_enusc_vhdv.py: EXISTS
- pipeline/snapshots/fetch_enusc_vhdv.py: EXISTS
- data/snapshots/enusc_vhdv.json: EXISTS
- data/snapshots/ATTRIBUTION.md: MODIFIED
- Commits b555489, 181ec2a, 91733c8: CONFIRMED in git log
