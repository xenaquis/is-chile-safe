---
phase: 36-classification-fidelity-attribution
plan: 07
subsystem: news-pipeline
tags: [ingest, google-news, FID-04, G-31, G-37, G-43, G-44, R-03, R-14]
requires:
  - phase: 36-01
    provides: "store.build_incident(via_url=...) with scheme validation; schema via_url"
  - phase: 36-04
    provides: "live OK path with the per-row R-14 guard (url_rejected / invalid_record)"
  - phase: 36-05
    provides: "cross-run dedup identity on url/via_url"
provides:
  - "pipeline/news/ingest_url.py: resolve_publisher_url(gn_url, session, timeout=10) + DecodeBudget (60 items / 180 s / 1.5 s)"
  - "scrape_news: fresh Google-News items get url = publisher URL, via_url = Google link, id = sha256(publisher)[:16]; seen/pending keyed on both"
  - "run summary key gnews_decode = {candidates, decoded, failed, skipped_budget} (input to 36-09 FID-04(a))"
  - "36-GNEWS-DECODE.md: success_rate 50/50 (residential), live_decode_floor 0.70"
affects: [36-08, 36-09, 36-10, 36-11]
tech-stack:
  added: []
  patterns:
    - "network decode placed strictly after the keyword prefilter and the seen/pending check; queued items bypass it"
    - "optional keys (via_url) are added only when set, never defaulted to \"\" (R-14)"
key-files:
  created:
    - pipeline/news/ingest_url.py
    - pipeline/tests/test_ingest_url.py
    - pipeline/experiments/measure_gnews_decode.py
    - .planning/phases/36-classification-fidelity-attribution/36-GNEWS-DECODE.md
  modified:
    - pipeline/scrape_news.py
    - pipeline/news/pending.py
    - pipeline/tests/test_scrape_news.py
    - pipeline/tests/test_pending_queue.py
decisions:
  - "Residential decode rate 50/50 (all new-format, 0 old-format tokens); live_decode_floor = min(0.70, 1.00-0.20) = 0.70 per G-37/G-44."
  - "A successful decode whose publisher URL is already seen or pending still counts as decoded (it is a decode success for the 36-09 rate); it is skipped without classification and its Google link is marked seen."
  - "Decode budget counts only wait+decode time (not feed fetches between decodes); max_items 0 via NEWS_MAX_DECODE disables decoding (all skipped_budget)."
metrics:
  duration: "~45 min"
  completed: 2026-09-25
  tasks: 2
  files: 8
---

# Phase 36 Plan 07: Google-News publisher URL at ingest (FID-04) Summary

Fresh Google-News items are now decoded once, at ingest, to the publisher URL. The Google link is kept as `via_url`, `seen.json` and `pending.json` are keyed on both URLs, and the run summary reports the per-run `gnews_decode` counters. The measured residential decode rate (50/50) sets the G-37 live floor at 0.70.

## Task 1: decode-rate measurement

`pipeline/experiments/measure_gnews_decode.py` is read-only. It samples 50 of the 435 news.google.com URLs in current.json with `random.Random(3607)`. For each URL it tries `_try_old_format` first, then `decode_gnews_url` with a `requests.Session` (User-Agent `fulltext.USER_AGENT`, timeout 10 s), sleeping 1.5 s between URLs.

- **Result:** old_format 0, new_format 50, failed 0, so `success_rate: 50/50`.
- **Wall time:** 79.8 s.
- **Floor:** `live_decode_floor: 0.70`.
- **t.co:** 2/50 decoded to `t.co` shortener links. These are valid http(s) URLs and are recorded as an observation, not a gate.
- **Side effects:** data/ unchanged; no LLM calls.

## Task 2: ingest wiring

**`ingest_url.resolve_publisher_url`**
- Accepts the decoder output only if `store.is_safe_url` passes and the host is not news.google.com.
- Strips `utm_*` via `dedup._canonical_url`.
- Never raises.
- Looks up `gnews_decoder.decode_gnews_url` at call time, so the hardcoded batchexecute host (T-gf7-04) is preserved.

**`DecodeBudget`**
- Enforces at most 60 decodes and 180 s of decode time per run.
- Sleeps `REQUEST_DELAY` between decodes, never before the first.
- The clock and sleep are injectable.

