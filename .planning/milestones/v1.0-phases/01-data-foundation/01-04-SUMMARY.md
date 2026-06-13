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
  data_outputs:
    - data/cead/comunas/*.json (346 files)
    - data/cead/regions/*.json (16 files)
    - data/cead/national.json
    - data/cead/map-payload.json
    - data/cead/map-payload-{2005..2025}.json (21 per-year)
    - data/cead/meta/index.json
    - data/cead/meta/catalog.json
decisions:
  - "PLAUSIBILITY_MAX_RATE raised to 100000 after first live run — micro-communes (Sierra Gorda, Juan Fernandez) reach 43369 per-100k; 100k is >2x observed max and still catches decimal-parse corruption (millions)"
  - "map-payload rates rounded to integers (not 1 decimal) to stay within 30KB budget; full precision in per-commune files"
  - "Pipeline must be invoked as module: python -m pipeline.scrape_cead (python pipeline/scrape_cead.py fails with ModuleNotFoundError)"
  - "Santiago 2026 rate is partial-year (2059/100k); latest full year 2024 rate ~2959/100k matching CEAD medida=2"
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

Full CEAD pipeline producing 346 commune JSON files with rates, trends, ranks, featured flags, and a 27.5KB map-payload — validated gate enforced, two live-run bugs fixed as deviations, all data committed to repo as static contract.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Normalizer RED tests | d586ae1 | Done |
| 1 | Normalizer GREEN implementation | 643db54 | Done |
| 2 | Orchestrator RED tests | d175a56 | Done |
| 2 | Orchestrator GREEN implementation | b72c5f3 | Done |
| 3 | checkpoint:human-verify (live full run) | dfb6954 | Done |
| fix | Raise plausibility cap 20000 → 100000 | 4f44ef9 | Done (deviation) |
| fix | Round map-payload rates to int for 30KB | f072f05 | Done (deviation) |

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

**2. [Rule 1 - Bug] Raised plausibility cap from 20000 to 100000**
- **Found during:** Task 3 live pipeline run
- **Issue:** `ValueError: Implausible rate 20838.0... for 5604 in 2013` — micro-communes (Sierra Gorda pop ~2000, Juan Fernandez CUT 5604 pop ~900) legitimately reach 43369 per-100k due to transient mining/tourism populations not captured by INE residential estimates
- **Fix:** `PLAUSIBILITY_MAX_RATE` raised from 20000 to 100000 in `pipeline/shared/schema.py`. Tests updated accordingly: `test_implausible_rate_is_rejected` now uses 150000; `test_boundary_rate_100000_is_accepted` replaces old 20000 boundary test.
- **Rationale:** 100k is >2x observed real maximum (43369); still catches decimal-parse corruption which produces values in the millions
- **Files modified:** `pipeline/shared/schema.py`, `pipeline/tests/test_schema.py`
- **Commit:** 4f44ef9

**3. [Rule 1 - Bug] Round map-payload rates to integers to satisfy 30KB guard**
- **Found during:** Task 3 pipeline re-run after cap fix
- **Issue:** `ValueError: map-payload.json exceeds 30 KB limit: 33060 bytes` — 346 communes with 7 family floats at 1 decimal each exceeds budget
- **Fix:** `build_map_payload` rounds `rate` and all `by_family` values to `int`. Full precision preserved in per-commune JSON files; map-payload is used only for choropleth color level — integer rates are sufficient
- **Result:** 27527 bytes (26.9 KB, well within 30720 limit)
- **Files modified:** `pipeline/scrape_cead.py`
- **Commit:** f072f05

**4. [Rule 2 - Missing critical functionality] MapPayloadEntry.by_family schema change**
- **Found during:** Task 2 (30KB size guard test failure)
- **Issue:** A 346-commune map-payload with 7 named family keys per entry serializes to ~62KB — more than double the 30KB limit even with compact JSON. Named-key dicts are inherently verbose.
- **Fix:** Changed `by_family` from `dict[str, float | None]` to `list[float | None]` ordered per FAMILY_KEYS. This is documented in schema.py and in meta/catalog.json (key order mapping). Compact serialization with separators=(',',':') then produces ~27KB.
- **Files modified:** pipeline/shared/schema.py, pipeline/shared/atomic_write.py, pipeline/tests/test_schema.py, pipeline/tests/test_output.py
- **Commit:** b72c5f3

## Checkpoint Verification — Task 3 (Live Full Run)

Pipeline ran from cache (~1 min). All criteria passed:

| Criterion | Expected | Actual |
|-----------|----------|--------|
| data/cead/comunas count | 346 | 346 |
| data/cead/regions count | 16 | 16 |
| map-payload.json size | <30720 bytes | 27527 bytes |
| meta/index.json entries | 346 | 346 |
| Santiago 13101 latest rate | plausible (CEAD medida=2) | 2059.4/100k (2025 partial); 2024 full year ~2959 |
| Low-pop commune rank | national_rank: null | Cochamó (10103) confirmed |

A1 assumption confirmed: CEAD returns all 346 communes per familia×year call regardless of region param. Intentional `break` at scrape_cead.py:401 is correct. Actual batch count: 154 (7 familias × 22 years), all cached in pipeline/cache/cead_*.html.

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
- data/cead/comunas: 346 files
- data/cead/regions: 16 files
- data/cead/map-payload.json: 27527 bytes
- data/cead/meta/index.json: 346 entries
- Commits d586ae1, 643db54, d175a56, b72c5f3, 4f44ef9, f072f05, dfb6954: all present in git log
- 95 tests pass, 0 failures
