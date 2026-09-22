# Phase 28: News Visualizer UI - Pattern Map

**Mapped:** 2026-07-30
**Files analyzed:** 6 (2 created, 4 modified)
**Analogs found:** 6 / 6

Binding sources of record: `28-UI-SPEC.md` (markup/tokens/i18n keys/query-param contract/hide-show mechanism), `28-RESEARCH.md` (data-flow + pitfalls), `28-VALIDATION.md` (F-27: filter logic is imported, not copy-pasted; F-28: self-exclusion facet counts). Where an analog's convention conflicts with these, the binding docs win — flagged explicitly per file below.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `site/src/lib/newsFilterLogic.ts` | utility (pure-function module) | transform | `site/src/lib/newsFacets.ts` (whole file) | exact — same directory, same "published-contract pure module" role |
| `site/src/lib/newsFilterLogic.test.ts` | test | transform | `site/src/lib/newsFacets.test.ts` (whole file, lines 1-80 read) | exact — same test-fixture idioms, same vitest setup |
| `site/src/pages/news.astro` | route/component | request-response (SSG) + event-driven (client script) | itself (existing file, full read) + `site/src/components/RankingTableEnhancer.astro` (inline-script pattern) + `site/src/pages/communes/index.astro:170-307` (client-filter IIFE pattern) | role-match (self) / exact (inline-script-plus-inert-JSON pattern) |
| `site/src/pages/es/noticias.astro` | route/component | request-response (SSG) + event-driven (client script) | `site/src/pages/news.astro` (byte-identical structure per RESEARCH.md, EN mirror) | exact |
| `site/src/config/i18n.ts` | config | CRUD (string map) | itself — `dir_search_placeholder` key insertion (interface:128, EN:330, ES:537) | exact — three-place insertion pattern already established |
| `site/scripts/validate/facets.mjs` | utility (build validator) | batch (build-time assertion) | itself — assertion 7 (lines 249-332) | exact — this is the model, not an external analog |

---

## Pattern Assignments

### `site/src/lib/newsFilterLogic.ts` (utility, transform)

**Analog:** `site/src/lib/newsFacets.ts` (whole file, 253 lines)

**Module-header contract-comment pattern** (`newsFacets.ts:1-31`):
```typescript
/**
 * newsFacets.ts — shared build-time facet-computation module for /news/ and
 * /es/noticias/ (Phase 27, FACET-01..06).
 *
 * Module Published Contract (F-20 — Phase 28 inherits this without re-deriving it):
 * - Facet counts are unfiltered totals over the window — ...
 * ...
 */
```
Mirror this exactly for `newsFilterLogic.ts`: open with a contract-comment block naming the phase (28), the F-27/F-28 Fable decisions it encodes, and every non-obvious invariant (window boundary is inclusive both ends, UTC-anchored, self-exclusion semantics for counts).

