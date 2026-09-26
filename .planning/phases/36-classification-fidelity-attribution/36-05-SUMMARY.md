---
phase: 36-classification-fidelity-attribution
plan: 05
subsystem: news-pipeline
tags: [dedup, cross-run, FID-05, FID-04, G-30, R-04, BF-06, validator-19]
requires:
  - phase: 36-01
    provides: "store.build_incident / merge_and_write baseline"
  - phase: 36-04
    provides: "title_src == title_es for new rows (the rule's title field)"
provides:
  - "pipeline/news/dedup.py: prune_near_duplicates(items) -> (kept, [(item, kept_id, reason)]), filter_new_against(existing, new); url|via_url one identity"
  - "pipeline/news/store.py: PRUNE_EXISTING = True; cross-run dedup after _merge_by_id in merge_and_write; archive: aged near-dups not added, existing archive rows never pruned"
  - "pipeline/validate_news_dedup.py: drops=N, exit 0/1/2, --list, --only-new-since IDS_FILE (forward-only, R-04)"
  - "site/scripts/validate/news-dedup.mjs: validator #19 wrapper (NOT registered in all.mjs; 36-09 registers)"
  - "36-DEDUP-REVIEW.md: 58-pair fresh-opus review, 0 false merges, PRUNE_EXISTING=True"
affects: [36-09, 36-10, 36-11]
tech-stack:
  added: []
  patterns:
    - "single rule source: validator and store both call dedup.prune_near_duplicates; no JS re-implementation"
    - "seeded two-phase filter (url keys, then (cut,date) title buckets) shared by prune and forward-only filter"
key-files:
  created:
    - pipeline/validate_news_dedup.py
    - pipeline/tests/test_validate_news_dedup.py
    - site/scripts/validate/news-dedup.mjs
    - .planning/phases/36-classification-fidelity-attribution/36-DEDUP-REVIEW.md
  modified:
    - pipeline/news/dedup.py
    - pipeline/tests/test_dedup.py
    - pipeline/news/store.py
    - pipeline/tests/test_store.py
decisions:
  - "PRUNE_EXISTING = True ships (G-30): fresh-opus review of 58 pairs = 57 SAME_EVENT, 0 DIFFERENT_EVENT, 1 UNSURE; 514872e1d06db7f2 not in the list."
  - "Pair 3 (UNSURE, Antofagasta carabinero attempted homicide, second imputado vs imputado + weapons) is the same single crime at different procedural steps, so it is not a false merge under the v2.1 'different events' standard."
  - "Title-match ratio in the drop reason is the first kept bucket title reaching >= 0.82 (same 'any' semantics as the old deduplicate)."
  - "deduplicate() now also collapses url/via_url aliases (FID-04); otherwise identical and all pre-existing test_dedup tests pass unedited."
  - "news-dedup.mjs skips a Windows Store python3 stub (exit 9009) before falling back to python."
metrics:
  duration: "~50 min (plus external review)"
  completed: 2026-09-26
  tasks: 3
  files: 8
---

# Phase 36 Plan 05: Cross-run deterministic dedup + validator #19 Summary

The existing 0.82 (cut, date) title rule, now with url|via_url identity, runs across runs inside `merge_and_write`. It prunes existing near-duplicate cards (first-seen wins) and keeps new near-duplicates out. A stdlib-only validator reports the drops over current.json. The one-time existing-row prune is backed by a 0-false-merge fresh-opus review.

## Tasks

| Task | Commits | Result |
|---|---|---|
| 1 dedup APIs + store cross-run dedup (TDD) | 999a7c9 (RED), b33aa00 (GREEN) | 119 passed across test_dedup/test_store/test_backfill_classifier_outage/test_scrape_news. Negative control (prune skipped) fails the [A,B]->[A] and no-op tests; reverted. |
| 2 validate_news_dedup.py + news-dedup.mjs (TDD) | e581b3e (RED), ed0cbfd (GREEN) | 11 passed (incl. stdlib-only import pin and node wrapper exit parity). Not in all.mjs. |
| 3 drop-list review -> PRUNE_EXISTING | f7e2eee | 58 pairs, 0 false merges, 514872e1d06db7f2 absent -> True kept. |

## Measurements

- Pre-ship drop count over data/incidents/current.json: **drops=58 over 787 incidents** (validator exit 1). The 2026-09-24 baseline was 64/798. All 58 are title matches; 9 DROP rows are dated >= 2026-09-23.
- **Expected post-ship first-run for 36-09:** the first live merge_and_write drops the existing pairs (about 58, fewer if rows age out first, a few more if new cron pairs form). After that run, `validate_news_dedup.py` over current.json must report drops=0.
- Full `pytest pipeline`: 788 passed, 1 skipped, 2 xfailed, rc=0.

## FRESH-04 / BF-06

- No `test_fresh04_*` assert changed. The only existing fixture change is the bump002 `title_es` in `test_fresh04_new_incident_rewrites_and_bumps` (comment `FID-05 36-05: cross-run dedup`).
- New test `test_fid05_cross_run_near_duplicate_is_noop`: the call returns 0, last_new_incident_at is not bumped, and current.json stays byte-identical.
- The no-op guard, threshold, normalization and prune order are unchanged.

## Deviations from Plan

**1. [Rule 2 - Robustness] Windows Store python3 stub in news-dedup.mjs**
- **Issue:** On Windows, `python3` can be an App Execution Alias stub that exits 9009 instead of raising ENOENT, which would mask the `python` fallback.
- **Fix:** On win32, a 9009 exit is treated like ENOENT.
- **Commit:** ed0cbfd

Otherwise the plan was executed as written, including Revisions R1 and R2.

## Notes for downstream

- Pair 9 (informational): both cards sit at 13101 Santiago, but the story is a rapper shot in Temuco. This is a geolocation defect for Phase-36 family/commune accuracy notes, not a dedup issue.
- 36-09 registers #19 in all.mjs after a post-ship live run at 0 drops. The `--only-new-since` forward-only mode stays available (R-04), although it is not needed because PRUNE_EXISTING=True.

## Known Stubs

None.

## Self-Check: PASSED

- Files present: pipeline/validate_news_dedup.py, pipeline/tests/test_validate_news_dedup.py, site/scripts/validate/news-dedup.mjs, 36-DEDUP-REVIEW.md.
- Commits present: 999a7c9, b33aa00, e581b3e, ed0cbfd, f7e2eee.
