---
phase: 35-honest-freshness-signals
plan: 06
subsystem: validate
tags: [validator, vitest, freshness, news, commune, G-05, node]

# Dependency graph
requires:
  - phase: 35-01
    provides: "newsEvidence.mjs (G-05 helper), newsCoverageGaps.ts, computeDayBuckets gap flag"
  - phase: 35-04
    provides: "the freshness/gap/caveat markup contracts this validator checks — p.freshness, .news-stale-notice, .day-bar[data-gap], .day-gap-caption, section.cnews-section[data-news-stale]"
  - phase: 35-05
    provides: "wave ordering only (executed alone, wave 5, after 35-04/35-05 per G-21(1)); validator numbering precedent (#17 cead-vintage.mjs)"
provides:
  - "news-freshness.lib.mjs — checkNewsPage/checkCommuneSection pure checkers built on the single newsEvidence.mjs G-05 rule"
  - "news-freshness.mjs — validator #18, registered in all.mjs (18/18 PASS)"
  - "news-freshness-fixtures.mjs — Sep-4-frozen vs today-fresh real-build harness (not in all.mjs; 35-07 close-gate artifact)"
  - "fixtures/news-current-frozen-2026-09-04.json — 40 newest incidents of git f5761ea's current.json, no last_new_incident_at"
