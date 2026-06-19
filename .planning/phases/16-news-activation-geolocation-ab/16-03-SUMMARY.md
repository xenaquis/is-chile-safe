---
phase: 16-news-activation-geolocation-ab
plan: "03"
subsystem: pipeline/news
tags: [schema, orchestrator, resolver, tdd, news, geolocation]
dependency_graph:
  requires: ["16-01", "16-02"]
  provides: ["NEWS-03"]
  affects: ["data/incidents/current.json", "pipeline/scrape_news.py"]
tech_stack:
  added: []
  patterns:
    - "resolve_cut(name, region_hint) → (cut, slug) | None — anti-hallucination guard"
    - "Provider-aware API key check: NEWS_PROVIDER env selects key_env"
    - "Optional Pydantic field with default for back-compat (slug: str | None = None)"
key_files:
  created: []
  modified:
    - pipeline/news/schema.py
    - pipeline/news/store.py
    - pipeline/scrape_news.py
    - pipeline/tests/test_schema_incidents.py
    - pipeline/tests/test_store.py
    - pipeline/tests/test_scrape_news.py
decisions:
  - "slug is optional with default=None in IncidentRecord for back-compat with existing current.json (Pitfall 1)"
  - "Orchestrator drops incident when resolve_cut returns None — never let hallucinated commune through"
  - "Provider-aware key check reads MINIMAX_API_KEY when NEWS_PROVIDER=minimax (Pitfall 6)"
  - "Graceful exit-0 on missing key per CLAUDE.md pattern — renamed test to reflect contract"
metrics:
  duration: "20m"
  completed: "2026-06-18"
  tasks_completed: 2
  tasks_total: 3
  files_changed: 6
---

# Phase 16 Plan 03: Schema Slug + Orchestrator Resolver Wiring Summary

IncidentRecord gains optional `slug` field (back-compat), orchestrator rewired to resolve LLM commune_name → (cut, slug) via deterministic resolver, dropping hallucinated names.

## Tasks

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Add slug to IncidentRecord + build_incident | DONE | 7ce2188 |
| 2 | Rewire orchestrator to resolve name→(cut, slug) | DONE | a484224 |
| 3 | Live pipeline run → current.json | CHECKPOINT (key-gated) | — |

## What Was Built

**Task 1 (schema + store):** `IncidentRecord.slug: str | None = None` added to `pipeline/news/schema.py`. `build_incident` in `store.py` gains a `slug=None` keyword param that is included in the returned dict. Back-compat preserved: any existing `current.json` without `slug` still validates (Pydantic optional with default). Three new tests added.

**Task 2 (orchestrator):** `pipeline/scrape_news.py` now:
- Imports `resolve_cut` from `pipeline.news.resolver`
- Replaces broken `result.commune_cut` (removed in Plan 01) with `resolve_cut(result.commune_name, result.region_hint)`
- Drops incident with `continue` when `resolve_cut` returns `None` (anti-hallucination guard, T-16-07)
- Unpacks `cut, slug = resolved` and passes `slug=slug` to `build_incident`
- Provider-aware key check: reads `MINIMAX_API_KEY` when `NEWS_PROVIDER=minimax`, `DEEPSEEK_API_KEY` otherwise (Pitfall 6 / T-16-09)
- Five existing `test_scrape_news.py` tests updated (commune_cut→commune_name); three new tests added

**Full pytest suite: 153 passed, 0 failed.**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_main_no_api_key_returns_1 expected wrong exit code**
- **Found during:** Task 2 test update
- **Issue:** Existing test asserted `result == 1` on missing key, but orchestrator has always returned `0` (graceful exit per CLAUDE.md "pipeline debe fallar con gracia y alertar")
- **Fix:** Renamed to `test_main_no_api_key_returns_0` and corrected assertion to match actual contract
- **Files modified:** pipeline/tests/test_scrape_news.py
- **Commit:** a484224

**2. [Rule 1 - Bug] test_incidents_file_valid_round_trip expected stale field set**
- **Found during:** Task 1 GREEN phase
- **Issue:** Test asserted exact field keys of IncidentRecord — did not include `slug` after it was added
- **Fix:** Updated expected set to include `slug`
- **Files modified:** pipeline/tests/test_schema_incidents.py
- **Commit:** 7ce2188

## Checkpoint: Task 3 (Live Pipeline Run)

**Status:** PENDING — returned as checkpoint for human execution.

Task 3 requires a live API key (DEEPSEEK_API_KEY or MINIMAX_API_KEY per NEWS_PROVIDER) and live RSS network access. The plan instructs the executor to stop here and return a checkpoint signal.

**Key-absent fallback:** write empty-valid `data/incidents/current.json`:
```json
{"generated": "<ISO timestamp>", "window_days": 30, "incidents": []}
```
and record "live run pending keys" in 16-VERIFICATION.md so NEWS-04 build proceeds.

## Known Stubs

None. T1 and T2 are fully wired. Task 3 (live run) is gated on an API key; the empty-valid fallback is documented in the plan.

## Threat Flags

None. T-16-07 (hallucinated commune names → drop), T-16-08 (validation gate), and T-16-09 (key never printed, provider-aware) are all addressed in Tasks 1+2.

## Self-Check

- [x] pipeline/news/schema.py modified (slug field added)
- [x] pipeline/news/store.py modified (slug param added)
- [x] pipeline/scrape_news.py modified (resolve_cut wired, commune_cut removed)
- [x] test files modified and passing
- [x] Commit 7ce2188 exists
- [x] Commit a484224 exists

## Self-Check: PASSED
