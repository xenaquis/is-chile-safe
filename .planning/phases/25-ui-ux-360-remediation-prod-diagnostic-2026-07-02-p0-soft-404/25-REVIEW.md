---
phase: 25-ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
reviewed: 2026-07-02T00:00:00Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - pipeline/news/classifier.py
  - pipeline/tests/test_classifier_traffic.py
  - site/package.json
  - site/public/favicon.svg
  - site/scripts/gen-favicon.mjs
  - site/src/components/CommuneRankingTable.astro
  - site/src/components/ComparableCommune.astro
  - site/src/components/ContactForm.astro
  - site/src/components/PageHeader.astro
  - site/src/components/map/IncidentPinLayer.ts
  - site/src/components/map/Legend.tsx
  - site/src/components/map/MapIsland.tsx
  - site/src/components/map/MapTopbar.tsx
  - site/src/components/map/ResultPanel.tsx
  - site/src/components/map/map.css
  - site/src/config/i18n.ts
  - site/src/islands/ComparatorIsland.tsx
  - site/src/layouts/BaseLayout.astro
  - site/src/lib/formatNumber.test.ts
  - site/src/lib/formatNumber.ts
  - site/src/lib/jsonld.ts
  - site/src/pages/404.astro
  - site/src/pages/communes/index.astro
  - site/src/pages/compare/index.astro
  - site/src/pages/es/comparar/index.astro
  - site/src/pages/es/comunas/index.astro
  - site/src/pages/es/noticias.astro
  - site/src/pages/es/region/[slug].astro
  - site/src/pages/index.astro
  - site/src/pages/is-chile-safe.astro
  - site/src/pages/is-santiago-safe.astro
  - site/src/pages/news.astro
  - site/src/pages/rankings.astro
  - site/src/pages/region/[slug].astro
  - site/src/styles/global.css
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 25: Code Review Report

**Reviewed:** 2026-07-02
**Depth:** standard
**Files Reviewed:** 35
**Status:** issues_found

## Summary

Phase 25 delivers the P0/P1/P2 remediation set from the UI-360 diagnostic: soft-404 fix (real `404.html`), map framing and accessible incident pins, collapsible mobile legend with purple pin row, news semantic restructure (month-grouped h2/h3, type+commune chips, parity between `/news/` and `/es/noticias/`), comparator URL sync and popular chips, formatter unification (`formatNumber.ts`), skip-to-main link, focus-visible guard, region page copy polish, and home JSON-LD. The news classifier also gained a traffic-accident exclusion rule.

The security surface is clean — no XSS vectors introduced. The `aria-label` attribute in `IncidentPinLayer.ts` correctly reuses the `escHtml`-escaped `title` value, and `{incident.title_*}` in Astro templates is auto-escaped. URL params (`?cut=`, `?a=`, `?b=`) are validated with the correct 4-5 digit regex before lookup. Data attribution and rank direction are correctly labelled throughout.

Three warnings were found, none crash-level. The most impactful is the URL sync in `ComparatorIsland` that unconditionally writes `?a=&b=` to the browser URL on every cold page load of `/compare/`.

---

## Warnings

### WR-01: Comparator URL sync always writes `?a=&b=` on cold page load

**File:** `site/src/islands/ComparatorIsland.tsx:197-203`

**Issue:** The `useEffect` that syncs `selected` to URL query params has no guard for the empty-selection initial state. On every cold load of `/compare/` or `/es/comparar/`, the effect fires immediately with `selected = []`, calling:

```
window.history.replaceState(null, '', '?a=&b=')
```

This appends `?a=&b=` to the URL even when the page was loaded with a clean URL (no params). Consequences: (1) every visitor to the compare page immediately gets a polluted URL they might share or bookmark; (2) crawlers indexing `/compare/?a=&b=` may split link equity from `/compare/`; (3) in future, if Google treats `?a=` and `?b=` as signals for soft-404 (empty comparator), this recreates the problem the phase was fixing.

**Fix:**

```ts
useEffect(() => {
  if (typeof window === 'undefined') return;
  const a = selected[0]?.id ?? '';
  const b = selected[1]?.id ?? '';
  // Do not pollute the URL when nothing is selected yet
  if (!a && !b) {
    // Restore clean URL only if params are currently present
    if (window.location.search) {
      window.history.replaceState(null, '', window.location.pathname);
    }
    return;
  }
  window.history.replaceState(null, '', '?a=' + a + '&b=' + b);
}, [selected]);
```

---

### WR-02: Region map CTA links use `?region=` which MapIsland does not handle

