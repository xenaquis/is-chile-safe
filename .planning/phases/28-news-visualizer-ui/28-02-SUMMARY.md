---
phase: 28-news-visualizer-ui
plan: 02
subsystem: news-filtering-ui
tags: [news, filtering, i18n, astro, vanilla-js]
dependency-graph:
  requires:
    - site/src/lib/newsFilterLogic.ts (Plan 28-01)
    - site/src/lib/newsFacets.ts NewsFacetIndex.anchorDate (Plan 28-01)
    - 15 news_* i18n keys (Plan 28-01)
  provides:
    - site/src/pages/news.astro filter-bar UI, data-* attributes, client-side filtering script
    - site/src/pages/es/noticias.astro identical ES-locale wiring
  affects:
    - Plan 28-03 (phase-close gate) asserts card counts, FILTER_LOGIC_MARKER presence, no-astro-island, i18n parity against these two files
tech-stack:
  added: []
  patterns:
    - "Progressive-enhancement filter bar: server-rendered <details>/<fieldset>, hidden-attribute-only show/hide, no client: directive"
    - "F-28 self-exclusion facet counts recomputed client-side from card data-* attributes (F-29, no facetKeys serialization)"
key-files:
  created: []
  modified:
    - site/src/pages/news.astro
    - site/src/pages/es/noticias.astro
decisions:
  - "regionNames Map built once per page from facets.byRegion via loadRegion(regionFileId(...)).name — CommuneMeta has no region-name field, so this is the only correct source (at most 16 lookups)"
  - "F-32 server-side substitution done via three frontmatter consts (anchorLabel, resultCountText, windowLatestText) computed with toLocaleDateString(..., { timeZone: 'UTC', month: 'short', day: 'numeric' }) — mandatory UTC to avoid a one-day-off label for Chilean readers"
  - "The one deliberate {n} token that ships in indexed HTML is the data-result-count-template attribute on #news-result-count, read client-side via .dataset.resultCountTemplate for live re-substitution on every filter change — the visible textContent itself is always server-substituted"
  - "TS null-narrowing fix: document.getElementById('news-filters') is captured into a non-null-typed const (filtersEl: HTMLElement) immediately after the early-return guard, because narrowing does not persist across the nested applyFilters()/event-listener closures — without this astro check reported 5 new ts(18047) errors above the 4-error baseline"
metrics:
  duration: "~40 minutes"
  completed: "2026-07-30"
---

# Phase 28 Plan 02: News Visualizer UI Wiring Summary

One-liner: Wires the UI-SPEC filter bar (time/region/family/comuna-search, count-in-its-own-span markup) onto both `/news/` and `/es/noticias/` as pure progressive enhancement — every one of the 1,215 incidents stays server-rendered and visible with JS disabled, filtering and per-option counts are driven entirely by an imported `newsFilterLogic.ts` client script reading `data-*` attributes already present on each card.

## What Was Built

### Task 1 — `site/src/pages/news.astro`
- Imported `loadRegion`/`regionFileId` (data.ts), `norm`/`FILTER_LOGIC_MARKER` (newsFilterLogic.ts), `EN_STRINGS as t` (i18n.ts).
- Added `cutToRegion` map (mirrors newsFacets.ts's internal map, baked into markup) and `regionNames` map (`loadRegion(regionFileId(r.regionId)).name`, at most 16 lookups).
- Added `anchorDate: facets.anchorDate` to `facetsProjection` — folds into the existing single `escapeForInlineScript(JSON.stringify(facetsProjection))` call; `facetKeys` deliberately absent (F-29).
- F-32 server-side substitution: `anchorLabel` (UTC-formatted), `resultCountText`, `windowLatestText` computed in frontmatter — no literal `{n}`/`{date}` ships in the rendered HTML except the one deliberate `data-result-count-template` carrier.
- Added 5 `data-*` attributes to every `.news-card` (`data-family`, `data-region-id`, `data-year-month`, `data-commune-norm`, `data-date`) and `id={'month-' + yearMonth}` on each `.news-month-section`.
- Inserted the `<details id="news-filters" open>` filter bar: window radios (today/7d/30d/all, all four with their own `<span class="filter-count">`), region checkboxes, family checkboxes, comuna `<input type="search">`, result-count span (`role="status" aria-live="polite"`), clear-filters button.
- Added `<div id="news-empty" hidden>` with `news_empty_heading`/`news_empty_body` as plain `<p>` text (no heading tag).
- Added a second inline `<script>` (no `client:`, no `is:inline`) that imports `parseFilterParams`, `serializeFilterParams`, `norm`, `cardMatchesFilters`, `computeFacetCounts`, `FILTER_LOGIC_MARKER` from `'../lib/newsFilterLogic'`; sets `data-filter-logic={FILTER_LOGIC_MARKER}` on `#news-filters`; reads `anchorDate` from the `#news-facets` JSON node; builds `CardFilterState[]` from card `data-*` (F-29 count source, no `facetKeys` transport); pre-populates controls from `parseFilterParams(location.search)`; `applyFilters()` sets `card.hidden`/`section.hidden`/`emptyEl.hidden` exclusively via the `hidden` attribute (never `style.display`), recomputes F-28 self-exclusion counts per dimension and writes them into each `span.filter-count`'s `textContent` only (never the `<label>`'s), updates `#news-result-count` via the `data-result-count-template` attribute, and syncs the URL with `history.replaceState` (never `pushState`).
- Added filter-bar CSS to the `<style>` block, reusing existing tokens (`--xs/--sm/--md/--lg/--xl`, `--primary`, `--line`, `--text-label/--text-heading`), `min-height: 44px` touch targets, `.filter-chip:has(input:checked)` for the accent-selected state, single ≤480px stacking breakpoint.
- Added `site/.astro-check.log` line already present in `site/.gitignore` (no change needed — verified pre-existing).

