---
phase: 02-astro-site-programmatic-pages
reviewed: 2026-06-13T00:00:00Z
depth: standard
files_reviewed: 33
files_reviewed_list:
  - site/astro.config.mjs
  - site/src/env.d.ts
  - site/src/config/i18n.ts
  - site/src/lib/data.ts
  - site/src/lib/colorScale.ts
  - site/src/lib/slugMaps.ts
  - site/src/lib/proseEngine.ts
  - site/src/layouts/BaseLayout.astro
  - site/src/components/CommuneRankingTable.astro
  - site/src/components/ComparableCommune.astro
  - site/src/components/ComparisonCallout.astro
  - site/src/components/FamilyBreakdownBars.astro
  - site/src/components/LevelChip.astro
  - site/src/components/MapPlaceholderSlot.astro
  - site/src/components/MethodologyCaveat.astro
  - site/src/components/PageFooter.astro
  - site/src/components/PageHeader.astro
  - site/src/components/Sparkline.astro
  - site/src/components/StatCard.astro
  - site/src/components/TrendChip.astro
  - site/src/pages/index.astro
  - site/src/pages/es/index.astro
  - site/src/pages/commune/[slug].astro
  - site/src/pages/es/comuna/[slug].astro
  - site/src/pages/region/[slug].astro
  - site/src/pages/es/region/[slug].astro
  - site/src/pages/crime/[family].astro
  - site/src/pages/es/delito/[family].astro
  - site/scripts/validate/all.mjs
  - site/scripts/validate/commune.mjs
  - site/scripts/validate/region.mjs
  - site/scripts/validate/crime.mjs
  - site/scripts/validate/rollout.mjs
  - site/scripts/validate/hreflang.mjs
  - site/scripts/validate/schema.mjs
  - site/scripts/validate/structure.mjs
findings:
  critical: 2
  warning: 6
  info: 5
  total: 13
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-13
**Depth:** standard
**Files Reviewed:** 33
**Status:** issues_found

## Summary

Reviewed the Astro SSG programmatic-page layer (data loader, prose engine, layout, 8 page routes, 13 components, 7 validators) for the Chile Safety Map. The data-loading discipline around the SUM-vs-MEAN pitfall is consistently correct — every vs-average comparison uses `loadNationalAverage()`/`loadRegionalAverage()`, and `latestCompleteYearRate()` correctly filters partial years. JSON-LD is serialized through `JSON.stringify()` + `set:html`, which is safe.

However, two correctness bugs will ship broken pages: the commune breadcrumb links to a region URL built from the **commune** slug (every commune page links to a 404 region), and the crime-page `latestYear` lookup can silently fall back to a hardcoded Santiago CUT. Several warnings concern ranking-tier boundary logic, an inconsistent `toLocaleString` locale on ES crime pages, the `set:html` on prose, and a likely-incorrect `bottom25` tier band. The structural-findings substrate was not provided with this prompt.

## Critical Issues

### CR-01: Commune breadcrumb links to region URL built from the commune slug — every commune page links to a broken/incorrect region page

**File:** `site/src/pages/commune/[slug].astro:122` (and identical bug at `site/src/pages/es/comuna/[slug].astro:123`)

**Issue:** The breadcrumb "region" link is constructed from `data.slug`, which is the **commune** slug, not the region slug:

```astro
<a href={`/region/${data.slug}/`}>{data.regionName}</a>
```

Region pages are built at `/region/{region.slug}/` (see `region/[slug].astro` getStaticPaths, which uses `region.slug`). For example, the Santiago commune page renders a link to `/region/santiago/` while displaying the text "Metropolitana" — that URL does not exist (the region page lives at `/region/metropolitana/`), so the breadcrumb is a guaranteed 404 on every commune page. The ES variant has the same defect (`/es/region/${data.slug}/`). The available data does not expose the region slug on `CommuneData`, so the fix requires loading it.

**Fix:** Resolve the region slug instead of reusing the commune slug. In the frontmatter:
```ts
import { loadRegion, regionFileId } from '../../lib/data.ts';
const regionSlug = loadRegion(regionFileId(data.region_id)).slug;
```
Then:
```astro
<a href={`/region/${regionSlug}/`}>{data.regionName}</a>
```
(ES: `/es/region/${regionSlug}/`). Alternatively, enrich `loadCommune()` to also return `regionSlug` alongside `regionName` (it already loads the region object at `data.ts:150`), avoiding a second `loadRegion()` call.