affects: [35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Validator #18 imports the shared newsEvidence.mjs G-05 rule directly (unlike cead-vintage.mjs's from-scratch reimplementation precedent) because the whole point of this validator is page-vs-payload consistency against that single rule, not independent re-derivation of a data label."
    - "The Task 2 fixture harness is deliberately independent of the Task 1 lib (T-35-13): its assertions are plain string search over the raw HTML, not a call into news-freshness.lib.mjs, so a shared bug between page code and lib cannot make the harness lie."
    - "Attribute-order/data-astro-cid tolerant section extraction via lookahead regex (`<section\\b(?=[^>]*\\bclass=\"cnews-section\")...`), scoped strictly to the substring up to the matching `</section>` — the CEAD `<time>` and other h2.section-heading nodes on a commune page are never inspected (R1/R-08)."

key-files:
  created:
    - site/scripts/validate/news-freshness.lib.mjs
    - site/scripts/validate/news-freshness.test.ts
    - site/scripts/validate/news-freshness.mjs
    - site/scripts/validate/news-freshness-fixtures.mjs
    - site/scripts/validate/fixtures/news-current-frozen-2026-09-04.json
  modified:
    - site/scripts/validate/all.mjs

key-decisions:
  - "checkNewsPage's per-bar gap check (R1/R-01) and gap-caption span check (R2/F35-R1-04) both operate against the exact `payload` argument passed in — for the real build this is the same site/public/data/incidents/current.json the page itself read, so 'no payload incident has date D' is computed from the full incident set, not the page's 30-day window."
  - "news-freshness-fixtures.mjs writes each fixture to both the build input (site/public/data/incidents/current.json, overwritten per iteration) and a dedicated OS-temp payload file, so the post-build call to news-freshness.mjs (via NEWS_FRESHNESS_CURRENT_JSON) always reads the exact fixture that produced that outDir, even after the next iteration has already overwritten the public copy."
  - "k (the fresh fixture's date shift) is computed as the whole-day difference between today UTC and 2026-09-04, applied via UTC string arithmetic (addDaysStr, ported from newsDayFacets.ts's addDays) — never local-time Date math."

requirements-completed: [FRESH-01, FRESH-02, FRESH-03]

# Metrics
duration: ~70min
completed: 2026-09-24
---

# Phase 35 Plan 06: Validator #18 (news-freshness) + Sep-4-frozen fixture harness Summary

**Validator #18 (news-freshness.mjs) mechanically checks that /news/, /es/noticias/ and every commune's press section agree with the shared G-05 evidence rule on whatever payload the build consumed — including per-day outage-gap bars and their contiguous-span captions — and a separate two-build harness (news-freshness-fixtures.mjs) proves the Sep-4-frozen fixture makes the stale notice and caveated heading appear, while a today-shifted fresh fixture makes them disappear, across both locales.**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-09-24T20:56Z (approx, first read)
- **Completed:** 2026-09-25T00:06Z
- **Tasks:** 2/2
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments

- **Task 1 (validator #18):** `news-freshness.lib.mjs` exports `checkNewsPage(html, payload, locale)` and `checkCommuneSection(html, locale)`, both built on the single `newsEvidence.mjs` G-05 rule (no second definition anywhere). `checkNewsPage` asserts the `data-latest-incident`/`data-build-now` attributes, the visible "Latest incident"/"Último incidente" text, the `.news-stale-notice` presence/absence mirroring 35-04's `verdict ∈ {'stale','none'}` mapping exactly (R1/R-07: `'future'` never triggers a notice), a build-time `">Updated "` stamp regression guard, the R1/R-01 per-bar gap check (expected gap = date in a declared `COVERAGE_GAPS` range AND no payload incident on that date), and the R2/F35-R1-04 gap-caption span check (every date in a caption's span must be a `data-gap="true"` bar, spans must be maximal, and the visible text must name both dates in the locale's long format — verified with a fixture where a real 09-22 incident shrinks the caption's end to 09-21). `checkCommuneSection` scopes strictly to the `<section class="cnews-section">…</section>` substring (R1/R-08, tolerant of attribute order and `data-astro-cid-*`), checking `data-news-stale` against the newest listed item's 168h verdict and the exact heading literal (`Earlier Incidents in the News` / `Incidentes Anteriores en la Prensa` vs the normal heading), with a regression guard against the old zero-quantifier `(none in the last 7 days)` phrasing (R2/F35-R1-05).
- The committed frozen fixture (`fixtures/news-current-frozen-2026-09-04.json`) holds the 40 newest incidents of `git f5761ea`'s `current.json` (max date 2026-09-04, no `last_new_incident_at`), generated deterministically and verified by an independent python assertion.
- `news-freshness.mjs` scans `dist/news/`, `dist/es/noticias/`, and every `dist/commune/<slug>/` + `dist/es/comuna/<slug>/` cnews-section, registered as validator #18 in `all.mjs` (18/18 PASS on the real build).
- **Task 2 (fixture harness):** `news-freshness-fixtures.mjs` builds the site twice into OS-temp outDirs (never OneDrive) from the frozen fixture and a today-shifted fresh copy, asserting hardcoded absolute outcomes with plain string search — deliberately independent of the Task 1 lib (T-35-13). Frozen: exactly 1 `.pulse-stale` on each home page, exactly 1 `.news-stale-notice` on each news page, `data-latest-incident="2026-09-04"`, the exact "Latest incident: September 4, 2026" / "Último incidente: 4 de septiembre de 2026" text, and all 23 fixture-commune sections (of 40 incidents' distinct communes) found on the build caveated true/stale in both locales. Fresh: 0 of each, `data-latest-incident` = today UTC, all 23 fixture communes normal/false. Wall time: **~37-38s** for both builds plus both validator cross-checks. `git status --porcelain site/public data` = 0 after every run (the `finally` block restores via `sync-data.mjs` and removes temp dirs unconditionally, even on assertion failure).
- Three mandatory negative controls, each run then reverted: `news.astro`'s `showStale = false` → harness exits 1 naming "frozen: expected exactly 1 news-stale-notice on EN news, got 0"; `HomeNewsPulse.astro`'s `showStale = false` → exits 1 naming "frozen: expected exactly 1 pulse-stale on EN home, got 0"; `newsEvidence.mjs`'s `COMMUNE_NEWS_STALE_HOURS = 100000` → exits 1 on every frozen commune (macul, el-tabo, las-condes, …). All three reverts confirmed clean via a final harness re-run (PASS, `git status --porcelain site/public data` = 0).

## Task Commits

1. **Task 1: news-freshness.lib.mjs + runner (#18) + frozen fixture file** - `d3fd15c` (feat)
2. **Task 2: news-freshness-fixtures.mjs — frozen vs fresh real-build harness** - `31576e2` (feat)

**Plan metadata:** (this commit, pending)

## Files Created/Modified

- `site/scripts/validate/news-freshness.lib.mjs` - pure `checkNewsPage`/`checkCommuneSection` + `formatLongDate`/`COVERAGE_GAPS` literal copy
- `site/scripts/validate/news-freshness.test.ts` - 23 vitest cases covering every behavior bullet in the plan (positive/negative fixtures, R1/R-01, R2/F35-R1-04, R1/R-07, R1/R-08, R2/F35-R1-05, COVERAGE_GAPS parity)
- `site/scripts/validate/news-freshness.mjs` - dist scanner; validator #18
- `site/scripts/validate/news-freshness-fixtures.mjs` - frozen/fresh two-build harness with 3 negative-control-tested assertions
- `site/scripts/validate/fixtures/news-current-frozen-2026-09-04.json` - committed Sep-4-frozen fixture (40 incidents)
- `site/scripts/validate/all.mjs` - appends `news-freshness.mjs` after `cead-vintage.mjs`; header comment updated to list 18 validators

## Decisions Made

- Followed the plan's Step 0 precondition literally: `grep -c '^- \[x\] \*\*Phase 34' .planning/ROADMAP.md` printed `1` before any edits, confirming Phase 34 is closed.
- `news-freshness.mjs`'s per-bar and caption checks read the exact `NEWS_FRESHNESS_CURRENT_JSON` payload (default: `site/public/data/incidents/current.json`, the file the build actually consumed) rather than re-deriving anything from `dist/`, keeping the validator data-agnostic as the plan's objective requires.
- Chose a lookahead-based `<section>`/`<h2>` extraction regex (`/<section\b(?=[^>]*\bclass="cnews-section")([^>]*)>([\s\S]*?)<\/section>/`) over a fixed-attribute-order regex specifically to satisfy R1/R-08's attribute-order and `data-astro-cid-*` tolerance requirement, verified against a synthetic out-of-order fixture in the vitest suite.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `SITE_ROOT` computed one directory too shallow in news-freshness.mjs**
- **Found during:** Task 1 verify (validator run against the real build)
- **Issue:** `path.resolve(__dirname, '..')` from `site/scripts/validate/` resolves to `site/scripts/`, not `site/`, causing every `dist`/`public` path to be wrong and both news pages to report "missing" even though they existed.
- **Fix:** Changed to `path.resolve(__dirname, '../..')`, matching the `cead-vintage.mjs`/`freshness.mjs` precedent, and removed the now-unused `REPO_ROOT` variable (this validator never reads repo-root paths).
- **Files modified:** `site/scripts/validate/news-freshness.mjs`
- **Commit:** `d3fd15c` (folded into Task 1's commit; fixed before commit)

**2. [Rule 1 - Bug] Unescaped `*/` inside a block comment broke module parsing**
- **Found during:** Task 1 verify (validator run)
- **Issue:** The JSDoc header's literal path example `dist/commune/*/index.html` contains `*/`, which Node's parser reads as the comment's closing delimiter, producing a `SyntaxError: Unexpected identifier 'and'` on the next line.
- **Fix:** Rewrote the example as `dist/commune/&lt;slug&gt;/index.html` (HTML-entity-escaped angle brackets, no literal `*/`).
- **Files modified:** `site/scripts/validate/news-freshness.mjs`
- **Commit:** `d3fd15c` (folded into Task 1's commit; fixed before commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1, both mechanical path/syntax bugs caught by the plan's own verify command before commit).
**Impact on plan:** Both fixes were required for the validator to run at all; no scope creep, no behavior change beyond correcting the bugs.

## Issues Encountered

None beyond the two deviations above. No auth gates, no architectural questions, no fix-attempt-limit issues.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Validator count is now 18 (`structure` … `cead-vintage`, `news-freshness`); `npm run validate` prints `18/18 validators passed`.
- `news-freshness-fixtures.mjs` is ready for 35-07's close gate to invoke directly (not wired into `all.mjs` — costs two full builds, ~37-38s measured wall time well under the 10-minute tool timeout, addressing the gate's "Measurements reserved to the orchestrator" B-R1-06 item for this specific harness).
- `NEWS_FRESHNESS_DIST` / `NEWS_FRESHNESS_CURRENT_JSON` env overrides on `news-freshness.mjs` are the injection points 35-07 can reuse against prod-fetched HTML, mirroring the `CEAD_VINTAGE_DIST` precedent from 35-05.
- No blockers for 35-07. Full local validation: `npx vitest run` (site/): 183/183 passed (15 files, including the new 23-case `news-freshness.test.ts`); `npm run build` (834 pages) + `npm run validate` (18/18 PASS); `git status --porcelain site/public data` = 0 after the fixture harness and all three negative controls.

---
*Phase: 35-honest-freshness-signals*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: site/scripts/validate/news-freshness.lib.mjs
- FOUND: site/scripts/validate/news-freshness.test.ts
- FOUND: site/scripts/validate/news-freshness.mjs
- FOUND: site/scripts/validate/news-freshness-fixtures.mjs
- FOUND: site/scripts/validate/fixtures/news-current-frozen-2026-09-04.json
- FOUND: .planning/phases/35-honest-freshness-signals/35-06-SUMMARY.md
- FOUND commit: d3fd15c
- FOUND commit: 31576e2
