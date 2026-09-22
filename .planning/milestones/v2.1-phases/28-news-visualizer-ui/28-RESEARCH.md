# Phase 28: News Visualizer UI - Research

**Researched:** 2026-07-30
**Domain:** Progressive-enhancement client-side filtering over a zero-JS Astro static page (vanilla `<script>`, no framework, no island)
**Confidence:** HIGH (all claims below verified directly against the repo source, a real build, or a real measurement — this phase has no external-library unknowns; `28-UI-SPEC.md` already fixed the design)

## Summary

Phase 28 adds client-side query-param faceting on top of two already-shipped, near-identical static pages (`site/src/pages/news.astro`, `site/src/pages/es/noticias.astro`) that Phase 27 already wired to `computeNewsFacets()`. The UI-SPEC is binding and fixes markup, tokens, breakpoints, hide/show mechanism (`hidden` attribute only), and the query-param contract. What's left for research/planning is: (1) the exact new `data-*` attributes the filter script needs on existing markup, (2) whether to share or duplicate the filter script between the two pages, (3) how cross-filtered counts get their data given `facetKeys` is not currently serialized to the page, (4) how the anchor date reaches the template, and (5) what falsifiable assertions gate the new client behavior given `facets.mjs`'s F-24 lesson that unfalsifiable assertions are worse than none.

The single highest-leverage finding: serializing the full `facetKeys` array (1,215 entries today) costs **121,626 bytes measured** (see Q3below) — two orders of magnitude larger than the current 973-byte `#news-facets` payload, and it duplicates data already present in the DOM as card attributes. Recommendation: **do not serialize `facetKeys`; derive cross-filtered counts from the DOM** by counting cards whose `data-*` attributes match the active filter set, using the exact same `!card.hidden` predicate the UI-SPEC already locks for visibility. This keeps the payload at effectively zero added bytes and gives one source of truth (the DOM) instead of two (DOM + parallel JSON) that could drift.

**Primary recommendation:** Extract the filter engine as one plain (non-module, no build-step) `<script>` block duplicated verbatim in both `.astro` files — not a shared `.ts` module imported into two components — because this codebase's established convention (confirmed in `communes/index.astro`) is inline, non-modular, per-page vanilla scripts, and `facets.mjs` assertion 7's per-locale dist-level check pattern (checking both `dist/news/index.html` and `dist/es/noticias/index.html` independently) is the existing template for catching EN/ES drift in exactly this kind of duplicated control — extend it with an EN/ES byte-comparison or logic-equivalence assertion for the new script block rather than trying to avoid duplication architecturally.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Facet index computation (counts, region/family/window buckets) | Frontend Server (SSR/SSG, build-time) | — | Already owned by `newsFacets.ts`, Astro frontmatter, at build time — Phase 27 contract, unchanged by Phase 28 |
| Initial/unfiltered facet counts shown at rest | Frontend Server (SSG) | — | Static HTML from `facetsProjection.byFamily/byRegion/byWindow`, F-20 contract |
| Cross-filtered per-option counts (once a filter is active) | Browser / Client | — | New in Phase 28; DOM-derived per this research's recommendation (Q3) — no server round-trip, no new build artifact |
| Card/section visibility toggling | Browser / Client | — | Pure `hidden`-attribute DOM manipulation, UI-SPEC-locked mechanism |
| URL query-param sync | Browser / Client | — | `history.replaceState`, mirrors `/compare/` precedent (Phase 25 P1-2) |
| Comuna typeahead matching | Browser / Client | — | Reuses `communes/index.astro`'s `norm()` pattern verbatim; runs against `data-commune-norm` on cards |
| i18n strings | Frontend Server (SSG) | — | `i18n.ts` `I18nStrings`/`EN_STRINGS`/`ES_STRINGS`, consumed at render time, never client-fetched |
| Build-time validation of facet integrity | CI / Build tooling | — | `facets.mjs` validator #16, extended in this phase, not a runtime tier |

## User Constraints

<user_constraints>
No CONTEXT.md exists for this phase — this is an authorized unattended run (`.planning/v2.1-AUTONOMOUS-DIRECTIVE.md`, `mode: yolo`, `skip_discuss: true`). `.planning/phases/28-news-visualizer-ui/28-UI-SPEC.md` is the binding decision source of record in place of CONTEXT.md — every markup shape, token, breakpoint, hide/show mechanism, i18n key name, and query-param name it specifies is LOCKED and must not be re-decided. This research covers only what the UI-SPEC leaves open (data attributes, script-sharing strategy, facetKeys serialization, anchor-date plumbing, validator design) plus implementation hazards.

**Hard constraints (non-negotiable, from the directive and locked v2.1 milestone decisions):**
- Query-param facets only, over the two existing URLs `/news/` and `/es/noticias/` — zero new indexable URLs.
- Zero new shipped frontend JS dependencies (no new npm package of any kind for the frontend).
- No React island on these pages — must stay zero-JS-for-content-visibility (progressive enhancement only).
- NEWSUI-05 degrades to faceting-only — Phase 26 returned NO-GO; no `cluster_id`/`is_primary` field exists on `IncidentRecord`; do not build cluster-card markup.
- `data/` is READ-ONLY for this phase (and the whole run) — no data migration, no pipeline changes.
- Never `git push` during this run.
- Chain `npm run build && npm run validate` in ONE command (OneDrive `dist/` desync gotcha).
- Never render an unqualified "safe/dangerous/seguro/peligroso" territorial verdict.
</user_constraints>