### CR-02: Crime-page `latestYear` silently falls back to a hardcoded Santiago CUT ('13101'), producing a wrong year for any page where the top-ranked commune slug is not found

**File:** `site/src/pages/crime/[family].astro:139-141` (and identical at `site/src/pages/es/delito/[family].astro:129-131`)

**Issue:**
```ts
const latestYear = eligibleRows[0]
  ? (loadCommune(index.find((c) => c.slug === eligibleRows[0]!.slug)?.cut ?? '13101' ).latestCompleteYear)
  : new Date().getFullYear() - 1;
```
`eligibleRows[0].slug` was copied from `meta.name`/`meta.slug` in the same loop, so the `index.find(... slug === ...)` lookup should normally succeed — but if it ever does not (slug collision, data drift, or a commune whose slug is non-unique), the `?? '13101'` fallback loads Santiago and uses **Santiago's** latest complete year for an unrelated crime page. This is a silent wrong-data path: the displayed "(year)" in headings, the ranking-table heading, the region-breakdown heading, and `temporalCoverage` in JSON-LD would all show a year that does not correspond to the data actually rendered. The double round-trip (build `eligibleRows`, then re-`loadCommune` to recover a year that was already available) is also fragile. Worse, `eligibleRows[0]` only sorts by *family* rate; the year is taken from whichever commune happens to top *that family*, which is an indirect way to get a value that every commune already carries.

**Fix:** Capture `latestCompleteYear` directly in the ranking loop instead of re-deriving it via a slug lookup with a hardcoded fallback. In the `for (const meta of index)` loop you already call `loadCommune(meta.cut)`:
```ts
let latestYear = new Date().getFullYear() - 1;
for (const meta of index) {
  const commune = loadCommune(meta.cut);
  if (!meta.low_population) latestYear = Math.max(latestYear, commune.latestCompleteYear);
  // ...existing row push...
}
```
This removes the `'13101'` magic fallback and the second `loadCommune` round-trip entirely, and makes the year deterministic regardless of slug-lookup outcome.

## Warnings

### WR-01: `rankTier` boundary logic makes the `bottom25` band unreachable / mislabeled for ranks in the 260–311 range

**File:** `site/src/lib/proseEngine.ts:53-63`

**Issue:**
```ts
const bot25 = Math.round(total * 0.75); // 260
const bot10 = Math.round(total * 0.9);  // 311
if (nationalRank <= top10) return 'top10';
if (nationalRank <= top25) return 'top25';
if (nationalRank >= bot10) return 'bottom10';
if (nationalRank >= bot25) return 'bottom25';
return 'mid';
```
The naming is inverted relative to incidence: `national_rank` 1 = highest incidence (per `EN_OPENING.up.top10` "highest reported crime incidence"). So rank 1 → `top10` = "highest incidence", and rank 346 → `bottom10` = "lowest incidence". That is internally consistent. However, the band thresholds use `Math.round` on different fractions and the `mid` range becomes ranks 87–259, while `bottom25` is 260–310. This is defensible, but the comparison `nationalRank >= bot25` (260) combined with `<= top25` (87) leaves a large `mid` block — verify against UI-SPEC that the intended quartile cuts are 0.10/0.25/0.75/0.90 of *rank* rather than of *rate*. If the spec intended tiers by incidence percentile, ranks should be bucketed directly; rounding `total*0.75` for a 346-item list yields 260, not 259 or 261, which can shift a commune between `mid` and `bottom25` by one position versus a naive expectation. Confirm the boundary is the intended one (off-by-one risk at the 260 and 311 edges).

**Fix:** Add an explicit comment documenting that rank 1 = highest incidence and that bands are rank-percentile (not rate-percentile), and assert the edges with a unit test (e.g. rank 87 → top25, rank 260 → bottom25, rank 311 → bottom10) so the rounding behavior is pinned.

### WR-02: ES crime page formats numbers with default (en-US) locale, breaking ES thousands separators

**File:** `site/src/pages/es/delito/[family].astro:187,224,252` (`Math.round(...).toLocaleString()` with no locale arg)

