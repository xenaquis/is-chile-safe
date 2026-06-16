---
phase: 15-crime-type-seo-ranking-pages
reviewed: 2026-06-16T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - site/scripts/validate/seo.mjs
  - site/src/lib/familyDefs.ts
  - site/src/pages/crime-ranking/[crime].astro
  - site/src/pages/es/ranking-delito/[crime].astro
  - site/src/pages/commune/[slug].astro
  - site/src/pages/es/comuna/[slug].astro
findings:
  critical: 2
  warning: 6
  info: 4
  total: 12
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-06-16
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 15 adds crime-type SEO ranking pages (`/crime-ranking/{crime}/` EN and `/es/ranking-delito/{crime}/` ES, 8 pages each), shared crime-family constants in `familyDefs.ts`, wiring of per-crime-type spokes into the commune pages, and extension of the `seo.mjs` validator to sample the new routes.

The new ranking pages are largely well structured and consciously avoid several documented pitfalls (homicide-from-`featured_rates`, hardcoded ES slugs, neutral ItemList names). However the integration into the existing commune pages introduces two correctness defects that ship broken links and a confusing duplicate label to end users — and the new ranking table mixes per-commune "latest complete year" values under a single year heading, which is a data-integrity problem for a site whose core value is "real CEAD data."

Cross-cutting verification done: confirmed `catalog.family_keys` contains `vida` (not `homicidios`); confirmed `FAMILY_SLUGS.vida.en === 'homicide'`; confirmed `/crime/[family].astro` builds `/crime/homicide/` representing the **vida (Life Crimes)** family; confirmed commune JSON `by_family` keys and `featured_rates.homicidios` string-year shape.

## Critical Issues

### CR-01: Commune "Rankings by Crime Type" spoke emits a broken link AND a mislabeled duplicate "homicide ranking"

**File:** `site/src/pages/commune/[slug].astro:240-250` (and ES mirror `site/src/pages/es/comuna/[slug].astro:243-253`)

**Issue:** The crime-type spoke renders an explicit homicide link plus one link per `by_family` key:

```astro
<li><a href="/crime-ranking/homicide/">homicide ranking</a></li>
{Object.entries(byFamily).map(([key]) => (
  <li>
    <a href={`/crime/${FAMILY_SLUGS[key]?.en ?? key}/`}>
      {FAMILY_SLUGS[key]?.en ?? key} ranking
    </a>
  </li>
))}
```

`byFamily` keys are `vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades` (verified against commune JSON + `catalog.family_keys`). Two concrete defects result:

1. **Mislabeled duplicate "homicide ranking".** `FAMILY_SLUGS.vida.en === 'homicide'`, so the `vida` row renders a second link labeled "homicide ranking" pointing to `/crime/homicide/`. But `/crime/homicide/` is the **Life Crimes (vida) family** page, NOT the subgroup-101 homicide page. The page now shows two links both labeled "homicide ranking" that go to different destinations (`/crime-ranking/homicide/` vs `/crime/homicide/`) and the second one is semantically wrong. This is exactly the homicide/vida confusion the new `/crime-ranking/` namespace was created to avoid (see file header "Pitfall 2").

2. **Inconsistent target namespace.** The hand-written homicide link points at the new `/crime-ranking/` pages (phase 15), but every family link points at the older `/crime/` pages. If the intent of phase 15 was to route commune spokes to the new ranking pages, six of seven links bypass them. If the intent was to keep `/crime/` links, the homicide link is the odd one out. Either way the set is internally inconsistent.

The ES mirror (`/es/comuna/[slug].astro:243-253`) has the identical structure: explicit `/es/ranking-delito/homicidios/` link plus `vida` rendering a second `/es/delito/homicidios/` link labeled "ranking homicidios". `FAMILY_SLUGS.vida.es === 'homicidios'`, so ES also produces a duplicate "homicidios" label pointing to a different page.

**Fix:** Skip the `vida` key in the family loop (the explicit homicide link already covers the featured subgroup), or relabel/redirect deliberately. Minimal fix:

```astro
{Object.entries(byFamily)
  .filter(([key]) => key !== 'vida')  // 'vida'.en === 'homicide' collides with the explicit link above
  .map(([key]) => (
    <li>
      <a href={`/crime/${FAMILY_SLUGS[key]?.en ?? key}/`}>
        {FAMILY_SLUGS[key]?.en ?? key} ranking
      </a>
    </li>
  ))}
```

Decide explicitly whether family links should target `/crime/` or the new `/crime-ranking/` pages and make all seven consistent. Confirm the `vida` Life-Crimes ranking is still reachable somewhere if it should be.

### CR-02: National ranking table mixes per-commune "latest complete year" values under one year heading

**File:** `site/src/pages/crime-ranking/[crime].astro:81-107, 229` (and ES mirror `site/src/pages/es/ranking-delito/[crime].astro:89-115, 235`)

