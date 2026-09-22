---
phase: 21-commune-comparator-a-vs-b-seo
reviewed: 2026-06-20T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - scripts/generate-pairs.mjs
  - site/scripts/validate/all.mjs
  - site/scripts/validate/avs-b-budget.mjs
  - site/scripts/validate/hreflang.mjs
  - site/scripts/validate/spine.mjs
  - site/src/components/ComparatorPairsLinks.astro
  - site/src/components/PageHeader.astro
  - site/src/config/i18n.ts
  - site/src/islands/ComparatorIsland.tsx
  - site/src/lib/comparisonProse.ts
  - site/src/pages/commune/[slug].astro
  - site/src/pages/compare/[pair].astro
  - site/src/pages/compare/index.astro
  - site/src/pages/es/comparar/[pair].astro
  - site/src/pages/es/comparar/index.astro
  - site/src/pages/es/comuna/[slug].astro
findings:
  critical: 0
  warning: 8
  info: 5
  total: 13
status: issues_found
---

# Phase 21: Code Review Report

**Reviewed:** 2026-06-20
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the A-vs-B commune comparator: pair-allowlist generator, three new
validators (budget, hreflang reciprocity check, spine assertion M), the bilingual
deterministic prose engine, the React comparator island, the two static A-vs-B
page routes (EN/ES), the comparator landing shells, and the commune-page
cross-link integration.

Security is sound: every dynamic value (commune names, prose, titles, meta
descriptions) is rendered through Astro `{expr}` or React `{}` auto-escaping —
there is **no `set:html`, `innerHTML`, or `dangerouslySetInnerHTML` anywhere** in
the changed surface, so the generated prose and autocomplete name rendering are
not XSS vectors. The accent-insensitive normalization (`NFD` + `\p{Diacritic}`
strip + lowercase) is correct. The homicide `!== undefined` guard is correctly
applied on both static pages (0 is preserved as valid data).

No BLOCKER-class defects were found. The findings below are correctness and
quality issues — the most material being (1) a year mismatch between the island's
"Chile avg." column and the per-commune columns, (2) the "Chile avg." column on
the static A-vs-B pages being permanent dead placeholder content, and (3) the
spine.mjs assertion M being a false-pass that cannot actually detect a missing
comparator spoke.

There were no structural findings supplied with this review.

## Warnings

### WR-01: Island "Chile avg." column reads a different year than the commune columns

**File:** `site/src/islands/ComparatorIsland.tsx:256-263` (`getNationalFamilyRate`)
**Issue:** Per-commune family rates use `latestCompleteYear(data)` →
`series.find(s => s.year === year)`. The national average column instead does
`nationalData.series.filter(!partial)` then takes `latestSeries[length-1]` — a
positional last-element read that assumes ascending year order and uses
*national's* latest complete year. national.json currently ends 2024/2025/2026
(2026 partial), so the avg column resolves to 2025, while a commune whose latest
complete year is 2024 would render its 2024 figures in the same table with **no
visible year label on the avg column**. The two columns can silently compare
different reference years, and the comparison is presented as apples-to-apples.
**Fix:** Resolve the national rate for the *same* year used by the commune
columns, and find by year rather than by position:
```ts
function getNationalFamilyRate(family: string, year: number): number | null {
  if (!nationalData) return null;
  const entry = nationalData.series.find(s => s.year === year && !s.partial);
  const val = entry?.by_family[family];
  return val !== undefined ? val : null;
}
```
Pick the year deterministically (e.g. the min of each selected commune's
latestCompleteYear, or display a per-column year). At minimum, label the avg
column with its year.

### WR-02: Static A-vs-B "Chile avg." column is permanent dead placeholder ("—")

**File:** `site/src/pages/compare/[pair].astro:113-114, 185, 202` and
`site/src/pages/es/comparar/[pair].astro:177, 194`
**Issue:** Both static routes render a "Chile avg." / "Prom. Chile" table column,
but every data cell is hardcoded to `'—'` (the comment at EN:113-114 admits the
per-family national data "requires an extra data call not in scope"). The column
header promises data that never arrives on any of the ~20 enabled pages. This is
thin/misleading content on an SEO page whose entire purpose is data comparison,
and `loadNationalAverage()` is called (EN:72) only to be discarded. Either wire
the per-family national rates (they exist in `national.json` `by_family`, as the
island already reads) or remove the column entirely.
**Fix:** Use the national `by_family` map for the latest complete year to fill
the column, mirroring the island, or delete the 4th column and its header.

