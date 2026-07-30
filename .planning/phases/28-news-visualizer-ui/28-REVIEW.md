---
phase: 28-news-visualizer-ui
reviewed: 2026-07-30T00:00:00Z
depth: deep
files_reviewed: 7
files_reviewed_list:
  - site/src/lib/newsFilterLogic.ts
  - site/src/lib/newsFilterLogic.test.ts
  - site/src/lib/newsFacets.ts
  - site/src/lib/newsFacets.test.ts
  - site/src/config/i18n.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - site/scripts/validate/facets.mjs
findings:
  critical: 0
  warning: 8
  info: 6
  total: 14
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-07-30
**Depth:** deep (cross-file: module ↔ both pages ↔ validator ↔ dist)
**Files Reviewed:** 7 source + 1 validator
**Status:** issues_found — 3 must-fix before close, 5 should-fix, 6 carry

## Summary

Phase 28 is materially sound on its two highest-risk axes. I verified by execution rather
than by reading the summaries:

- **NEWSUI-02 holds in the shipped artifact.** `grep -c 'news-card" hidden' dist/news/index.html`
  returns **0**; every one of the 1,215 `<article class="news-card">` ships visible, and no
  author CSS rule sets `display` on `.news-card`, `.news-month-section` or `#news-empty`, so the
  UA `[hidden]{display:none}` rule is the only mechanism (F-26 satisfied). There is no
  server-side read of the query string. The JS-error failure path is benign: `applyFilters()` is
  built only from pure functions plus `el.hidden` writes; the only statement that can realistically
  throw (`history.replaceState`, sandboxed/`file:` contexts) is the **last** statement, after the
  cards, the month sections, the empty state and the count have all been settled.
- **Window semantics are exact.** `newsFilterLogic.ts:129/133` uses `WINDOW_*_WIDTH_DAYS - 1`
  = 6 / 29, byte-equivalent to `newsFacets.ts:191-192`'s `lower7 = lowerBoundDate(anchorMs, 6)` /
  `lower30 = …, 29)`, same UTC string arithmetic, same `>=` inclusivity, and `today` is
  `date === newestDate` in both. Chip counts and the list they filter agree.
- **F-28 self-exclusion is real**, and reduces to F-20 marginals at the no-filter state: with
  `active` all-empty, `cardMatchesFilters(..., excludeDimension)` returns `true` for every card,
  so `computeFacetCounts` degenerates to per-key marginal totals — identical to the server-rendered
  `facets.byFamily` / `byRegion` / `byWindow.*.length` values it overwrites on load. No first-paint
  count flicker.
- **XSS is clean.** Every data-derived DOM write is `textContent` (`news.astro:405,426,443,458`);
  the only value assignments are `input.checked` and `comunaInput.value`. `escapeForInlineScript`
  is still wrapped around the `#news-facets` payload on both pages and is guarded at source level
  by assertion 7. `?q=` is never interpolated into markup and there is no highlight path.
- **EN/ES drift: none.** A full `diff news.astro es/noticias.astro` yields only import depth,
  `ES_STRINGS`, `FAMILY_LABELS_ES`, `regionNameEs()`, translated prose/comments, the `/es/comuna/`
  link prefix, `title_es` vs `title_en`, and a cosmetic reordering of two identical CSS blocks
  (`.freshness`/`.empty-state`). Zero behavioral divergence in the script block.
- **All 11 new validator assertions can fail** — I could not construct a tautology among 11–21.
  Two are weakened by regex defects (WR-04, WR-05) and one leaves the phase's own headline
  invariant unguarded (WR-02), but none is dead.

The defects below are concentrated in (a) one real user-visible URL bug, (b) gaps between what
the gates claim to cover and what they can actually detect, and (c) test coverage that repeats
Phase 27's "boundary width completely unpinned while the suite reads green" pattern for the 30-day
window.

## Narrative Findings (AI reviewer)

### Must fix before Phase 28 closes

#### WR-01 (HIGH) — `history.replaceState` discards every non-filter query param and leaves a bare `?`

**File:** `site/src/pages/news.astro:461`, `site/src/pages/es/noticias.astro:461`