**Issue:** The rate for each commune is read at **that commune's own** `commune.latestCompleteYear`:

```js
rate = entry?.by_family?.[familyKey] ?? 0;   // entry.year === commune.latestCompleteYear
```

while `latestYear` is computed as the **maximum** `latestCompleteYear` across all non-low-pop communes:

```js
latestYear = Math.max(latestYear, commune.latestCompleteYear);
```

The table heading then claims a single year for the whole ranking:

> "Communes ranked by {crime} rate per 100,000 inhabitants ({latestYear})"

If any commune lags (its latest complete year is 2024 while the national max is 2025), its 2024 rate is ranked and displayed against communes' 2025 rates, all under a "(2025)" heading. This silently compares non-comparable years and mis-ranks communes — a data-integrity defect on a product whose stated core value is "real CEAD data really by commune." The same `latestYear`-vs-per-commune-year mismatch feeds `familyNationalMean` and the region-breakdown means, so every aggregate on the page inherits it.

Note: this mismatch already exists in the older `/crime/[family].astro` (same pattern), so it is a propagated bug, not solely introduced here — but phase 15 re-introduces it in two new files and surfaces it on new public pages, so it must be addressed.

**Fix:** Pin a single ranking year and read every commune at that year (skipping/flagging communes that lack a complete entry for it), so the heading year matches every row:

```js
// Determine national ranking year first (max complete year across eligible communes)
const rankingYear = latestYear;
// ...then read each commune at rankingYear, not commune.latestCompleteYear:
const entry = commune.series.find((s) => s.year === rankingYear && !s.partial);
rate = entry?.by_family?.[familyKey] ?? 0;   // 0/skip if this commune has no complete rankingYear entry
```

For the homicide branch, index `featured_rates.homicidios?.[rankingYear]` consistently. Requires a two-pass approach (pass 1 to find `rankingYear`, pass 2 to read rates) since `rankingYear` isn't known until all communes are scanned.

## Warnings

### WR-01: `rate ?? 0` silently buries missing-data communes at the bottom of the ranking

**File:** `site/src/pages/crime-ranking/[crime].astro:90, 95` (ES `:98, 103`)

**Issue:** When a commune has no `featured_rates.homicidios` entry or no `by_family[familyKey]` for the chosen year, `rate` falls back to `0`. A genuine-zero commune and a missing-data commune become indistinguishable, both sorting to the bottom and both contributing `0` to `familyNationalMean` and the region means — deflating those averages. There is no count of how many communes actually had data, yet the hero claims "{eligibleRows.length} communes ranked" as if all are real data points.

**Fix:** Track communes with missing data separately (e.g. `rate: number | null`), exclude nulls from the mean denominator, and either omit them or mark them like low-population rows. At minimum, do not include `0`-by-absence rows in `familyNationalMean`.

### WR-02: Region breakdown groups by `regionFileId(region_id)`, inheriting the documented Tarapacá CUT collision

**File:** `site/src/pages/crime-ranking/[crime].astro:134-148` (ES `:140-153`)

**Issue:** Region grouping keys on `regionFileId(meta.region_id)`. Per the project memory (`tarapaca-region-id-collision`) and the in-code BUGFIX-999.1 note in the commune pages, `region_id` province codes 11/14 collide with Aysén/Los Ríos, so some communes are mis-grouped by region. The region-breakdown bars on these new public pages will silently mis-attribute communes to the wrong region without any caveat, unlike the commune page which at least documents the limitation inline.

**Fix:** Derive region from CUT (per the documented fix) for the grouping key, or add the same explicit caveat the commune pages carry. Do not ship a region-comparison visual built on a key known to collide without flagging it.

### WR-03: Duplicated `ES_CRIME_SLUGS` map in the ES ranking page (3 copies of the same slug table across 2 files)

**File:** `site/src/pages/es/ranking-delito/[crime].astro:24-33` and `:47-56`

**Issue:** The ES page declares `ES_CRIME_SLUGS` at module scope (lines 24-33) AND a byte-identical `ES_SLUGS` inside `getStaticPaths` (lines 47-56). The module-scope `ES_CRIME_SLUGS` is never read in this file (the page derives `crime` from `Astro.params` and `enParam` from props), so it is dead. A third identical copy lives in the EN page (`crime-ranking/[crime].astro:46-55`). Three sources of truth for one mapping invites drift — exactly the failure mode `familyDefs.ts` was created to prevent.

**Fix:** Delete the unused module-scope `ES_CRIME_SLUGS` in the ES file, and hoist the single slug map into `familyDefs.ts` (or `i18n.ts` alongside `FAMILY_SLUGS`) and import it in both pages.

### WR-04: `seo.mjs` `temporalCoverage` and `latestYear` divergence not validated; OG/JSON-LD asserts only sampled FIRST subdir

