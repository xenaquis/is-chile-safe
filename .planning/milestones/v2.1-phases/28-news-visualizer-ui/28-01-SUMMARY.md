---
phase: 28-news-visualizer-ui
plan: 01
subsystem: news-filtering-logic
tags: [news, i18n, vitest, build-probe]
dependency-graph:
  requires: []
  provides:
    - site/src/lib/newsFilterLogic.ts (parseFilterParams, serializeFilterParams, norm, matchesWindow, computeNewestDate, cardMatchesFilters, computeFacetCounts, FILTER_LOGIC_MARKER, WINDOW_7D_WIDTH_DAYS, WINDOW_30D_WIDTH_DAYS)
    - site/src/lib/newsFacets.ts NewsFacetIndex.anchorDate
    - 15 news_* i18n keys in I18nStrings/EN_STRINGS/ES_STRINGS
    - F-27 bundling assumption empirically settled (see Task 0 Probe Findings)
  affects:
    - Plan 28-02 (Wave 2 page wiring) imports newsFilterLogic.ts and reads facets.anchorDate + all news_* keys with zero additional contract decisions
tech-stack:
  added: []
  patterns:
    - "Pure-function module with zero I/O, mirroring newsFacets.ts's published-contract style"
    - "F-28 self-exclusion facet counting (excludeDimension parameter)"
key-files:
  created:
    - site/src/lib/newsFilterLogic.ts
    - site/src/lib/newsFilterLogic.test.ts
  modified:
    - site/src/lib/newsFacets.ts
    - site/src/lib/newsFacets.test.ts
    - site/src/config/i18n.ts
decisions:
  - "Task 0 probe page was renamed from _f27probe.astro to f27probe.astro mid-task (Rule 3 blocking-issue fix) because Astro silently excludes underscore-prefixed files from page routing — the plan's literal filename would never have been built at all"
  - "F-27 bundling assumption CONFIRMED: a bare <script> (no client:/is:inline) importing from a sibling lib module IS bundled by Astro/Vite, and — because the resulting chunk is under Vite's 4096-byte assetsInlineLimit — it is emitted INLINE in the page HTML, not as a separate src= chunk"
metrics:
  duration: "~15 minutes"
  completed: "2026-07-30"
---

# Phase 28 Plan 01: News Filter Logic + anchorDate + i18n keys Summary

One-liner: Ships the ONE pure, unit-tested filter-logic module (`newsFilterLogic.ts`) both news pages will import, publishes `newsFacets.ts`'s previously-internal `newestDate` as `anchorDate`, adds all 15 bilingual `news_*` i18n keys, and empirically proves (not asserts) that Astro bundles a bare-`<script>` ES-module import.

## What Was Built

### Task 1 — `site/src/lib/newsFilterLogic.ts` + `newsFilterLogic.test.ts`
Every export from the plan's Interfaces block: `WINDOW_7D_WIDTH_DAYS`/`WINDOW_30D_WIDTH_DAYS` named constants, `FILTER_LOGIC_MARKER` string literal, `norm()`, `parseFilterParams`/`serializeFilterParams`, `computeNewestDate`, `matchesWindow`, `cardMatchesFilters` (F-28 self-exclusion via `excludeDimension`), `computeFacetCounts`. 11 vitest cases. Both mandated mutation tests were manually performed:
- Flipped `WINDOW_7D_WIDTH_DAYS` 7→6: Test 7 went RED (`expected false to be true`). Reverted to 7: GREEN restored (11/11 pass).
- Flipped `computeFacetCounts` to call `cardMatchesFilters(card, active, newestDate, undefined)` (i.e. apply every filter, defeating self-exclusion): Test 9 went RED (`{'8': 0}` vs expected `{'8': 1}`). Reverted: GREEN restored (11/11 pass).

### Task 0 — F-27/F-31 bundling probe (executed after Task 1, per plan's stated conceptual-vs-execution-order note)
Created throwaway `site/src/lib/_f27probeModule.ts` (`export const PROBE_MARKER = 'f27probe/v1';`) and a throwaway probe page.