```js
history.replaceState(null, '', '?' + serializeFilterParams(active));
```

`serializeFilterParams` (`newsFilterLogic.ts:83-90`) constructs a **fresh** `URLSearchParams` and
emits only `family|region|window|q`. `applyFilters()` runs unconditionally at the end of the IIFE
(`news.astro:508`), so on **every** JS-enabled page load the URL is rewritten from whatever it was
to only those four params.

Two concrete failures:

1. **Attribution/tracking loss.** A visitor arriving at `/news/?utm_source=newsletter&utm_medium=email`
   or `/news/?ref=…` has those params silently deleted from `location.href` before most deferred
   analytics/AdSense code reads them. This is a data-loss bug on the site's only monetization-relevant
   surface, and it is entirely invisible to every existing gate (assertion 19 only inspects rendered
   `<a href>`s and the canonical, never runtime URL rewriting).
2. **Bare `?`.** With no filters active, `serializeFilterParams` returns `''`, so the argument is the
   single character `'?'`. Per URL resolution that yields `/news/?` — every visitor's address bar and
   every copy-pasted/shared link acquires a trailing `?`. Test 5 in the spec round-trips three
   *non-empty* inputs and never exercises the empty case, which is exactly why this shipped.

**Fix** (both pages, identical edit):

```js
const qs = serializeFilterParams(active);
history.replaceState(
  null,
  '',
  qs ? location.pathname + '?' + qs : location.pathname
);
```

Preserving unknown params instead of dropping them is the stricter fix and is preferable:
build the new search from `new URLSearchParams(location.search)`, delete/set only the four
filter keys, and serialize that. Add a vitest case pinning
`serializeFilterParams({family:[],region:[],window:'',q:''}) === ''` so the empty case is covered.

#### WR-02 (HIGH) — no gate proves the cards ship un-hidden; assertion 12 counts hidden cards as present

**File:** `site/scripts/validate/facets.mjs:527-536`

```js
const cardMatches = distHtml.match(/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"/g) ?? [];
if (cardMatches.length !== incidents.length) { … }
```

The regex terminates at the `class` attribute and never inspects the remaining attributes.
An `<article class="news-card" hidden …>` matches identically. So the phase's single most
important requirement — **NEWSUI-02: with JS disabled all 1,215 incidents remain visible** —
has no automated guard at all. Assertion 14 checks `hidden` on `#news-empty` (the one node that
*should* have it) and nothing checks the ~1,215 nodes that must *not*. A future refactor that
server-renders `hidden` from a query param, or adds `.news-card{display:none}` pre-JS, closes
21/21 green.

**Fix:** add to the assertion-12 loop, plus a CSS check:

```js
if (/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"[^>]*\shidden[\s>]/.test(distHtml)) {
  fail(`assertion 12 — ${locale} ships a .news-card with the hidden attribute (NEWSUI-02 violation)`);
}
if (/<section\b[^>]*\bclass="[^"]*\bnews-month-section\b[^"]*"[^>]*\shidden[\s>]/.test(distHtml)) {
  fail(`assertion 12 — ${locale} ships a hidden .news-month-section (NEWSUI-02 violation)`);
}
// author CSS must not override display on the hidden-controlled nodes
if (/\.news-card[^{}]*\{[^}]*display\s*:/.test(distHtml)) {
  fail(`assertion 12 — ${locale} author CSS sets display on .news-card, defeating [hidden]`);
}
```

Falsifiable counterexample: add `hidden` to the `<article>` in `news.astro:285-292`, rebuild → RED.
Restore → GREEN.

#### WR-03 (HIGH) — the 30-day boundary and the `today` predicate are entirely unpinned by the spec

**File:** `site/src/lib/newsFilterLogic.test.ts:72-86`

Test 7 pins the 7-day boundary correctly (inclusive at anchor−6, exclusive at anchor−7) and even
asserts `WINDOW_7D_WIDTH_DAYS === 7`. But:

