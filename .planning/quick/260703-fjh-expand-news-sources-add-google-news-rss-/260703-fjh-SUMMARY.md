---
phase: quick-260703-fjh
plan: "01"
subsystem: pipeline/news
tags: [news, feeds, google-news, rss, dedup, attribution]
dependency_graph:
  requires: []
  provides: [google_news_url, resolve_outlet, GoogleNews-* FEEDS, LaCuarta FEED]
  affects: [pipeline/news/feeds.py, pipeline/scrape_news.py]
tech_stack:
  added: []
  patterns: [Google News RSS via standard feedparser, <source> tag outlet attribution]
key_files:
  created:
    - pipeline/tests/fixtures/feed_googlenews_sample.xml
  modified:
    - pipeline/news/feeds.py
    - pipeline/scrape_news.py
    - pipeline/tests/test_feeds.py
    - pipeline/tests/test_dedup.py
decisions:
  - "Store Google News redirect URL as incident.url rather than resolving it (avoids SSRF surface, user click lands on source)"
  - "resolve_outlet uses feedparser's entry.source dict-or-attr detection for compatibility"
  - "Regional queries use when:3d window (vs when:2d national) to compensate for lower volume in target regions"
metrics:
  duration: "~15 min"
  completed: "2026-07-03"
  tasks_completed: 2
  files_changed: 5
---

# Phase quick-260703-fjh Plan 01: Expand News Sources — Google News RSS + La Cuarta

**One-liner:** Added Google News RSS queries (1 national + 4 regional) and La Cuarta feed with `<source>`-tag outlet attribution and redirect-URL storage, without changing the incident data contract or dedup logic.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Register Google News + La Cuarta feeds; add `resolve_outlet()` and `google_news_url()`; wire into scrape_news.py | 058013d |
| 2 | Google News RSS fixture + 6 new test_feeds tests + cross-outlet dedup test | 835e636 |

## What Was Built

### pipeline/news/feeds.py

- `google_news_url(query)` — builds percent-encoded `https://news.google.com/rss/search?q=...&hl=es-419&gl=CL&ceid=CL:es-419` URL
- `_GOOGLE_NEWS_QUERIES` — 5 regional/national query strings (when:2d national, when:3d for Antofagasta/Tarapacá/Coquimbo/Araucanía)
- FEEDS extended: +LaCuarta (Arc platform, same shape as LaTercera) +5 GoogleNews-* keys
- `canonical_url()` extended: `GoogleNews` prefix → returns `entry.link` (redirect URL)
- `resolve_outlet(entry, feed_name)` — non-Google feeds pass through feed name; Google News feeds extract `<source>` tag title, fallback to `"Google News"`

### pipeline/scrape_news.py

- Import `resolve_outlet`; outlet field changed from `feed_name` to `resolve_outlet(entry, feed_name)`

### Tests

- `pipeline/tests/fixtures/feed_googlenews_sample.xml` — valid RSS 2.0 with 3 items: 2 with `<source>` tags (Puranoticia, ADPrensa) + 1 without source (fallback test)
- 6 new tests in `test_feeds.py` covering outlet extraction, fallback, canonical URL, non-Google passthrough, URL format, and FEEDS registry shape
- 1 new test in `test_dedup.py` verifying 3 Google News outlets for same homicide (same cut+date) collapse to 1 pin while a distinct incident survives

## Test Results

- `pipeline/tests/test_feeds.py pipeline/tests/test_dedup.py`: **15 passed**
- Full regression `pipeline/tests -q`: **212 passed, 5 pre-existing failures** in `test_build_enusc_enrichment.py` (unrelated to this plan)

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced. Google News redirect URLs pass through existing `store.is_safe_url()` https check (T-fjh-03). No new packages added (T-fjh-SC).

## Self-Check: PASSED

- `pipeline/news/feeds.py` — modified, exports `google_news_url` and `resolve_outlet`
- `pipeline/scrape_news.py` — modified, uses `resolve_outlet`
- `pipeline/tests/fixtures/feed_googlenews_sample.xml` — created
- `pipeline/tests/test_feeds.py` — modified with 6 new tests
- `pipeline/tests/test_dedup.py` — modified with 1 new test
- Commits 058013d and 835e636 verified in git log
