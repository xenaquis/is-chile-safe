---
phase: quick-260810-kcj
reviewed: 2026-08-10T00:00:00Z
depth: quick
files_reviewed: 7
files_reviewed_list:
  - site/src/lib/newsDayFacets.ts
  - site/src/lib/newsDayFacets.test.ts
  - site/src/lib/newsFilterLogicDay.test.ts
  - site/src/lib/newsFilterLogic.ts
  - site/src/pages/news.astro
  - site/src/pages/es/noticias.astro
  - site/src/config/i18n.ts
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Quick 260810-kcj: Code Review Report

**Reviewed:** 2026-08-10
**Depth:** quick (focused — gates already green, so nothing an assertion covers is repeated here)
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Reviewed the news UX redesign (day histogram + dense list) against the six focus
questions. Three of them come back clean and are stated briefly below; the other
three surface one editorial/legal blocker and six warnings.

**Clean (verified, not assumed):**

1. **Fix (a) — `day` omitted when falsy.** Traced every read of `.day` across the
   diff: `newsFilterLogic.ts:112` (parse), `:127` (serialize), `:213`
   (`cardMatchesFilters`), and in both pages `news.astro:587,591,654` /
   `noticias.astro:587,591,654`. All five consumers are truthiness tests
   (`if (params.day)`, `active.day ? … :`, `active.day === key`), never
   `.length`, `.startsWith`, or a bare string method. `computeFacetCounts`
   touches `active` only through `cardMatchesFilters`. `active.day === key`
   with `active.day === undefined` and `key` a non-empty ISO date is correctly
   `false`. No consumer breaks on `undefined`. The fix is correct.
2. **EN/ES parity.** A comment-stripped, import-path-normalised diff of the two
   pages returns *only* intentional locale differences: `FAMILY_LABELS_EN/ES`,
   `EN_STRINGS/ES_STRINGS` + `regionNameEs`, `en-US`/`es-CL`, `title_en`/`title_es`,
   `/commune/` vs `/es/comuna/`, JSON-LD, `<h1>`/intro copy, empty-state copy.
   Zero divergent handlers, ids, attributes, or CSS rules. The 6 new ES strings
   (`i18n.ts:635-640`) are genuine translations, not EN copies, and both
   `news_histogram_peak` variants keep the `{n}`/`{date}` tokens.
3. **XSS / injection.** The single `set:html` per page
   (`news.astro:425`, `noticias.astro:424`) passes through
   `escapeForInlineScript` (`newsFacets.ts:104-106`, escapes `<` to `<`,
   so `</script` is unreconstructable). Every incident field reaching the DOM
   (`title_*`, `outlet`, commune name, `data-*`) goes through an Astro
   expression and is HTML-escaped; `incident.url` goes through `safeUrl()`
   (protocol allow-list, `#` fallback) with `rel="noopener noreferrer"`. The
   client script only ever assigns `textContent` / `style.setProperty` with a
   `Math.round`ed number. No injection path found.

## Critical Issues

### CR-01: Outlet attribution disappears on every viewport ≤ 860px

**File:** `site/src/pages/news.astro:1192-1194`, `site/src/pages/es/noticias.astro:1192-1194`

```css
@media (max-width: 860px) {
  .news-outlet { display: none; }
}
```

**Issue:** CLAUDE.md's editorial/legal constraint is explicit: *"siempre atribuir
fuentes (CEAD, medio de prensa); incidentes de noticias citan y enlazan la
fuente"*, and both pages' own doc comments repeat it ("Legal-safe tone: attribute
outlet" / "Se atribuye siempre la fuente"). The pre-redesign markup rendered
`<span class="news-date-outlet">{incident.date} · {incident.outlet}</span>`
unconditionally. The dense redesign moved the outlet into its own grid column and
then removes that column entirely below 860px — i.e. for the majority of the
site's traffic, the outlet name is not merely visually de-emphasised, it is
removed from the accessibility tree too (`display:none` is not `.news-sr`). The
`<a href>` still points at the article, but a bare headline with no named medium
is exactly the attribution failure the constraint exists to prevent, and it
degrades the intro paragraph's claim ("Each entry links to its original source
article") into something the mobile reader cannot verify at a glance.
This is not covered by any assertion — `facets.mjs` checks markup, not media queries.

