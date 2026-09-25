---
phase: 36-classification-fidelity-attribution
plan: 01
subsystem: news-pipeline
tags: [schema, store, feeds, FID-01, FID-04, FID-06, G-28]
requires: []
provides:
  - "IncidentRecord.title_src / via_url (optional, validated)"
  - "store.build_incident(..., title_src=None, title_es=None, via_url=None)"
  - "feeds.source_headline(title, outlet)"
  - "feeds.strip_html entity decoding (single choke point)"
  - "fetch_feed: NonXMLContentType bozo at DEBUG when entries parsed"
affects: [36-03, 36-04, 36-05, 36-07]
tech-stack:
  added: []
  patterns: ["optional back-compat schema fields (like slug)", "legacy-shape-preserving keyword-only builder"]
key-files:
  created: []
  modified:
    - pipeline/news/schema.py
    - pipeline/news/store.py
    - pipeline/news/feeds.py
    - pipeline/tests/test_schema_incidents.py
    - pipeline/tests/test_store.py
    - pipeline/tests/test_feeds.py
decisions:
  - "build_incident emits via_url whenever it is not None, on both the title_src and legacy title_es paths; with via_url=None the legacy dict is byte-identical"
  - "The title-required check (ValueError) runs before the url scheme check, so a missing title always raises even with a bad url"
  - "source_headline returns the whitespace-collapsed title when stripping the suffix would leave nothing (' - La Tercera' -> '- La Tercera')"
metrics:
  duration: "~25 min"
  completed: 2026-09-25
  tasks: 2
  files: 6
---

# Phase 36 Plan 01: title_src/via_url contract and ingest helpers Summary

This plan adds the Phase-36 data contract. IncidentRecord and build_incident gain optional `title_src` (the outlet's verbatim headline, FID-01/G-28) and `via_url` (the Google News link, FID-04). Rows with `title_src` get `title_es` copied from it. Legacy callers get a byte-identical dict. In feeds.py, `source_headline()` derives the headline for any feed (decode entities, collapse whitespace, strip one trailing " - outlet"). `strip_html` now decodes HTML entities after removing tags. BioBio's NonXMLContentType bozo is logged at DEBUG only when entries were parsed.

## Tasks

| Task | Name | Commits | Files |
| ---- | ---- | ------- | ----- |
| 1 | IncidentRecord title_src/via_url + build_incident compat signature | f826367 (RED), f5957b6 (GREEN) | schema.py, store.py, test_schema_incidents.py, test_store.py |
| 2 | feeds.py source_headline, entity-decoding strip_html, quiet NonXMLContentType | 9803528 (RED), 6a8f572 (test fix), a2db7dc (GREEN) | feeds.py, test_feeds.py |

## Verification

- Step 0 precondition: `grep -c '^- \[x\] \*\*Phase 35' .planning/ROADMAP.md` printed 1.
- Task 1 verify: test_schema_incidents + test_store + test_scrape_news + test_backfill_classifier_outage gave 128 passed, exit 0. `current.json validates` was printed.
- Task 1 negative control: with `title_src: str` (required), validating current.json fails with `Field required`. Reverted.
- Task 2 step 0: `feedparser.NonXMLContentType` is `<class 'feedparser.exceptions.NonXMLContentType'>` (feedparser 6.0.14). The top-level attribute exists, so feeds.py imports `from feedparser import NonXMLContentType`.
- Task 2 verify: test_feeds + test_scrape_news gave 56 passed. Full `pytest pipeline` gave **675 passed, 1 skipped, 2 xfailed, rc=0**. That is baseline 642/1/2 plus 33 new tests (12 schema, 7 store, 14 feeds).
- Task 2 negative control: with strip_html reverted to tags-only, `test_strip_html_decodes_entities_and_nbsp` and `test_strip_html_unescape_runs_after_tag_removal` FAIL. Restored.
- `git diff --stat c6d5b45 HEAD` shows only the 6 listed files. `git status --porcelain data/` is empty. test_store.py keeps its CRLF endings and the other files keep LF.
- Existing-test edits: only the key-set assertion in `test_incidents_file_valid_round_trip` gained `"title_src", "via_url"` with the comment `FID-01/FID-04 36-01` (gate R1 BF-05). No serialization tricks were used.
- test_scrape_news.py and test_backfill_classifier_outage.py are unedited and green, so the legacy `title_es=` callers are unaffected.

## Deviations from Plan

**1. [Rule 1 - Bug] Test file escapes mangled by shell heredoc**
- **Found during:** Task 2 RED
- **Issue:** Writing the tests through a bash heredoc turned `\n` into a real newline (a syntax error in one parametrize case) and `\xa0` into a literal NBSP character, in both test_feeds.py and feeds.py. As a result, RED commit 9803528 failed on a SyntaxError during collection, not on the intended ImportError of `source_headline`.
- **Fix:** Restored the `\n` and `"\xa0"` escapes. The test fix is its own commit (6a8f572), and the feeds.py NBSP was normalized before GREEN (a2db7dc). The strip_html negative control confirms the tests really exercise the new behaviour.
- **Files modified:** pipeline/tests/test_feeds.py, pipeline/news/feeds.py

No other deviations. No caller changed, ClassifierOutput was not touched (36-06 owns it) and no dependency was added.

## TDD Gate Compliance

Both tasks have a `test(...)` RED commit followed by a `feat(...)` GREEN commit (f826367 -> f5957b6; 9803528 -> a2db7dc). The Task 2 RED commit was red for the wrong reason (SyntaxError), as described above.

## Threat Model

- T-36-01: title_src is stored as plain text. strip_html unescapes after removing tags, so `&lt;b&gt;x` becomes the literal `<b>x` (tested). Render-side escaping stays the job of 36-03.
- T-36-02: via_url is restricted to http/https in the schema validator and in build_incident (returns None and logs a warning; tested).
- T-36-03: both fields are optional, and the real current.json validates (a permanent test was added).
- No new threat surface.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: pipeline/news/schema.py, pipeline/news/store.py, pipeline/news/feeds.py and the 3 test files
- FOUND commits: f826367, f5957b6, 9803528, 6a8f572, a2db7dc
