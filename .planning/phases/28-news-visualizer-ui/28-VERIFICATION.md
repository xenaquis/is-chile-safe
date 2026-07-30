---
phase: 28-news-visualizer-ui
verified: 2026-07-30T11:05:00Z
status: passed
score: 5/5 success criteria verified; 7/7 requirements satisfied
verifier: Opus (gsd-verifier), goal-backward, FORCE stance
re_verification:
  previous_status: none
  note: initial verification of Phase 28
environmental_exclusions:
  - item: "freshness validator RED (data/incidents/current.json 3.0 days old)"
    governed_by: "F-19 / F-33 / F-34 — STATE.md § Blockers"
    confirmed: "failure output is EXACTLY the age assertion; not a phase defect; not remediated"
gaps: []
deferred: []
---

# Phase 28: News Visualizer UI — Verification Report

**Phase Goal:** A user on `/news/` or `/es/noticias/` can filter incidents by time window, region, and crime family with visible per-option counts, search comunas by typeahead instead of scanning a 346-item list, and — if Phase 26 was GO — see multi-source coverage grouped into one card; the whole experience stays fully indexable and zero-JS-required for content visibility.

**Verified:** 2026-07-30
**Status:** PASSED
**Re-verification:** No — initial verification.

> **Method note.** Nothing below is taken from a SUMMARY. Every claim was re-derived by running the build, the validators, the test suites, and — for the load-bearing invariants — by transpiling the *shipped* `newsFilterLogic.ts` and executing it against the *shipped* `dist/` HTML.

---

## 0. Baseline re-confirmation (executed this session)

| Check | Command | Result | Matches declared state |
|---|---|---|---|
| Build | `npm run build` | exit 0, **834 pages** in 24.16s | — |
| astro check | `npx astro check` | **4 errors / 0 warnings**, all four `ts(7031)` at `src/components/ComparatorPairsLinks.astro:28` (`cutA`,`cutB`,`nameA`,`nameB`) | YES — pre-existing, untouched by Phase 28 |
| vitest | `npx vitest run` | **37 passed / 3 files** | YES |
| facets validator | `node scripts/validate/facets.mjs` | PASS — 1215 incidents, 8 families, 346 communes, 3 months, `window(today=11,7d=297,30d=1215)`, TZ-determinism verified, **22 assertions passed** | YES |
| Full validator suite | `node scripts/validate/all.mjs` | **15/16**, only `freshness` FAIL | YES |
| freshness detail | `node scripts/validate/freshness.mjs` | `FAIL … is 3.0 days old (generated: 2026-07-27T14:25:05.303451Z)` — exactly the age assertion, not missing-file, not unparseable | YES — F-19 precondition (a) holds |
| pytest | `python -m pytest pipeline/tests -q` | **344 passed / 1 skipped / 1 xfailed** | YES — the Phase 26 gate xfail is still xfailed, not "fixed" |

`freshness` is excluded per the pre-declared F-19 environmental exclusion (STATE.md § Blockers). **Not scored against this phase. Not remediated — `MAX_AGE_DAYS` untouched, validator untouched, no `git pull`.**

---

