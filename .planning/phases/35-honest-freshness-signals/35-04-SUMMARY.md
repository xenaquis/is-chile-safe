---
phase: 35-honest-freshness-signals
plan: 04
subsystem: news
tags: [astro, i18n, freshness, G-05, coverage-gaps, vitest, react]

# Dependency graph
requires:
  - phase: 35-01
    provides: "newsEvidence.mjs (G-05 helper), newsCoverageGaps.ts, computeDayBuckets gap flag"
  - phase: 35-03
    provides: "no direct code dependency; wave ordering only (depends_on)"
provides:
  - "/news/ + /es/noticias/: data-derived 'Latest incident: {date}' stamp (build stamp removed), bilingual stale/no-data notice gated on evidenceVerdict, per-bucket outage gap bars with contiguous-span captions"
  - "CommuneNewsSection.astro: caveated 'Earlier Incidents in the News' heading + dated note when the newest listed item is > 168h old"
  - "HomeNewsPulse.astro: coverage-clipped histogram, declared-outage gap bars, static bilingual stale notice"
  - "site/src/lib/newsStripDays.ts — computeStripDays(anchor, windowDays, unfilteredDates, gaps) pure helper, consumed by MapIsland/NewsStrip on /map/ and /es/mapa/"
affects: [35-05, 35-06, 35-07]

tech-stack:
  added: []
  patterns:
    - "Every freshness/gap consumer imports the single newsEvidence.mjs helper and/or COVERAGE_GAPS declaration from 35-01 — no second definition of the G-05 rule or the outage range anywhere in this plan."
    - "Gap-day decisions are always computed against the UNFILTERED incident set (never a family-filtered subset), both server-side (news.astro dayBuckets) and client-side (HomeNewsPulse enhancer, NewsStrip via MapIsland's stripDays)."

key-files:
  created:
    - site/src/lib/newsStripDays.ts
    - site/src/lib/newsStripDays.test.ts
  modified:
    - site/src/config/i18n.ts
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
    - site/src/components/CommuneNewsSection.astro
    - site/src/components/home/HomeNewsPulse.astro
    - site/src/config/homeV2Strings.ts
    - site/src/components/map/NewsStrip.tsx
    - site/src/components/map/MapIsland.tsx
    - site/src/components/map/map-v2.css
    - site/src/config/mapV2Strings.ts

key-decisions:
  - "i18n.ts's Task 1 and Task 2 keys were added in a single interface/EN/ES edit pass (commune_news_heading_stale/_stale_note/_aria_stale alongside the Task 1 keys) since they live in the same file; Task 2's commit therefore has no further i18n.ts diff. No functional difference from doing it in two passes."
  - "F35-R1-04 gap-caption spans are computed per-bucket at render time (computeGapSpans over dayBuckets), never from the declared COVERAGE_GAPS range directly — verified in dist: the caption for the current data ends 2026-09-19 (last actually-gap-flagged day), not 2026-09-22 (the declared range's end), because 09-20..09-22 already have real incidents in the current build."
  - "NewsStrip.tsx's `anchor` prop was removed entirely (not just unused) once computeStripDays absorbed its only purpose, keeping the component free of dead parameters."

requirements-completed: [FRESH-01, FRESH-02, FRESH-03]

# Metrics
duration: ~70min
completed: 2026-09-24
---

# Phase 35 Plan 04: Data-derived news freshness signals (FRESH-01/02/03) Summary

**Removed the build-time "Updated {date}" stamp from /news/, /es/noticias/, commune pages and the home pulse, replacing it everywhere with the shared G-05 evidence helper's verdict, honest "no data collected" outage-gap bars (server-side histogram, home pulse, and map NewsStrip), and a caveated commune-news heading when the newest listed item is stale — all bilingual, all static HTML except the pulse's existing client enhancer.**

## Performance

- **Duration:** ~70 min
- **Completed:** 2026-09-24
- **Tasks:** 4/4 (Task 4 followed the RED → GREEN → wiring TDD gate sequence)
- **Files modified:** 12 (2 created, 10 modified)

## Accomplishments