## Phase Requirements

<phase_requirements>
| ID | Description | Research Support |
|----|-------------|------------------|
| NEWSUI-01 | Filter by time/region/family with per-option counts, both pages | Q1 (data-* attrs), Q3 (DOM-derived cross-filtered counts), UI-SPEC markup |
| NEWSUI-02 | Unfiltered superset fully pre-rendered; filtering is progressive enhancement | Confirmed both pages already render 100% of incidents server-side (news.astro:176-206); new `<script>` has no `client:` directive — see Q7 |
| NEWSUI-03 | Accent-insensitive comuna typeahead reusing directory-finder pattern | Q1 (`data-commune-norm`), `communes/index.astro:174-306` read in full |
| NEWSUI-04 | Query-param state round-trips; zero-result empty state, never indexed as thin content | UI-SPEC query-param table + empty-state section; Q5 falsifiable assertions |
| NEWSUI-05 | Clustering GO branch (inactive) / NO-GO graceful degradation | Phase 26 NO-GO confirmed in STATE.md; no markup work needed, i18n key reserved only |
| NEWSUI-06 | LLM-derived text escaped; no CLS/hydration regression | Q7 (zero-JS/CLS facts), UI-SPEC escaping section, `escapeForInlineScript` reuse |
| NEWSUI-07 | EN/ES parity via `i18n.ts` keys; hardcoded ES slugs | Q2 (shared-vs-duplicated script + EN/ES drift risk), UI-SPEC copywriting contract |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Astro 6.4.x + islands: this phase must NOT add a React island — matches NEWSUI's zero-JS mandate exactly (CLAUDE.md's own island guidance: `client:load` is banned on the map island for JS-weight reasons; by extension, no `client:*` directive belongs on these pages at all).
- `prefixDefaultLocale: false` — EN clean URLs unaffected; no routing change in this phase.
- Cloudflare Pages 20K-file free-tier budget — current build is **834 pages** (measured live, see Q7); this phase adds zero new pages by design (query-param client state only).
- OneDrive gotcha — `npm run build && npm run validate` must be chained.
- No absolute safe/dangerous verdict — the empty-state copy and filter labels in UI-SPEC already comply; no new risk here.

## Standard Stack

No new dependencies. This phase is 100% reuse of the existing stack:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Astro | 6.4.x (already installed) | SSG frontmatter computes facets; `<script>` (no `client:` directive) ships inline vanilla JS | Confirmed already in use by `news.astro`/`es/noticias.astro`; adding a plain `<script>` block (no directive) is the same mechanism `communes/index.astro:170-307` already uses |
| Native `<details>`/`<fieldset>` | HTML5 | Filter bar container, progressive-enhancement disclosure | UI-SPEC-locked; zero-JS-dependency posture (milestone-locked decision) |

