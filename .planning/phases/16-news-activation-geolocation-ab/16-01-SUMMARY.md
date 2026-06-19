---
phase: 16-news-activation-geolocation-ab
plan: "01"
subsystem: pipeline/news
tags: [news, geolocation, anti-hallucination, resolver, classifier, schema]
dependency_graph:
  requires: []
  provides: [pipeline/news/resolver.py, ClassifierOutput.commune_name]
  affects: [pipeline/news/schema.py, pipeline/news/classifier.py]
tech_stack:
  added: []
  patterns: [deterministic-name-to-cut-lookup, NFD-accent-normalization, closed-set-validation]
key_files:
  created:
    - pipeline/news/resolver.py
    - pipeline/tests/test_resolver.py
  modified:
    - pipeline/news/schema.py
    - pipeline/news/classifier.py
    - pipeline/tests/test_classifier.py
    - pipeline/tests/test_schema_incidents.py
decisions:
  - LLM emits commune_name (Spanish) + region_hint; CUT resolution is deterministic in resolver.py
  - resolve_cut returns None for unknown names — hallucinated names can never reach the store
  - _norm uses unicodedata NFD + category Mn filter, mirroring Astro frontend normalization
  - region_hint only consulted on multi-entry collision (theoretically impossible at 346 communes)
  - test_scrape_news.py failures are expected — orchestrator references commune_cut; Plan 03 fixes
metrics:
  duration: 18m
  completed: "2026-06-18"
  tasks: 2
  files: 6
---

# Phase 16 Plan 01: Resolver + Classifier Schema Redesign Summary

Deterministic name→CUT resolver and classifier prompt redesign (NEWS-01): LLM emits Spanish commune name instead of a bare CUT code, eliminating ~60-70% wrong-CUT hallucination rate.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create resolver.py + RED tests | 6b733a8 | pipeline/news/resolver.py, pipeline/tests/test_resolver.py |
| 2 | Switch classifier to name-emit + update schema | 5fa2e45 | pipeline/news/classifier.py, pipeline/news/schema.py, pipeline/tests/test_classifier.py, pipeline/tests/test_schema_incidents.py |

## What Was Built

**resolver.py** — Module-level deterministic lookup built from `data/cead/meta/index.json` at import time. Three dicts: `_NAME_TO_ENTRIES` (normalized→entries list), `_CUT_TO_SLUG` (cut→slug). `_norm()` applies NFD + strips Mn-category combining characters (accent-insensitive, case-insensitive). `resolve_cut(name, region_hint=None)` returns `(cut, slug)` or `None`. `slug_for_cut(cut)` returns slug or `None`. No network calls; pure stdlib (unicodedata, pathlib, json).

**schema.py** — `ClassifierOutput.commune_cut` replaced by `commune_name: str | None` and `region_hint: str | None = None`. All other fields and validators unchanged.

**classifier.py** — `_CUT_LIST_STR` removed; new `_COMMUNE_LIST_STR` built as `"<name> (region_id:<N>)"` per line from index.json. `SYSTEM_PROMPT` rewritten to instruct LLM to emit `commune_name` (exact from list) + `region_hint`; still contains "json" per DeepSeek JSON-mode requirement. `VALID_CUTS` membership-reject block removed; name→CUT resolution is now resolver.py's responsibility.

## Verification Results

```
pytest tests/test_resolver.py -x -q → 7 passed
pytest tests/test_resolver.py tests/test_classifier.py -x -q → 11 passed
pytest tests/test_schema_incidents.py tests/test_resolver.py tests/test_classifier.py -q → 24 passed
pytest tests/ -q → 142 passed, 5 failed (all in test_scrape_news.py — expected, addressed in Plan 03)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing update] test_schema_incidents.py ClassifierOutput tests used old commune_cut API**
- **Found during:** Task 2 full test suite run
- **Issue:** `test_classifier_output_null_cut_accepted` and `test_classifier_output_valid_cut_accepted` used `commune_cut` field that no longer exists in ClassifierOutput
- **Fix:** Updated both tests to `commune_name` / `region_hint` API; renamed to `test_classifier_output_null_commune_name_accepted` and `test_classifier_output_commune_name_accepted`
- **Files modified:** pipeline/tests/test_schema_incidents.py
- **Commit:** 5fa2e45

### Expected Failures (Not Deviations)

`test_scrape_news.py` (5 tests) fail because `_make_classifier_output()` in that file still constructs `ClassifierOutput(commune_cut=..., ...)`. Per plan verification note: "if `tests/test_scrape_news.py` breaks on the schema change, that is expected and addressed in Plan 03." These failures will be resolved when Plan 03 updates the orchestrator (scrape_news.py) to use resolver.py.

## Threat Model Compliance

| Threat ID | Status |
|-----------|--------|
| T-16-01 (commune_name spoofing) | Mitigated — resolver's `_norm` lookup against closed 346-name index; unknown names → None |
| T-16-02 (resolver input tampering) | Mitigated — resolve_cut only returns (cut, slug) from index.json closed set |
| T-16-03 (DEEPSEEK_API_KEY disclosure) | Accepted — unchanged pattern |
| T-16-SC (npm/pip installs) | Accepted — no new packages (unicodedata/pathlib/json are stdlib) |

## Known Stubs

None — resolver and schema changes are complete. Downstream integration (Plan 03) wires resolver into scrape_news.py orchestrator.

## Self-Check: PASSED

- pipeline/news/resolver.py: EXISTS
- pipeline/tests/test_resolver.py: EXISTS
- pipeline/news/schema.py commune_name field: EXISTS
- pipeline/news/classifier.py commune_name in prompt: EXISTS, commune_cut absent
- Commits 6b733a8 and 5fa2e45: VERIFIED in git log
