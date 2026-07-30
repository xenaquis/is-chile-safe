---
phase: 28-news-visualizer-ui
plan: 03
subsystem: news-visualizer-build-validation
tags: [validation, build-gate, i18n, tz-determinism, bundling-proof]
dependency-graph:
  requires:
    - site/scripts/validate/facets.mjs (existing validator #16, 10 assertions)
    - site/src/lib/newsFilterLogic.ts (Plan 28-01, FILTER_LOGIC_MARKER)
    - site/src/pages/news.astro + site/src/pages/es/noticias.astro (Plan 28-02, filter-bar UI)
  provides:
    - facets.mjs assertions 11-21 (still validator #16, no new sibling file, no F-21 count-correction needed)
    - Phase 28 Wave 0 requirements table fully closed (every ❌ row now falsifiable and green)
    - TZ-determinism fix in both news pages' formatMonth()/generated-date formatters
  affects:
    - Phase 28 close-out / verification (this is the terminal Wave 3 plan)
tech-stack:
  added: []
  patterns:
    - "Per-locale iteration via existing DIST_PAGES/SERIALIZATION_SITES arrays (RR-1 pattern), extended for 9 new both-locale assertions"
    - "Comment-stripping before source-level forbidden-pattern scans, to avoid false positives on doc comments that merely NAME a forbidden pattern"
    - "F-27 bundling proof follows one level of static import specifiers from a page's own chunk to find a marker Rollup hoisted into a shared chunk"
key-files:
  created: []
  modified:
    - site/scripts/validate/facets.mjs
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
decisions:
  - "Rule 1 fix (in-scope, same file, same bug class as assertion 11): formatMonth() and the generated-date formatter in both news pages used toLocaleDateString with a month: option but no timeZone: 'UTC' — real TZ-nondeterminism (build-machine-dependent month heading), not a false positive. Fixed via Date.UTC construction + timeZone: 'UTC' formatting, consistent with the existing anchorLabel pattern in the same files."
  - "Assertion 20's forbidden-DOM-sink scan strips // line comments before matching, because news.astro:372 has a doc comment reading '(T-12-01: value assignment only, never innerHTML)' that would otherwise false-positive — same false-positive class the plan explicitly calls out for the set:html bare-token scan."
  - "Assertion 17 walks one level of a page-chunk's own static import specifiers (matching from\"./*.js\" / from '*.js') because Rollup hoisted newsFilterLogic.ts into a separate shared chunk (newsFilterLogic.BS0afx7K.js) referenced from news.astro's own page chunk — VERIFIED the marker literal lives there, not in the page chunk itself."
metrics:
  duration: "~50 minutes"
  completed: "2026-07-30"
---

# Phase 28 Plan 03: facets.mjs Wave 0 Closure + Phase-Close Gate Summary

One-liner: Extends `facets.mjs` (still validator #16) with 11 new build-time-falsifiable assertions (anchorDate correctness, card-count parity, i18n key parity, empty-state/no-island/no-cluster guards, F-27 bundling proof, filter-control presence, canonical stability, no-innerHTML, no-client-directive) closing every ❌ row in 28-VALIDATION.md's Wave 0 table, plus a Rule 1 fix for a real TZ-nondeterminism bug the new assertion surfaced.

## What Was Built

### Task 1 — Assertions 11-16
Added six assertion blocks to `facets.mjs` after the existing assertion 10:
- **11 (anchorDate)**: reuses the existing `newestDate` local (assertion 8) rather than recomputing a third time; asserts both dist pages' `#news-facets.anchorDate` matches it. Also scans both `.astro` sources for any `toLocaleDateString(...)` call with a `month:` option lacking `timeZone: 'UTC'`.
- **12 (card-count)**: `/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"/g`, order-independent, not the literal `/<article class="news-card"/g` nor a bare substring. Confirmed against real build: 1215 both locales, matching `incidents.length`.
- **13 (i18n parity)**: extracts `EN_STRINGS`/`ES_STRINGS` blocks from `i18n.ts` source via string anchors (not import), harvests `news_*` keys with `matchAll(/^\s*(news_[a-z0-9_]+)\s*:/gm)` (digit-safe — `[a-z_]+` alone would miss `news_window_7d_label`), asserts bidirectional set equality and a ≥15 floor on each side.
- **14 (empty-state)**: asserts `id="news-empty"` exists, ships `hidden` in the initial render, and is not an `<h1>`/`<h2>`.
- **15 (no-island)**: asserts neither dist page contains `astro-island`.
- **16 (no cluster markup)**: greps both `.astro` sources AND dist HTML for `news-source-count`/`news-cluster`/`source-count`/`sources</`/`fuentes</`, never `i18n.ts` (which is expected to hold the reserved `news_cluster_source_count` key per assertion 13).

### Task 2 — Assertion 17 (F-27 bundling proof) + 18-21 + phase-close gate
- **17**: for each dist page, collects all inline `<script type="module">` bodies AND every `dist/_astro/*.js` referenced via `src=`, plus one level of that chunk's own static `import ... from "./*.js"` specifiers. Asserts the combined text contains the literal `newsFilterLogic/v1`. VERIFIED on the real build: neither page's own emitted chunk (`news.astro_astro_type_script_index_0_lang.*.js`) contains the marker directly — Rollup hoisted `newsFilterLogic.ts` into a separate shared chunk (`newsFilterLogic.BS0afx7K.js`) imported from the page chunk, which is exactly the shape this assertion's "one level of import" logic exists to follow.
- **18**: asserts presence of `news-filters`, `news-comuna-q`, `news-result-count`, `news-clear-filters` ids, `data-facet="window"|"region"|"family"` fieldsets with at least one checkbox each in region/family, and the exact token-scan form specified by the plan (strip the one required `data-result-count-template` carrier, then scan for `{n}`/`{date}`; separately pin the carrier count to exactly 1).
- **19**: asserts each page's `<link rel="canonical">` is exactly the bare path (`https://ischilesafe.com/news/` / `.../es/noticias/`), no query-string `<link rel="alternate">`, and no internal `<a href>` containing `?family=`/`?region=`/`?window=`/`?q=`.
- **20**: source-level scan of both `.astro` pages + `newsFilterLogic.ts` for `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`, with `//` line comments stripped first (see Deviations). Separately counts the `set:html=` ATTRIBUTE form and requires exactly 1 per page (never the bare token, which is 2 due to a Phase 27 explanatory comment).
- **21**: source-level scan of both `.astro` pages for `client:load`/`client:idle`/`client:visible`/`client:only`/`client:media`.

After all 21 assertions passed against the real build, ran the full chained phase-close gate exactly as specified in the plan's `<verification>` block (single `;` after `npx astro check`, everything downstream joined by `&&` only).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TZ-nondeterminism in `formatMonth()` and the generated-date formatter, both news pages**
- **Found during:** Task 1, first run of the new assertion 11 against the real build
- **Issue:** `news.astro`'s `formatMonth(yearMonth)` built a `Date` from local `y`/`m` components (`new Date(y, m - 1, 1)`) and formatted it with `toLocaleDateString('en-US', { year: 'numeric', month: 'long' })` — no `timeZone` option, so the rendered month heading depends on the build machine's system timezone rather than being deterministic. The `formattedDate` block (the "Updated {date}" freshness line) had the identical gap: `new Date(generated).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })`, no `timeZone`. Both are pre-existing (predate Phase 28), but this is exactly the class of bug assertion 11 exists to close per the plan's own framing ("closes the gap left by assertion 9, which only scans newsFacets.ts and never reads the .astro pages") — in-scope because it's the same file this task modifies and the same TZ-determinism concern the phase already treats as a correctness requirement (F-32's mandatory `timeZone: 'UTC'` on the anchorLabel computation in the same file).
- **Fix:** `formatMonth()` now builds the Date via `Date.UTC(y, m - 1, 1)` and formats with `timeZone: 'UTC'`. The generated-date formatter adds `timeZone: 'UTC'` to its existing options object. Applied identically to `news.astro` and `es/noticias.astro` (Spanish locale strings unchanged, only the TZ handling).
- **Files modified:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro`
- **Commit:** `8d9128f` (bundled with the facets.mjs assertion commit, since it was discovered by and fixes the exact gap assertion 11 introduces)

**2. [Rule 1 - Bug, validator-internal] False-positive risk in assertion 20's forbidden-DOM-sink scan**
- **Found during:** Task 2, first run of assertion 20 against the real build
- **Issue:** `news.astro:372` has a doc comment reading `// Pre-populate controls from parsed params (T-12-01: value assignment only, never innerHTML)`. A raw `/innerHTML/` regex scan of the full source matches this comment and fires a false FAIL, even though no code assigns to `innerHTML`. This is the same false-positive class the plan explicitly calls out for the `set:html` bare-token scan (which is why that scan uses the attribute form).
- **Fix:** Strip `//` line comments before scanning for the forbidden-DOM-sink patterns (`innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`).
- **Files modified:** `site/scripts/validate/facets.mjs` (validator logic only, no separate commit — folded into the same Task 1/2 commit since it was fixed before either task's `<verify>` block was run to completion)
- **Commit:** `8d9128f`

No architectural deviations. No auth gates encountered.

## RED-Demonstration Table

Every new assertion (11-21) was manually broken, confirmed non-zero exit with the expected `FAIL facets: assertion N` message, then restored and reconfirmed exit 0, per Operating Lesson 11.

| Assertion | Counterexample applied | RED confirmed | Restored GREEN |
|---|---|---|---|
| 11a (anchorDate) | `FACETS_CURRENT_JSON` fixture with newest incident's date moved back 1 day | `assertion 11 — EN rendered anchorDate "2026-07-27" !== independently-recomputed newest date "2026-07-26"` | Yes |
| 11b (UTC scan) | Removed `timeZone: 'UTC'` from `formatMonth()`'s `toLocaleDateString` call | `assertion 11 — EN page has a toLocaleDateString(...) call with a "month:" option but no "timeZone: 'UTC'"` | Yes |
| 12 (card-count) | Renamed one `class="news-card"` to `class="news-cardX"` in dist HTML | `assertion 12 — EN news-card count (1214) !== incidents.length (1215)` | Yes |
| 13 (i18n parity) | Deleted `news_clear_filters` from `ES_STRINGS` | `assertion 13 — ES_STRINGS harvested only 14 news_* keys, expected >= 15` | Yes |
| 14 (empty-state) | Removed `hidden` from `#news-empty` in dist HTML | `assertion 14 — EN #news-empty node does not ship the "hidden" attribute` | Yes |
| 15 (no-island) | Inserted `<astro-island></astro-island>` into dist HTML | `assertion 15 — EN built page contains "astro-island"` | Yes |
| 16 (no cluster) | Added `<span class="news-source-count">` to `news.astro` source | `assertion 16 — EN page source contains cluster-markup pattern /news-source-count/` | Yes |
| 17 (F-27 bundling) | Replaced `newsFilterLogic/v1` with `newsFilterLogic-CORRUPTED` in the real shared chunk `newsFilterLogic.BS0afx7K.js` | `assertion 17 — EN page's shipped module script(s) do not contain the FILTER_LOGIC_MARKER literal` | Yes |
| 18a (control presence) | Renamed `id="news-comuna-q"` to `id="news-comuna-qX"` in dist HTML | `assertion 18 — EN built page missing required id="news-comuna-q"` | Yes |
| 18b (token scan) | Reintroduced literal `{n}` in visible text while corrupting the carrier attribute | `assertion 18 — EN: unsubstituted token in rendered markup` | Yes |
| 19 (canonical/routes) | Added `<a href="/news/?family=robos">` to dist HTML | `assertion 19 — EN built page has an internal <a href> containing "?family=": /news/?family=robos` | Yes |
| 20a (innerHTML) | Changed `resultCountEl.textContent =` to `resultCountEl.innerHTML =` in `news.astro` | `assertion 20 — EN source ... contains forbidden DOM sink /innerHTML/` | Yes |
| 20b (set:html count) | Added a second `set:html=` attribute (on a throwaway `<div>`) to `news.astro` | `assertion 20 — EN page has 2 set:html= attribute occurrence(s), expected exactly 1` | Yes |
| 21 (no client:) | Added `client:load` to `#news-empty` in `news.astro` | `assertion 21 — EN page source contains a client: directive` | Yes |

(Removing the `set:html=` attribute entirely correctly fires on assertion 7, which runs earlier in the file and already guards the H-2 escaping call — confirming assertion ordering doesn't mask coverage.)

## Phase-Close Gate — Actual Output

Ran exactly the plan's `<verification>` command (single `;` after `npx astro check`, everything downstream joined by `&&` only — no reordering, no `|| true`):

```
cd site && npx astro check > .astro-check.log 2>&1; node -e "..." && rm -f .astro-check.log && npm run build && npm test && npm run validate && cd .. && python -m pytest -q
```

- **`npm run check` (astro check):** `astro check 4/0 baseline confirmed` — exactly 4 errors / 0 warnings, all pre-existing `ts(7031)` in `ComparatorPairsLinks.astro:28`, unchanged baseline.
- **`npm run build`:** 834 pages built successfully.
- **`npm test` (vitest):** 3 test files, 32 tests, all passed.
- **`npm run validate`:** **16/16 validators passed** — `structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo, figure-registry, avs-b-budget, freshness, facets` all PASS.
  - `freshness`: `PASS freshness: data/incidents/current.json is 3.0 days old (generated: 2026-07-27T14:25:05.303451Z)` — green, at the boundary but under `MAX_AGE_DAYS=3`. **No F-19 exclusion was needed** — the gate closed at the full 16/16, not the 15/16-with-exclusion fallback.
  - `facets`: `PASS facets: 1215 incidents, 8 families observed, 346 communes cross-checked, 3 months in byMonth union, window(today=11,7d=297,30d=1215), TZ-determinism verified, 21 assertions passed`
- **`python -m pytest -q`:** `344 passed, 1 skipped, 1 xfailed, 67 warnings in 133.64s` — exact match to the plan's expected baseline. The 1 xfail is the deliberate Phase 26 gate quarantine (F-08), confirmed not "fixed" (still XFAIL, not XPASS).

No red validator, no F-19 exclusion narrative required, no regression in the Python suite.

## Self-Check

- `site/scripts/validate/facets.mjs` contains assertions 11-21 (21 total): FOUND (grep confirms `assertion 11` through `assertion 21` message strings present)
- `facets.mjs` still registered as validator #16 in `site/scripts/validate/all.mjs`: unchanged (no edits made to `all.mjs`, no sibling validator added)
- Commit `8d9128f`: FOUND in `git log --oneline`
- `npm run validate` real run: 16/16 (confirmed above, not inferred)
- `python -m pytest -q` real run: 344 passed / 1 skipped / 1 xfailed (confirmed above, not inferred from git status)

## Self-Check: PASSED
