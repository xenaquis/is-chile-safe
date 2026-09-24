---
phase: 35-honest-freshness-signals
plan: 01
subsystem: news
tags: [astro, vitest, freshness, G-05, coverage-gaps]

requires: []
provides:
  - "site/src/lib/newsEvidence.mjs — the single JS definition of the G-05 evidence rule (latestIncidentDate, computeEvidence, evidenceVerdict, MAX_AGE_HOURS=48, FUTURE_ALLOWANCE_HOURS=24, COMMUNE_NEWS_STALE_HOURS=168), typed via newsEvidence.d.mts"
  - "freshness.mjs refactored into a thin consumer of newsEvidence.mjs; byte-identical console output and exit codes; 12 pre-existing fixture tests unmodified and green"
  - "site/src/lib/newsCoverageGaps.ts — COVERAGE_GAPS declaring the G-18 classifier outage (2026-09-05..2026-09-22)"
  - "computeDayBuckets (newsDayFacets.ts) clips the histogram window to the earliest valid incident date (FRESH-02) and flags per-bucket gap: boolean per declared COVERAGE_GAPS (R-01)"
affects: [35-02, 35-03, 35-04, 35-06, 35-07]

tech-stack:
  added: []
  patterns:
    - "Shared JS evidence helper consumed by both a build-time validator and (in later 35 plans) page consumers, keeping G-05 defined exactly once in JS; the Python twin (pipeline/news_evidence.py) stays pinned by the same lettered fixtures A-G."
    - "Coverage gaps are declared, not inferred, and self-disable per day on count>0 rather than being time-bound removed (A-R1-08)."

key-files:
  created:
    - site/src/lib/newsEvidence.mjs
    - site/src/lib/newsEvidence.d.mts
    - site/src/lib/newsEvidence.test.ts
    - site/src/lib/newsCoverageGaps.ts
  modified:
    - site/scripts/validate/freshness.mjs
    - site/src/lib/newsDayFacets.ts
    - site/src/lib/newsDayFacets.test.ts

key-decisions:
  - "computeEvidence/evidenceVerdict live in newsEvidence.mjs only; freshness.mjs imports them instead of maintaining its own copy of the G-05 rule."
  - "computeDayBuckets clips the window start to max(anchor-(width-1), earliest valid incident date), never to generated-window_days, because FRESH-04 (35-02) changes what generated means."
  - "gap flag is per-bucket (count===0 AND date inside a declared range); COVERAGE_GAPS ranges are never removed, since a per-day count>0 self-disables the flag for that day (A-R1-08)."

requirements-completed: [FRESH-01, FRESH-02, FRESH-03]

duration: 55min
completed: 2026-09-24
---

# Phase 35 Plan 01: Shared G-05 evidence helper + coverage-clipped day histogram Summary

**Single JS definition of the G-05 freshness rule (newsEvidence.mjs) consumed by freshness.mjs, plus a coverage-clipped, gap-flagged day histogram (newsDayFacets.ts) so /news/ never draws bars before the data starts or presents a known classifier outage as zero-incident days.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-09-24T22:16:00Z (approx, first read)
- **Completed:** 2026-09-24T23:11:46Z
- **Tasks:** 2
- **Files modified:** 7 (4 created, 3 modified)

## Accomplishments
- Extracted the G-05 evidence rule (last_new_incident_at, else max(date)+1d; 48h stale; 24h future refusal) into one pure ESM helper, `newsEvidence.mjs`, with strict `.d.mts` types and a dedicated `evidenceVerdict` that also serves the 168h commune-news caveat threshold (FRESH-03).
- Refactored `freshness.mjs` into a thin consumer: it imports the helper, keeps every console message and exit code byte-identical, and its 12 pre-existing fixture tests (A-G plus edge cases) pass unmodified.
- Confirmed the Python twin (`pipeline/news_evidence.py`, tested via `TestNewsHeartbeatG05`) is untouched and still green — 10/10 passed by exit code.
- Fixed FRESH-02: `computeDayBuckets` now clips the histogram's window start to the earliest valid incident date in the input, so no bar is ever drawn for a day before the data's own coverage. Internal zero days inside the clipped window are still drawn (dense series preserved).
- Implemented R-01: `newsCoverageGaps.ts` declares the G-18 classifier-outage range (2026-09-05..2026-09-22); `computeDayBuckets` now emits `gap: boolean` per bucket, true only when the bucket both falls in a declared range AND has 0 incidents, so a partial backfill self-disables the flag per day without ever removing the declared range.

## Task Commits

1. **Task 1: Shared evidence helper newsEvidence.mjs + freshness.mjs refactor** - `da6534a` (feat)
2. **Task 2: FRESH-02 clip the day histogram to the data's coverage + declared outage gaps (R-01)** - `db1c74f` (feat)

**Plan metadata:** (this commit, pending)

## Files Created/Modified
- `site/src/lib/newsEvidence.mjs` - single JS definition of latestIncidentDate/computeEvidence/evidenceVerdict + G-05/FRESH-01/FRESH-03 constants
- `site/src/lib/newsEvidence.d.mts` - strict TS types for the .mjs helper
- `site/src/lib/newsEvidence.test.ts` - behavior-bullet fixtures for the helper
- `site/scripts/validate/freshness.mjs` - refactored to import the helper; console/exit-code output unchanged
- `site/src/lib/newsCoverageGaps.ts` - COVERAGE_GAPS declaration (G-18 outage)
- `site/src/lib/newsDayFacets.ts` - computeDayBuckets clips to earliest incident date and adds gap flag; DayBucket gains `gap: boolean`
- `site/src/lib/newsDayFacets.test.ts` - updated existing shapes to coverage-clipped values, added clipping + R-01 gap-flag tests

## Decisions Made
- Followed the plan's knob explicitly: coverage start is the earliest valid incident date in the payload, not `generated - window_days` (FRESH-04 in 35-02 changes what `generated` means, so this stays decoupled).
- `earliestValidDate` is computed over the full `dates` array (not window-filtered first), matching the "excludes dates outside window" test where an out-of-window earlier date does not incorrectly clip the window (it's only used when it would raise the lower bound).
- Added `evidenceVerdict`'s custom `maxAgeHours` parameter to directly serve the COMMUNE_NEWS_STALE_HOURS (168h) caveat use case described in the behavior bullets, without a second function.

## Deviations from Plan

None - plan executed exactly as written, including the negative controls specified in each task's `<verify>` block (MAX_AGE_HOURS temporarily set to 72, clip line disabled, gap condition forced to `false` — each confirmed the expected test failures, then reverted).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `newsEvidence.mjs` is ready for 35-02's FRESH-01 notice and 35-03/35-04's stale-caveat consumers to import directly, with no third copy of the G-05 rule.
- `computeDayBuckets`'s new `gap: boolean` field and 4th `gaps` parameter are ready for 35-04's gap-styling task and 35-06's caption-span assertions (F35-R1-04 gate condition), though the {from}/{to} caption derivation itself is out of scope for this plan.
- No blockers. `npx vitest run` (site/): 124/124 passed. `npx astro check`: 0 errors. `pytest -k TestNewsHeartbeatG05`: 10/10 passed. `data/` untouched (`git status --porcelain data/` empty).

---
*Phase: 35-honest-freshness-signals*
*Completed: 2026-09-24*