**Issue:** The ES region page and ES commune page correctly pass `'es-CL'` to `toLocaleString` (e.g. `region/.../es:169`, `comuna/.../es:128,139`), but the ES crime page calls `toLocaleString()` with no argument for the national-mean stat (line 187), each ranking-row rate (line 224), and each region-breakdown value (line 252). On a build host with a non-`es` default locale this renders `1,234` (comma) instead of the Spanish `1.234` (period), inconsistent with the rest of the ES site and with the page's own `por 100.000` copy. The EN crime page is fine.

**Fix:** Pass the explicit locale on every numeric format in the ES crime page: `Math.round(...).toLocaleString('es-CL')`. (For symmetry, the EN crime page should pass `'en-US'` rather than relying on the host default.)

### WR-03: Prose paragraphs rendered via `set:html` — bypasses Astro auto-escaping for no benefit

**File:** `site/src/pages/commune/[slug].astro:189-191` and `site/src/pages/es/comuna/[slug].astro:190-192`

**Issue:**
```astro
{prose.split('\n\n').map((para) => (
  <p set:html={para} />
))}
```
The prose engine produces **plain text only** — there is no HTML in any sentence-bank string. Using `set:html` here disables Astro's automatic escaping. If any interpolated value (commune name, region name, comparable-commune name from CEAD data) ever contains `&`, `<`, or `>` (e.g. a commune name with an ampersand), the output becomes malformed HTML or, in a worst case where upstream data is ever attacker-influenced, an injection vector. Since the prose is plain text, `set:html` provides zero benefit over normal interpolation.

**Fix:** Render with normal (auto-escaped) interpolation:
```astro
{prose.split('\n\n').map((para) => <p>{para}</p>)}
```
This keeps line breaks via separate `<p>` elements and restores escaping.

### WR-04: `nearestComparable` can return the target commune itself when it falls back to the national pool

**File:** `site/src/lib/data.ts:234-270`

**Issue:** When a region has fewer than 2 eligible communes, `candidates` falls back to `pool` (line 244), which is filtered with `c.cut !== targetCut` (line 242), so self-selection is prevented in the fallback path — good. However, the target commune itself may be `low_population`. If the target is low-population, it is excluded from `pool` entirely, but it is still a valid page (commune pages are built for low-pop communes too). The "comparable" then compares a low-pop commune against a pool that never includes peers of similar (tiny) population, and the prose claims "The two communes share a similar incidence tier" (`EN_COMPARABLE_PARA`) — which may be false when the target's rate is volatile/low-pop. The result is a potentially misleading editorial claim of similarity. Not a crash, but a data-quality/editorial-accuracy risk for low-pop commune pages.

**Fix:** When `target.low_population` is true, either suppress the "share a similar incidence tier" sentence or pick the nearest by absolute rate distance without asserting tier similarity. At minimum, gate the "share a similar incidence tier" clause behind `!target.low_population`.

### WR-05: Sparkline x-axis can overflow the SVG width for long series (bar layout uses `barW + 1` spacing without fitting to width)

**File:** `site/src/components/Sparkline.astro:23,36`

**Issue:** `barW = Math.max(2, Math.floor(width / series.length) - 1)` then each bar is placed at `x = i * (barW + 1)`. With `Math.max(2, ...)` the floor can produce a `barW` of 2 (the minimum) when `series.length` is large; the total drawn width becomes `series.length * (2 + 1)` which can exceed `width` (480). For a 20-year CEAD series this is `20 * 3 = 60` (fine), but the guard only protects the *minimum* bar width, not the total — if a series ever exceeds ~160 entries the bars run past the right edge. `overflow: visible` (line 32 inline style) means they will visibly spill rather than clip. Low likelihood given annual data, but the layout math does not actually fit the series to `width`.

**Fix:** Compute `barW` and step from the available width without a hard minimum that breaks the fit, e.g. `const step = width / series.length; const barW = Math.max(1, step - 1);` and place at `x = i * step`. Or set `overflow: hidden` on the SVG style to clip.

### WR-06: `levelForRate` quantile boundaries use `<=` against quantile values that may collide, skewing level distribution when many rates are equal

**File:** `site/src/lib/colorScale.ts:21-30`