**Fix:** keep the outlet in the DOM on mobile. Simplest form, in both pages:

```css
@media (max-width: 860px) {
  .news-row { grid-template-columns: minmax(0, 1fr) auto; row-gap: 2px; }
  .news-title { grid-column: 1 / -1; }
  /* Outlet stays: it is the source attribution, not decoration. */
  .news-outlet { grid-column: 1; font-size: var(--text-label); }
  .news-date { grid-column: 2; text-align: right; }
  /* commune chip wraps to its own line if needed */
}
```

If horizontal space genuinely does not allow it, merge outlet and date into one
cell (`{outlet} · {date}`) as the old design did — never drop the outlet.

## Warnings

### WR-01: `day` + `window` mutual exclusion is missing on initial URL parse — a reachable, unexplained empty list

**File:** `site/src/pages/news.astro:478-492` and `:627-661`, same lines in `noticias.astro`

**Issue:** The comment at `:623-626` claims exclusivity is enforced "HERE, at the
interaction layer". It is enforced in the two *event handlers* (`:629` clears
`day`, `:655` clears `window`) but **not** at bootstrap. `parseFilterParams` happily
returns both, and nothing normalises `active` before the first `applyFilters()`
at `:682`. So `?day=2026-08-05&window=today` (a shared/edited/bookmarked URL — and
these URLs are written back by `history.replaceState`, so they *are* shared) lands
in a state the UI cannot produce and cannot explain:

- both predicates AND at `newsFilterLogic.ts:209-215`, so the list is very likely 0;
- the window radio renders checked (`:481`) **and** a bar renders pressed (`:588`);
- the histogram's `is-out` branch at `:591-597` takes the `active.day` path, which
  dims every bar except the pinned one — so the active window filter becomes
  completely invisible in the one control that would have shown it;
- `#news-empty` shows a generic "no results" message with no hint that two date
  filters are stacked.

A related instance: `?day=1999-01-01` passes the ISO regex, matches no card and no
rendered bar, so the page goes empty with *zero* filter controls appearing active.

**Fix:** normalise once, immediately after parsing, in both pages:

```ts
let active: FilterParams = parseFilterParams(window.location.search);
// day and window are mutually exclusive date predicates (see handlers below);
// a hand-edited URL must not reach a state the UI cannot produce or explain.
if (active.day) active = { ...active, window: '' };
// and drop a day that is not in the rendered histogram window:
if (active.day && !dayKeys.includes(active.day)) active = { ...active, day: '' };
```

(`dayKeys` is already computed at `:475`; move the two lines below it.)

### WR-02: Crime type in the list is colour-only for sighted users, and two families share the same red

**File:** `site/src/pages/news.astro:401,405` and `:724,732` (identical in `noticias.astro`)

**Issue:** The redesign traded the visible type chip for
`<span class="fam-dot" aria-hidden="true">` + `<span class="news-sr">{familyLabel}</span>`.
`.news-sr` is `clip-path: inset(50%)` — assistive tech gets the label, a sighted
reader with any colour-vision deficiency gets nothing at all. That is WCAG 2.2
SC 1.4.1 (Use of Color): colour is the sole visual means of conveying the type
dimension. It is worse than the generic case because the palette itself is not
separable: `[data-family='vida'] { oklch(0.58 0.14 25) }` and
`[data-family='homicidios'] { oklch(0.52 0.15 20) }` are two near-identical dark
reds at 9×9px — indistinguishable even with normal vision, and per
`vida/homicide slug collision` these two are already a known confusion pair. The
filter chips do carry dot+label, but they live inside a collapsible `<details>`
that the reader may have closed, and they are far from the row being read.

**Fix:** give the dot a hover/focus-visible text affordance and separate the two
reds. Minimum viable, in both pages:

