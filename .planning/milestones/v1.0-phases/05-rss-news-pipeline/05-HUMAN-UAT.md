---
status: partial
phase: 05-rss-news-pipeline
source: [05-VERIFICATION.md]
started: 2026-06-13T00:00:00.000Z
updated: 2026-06-13T00:00:00.000Z
---

## Current Test

[awaiting human testing — requires a live DEEPSEEK_API_KEY]

## Tests

### 1. Live pipeline run
expected: With a real `DEEPSEEK_API_KEY` set (pipeline/.env or repo secret), `python pipeline/scrape_news.py` ingests the 3 live feeds, classifies crime items, and writes a valid `data/incidents/current.json` (≥1 incident; a down feed is skipped + logged without crashing the run).
result: [pending]

### 2. D-16 — 50-incident commune-hallucination audit (NEWS-02 success criterion #5)
expected: After a live run, `python pipeline/scripts/audit_incidents.py` dumps 50 random incidents (title, outlet, source URL, assigned commune); human review confirms no commune-hallucination errors before the pipeline is declared production-ready. Tune `confidence` (0.6) / dedup (0.82) thresholds if false accept/reject observed.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps

(none — both items are deferred-by-design; they need a live API key + network, configured in Phase 6 deployment. All code + unit tests (135 passed, DeepSeek mocked) are complete and verified.)