## 1. Success Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Filter by time window, region, crime family with per-option counts visible, on both pages | **PASS** | Both `dist/news/index.html` and `dist/es/noticias/index.html` contain 3 server-rendered `<fieldset data-facet="window|region|family">` blocks + a comuna-search group, with **28 `class="filter-count"` spans on each page** (4 window + 16 region + 8 family). Counts are pre-rendered *values*, not placeholders — see §3 for the executed server↔client agreement proof. |
| 2 | Unfiltered superset fully present in static pre-rendered HTML; filtering is progressive enhancement only | **PASS** | `<article class="news-card">` count = **1215 on EN and 1215 on ES**, matching the 1215 incidents facets.mjs counts. `<article class="news-card" … hidden>` = **0** on both. `astro-island` = **0**. `client:` directives = **0**. The only JS is one deferred `<script type="module" src="/_astro/…">`; nothing is hidden or constructed before it runs. Month sections carrying `hidden` at rest = 0. |
| 3 | Accent-insensitive comuna typeahead reusing the directory-finder pattern | **PASS** | `norm()` in `newsFilterLogic.ts:54-60` is the `communes/index.astro:174-176` algorithm verbatim (`.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase()`) plus `.trim()` (WR-06). Executed against shipped dist cards: `"  Viña del Mar "` → **21 matches**, `"vina del mar"` → **21 matches** — identical, on both locales. Substring search over 346 pre-rendered comuna values replaces the flat list. |
| 4 | Filter state round-trips through shareable query params; zero-result combination renders a clear bilingual empty state never indexed as a thin page | **PASS** | Executed round-trip: `serializeFilterParams({family:['vida'],region:['1'],window:'7d',q:'la florida'})` → `family=vida&region=1&window=7d&q=la+florida` → `parseFilterParams` returns the **byte-identical** object on both locales. Hostile input `?window=%3Cscript%3E&family=` degrades to `{family:[],region:[],window:'',q:''}` without throwing. Empty state: `<div id="news-empty" hidden …>` present on both pages, contents are two `<p>` elements (EN "No incidents match these filters" / ES "Ningún incidente coincide con estos filtros") — **not a heading**, ships `hidden`, and creates **no URL**. Canonicals are the bare paths (`https://ischilesafe.com/news/`, `https://ischilesafe.com/es/noticias/`); zero internal `<a href>` carries `?family=/?region=/?window=/?q=`; no query-string `<link rel="alternate">`. A zero-result combo was executed and returns 0 matching cards, which drives `emptyEl.hidden = false` (news.astro:402). |
| 5 | Clustering half N/A on Phase 26 NO-GO → faceting only; LLM text escaped; no CLS/hydration regression; EN/ES parity via `i18n.ts` | **PASS** | **Clustering (correctly absent):** zero occurrences of `news_cluster_source_count`, `data-cluster`, or any cluster badge markup in either dist page; `news_cluster_source_count` exists in `i18n.ts` (EN `'{n} sources'` / ES `'{n} fuentes'`) as a reserved, unconsumed key. Gated by facets.mjs assertion 16. **Escaping:** the only `set:html` is `escapeForInlineScript(JSON.stringify(facetsProjection))` (`newsFacets.ts:104` → `.replace(/</g,'\\u003c')`), one occurrence per page; all card text (titles, outlet, family labels) goes through Astro's auto-escaping `{expr}`; `grep innerHTML` on both shipped chunks = **0**. **Hydration/CLS:** no island, no `client:`, no `document.write`; the filter bar and all 28 counts are server-rendered with final values, so the default (no-param) load performs zero DOM mutation. **Parity:** 15 `news_*` keys declared in the interface, 15 EN, 15 ES; both pages reference `t.news_*` **15 times each**; no per-locale inline literal. |

**Score: 5/5.**

---

## 2. Requirements Coverage (NEWSUI-01..07)

| Req | Status | Evidence executed |
|---|---|---|
| NEWSUI-01 | **SATISFIED** | 28 pre-rendered per-option counts per page on both locales; F-28 self-exclusion implemented in `computeFacetCounts`/`cardMatchesFilters` (`newsFilterLogic.ts:161-220`) with `q` applied cross-cuttingly; wired to change listeners for window/region/family/comuna and a clear button (`news.astro:477-516`). |
| NEWSUI-02 | **SATISFIED** | 1215/1215 cards in static HTML on both locales, **0 hidden at rest**, 0 `astro-island`, 0 `client:`, 0 inline `style="display:none"` on cards. Gated by facets.mjs assertion 12 (hardened by WR-02/WR2-02/WR2-03). |
| NEWSUI-03 | **SATISFIED** | See criterion 3. Accent- and whitespace-insensitivity proven by execution against the shipped corpus (21 == 21). |
| NEWSUI-04 | **SATISFIED** | See criterion 4. Also verified WR-01's fix in the shipped source: `applyFilters` starts from `new URLSearchParams(location.search)`, deletes only the four owned keys, re-sets them, and emits `location.pathname + (qs ? '?' + qs : '') + location.hash` — unknown params (`utm_source`, `gclid`) survive and no bare `?` is produced. Gated at source level by assertion 22. |
| NEWSUI-05 | **SATISFIED (NO-GO branch, by design)** | Phase 26 returned NO-GO (precision 0.667 vs a 100%/zero-false-merge gate). The page ships faceting only; no cluster markup exists anywhere in dist; the i18n key is reserved and unconsumed. This is the specified degradation, **not a gap**. |
| NEWSUI-06 | **SATISFIED** (escaping by execution; CLS by construction) | Escaping proven above. "No measurable CLS/hydration regression" is structurally guaranteed — no island, no JS-created DOM, all counts and the result-count sentence server-substituted (`1215 incidents shown` / `1215 incidentes mostrados`; zero literal `{date}`, and the single literal `{n}` per page lives only inside the deliberate `data-result-count-template` carrier). A *numeric* CLS measurement remains browser-only (see §5). |
| NEWSUI-07 | **SATISFIED** | 15/15/15 key parity in `i18n.ts`; both pages consume `t.news_*` exclusively (15 references each); gated by facets.mjs assertion 13 (digit-safe EN/ES parity). ES page reachable at the hardcoded localized slug `/es/noticias/`. |

---

## 3. Key Link Verification — server counts ↔ client filter logic

The highest-value check, because a facet UI whose displayed counts disagree with the list it filters is a published factual error. I transpiled the **shipped** `src/lib/newsFilterLogic.ts` and ran it over the card `data-*` attributes extracted from the **shipped** dist HTML, comparing its output to the server-rendered `.filter-count` values.