- **Task 1 (FRESH-01 + R-01):** `/news/` and `/es/noticias/` no longer show a build-time "Updated"/"Actualizado" stamp. They show `p.freshness[data-latest-incident][data-build-now]` with a data-derived "Latest incident: {date}" (long-format, UTC), and a `.news-stale-notice` sibling paragraph that renders only when `evidenceVerdict(computeEvidence(payload), buildNowMs, 48)` is `'stale'` or `'none'` — `'future'` is deliberately excluded (R1/R-07). Histogram buckets flagged `gap: true` by 35-01's `computeDayBuckets` render "no data collected"/"sin datos recolectados" with a striped fill instead of "· 0", and one `.day-gap-caption[data-gap-from][data-gap-to]` renders per contiguous gap span — `{from}/{to}` come from the span's own first/last gap-bucket dates, never the declared `COVERAGE_GAPS` range (F35-R1-04). Verified in the built HTML: with local data frozen mid-recovery, the caption reads 2026-09-05..2026-09-19 (15 real gap days remaining), not the full declared 09-05..09-22 range, because 09-20..09-22 already carry real incidents.
- **Task 2 (FRESH-03):** `CommuneNewsSection.astro` computes `stale` from the newest of its (already forbidden-term-filtered, max-6) displayed items via `evidenceVerdict(computeEvidence({incidents: items}), buildNowMs, COMMUNE_NEWS_STALE_HOURS)` (168h). When stale, the heading switches to "Earlier Incidents in the News" / "Incidentes Anteriores en la Prensa" (no zero-quantifier, per gate condition F35-R1-05) and a `.cnews-stale-note` states the newest listed date, with no claim about geolocation or pipeline activity (R1/R-06). 109 EN/ES commune sections rendered in the local build, 74 of them stale.
- **Task 3 (R-03):** `HomeNewsPulse.astro` reads `current.json` at build time with the same G-05 helper, stamps the card with `data-coverage-gaps`, `data-gap-label` and `data-build-now`, and renders a static `.pulse-stale` notice when stale/none. The client enhancer's histogram start now clips to `max(anchor-29, earliest valid date in the unfiltered `all`)` (no more 30-day pre-coverage pad) and marks declared-outage days as gap bars computed against `all` (never the family-filtered `pool`), so a family filter can never manufacture or hide a gap day.
- **Task 4 (F35-R1-06, G-22(b), TDD):** New pure helper `newsStripDays.ts` (`computeStripDays`) replaces `NewsStrip.tsx`'s old internal range computation — the `:72-73` pre-coverage extension and the 2×-window floor cap are both deleted. `MapIsland.tsx` derives `stripDays` from the UNFILTERED incidents file and passes it down; `NewsStrip` renders gap days with a striped bar and a `"{dayLabel} : no data collected"` aria-label. RED (failing import) → GREEN (6/6 behavior fixtures) → wiring, each its own commit; a negative control (disabling the coverage-clip line) was run and reverted, confirming 2 of 6 tests fail without it.

## Task Commits

1. **Task 1: FRESH-01 latest-incident stamp + stale notice + outage gap bars** - `f2c3b61` (feat)
2. **Task 2: FRESH-03 caveated commune news heading** - `85a00e6` (feat)
3. **Task 3: R-03 home news pulse coverage clip + gap days + stale notice** - `8f06658` (feat)
4. **Task 4a: RED — failing test for newsStripDays** - `78cd01c` (test)
5. **Task 4b: GREEN — implement computeStripDays** - `5fd652b` (feat)
6. **Task 4c: wire computeStripDays into NewsStrip/MapIsland** - `c3fd8ce` (feat)

## Files Created/Modified