**Window-boundary math to port verbatim** (`newsFacets.ts:82-90, 179-216`):
```typescript
function lowerBoundDate(anchorMs: number, days: number): string {
  const ms = anchorMs - days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}
// ...
const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
const lower7 = lowerBoundDate(anchorMs, 6);
const lower30 = lowerBoundDate(anchorMs, 29);
// isToday = inc.date === newestDate; is7d = inc.date >= lower7; is30d = inc.date >= lower30;
```
This is the exact algorithm `newsFilterLogic.ts` must expose as a pure, independently-callable function (e.g. `computeWindowBucket(dateStr, newestDate)` / `computeNewestDate(dates)`) — UTC/string-only arithmetic, never `toLocaleDateString`/`getMonth()`/bare `new Date(y,m,d)` (per RESEARCH.md Q6 and `facets.mjs` assertion 9's TZ-independence proof). VALIDATION.md's falsifiable counterexample table requires a dedicated test that changes the 7-day width to 6 and expects RED — build the function so that width is a named constant, not a magic literal, to make that mutation test meaningful.

**Type-export pattern to mirror** (`newsFacets.ts:36-77`): export small, named interfaces (`FacetBucket`, `WindowFacet`, `FacetKeyEntry`) rather than one large inline type. `newsFilterLogic.ts` should export at minimum: a `FilterParams` type (`{family: string[], region: string[], window: 'today'|'7d'|'30d'|'', q: string}`), `parseFilterParams(search: string): FilterParams`, `serializeFilterParams(params: FilterParams): string`, `norm(s: string): string`, a comuna-match predicate, and the F-28 self-exclusion count routine (signature roughly `computeFacetCounts(cards: CardLike[], active: FilterParams): {family: Record<string,number>, region: Record<string,number>, window: Record<string,number>}`).

**`norm()` — copy the algorithm, NOT the copy-paste convention.** Source: `communes/index.astro:175-176`:
```typescript
const norm = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
```
Per F-27 (VALIDATION.md line 13) the shipped filter logic must BE the unit-tested module, imported — not a copy-pasted twin. This directly overrides RESEARCH.md's "copy-paste `norm()` like `communes/index.astro` does" recommendation (RESEARCH.md lines 178, 326, Q1) — that guidance is now superseded by the later Fable decision. Implement `norm()` once, inside `newsFilterLogic.ts`, exported, and imported by both `.astro` pages' `<script>` blocks. Do not duplicate the function body anywhere.

**Escaping helper to reuse, not reinvent** (`newsFacets.ts:92-105`): if `newsFilterLogic.ts` needs to build any HTML fragment (it should not — filtering is DOM-attribute matching only, no new `innerHTML`), do not add a second escaping utility; there is none needed here since this module never touches `set:html`.

---

### `site/src/lib/newsFilterLogic.test.ts` (test, transform)

**Analog:** `site/src/lib/newsFacets.test.ts` (20-test real spec, lines 1-80 read in full)

**Imports + fixture-builder pattern** (`newsFacets.test.ts:1-33`):
```typescript
import { describe, it, expect, afterEach } from 'vitest';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { computeNewsFacets, escapeForInlineScript, type IncidentLike } from './newsFacets';
import type { CommuneMeta } from './data';

function makeIndex(): CommuneMeta[] {
  return [
    { cut: '13101', name: 'Santiago', slug: 'santiago', region_id: '13', population: 100, low_population: false },
    { cut: '8106', name: 'Lota', slug: 'lota', region_id: '8', population: 50, low_population: false },
  ];
}
```
`newsFilterLogic.test.ts` needs no filesystem fixtures (pure functions, no I/O) — drop the `mkdtempSync`/`afterEach` scaffolding entirely; keep only the `describe`/`it`/`expect` import and a small literal-object fixture builder analogous to `makeIndex()` (e.g. `makeCards()` returning plain objects with the `data-*` attribute values as fields).

**Exhaustive-assertion style to copy** (`newsFacets.test.ts:36-45`):
```typescript
it('Test 1: empty incidents array returns all-empty facets, no throw', () => {
  const result = computeNewsFacets([], makeIndex());
  expect(result).toEqual({ byFamily: [], byRegion: [], byWindow: {...}, byMonth: [], facetKeys: [] });
});
```
Use `toEqual` for exhaustive shape assertions on `parseFilterParams`/`serializeFilterParams` round-trips. VALIDATION.md's per-task command is `npx vitest run src/lib/newsFilterLogic.test.ts src/lib/newsFacets.test.ts` — keep test names numbered/behavior-labeled the same way (`'Test N: <behavior>'`) for consistency with the existing suite's convention.

**Boundary-width test to copy verbatim in structure** (`newsFacets.test.ts:70-80`, Test 4):
```typescript
it('Test 4: window boundaries (today/7d/30d) — newest date 2026-07-28', () => {
  const incidents: IncidentLike[] = [ /* dates spanning the boundary */ ];
  const result = computeNewsFacets(incidents, makeIndex());
  expect(result.byWindow.today.length).toBe(1);
  expect(result.byWindow.sevenDay.length).toBe(2);
  expect(result.byWindow.thirtyDay.length).toBe(3);
});
```
This is the exact shape for the VALIDATION.md-mandated mutation test: "change the window width from 7 to 6 days in `newsFilterLogic.ts` → RED." Write the equivalent test against `newsFilterLogic.ts`'s ported window function, then manually flip 6↔7 once to confirm RED before restoring, per Operating Lesson 11.

**Do NOT reuse:** the `mkdtempSync`/archive-file fixture machinery (`newsFacets.test.ts:21-33`) — that exists only because `computeNewsFacets` reads `archiveDir` from disk; `newsFilterLogic.ts` has no filesystem dependency at all.

---

### `site/src/pages/news.astro` (route/component, request-response SSG + event-driven client script)

**Analog A — inline-script-plus-inert-JSON-node pattern:** `site/src/components/RankingTableEnhancer.astro:56-70`
```astro
<script type="application/json" id="rte-strings" data-locale={locale} set:html={JSON.stringify(strings)}></script>

<script>
(function () {
  'use strict';
  const blob = document.getElementById('rte-strings');
  if (!blob) return;
  const S: {...} = JSON.parse(blob.textContent || '{}');
  ...
})();
</script>
```
`news.astro` already has this exact shape at line 210 for `#news-facets`. Phase 28 extends it (adds `anchorDate` to the same `facetsProjection` object, per RESEARCH.md Q4/Pitfall 4 — do NOT add a second `set:html` node) and adds a SECOND inline `<script>` (no `client:` directive) that imports `newsFilterLogic.ts` and wires the filter bar. Per F-27, this new script uses a real `import { ... } from '../lib/newsFilterLogic'` statement — Astro's plain `<script>` (no `is:inline`) is processed by Vite and supports ES module imports without becoming a hydrated island; this does not violate the "no client: directive" / "no island" constraint validated by `facets.mjs`'s planned `no astro-island in dist` assertion.

**Analog B — existing `#news-facets` node + `facetsProjection` build** (`news.astro:120-136, 207-210`, self, exact lines already in this file):
```typescript
const facets = computeNewsFacets(incidents as unknown as import('../lib/newsFacets').IncidentLike[], loadIndex(), archiveDir);
const facetsProjection = {
  byFamily: facets.byFamily,
  byRegion: facets.byRegion,
  byMonth: facets.byMonth,
  byWindow: { today: facets.byWindow.today.length, sevenDay: facets.byWindow.sevenDay.length, thirtyDay: facets.byWindow.thirtyDay.length },
};
```
```astro
<script type="application/json" id="news-facets" set:html={escapeForInlineScript(JSON.stringify(facetsProjection))}></script>
```
Add `anchorDate: facets.anchorDate` (after adding the field to `NewsFacetIndex`/`computeNewsFacets` return per RESEARCH.md Q4) as one more key in this same object literal — it is automatically covered by the existing `escapeForInlineScript(JSON.stringify(facetsProjection))` call, satisfying `facets.mjs` assertion 7 with zero new escaping call sites.

**Analog C — `.news-card` markup to add `data-*` attributes to** (`news.astro:176-206`, self):
```astro
<article class="news-card">
  <h3 class="news-title">...</h3>
  <p class="news-meta">...</p>
</article>
```
Add per UI-SPEC/RESEARCH.md Q1: `data-family={incident.family ?? ''}`, `data-region-id={cutToRegion.get(String(incident.cut)) ?? ''}`, `data-year-month={yearMonth}` (reuse the existing loop variable — do not recompute), `data-commune-norm={communeInfo ? norm(communeInfo.name) : ''}`, `data-date={incident.date}` (RESEARCH.md's recommended approach for window filtering — avoids a second pre-baked bucket that must stay in sync with `newsFilterLogic.ts`'s window function). Add `id={'month-' + yearMonth}` to the wrapping `<section class="news-month-section">`. This is purely additive — no existing class/attribute renamed, so `facets.mjs`, `newsFacets.test.ts`, and any other validator's DOM assumptions are unaffected (RESEARCH.md line 242).

**Analog D — client-filter IIFE + `hidden`-attribute toggling pattern (algorithm to port, NOT the mixed-mechanism precedent):** `site/src/pages/communes/index.astro:170-307` (full range read)
```typescript
(function () {
  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  // ... query all .citem, filter by data-norm, toggle visibility, update count, highlight
  const initialQ = new URLSearchParams(window.location.search).get('q');
  if (initialQ) { q = initialQ; input.value = initialQ; }  // T-12-01: value assignment only, never innerHTML
  // highlight() slices the TRUSTED data-name attribute around match index — never injects raw query (T-11-05)
})();
```
Structural pieces to mirror in `news.astro`'s new script: read `URLSearchParams(location.search)` synchronously before first paint, query all `.news-card` via `querySelectorAll`, apply a match predicate per filter dimension (imported from `newsFilterLogic.ts`), then toggle visibility and re-render counts/result-count/empty-state.

**What must NOT be copied from this analog:**
1. `communes/index.astro:232, 259, 266, 296` mix `item.style.display = matches ? '' : 'none'` with `activeBlock.setAttribute('hidden', '')` / `azIndex.style.display` — a mixed-mechanism precedent. UI-SPEC §Empty state (line 197) explicitly and deliberately diverges from this: Phase 28 uses the `hidden` attribute EXCLUSIVELY for every element the filter script shows/hides (`.news-card`, `.news-month-section`, `#news-empty`), never `style.display`, so the visible-count predicate stays exactly `!card.hidden`.
2. The inline copy-pasted `norm()` function body — per F-27, import it from `newsFilterLogic.ts` instead of re-declaring it in the page's `<script>` (see the `newsFilterLogic.ts` section above).
3. `communes/index.astro:221, 271` build `<mark>` HTML via `innerHTML = highlight(name)` and `emptyEl.textContent = 'No results for "' + q + '".'` — the second one interpolates the raw query into text content, which is safe (`textContent`, not `innerHTML`) but is NOT the pattern UI-SPEC wants for the empty state: `news_empty_heading`/`news_empty_body` are static i18n strings, not query-echoing text — do not echo `q` into the Phase 28 empty-state copy.
4. Do not add a "view all {family}" link built from `FAMILY_SLUGS` in this filter markup (Pitfall 2, `vida`/`homicide` slug collision) — filtering here is `?family=<key>` query-param only, never a route.

---

### `site/src/pages/es/noticias.astro` (route/component, request-response SSG + event-driven client script)

**Analog:** `site/src/pages/news.astro` (post-Phase-28-edit) — confirmed byte-identical structure to EN today (RESEARCH.md line 206, 273: "both `.astro` files... byte-identical shape, only copy differs"). Apply every pattern above identically, swapping only the ES copy strings (sourced from `ES_STRINGS`, never inline literals per NEWSUI-07) and the ES-locale `toLocaleDateString('es-CL', ...)` call for the anchor-date formatting. `facets.mjs` assertion 7's `SERIALIZATION_SITES`/`DIST_PAGES` arrays (see below) already enforce EN/ES parity at the `escapeForInlineScript` call-site level — extend any new Phase 28 assertion (filter-script parity, i18n key parity) the same two-locale way.

---

### `site/src/config/i18n.ts` (config, CRUD string map)

**Analog:** itself — the existing `dir_search_placeholder` key, present at all three required insertion points:

**1. Interface declaration** (`i18n.ts:128`):
```typescript
export interface I18nStrings {
  // ...
  dir_search_placeholder: string;
  // ...
}
```

**2. EN_STRINGS value** (`i18n.ts:330`):
```typescript
export const EN_STRINGS: I18nStrings = {
  // ...
  dir_search_placeholder: "Filter by name… (e.g. 'la ', 'puerto', 'vina')",
  // ...
};
```

**3. ES_STRINGS value** (`i18n.ts:537`):
```typescript
export const ES_STRINGS: I18nStrings = {
  // ...
  dir_search_placeholder: "Filtra por nombre… (ej. 'la ', 'puerto', 'viña')",
  // ...
};
```

Add all 14 `news_*` keys (`news_filter_heading`, `news_filter_window_label`, `news_window_latest`, `news_window_7d`, `news_window_30d`, `news_window_all`, `news_filter_region_label`, `news_filter_family_label`, `news_search_comuna_label`, `news_search_comuna_placeholder`, `news_result_count`, `news_clear_filters`, `news_empty_heading`, `news_empty_body`, `news_cluster_source_count` — UI-SPEC Copywriting Contract table has the exact EN/ES strings) at all three sites, in the same relative position (grouped together, e.g. near the existing `news_*`-adjacent or `dir_*` keys) so a reviewer can visually diff the three blocks side by side. `news_search_comuna_placeholder` must literally mirror `dir_search_placeholder`'s wording pattern (UI-SPEC line 95) — same ellipsis-plus-examples shape, not a novel phrasing.

**Falsifiable gate this insertion feeds:** VALIDATION.md Wave 0 requires a new `facets.mjs` (or sibling) assertion that every new `news_*` key exists in BOTH `EN_STRINGS` and `ES_STRINGS` — counterexample: delete one ES key → must go RED (see `facets.mjs` section below for the exact both-locales scanning idiom to copy).

---

### `site/scripts/validate/facets.mjs` (utility, build validator, batch)

**Analog:** its own assertion 7 (lines 249-332) — this is the model for any NEW both-locales assertion this phase adds (`anchorDate` correctness, card-count == incident-count, i18n key parity, empty-state node presence, no-island, no-cluster-markup). Quote verbatim as the template:

```javascript
// RR-1 (fix cycle 2), part 1 of 2 — SOURCE-level guard on the H-2 escaping.
//
// The re-review proposed catching a reverted escaping by asserting the rendered
// node contains no raw `<`. Measured: that does NOT work. ... The only check that
// actually detects the control disappearing is a source-level one, so both
// guards are kept: this one catches the revert, the dist-level `<` check below
// catches a hostile payload that somehow reaches the page unescaped.
const SERIALIZATION_SITES = [
  ['EN', path.join(SITE_ROOT, 'src', 'pages', 'news.astro')],
  ['ES', path.join(SITE_ROOT, 'src', 'pages', 'es', 'noticias.astro')],
];
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  if (!existsSync(pagePath)) {
    fail(`assertion 7 — ${locale} news page source not found at ${pagePath}`);
  }
  const pageSrc = readFileSync(pagePath, 'utf-8');
  if (!pageSrc.includes('escapeForInlineScript(JSON.stringify(facetsProjection))')) {
    fail(`assertion 7 — ${locale} news page does not wrap the #news-facets payload in ...`);
  }
}
```
and the paired dist-level check right after it (lines 280-332):
```javascript
const DIST_PAGES = [
  ['EN', path.join(SITE_ROOT, 'dist', 'news', 'index.html')],
  ['ES', path.join(SITE_ROOT, 'dist', 'es', 'noticias', 'index.html')],
];
for (const [locale, distPath] of DIST_PAGES) {
  if (!existsSync(distPath)) {
    fail(`assertion N — ${locale} built page not found at ${distPath} (requires a prior build)`);
  }
  const distHtml = readFileSync(distPath, 'utf-8');
  // ... regex-match the relevant node, parse, compare against an independently-computed expected value
}
```

**Pattern to replicate for each new Wave-0 assertion (per VALIDATION.md's falsifiability table):**
- **Always iterate `[locale, path]` pairs for BOTH `news.astro`/`es/noticias.astro` (source) and BOTH `dist/news/index.html`/`dist/es/noticias/index.html` (built output)** — never check only EN (this is exactly the RR-1 defect this assertion was created to fix: "no validator ever opened dist/es/noticias/index.html... could drift... without any gate noticing", lines 241-243).
- Use `fail(...)` with a message string starting `assertion N — ${locale} ...` (consistent numbering/naming convention across the file).
- For the card-count assertion: match on the opening tag `class="news-card"` specifically (per VALIDATION.md's counterexample note), not a bare substring — mirror the existing `facetsMatch` regex idiom (`distHtml.match(/<script type="application\/json" id="news-facets">([\s\S]*?)<\/script>/)`) as the template for any new targeted regex extraction against dist HTML.
- For the i18n key-parity assertion: this is a NEW pattern not present in `facets.mjs` today (it currently only checks `#news-facets` content, not `i18n.ts` directly) — write it as a new numbered assertion block that imports/reads `i18n.ts`'s `EN_STRINGS`/`ES_STRINGS` object keys and diffs the `news_*`-prefixed key sets, `fail()`-ing on any asymmetry. If a NEW sibling validator file is added instead of extending `facets.mjs`, VALIDATION.md requires registering it in `all.mjs` and updating every hardcoded "16 validators" count in the same commit (F-21 lesson).