```astro
<span class="fam-dot" title={familyLabel(family)} aria-hidden="true"></span>
```

plus re-hue one of the pair (e.g. `homicidios` to `oklch(0.45 0.16 12)`) or give
`homicidios` a ring/second visual channel. Better: render the label as visible
text at ≥ 861px (there is room in the headline column) and keep `.news-sr` only
where it is genuinely truncated.

### WR-03: Region disclosure count is an unlabelled, untranslated, unannounced " · N"

**File:** `site/src/pages/news.astro:602-604` and `:271`, identical in `noticias.astro`

```ts
regionCountEl.textContent = active.region.length > 0 ? ' · ' + active.region.length : '';
```

**Issue:** Three problems in one line. (a) The string is hard-coded in the script,
not an i18n key, so ES and EN render the identical `" · 2"` — the one piece of new
UI copy that skipped the i18n pass the commit was supposedly finishing.
(b) It has no accessible name: a screen-reader user activating the summary hears
"Region · 2" with no indication whether 2 means *selected regions* or *matching
results* — ambiguous precisely because `#news-result-count` next to it is also a
number. (c) It is mutated in `applyFilters()` but has no `aria-live`, and — unlike
`#news-result-count` which does — it is inside a `<summary>` the user may have
collapsed, so a change is silent.

**Fix:** add a key (e.g. `news_filter_region_selected: '{n} selected'` /
`'{n} seleccionadas'`), carry it via `data-*` like the result-count template
already does, and emit a visible " · N" plus a `.news-sr` expansion:

```astro
<span class="dd-count" id="news-region-count"></span>
<span class="news-sr" id="news-region-count-sr"></span>
```

### WR-04: The 258-line client script and 528-line stylesheet are byte-identical twins across the two pages

**File:** `site/src/pages/news.astro:426-684` + `:687-1214`, `site/src/pages/es/noticias.astro:425-683` + `:687-1214`

**Issue:** `newsFilterLogic.ts`'s own header (lines 5-9) states the contract: the
shipped filter logic "must BE this unit-tested module, imported by both pages'
inline `<script>` blocks, **never a copy-pasted twin**". The pure predicates honour
that; everything else does not. The entire DOM wiring — bootstrap, pre-population,
`applyFilters`, four facet-count loops, the histogram rescale, the `replaceState`
block, six event handlers — is duplicated verbatim, differing only in the relative
import path. So is the whole `<style>` block, including the family palette whose
own comment concedes "the block must be edited in BOTH pages together". This grew
from ~330 lines to ~1200 lines per page in this commit, i.e. the divergence surface
roughly quadrupled, and no assertion or test compares the two pages. WR-01, WR-02,
WR-03 and CR-01 each now require the same edit applied twice, correctly.

**Fix:** extract `site/src/scripts/newsFilterBar.ts` exporting
`initNewsFilterBar()` (it reads everything it needs from the DOM and from the
already-substituted `data-*` templates — it needs no locale input), and have both
pages ship `<script>import { initNewsFilterBar } from '…'; initNewsFilterBar();</script>`.
Move the shared CSS into a single imported stylesheet (or add a parity test that
diffs the two `<style>` blocks after normalising comments — the exact diff used in
this review).

### WR-05: Filtering to zero results leaves an empty bordered table shell with a column header

**File:** `site/src/pages/news.astro:365-381` and `:494-510`

**Issue:** `applyFilters()` hides each `.news-card` and each `.news-month-section`,
and reveals `#news-empty`. It never touches `.news-list` (`:375`) or its
`.news-list-head` (`:376-381`). At zero results the reader sees the "no incidents
match" message, and *below* it an empty bordered box still captioned
REPORTED INCIDENT / COMMUNE / OUTLET / DATE. It reads like a broken render rather
than an empty result. (Pre-redesign there was no header row, so this is new.)

**Fix:** in `applyFilters()`, alongside the `emptyEl` toggle:

