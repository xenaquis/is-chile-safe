---
phase: 01-data-foundation
plan: "04"
subsystem: pipeline/cead
tags: [normalizer, orchestrator, data-pipeline, trend, slug, ranks, map-payload]
dependency_graph:
  requires: [01-01, 01-02, 01-03]
  provides:
    - pipeline/cead/normalizer.py
    - pipeline/scrape_cead.py
    - pipeline/shared/atomic_write.py (compact=True param added)
  affects: [01-05, phase-2, phase-3, phase-5]
tech_stack:
  added: []
  patterns:
    - NFD-slug-generation
    - quintile-rank-computation
    - all-or-nothing-validation-gate
    - compact-json-map-payload
    - partial-year-marking
key_files:
  created:
    - pipeline/cead/normalizer.py
    - pipeline/scrape_cead.py
    - pipeline/tests/test_normalizer.py
    - pipeline/tests/test_output.py
  modified:
    - pipeline/shared/atomic_write.py
    - pipeline/shared/schema.py
    - pipeline/tests/test_schema.py
decisions:
  - "make_slug strips apostrophes before replacing non-alphanumeric chars with hyphens so O'Higgins → ohiggins (not o-higgins)"
  - "MapPayloadEntry.by_family changed from dict[str, float|None] to list[float|None] ordered per FAMILY_KEYS — compact list format is the only way to keep 346-commune map-payload under 30KB"
  - "atomic_write_json gains compact=True parameter; map-payload files use separators=(',',':') and produce ~27KB vs ~32KB with default separators"
  - "FEATURED_SUBGROUPS.secuestros remains None — Open Question 3 subgroup ID still unconfirmed; homicidios=101 used as documented assumption"
  - "main() delegates to _run_pipeline/_write_all_outputs for testability; live entry point is _main_with_live_session() called from __main__"
  - "A1 assumption (catalog returns all 346 communes) used in orchestrator with a break after first region iteration — revisit if live run returns <346"
metrics:
  duration: "~45 minutes"
  completed: "2026-06-13"
---

# Phase 1 Plan 4: Normalization Layer and Orchestrator Summary

Normalization utilities (trend/slug/ranks/quintile/featured-flags) and the full CEAD pipeline orchestrator with all-or-nothing validation gate and compact map-payload under 30KB — unit-tested offline, awaiting live full-run checkpoint.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Normalizer RED tests | d586ae1 | Done |
| 1 | Normalizer GREEN implementation | 643db54 | Done |
| 2 | Orchestrator RED tests | d175a56 | Done |
| 2 | Orchestrator GREEN implementation | b72c5f3 | Done |
| 3 | checkpoint:human-verify (live full run) | — | AWAITING |

## What Was Built

### pipeline/cead/normalizer.py
- `compute_trend(series, threshold_pct=5.0) -> str`: 3-year trend ('up'/'down'/'stable') from last 4 years. Guards: len<4 returns 'stable'; rate_start==0 returns 'stable' (no division by zero). D-13.
- `make_slug(name) -> str`: NFD decompose → strip combining marks → remove apostrophes → lowercase → replace non-alnum runs with '-' → strip edge hyphens. 'Ñuñoa'→'nunoa', "O'Higgins"→'ohiggins', 'Aysén'→'aysen'.
- `compute_ranks(records, year) -> list[dict]`: national_rank + regional_rank by rate_per_100k descending. low_population=True or empty series → rank=None (D-12). Regional rank scoped per region_id.
- `compute_level(rate, all_rates) -> int`: percentile → quintile 1-5 (1=lowest crime, 5=highest). Matches prototype data.js 'level' field.
- `FEATURED_FAMILIES = {'propiedad', 'vida'}`, `FEATURED_SUBGROUPS = {'homicidios': 101, 'secuestros': None}` (D-06).
- `attach_featured(commune_data) -> dict`: builds featured_rates dict with propiedad/homicidios/secuestros by year. Never fabricates data.