**Issue:** `q(p) = sortedRates[Math.floor(n * p)]`. With `n = 346`, `q(0.2) = sortedRates[69]`. The chain `if (rate <= q(0.2)) return 1; ...` assigns level by the value at fixed index positions. If many communes share the same rate (common when rates are rounded to integers, per the pipeline note that map-payload rates are rounded), a single rate value can span multiple quantile breakpoints, so the `<=` comparisons can push a large cluster into one level and starve adjacent levels. Build-time only and non-fatal, but the choropleth/LevelChip distribution may not be the intended even quintiles. Also `Math.floor(n * 0.2)` for `p=1.0`-adjacent indices is guarded by `?? sortedRates[n-1]`, which is correct.

**Fix:** Acknowledged minor — if even quintile *counts* are desired rather than value-threshold quintiles, assign by index rank (`position / n`) rather than by value comparison. Otherwise document that levels are value-threshold quintiles, not equal-count buckets.

## Info

### IN-01: `data.ts` header comment contradicts the implementation (claims `fileURLToPath`, code uses `process.cwd()`)

**File:** `site/src/lib/data.ts:3-8` vs `17-20`

**Issue:** The top JSDoc says `DATA_ROOT is resolved via fileURLToPath(import.meta.url) parent traversal` and "NEVER use process.cwd()", but the actual code (line 20) uses `path.resolve(process.cwd(), '..', 'data', 'cead')` and the inline comment at 17-19 explains the opposite decision. The stale header comment directly contradicts the chosen approach and will mislead the next maintainer.

**Fix:** Delete or rewrite the lines 3-8 JSDoc block to match the `process.cwd()` decision documented at lines 17-19.

### IN-02: PageHeader nav links to `/map` and `/methodology/` which are not built in Phase 2 (dead links until Phase 4)

**File:** `site/src/components/PageHeader.astro:22-23`; `site/src/components/MethodologyCaveat.astro:20`

**Issue:** `mapHref = getRelativeLocaleUrl(locale, '/map')` and `methodHref = '/methodology/'` (`/es/metodologia/`) point to pages not produced in this phase. MethodologyCaveat's header comment acknowledges this is acceptable per the phase boundary; PageHeader does not. These render as site-wide 404 links in every built page until Phase 4.

**Fix:** Acceptable per phase boundary, but add a comment in PageHeader noting the `/map` and methodology links are Phase 3/4 deferrals, mirroring the note already in MethodologyCaveat.

### IN-03: Dead/unused parameters and variables in the prose engine

**File:** `site/src/lib/proseEngine.ts:177,272 (`_dominantPct`); 339-342 (`dominantPct`)`

**Issue:** `EN_FAMILY_PARA`/`ES_FAMILY_PARA` accept `_dominantPct` but never use it. The caller computes `dominantPct` (lines 339-342) solely to pass it into a parameter that is discarded. This is dead computation plus a dead parameter.

**Fix:** Remove the `_dominantPct` parameter from both `*_FAMILY_PARA` functions and delete the `dominantPct` computation at lines 339-342, or actually surface the dominant share in the family paragraph (it would add useful, varied content).

### IN-04: `ComparisonCallout` has a no-op ternary for text color

**File:** `site/src/components/ComparisonCallout.astro:37`

**Issue:** `const colorVar = direction === 'above' ? 'var(--ink)' : 'var(--ink)';` — both branches are identical, so the ternary is dead code.

**Fix:** Replace with `const colorVar = 'var(--ink)';` (or remove and inline).

### IN-05: Magic literal `346` repeated across components and pages instead of a shared constant

**File:** `site/src/pages/commune/[slug].astro:142`; `site/src/components/ComparableCommune.astro:55`; `proseEngine.ts:53` (`total = 346`); EN/ES openers embed "of 346" in dozens of strings

**Issue:** The total commune count `346` is hardcoded in StatCard values, the comparable card, the `rankTier` default, and many sentence-bank strings. If the commune universe changes (CEAD adds/removes communes), these will silently drift out of sync with `loadIndex().length`. The sentence-bank strings cannot be parameterized without a refactor, but the page-level `346` literals can.

**Fix:** Derive the total from `loadIndex().length` (or export a `TOTAL_COMMUNES` constant from `data.ts`) and use it in `rankTier`, the StatCard "of 346", and `ComparableCommune`. Treat the in-prose "346" as a known limitation to revisit if the universe changes.

---

_Reviewed: 2026-06-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
