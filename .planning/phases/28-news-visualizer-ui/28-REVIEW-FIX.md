---
phase: 28-news-visualizer-ui
fixed_at: 2026-07-30T10:22:00Z
review_path: .planning/phases/28-news-visualizer-ui/28-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
tests_passed: true
test_command: "npx astro check && npm run build && npm test && npm run validate && python -m pytest -q"
status: all_fixed
---

# Phase 28: Code Review Fix Report

**Fixed at:** 2026-07-30T10:22:00Z
**Source review:** .planning/phases/28-news-visualizer-ui/28-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (WR-01..WR-05, as specified in the fix task; WR-06/07/08 and IN-01..06 were out of scope)
- Fixed: 5
- Skipped: 0
- Test gate: PASSED (astro check 4/0, vitest 3 files/36 tests, 16/16 validators, pytest 344 passed/1 skipped/1 xfailed)

## Test Gate

- PASSED — full chained gate exited clean after all fixes:
  - `npx astro check` → 4 errors / 0 warnings (pre-existing baseline, unchanged)
  - `npm run build` → 834 pages built
  - `npm test` → 3 test files, 36 tests passed (32 pre-existing + 4 new: 1 WR-01 regression test, 3 WR-03 tests)
  - `npm run validate` → 16/16 validators passed (facets.mjs: 21 assertions passed)
  - `python -m pytest -q` → 344 passed, 1 skipped, 1 xfailed

## Fixed Issues

### WR-01: history.replaceState discarded non-filter query params and emitted a bare '?'

**Files modified:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro`, `site/src/lib/newsFilterLogic.test.ts`
**Commit:** 9bbde22
**Applied fix:** Replaced the fresh-`URLSearchParams` rebuild with a merge against `location.search`: only the four filter keys (`family`, `region`, `window`, `q`) are deleted/re-set, all other params (utm_source, ref, gclid, etc.) are preserved, and the `'?'` is omitted entirely when the resulting query string is empty (`location.pathname + (qs ? '?' + qs : '') + location.hash`). Applied identically to both EN and ES pages. Added `Test 12` pinning `serializeFilterParams(all-empty) === ''`.
**RED demonstration observed:** Reproduced the pre-fix bug in isolation — a Node script simulating the old `'?' + usp.toString()` logic with an all-empty filter state produced the literal string `"?"`, confirming the bare-`?` regression the fix addresses.

### WR-02: assertion 12 could not detect a hidden `.news-card` (NEWSUI-02 unguarded)

**Files modified:** `site/scripts/validate/facets.mjs`
**Commit:** 5b8c058
**Applied fix:** Added a companion check inside the existing assertion-12 loop: fails if any `<article class="news-card" ... hidden ...>` or `<section class="news-month-section" ... hidden ...>` node appears in the built dist HTML, and fails if author CSS sets `display` on `.news-card`.
**RED demonstration observed:** Added `hidden` to the `<article>` element at `news.astro:285`, rebuilt, and ran `node scripts/validate/facets.mjs` directly — got `FAIL facets: assertion 12 — EN ships a .news-card with the hidden attribute (NEWSUI-02 violation)`. Reverted the injected `hidden`, rebuilt, re-ran — green (21 assertions passed, 16/16 validators).

### WR-03: 30-day boundary and `today` predicate unpinned by the spec

**Files modified:** `site/src/lib/newsFilterLogic.test.ts`
**Commit:** 90b34d3
**Applied fix:** Added three tests: `Test 13` pins the 30d boundary (inclusive at anchor−29, exclusive at anchor−30, plus `WINDOW_30D_WIDTH_DAYS === 30`), `Test 14` pins `matchesWindow(..., 'today')` exactness, `Test 15` exercises `computeFacetCounts(..., 'window', [...])`.
**RED demonstration observed:** (a) Mutated `WINDOW_30D_WIDTH_DAYS` from `30` to `31` — Test 13 failed (`expected true to be false`). Reverted, confirmed green. (b) Mutated the `today` branch from `dateStr === newestDate` to `dateStr >= newestDate` — Test 14 failed on the future-date case. Reverted, confirmed green (15/15 in the file).

### WR-04: assertion 20's comment-stripper truncated code at a URL's `//`

**Files modified:** `site/scripts/validate/facets.mjs`
**Commit:** e68df5d
**Applied fix:** Replaced the trailing-`//` strip (`line.replace(/\/\/.*$/, '')`, which cuts a line short at any `//` including one inside a URL literal) with a whole-line-comment filter (`!/^\s*(\/\/|\/\*|\*)/.test(line)`) that never touches trailing text on a code line.
**RED demonstration observed:** Ran a standalone Node repro: the line `const u = "https://ischilesafe.com/news/"; el.innerHTML = data;` — the OLD stripper truncated it to `const u = "https:` (evading the `innerHTML` scan entirely, confirmed `/innerHTML/.test(oldStripped) === false`); the NEW filter-based approach left the full line intact and correctly flagged `innerHTML` (`true`). Rebuilt and re-ran the full validator after applying the fix — still green (both news pages' genuine whole-line `//` doc-comments naming `innerHTML` remain excluded, confirmed no false positive was introduced).

### WR-05: assertion 11's `toLocaleDateString` scan couldn't match a call containing any `)`

**Files modified:** `site/scripts/validate/facets.mjs`
**Commit:** 18e72f9
**Applied fix:** Replaced the `[^)]*month:[^)]*` pattern (which cannot cross a closing paren) with a call-head match (`(toLocaleDateString|Intl\.DateTimeFormat)\s*\(`) followed by a fixed-length tail scan (400 chars) for `month:`/`timeZone: 'UTC'`, so nested-paren argument forms are still inspected.
**RED demonstration observed:** Ran a standalone Node repro with `d.toLocaleDateString(getLocale(), { month: "long" })` (missing `timeZone: 'UTC'`, nested call in the first argument) — the OLD regex produced 0 matches (silently evaded, not failed); the NEW scan correctly flagged it (`flagged === true`). Rebuilt and re-ran the full validator after applying the fix — still green; all four real `toLocaleDateString` call sites across both pages carry `timeZone: 'UTC'` and are correctly matched by the wider tail scan.

## Skipped Issues

None — all 5 in-scope findings were fixed and verified.

---

_Fixed: 2026-07-30T10:22:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
