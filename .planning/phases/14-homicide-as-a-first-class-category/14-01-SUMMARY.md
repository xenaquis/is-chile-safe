---
phase: 14-homicide-as-a-first-class-category
plan: "01"
subsystem: pipeline
tags: [cead, homicide, test-fixtures, tdd-red, param-confirmation]
dependency_graph:
  requires: []
  provides:
    - "Confirmed CEAD POST param for homicide subgroup 101 (grupo[]=101)"
    - "Offline HTML fixtures for subgroup-101 rate and count responses"
    - "RED Nyquist test scaffold for homicide accumulator (3 tests, 14-02 turns GREEN)"
  affects:
    - "pipeline/tests/test_scrape_cead.py — 3 tests RED, 1 GREEN"
    - "pipeline/experiments/test_subgroup101.py — param corrected"
tech_stack:
  added: []
  patterns:
    - "All-zero fallback detection: parse_cead_float on every value, not just row count"
    - "Nyquist RED scaffold: test asserts desired post-implementation payload keys before code exists"
key_files:
  created:
    - pipeline/tests/fixtures/cead_subgroup101_rate_sample.html
    - pipeline/tests/fixtures/cead_subgroup101_count_sample.html
    - pipeline/tests/test_scrape_cead.py
  modified:
    - pipeline/experiments/test_subgroup101.py
decisions:
  - "CONFIRMED param is grupo[]=101, NOT subgrupo[]=101 — subgrupo[] is silently ignored (all-zero rows)"
  - "Rate (medida=2) and count (medida=1) require TWO SEPARATE REQUESTS — medida is single-valued per request"
  - "Numeric zero renders as '0,0000000000' (full-decimal format_4). parse_cead_float already handles it (0.0 not None)"
metrics:
  duration: "~25m"
  completed: "2026-06-16"
  tasks_completed: 3
  files_changed: 4
requirements: [HOM-01]
---

# Phase 14 Plan 01: Subgroup-101 Live Confirmation + RED Scaffold Summary

Live CEAD confirmation establishing grupo[]=101 as the authoritative homicide param, capturing offline fixtures, and laying the RED test scaffold for 14-02 to implement against.

## Confirmed Facts (AUTHORITATIVE — 14-02 MUST implement against these)

### Fact 1: The Correct Param is `grupo[]=101`, NOT `subgrupo[]=101`

`subgrupo[]=101` is **silently ignored** by the CEAD endpoint. It returns 5 rows of
`0,0000000000` for every row including TOTAL PAÍS — the all-zero result looks like
valid data but is the full `vida` aggregate with the filter suppressed.

`grupo[]=101` returns plausible homicide rates:
- TOTAL PAÍS: 5,07/100k
- Región Metropolitana: 5,49/100k
- Provincia de Santiago: 5,40/100k
- Santiago: 5,69/100k
- Cerrillos: 7,76/100k

**14-02 MUST use `grupo[]=101` in all homicide POST payloads.**

### Fact 2: Rate and Count Require TWO SEPARATE REQUESTS

`medida` is single-valued per request. Rate and count come back numerically different:
- `medida=2` (rate, grupo[]=101): TOTAL PAÍS 5,07 · Santiago 5,69 /100k
- `medida=1` (count, grupo[]=101): TOTAL PAÍS 1.019 · Santiago 31 (small integers)

The pipeline must POST twice for each year to collect both metrics.

### Fact 3: Zero-Marker is `0,0000000000` (full-decimal)

Genuine numeric zero renders as `0,0000000000` in the CEAD response
(formato_4, full decimals). This is distinct from the missing-value markers
`-`, `S/I`, `N/A`, `` (empty) which `parse_cead_float` already maps to `None`.
A genuine zero parses to `0.0` — not `None`. CEAD Assumption A3 is now closed.

## Tasks Completed

| Task | Description | Commit | Key Files |
|------|-------------|--------|-----------|
| A (script fix) | Corrected experiment script: subgrupo[]→grupo[]=101; all-zero fallback detection | a9d8e9a | pipeline/experiments/test_subgroup101.py |
| B (fixtures) | Copied cache HTML to test fixtures (latin-1 bytes verbatim) | e7da8b3 | pipeline/tests/fixtures/cead_subgroup101_{rate,count}_sample.html |
| C (TDD RED) | Wrote RED scaffold: 3 failing tests for homicide_rate/count keys, 1 passing parser test | c214399 | pipeline/tests/test_scrape_cead.py |

## TDD Gate Compliance

RED gate: `test(14-01)` commit c214399 — 3 tests fail with clear "key missing" assertion messages.
GREEN gate: 14-02 will turn them green by adding `homicide_rate`/`homicide_count` to `build_map_payload`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Experiment script fallback never fired despite subgrupo[] being wrong**

- **Found during:** Task A (script fix)
- **Issue:** Original fallback `if len(rows_a) == 0` never triggered because `subgrupo[]=101` returns 5 rows of all-zero values — row count is non-zero, but data is garbage.
- **Fix:** Added `_is_all_zero()` helper that checks whether every parsed value is `0.0`. Primary payload changed from `subgrupo[]` to `grupo[]` (confirmed correct). Fallback now detects both empty rows AND all-zero rows.
- **Files modified:** pipeline/experiments/test_subgroup101.py
- **Commit:** a9d8e9a

## Fixtures Verified

| Fixture | Rows Parsed | Sample Value (2024) |
|---------|-------------|---------------------|
| cead_subgroup101_rate_sample.html | 5 | TOTAL PAÍS: 5,0730900849/100k |
| cead_subgroup101_count_sample.html | 5 | TOTAL PAÍS: 1.019 (as '1.019,0000000000') |

Both fixtures load offline via `parse_cead_table` without live network access.

## Test Results (RED State — Expected)

```
FAILED test_map_payload_entry_has_homicide_rate
  AssertionError: homicide_rate key missing from map-payload entry '10000'.
  This test is RED until 14-02 implements the homicide accumulator loop.

FAILED test_map_payload_entry_has_homicide_count
  AssertionError: homicide_count key missing from map-payload entry '10000'.
  This test is RED until 14-02 implements the homicide accumulator loop.

FAILED test_map_payload_346_entries_with_homicide_under_30kb
  AssertionError: homicide_rate key missing — test is RED until 14-02 implements accumulator

PASSED test_cead_subgroup101_rate_fixture_yields_plausible_rates
  (parser test — exercises existing parse_cead_table against real fixture; GREEN now)

Full suite: 3 failed, 136 passed (suite collects without errors)
```

## Known Stubs

None — no UI stubs introduced. Pipeline code not yet modified (14-02 does that).

## Threat Flags

None — no new network endpoints or auth paths introduced. The experiment script accesses the existing CEAD gov endpoint with a single pair of courtesy requests (no loop). Fixtures are static committed HTML.

## Self-Check: PASSED

- [x] pipeline/experiments/test_subgroup101.py — modified, committed a9d8e9a
- [x] pipeline/tests/fixtures/cead_subgroup101_rate_sample.html — created, committed e7da8b3
- [x] pipeline/tests/fixtures/cead_subgroup101_count_sample.html — created, committed e7da8b3
- [x] pipeline/tests/test_scrape_cead.py — created, committed c214399
- [x] 3 RED tests fail with clear "key missing" messages (not import/collection errors)
- [x] Full suite (139 tests) collects and runs without errors