### pipeline/scrape_cead.py
- `main() -> int`: returns 0/1; delegates to `_main_with_live_session()` when run as `__main__`.
- `_main_with_live_session()`: creates CEAD session, fetches 346-commune catalog (raises if ≠346), calls `_run_pipeline` + `_write_all_outputs`.
- `_run_pipeline(session, catalog, run_date)`: accumulates CEAD batches per region×family×year with 2.5s sleep (D-03), caches raw HTML (D-04), parses and normalizes into 346 ComunaRecord dicts + region/national aggregates.
- `_write_all_outputs(communes, regions, national, output_dir)`: calls `_validate_communes` FIRST (D-14 gate), then writes all files atomically including compact map-payload.json + per-year payloads.
- `build_map_payload(records, year, all_rates) -> dict`: 346-entry payload with id/rate/level/by_family (compact list). Serializes to ~27KB with separators=(',',':') — under 30KB limit (DATA-03).
- `build_meta_index(records) -> list`: 346 entries each with cut/name/slug/region_id/population/low_population.
- `mark_partial_year(series, run_date) -> list`: marks current year partial=True if run before Dec 31 (Open Question 2).
- `filter_series_for_trend(series) -> list`: excludes partial years from trend computation.

### pipeline/shared/atomic_write.py (modified)
- Added `compact: bool = False` parameter. When `compact=True`, writes minified JSON with `separators=(',',':')` — used for map-payload files to meet 30KB constraint.

### pipeline/shared/schema.py (modified)
- `MapPayloadEntry.by_family`: changed from `dict[str, float | None]` to `list[float | None]` (ordered per FAMILY_KEYS). Required for 30KB compliance — named-key dict adds ~110 chars/entry × 346 = ~40KB overhead.

## Test Results

```
95 passed in 0.83s
```

- test_normalizer.py: 24 tests — trend (7), slug (5), ranks (4), compute_level (4), FEATURED_FAMILIES/SUBGROUPS (3), attach_featured (1)
- test_output.py: 7 tests — 30KB guard, validate-before-write ordering, main returns 1 on failure, main returns 0 on success, map-payload entry schema, meta/index structure, partial year marking

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] make_slug apostrophe handling**
- **Found during:** Task 1 GREEN (test failure)
- **Issue:** `make_slug("O'Higgins")` returned `'o-higgins'` instead of `'ohiggins'` because NFD normalization preserves apostrophes and the `re.sub(r"[^a-z0-9]+", "-", ...)` pattern converts them to hyphens.
- **Fix:** Added `re.sub(r"[''`']", "", ascii_only)` before the hyphen replacement step.
- **Files modified:** pipeline/cead/normalizer.py
- **Commit:** 643db54

**2. [Rule 2 - Missing critical functionality] MapPayloadEntry.by_family schema change**
- **Found during:** Task 2 (30KB size guard test failure)
- **Issue:** A 346-commune map-payload with 7 named family keys per entry serializes to ~62KB — more than double the 30KB limit even with compact JSON. Named-key dicts are inherently verbose.
- **Fix:** Changed `by_family` from `dict[str, float | None]` to `list[float | None]` ordered per FAMILY_KEYS. This is documented in schema.py and in meta/catalog.json (key order mapping). Compact serialization with separators=(',',':') then produces ~27KB.
- **Files modified:** pipeline/shared/schema.py, pipeline/shared/atomic_write.py, pipeline/tests/test_schema.py, pipeline/tests/test_output.py
- **Commit:** b72c5f3

## Open Questions / Deferred Items

- **Open Question 3 (carried from Plan 03):** `FEATURED_SUBGROUPS['secuestros']` is None — kidnapping subgroup ID not confirmed. The live checkpoint (Task 3) should be used to enumerate CEAD subgroups for familia 1 (vida) and identify the secuestros subgroup ID. Homicidios subgroup ID=101 is assumed but not live-confirmed.
- **A1 assumption (catalog):** `_run_pipeline` uses a `break` after the first region iteration assuming catalog returns all 346 communes for any region. If the live run produces <346 communes, remove the `break` and loop over all regions.

## Known Stubs

None — all pipeline logic is wired. Live data is fetched during the checkpoint run.

## Threat Flags

None — no new network endpoints or trust boundaries introduced beyond what the plan specified.

## Self-Check: PASSED

- pipeline/cead/normalizer.py: FOUND (contains `FEATURED_FAMILIES`, `compute_level`, `compute_trend`, `make_slug`)
- pipeline/scrape_cead.py: FOUND (contains `def main`, `sys.exit`, `validate_all_communes`, `atomic_write_json`)
- pipeline/tests/test_normalizer.py: FOUND (24 tests)
- pipeline/tests/test_output.py: FOUND (7 tests)
- Commits d586ae1, 643db54, d175a56, b72c5f3: all present in git log
- 95 tests pass, 0 failures