### Supporting
None — no new library needed for URL param parsing (`URLSearchParams`, native), state sync (`history.replaceState`, native), or accent stripping (`String.prototype.normalize`, native — already used verbatim in `communes/index.astro:175-176`).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Serializing `facetKeys` to `#news-facets` | A shared client-side facet-index JSON payload | Rejected — measured 121,626 bytes (Q3) for 1,215 incidents vs. deriving counts from the DOM the page already renders; a second data source risks drifting from what's actually shown |
| Vanilla per-page inline `<script>` | A shared `<script src="...">` external module | Rejected — this repo has zero precedent for a shared client JS module for inline page behavior (`communes/index.astro`'s script is inline/non-modular by explicit codebase convention, restated in UI-SPEC §Comuna typeahead); introducing one here would be a new pattern the milestone didn't ask for |

**Installation:** none required — zero new packages.

## Package Legitimacy Audit

Not applicable — this phase installs no external packages (frontend or pipeline). No `npm install` / `pip install` step exists in the scope. Skipping the Package Legitimacy Gate per its own scope condition ("whenever this phase installs external packages").

## Architecture Patterns

### System Architecture Diagram

```
Build time (Astro SSG, unchanged from Phase 27):
  data/incidents/current.json + archive/*.json + cead/meta/index.json
        │
        ▼
  computeNewsFacets() (newsFacets.ts)          [unchanged]
        │
        ├─► facetsProjection (byFamily/byRegion/byMonth/byWindow.length)
        │     → escapeForInlineScript(JSON.stringify(...)) → #news-facets <script type="application/json">
        │
        └─► incidents[] rendered as <article class="news-card" data-family=... data-region-id=...
              data-year-month=... data-commune-norm=...> inside <section class="news-month-section">
              (this phase ADDS the data-* attributes; markup shape otherwise unchanged)

Page load (client, progressive enhancement, no client: directive):
  <script> (per-page, no import, no build step) reads:
    - URLSearchParams(location.search)  → family, region, window, q
    - all .news-card elements (already in DOM, server-rendered)
        │
        ▼
  applyFilters(): for each .news-card, compute match against active filter set
    using its data-* attributes  →  toggle `hidden` attribute (never style.display)
        │
        ├─► toggle `hidden` on any .news-month-section with zero visible children
        ├─► toggle `hidden` on #news-empty when total visible === 0
        ├─► recompute per-option counts by counting matching (non-hidden-by-OTHER-facets) cards
        │     → update text content of each filter-group's option labels + #news-result-count
        └─► history.replaceState(null, '', newURL)  (never pushState)
```

### Recommended Project Structure

No new files/folders — all changes are inline edits to existing files:

```
site/src/
├── pages/news.astro              # + data-* attrs on .news-card, + <script> filter block, + facet markup from UI-SPEC
├── pages/es/noticias.astro       # same, ES copy
├── config/i18n.ts                # + 14 keys (news_filter_heading .. news_cluster_source_count)
├── lib/newsFacets.ts             # + anchorDate field (Q4 recommendation) — see Don't Hand-Roll / Pitfalls
├── lib/newsFacets.test.ts        # + tests for anchorDate, no facetKeys-serialization test needed (not shipped)
site/scripts/validate/
├── facets.mjs                    # + new assertions for anchorDate presence, EN/ES filter-script parity (Q5)
```

### Pattern 1: Data-attribute-driven client filtering (no client-side data fetch)
**What:** Every filterable dimension is exposed as a `data-*` attribute directly on the server-rendered `.news-card`; the client script never fetches or parses a separate facet payload for filtering logic, only reads attributes already in the DOM.
**When to use:** Always, for this phase — matches `communes/index.astro`'s `data-norm`/`data-name` precedent exactly.
**Example (server-side, Astro frontmatter → markup):**
```astro
// Source: pattern extrapolated from communes/index.astro:116-119 (data-name/data-norm) + UI-SPEC §Comuna typeahead
<article
  class="news-card"
  data-family={incident.family ?? ''}
  data-region-id={communeInfo ? cutToRegion.get(String(incident.cut)) ?? '' : ''}
  data-year-month={incident.date.slice(0, 7)}
  data-commune-norm={communeInfo ? norm(communeInfo.name) : ''}
>
```
Where `cutToRegion` is the same `Map<string,string>` `newsFacets.ts` already builds internally (line 166) — the page must build its own copy from `loadIndex()` (already imported in both pages) since `newsFacets.ts` doesn't currently export the map itself. This is a ~3-line addition in each `.astro` file's frontmatter, not a new module.

### Pattern 2: `hidden`-attribute-only visibility (UI-SPEC-locked)
**What:** Every element the filter script shows/hides uses the `hidden` DOM attribute exclusively — never `style.display`.
**When to use:** `.news-card`, `.news-month-section`, `#news-empty` — all three, uniformly.
**Why (from UI-SPEC, restated for planning):** the visible-count check becomes exactly `!card.hidden`, one predicate, one query — mixing mechanisms (as `communes/index.astro:262-267` does with `style.display`) would let a section-collapse check and a card-hide mechanism disagree.

### Anti-Patterns to Avoid
- **Serializing `facetKeys` for client-side count recomputation:** measured 121,626 bytes for 1,215 incidents (Q3) — two orders of magnitude larger than the existing 973-byte payload, for data already present in the DOM. Don't hand-roll a second data channel when the DOM already has it.
- **A shared `.ts` client module imported by both `.astro` files:** no precedent in this codebase; `communes/index.astro`'s script is deliberately inline/non-modular. Would also complicate `facets.mjs`'s per-locale source-scanning pattern (assertion 7 style), which greps page source files directly, not a shared module.
- **`style.display` for any hide/show toggle in this phase:** explicitly banned by UI-SPEC — would break the `!card.hidden` visible-count invariant.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accent-insensitive string matching | A new normalize/strip-accents utility | `s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()` — copy-paste verbatim from `communes/index.astro:175-176` | NEWSUI-03 explicitly requires reusing this exact established pattern; it is the only accent-insensitive search implementation in the codebase (UI-SPEC Decision 4) |
| Cross-filtered facet counting | A new client-side data-index / mini-query-engine | Iterate the existing `.news-card` NodeList once per filter change and tally by `data-*` attribute match | Card count is 1,215 today; a `querySelectorAll` + `Array.filter` pass is O(n) and trivially fast — no library or index structure is justified at this volume |
| CUT→region mapping on the client | Re-deriving region from CUT length in client JS | Bake `region-id` into `data-region-id` at build time (server already has `cutToRegion`) | Region derivation logic (CUT-length rule) already exists build-time in `newsFacets.ts`; duplicating it in client JS risks the two diverging — bake the *result*, not the *logic*, into the DOM |

**Key insight:** At 1,215 incidents (and no realistic near-term growth into the tens of thousands — this is a national news aggregator, not a firehose), every "don't hand-roll" temptation in this phase (indexing, virtualization, a client router) is solving a problem this dataset doesn't have. The correct scope is the smallest one: read attributes already on cards that are already in the DOM.

## Common Pitfalls

### Pitfall 1: `{expr}` inside `<script>` is rendered literally by Astro, not interpolated
**What goes wrong:** Writing `<script>const facets = {facetsProjection};</script>` in an `.astro` file emits the literal text `{facetsProjection}` into the shipped JS, not the serialized value — this exact trap is recorded in project memory (`astro-script-no-expr-interpolation`).
**Why it happens:** Astro only interpolates `{expr}` in the component template region, not inside `<script>`/`<style>` blocks.
**How to avoid:** Data must cross the server→client boundary via `data-*` attributes (as this phase does for filtering) or via `set:html` on a `<script type="application/json">` node (as `#news-facets` already does) — never via literal `{expr}` inside an executable `<script>` block. The new filter `<script>` in this phase reads data exclusively from the DOM (`data-*` attributes, `#news-facets` counts) at runtime — it does not need any build-time value injected into its own body, which sidesteps this pitfall entirely.
**Warning signs:** A shipped script containing the literal text `{` followed by a JS identifier that should have been a server value.

### Pitfall 2: `vida`/`homicide` family-slug collision in any family-keyed loop
**What goes wrong:** `FAMILY_SLUGS.vida.en === 'homicide'` (documented in project memory `vida-homicide-slug-collision`); a naive `byFamily` iteration that builds links or labels keyed only by family slug can silently duplicate/mislabel homicide.
**Why it happens:** Historical naming collision between the `vida` family key and its English slug.
**How to avoid:** This phase's family filter checkboxes are built directly from `facets.byFamily` entries (`{key, count}`) using `FAMILY_LABELS_EN`/`FAMILY_LABELS_ES` (`familyDefs.ts`) for display text — never construct a URL/slug from the family key in this phase (filtering is query-param `?family=<key>`, not a route). The collision risk is specifically about routing/slugs, which this phase does not touch. Flag it anyway for the planner: do not add a "view all {family}" link using `FAMILY_SLUGS` without checking this collision first.
**Warning signs:** A homicide-labeled filter chip appearing twice, or a "vida" filter option linking to a `/crime/homicide/` page.

### Pitfall 3: OneDrive build/validate desync
**What goes wrong:** `dist/` can vanish or go stale between a `npm run build` and a separate `npm run validate` invocation because the repo lives inside OneDrive and sync timing interferes with process handoff.
**Why it happens:** Documented project memory (`onedrive-build-artifacts-desync`).
**How to avoid:** Always chain `cd site && npm run build && npm run validate` in ONE command — verified working during this research (see Q7: `npm run build` completed in 22.9s, 834 pages, then `npm run check` ran immediately after in the same command chain without desync).
**Warning signs:** `facets.mjs` assertion 7 failing with "built page not found" despite a build having just "succeeded" in a prior separate command.

### Pitfall 4: `set:html` is unescaped — any new data-derived string added to `#news-facets` needs the same treatment
**What goes wrong:** `JSON.stringify` does not escape `</script>`; if this phase adds the anchor date (Q4) or any other LLM/classifier-derived string to the `#news-facets` node without routing it through `escapeForInlineScript`, a poisoned value could break out of the `<script>` element.
**Why it happens:** `set:html` in Astro renders raw HTML, by design (that's why it's used here — `JSON.stringify` output is not otherwise renderable as a script body without Astro re-escaping quotes).
**How to avoid:** Reuse the existing `escapeForInlineScript()` call already wrapping the whole `facetsProjection` object — if `anchorDate` is added as a field on `facetsProjection` (recommended, Q4), it is automatically covered by the existing single `escapeForInlineScript(JSON.stringify(facetsProjection))` call at `news.astro:210` / `es/noticias.astro:209`. Do NOT add a second, separate `set:html` call for the anchor date.
**Warning signs:** A second `<script set:html={...}>` node anywhere in the page, or a raw `{anchorDate}` interpolated directly into non-script markup without going through `t.news_window_latest.replace('{date}', ...)`.

## Code Examples

### Q1 — Exact current render structure + new data-* attributes

Verified structure in `news.astro:176-206` / `es/noticias.astro:175-204` (byte-identical shape, only copy differs):

```astro
<section class="news-month-section">
  <h2 class="news-date-group">{formatMonth(yearMonth)}</h2>
  {groupIncidents.map((incident) => {
    const communeInfo = getCommuneInfo(incident);
    return (
      <article class="news-card">
        <h3 class="news-title">
          <a href={safeUrl(incident.url)} target="_blank" rel="noopener noreferrer">{incident.title_en}</a>
        </h3>
        <p class="news-meta">
          {incident.family && <span class="news-type-chip">{familyLabel(incident.family)}</span>}
          {communeInfo && <span class="news-commune-chip"><a href={...}>{communeInfo.name}</a></span>}
          <span class="news-date-outlet">{incident.date} · {incident.outlet}</span>
        </p>
      </article>
    );
  })}
</section>
```

`.news-card` currently has **zero** `data-*` attributes. `.news-month-section` also has zero. Neither has an `id`.

**New attributes needed (verified from UI-SPEC's query-param contract + facet dimensions):**

| Attribute | On element | Source expression | Notes |
|-----------|-----------|-------------------|-------|
| `data-family` | `.news-card` | `incident.family ?? ''` | matches `?family=` values; empty string when incident has no family (rare — `facets.mjs` assertion 1 already tracks incidents-without-family separately) |
| `data-region-id` | `.news-card` | `cutToRegion.get(String(incident.cut)) ?? ''` | requires building a page-local `cutToRegion` Map from `loadIndex()` — 3 lines, both pages already `import { loadIndex } from '../lib/data'` |
| `data-year-month` | `.news-card` | `incident.date.slice(0, 7)` | already computed per-card as the grouping key in the existing loop — reuse the loop variable, don't recompute |
| `data-commune-norm` | `.news-card` | `communeInfo ? norm(communeInfo.name) : ''` | UI-SPEC's own recommendation (§Comuna typeahead); `norm()` copy-pasted from `communes/index.astro:175-176`, defined server-side in Astro frontmatter (plain JS, no DOM needed at build time) |
| (none needed for `window`) | — | — | `window` (today/7d/30d) is computed **client-side from `data-year-month`+the card's actual `date`**, OR simplest: add `data-date={incident.date}` (the raw ISO date) so the client script can replicate the exact `newestDate`/`lowerBoundDate` boundary logic against real dates rather than pre-bucketing at build time. **Recommended: add `data-date` instead of a precomputed window tag** — see Q6, this avoids a second place where window-bucket logic must be kept in sync with `newsFacets.ts`. |
| `id` | `.news-month-section` | `'month-' + yearMonth` | needed so the client script can target sections directly for the empty-month-hide behavior, rather than only walking children |

This is additive — no existing attribute or class is renamed, so `facets.mjs`, `newsFacets.test.ts`, and every existing validator's DOM assumptions are unaffected.

### Q6 — `?window=today` semantics (client must replicate exactly)

From `newsFacets.ts:179-216` (verified read in full):
- `newestDate` = max `inc.date` string across ALL incidents (simple string comparison, works because dates are `YYYY-MM-DD` — lexicographic order equals chronological order).
- `anchorMs = Date.parse(newestDate + 'T00:00:00Z')` — UTC midnight of the newest date.
- `lower7 = lowerBoundDate(anchorMs, 6)` → newestDate minus 6 days (7-day inclusive window: today + 6 prior days = 7 days total).
- `lower30 = lowerBoundDate(anchorMs, 29)` → newestDate minus 29 days (30-day inclusive window).
- Bucket membership is **inclusive** on both ends: `isToday = inc.date === newestDate`; `is7d = inc.date >= lower7`; `is30d = inc.date >= lower30`. Note `is7d`/`is30d` are **not mutually exclusive with `isToday`** — a "today" incident is also counted in `is7d` and `is30d` (this is why `byWindow.today/sevenDay/thirtyDay` are three separately-populated arrays, not a partition).
- `facets.mjs` assertion 9 (lines 376-436) already proves this arithmetic is TZ-independent (runs the identical calc under `TZ=UTC` and `TZ=America/Santiago`, asserts identical output) — the client script can safely use the same `Date.parse(dateStr + 'T00:00:00Z')` pattern without any TZ hazard, PROVIDED it also avoids `toLocaleDateString`/`getMonth()`/bare `new Date(y,m,d)` (the exact patterns assertion 9 scans for in `newsFacets.ts`).

**Client-side reproduction is exact IF and only if** the client script uses `data-date` (full ISO date per card, recommended above) and re-derives `newestDate` as `max(all data-date values)` — this can literally be a client-side line-for-line port of `newsFacets.ts:180-216`'s window logic (≈15 lines), which is small enough to duplicate safely as long as a validator assertion (Q5) proves the two stay in sync.

**Divergence risk:** if the client instead trusted a pre-baked `data-window="today"` attribute computed once at build time, and the build is stale relative to "now" by more than a day (a real, already-observed condition — STATE.md: newest incident 2026-07-27 while build date was 2026-07-30), the pre-baked value is still internally consistent (it's relative to the data, not wall-clock) so this isn't actually a staleness bug — but it DOES mean the server-rendered unfiltered counts (`facets.byWindow.today.length`, static text) and a client recomputation must use identical anchor logic or they will silently disagree. **Recommendation: compute `newestDate` client-side from the DOM's own `data-date` values, mirroring server logic exactly, rather than trusting a single baked flag** — this is the safer of the two designs specifically because it makes drift structurally impossible (one algorithm, ported once, not two systems that must agree by discipline).

### Q4 — Anchor date plumbing recommendation

**Recommended: (a) add `anchorDate` field to `NewsFacetIndex`.** Confirmed via source read (`newsFacets.ts:180-183`) that `newestDate` is currently a local `let` variable, never returned, never exported. The UI-SPEC itself states preference for (a) ("preferred — it makes the value the module's published contract rather than a re-derivation").

**Blast radius of adding `anchorDate: string | null` to `NewsFacetIndex`:**
- `newsFacets.ts`: add one field to the interface (line ~71-77) and one line in the return statement (line 252) — `newestDate` already exists as a local, just needs to be added to the returned object. Trivial, ~2 lines.
- `newsFacets.test.ts`: Test 1 (`empty incidents array returns all-empty facets`, line 36-45) currently does an exact `toEqual` match against the full returned shape — **this test WILL break** the moment `anchorDate` is added to the return object, because `toEqual` is exhaustive. It needs one line added: `anchorDate: null` in both the expected object in Test 1 and likely a new dedicated test asserting `anchorDate` equals the max date across a small fixture. Every OTHER existing test in the 20-test suite that does NOT use exhaustive `toEqual` (partial assertions via `.toBe`/`.some`) is unaffected — but this must be verified test-by-test at execution time, not assumed.
- `facets.mjs`: no assertion currently reads `newestDate`/`anchorDate` from the rendered page, so no existing assertion breaks; a NEW assertion should be added (Q5) to check the rendered `#news-facets.anchorDate` equals the independently-recomputed max date from raw `current.json`.
- `news.astro` / `es/noticias.astro`: `facetsProjection` object gains `anchorDate: facets.anchorDate` (one line each, mirrors the existing `byFamily`/`byRegion`/`byMonth` pattern already there) — automatically covered by the existing `escapeForInlineScript` call (Pitfall 4, no new escaping site).
- Template rendering: `t.news_window_latest.replace('{date}', formattedAnchor)` where `formattedAnchor = anchorDate ? new Date(anchorDate + 'T00:00:00Z').toLocaleDateString(locale, { month: 'short', day: 'numeric' })` — per UI-SPEC's explicit formatting instruction (never reuse `formattedDate`, which formats `generated`, not `anchorDate`).

**Option (b) — `incidents[0].date`** was considered and rejected as the primary recommendation: while `news.astro:97` does sort `incidents` newest-first before rendering, deriving the anchor date this way at the template-render call site (rather than inside `newsFacets.ts`) means it is NOT part of the module's published contract and a future consumer of `computeNewsFacets()` (e.g., a future page) would need to re-derive it identically — exactly the kind of re-derivation F-20's contract language was written to avoid. Use (a).

### Q7 — Zero-JS / CLS / hydration facts (verified via live build)

- **Confirmed via full read of both `.astro` files:** neither page currently ships ANY `<script>` element of any kind (not even the `#news-facets` node — that's `type="application/json"`, inert, non-executable). Both pages are, today, 100% zero-client-JS.
- **Adding the new filter `<script>` (no `client:` directive) does NOT create an Astro island.** Confirmed by the existing precedent at `communes/index.astro:170-307` — that page has a bare `<script>` block with TypeScript type annotations (`as HTMLElement`, `: string`) that Astro's build pipeline transpiles/strips and inlines into the built HTML as a plain `<script>` tag; it is NOT hydrated, NOT a React/island component, and ships as ordinary parsed-and-executed page JS exactly like a hand-written `<script>` in plain HTML. This is the correct, established mechanism for "progressive enhancement, zero framework" per the milestone's locked "Map controls: native `<details>`/`<dialog>` + CSS" decision extended to news faceting (UI-SPEC Decision 3).
- **astro-check baseline: confirmed 4 errors, 0 warnings, 38 hints** — reran `npm run check` live during this research (`08:29:55`, same session): `4 errors` exactly matches STATE.md's stated baseline. All 4 errors are in `scripts/validate/*.mjs` (unrelated tooling files, not phase-28 scope) per the hint/warning breakdown shown. **The plan should assert "4 errors, baseline unchanged" as the gate, not "0 errors."**
- **Build size / page count: confirmed live — `npm run build` completed in 22.9s, 834 pages built.** This is far under the 18,000-page internal budget and the 20,000-file Cloudflare free-tier ceiling; Phase 28 adds zero new pages by design (query-param client state only, per the locked facet-URL-strategy decision), so this number should not move.
- **No CLS mechanism exists in this design by construction:** the `<details open>` element (UI-SPEC's filter bar) ships `open` in the initial server-rendered HTML at every breakpoint (no JS ever adds/removes `open`), and all `.news-card`/`.news-month-section` elements are rendered visible (`hidden` absent) by default — the filter script only ever adds `hidden` in response to a URL param already present at parse time (before first paint, since it reads `location.search` synchronously) or a later user interaction (not a layout-shifting event, since `hidden` collapses an already-rendered box, it doesn't insert new content above the fold after paint). This satisfies NEWSUI-06's "no measurable CLS" requirement by design, not by measurement — flag for the planner that a Lighthouse/CLS spot-check is still a reasonable manual verification step even though the design should not regress it structurally.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| (n/a — Phase 27 shipped `computeNewsFacets()` as build-time-only, no client consumption) | Phase 28 adds client-side reading of DOM attributes for filtering; `#news-facets` remains build-time-only for INITIAL unfiltered counts | This phase | `#news-facets`'s scope stays exactly what Phase 27 shipped (F-20: "unfiltered marginal totals... Phase 27 ships the base index only") — Phase 28 does not need to (and per Q3, should not) expand that payload |

**Deprecated/outdated:** none — this is the first client-JS behavior these two pages have ever shipped; there is no prior pattern being replaced, only the "no client JS at all" baseline being extended.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | The recommended `data-date` (raw ISO date per card) approach for window filtering is preferred over a pre-baked `data-window` tag | Q6 | Low — both are implementable; if the planner prefers pre-baked tags for simplicity, the risk is a possible (currently theoretical, not observed) drift between server and client window-boundary logic, mitigated by a Q5-style validator assertion either way |
| A2 | `newsFacets.test.ts` Test 1's exhaustive `toEqual` is the only test that breaks when `anchorDate` is added to `NewsFacetIndex` | Q4 | Medium — this was reasoned from the visible test file structure (20 tests, only Test 1 read in full at line 36-45) rather than every one of the 20 tests being individually re-read; the executor must run the actual suite after the change and treat any other failure as equally expected, not a regression to work around |

## Open Questions

1. **Exact tie-break for which filter-option counts are "cross-filtered" vs "marginal" when multiple filter dimensions are simultaneously active** (e.g., with `family=drogas&region=13` active, should the *region* checkboxes' counts reflect only the family filter, or the family+window filters too, but not the region filter itself — the standard faceted-search UX pattern of "exclude this facet's own filter when computing its own counts")?
   - What we know: UI-SPEC says "per-option counts recompute client-side from [DOM] once any filter is active" but does not specify per-dimension exclusion semantics.
   - What's unclear: whether region checkbox counts should self-exclude the region filter (standard faceted search UX) or reflect the fully-filtered set (simpler code, arguably confusing UX — a checked option's own count would show the post-filter total, which is trivially "all currently visible cards", not useful).
   - Recommendation: implement standard faceted-search self-exclusion (each dimension's counts are computed with every OTHER active filter applied, but not its own) — this is the only semantically useful behavior and is a bounded, well-known algorithm (three passes, each excluding one dimension) well within the volume this page handles. Planner should make this an explicit task, not leave it implicit.

## Environment Availability

Skipped — no external dependencies beyond what's already installed and verified working (Node/npm, Astro build toolchain, vitest). No new CLI tool, service, or runtime is introduced by this phase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | vitest (already installed; `newsFacets.test.ts` is the existing real spec, 20 tests) |
| Config file | `site/vitest.config.*` (existing, unmodified by this phase) |
| Quick run command | `cd site && npx vitest run src/lib/newsFacets.test.ts` |
| Full suite command | `cd site && npm test` (= `vitest run`, per `package.json` line 14) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| NEWSUI-01 | Per-option facet counts (server, unfiltered) | unit | `npx vitest run src/lib/newsFacets.test.ts` | ✅ (existing) |
| NEWSUI-01 | Cross-filtered client-side count recomputation | build validator | `node scripts/validate/facets.mjs` extended (Q5) — client logic itself is inline `<script>`, not independently unit-testable without extraction (see below) | ❌ Wave 0 — new assertion needed |
| NEWSUI-02 | Unfiltered superset present in static HTML with JS disabled | build validator + manual | `curl -s http://localhost:4321/news/ \| grep -c 'news-card'` count matches `current.json` incident count; manual JS-disabled browser check | ❌ Wave 0 — add a simple grep-count assertion to `facets.mjs` or a new light validator |
| NEWSUI-03 | Accent-insensitive typeahead matches `communes/index.astro` behavior | manual (BrowserOS or local dev server click-through) | n/a — behavioral, DOM-interaction test; see note below | manual-only, justified: no existing DOM-interaction test harness (Playwright/Testing-Library) exists in this repo for `.astro`-rendered pages |
| NEWSUI-04 | Query-param round-trip + empty state | build validator (static assertions) + manual (interactive round-trip) | `facets.mjs` extended checks the empty-state node exists with `hidden` in dist HTML; manual click-through for round-trip | ❌ Wave 0 (static half) / manual (interactive half) |
| NEWSUI-06 | `#news-facets` escaping intact if `anchorDate` added | build validator | `node scripts/validate/facets.mjs` (assertion 7 already covers this — no new assertion needed since `anchorDate` folds into the SAME `facetsProjection` object already covered) | ✅ (existing assertion 7 extends automatically) |
| NEWSUI-07 | EN/ES parity of new i18n keys | build validator | new `facets.mjs` (or `i18n.mjs`, check if one exists) assertion: both `EN_STRINGS` and `ES_STRINGS` define all 14 new keys, no key present in one but not the other | ❌ Wave 0 — new assertion needed |

**On unit-testing the inline `<script>` filter logic directly:** confirmed by reading `communes/index.astro:170-307` — this codebase's inline page scripts are NOT extracted into a separately-imported, separately-unit-testable module; they are self-contained IIFEs written directly in the `.astro` file. Astro does NOT provide a supported mechanism for an inline `<script>` (no directive) to `import` from a `.ts` file without turning it into a bundled client entry point (which would change its zero-`client:`-directive status and is out of scope for this phase — the milestone's zero-new-frontend-deps and zero-React-island constraints don't forbid this specifically, but doing so would be a new architectural pattern not asked for by the phase and not present anywhere else in the codebase). **Recommendation:** if the pure predicate logic (window-bucket boundary math, self-exclusion count logic) needs regression protection, extract it into a small pure-function module (e.g., `site/src/lib/newsFilterLogic.ts`) that is (a) unit-tested directly via vitest, AND (b) its exact source is duplicated (copy-pasted, small — the window logic is ~15 lines per Q6) into each page's inline `<script>`, the same way `norm()` is currently copy-pasted rather than imported. This gives real unit-test coverage of the ALGORITHM without creating a new "shared client bundle" architecture. State plainly: the inline `<script>` itself, as shipped in the page, is not directly unit-testable — only a duplicated pure-function twin can be.

### Sampling Rate
- **Per task commit:** `cd site && npx vitest run src/lib/newsFacets.test.ts`
- **Per wave merge:** `cd site && npm run build && npm run validate` (chained per OneDrive rule) — this runs `npm test` internally? **Verify at plan time**: confirm whether `npm run validate` (the 16-validator runner, `scripts/validate/all.mjs`) also invokes `vitest`, or whether `npm test` must be run as a separate step in the same chained command. Based on `package.json` line 14 (`"test": "vitest run"`) being a distinct script from `"validate"`, the safe assumption is **both must be chained explicitly**: `npm run build && npm test && npm run validate`.
- **Phase gate:** Full suite green (`npm test` + `npm run validate`, all 16-and-growing validators) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `facets.mjs` assertion for `anchorDate` correctness (independently recompute max date from raw `current.json`, compare against rendered `#news-facets.anchorDate` in both dist pages) — falsifiable counterexample: mutate a fixture's newest incident's date backward by one day; assertion must fail.
- [ ] `facets.mjs` (or new `i18n-parity.mjs`) assertion that all 14 new `news_*` i18n keys exist in both `EN_STRINGS` and `ES_STRINGS` — falsifiable counterexample: delete one ES key; assertion must fail.
- [ ] `facets.mjs` assertion that `dist/news/index.html` and `dist/es/noticias/index.html` contain the SAME NUMBER of `.news-card` occurrences as `current.json` incidents (progressive-enhancement / NEWSUI-02 static-superset guard) — falsifiable counterexample: truncate a test fixture's incident list before render; assertion must fail (requires care to not double-count `data-*`-attribute strings that happen to contain the class name — match on the actual `class="news-card"` opening-tag pattern, not a substring anywhere in the page).
- [ ] If `newsFilterLogic.ts` pure-function extraction (recommended above) is adopted: `newsFilterLogic.test.ts` — mutation-tested per Operating Lesson 11 (v2.1 directive): break the exact 7-day boundary width, confirm RED, restore, confirm GREEN.
- [ ] Framework install: none — vitest already present.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|--------------------|
| V2 Authentication | no | No auth on these pages |
| V3 Session Management | no | No session state — query-param + `history.replaceState` only |
| V4 Access Control | no | Public static content |
| V5 Input Validation | yes | Every client-read `data-*` attribute value and URL query-param value used in DOM comparisons only (never `innerHTML`'d except the pre-existing trusted `data-name` highlight pattern, which this phase does not touch for family/title/outlet) — matches UI-SPEC §LLM-derived string escaping |
| V6 Cryptography | no | Not applicable |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| XSS via `</script>` breakout in `set:html`-rendered JSON (LLM-classifier-derived `family`/`title` strings) | Tampering / Elevation of Privilege (client-side) | `escapeForInlineScript()` (existing, `newsFacets.ts:103-105`) — already covers `facetsProjection`; if `anchorDate` is added to the same object it is automatically covered (Pitfall 4). No new field should ever get a second unescaped `set:html` call. |
| Reflected content via `?q=` typeahead search param | Tampering (client-side, low severity — no server round-trip) | `input.value = initialQ` assignment only, NEVER `innerHTML` (T-12-01 rule, already the established pattern at `communes/index.astro:279-284`); highlight rendering slices the TRUSTED `data-name`/`data-commune-norm` attribute around the match index, never injects the raw query string into the DOM (T-11-05 rule) |
| Malformed/hostile `family`/`region`/`window` query-param values | Tampering | Client script must treat every param as untrusted: compare against a fixed allowlist of known family keys / region ids (both already known at build time as `data-*` values present in the DOM) rather than blindly trusting the URL; an unrecognized value should degrade to "no match for this filter" (empty result + empty state), never throw or produce a broken page |

## Sources

### Primary (HIGH confidence — read directly from repo, or measured via live command)
- `site/src/pages/news.astro` (full read) — render structure, `#news-facets` wiring, existing classes/attributes
- `site/src/pages/es/noticias.astro` (full read) — confirmed byte-identical structure to EN, only copy differs
- `site/src/lib/newsFacets.ts` (full read) — module contract, `newestDate`/window logic, `escapeForInlineScript`
- `site/src/lib/newsFacets.test.ts` (partial read, lines 1-60) — existing test shape, `toEqual` exhaustiveness in Test 1
- `site/scripts/validate/facets.mjs` (full read) — all 10 assertions, F-24's 7-load-bearing/3-not finding, per-locale dist-check pattern (assertion 7)
- `site/scripts/validate/all.mjs` (grep) — validator #16 registration, VALIDATORS array
- `site/src/pages/communes/index.astro` lines 150-307 (full read) — `norm()`, `data-name`/`data-norm`, inline non-modular script pattern, `?q=` param handling, `hidden`/`style.display` mixed precedent
- `site/src/lib/familyDefs.ts` (full read) — `FAMILY_LABELS_EN`/`FAMILY_LABELS_ES` keys, confirms `sexuales` absent from `familyDefs.ts` (news-only family, matches F-20/FACET-04)
- `site/src/config/i18n.ts` (grep for `dir_search_placeholder`) — confirmed existing key pattern UI-SPEC's `news_search_comuna_placeholder` should mirror
- `site/package.json` (grep) — `"check": "astro check"`, `"test": "vitest run"` script names
- Live command: `node -e "..."` computing `facetKeys` serialization size against real `site/public/data/incidents/current.json` — **measured 121,626 bytes** for 1,215 incidents (Q3)
- Live command: `npm run build` — **834 pages, 22.9s**, then `npm run check` — **4 errors, 0 warnings, 38 hints**, all 4 errors in unrelated `scripts/validate/*.mjs` tooling files (confirms STATE.md's stated baseline)
- `.planning/phases/28-news-visualizer-ui/28-UI-SPEC.md` (full read) — binding design contract
- `.planning/REQUIREMENTS.md` (full read) — NEWSUI-01..07, locked decisions table
- `.planning/ROADMAP.md` Phase 28 section (grep) — goal, success criteria, dependencies
- `.planning/v2.1-AUTONOMOUS-DIRECTIVE.md` (full read) — run contract, Operating Lessons 1-13
- `.planning/STATE.md` (Phase 27 Outcome, Phase 26 Outcome, Fable Decisions sections) — F-20 published contract, four things Phase 28 must handle, F-24 assertion-count caveat
- `CLAUDE.md` (project instructions, provided in system context)

### Secondary (MEDIUM confidence)
None used — every claim in this research was verifiable directly against repo source or a live command in this session.

### Tertiary (LOW confidence)
None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies, entire stack already installed and verified building successfully live in this session
- Architecture: HIGH — every pattern is a direct extension of an existing, fully-read precedent (`communes/index.astro`) or an already-shipped module (`newsFacets.ts`)
- Pitfalls: HIGH — all four pitfalls are documented project memory or directly observed in source, not speculative

**Research date:** 2026-07-30
**Valid until:** 14 days (fast-moving — this is the run's active phase; do not treat as stale-but-usable past the next `data/incidents/current.json` cron refresh, since incident counts feed the byte-size measurement in Q3, though the magnitude conclusion (DOM-derive, don't serialize) holds regardless of exact count)