### Task 2 — `site/src/pages/es/noticias.astro`
Applied every Task 1 change with the required differences: import paths one level deeper (`'../../lib/newsFilterLogic'`, `'../../lib/data'`, `'../../config/i18n.ts'`); `ES_STRINGS as t`; region labels wrapped in `regionNameEs(loadRegion(regionFileId(r.regionId)).name)`; anchor-date formatted with `toLocaleDateString('es-CL', { timeZone: 'UTC', month: 'short', day: 'numeric' })`; commune links point at `/es/comuna/`; `title_es` used instead of `title_en`. Query-param names/values (`family`, `region`, `window`, `q`) are byte-identical to EN — only rendered labels differ.

**EN/ES structural diff (recorded per task instruction):** ran a normalized diff (import depth, locale strings, `FAMILY_LABELS_EN/ES`, `en-US`/`es-CL`, `title_en`/`title_es`, `/commune/`/`/es/comuna/` all masked). Remaining differences are exclusively: file-header doc comments (EN vs ES prose), the pre-existing `formattedDate` block ordering (sits before vs. after the commune-lookup block — pre-existing drift noted in the plan, not introduced here), inline code comments (EN vs ES), and the four required substitutions (import depth, `t` source, `regionNameEs` wrap, locale string). No new structural divergence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `filtersEl` TS null-narrowing lost across closures**
- **Found during:** Task 1 verify (`npx astro check`)
- **Issue:** `const filtersEl = document.getElementById('news-filters'); if (!filtersEl) return;` narrows `filtersEl` to `HTMLElement` only within the same function scope. Because `applyFilters()` and the event-listener callbacks are nested closures, TypeScript does not retain that narrowing there, producing 5 new `ts(18047)` "possibly null" errors — pushing the error count from the 4-error baseline to 9.
- **Fix:** Captured the checked value into a separately-typed `const filtersEl: HTMLElement = filtersElMaybe;` immediately after the guard, so every closure sees the non-null type directly.
- **Files modified:** `site/src/pages/news.astro`, `site/src/pages/es/noticias.astro` (same pattern applied to both from the start in Task 2, so ES never hit the 9-error state)
- **Commit:** `45293b6` (Task 1), `9283ce8` (Task 2)

No architectural deviations. No auth gates encountered.

## Self-Check

- `site/src/pages/news.astro` contains `from '../lib/newsFilterLogic'`: FOUND
- `site/src/pages/es/noticias.astro` contains `from '../../lib/newsFilterLogic'`: FOUND
- `dist/news/index.html` card count: 1215 (matches `current.json` incident count)
- `dist/es/noticias/index.html` card count: 1215
- Both dist pages: no literal `{date}`; the only literal `{n}` is inside `data-result-count-template="..."` (the deliberate F-32 exception)
- Both dist pages emit an external `_astro/*.js` module chunk (not an inline `<script type="module">` body) — the bundled `newsFilterLogic.ts` import exceeded Vite's 4096-byte inline threshold, consistent with Plan 28-01's probe finding that either emission shape is acceptable as long as `FILTER_LOGIC_MARKER` is discoverable in the shipped output
- Commit `45293b6` (Task 1): FOUND in `git log --oneline`
- Commit `9283ce8` (Task 2): FOUND in `git log --oneline`

## Full-Suite Verification (post-Wave)

`cd site && npx astro check > .astro-check.log 2>&1 && node <baseline-assertion> && npm run build && npm test` — chained, run twice (once per task), both times:
- `astro check`: 4-error/0-warning baseline unchanged (all 4 pre-existing `ts(7031)` in `ComparatorPairsLinks.astro:28`).
- `npm run build`: 834 pages built successfully both times.
- `npm test` (vitest): 3 test files, 32 tests, all passed both times.

## Self-Check: PASSED