**`scrape_news` feed loop**
- The decode runs only for news.google.com hosts, and only AFTER the keyword prefilter and the seen/pending check on the Google link.
- On success: `via_url` = G and `url` = P.
- If P is already in seen or pending, the item is skipped and `seen[G]` is recorded.
- On failure, or when the budget is exhausted, `url` stays G and no `via_url` is set.

**Seen and pending keys**
- `_answered` also marks `via_url` seen.
- The pending `via_url`s join `pending_urls`.
- Queued candidates normalize `via_url = p.get("via_url") or None` outside the `or ""` comprehension (R-14).
- `build_incident(via_url=item.get("via_url"))`.

**`pending.upsert_failure`** copies `via_url` only when it is present, so old queues stay byte-identical.

**Summary:** gains `gnews_decode`. The key pin carries the comment "FID-04 36-07". As a dict, it is excluded from GITHUB_OUTPUT.

**Negative controls**, both run and both reverted:
- Moving the decode above the seen check failed 5 tests, including `test_fid04_no_decode_for_keyword_failing_or_seen_google_entries`.
- Dropping `seen[item["via_url"]]` failed the both-keys tests (`..._stores_publisher_url_and_via_url` and `..._api_error_queues_publisher_url_and_never_redecodes`).

**pytest:** full suite 827 passed / 1 skipped / 2 xfailed, rc=0 (baseline 796/1/2, +31 new). The targeted verify set gives 143 passed, and `test_news_health_gate` passes unedited.

## Commits

| Task | Commit | Message |
|---|---|---|
| 1 | df4f52a | docs(36-07): measure Google-News decode rate (50/50) and fix live_decode_floor 0.70 |
| 2 (RED) | 4d2e688 | test(36-07): add failing tests for Google-News publisher URL ingest (FID-04) |
| 2 (GREEN) | d417ef3 | feat(36-07): store publisher URL for Google-News items, via_url kept, seen/pending on both keys (FID-04) |

## Deviations from Plan

**1. [Rule 2 - Missing critical] `_expire` also marks `via_url` seen**
- **Found during:** Task 2
- **Issue:** An expired queued item carrying `via_url` marked only P as seen. The feed could then re-offer G, which would be decoded again only to be skipped.
- **Fix:** Apply the same both-keys rule as `_answered` (the FID-04 "seen keys on both" truth).
- **Files:** pipeline/scrape_news.py
- **Commit:** d417ef3

**2. [Rule 3 - Blocking] The test autouse fixture stubs the decoder offline**
- **Found during:** Task 2
- **Issue:** Once wired, the existing Google-entry tests in test_scrape_news.py would have made real news.google.com requests.
- **Fix:** The `_no_live_llm` autouse fixture now patches `gnews_decoder.decode_gnews_url` to return None (decode failure). FID-04 tests override it per test. The existing test assertions are unchanged.
- **Files:** pipeline/tests/test_scrape_news.py
- **Commit:** 4d2e688

**3. [Rule 1 - Bug, own change] Line endings**
- **Found during:** Task 2
- **Issue:** The scripted edits flipped scrape_news.py and pending.py to CRLF, and the appended test block was LF inside a CRLF file.
- **Fix:** scrape_news.py and pending.py were restored to LF, and test_scrape_news.py to all-CRLF, before the feat commit. The committed RED version of test_scrape_news.py has mixed endings, which the feat commit normalizes.
- **Commit:** d417ef3

**Note on User-Agent.** Per the plan, the session header is `feeds.USER_AGENT`. However, `gnews_decoder` sets `User-Agent = fulltext.USER_AGENT` on every request it makes, so the header actually sent is the fulltext one, the same as G-43 and Task 1. There is no behavioral difference.

## Threat Flags

None beyond the plan's register:
- T-36-18: only the Google link and the hardcoded batchexecute host are contacted.
- T-36-19: `is_safe_url` plus the host check.
- T-36-20: 60 / 180 s / 1.5 s / 10 s limits.
- T-36-21: seen and pending keyed on both URLs; queued items are never re-decoded.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: pipeline/news/ingest_url.py, pipeline/tests/test_ingest_url.py, pipeline/experiments/measure_gnews_decode.py, 36-GNEWS-DECODE.md
- FOUND commits: df4f52a, 4d2e688, d417ef3
