---
phase: 20-methodology-sources-hardening
plan: "04"
subsystem: validators
tags: [ci-guards, ine-spotcheck, figure-registry, forbidden-language, pytest, src-01, src-05, mth-04]
dependency_graph:
  requires: ["20-01", "20-02", "20-03"]
  provides: ["INE population spot-check CI", "figure-registry zero-orphan validator", "13-validator suite"]
  affects: ["pipeline/tests/", "site/scripts/validate/"]
tech_stack:
  added: []
  patterns: ["pytest parametrize for ground-truth spot-check", "token-group OR-AND registry validation"]
key_files:
  created:
    - pipeline/tests/test_ine_population_spotcheck.py
    - site/scripts/validate/figure-registry.mjs
  modified:
    - site/scripts/validate/all.mjs
    - data/SOURCES.md
decisions:
  - "INE spot-check uses exact-match tolerance (integer projections are deterministic; rounding not expected within same vintage)"
  - "figure-registry uses token-group OR-AND matching (at least one group, all tokens within group) for flexibility on multi-source figures"
  - "F15 news layer: added ## News feeds RSS section to SOURCES.md since 20-01 did not include it; this was the only orphan found"
  - "forbidden-language.mjs confirmed gated + registered (no changes needed)"
metrics:
  duration: "~8 minutes"
  completed: "2026-06-19"
  tasks_completed: 3
  files_changed: 4
---

# Phase 20 Plan 04: CI Guards (INE Spot-Check + Figure-Registry + Forbidden-Language) Summary

**One-liner:** INE population spot-check pytest (9 tests, 7 communes) + figure-registry zero-orphan validator registered as 13th — full suite 13/13 PASS, pipeline 179/179 PASS.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | INE population spot-check pytest (SRC-01) | 11e4a71 | pipeline/tests/test_ine_population_spotcheck.py |
| 2 | Figure-registry validator + register as 13th (SRC-05) | 7568719 | site/scripts/validate/figure-registry.mjs, all.mjs, data/SOURCES.md |
| 3 | Verify forbidden-language validator (MTH-04) | — (no code change needed) | — |

---

## Verification Results

### Build
- **791 pages** built in 19.23s (ROLLOUT_ALL=true, 346 communes)

### Validation Suite
```
13/13 validators passed

  PASS  structure
  PASS  commune
  PASS  rollout
  PASS  region
  PASS  crime
  PASS  hreflang
  PASS  schema
  PASS  map
  PASS  forbidden-language
  PASS  coverage
  PASS  spine
  PASS  seo
  PASS  figure-registry        ← new (13th)
```

### Pipeline Pytest
```
179 passed, 12 warnings in 6.45s
```
(12 warnings are pre-existing feedparser DeprecationWarning, not from new test)

### INE Spot-Check (new test)
```
9 passed in 0.14s

  PASS  test_data_file_exists
  PASS  test_at_least_346_communes
  PASS  test_commune_population_matches_official_ine[1101-231962-Iquique]
  PASS  test_commune_population_matches_official_ine[2101-444276-Antofagasta]
  PASS  test_commune_population_matches_official_ine[4101-267400-La Serena]
  PASS  test_commune_population_matches_official_ine[13101-544388-Santiago]
  PASS  test_commune_population_matches_official_ine[13110-407297-La Florida]
  PASS  test_commune_population_matches_official_ine[8101-239776-Concepcion]
  PASS  test_commune_population_matches_official_ine[1402-1374-Camina]
```

### Figure-Registry Validator (new validator #13)
```
figure-registry: PASS — all 13 in-scope figures (F1-F12, F15) have registered sources
                          in data/SOURCES.md (zero orphans)
```

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Added ## News feeds RSS section to data/SOURCES.md**
- **Found during:** Task 2 (figure-registry validator execution)
- **Issue:** F15 (news incidents) was an orphan because SOURCES.md lacked any news/RSS entry. Plans 20-01 through 20-03 did not add this section.
- **Fix:** Added `## News feeds — qualitative incident layer (RSS)` section to data/SOURCES.md documenting Emol/BioBio/T13/Cooperativa RSS feeds, the processing pipeline, attribution requirements, measure semantics, vintage, and licence. No URLs fabricated; feeds are the live-production ones from P16.
- **Files modified:** data/SOURCES.md
- **Commit:** 7568719

---

## Forbidden-Language Validator Verification (MTH-04)

Confirmed gated and registered:
- **Gated:** exits 1 when `dist/` does not exist (line 26-29 of forbidden-language.mjs)
- **Registered:** entry #9 in VALIDATORS array of all.mjs
- **Coverage:** guards `zona peligrosa`, `area peligrosa`, `comuna peligrosa`, `barrio peligroso`, `dangerous zone/area/commune/neighborhood`, `100% safe/seguro`, `the safest`, etc.
- **Allow-list:** CEAD-attributed superlatives exempted via regex window check
- **Result:** 0 forbidden terms found across all 791 HTML pages
- **Decision:** No code change needed — current coverage matches MTH-04 spec intent

---

## Known Stubs

None.

---

## Threat Flags

None. All changes are offline validators (no new network endpoints, auth paths, or schema changes at trust boundaries).

---

## Self-Check: PASSED

- `pipeline/tests/test_ine_population_spotcheck.py` — FOUND
- `site/scripts/validate/figure-registry.mjs` — FOUND
- Commit 11e4a71 (test INE spot-check) — FOUND in git log
- Commit 7568719 (figure-registry validator) — FOUND in git log
- 13/13 validators passed (confirmed in build output above)
- 179/179 pytest passed