### WR-03: spine.mjs assertion M cannot detect a missing comparator spoke (false-pass)

**File:** `site/scripts/validate/spine.mjs:358-417`
**Issue:** Assertion M is documented as the CMP-06 guard that "every commune page
contains the comparator cross-link" via `ComparatorPairsLinks`. But `PageHeader`
(included by `BaseLayout` on *every* page) already emits `href="/compare/"` (EN)
and `href="/es/comparar/"` (ES) in the nav (`PageHeader.astro:32,68`). The
assertion uses `content.includes('href="/compare/')` — a substring the site-wide
nav always satisfies. The check therefore passes even if `ComparatorPairsLinks`
were removed from the commune template, defeating its stated purpose. The same
weakness applies to assertions J/I/L (all satisfied by nav/footer regardless of
the per-page spoke).
**Fix:** Assert on the spoke's distinctive markup, not the bare prefix — e.g.
require the `comparator-pairs-spoke` section class, or a pair-slug link
`href="/compare/{cut}-vs-{cut}/"` (a `-vs-` link the nav never emits):
```js
if (!/href="\/compare\/\d+-vs-\d+\//.test(content)) enCmpOffenders.push(slug);
```

### WR-04: Cross-region Block 5 prose emits a malformed parenthetical

**File:** `site/src/lib/comparisonProse.ts:195`
**Issue:** The `!sameRegion` branch of `EN_BLOCK5_REGIONAL` contains
`the national rank (#${regRankA === 0 ? '—' : ''})` — `regRankA` is a regional
rank (essentially never 0), so this always renders `(#)`: an empty parenthetical
that also mislabels a *regional* rank as a *national* one. Today this branch is
unreachable because `generate-pairs.mjs` only emits same-region pairs, so no
enabled pair is cross-region — but the dead branch is latent and would ship
broken prose the moment a cross-region pair is enabled. (The ES branch at line
279 is written correctly.)
**Fix:** Remove the broken interpolation; reference the actual national ranks
that are in scope, or delete the unreachable branch and assert `sameRegion`.

### WR-05: Island homicide row requires a count to display a valid rate

**File:** `site/src/islands/ComparatorIsland.tsx:523-525, 611-616`
**Issue:** `hasHom = homRate !== undefined && homCount !== undefined`. The cell
only shows the rate (`homRate!.toFixed(2)`) when **both** rate and count exist;
if a commune ever has a homicide rate but no count, the row falls back to
"No reported cases" — incorrectly suppressing a real, non-zero rate. This
diverges from the static pages (`[pair].astro:193-195`), which show the rate when
`homRateA !== null` and append the count only if present. Current data always
pairs rate+count (verified: 0 rate-years lack a count), so this does not misfire
today, but it is a latent correctness bug and an EN-island-vs-static
inconsistency. The "No reported cases" label is also semantically wrong for a
missing-count case (it is not "no cases", it is "count unavailable").
**Fix:** Gate display on the rate alone and append the count conditionally:
```ts
const hasHom = homRate !== undefined;
// ...
{hasHom ? `${homRate!.toFixed(2)}${homCount !== undefined ? ` (${homCount})` : ''}` : noData}
```

### WR-06: `mostDivergentFamily` fabricates a "propiedad 0 vs 0" claim on empty data

**File:** `site/src/lib/comparisonProse.ts:83-107, 343-347`
**Issue:** When `latestCompleteEntry` returns undefined for either commune,
`byFamilyA`/`byFamilyB` default to `{}`, so `mostDivergentFamily` iterates no
keys and returns the seeded default `{ family: 'propiedad', rateA: 0, rateB: 0,
factor: 1 }`. Block 2 then asserts "The sharpest per-category difference … is in
property crimes … 0 incidents per 100,000 … a gap of approximately 1×" — a
factually wrong, swappable sentence that also undermines the non-swappability
guarantee the module documents. Enabled communes currently have data so this is
latent, but the silent default masks a real "no data" condition.
**Fix:** When `families.length === 0` (or `maxDivergence === 0`), produce a
neutral "comparable across categories / data unavailable" sentence instead of
emitting the seeded propiedad/0/0 claim.

### WR-07: `getRegionSize` resolves data root differently from the rest of the codebase