**Deviation (Rule 3 — blocking issue, auto-fixed):** the plan specified the probe page path as `site/src/pages/_f27probe.astro`. Astro's routing convention silently **excludes any file/directory whose name starts with `_`** from page generation — the first build with that filename produced 834 pages (the pre-existing count) with `dist/_f27probe` never created at all, which would have made the probe execute nothing and prove nothing. Renamed to `site/src/pages/f27probe.astro` (no leading underscore) so the page actually built; the throwaway module in `src/lib/` kept its `_` prefix since `src/lib` is not part of Astro's file-based routing. Rebuilt: 835 pages (834 + 1 probe), confirming the page now really exists.

**Probe findings (recorded per the plan's 5-point checklist):**
1. **Build succeeded.**
2. **Emission shape:** `dist/f27probe/index.html` contains a fully **inline** `<script type="module">…</script>` body — NOT a `<script type="module" src="/_astro/…">` reference. Full file content: `<!DOCTYPE html><script type="module">const o="f27probe/v1";console.log(o);</script>`.
3. **Marker presence:** the literal `f27probe/v1` string DOES appear in the shipped JS, preserved verbatim as a string literal even though the local identifier `PROBE_MARKER` was mangled to `o` (esbuild minification, matching the precedent already noted in the interfaces block for `RankingTableEnhancer`/`communes/index.astro`).
4. **Byte size:** the emitted `<script>…</script>` tag is 69 bytes total; the full page HTML is 83 bytes. Well under Vite's default 4096-byte `assetsInlineLimit`, which is why Astro chose to inline the chunk rather than emit a separate `src=` file.
5. **No `astro-island` marker:** confirmed absent (`grep -c astro-island` → 0 matches).

**Conclusion: F-27's bundling assumption is CONFIRMED, not falsified.** A bare `<script>` (no `client:`/`is:inline`) importing from a sibling `lib/` module IS processed by Vite and bundled into the page — in this small-probe case, inlined directly into the HTML because the resulting chunk is tiny. Plan 28-02's real `newsFilterLogic.ts` import will be larger; if its bundled chunk exceeds 4096 bytes it will instead ship as a separate `src="/_astro/….js"` file rather than inline — either way the import is bundled and the literal `FILTER_LOGIC_MARKER` string will be discoverable in the shipped output (inline body or referenced chunk), which is exactly the guarantee Plan 28-03's assertion 17 needs.

Cleanup: both throwaway files deleted, rebuild returned to 834 pages, `git status --short` showed no trace of the throwaway files (they were never staged/committed — no cleanup commit was needed), and `node scripts/validate/facets.mjs` exited 0 (`PASS facets: 1215 incidents, 8 families observed, 346 communes cross-checked, 3 months in byMonth union, window(today=11,7d=297,30d=1215), TZ-determinism verified`).

### Task 2 — `newsFacets.ts` `anchorDate` field
Added `anchorDate: string | null;` to `NewsFacetIndex` (after `facetKeys`) and `anchorDate: newestDate` to the `computeNewsFacets` return statement — pure exposure of the existing local, no new computation. Updated Test 1's exhaustive `toEqual` to include `anchorDate: null`, added Test 12 asserting `anchorDate === '2026-07-27'` for a 3-incident fixture. Full suite: 14/14 pass (13 existing + 1 new).

### Task 3 — 15 `news_*` i18n keys
Inserted at all three sites (`I18nStrings` interface after `dir_empty`, `EN_STRINGS` after `dir_empty`, `ES_STRINGS` after `dir_empty`), grouped together for side-by-side diffing. Copy taken verbatim from the amended UI-SPEC Copywriting Contract table, including the 2026-07-30 rename (`news_window_7d_label`/`news_window_30d_label`, no `{n}` token — count moved to a dedicated `<span class="filter-count">`). `news_search_comuna_placeholder` mirrors `dir_search_placeholder`'s ellipsis-plus-examples pattern. `news_cluster_source_count` shipped as a reserved, unwired key (NEWSUI-05 NO-GO).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Task 0 probe page renamed from `_f27probe.astro` to `f27probe.astro`**
- **Found during:** Task 0
- **Issue:** Astro's file-based router silently excludes any page file/directory whose name starts with `_` from routing (this is documented Astro convention for "private" files, not a bug in Astro). The plan's literal filename `site/src/pages/_f27probe.astro` would never have produced a route or a `dist/_f27probe/` output — the probe's build-and-inspect step would have silently found nothing to inspect.
- **Fix:** Renamed the page file to `site/src/pages/f27probe.astro` (no leading underscore). Kept the module file `site/src/lib/_f27probeModule.ts` with its underscore prefix, since `src/lib/` is not routed by Astro at all — only the routing exclusion applied to the page path.
- **Files modified:** `site/src/pages/_f27probe.astro` → `site/src/pages/f27probe.astro` (both throwaway, deleted by end of task per plan's `<done>` criteria)
- **Commit:** none (throwaway files were never git-added/committed; deleted before any commit touched them)

**2. [Environment quirk, not a code defect] Task 3's literal `<automated>` verify command as written in PLAN.md does not execute correctly through this session's Bash tool**
- **Found during:** Task 3 verification
- **Issue:** The plan's verify command passes a JS string to `node -e "..."` inside a double-quoted shell argument, using `\\\\b`/`\\\\s` (4 backslashes) intending to reach the JS engine as `\b`/`\s` (regex word-boundary/whitespace escapes). Empirically, in this Windows/git-bash Bash tool, that double-quoted argument loses backslash pairs before reaching `node -e`'s argument parser — confirmed via a minimal isolated test (`node -e "console.log(JSON.stringify('\\\\b'))"` printed `"\b"` i.e. a literal backspace character, not `"\\b"`), causing every `new RegExp(...)` in the script to build a non-matching pattern and report all 15 keys as missing even though they are verbatim present.
- **Verification performed instead:** Wrote the identical parsing/regex logic (unchanged) to a script file via the Write tool (which does not go through shell backslash-collapsing) and ran it with `node <script-file>`. Result: `all 15 keys present in interface + EN + ES`, exit 0.
- **Files modified:** none (this is a verification-method note, not a code change)
- **Commit:** none

No architectural deviations. No auth gates encountered.

## Self-Check

- `site/src/lib/newsFilterLogic.ts` exists: FOUND
- `site/src/lib/newsFilterLogic.test.ts` exists: FOUND
- `site/src/lib/newsFacets.ts` contains `anchorDate`: FOUND (grep confirmed both interface field and return-statement assignment)
- `site/src/config/i18n.ts` contains all 15 `news_*` keys in interface + EN_STRINGS + ES_STRINGS: FOUND (confirmed via equivalent script, see Deviation 2)
- Commit `419ff8a` (Task 1): FOUND in `git log --oneline`
- Commit `c662da5` (Task 2): FOUND in `git log --oneline`
- Commit `19e4f39` (Task 3): FOUND in `git log --oneline`

## Full-Suite Verification (post-Wave)

`cd site && npm run build && npm test && npm run validate` — chained, one command, as VALIDATION.md requires:
- Build: 834 pages built successfully (back to baseline after probe cleanup).
- `npm test` (vitest): **3 test files, 32 tests, all passed** (11 newsFilterLogic + 14 newsFacets + 7 formatNumber).
- `npm run validate`: **16/16 validators passed** (structure, commune, rollout, region, crime, hreflang, schema, map, forbidden-language, coverage, spine, seo, figure-registry, avs-b-budget, freshness, facets).
- `npm run check`: baseline unchanged — 4 errors (all pre-existing `ts(7031)` in `ComparatorPairsLinks.astro:28`), 0 warnings.

## Self-Check: PASSED
