---
phase: quick-260726-gf7
plan: "01"
subsystem: pipeline
tags: [gnews-decoder, ssrf-guard, rejected-corpus, r2-archive, kind-ledger]
dependency_graph:
  requires: [quick-260726-ep0]
  provides: [gnews-decode, rejected-capture, kind-aware-archive]
  affects: [pipeline/news/fulltext.py, pipeline/archive_r2.py, pipeline/scrape_news.py]
tech_stack:
  added: []
  patterns: [base64url-decode, batchexecute-gnews, ssrf-allowlist, streamed-5mb-cap, kind-ledger-v2]
key_files:
  created:
    - pipeline/news/gnews_decoder.py
    - pipeline/tests/test_gnews_decoder.py
    - pipeline/tests/test_rejected_capture.py
  modified:
    - pipeline/news/fulltext.py
    - pipeline/scrape_news.py
    - pipeline/archive_r2.py
    - pipeline/tests/test_archive_r2.py
decisions:
  - batchexecute POST host hardcoded to news.google.com/_/DotsSplashUi/data/batchexecute (T-gf7-04 SSRF prevention)
  - is_safe_url rejects based on literal IP parsing only — no DNS resolution
  - Legacy ledger rows without 'kind' default to 'incident' on merge (T-gf7-06 backward compat)
  - SCHEMA_VERSION bumped to 2; totals split by kind {incidents, rejected}
  - Incidents consume the fetch cap first; rejected get the remainder (priority ordering)
  - monkeypatch targets ar.fetch_article (imported name) not ft.fetch_article for test isolation
metrics:
  duration: "~25 minutes"
  completed: "2026-07-26"
  tasks: 3
  files: 7
---

# Phase quick-260726-gf7 Plan 01: Google News URL Decoder + Archive Rejected Summary

**One-liner:** Google News RSS URLs decoded offline (base64) + batchexecute fallback; fulltext hardened with SSRF/5MB/content-type guards; rejected candidates persisted monthly; R2 archive upgraded to schema v2 with per-kind totals and rejected.jsonl.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Google News URL decoder + fulltext security guards | 57069e8 | pipeline/news/gnews_decoder.py, pipeline/news/fulltext.py, pipeline/tests/test_gnews_decoder.py |
| 2 | Capture rejected candidates in scrape_news.py | 9f7e6b8 | pipeline/scrape_news.py, pipeline/tests/test_rejected_capture.py |
| 3 | Kind-aware R2 archive — consolidate + fetch + corpus-state v2 | ce0aeea | pipeline/archive_r2.py, pipeline/tests/test_archive_r2.py |

## What Was Built

### Task 1: gnews_decoder + fulltext hardening

`pipeline/news/gnews_decoder.py` — `decode_gnews_url(url, session, timeout)`:
- Fast path: non-gnews hosts return unchanged, zero network.
- Old-format: base64url decode of the `/articles/<token>` segment, regex for `https?://` URL. No network.
- New-format fallback: GET splash page → extract `data-n-a-sg`/`data-n-a-ts` → POST to hardcoded batchexecute endpoint → parse URL from JSON-ish response. Any exception → None.

`pipeline/news/fulltext.py` additions:
- `is_safe_url(url)`: rejects non-http(s) schemes, embedded credentials, private/loopback/link-local/reserved IP literals (no DNS resolution).
- `MAX_DOWNLOAD_BYTES = 5 MB`: streamed via `iter_content`, aborts over-limit as failure.
- `ALLOWED_CONTENT_TYPES = ("text/html", "text/plain")`: non-text (PDF, etc.) → failure.
- gnews decode wiring: if host is `news.google.com`, decode first; None → failure dict; decoded URL also guarded by `is_safe_url`.
- `decoded_from_gnews` bool threaded through result and article object.

### Task 2: record_rejected

`pipeline/scrape_news.py` — `record_rejected(items, data_dir)`:
- Writes `data_dir/rejected/YYYY-MM.json` with envelope `{generated, items}`.
- Deduplicates by `sha256(url)[:16]`; first_seen preserved on re-encounter.
- HTML-strips description, caps at 500 chars.
- Wired at all 3 reject points with stage labels: `classifier_none`, `commune_null`, `resolver_fail`, `centroid_fail`.
- Wrapped in `try/except` — never fails the news pipeline.