- `WINDOW_30D_WIDTH_DAYS` is **never imported and never asserted**. Mutating
  `newsFilterLogic.ts:28` to `31` (or `newsFilterLogic.ts:133` to `WINDOW_30D_WIDTH_DAYS`, dropping
  the `- 1`) leaves the suite at 32/32 green while the "Last 30 days" chip and the list it filters
  both silently diverge from `newsFacets.ts:192`'s server-side `lower30`. That is precisely the
  Phase 27 failure the phase brief names ("a 7-day window whose boundary width was completely
  unpinned while the suite read 16/16"), reproduced one window over.
- `matchesWindow(date, newest, 'today')` is never called in the spec. Mutating line 125 to
  `dateStr >= newestDate` or `>=`/`<=` variants is undetected.
- `computeFacetCounts(..., 'window', ['today','7d','30d'])` — the branch at line 200-201 that
  makes the window chips' counts work — is never exercised. Test 9 only covers `region` and `family`.

**Fix:** add three cases (mutation-verified before committing):

```ts
it('30d boundary is inclusive at width-1 days back, exclusive one further', () => {
  expect(WINDOW_30D_WIDTH_DAYS).toBe(30);
  expect(matchesWindow('2026-06-29', '2026-07-28', '30d')).toBe(true);  // anchor-29
  expect(matchesWindow('2026-06-28', '2026-07-28', '30d')).toBe(false); // anchor-30
});
it('today matches only the anchor date exactly', () => {
  expect(matchesWindow('2026-07-28', '2026-07-28', 'today')).toBe(true);
  expect(matchesWindow('2026-07-27', '2026-07-28', 'today')).toBe(false);
});
it('computeFacetCounts window dimension uses matchesWindow per key', () => {
  const cards = makeCards();
  const newest = computeNewestDate(cards.map(c => c.date));
  expect(computeFacetCounts(cards, {family:[],region:[],window:'',q:''}, newest, 'window',
    ['today','7d','30d'])).toEqual({ today: 1, '7d': 2, '30d': 4 });
});
```

Also worth adding the F-20 reduction as an explicit assertion: with an all-empty `active`,
`computeFacetCounts` for each dimension must equal the plain marginal totals.

### Should fix

#### WR-04 (MEDIUM) — assertion 20's comment-stripping deletes real code after any URL

**File:** `site/scripts/validate/facets.mjs:808-811`

```js
const codeOnly = src.split('\n').map((line) => line.replace(/\/\/.*$/, '')).join('\n');
```

`//` inside a string literal is indistinguishable from a line comment to this regex. Both news
pages contain `"url": "https://ischilesafe.com/news/"` (`news.astro:170`), so that line is truncated
at `https:`. Consequence: **any line containing a URL also loses everything after it from the scan**,
so `const u = "https://x"; el.innerHTML = data;` passes assertion 20 clean. The guard against the
phase's stated XSS sink is evadable by accident, not just by malice.

**Fix:** strip only lines whose first non-whitespace characters are `//` or `*`, and keep the rest:

```js
const codeOnly = src
  .split('\n')
  .filter((line) => !/^\s*(\/\/|\*|\/\*)/.test(line))
  .join('\n');
```

Then re-verify the assertion still passes (the doc-comments naming `innerHTML` at `news.astro:372`
are whole-line `//` comments, so they are still excluded).

#### WR-05 (MEDIUM) — assertion 11's `toLocaleDateString` scan cannot match a call containing any `)`

**File:** `site/scripts/validate/facets.mjs:507`

```js
const monthCalls = Array.from(pageSrc.matchAll(/toLocaleDateString\(([^)]*month:[^)]*)\)/gs));
```

`[^)]*` cannot cross a closing paren. Every call in today's pages happens to have paren-free
arguments, so the check fires. But the moment a call is written as
`toLocaleDateString(locale, buildOpts())`, `toLocaleDateString(getLocale(), {…month:'long'})`, or with
any nested call/`Number(x)` in the options, the regex silently stops matching and the assertion
becomes unenforceable for that call — it does not fail, it just stops looking. Given F-37 records
that this assertion caught a **real** TZ bug in this very phase, its silent-evasion mode matters.

**Fix:** match the call head and then balance-scan forward, or at minimum widen to a
non-greedy multi-paren form and require the guard on any `toLocaleDateString`/`Intl.DateTimeFormat`
occurrence in the file:

```js
for (const m of pageSrc.matchAll(/(toLocaleDateString|Intl\.DateTimeFormat)\s*\(/g)) {
  const tail = pageSrc.slice(m.index, m.index + 400);
  if (/month\s*:/.test(tail) && !/timeZone:\s*['"]UTC['"]/.test(tail)) fail(...);
}
```

#### WR-06 (MEDIUM) — the comuna query is not trimmed; whitespace silently zeroes the list

**File:** `site/src/lib/newsFilterLogic.ts:171-173`

```js
if (active.q !== '') {
  if (!card.communeNorm || !card.communeNorm.includes(norm(active.q))) return false;
}
```

`norm()` does not trim. Consequences on a live typeahead: typing `"santiago "` (trailing space,
common on mobile autocorrect/space-key) matches **zero** communes and the empty state fires; a
query of a single space matches only multi-word communes ("viña del mar", "puente alto") and hides
every single-word one, which reads as a broken filter rather than a query. The EN placeholder
(`i18n.ts:364`) even advertises `'la '` as an example, so leading/trailing whitespace is an
expected input here.

**Fix:** trim at the predicate so both the URL round-trip and the count passes agree:

```js
const qNorm = norm(active.q).trim();
if (qNorm !== '') {
  if (!card.communeNorm || !card.communeNorm.includes(qNorm)) return false;
}
```

(Do **not** trim in `parseFilterParams` only — `computeFacetCounts` calls `cardMatchesFilters`
directly and would then disagree with `applyFilters`.) Add a test for `q: '  santiago  '`.

#### WR-07 (MEDIUM) — singular/plural defect in the result count, on a template Phase 25 already fixed elsewhere

**File:** `site/src/config/i18n.ts:365` (`'{n} incidents shown'`), `:589` (`'{n} incidentes mostrados'`)

At `n === 1` the page renders "1 incidents shown" / "1 incidentes mostrados". Phase 25 explicitly
carried a P2 fix for exactly this defect class (`"(1 cases)" plural`), so this is a regression of a
resolved convention on a page Google indexes. Reachable in practice: any single-comuna + single-family
filter combination.

**Fix:** add `news_result_count_one` to `I18nStrings`/`EN_STRINGS`/`ES_STRINGS`
(`'1 incident shown'` / `'1 incidente mostrado'`), ship it as a second `data-*` carrier
(`data-result-count-template-one`) and branch in `applyFilters`. Note assertion 18 requires
**exactly one** `data-result-count-template="` occurrence — update that count in the same commit,
or the fix reddens the validator.

#### WR-08 (MEDIUM) — assertion 14's `hidden` check matches any attribute value containing the word

**File:** `site/scripts/validate/facets.mjs:591-598`

```js
const emptyMatch = distHtml.match(/<(\w+)\b([^>]*\bid="news-empty"[^>]*)>/);
…
if (!/\bhidden\b/.test(attrs)) { … }
```

`attrs` is the whole attribute string, so `class="empty hidden-state"` or
`data-x="hidden"` satisfies the test without the boolean `hidden` attribute being present. The
assertion reads as "ships hidden" and actually tests "the substring `hidden` appears somewhere in
the tag". Low likelihood today, but the check is the only thing standing between the current
behavior and an empty-state block that is permanently visible above 1,215 incidents.

**Fix:** `if (!/(^|\s)hidden(=|\s|$)/.test(attrs))`, and additionally assert the built CSS does not
set `display` on `#news-empty` (same pattern as WR-02).

## Info / carry

#### IN-01 (LOW) — unused frontmatter import of `FILTER_LOGIC_MARKER` on both pages

`site/src/pages/news.astro:19`, `site/src/pages/es/noticias.astro:20`.
The frontmatter imports `{ norm, FILTER_LOGIC_MARKER }`; only `norm` is used server-side
(`:290`). `FILTER_LOGIC_MARKER` is used exclusively inside the client `<script>`, which has its own
import (`:328`). Dead import; also pulls the module into the SSR graph for no reason.
**Fix:** `import { norm } from '../lib/newsFilterLogic';`

#### IN-02 (LOW) — dead i18n key `news_cluster_source_count`, and an assertion that exists only to police it

`site/src/config/i18n.ts:150,369,593`; `facets.mjs:626-648`. Phase 26 returned NO-GO, so this
key can never be consumed. It is shipped in `I18nStrings` (forcing every future locale to define it)
and assertion 16 spends a source+dist scan on both pages guarding against its use. Either delete the
key and assertion 16 together, or add a one-line comment at `i18n.ts:150` stating it is reserved
against a future clustering phase and intentionally unwired. Note assertion 13's `>= 15` threshold
would still pass at 14 keys.

#### IN-03 (LOW) — unreachable `return false` in `matchesWindow`

`site/src/lib/newsFilterLogic.ts:136`. `WindowValue` is exhausted by the four branches above;
the trailing `return false` is only reachable from untyped JS callers. Harmless (fails closed),
but it means a future added window value fails silently instead of loudly. Consider
`const _exhaustive: never = window;` in its place.

#### IN-04 (LOW) — stale validator header: "0 — all 10 assertions pass"

`site/scripts/validate/facets.mjs:19`. The file now has 21 assertions and its own success line
(`:848`) says so. F-21 ruled a stale count "a phase defect, not a nit"; this is the same class,
inside the file the ruling was about.
**Fix:** `0 — all 21 assertions pass (PASS)`.

#### IN-05 (LOW) — assertion 12 compares a dist page built from `site/public/data/` against repo-root `data/`

`facets.mjs:527-536` counts cards in `dist/` (rendered from
`site/public/data/incidents/current.json`, `news.astro:27`) and compares to `incidents.length`
loaded from `data/incidents/current.json` (`facets.mjs:40`). If the `public/` sync lags the repo
data, this reddens with a card-count message that misdescribes the cause. Same coupling applies to
assertions 7 and 11. **Fix:** on mismatch, add a hint line naming the sync as the likely cause, or
assert the two files are byte-identical up front.

#### IN-06 (LOW) — assertion 17's chunk regex is attribute-order/shape brittle

`facets.mjs:681` requires the exact literal `<script type="module" src="…"></script>`. Any extra
attribute Astro or a future integration emits (`crossorigin`, `async`, `data-astro-*`) yields zero
matches. It **fails closed** (empty `combined` → RED), so this is a maintenance nuisance rather than
a coverage hole — recorded so a future RED here is diagnosed as regex brittleness rather than a
genuine F-27 regression.

---

### Explicitly checked and found clean

- Editorial/legal: no unqualified absolute safe/dangerous/seguro/peligroso verdict in any of the 15
  new i18n strings or the new markup. `news_window_latest` correctly labels the anchor as
  "Latest data: {date}" / "Últimos datos: {date}" per Phase 27 handoff item 1 — never "Today".
- F-32(a): all four `toLocaleDateString` call sites across the two pages carry `timeZone: 'UTC'`
  (`news.astro:85,92,156` + ES equivalents), and `formatMonth` builds via `Date.UTC()`.
- F-32(b): `dist/news/index.html` contains no unsubstituted `{n}`/`{date}` outside the single
  deliberate `data-result-count-template="{n} incidents shown"` carrier — verified by grep.
- F-27/F-30: `dist/_astro/news.astro_…DK6PG8U5.js` opens with
  `import{F as k,p as b,c as g,a as f,s as B}from"./newsFilterLogic.BS0afx7K.js"` — the tested
  module is the shipped module, in a shared chunk, on both pages. `norm()` is defined once.
- F-29: no `facetKeys` in the `#news-facets` payload; counts derive from card `data-*`.
- Accessibility: `<details … open>` and no script touches its `open` state; `role="status"` +
  `aria-live="polite"` on `#news-result-count`; real `<legend>`s per fieldset and a real
  `<label for="news-comuna-q">`; 44px min touch targets on chips, input and button.
- CLS: the filter bar renders server-side at full size with server-computed counts identical to
  the client's first-pass values, so no post-hydration reflow.

---

_Reviewed: 2026-07-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
