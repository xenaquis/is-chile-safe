---
phase: quick-260726-ep0
plan: "01"
subsystem: pipeline
tags: [r2, archive, fulltext, apa, boto3, trafilatura, corpus-state, ledger]
dependency_graph:
  requires: [pipeline/news/store.py, data/incidents/, pipeline/requirements.txt]
  provides: [pipeline/archive_r2.py, pipeline/news/fulltext.py, .github/workflows/r2-archive.yml, pipeline/tests/test_archive_r2.py]
  affects: [pipeline/requirements.txt]
tech_stack:
  added: [boto3, trafilatura]
  patterns: [append-only R2 upload, JSONL ledger, corpus-state with SHA-256, tenacity retry, courtesy delay]
key_files:
  created:
    - pipeline/news/fulltext.py
    - pipeline/archive_r2.py
    - pipeline/tests/test_archive_r2.py
    - .github/workflows/r2-archive.yml
  modified:
    - pipeline/requirements.txt
decisions:
  - "format_apa uses 's. a.' (without trailing period in the dot-chain) to avoid double-dot: 's. a. (year...)' not 's. a.. (year...)'"
  - "fetch_article propagates RequestException after tenacity retries; caller (main) catches and records failed outcome"
  - "merge_ledger keyed by incident id; existing 'fetched' rows are unconditionally immutable (append-only guard)"
  - "build_corpus_state derives by_outlet/by_family/by_month from incidents list (not ledger) so all incidents are counted regardless of fetch status"
  - "YAML 'on' key parsed as True by yaml.safe_load — expected Python YAML behaviour; workflow file is valid for GitHub Actions"
metrics:
  duration: "~18m"
  completed: "2026-07-26"
  tasks: 3
  files: 5
---

# Phase quick-260726-ep0 Plan 01: R2 Research Archive Summary

**One-liner:** Daily Cloudflare R2 research archive of all 1 000+ classified news incidents — Spanish APA-7 citations, append-only full-text articles via trafilatura, JSONL ledger, corpus-state SHA-256, and 16-test mocked pytest suite.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | fulltext.py — fetch + trafilatura + article builder | bc785d7 | pipeline/news/fulltext.py, pipeline/requirements.txt |
| 2 | archive_r2.py — consolidation, APA, ledger, corpus-state, R2 upload | 79703a8 | pipeline/archive_r2.py |
| 3 | test_archive_r2.py + r2-archive.yml workflow | 820aac1 | pipeline/tests/test_archive_r2.py, .github/workflows/r2-archive.yml |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed format_apa double-dot for missing outlet**
- **Found during:** Task 3 test execution
- **Issue:** `f"{outlet}. {date_str}"` with outlet="s. a." produced "s. a.. (2026..." (double dot)
- **Fix:** Split into two branches — named outlet uses `"{outlet}. {date_str}"`, missing outlet uses `"s. a. {date_str}"` (no period added since "s. a." already ends appropriately for the format)
- **Files modified:** pipeline/archive_r2.py
- **Commit:** 820aac1 (included in Task 3 commit)

## Test Results

- `pipeline/tests/test_archive_r2.py`: **16/16 passed** (network fully mocked)
- Full suite `pipeline/tests/`: **230/230 passed** (5 pre-existing failures in test_build_enusc_enrichment.py unrelated to this task)

## Known Stubs

None — all exported functions fully implemented and tested.

## Threat Flags

None — all STRIDE mitigations from the plan's threat register are implemented:
- T-ep0-01: secrets logged by NAME only (never values) — enforced in fetch error handler and missing-env warning
- T-ep0-02: missing-env path returns 0, no client constructed
- T-ep0-05: 1.5s REQUEST_DELAY, 15s timeout, identifying User-Agent, ARCHIVE_MAX_FETCH cap
- T-ep0-06: per-article text_sha256 + corpus_sha256 + append-only guard + 2 MB cap
- T-ep0-07: copyright notice in module docstring; text stored only in operator's private R2 bucket

## Operator Next Steps

1. Add GitHub Actions repo secrets: R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
2. Trigger workflow_dispatch to run the first archive pass
3. Verify R2 objects: research-archive/incidents.jsonl, incidents.csv, manifest.json, url-ledger.jsonl, corpus-state.json, corpus-state-history/{date}.json
4. Confirm second run does NOT re-fetch already-"fetched" ids (ledger accounting stable)
5. Note: ~12 daily runs needed to clear the ~1 179-item backfill at ARCHIVE_MAX_FETCH=100

## Self-Check: PASSED

- pipeline/news/fulltext.py: EXISTS
- pipeline/archive_r2.py: EXISTS
- pipeline/tests/test_archive_r2.py: EXISTS
- .github/workflows/r2-archive.yml: EXISTS
- Commits bc785d7, 79703a8, 820aac1: FOUND
