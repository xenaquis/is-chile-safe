---
phase: 14-homicide-as-a-first-class-category
plan: "02"
subsystem: pipeline
tags: [cead, homicide, subgroup-101, scraper, map-payload, data-pipeline]
dependency_graph:
  requires:
    - "14-01: confirmed grupo[]=101 param + RED scaffold"
  provides:
    - "fetch_subgroup_batch in pipeline/cead/client.py (grupo[]=101)"
    - "homicide accumulator loop in scrape_cead.py (2005-2026, rate+count)"
    - "featured_rates.homicidios + homicidios_count populated in 346 commune JSONs"
    - "map-payload.json carries 'hr' (homicide_rate) per entry, 29993B < 30720B"
  affects:
    - "pipeline/cead/client.py — new fetch_subgroup_batch function"
    - "pipeline/shared/schema.py — MapPayloadEntry extended with optional homicide fields"
    - "pipeline/scrape_cead.py — accumulator loop, normalizer wiring, build_map_payload"
    - "pipeline/cead/normalizer.py — attach_featured returns homicidios_count"
    - "data/cead/comunas/* — all 346 commune JSONs updated"
    - "data/cead/map-payload.json — regenerated with hr field"
tech_stack:
  added: []
  patterns:
    - "Abbreviated payload key 'hr' (vs 'homicide_rate') — D-09 compact encoding saves 10B/entry"
    - "Cache-first homicide fetch: cead_subgroup101_{year}_{rate|count}.html, sleep(2.5) on miss only"
    - "Dual int/str year key lookup in build_map_payload fallback (in-memory=int, post-JSON=str)"
    - "Budget escape: homicide_count dropped from map-payload, preserved in per-commune JSON"
key_files:
  created: []
  modified:
    - pipeline/cead/client.py
    - pipeline/shared/schema.py
    - pipeline/scrape_cead.py
    - pipeline/cead/normalizer.py
    - pipeline/tests/test_scrape_cead.py
    - data/cead/comunas/13101.json  # representative — all 346 updated
    - data/cead/map-payload.json
decisions:
  - "Abbreviated 'hr' key in map-payload (vs 'homicide_rate') — saves ~10B per entry, keeps payload under 30KB with real data (29993B < 30720B)"
  - "homicide_count dropped from map-payload (budget escape per Pitfall 3) — preserved in featured_rates.homicidios_count in per-commune JSON"
  - "grupo[]=101 confirmed from 14-01 — fetch_subgroup_batch uses this param exclusively"
  - "Fallback year key lookup tries int then str — in-memory pipeline dicts use int keys, JSON round-trip produces str"
metrics:
  duration: "~35m (including 42 live CEAD requests at 2.5s courtesy delay)"
  completed: "2026-06-16"
  tasks_completed: 3
  files_changed: 390
requirements: [HOM-01]
---

# Phase 14 Plan 02: Homicide Data Acquisition End-to-End Summary

CEAD subgroup-101 (homicidios) data acquisition wired end-to-end: fetch_subgroup_batch added with confirmed grupo[]=101 param, homicide accumulator loop for 2005-2026 (rate + count, cache-first, courtesy delays), normalizer extended with homicidios_count, and map-payload rebuilt with abbreviated "hr" field (29993B < 30720B limit) — all 14-01 RED tests now GREEN.

## Confirmed Facts (Carried Forward)

- **param**: `grupo[]=101` (confirmed 14-01, NOT subgrupo[])
- **two requests per year**: medida=2 (rate) + medida=1 (count)
- **homicide rate range observed (2025)**: Santiago 8.69/100k; national range varies widely
- **years scraped**: 2005–2026 (22 years); 2026 is partial

## Tasks Completed

