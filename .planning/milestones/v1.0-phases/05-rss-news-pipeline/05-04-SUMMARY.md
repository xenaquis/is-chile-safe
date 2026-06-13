---
phase: 05-rss-news-pipeline
plan: "04"
subsystem: pipeline/news
tags: [python, orchestrator, pipeline, integration-test, uat-pending]
requires: ["05-01", "05-02", "05-03"]
provides: ["pipeline/scrape_news.py", "pipeline/tests/test_scrape_news.py"]
affects: ["data/incidents/current.json", "data/incidents/seen.json"]
tech_stack:
  added: []
  patterns:
    - "scrape_cead.py orchestrator pattern: main()->int, sys.exit guard, logging.basicConfig, env override, per-unit try/except"
    - "monkeypatch + side_effect integration testing with mocked DeepSeek"
key_files:
  created:
    - pipeline/scrape_news.py
    - pipeline/tests/test_scrape_news.py
  modified:
    - pipeline/news/store.py
decisions:
  - "Added build_incident() to store.py (was referenced in plan interfaces but absent from Wave-1 implementation)"
  - "Within-run URL deduplication added to orchestrator (seen_set tracks current-run URLs to prevent same-URL double-classification before seen-ledger is persisted)"
metrics:
  duration: "~25min"
  completed: "2026-06-13"
  tasks_completed: 1
  tasks_total: 2
  files_changed: 3
---

# Phase 05 Plan 04: Orchestrator + Integration Test Summary

**One-liner:** RSS news pipeline orchestrator wiring fetch→keyword-filter→seen-ledger→classify→centroid→dedup→merge_and_write with D-17 cost cap, graceful no-key path, and 6 mocked-DeepSeek integration tests (IncidentsFile.model_validate + TS field names confirmed).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | scrape_news.py orchestrator + integration test | 2e38622 | pipeline/scrape_news.py, pipeline/tests/test_scrape_news.py, pipeline/news/store.py |

## Task 2 Status: PENDING HUMAN UAT (D-16)

**Status:** Deferred to human — no DEEPSEEK_API_KEY available in this autonomous run.

**What was verified (smoke only):**
- `pipeline/scripts/audit_incidents.py` exists and exits cleanly (code 1, clear message) when `data/incidents/current.json` is absent — no crash, no traceback.

**What requires human action (Phase 6 / manual run):**
1. Set `DEEPSEEK_API_KEY` in `pipeline/.env`
2. Run `python pipeline/scrape_news.py` — confirm log shows fetched/classified/written counts
3. Confirm `data/incidents/current.json` exists and validates
4. Run `python pipeline/scripts/audit_incidents.py` — review 50 sampled incidents
5. For each: open source URL, confirm assigned commune matches article location
6. If hallucinations found: adjust `CONFIDENCE_THRESHOLD` (currently 0.6) in `pipeline/news/classifier.py` and re-run
7. Signal "approved" when 0 commune hallucinations found

**Gate:** D-16 blocks production-ready declaration per plan Task 2.

## Deviations from Plan

### Auto-added Missing Critical Functionality

**1. [Rule 2 - Missing API] Added `build_incident()` to `pipeline/news/store.py`**
- **Found during:** Task 1 implementation
- **Issue:** Plan interfaces section listed `build_incident(...)` as a store.py function, but it was absent from the Wave-1 implementation. The orchestrator imports it.
- **Fix:** Added `build_incident(**kwargs) -> dict` with keyword-only args for all IncidentRecord fields.
- **Files modified:** pipeline/news/store.py
- **Commit:** 2e38622

**2. [Rule 1 - Bug] Within-run URL deduplication in orchestrator**
- **Found during:** Integration test (StopIteration on mock side_effect exhaustion)
- **Issue:** Two entries with the same URL from the same feed both passed the seen-ledger check (ledger only contains prior-run URLs), causing double-classification and mock exhaustion.
- **Fix:** Added `seen_set.add(url)` immediately after the seen-set check so within-run duplicate URLs are skipped before reaching the classifier.
- **Files modified:** pipeline/scrape_news.py
- **Commit:** 2e38622

## Verification

**Automated:**
```
pytest pipeline/tests/ -q
135 passed, 12 warnings
```

**Audit smoke test:**
```
python pipeline/scripts/audit_incidents.py
→ Exit code 1: "ERROR: current.json not found — run scrape_news.py first."
No crash, no traceback.
```

## Threat Surface Scan

No new network endpoints, auth paths, or trust boundaries introduced beyond those in the plan's threat model (T-05-04-01 through T-05-04-04). The `build_incident()` helper is pure data transformation — no external I/O.

## Known Stubs

None — all pipeline fields are wired. The D-16 audit gate is a human verification step, not a code stub.

## Self-Check: PASSED

- pipeline/scrape_news.py: EXISTS
- pipeline/tests/test_scrape_news.py: EXISTS
- pipeline/news/store.py (build_incident): EXISTS
- Commit 2e38622: EXISTS
- pytest 135 passed: CONFIRMED