```ts
const listEl = document.querySelector<HTMLElement>('.news-list');
if (listEl) listEl.hidden = visibleTotal === 0;
```

(`.news-list` sets `display` in CSS — as `.news-list` is not `.news-card`,
assertion 12 does not apply, but the `display` rule *will* defeat `hidden`, so
toggle a class or add `.news-list[hidden] { display: none; }`.)

### WR-06: `applyFilters()` runs unthrottled on every keystroke and the `day` dimension multiplied its cost

**File:** `site/src/pages/news.astro:662-667`, `:572-600`

**Issue:** Flagged despite performance being nominally out of v1 scope, because
this is a *user-visible input-lag regression introduced by this commit*, not a
micro-optimisation. The comuna search fires `applyFilters()` per `input` event with
no debounce. Each call now runs `computeFacetCounts` four times — window (3 keys),
region (~16), family (~9) and, new in this commit, **day (30 keys)** — and each of
those is O(cards × keys) with a fresh `cards.map(c => c.state)` allocation per call
(`:518,541,556,574`). At ~1,500 incidents that is roughly 85,000 predicate
evaluations plus four 1,500-element array allocations *per typed character*, and
`norm(active.q)` is recomputed inside every single `cardMatchesFilters` call
(`newsFilterLogic.ts:218`). On a mid-range Android this will drop characters.

**Fix:** debounce the search input (~120ms) and hoist the invariants:

```ts
const cardStates = cards.map((c) => c.state); // hoist out of applyFilters
let searchTimer: number | undefined;
comunaInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    active = { ...active, q: comunaInput.value };
    applyFilters();
  }, 120);
});
```

## Info

### IN-01: Histogram bars give mouse users no count

**File:** `site/src/pages/news.astro:317-328`

The per-bar `Aug 5 · 12` text is `.news-sr` only. A pointer user hovering a bar
gets nothing — no `title`, no tooltip. Add `title={`${dayLabel(b.date)} · ${b.count}`}`
to the `<button>`; it costs nothing and does not affect the accessible name
(the `.news-sr` text already wins).

### IN-02: Zero-count bars are ordinary buttons that filter to nothing

**File:** `site/src/pages/news.astro:317-328`, `newsDayFacets.ts:87-94`

The bucket series is deliberately dense (correct — gaps are information), but a
`count: 0` day renders as a fully focusable, clickable button whose only outcome is
an empty list. Consider `aria-disabled="true"` + skipping the click for
`b.count === 0`, keeping the 3px tick purely as an axis mark.

### IN-03: 30 extra tab stops with no skip affordance

**File:** `site/src/pages/news.astro:316-329`

`role="group"` groups the bars visually/semantically but does not make them
skippable. A keyboard user tabbing from the region dropdown to the family chips
now traverses 30 buttons. Consider roving-tabindex (one tab stop, arrow keys move
between bars), which is the standard pattern for a toggle-button group.

### IN-04: `serializeFilterParams` guard style drifts from the module's own convention

**File:** `site/src/lib/newsFilterLogic.ts:127`

`if (params.day)` versus `if (params.window !== '')` / `.length > 0` above it.
Behaviourally identical for the three reachable values (`undefined`, `''`, ISO
date), so this is cosmetic — but the file's stated posture is explicitness about
the optional field, and a future `day: '0'`-style value would silently drop.
`if (params.day && params.day !== '')` or a comment would settle it.

### IN-05: `.news-list-head` is `aria-hidden`, leaving the row cells unlabelled for AT

**File:** `site/src/pages/news.astro:376-381`, `:407-413`

The visible column headers are hidden from assistive tech (reasonable — they are
not a real table header), but the cells they label are bare `<span>`s. A screen
reader reads "…headline link, Providencia link, Emol, Aug 5" with no indication
that "Emol" is the outlet. Once CR-01 is fixed, consider
`<span class="news-outlet"><span class="news-sr">{t.news_col_outlet}: </span>{incident.outlet}</span>`
— which also strengthens the attribution the blocker is about.

---

_Reviewed: 2026-08-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick (focused)_