| Task | Description | Commit | Key Files |
|------|-------------|--------|-----------|
| 1 | fetch_subgroup_batch + MapPayloadEntry extension | 8fdf342 | pipeline/cead/client.py, pipeline/shared/schema.py |
| 2 | Homicide accumulator loop + normalizer + build_map_payload | 77a593d, f2e83fe | pipeline/scrape_cead.py, pipeline/cead/normalizer.py, pipeline/tests/test_scrape_cead.py |
| 3 | Full scrape run — 346 commune JSONs + map-payload populated | 27265ac | data/cead/comunas/, data/cead/map-payload.json |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] build_map_payload int/str year key lookup mismatch**

- **Found during:** Task 3 (scrape run verification)
- **Issue:** `build_map_payload` fallback looked up `featured_rates.homicidios` with `str(year)` (e.g. `"2025"`), but in-memory pipeline dicts store integer year keys. Result: `homicide_rate` was always `None` in the payload despite commune JSONs having data.
- **Fix:** Updated fallback to try `homicidios.get(year)` (int) first, then `homicidios.get(str(year))` (str), covering both in-memory and JSON-round-trip cases.
- **Files modified:** pipeline/scrape_cead.py
- **Commit:** f2e83fe

**2. [Rule 2 - Budget] Abbreviated 'hr' key instead of 'homicide_rate' in map-payload**

- **Found during:** Task 3 (size verification)
- **Issue:** Even with homicide_count dropped, `"homicide_rate"` (12 chars) + value per entry × 346 = 33799B, exceeding 30720B limit. The plan anticipated dropping homicide_count but not that homicide_rate alone would trip the budget.
- **Fix:** Used abbreviated key `"hr"` (2 chars) — saves 10B × 346 = 3460B. Final payload: 29993B. This follows D-09 compact encoding (same pattern as by_family compact list). Updated RED scaffold tests to use `"hr"`.
- **Files modified:** pipeline/scrape_cead.py, pipeline/tests/test_scrape_cead.py
- **Commit:** f2e83fe

### Budget Decisions

- **homicide_count dropped from map-payload**: Adding count would require `"homicide_count":N,` ≈ +22B × 346 = +7612B, total > 37KB. Dropped per plan escape hatch (Pitfall 3). Count lives in `featured_rates.homicidios_count` in per-commune JSON.
- **homicide_rate abbreviated to "hr"**: Even without count, `"homicide_rate"` key alone pushes to 33799B. Abbreviated to `"hr"` brings it to 29993B (under budget). Half B UI will read `"hr"` from map-payload.

## Data Quality

| Metric | Value |
|--------|-------|
| Payload size | 29993 bytes (limit: 30720) |
| Entries with hr | 346/346 (100%) |
| Years scraped | 2005–2026 (22 years) |
| Santiago homicidios years | 22 |
| Santiago 2025 rate | 8.69/100k |
| Test suite | 139 passed, 0 failed |

## Known Stubs

None — homicide data is real CEAD data. The `"hr"` key is populated for all 346 commune entries. Half B UI plans will consume `hr` from map-payload and `featured_rates.homicidios` from per-commune JSON.

## Threat Flags

None — no new network endpoints or auth paths. All threats in plan threat register (T-14-03 through T-14-06) mitigated as designed.

## Self-Check: PASSED

- [x] pipeline/cead/client.py contains `def fetch_subgroup_batch(` with `subgrupo_id` param and `grupo[]` key
- [x] pipeline/shared/schema.py MapPayloadEntry has `homicide_rate: int | None = None` and `homicide_count: int | None = None`
- [x] pipeline/scrape_cead.py contains `homicide_accumulator` and `homicidios_by_year: {}` is replaced
- [x] pipeline/cead/normalizer.py attach_featured returns `homicidios_count` key
- [x] data/cead/comunas/13101.json featured_rates.homicidios has 22 years of data
- [x] data/cead/map-payload.json has `hr` in entries, 29993B < 30720B
- [x] All 139 tests pass (14-01 RED tests now GREEN)
- [x] Commits: 8fdf342, 77a593d, f2e83fe, 27265ac
