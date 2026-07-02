---
phase: 25
plan: "03"
subsystem: frontend/pipeline
tags: [news, semantics, a11y, seo, classifier, tdd]
dependency_graph:
  requires: [25-01]
  provides: [semantic-news-page, traffic-accident-exclusion]
  affects: [site/src/pages/news.astro, pipeline/news/classifier.py]
tech_stack:
  added: []
  patterns: [astro-build-time-grouping, cut-string-coercion, tdd-red-green]
key_files:
  created:
    - pipeline/tests/test_classifier_traffic.py
  modified:
    - site/src/pages/news.astro
    - pipeline/news/classifier.py
decisions:
  - CUT in current.json incidents is stored as integer; index.json stores CUT as string — convert via String() in Map lookup
  - Month grouping done at build time via Map<YYYY-MM, incidents[]>; zero client JS
  - Slug-to-commune fallback lookup added for incidents with slug but no CUT
  - Traffic exclusion rule added to SYSTEM_PROMPT Rules block after the "not a crime" rule
metrics:
  duration: "~12m"
  completed: "2026-07-02"
  tasks: 2
  files_changed: 3
---

# Phase 25 Plan 03: News Page Semantics + Traffic Classifier Exclusion Summary

**One-liner:** Build-time month-grouped news page with h2/h3 headings and crime-type/commune chips; classifier SYSTEM_PROMPT hardened to reject traffic accidents at confidence=0.0.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | News page semantic headings, chips, build-time date grouping | 322816d | site/src/pages/news.astro |
| 2 (RED) | Classifier traffic-accident regression test (failing) | 8fc5e8c | pipeline/tests/test_classifier_traffic.py |
| 2 (GREEN) | Classifier SYSTEM_PROMPT traffic exclusion rule | f3f7e6a | pipeline/news/classifier.py |

## What Was Built

**Task 1 — news.astro:**
- 129 incidents grouped by YYYY-MM into `<section><h2 class="news-date-group">Month YYYY</h2>` at build time
- Each article rendered as `<article class="news-card"><h3 class="news-title"><a href=...>title</a></h3>`
- `news-type-chip` (family, capitalized) and `news-commune-chip` (commune name from loadIndex CUT lookup) per card
- CUT type-coercion fix: incidents store cut as integer, index.json as string — resolved via `String(incident.cut)`
- Commune name link: `/commune/{slug}/` for EN; commune name sourced from loadIndex (never bare "View commune")
- All titles rendered via Astro `{expr}` auto-escaping — XSS mitigated (T-25-03-XSS)
- h1 updated to "Recent Crime Incidents in Chile"
- Build result: 42 h3 elements, 42 type chips, 42 commune chips, 1 h2 month group

**Task 2 — classifier.py + test_classifier_traffic.py:**
- SYSTEM_PROMPT Rules block extended: traffic accidents / colisión / accidente de tránsito / choque / atropello sin culpa criminal → confidence MUST be 0.0
- Existing `CONFIDENCE_THRESHOLD = 0.6` gate rejects these automatically
- Regression tests: `test_traffic_accident_rejected`, `test_zero_confidence_traffic_rejected`, `test_system_prompt_contains_traffic_exclusion` — all 3 pass
- No live DeepSeek calls; client patched via `unittest.mock.patch`
- TDD gate compliance: RED commit 8fc5e8c → GREEN commit f3f7e6a

## Deviations from Plan

**1. [Rule 1 - Bug] CUT integer/string type mismatch in Map lookup**
- **Found during:** Task 1 post-build verification (commune chips showed 0 matches)
- **Issue:** incidents.cut is stored as integer (e.g., `13106`) in current.json; index.json CUT is string (`"13106"`); TypeScript Map.get() uses strict equality
- **Fix:** Changed incident type to `cut?: string | number`, getCommuneInfo converts via `String(incident.cut)`
- **Files modified:** site/src/pages/news.astro
- **Commit:** included in 322816d (same task commit)

## Known Stubs

None — all 42 incidents render real commune names and crime-type labels from actual data.

## Threat Flags

None — XSS (T-25-03-XSS) and classifier tampering (T-25-03-CLS) both mitigated as planned.

## TDD Gate Compliance

- RED gate: commit 8fc5e8c `test(25-03): add failing regression test` — 1/3 tests failed (SYSTEM_PROMPT rule absent)
- GREEN gate: commit f3f7e6a `feat(25-03): add traffic-accident exclusion rule` — 3/3 tests pass
- REFACTOR: not needed

## Self-Check

- [x] site/src/pages/news.astro — modified
- [x] pipeline/news/classifier.py — modified
- [x] pipeline/tests/test_classifier_traffic.py — created
- [x] Commits 322816d, 8fc5e8c, f3f7e6a exist in git log
- [x] `npm run build && npm run validate` — 14/14 validators passed
- [x] `python -m pytest pipeline/tests/test_classifier_traffic.py` — 3/3 passed

## Self-Check: PASSED