| Locale | Cards parsed | Anchor date derived | Window counts (client) | Options compared | Mismatches |
|---|---|---|---|---|---|
| EN `/news/` | 1215 | `2026-07-27` | `{today:11, 7d:297, 30d:1215}` | 4 window + 8 family + 16 region = 28 | **0** |
| ES `/es/noticias/` | 1215 | `2026-07-27` | `{today:11, 7d:297, 30d:1215}` | 28 | **0** |

Client-derived window counts equal the `newsFacets.ts` build-time values reported by facets.mjs (`today=11, 7d=297, 30d=1215`) exactly — i.e. **server/client window-boundary equivalence is verified by execution, not by shared-source assumption.** The `Latest data:` chip renders `Jul 27` / `27 jul`, the correct UTC anchor (F-32a).

### F-27 bundling (shipped code == tested code)

| Fact | Evidence |
|---|---|
| One shared module, not a copy-pasted twin | `dist/_astro/newsFilterLogic.CQ0hTsM2.js` is the **only** file containing `newsFilterLogic/v1`. |
| Both pages import it | `news.astro_…BL4BH8y7.js` and `noticias.astro_…BL4BH8y7.js` both begin `import{F as L,p as B,c as S,a as y,s as F}from"./newsFilterLogic.CQ0hTsM2.js";` — identical content hash, confirming byte-identical logic across locales. |
| No hydration framework pulled in | Neither chunk contains `innerHTML`; neither page contains `astro-island`. |

---

## 4. Anti-patterns / observations (none blocking)

| Item | Severity | Note |
|---|---|---|
| facets.mjs assertion 19 is labelled "canonical + **route count unchanged**" but asserts only canonical correctness + absence of query-param internal links | ℹ️ Info | A naming overstatement in a comment, not a coverage gap for this phase. Route-count invariance is nonetheless **verified by construction**: the complete non-planning diff for Phase 28 touches only `newsFilterLogic.ts(+.test)`, `newsFacets.ts(+.test)`, `i18n.ts`, `news.astro`, `es/noticias.astro`, `facets.mjs`, `all.mjs`, `package.json`, `.gitignore` (plus `pipeline/` from Phase 26) — **no new route-producing file, and no `getStaticPaths` added**. Worth a one-line comment fix in a future `/gsd:quick`. |
| `{n}` appears once per dist page | ℹ️ Info | Inside `data-result-count-template` only — the deliberate F-35 carrier. Visible text is server-substituted. |
| WR2-05, F-24's three true-by-construction original assertions, N1 (`?region=` namespace split), N4 ("All dates" count not recomputed client-side) | ℹ️ Info | Previously recorded and accepted in STATE.md. Re-confirmed present, re-confirmed non-blocking. Not new findings. |
| 4 `astro check` errors | ℹ️ Info | Pre-existing, in a file Phase 28 does not touch. |

No `TBD` / `FIXME` / `XXX` debt markers were introduced by this phase's source changes.

---

## 5. What remains genuinely unverifiable without a browser (N3)

The functional half of the deferred manual pass was verified statically by executing the shipped module against the shipped HTML (typeahead matching, count arithmetic, URL round-trip, zero-result path, month-collapse predicate at `news.astro:395-400`). What a static pass cannot establish, and what a human should spot-check when convenient — **none of it blocking**:

1. **Numeric CLS / INP measurement.** Structurally there is nothing that can shift (no island, no JS-injected nodes), but the metric itself needs a browser.
2. **Visual rendering of the filter bar** — the `<details open>` chip layout at 375px, chip wrapping, and whether the 16-region + 8-family chip grid is comfortable on mobile.
3. **Keyboard / focus behaviour** of the chips and the search input, and screen-reader announcement of the `role="status" aria-live="polite"` result count.
4. **Real JS-off render.** Verified by construction (0 hidden cards, 0 islands in the served HTML), but not observed in a real browser with scripting disabled.

---

## Verdict

**PASSED — 5/5 success criteria, 7/7 requirements.**

The phase goal is achieved in the codebase, not merely in its SUMMARYs. Both locales ship the complete 1,215-incident superset in static HTML with zero cards hidden at rest and zero hydration, a server-rendered three-dimension facet bar whose 28 counts were proven by execution to agree exactly with the client logic that filters the list, an accent- and whitespace-insensitive comuna search reusing the established pattern, an exact query-param round trip that preserves foreign params, and a hidden, non-heading, bilingual empty state that adds no indexable URL. NEWSUI-05's clustering half is correctly absent on the Phase 26 NO-GO. The single red validator is the pre-declared F-19 environmental `freshness` exclusion and is not a phase defect.

No gaps. Ready to proceed to Phase 29.

---

_Verified: 2026-07-30 — Claude (gsd-verifier), goal-backward / FORCE stance_