**File:** `site/src/lib/comparisonProse.ts:297-307`
**Issue:** This module reads `path.resolve(process.cwd(), '..', 'data', 'cead')`
and re-parses `meta/index.json` itself, duplicating the `DATA_ROOT` logic that
already lives in `data.ts` (which exposes `loadIndex()`). The duplicated path is
build-CWD-dependent (the project memory note "News page build path drift" and
"OneDrive build artifacts desync" both flag fragility around build-time path
resolution). If this module is ever invoked with a different CWD than `site/`,
`getRegionSize` throws while `data.ts` would have resolved correctly, and the
cache is a module-level singleton that silently returns 0 on a miss.
**Fix:** Compute region sizes from the already-loaded `loadIndex()` in `data.ts`
(pass region size in, or import `loadIndex`) rather than re-reading the file with
a second, divergent path resolver.

### WR-08: Region commune count for the static cross-region path is unused / inconsistent

**File:** `site/src/lib/comparisonProse.ts:352`
**Issue:** `const regionSize = sameRegion ? getRegionSize(commA.region_id) : 0;`
— the cross-region branch passes `regionSize = 0`, and Block 5's cross-region
text never uses it, while the same-region text uses it correctly. Combined with
WR-04 this confirms the cross-region path was not exercised. Low impact while
only same-region pairs are enabled, but the `0` sentinel is a code smell that
will silently produce "contains 0 communes" if the same-region/cross-region
branch logic is ever changed.
**Fix:** Compute `regionSize` unconditionally (it is cheap and cached) or assert
`sameRegion` for the enabled-pair invariant.

## Info

### IN-01: Unused imports on both A-vs-B routes

**File:** `site/src/pages/compare/[pair].astro:23,25` and
`site/src/pages/es/comparar/[pair].astro:20,22`
**Issue:** `loadIndex` and `FAMILY_SLUGS` are imported but never used on both
routes; `loadNationalAverage` is imported on both and only invoked (then
discarded) on EN. The block comment at EN:80-82 references `FAMILY_SLUGS.vida`
but the code uses a local `familyLabelEn`/`familyLabelEs` map and a plain
`!== 'vida'` filter, so the import is genuinely dead.
**Fix:** Remove the unused imports (and the discarded `nationalAvg` call once
WR-02 is resolved).

### IN-02: Dead helper `countDirs` in the budget validator

**File:** `site/scripts/validate/avs-b-budget.mjs:46-49`
**Issue:** `countDirs` is defined but never called — the pair-symmetry check uses
the separate `countPairDirs` (lines 79-84). Leftover scaffolding.
**Fix:** Delete `countDirs`.

### IN-03: Pair-symmetry assertion is duplicated across two validators

**File:** `site/scripts/validate/avs-b-budget.mjs:71-101` and
`site/scripts/validate/hreflang.mjs:162-188`
**Issue:** The EN/ES `-vs-` directory-count symmetry check is implemented twice
(once as CMP-03 in avs-b-budget, once inline in hreflang). Duplicated logic
drifts; the two report under different labels ([CMP-03] vs [hreflang]).
**Fix:** Keep one canonical implementation and have the other reference it, or
document that the redundancy is intentional defense-in-depth.

### IN-04: `generate-pairs.mjs` reads `name` from index but never uses it

**File:** `scripts/generate-pairs.mjs:46-48`
**Issue:** The destructure pushes `{ cut, region_id }` (name dropped); the JSDoc
type on line 43 still lists `name`. Harmless, but the type annotation is stale.
**Fix:** Drop `name` from the `@type` annotation, or store it if needed
downstream.

### IN-05: Hardcoded magic constants for index tiers and budget bounds

**File:** `site/src/lib/comparisonProse.ts:171-174, 254-257`;
`scripts/generate-pairs.mjs:70,82,95-96`; `site/scripts/validate/avs-b-budget.mjs:56`
**Issue:** The `346` commune count, the 0.1/0.25/0.75/0.9 tier breakpoints, the
`EXPECTED_PAIRS = 5031`, `WAVE_SIZE = 20`, `BASE_FILES = 1882`, and
`SAFE_BOUND = 18000` are scattered literals. `346` in particular appears in many
places and will require a coordinated edit if the commune universe ever changes.
**Fix:** Centralize the commune count and shared bounds in one constants module;
derive tier thresholds from it.

---

_Reviewed: 2026-06-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