- `site/src/lib/newsStripDays.ts` — pure `computeStripDays(anchor, windowDays, unfilteredDates, gaps)` helper
- `site/src/lib/newsStripDays.test.ts` — 6 behavior fixtures from the plan's `<behavior>` block
- `site/src/config/i18n.ts` — adds `news_latest_incident`, `news_stale_notice`, `news_stale_notice_nodate`, `news_gap_bar_label`, `news_gap_caption`, `commune_news_heading_stale`, `commune_news_stale_note`, `commune_news_aria_stale` (EN+ES)
- `site/src/pages/news.astro` / `site/src/pages/es/noticias.astro` — replace the build stamp with the data-derived stamp + stale notice; gap-flagged histogram bars + span captions
- `site/src/components/CommuneNewsSection.astro` — stale heading/note/aria-label switch
- `site/src/components/home/HomeNewsPulse.astro` — build-time evidence read, `.pulse-stale` notice, coverage-clipped + gap-flagged client histogram
- `site/src/config/homeV2Strings.ts` — adds `news_gap_label` (EN+ES)
- `site/src/components/map/NewsStrip.tsx` — replaces internal range computation with a `days: StripDay[]` prop; renders gap bars
- `site/src/components/map/MapIsland.tsx` — derives `stripDays` via `computeStripDays` and passes it to `NewsStrip`
- `site/src/components/map/map-v2.css` — adds `.news-strip-bar.gap > span` striped rule (see Deviations)
- `site/src/config/mapV2Strings.ts` — adds `news_strip_gap` (EN+ES)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking issue] `map-v2.css` edited though not in `files_modified`**
- **Found during:** Task 4
- **Issue:** The plan's action step says "Add a `.news-strip-bar.gap` striped style next to the existing strip CSS," but `NewsStrip.tsx` has no `<style>` block of its own — its CSS lives entirely in the sibling file `site/src/components/map/map-v2.css`, which the `files_modified` frontmatter list omits.
- **Fix:** Added the striped `.news-strip-bar.gap > span` rule to `map-v2.css`, next to the existing `.news-strip-bar` rules, matching the pattern already used for `.active`.
- **Files modified:** `site/src/components/map/map-v2.css`
- **Commit:** `c3fd8ce`

No other deviations — all other steps, including the R1/R2 revision text baked into the plan (F35-R1-01 guard, F35-R1-04 span captions, F35-R1-05 zero-quantifier-free heading, F35-R1-06 NewsStrip task), were followed literally.

## Issues Encountered

None beyond the deviation above. The Step 0 precondition (`grep -c '^- \[x\] \*\*Phase 34' .planning/ROADMAP.md` == 1) passed before any edits were made, confirming Phase 34 is closed and this plan was safe to execute.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All must_haves and artifacts from the plan frontmatter are present and machine-checkable: `p.freshness[data-latest-incident][data-build-now]`, `.news-stale-notice`, `.day-bar[data-gap]`, `.day-gap-caption[data-gap-from][data-gap-to]`, `section.cnews-section[data-news-stale][data-build-now]`, `.pulse-card[data-coverage-gaps][data-build-now]`, and the map's `days: StripDay[]` contract.
- 35-05/35-06/35-07 (mentioned as `affects`) can build their validators/harnesses directly against these data-* contracts without re-deriving any freshness logic.
- Local build state at completion: freshness verdict is `'fresh'` (last_new_incident_at 2.6h old at validation time), so the stale-notice counts recorded in each task's verify were 0 (expected per each task's "record the number" instruction) — the stale/none code paths are exercised only by the CommuneNewsSection per-commune 168h check (74/109 communes stale in the current data) and are otherwise dormant until the news feed pauses again, at which point they will render correctly per the shared helper's contract (already unit-tested in 35-01).
- Full validation: `npm run build` (834 pages) + `npm run validate` (16/16 validators PASS, including `freshness` and `facets`) + `npx vitest run` (138/138 tests, 13 files) + `npx astro check` (0 errors, 0 warnings) all green. `git status --short data/` is empty (data/ untouched).

---
*Phase: 35-honest-freshness-signals*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: site/src/lib/newsStripDays.ts
- FOUND: site/src/lib/newsStripDays.test.ts
- FOUND: .planning/phases/35-honest-freshness-signals/35-04-SUMMARY.md
- FOUND commit: f2c3b61
- FOUND commit: 85a00e6
- FOUND commit: 8f06658
- FOUND commit: 78cd01c
- FOUND commit: 5fd652b
- FOUND commit: c3fd8ce

## Post-execution fix (pre-push opus review, 2026-09-24)

- F1: `computeStripDays` lower bound changed from anchor-(windowDays-1) to anchor-windowDays. store.py keeps `date >= today - window_days` (31 dates), so the old bound hid a day holding real incidents while the header count included them. Test "08-27" expectation corrected to "08-26"; new parity test added. (Plan text 35-04:229 carried the off-by-one.)
- F2: stray space before the colon in the gap-bar aria-label removed.
- Gate after fix: build OK, validators 18/18, vitest 184, astro check 0 errors.
