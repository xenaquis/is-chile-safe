---
phase: 23-enusc-communal-victimization-layer
plan: "02"
subsystem: pipeline/enrichment
tags: [enusc, vhdv, enrichment, additive, tdd, ci-wiring]
dependency_graph:
  requires: [23-01]
  provides: [pipeline/build_enusc_enrichment.py, pipeline/tests/test_build_enusc_enrichment.py]
  affects: [data/cead/comunas/{cut}.json (enusc_vhdv key), .github/workflows/cead-scraper.yml]
tech_stack:
  added: []
  patterns: [additive-enrichment, overwrite-refusal, graceful-degrade, continue-on-error, tdd-red-green]
key_files:
  created:
    - pipeline/build_enusc_enrichment.py
    - pipeline/tests/test_build_enusc_enrichment.py
  modified:
    - .github/workflows/cead-scraper.yml
decisions:
  - "overwrite-refusal: if enusc_vhdv pre-exists with a different value, raise RuntimeError rather than silently overwrite — data integrity over convenience"
  - "idempotent re-run: identical value re-write is a no-op (no error) to allow safe re-runs without statefulness"
  - "CACHE_ONLY=1 on fetch step in CI: no stable ENUSC URL; cache must be manually deposited; CI never attempts network download"
metrics:
  duration: "~10 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_created: 2
  files_modified: 1
---

# Phase 23 Plan 02: ENUSC VHDV Enrichment + CI Wiring Summary

**One-liner:** Additive enusc_vhdv enrichment of 136 commune JSONs with byte-unchanged Phase-18 guarantee, overwrite-refusal guard, and graceful-degrade CI steps wired after the CEAD scraper.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Write failing pytest (RED) | 0a5d6f0 | pipeline/tests/test_build_enusc_enrichment.py |
| 2 | Implement build_enusc_enrichment.py (GREEN) | 1e72daf | pipeline/build_enusc_enrichment.py |
| 3 | Wire ENUSC steps into cead-scraper.yml | c0a1c91 | .github/workflows/cead-scraper.yml |

## Verification

- `python -m pytest pipeline/tests/test_build_enusc_enrichment.py -x -q` — 5 passed
- `cead-scraper.yml` order assertion: fetch_enusc_vhdv.py after scrape_cead.py and before build_composite_index.py — PASSED
- CACHE_ONLY set on fetch step, both new steps have continue-on-error: true

## Deviations from Plan

None — plan executed exactly as written.

## Success Criteria Verification

- [x] VL-01: enrichment is isolated and degrades gracefully (exit 0) when snapshot absent; CI never breaks CEAD (continue-on-error on both steps)
- [x] VL-02: coverage assertion enforces exactly 136 resolved CUTs (RuntimeError otherwise)
- [x] VL-05 (additive half): Phase-18 outputs byte-unchanged after enrichment, proven by pytest (test_additive_only + test_phase18_byte_unchanged)

## Known Stubs

None.

## Threat Surface Scan

No new network endpoints, auth paths, or trust-boundary changes. T-23-04 (Phase-18 field tampering) fully mitigated by additive-only write + pytest guards. T-23-05 (CEAD pipeline DoS by ENUSC failure) mitigated by continue-on-error + sys.exit(0) on absent snapshot.

## Self-Check: PASSED

- pipeline/tests/test_build_enusc_enrichment.py: EXISTS
- pipeline/build_enusc_enrichment.py: EXISTS
- .github/workflows/cead-scraper.yml: MODIFIED (fetch + enrich steps inserted)
- Commits 0a5d6f0, 1e72daf, c0a1c91: CONFIRMED in git log
