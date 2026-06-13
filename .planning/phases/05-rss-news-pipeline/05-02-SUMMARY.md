---
phase: 05-rss-news-pipeline
plan: 02
subsystem: pipeline
tags: [python, feedparser, deepseek, openai, rss, keyword-filter, seen-ledger, centroids, pytest]

requires:
  - phase: 05-rss-news-pipeline
    plan: 01
    provides: "pipeline/news/schema.py (ClassifierOutput, VALID_CUTS, VALID_FAMILIES); data/incidents/centroids.json; test scaffolds"

provides:
  - "pipeline/news/feeds.py: feedparser RSS fetch + keyword pre-filter + seen-ledger + canonical URL resolution (NEWS-01)"
  - "pipeline/news/classifier.py: DeepSeek v4-flash JSON classifier + CUT/confidence rejection + empty-content retry (NEWS-02)"
  - "pipeline/news/centroids.py: lazy-load CUT -> (lat,lng) lookup, monkeypatchable for tests (D-08)"

affects:
  - 05-03-dedup (imports feeds.py fetch_feed, classifier.py classify, centroids.py get_centroid)
  - 05-04-store (imports classifier output IncidentRecord via schema.py)

tech-stack:
  added:
    - "feedparser==6.0.11 (already pinned in requirements.txt from 05-01)"
    - "openai==2.34.0 (already pinned in requirements.txt from 05-01)"
  patterns:
    - "per-feed try/except returns [] — one feed never blocks others (D-04)"
    - "CRIME_KEYWORDS frozenset matched on lowercased title+stripped-description (D-02)"
    - "seen-ledger at data/incidents/seen.json — committed, survives CI runs (Pitfall 7)"
    - "canonical_url() dispatches on feed_name: BioBioChile -> entry.link; others -> entry.id (Pitfall 2)"
    - "strip_html() via re.sub for BioBio description (Pitfall 8)"
    - "classifier uses model=deepseek-v4-flash only; never deepseek-chat/reasoner/v4-pro"
    - "response_format={'type':'json_object'}, temperature=0.0, max_tokens=512 (NEWS-02)"
    - "SYSTEM_PROMPT embeds 346 CUT codes comma-joined + 7 FAMILY_KEYS; word 'json' present (DeepSeek requirement)"
    - "classify() rejects commune_cut not in VALID_CUTS OR confidence < 0.6 (T-05-02-01, D-07)"
    - "centroids.py exposes _CENTROIDS/_CENTROID_PATH at module level for monkeypatching"

key-files:
  created:
    - pipeline/news/feeds.py
    - pipeline/news/classifier.py
    - pipeline/news/centroids.py

key-decisions:
  - "is_crime_item() takes a dict with 'title'/'description' keys (not feedparser entry object) — matches test_feeds.py fixture shape exactly"
  - "filter_seen() takes list[dict] + set[str] (not dict ledger) — matches test_seen_ledger_known_url_skipped assertion"
  - "classify() signature is classify(title, description) without cut_list arg — VALID_CUTS loaded at module import, CUT list embedded in SYSTEM_PROMPT at module level (not per-call)"
  - "Empty-content retry is manual (call _call_api twice) rather than tenacity — simpler for a one-retry pattern"
  - "CONFIDENCE_THRESHOLD = 0.6 (module constant, tune after D-16 audit)"

duration: 20min
completed: 2026-06-13
---

# Phase 05 Plan 02: RSS Feeds + Classifier + Centroids Summary

**feedparser RSS fetch with per-feed graceful fallback, CRIME_KEYWORDS pre-filter, seen-URL ledger, DeepSeek v4-flash closed-list JSON classifier with CUT/confidence anti-hallucination rejection, and deterministic centroid lookup**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-13T18:10:00Z
- **Completed:** 2026-06-13T18:30:00Z
- **Tasks:** 2 (Task 1 pre-approved; Tasks 2 and 3 executed)
- **Files modified:** 3

## Accomplishments

- feeds.py: fetches 3 confirmed feeds with per-feed try/except returning []; CRIME_KEYWORDS frozenset keyword filter; canonical URL dispatcher (BioBioChile -> entry.link, others -> entry.id); seen-ledger at data/incidents/seen.json with 60-day prune; strip_html() for BioBio description; parse_pub_date() using feedparser UTC-normalised published_parsed
- classifier.py: OpenAI client to DeepSeek API; SYSTEM_PROMPT embeds all 346 CUT codes + 7 FAMILY_KEYS; model=deepseek-v4-flash, temp=0.0, json_object mode; rejects commune_cut not in VALID_CUTS or confidence < 0.6; empty-content one-retry; Pydantic ClassifierOutput.model_validate() gate; key from os.environ only
- centroids.py: lazy-load singleton with _CENTROIDS/_CENTROID_PATH exposed for monkeypatching; returns (lat,lng) or None

## Task Commits

1. **Task 2: feeds.py — RSS fetch + keyword pre-filter + seen-ledger** - `3195935` (feat)
2. **Task 3: classifier.py + centroids.py** - `7bfc03d` (feat)

## Files Created/Modified

- `pipeline/news/feeds.py` - feedparser RSS fetch + keyword pre-filter + seen-ledger
- `pipeline/news/classifier.py` - DeepSeek v4-flash JSON classifier + rejection gates
- `pipeline/news/centroids.py` - CUT -> (lat,lng) lazy-load lookup

## Decisions Made

- is_crime_item() accepts dict (not feedparser entry object) to match test scaffold API exactly
- filter_seen() takes set[str] (URL set) rather than the full ledger dict to keep the API simple and match the test assertion
- classify() has no cut_list parameter — VALID_CUTS loaded at module import, embedded in SYSTEM_PROMPT once at module level (not per-call overhead)
- Manual one-retry on empty content rather than tenacity decorator — single retry is simpler and sufficient for the rare empty-response case

## Deviations from Plan

None — plan executed exactly as written. Task 1 was pre-approved per sequential_execution directive; Tasks 2 and 3 implemented against exact Wave-0 scaffold function signatures.

## Issues Encountered

None.

## Known Stubs

None — no data flows to UI from this plan. feeds.py/classifier.py/centroids.py are pipeline-internal modules; no rendering surface.

## Threat Flags

No new threat surfaces beyond those in the plan's threat_model. All three mitigations implemented:
- T-05-02-01: commune_cut rejected if not in VALID_CUTS; confidence < 0.6 rejected; temp=0.0
- T-05-02-02: DEEPSEEK_API_KEY from os.environ only; never logged or hardcoded
- T-05-02-03: per-feed try/except returns [] on any error
- T-05-02-04: json.loads in try/except + empty-content retry + ClassifierOutput.model_validate(); None on any failure

## Self-Check

- [x] `pipeline/news/feeds.py` exists — fetch_feed, is_crime_item, filter_seen, canonical_url, FEEDS
- [x] `pipeline/news/classifier.py` exists — classify(), client, model="deepseek-v4-flash", base_url deepseek, key from os.environ
- [x] `pipeline/news/centroids.py` exists — get_centroid(), _CENTROIDS, _CENTROID_PATH
- [x] classifier.py contains "deepseek-v4-flash" and NO occurrence of deepseek-chat/deepseek-reasoner/deepseek-v4-pro
- [x] pytest pipeline/tests/test_feeds.py: 5 passed
- [x] pytest pipeline/tests/test_classifier.py pipeline/tests/test_centroids.py: 10 passed
- [x] pytest pipeline/tests/test_feeds.py pipeline/tests/test_classifier.py pipeline/tests/test_centroids.py: 15 passed
- [x] Commits: 3195935, 7bfc03d

## Self-Check: PASSED