**Files:** `site/src/pages/region/[slug].astro:221` and `site/src/pages/es/region/[slug].astro:215`

**Issue:** The new map CTA cards link to `/map/?region=${region.slug}` (EN) and `/es/mapa/?region=${region.slug}` (ES). However, `MapIsland.tsx` only reads `?cut=` from the URL (validated with `/^\d{4,5}$/`). The `?region=` parameter is silently ignored — users land on the default full-Chile view with no region pre-selected. The CTA copy ("View interactive map →" / "Ver mapa interactivo →") implies region-level navigation, which does not happen.

This is a user-facing functional defect: the CTA makes an implicit promise it cannot deliver.

**Fix (option A — remove unfulfilled promise):**

```astro
<a href="/map/" class="map-placeholder-card">
```

Use the bare map URL until `?region=` handling is implemented in MapIsland.

**Fix (option B — implement `?region=` in MapIsland):** Add a `focusRegion` path to `MapIsland.tsx` that reads `?region=`, finds all features whose `properties.region_slug` matches, and calls `fitBounds` on the union. This is the correct long-term fix.

---

### WR-03: Region sparkline heading hardcodes "2026*" instead of using `latestCompleteYear`

**Files:** `site/src/pages/region/[slug].astro:208` and `site/src/pages/es/region/[slug].astro:191`

**Issue:**

```astro
<h2 class="section-heading">Annual evolution (2005–2026*)</h2>
```

The variable `latestCompleteYear` is already computed and used as `activeYear` for the Sparkline component on the very next line, but the heading bypasses it and hardcodes `2026`. If the CEAD pipeline does not yet have 2026 partial data (or the site's data year advances past 2026), the heading will show a year the chart does not reach.

**Fix:**

```astro
<h2 class="section-heading">Annual evolution (2005–{latestCompleteYear}*)</h2>
<p class="chart-footnote">* {latestCompleteYear}: partial year data (Jan–Jun)</p>
```

Apply the same pattern to both EN and ES region page templates.

---

## Info

### IN-01: `vitest` added to devDependencies — deviates from plan's "zero new packages" claim

**File:** `site/package.json:35`

**Issue:** `"vitest": "^4.1.9"` was added to `devDependencies`. The plan review prompt notes the phase committed to zero new npm packages. The package is a devDependency (not shipped to browsers) and is correctly used for the new `formatNumber.test.ts` test suite, but the deviation from the plan constraint should be acknowledged.

**Fix:** Document the addition in the phase SUMMARY or update the plan constraint. No code change required.

---

### IN-02: `REGIONS` array in `rankings.astro` assumes sequential region IDs 1-16

**File:** `site/src/pages/rankings.astro:12`

**Issue:**

```ts
const REGIONS = Array.from({ length: 16 }, (_, i) => loadRegion(String(i + 1)));
```

This assumes region IDs are exactly the strings `"1"` through `"16"` in sequence. The project memory notes the Tarapacá `region_id` collision was resolved by deriving region_id from CUT length — but if any region ID key diverges from the 1-16 sequence, `loadRegion` will throw and the Astro build will fail with no clear error message.

**Fix:** Derive the region list from the actual index data to avoid the hardcoded assumption:

```ts
import { loadIndex } from '../lib/data.ts';
const regionIds = [...new Set(loadIndex().map(c => c.region_id))].sort((a, b) => +a - +b);
const REGIONS = regionIds.map(id => loadRegion(id));
```

---

### IN-03: `formatMonth` has no guard against malformed date strings

**Files:** `site/src/pages/news.astro:66`, `site/src/pages/es/noticias.astro:79`

**Issue:**

```ts
function formatMonth(yearMonth: string): string {
  const [year, month] = yearMonth.split('-');
  const d = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
}
```

If `incident.date` is an empty string, contains timezone info, or is otherwise malformed, `parseInt` returns `NaN` and `new Date(NaN, NaN, 1).toLocaleDateString()` returns the string `"Invalid Date"` in the h2 heading. The pipeline controls date format so the risk is low in practice, but there is no defensive guard.

**Fix:**

```ts
function formatMonth(yearMonth: string): string {
  if (!yearMonth || yearMonth.length < 7) return yearMonth;
  const [year, month] = yearMonth.split('-');
  const y = parseInt(year, 10);
  const m = parseInt(month, 10);
  if (isNaN(y) || isNaN(m)) return yearMonth;
  const d = new Date(y, m - 1, 1);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
}
```

Apply the same guard to the ES version in `noticias.astro`.

---

_Reviewed: 2026-07-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