---

## Shared Patterns

### Hide/show mechanism — `hidden` attribute exclusively
**Source:** UI-SPEC §Empty state (line 197), deliberately diverging from `communes/index.astro`'s `style.display` precedent.
**Apply to:** `news.astro`, `es/noticias.astro` — every element the new filter script shows/hides (`.news-card`, `.news-month-section`, `#news-empty`).
```javascript
el.hidden = !matches;         // never el.style.display = matches ? '' : 'none'
const visible = !card.hidden; // the ONE predicate used everywhere counts are derived
```

### LLM/data-derived string escaping — `escapeForInlineScript`
**Source:** `site/src/lib/newsFacets.ts:92-105`, consumed at `news.astro:210`.
**Apply to:** any new field added to `facetsProjection` (e.g. `anchorDate`) — folds into the existing single `escapeForInlineScript(JSON.stringify(facetsProjection))` call; never add a second `set:html` site.
```typescript
export function escapeForInlineScript(json: string): string {
  return json.replace(/</g, '\\u003c');
}
```

### Trusted-vs-untrusted DOM writes
**Source:** `communes/index.astro:201-221` (`highlight()`/`applyHighlight()`) — algorithm reusable, mechanism reusable, but scope narrowed by UI-SPEC.
**Apply to:** `news.astro`, `es/noticias.astro`. `textContent` for every classifier/RSS-derived string (`family`, `title_en`/`title_es`, `outlet`) — never `innerHTML`. The one exception (slicing a TRUSTED `data-name`/`data-commune-norm` attribute for highlight markup) is scoped exclusively to the comuna search, never to `family`/`title`/`outlet`.