**File:** `site/scripts/validate/seo.mjs:76-80, 174-194`

**Issue:** `firstSubdir()` returns the first directory entry only, so the validator checks exactly one crime-ranking page per locale. Since all 8 ranking pages share a template, a defect that manifests only on a specific crime (e.g. a missing `FAMILY_LABELS`/`RANKING_METHODOLOGY` key producing a raw `familyKey` in the title) would pass validation if it isn't the alphabetically-first directory. The validator gives false confidence of full coverage.

**Fix:** For template-generated route groups, iterate all subdirectories (or a representative sample per crime) rather than just `firstSubdir`, at least for the JSON-LD parse (Q) and OG presence (N) assertions which are cheap.

### WR-05: `latestYear` fallback `getFullYear() - 1` can disagree with actual data and label the table with a year no commune reports

**File:** `site/src/pages/crime-ranking/[crime].astro:81` (ES `:89`)

**Issue:** `latestYear` is seeded with `new Date().getFullYear() - 1` (2025 at build time on 2026-06-16) and only raised by `Math.max`. If the dataset's latest complete year is 2024 (data lag), `latestYear` stays at 2025 — a year for which no commune has data — yet the heading and `temporalCoverage` (`2005/${latestYear}`) advertise 2025. The label is decoupled from the data actually shown. This is build-clock-dependent, so it can change behavior across rebuilds with no data change.

**Fix:** Initialize `latestYear` from the data only (e.g. `0` or `-Infinity`), then take the max of observed complete years; never seed it from the wall clock. Combined with CR-02's `rankingYear`, derive the label strictly from data.

### WR-06: `maxRegionRate` guard floors at 1, distorting bars when all region means are sub-1

**File:** `site/src/pages/crime-ranking/[crime].astro:151, 278` (ES `:156, 284`)

**Issue:** `const maxRegionRate = Math.max(...regionBreakRows.map(r => r.rate), 1);` forces a minimum denominator of 1 to avoid divide-by-zero. For low-incidence crimes (e.g. weapons/homicide where regional means can be < 1 per 100k), the true max is divided into `1`, so every bar renders at a fraction of its real proportion and the visual comparison is wrong (the leading region no longer reaches 100%). The `1` floor is a magic number doing double duty as both a divide-by-zero guard and an implicit unit assumption.

**Fix:** Guard only against zero: `const denom = maxRegionRate > 0 ? maxRegionRate : 1;` computed from the actual max, so the largest bar always fills the track regardless of absolute scale.

## Info

### IN-01: `regionId` field on `RegionBreakRow` is computed but never rendered

**File:** `site/src/pages/crime-ranking/[crime].astro:127-131, 143-147` (ES mirror)

**Issue:** `RegionBreakRow.regionId` is populated but the template only renders `regionName` and `rate`. Dead field. Either link the region name to `/region/{regionId}/` (useful internal-link SEO, consistent with the hub-and-spoke goal) or drop the field.

### IN-02: Unused `.featured-badge` and `.rollout-note` CSS in both ranking pages

**File:** `site/src/pages/crime-ranking/[crime].astro:331-340, 462-467` (ES `:337-346, 468-473`)

**Issue:** `.featured-badge` and `.rollout-note` style rules exist but no element in the template uses those classes (no badge is rendered on ranking pages). Dead CSS carried over from a sibling template.

**Fix:** Remove the unused rules to keep the scoped `<style>` block honest.

### IN-03: `cut` field on ranking `RankRow` is collected but unused

**File:** `site/src/pages/crime-ranking/[crime].astro:69, 102` (ES mirror)

**Issue:** Every ranking row carries `cut`, but links and JSON-LD use `slug`. `cut` is never read after assignment. Minor dead data per row across ~346 rows × 8 pages × 2 locales.

**Fix:** Drop `cut` from the ranking `RankRow` type and `allRows.push` if it is not needed for a future feature.

### IN-04: `familyDefs.ts` `FAMILY_LABELS_*` / `FAMILY_DEFS_*` include `homicidios` key that ranking pages never look up by that key

**File:** `site/src/lib/familyDefs.ts:26, 38, 50, 62`

**Issue:** `FAMILY_LABELS_EN.homicidios`, `FAMILY_DEFS_*.homicidios`, etc. exist, but the crime-ranking homicide branch uses `familyKey: 'homicidios'` only via `RANKING_METHODOLOGY_*` and `FAMILY_LABELS_*` (which do define `homicidios`) — consistent. However `FAMILY_DEFS_*` (the short defs) are imported by `/crime/[family].astro` keyed on `vida..incivilidades` only; the `homicidios` def entry in `FAMILY_DEFS_*` is never consumed by any current page. Harmless but worth noting as latent unused data, and a reminder that `homicidios` is a special subgroup, not a family — keep the two concepts clearly separated to avoid the CR-01 class of bug.

---

_Reviewed: 2026-06-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