### Task 3: Kind-aware R2 archive

`pipeline/archive_r2.py`:
- `SCHEMA_VERSION = 2`
- `consolidate_rejected(data_dir)`: globs `rejected/*.json`, dedups by id, attaches APA.
- `merge_ledger(..., kind="incident"|"rejected")`: sets `row["kind"]` on new rows; legacy rows without kind get `kind="incident"` (T-gf7-06); fetched rows remain immutable.
- `build_corpus_state(ledger, incidents, rejected)`: totals split `{incidents: {...}, rejected: {...}}` by kind; `rejected_by_stage` Counter over rejection stages.
- `main()`: loads both lists, tags `_kind` in-memory, fetches incidents-first then rejected within cap, uploads `rejected.jsonl` + kind-tagged article objects, two `merge_ledger` passes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed existing fetch_article tests for stream=True response**
- **Found during:** Task 1 verification
- **Issue:** Three existing tests in `test_archive_r2.py` used `.text` attribute on mock response; new code uses `iter_content` (streaming). Tests would fail.
- **Fix:** Updated mock responses with `headers={"Content-Type": "text/html"}`, `iter_content.return_value`, `encoding="utf-8"`. Changed test URL from `news.google.com/rss/x` (now triggers decoder path) to `outlet.cl/nota`.
- **Files modified:** pipeline/tests/test_archive_r2.py
- **Commit:** 57069e8

**2. [Rule 1 - Bug] urlparse returns hostname=None for unbracketed IPv6 (http://::1/x)**
- **Found during:** Task 1 test run
- **Issue:** `urlparse("http://::1/x").hostname` returns `None`; IP guard was skipped.
- **Fix:** Added: if `hostname is None` and `netloc` is non-empty → return False (treat as unsafe).
- **Files modified:** pipeline/news/fulltext.py
- **Commit:** 57069e8

**3. [Rule 1 - Bug] ar.fetch_article vs ft.fetch_article patch target**
- **Found during:** Task 3 test run
- **Issue:** Test patched `ft.fetch_article` but `archive_r2.py` imports `fetch_article` by name at module level, so the patch didn't intercept calls in `main()`.
- **Fix:** Changed test to `monkeypatch.setattr(ar, "fetch_article", ...)`.
- **Files modified:** pipeline/tests/test_archive_r2.py
- **Commit:** ce0aeea

## Test Coverage

| File | New Tests | Total After |
|------|-----------|-------------|
| test_gnews_decoder.py | 13 | 13 |
| test_rejected_capture.py | 8 (11 parametrized) | 11 |
| test_archive_r2.py | 7 updated/new | 29 |
| Full suite | +43 | 280 |

All 280 tests pass. Original 237 tests remain green.

## Threat Surface

All mitigations from the plan's threat register were applied:
- T-gf7-01 SSRF: `is_safe_url` guards both original + decoded URL
- T-gf7-02 DoS: 5 MB streamed cap via `iter_content`
- T-gf7-03 Content-Type: allowlist applied before body reads
- T-gf7-04 Spoofing: batchexecute host hardcoded, never derived from input
- T-gf7-05 Logging: `logger.debug` only in decoder; no response bodies logged
- T-gf7-06 Backward compat: legacy ledger rows gain `kind="incident"` on merge
- T-gf7-SC: No new pip packages — decoder is fully inline

## Known Stubs

None. All functionality wired end-to-end (modulo live network which is intentionally excluded from tests per constraints).

## Self-Check: PASSED

- pipeline/news/gnews_decoder.py: EXISTS, contains `def decode_gnews_url`
- pipeline/news/fulltext.py: EXISTS, contains `def is_safe_url`, `MAX_DOWNLOAD_BYTES`, `ALLOWED_CONTENT_TYPES`
- pipeline/scrape_news.py: EXISTS, contains `def record_rejected`
- pipeline/archive_r2.py: EXISTS, contains `SCHEMA_VERSION = 2`, `def consolidate_rejected`
- Commits 57069e8, 9f7e6b8, ce0aeea: PRESENT in git log
- Test suite: 280 passed, 0 failed