### Query-param round-trip via `history.replaceState`
**Source:** STATE.md Phase 25 P1-2 precedent on `/compare/` (not directly read in this pass — cited in both UI-SPEC line 191 and RESEARCH.md line 23/122 as the established precedent); structurally same idiom as `communes/index.astro:279-284`'s `?q=` pre-population.
**Apply to:** `news.astro`, `es/noticias.astro`.
```javascript
const initialQ = new URLSearchParams(window.location.search).get('q');
if (initialQ) { q = initialQ; input.value = initialQ; }   // T-12-01: value assignment only, never innerHTML
// ... on filter change:
history.replaceState(null, '', newURL);  // never pushState — filtering is not a navigation event
```

---

## No Analog Found

None — all 6 files have a strong (exact or role-match) analog in the existing codebase.

## Metadata

**Analog search scope:** `site/src/lib/`, `site/src/pages/`, `site/src/pages/es/`, `site/src/pages/communes/`, `site/src/components/`, `site/src/config/`, `site/scripts/validate/`
**Files scanned:** `newsFacets.ts`, `newsFacets.test.ts`, `news.astro`, `communes/index.astro` (lines 150-310), `RankingTableEnhancer.astro`, `i18n.ts` (grep), `facets.mjs` (lines 240-340)
**Pattern extraction date:** 2026-07-30
