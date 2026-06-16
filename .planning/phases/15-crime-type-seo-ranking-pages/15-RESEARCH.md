# Phase 15: Crime-Type SEO Ranking Pages — Research

**Researched:** 2026-06-16
**Domain:** Astro programmatic pages, bilingual SEO, schema.org ItemList, homicide data ranking
**Confidence:** HIGH — all findings verified directly in the codebase

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CSEO-01 | Programmatic bilingual "las N comunas con más {delito}" ranking pages (homicide first) with internal linking to comuna/region pages, reciprocal hreflang, and sitemap entries. | Data exists in `featured_rates.homicidios` per commune JSON. EN/ES route pattern follows `crime/[family].astro` + `es/delito/[family].astro`. hreflang injected via BaseLayout `enPath`/`esPath` props. |
| CSEO-02 | Each page is static/indexable with a single keyword-focused H1, unique title/meta/canonical, and `ItemList` JSON-LD for the ranking; sober tone preserved. | `buildItemList()` in `site/src/lib/jsonld.ts` is ready. Forbidden-language validator enforces sober tone at build time. BaseLayout handles canonical + meta. |
</phase_requirements>

---

## Summary

Phase 15 adds "las N comunas con más {delito}" ranking pages — one per crime type, bilingual. The critical finding is that **the pattern already fully exists**: `site/src/pages/crime/[family].astro` and `site/src/pages/es/delito/[family].astro` are exactly the template to extend (or replicate with a new `[crime].astro` route). The 7 existing crime-family pages use `getStaticPaths`, compute national rankings from per-commune JSON, emit `buildItemList` + `buildBreadcrumb` JSON-LD, and receive hreflang + canonical from `BaseLayout` via `enPath`/`esPath` props.

The homicide ranking is the only genuinely new data path: homicide rates live in `commune.featured_rates.homicidios[year]` (a year-keyed dict at the top level of each commune JSON), NOT in `series[].by_family`. For the 7 regular crime families, rates come from `series[].by_family[familyKey]`. The planner must ensure the homicide ranking page reads the correct field. All other crime-family ranking pages can reuse `series[].by_family[familyKey]` exactly as the existing crime pages do.

The phase scope is: one new pair of Astro pages per crime type (starting with homicidios/homicide), a new validator assertion that these pages exist and carry `ItemList` JSON-LD, and seo.mjs sample-set expansion to cover the new routes. No new data pipeline work is needed — data is already present for 2025.

**Primary recommendation:** Create `site/src/pages/crime-ranking/[crime].astro` and `site/src/pages/es/ranking-delito/[crime].astro` (new URL namespace distinct from the existing `/crime/[family]/` family overview pages), or add "homicidios" as a virtual entry in the existing crime-page `getStaticPaths` with a special data branch. The new-namespace approach is cleaner because the existing `/crime/vida/` page covers ALL life crimes; this phase adds a page specifically for HOMICIDE as a subgroup.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ranking computation (homicide) | Frontend Server (Astro SSG) | — | `featured_rates.homicidios` read from commune JSON at build time; sorted server-side |
| Ranking computation (7 families) | Frontend Server (Astro SSG) | — | Reuse existing `series[].by_family` path, identical to `/crime/[family]/` pages |
| hreflang + canonical | Frontend Server (BaseLayout) | — | Already injected via `enPath`/`esPath` props — no new logic |
| ItemList JSON-LD | Frontend Server (Astro SSG) | — | `buildItemList()` called in page frontmatter, passed to BaseLayout `jsonLd` |
| Sitemap entries | CDN/Static (@astrojs/sitemap) | — | Auto-detected from `getStaticPaths` — new routes appear automatically |
| Forbidden-language guard | Build validator (forbidden-language.mjs) | — | Runs against dist/ HTML after build |
| Internal linking (commune rows) | Frontend Server (Astro SSG) | — | `/commune/{slug}/` and `/es/comuna/{slug}/` href patterns from existing templates |

---

## Standard Stack

### Core (no new packages — all existing)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Astro 6.4.x | existing | `getStaticPaths` + static pre-render | Mandatory for SEO; already in project |
| `site/src/lib/jsonld.ts` | project | `buildItemList`, `buildBreadcrumb` | Phase 13 deliverable; already tested |
| `site/src/lib/data.ts` | project | `loadIndex`, `loadCommune`, `loadCatalog` | Phase 1 deliverable; memoized since Phase 11 |
| `site/src/config/i18n.ts` | project | `FAMILY_SLUGS`, `EN_STRINGS`, `ES_STRINGS` | Crime slug translations already defined |
| `site/src/lib/familyDefs.ts` | project | `FAMILY_LABELS_EN/ES`, `FAMILY_DEFS_EN/ES` | Labels + defs for all 7 families + homicidios |
| `@astrojs/sitemap` | existing | Auto-generates sitemap entries for new routes | Picks up `getStaticPaths` automatically |

**Installation:** No new packages needed. [VERIFIED: direct codebase inspection]

---

## Package Legitimacy Audit

No external packages are introduced in this phase. All dependencies are already in the project.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### Key Decision: URL Namespace

The existing `/crime/[family]/` pages cover the **7 crime families** (vida, robos_violentos, etc.). Phase 15 needs pages for **specific crime types including homicide** (a subgroup of "vida"). There are two valid approaches:

**Option A — New URL namespace (recommended):**
- EN: `/crime-ranking/homicide/` or `/top-communes/homicide/`
- ES: `/es/ranking-delito/homicidios/`

**Option B — Add homicide as entry in existing crime-page `getStaticPaths`:**
- EN: `/crime/homicide/` (new slug alongside `vida`, `property`, etc.)
- ES: `/es/delito/homicidios/`

Option B is simpler (no new files, same template) but conflates the "vida" family overview with the specific "homicidios" subgroup. The existing `vida` page already covers life crimes broadly. Option A avoids confusion. [ASSUMED — planner should confirm URL scheme with user or choose by convention]

For homicide specifically, the most natural keyword-targeted URL would be:
- EN: `/communes-most-homicides/` or `/crime-ranking/homicide/`
- ES: `/es/comunas-mas-homicidios/` or `/es/ranking-delito/homicidios/`

**The keyword-focused H1 target** (CSEO-02): "Comunas con más homicidios reportados en Chile" (ES) / "Communes with the Highest Reported Homicide Rate in Chile" (EN). Must avoid forbidden terms — "more dangerous" / "más peligrosas" would fail the forbidden-language validator.

### Recommended Project Structure

```
site/src/pages/
├── crime-ranking/
│   └── [crime].astro          # EN: /crime-ranking/{crime}/
└── es/
    └── ranking-delito/
        └── [crime].astro      # ES: /es/ranking-delito/{crime}/
```

Alternatively, if the planner chooses Option B, the existing `crime/[family].astro` and `es/delito/[family].astro` files gain one new `getStaticPaths` entry each with a homicide-specific data branch.

### Pattern: getStaticPaths for Crime-Type Rankings

Directly copied from `site/src/pages/crime/[family].astro`:

```typescript
// Source: site/src/pages/crime/[family].astro (verified)
export async function getStaticPaths() {
  const catalog = loadCatalog();
  return catalog.family_keys.map((key) => ({
    params: { family: FAMILY_SLUGS[key]!.en },
    props: { familyKey: key },
  }));
}
```

For Phase 15, replace with an explicit list of crime types (families + homicide subgroup):

```typescript
// Proposed pattern for Phase 15
const CRIME_RANKING_DEFS = [
  { param: 'homicide',       familyKey: 'homicidios', dataSource: 'featured_rates' },
  { param: 'property',       familyKey: 'propiedad',  dataSource: 'by_family' },
  // ... other families
];

export async function getStaticPaths() {
  return CRIME_RANKING_DEFS.map((def) => ({
    params: { crime: def.param },
    props: def,
  }));
}
```

### Pattern: Homicide Rate Extraction (CRITICAL — different from 7 families)

The 7 crime families use `series[].by_family[familyKey]`. Homicide uses `featured_rates.homicidios[year]`:

```typescript
// Source: verified via direct commune JSON inspection (data/cead/comunas/10101.json)

// For 7 families — from series[].by_family (existing pattern):
const entry = commune.series.find(s => s.year === commune.latestCompleteYear && !s.partial);
const rate = entry?.by_family?.[familyKey] ?? 0;

// For homicide subgroup — from featured_rates.homicidios[year]:
const latestCompleteYear = commune.series
  .filter(s => !s.partial)
  .map(s => s.year)
  .sort((a, b) => b - a)[0];
const rate = commune.featured_rates?.homicidios?.[latestCompleteYear] ?? 0;
```

Note: `commune.latestCompleteYear` is enriched by `loadCommune()` in `data.ts` — use that directly. Both `featured_rates.homicidios` AND the series's latestCompleteYear year key (`2025` for most communes) are populated. [VERIFIED: direct data inspection]

### Pattern: hreflang via BaseLayout

```astro
<!-- Source: site/src/layouts/BaseLayout.astro (verified) -->
<BaseLayout
  lang="en"
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
  jsonLd={jsonLd}
  pageType="crime"
>
```

BaseLayout injects:
- `<link rel="alternate" hreflang="en" href="https://ischilesafe.com{enPath}" />`
- `<link rel="alternate" hreflang="es" href="https://ischilesafe.com{esPath}" />`
- `<link rel="alternate" hreflang="x-default" href="https://ischilesafe.com{enPath}" />`
- `<link rel="canonical" href="https://ischilesafe.com{enPath or esPath per lang}" />`

The ranking pages must hardcode `enPath` and `esPath` as string constants (not derived from `getRelativeLocaleUrl` — see pitfall below). [VERIFIED: site/src/layouts/BaseLayout.astro]

### Pattern: ItemList JSON-LD

```typescript
// Source: site/src/lib/jsonld.ts (verified)
import { buildItemList, buildBreadcrumb } from '../../lib/jsonld.ts';

// eligibleRankingRows = rankingRows filtered to !low_population
const ranking = buildItemList(eligibleRankingRows, 'en', {
  name: `Communes by reported homicide incidence (descending)`,
  order: 'Descending',
});
// NOTE: name MUST NOT contain: 'safest', 'most dangerous', 'safe', 'dangerous'
// (assertSafeName() throws at build time if violated)

const jsonLd = [jsonLdDataset, breadcrumb, ranking];
```

`buildItemList` requires each row to have `{ name, slug }` (for `urlMode: 'commune'`, the default). The `slug` field is on every commune's `index.json` meta entry. [VERIFIED: site/src/lib/jsonld.ts]

### Pattern: Commune Internal Links

EN table rows link to `/commune/{slug}/`, ES rows to `/es/comuna/{slug}/`:

```typescript
// Source: site/src/pages/crime/[family].astro (verified)
<a href={`/commune/${row.slug}/`} class="commune-link">{row.name}</a>
<a href={`/es/comuna/${row.slug}/`} class="commune-link">{row.name}</a>
```

### Pattern: Sitemap Auto-Detection

`@astrojs/sitemap` picks up all `getStaticPaths` routes automatically. No sitemap config changes needed as long as the new pages are in `site/src/pages/`. [VERIFIED: site/src/pages/crime/[family].astro behavior already in sitemap]

### Pattern: Commune Page Reciprocal Linking (Crime-Type Spokes)

Commune pages already link TO the existing 7 crime-family pages via the "Rankings by Crime Type" spoke (D-10):

```astro
<!-- Source: site/src/pages/commune/[slug].astro line 242 (verified) -->
<a href={`/crime/${FAMILY_SLUGS[key]?.en ?? key}/`}>
```

Phase 15 must also be linked from commune pages IF the new pages use a different URL namespace. If using the same `/crime/[family]/` namespace (Option B), commune pages already link correctly. If using a new namespace (Option A), commune pages need a small update to add a "Homicide ranking" spoke link. [ASSUMED — depends on URL scheme decision]

### Anti-Patterns to Avoid

- **Using `getRelativeLocaleUrl()` for ES slugs in hreflang/nav:** It does NOT translate slugs. Hardcode `/es/ranking-delito/homicidios/` directly. [VERIFIED: i18n-localized-slug-pitfall project memory]
- **Reading `series[].by_family['homicidios']`:** Homicide is NOT in `by_family`. It lives in `featured_rates.homicidios[year]`. Querying `by_family['homicidios']` silently returns `undefined` → 0 rate → all communes rank equally wrong.
- **Including rate in ItemList `name`:** `buildItemList()` deliberately excludes rate (editorial rule A1 — no "safety leaderboard" reading). Never pass rate as part of opts.name.
- **Forbidden language in H1/title/description:** The `forbidden-language.mjs` validator scans ALL dist/ HTML. Terms blocked: "zona peligrosa", "la mas segura", "the safest", "dangerous zone", "dangerous area", "dangerous commune", "dangerous neighborhood", "definitive ranking", "guaranteed safe", "100% safe", "guaranteed safety".
- **jsonld.ts forbidden term guard:** `buildItemList(opts.name)` throws at BUILD TIME if name contains: `'safest'`, `'most dangerous'`, `'safe'`, `'dangerous'`. Use "by reported homicide incidence (descending)" pattern.

---

## Crime-Type Taxonomy

### What Exists in Data

| Family Key | EN Label | ES Label | EN Slug (existing) | ES Slug (existing) | Data Field |
|-----------|----------|----------|------|------|------|
| `vida` | Life Crimes | Delitos contra la Vida | `homicide` | `homicidios` | `series[].by_family.vida` |
| `robos_violentos` | Violent Robbery | Robos Violentos | `violent-robbery` | `robos-violentos` | `series[].by_family.robos_violentos` |
| `vif` | Domestic Violence | Violencia Intrafamiliar | `domestic-violence` | `violencia-intrafamiliar` | `series[].by_family.vif` |
| `drogas` | Drug Crimes | Drogas | `drug-crimes` | `drogas` | `series[].by_family.drogas` |
| `armas` | Weapons Offences | Armas | `weapons` | `armas` | `series[].by_family.armas` |
| `propiedad` | Property Crimes | Delitos contra la Propiedad | `property` | `propiedad` | `series[].by_family.propiedad` |
| `incivilidades` | Disorder | Incivilidades | `disorder` | `incivilidades` | `series[].by_family.incivilidades` |
| `homicidios` (subgroup) | Homicide | Homicidios | _(new)_ | _(new)_ | `featured_rates.homicidios[year]` |

[VERIFIED: data/cead/comunas/10101.json + site/src/lib/familyDefs.ts + site/src/config/i18n.ts]

Note: `FAMILY_SLUGS` maps `vida -> { en: 'homicide', es: 'homicidios' }`. This means `/crime/homicide/` currently covers the "vida" (Life Crimes) FAMILY. A new page specifically for the homicide SUBGROUP should use a distinct URL to avoid collision. Suggested: `/crime/homicide-rate/` or `/crime-ranking/homicide/` (EN), `/es/ranking-delito/homicidios/` (ES). [ASSUMED — final URL pending planner decision]

### Value of N

- **Total communes:** 346
- **Non-low-population (eligible for ranking):** 256
- **Non-low-pop with non-zero homicide rate (2025):** 173

The ranking page should show all 256 non-low-pop communes (with 0-rate ones at bottom), mirroring the existing crime family pages which show all eligible rows. Low-pop communes appended below with asterisk footnote, matching existing pattern. N = 256 eligible communes in the ranked table. [VERIFIED: data inspection + existing crime page pattern]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ItemList JSON-LD | Custom schema builder | `buildItemList()` in `site/src/lib/jsonld.ts` | Phase 13 deliverable; editorial guard built in; already validator-tested |
| BreadcrumbList | Custom schema builder | `buildBreadcrumb()` in `site/src/lib/jsonld.ts` | Same |
| hreflang injection | Per-page `<link>` tags | BaseLayout `enPath`/`esPath` props | Already handles en/es/x-default + canonical |
| Sitemap registration | Manual sitemap.xml edit | `@astrojs/sitemap` + `getStaticPaths` | Auto-detects new routes |
| Forbidden-language checking | Manual review | `forbidden-language.mjs` build validator | Catches at build time; runs in CI |
| Rate computation | Custom aggregation | `loadCommune()` + `loadIndex()` from `data.ts` | Memoized; handles `latestCompleteYear` enrichment |
| OG/Twitter meta | Per-page meta tags | `BaseLayout` with `pageType="crime"` prop | Phase 13 deliverable; auto-selects `/og/crime.png` |

---

## Common Pitfalls

### Pitfall 1: Wrong data field for homicide rate
**What goes wrong:** Reading `series[].by_family['homicidios']` returns undefined (0 after nullish coalescing), so ALL communes show rate=0 and the ranking is meaningless.
**Why it happens:** Homicide is a subgroup (101) scraped separately; it lands in `featured_rates.homicidios` not in `by_family`.
**How to avoid:** Use `commune.featured_rates?.homicidios?.[commune.latestCompleteYear] ?? 0`.
**Warning signs:** All ranked rates are 0 in the built page.

### Pitfall 2: URL collision with existing /crime/homicide/ (vida family page)
**What goes wrong:** If the homicide ranking page is created at `/crime/homicide/`, it overwrites the existing `/crime/[family].astro` page for `vida` (which maps `vida -> en slug 'homicide'` via `FAMILY_SLUGS`).
**Why it happens:** `FAMILY_SLUGS.vida.en === 'homicide'` already occupies that URL.
**How to avoid:** Use a new URL namespace (e.g. `/crime-ranking/homicide/`) or rename the new page's slug (e.g. `/crime/homicide-rate/`).
**Warning signs:** Build-time Astro error about duplicate static paths, or the vida family page silently disappearing.

### Pitfall 3: getRelativeLocaleUrl does not translate ES slugs
**What goes wrong:** Calling `getRelativeLocaleUrl('es', '/crime-ranking/homicide/')` returns `/es/crime-ranking/homicide/` (not `/es/ranking-delito/homicidios/`), causing broken cross-locale links and incorrect hreflang.
**Why it happens:** Astro i18n only prefixes the locale; it does not translate path segments.
**How to avoid:** Hardcode the full ES path literal: `const esPath = '/es/ranking-delito/homicidios/';`
**Warning signs:** hreflang.mjs validator fails on reciprocity check; clicking the locale switcher 404s.

### Pitfall 4: buildItemList name triggers editorial guard
**What goes wrong:** Build fails with `[jsonld.ts] Forbidden term "safe" found in list name`.
**Why it happens:** `assertSafeName()` checks for 'safest', 'most dangerous', 'safe', 'dangerous' — the word "safe" alone is blocked.
**How to avoid:** Use "by reported {crime} incidence (descending)" framing, never "safest/most dangerous".
**Warning signs:** Build error from jsonld.ts; easy to trigger if copying from naive translations.

### Pitfall 5: Commune pages not updated to link to new URL namespace
**What goes wrong:** Comuna hub pages (D-10 crime-type spoke) still only link to `/crime/[family]/` (7 families) and miss the new homicide-specific ranking page.
**Why it happens:** The crime-type spoke iterates `Object.entries(byFamily)` which has the 7 family keys — homicidios is not a family key.
**How to avoid:** Add an explicit "Homicide ranking" spoke link in both `commune/[slug].astro` and `es/comuna/[slug].astro` pointing to the new page. This closes the IA-02 reciprocal-link requirement.

### Pitfall 6: seo.mjs sample set not updated
**What goes wrong:** `seo.mjs` does not sample the new crime-ranking pages, so OG/ItemList assertions never run on them.
**Why it happens:** `seo.mjs` has a hardcoded SAMPLES array with first-subdir heuristics for known path prefixes.
**How to avoid:** Add the new `crime-ranking/` and `es/ranking-delito/` paths to the SAMPLES array in `seo.mjs`.

---

## Code Examples

### Homicide Ranking Row Construction (verified pattern)

```typescript
// Source: verified data shape from data/cead/comunas/10101.json
// and loadCommune() in site/src/lib/data.ts

const index = loadIndex();
const rows = [];
for (const meta of index) {
  const commune = loadCommune(meta.cut);
  const rate = commune.featured_rates?.homicidios?.[commune.latestCompleteYear] ?? 0;
  rows.push({
    name: meta.name,
    slug: meta.slug,
    cut: meta.cut,
    regionName: commune.regionName,
    rate,
    low_population: meta.low_population,
  });
}
const eligibleRows = rows.filter(r => !r.low_population).sort((a, b) => b.rate - a.rate);
```

### ItemList + BreadcrumbList for Homicide Ranking (verified pattern)

```typescript
// Source: site/src/lib/jsonld.ts + crime/[family].astro (verified)
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Homicide Ranking' },  // current page — no url (schema.org spec)
]);

const ranking = buildItemList(eligibleRows, 'en', {
  name: 'Communes by reported homicide incidence (descending)',
  order: 'Descending',
  // urlMode defaults to 'commune' — uses /commune/{slug}/ prefix
});

const jsonLd = [jsonLdDataset, breadcrumb, ranking];
```

### BaseLayout invocation (verified pattern)

```astro
<!-- Source: site/src/pages/crime/[family].astro (verified) -->
<BaseLayout
  lang="en"
  title="Communes with the Highest Reported Homicide Rate in Chile — Chile Safety Map"
  description="Reported homicide rates per 100,000 inhabitants across Chilean communes. Official CEAD data, ranked nationally."
  enPath="/crime-ranking/homicide/"
  esPath="/es/ranking-delito/homicidios/"
  jsonLd={jsonLd}
  mountType="crime-type-map"
  pageType="crime"
>
```

### H1 keyword focus (sober framing, verified against forbidden-language list)

```html
<!-- EN — passes forbidden-language validator -->
<h1>Communes with the Highest Reported Homicide Incidence in Chile</h1>

<!-- ES — passes forbidden-language validator -->
<h1>Comunas con mayor incidencia de homicidios reportados en Chile</h1>
```

---

## Existing Validator Integration

### Validators that must pass after Phase 15

| Validator | What it checks | Action needed |
|-----------|----------------|---------------|
| `forbidden-language.mjs` | Scans ALL dist/ HTML for forbidden terms | No action — automatic; just write sober prose |
| `seo.mjs` | OG + ItemList shape on sampled pages | Add new crime-ranking sample paths to SAMPLES array |
| `hreflang.mjs` | Reciprocal hreflang on all pages | No action — BaseLayout handles it from enPath/esPath |
| `crime.mjs` | Crime-page HTML assertions | Check if it needs updating for new route |

Let me note: `crime.mjs` may need inspection to confirm it won't fail on new pages in a different path prefix. [ASSUMED — crime.mjs not read in full; planner should check]

---

## State of the Art

| Old Approach | Current Approach | Impact for Phase 15 |
|--------------|------------------|---------------------|
| Homicide folded in "vida" family | Phase 14: homicide is its own CEAD subgroup with `featured_rates.homicidios` | Enables homicide-specific ranking page with real per-commune data |
| No ItemList JSON-LD | Phase 13: `buildItemList()` in jsonld.ts | Ready to use; editorial guard included |
| No OG meta | Phase 13: BaseLayout OG injection | Ranking pages get OG automatically via `pageType="crime"` |
| Only 7 crime-family pages | Phase 15 target | Add homicide + optionally all 7 as "ranked N comunas" pages |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | URL scheme for new pages (new namespace `/crime-ranking/` vs. extending existing `/crime/`) | Architecture Patterns | Could cause URL collision with existing pages or missed internal links |
| A2 | `crime.mjs` validator doesn't need updates for new page route prefix | Validator Integration | Validator might fail on new pages with unrecognized path; planner should check |
| A3 | Commune hub pages need manual update to add homicide ranking spoke link | Common Pitfalls | If not updated, IA-02 reciprocal linking is incomplete |
| A4 | Final URL slug for homicide ranking (e.g., `/crime-ranking/homicide/` vs. `/communes-most-homicides/`) | Architecture Patterns | Affects SEO keyword targeting and internal link consistency |

---

## Open Questions

1. **URL scheme: new namespace vs. extend existing crime pages?**
   - What we know: `/crime/homicide/` is occupied by the `vida` family (FAMILY_SLUGS.vida.en = 'homicide')
   - What's unclear: Should Phase 15 use a new URL namespace or reclaim/rename slugs?
   - Recommendation: Use new namespace `/crime-ranking/[crime]/` + `/es/ranking-delito/[crime]/` to avoid touching existing pages and causing SEO disruption to already-indexed URLs.

2. **Which crime types beyond homicide to include in Phase 15?**
   - What we know: All 7 families have data; homicide is explicitly "first"
   - What's unclear: Does "homicide first" mean homicide only in Phase 15, or all 7+homicide?
   - Recommendation: Include all 7 crime families + homicide subgroup (8 pages × 2 locales = 16 pages). The data and template pattern are identical; the incremental cost is near zero.

3. **N in "las N comunas"?**
   - What we know: 256 non-low-pop communes, 173 with non-zero homicide rate
   - What's unclear: Should N be 20/50/all?
   - Recommendation: Show all 256 eligible (matching existing crime page behavior). The "N" in the phrase can be the actual count; the H1 can say "Comunas con mayor incidencia de homicidios reportados en Chile" without specifying N.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 15 is purely code/SSG changes. No external dependencies beyond existing Node.js + npm, already confirmed working.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Node.js ESM scripts (no test runner — project uses custom validators) |
| Config file | `site/scripts/validate/all.mjs` |
| Quick run command | `cd site && node scripts/validate/seo.mjs && node scripts/validate/hreflang.mjs && node scripts/validate/forbidden-language.mjs` |
| Full suite command | `cd site && npm run build && node scripts/validate/all.mjs` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CSEO-01 | Ranking pages exist for homicide (+ other types) in EN + ES | build smoke | `npm run build` (Astro build fails if getStaticPaths errors) | Wave 0 — new pages |
| CSEO-01 | hreflang reciprocal on all new pages | automated | `node scripts/validate/hreflang.mjs` | Yes |
| CSEO-01 | Sitemap contains new EN + ES URLs | automated | `node scripts/validate/coverage.mjs` (sitemap-coverage assertion) | Yes |
| CSEO-01 | Internal links to commune pages are valid | automated | `node scripts/validate/coverage.mjs` (no-orphan-link) | Yes |
| CSEO-02 | ItemList JSON-LD present and valid shape | automated | `node scripts/validate/seo.mjs` (after SAMPLES update) | Needs update |
| CSEO-02 | Single H1 per page | automated | `node scripts/validate/spine.mjs` (single-H1 assertion) | Yes |
| CSEO-02 | No forbidden language | automated | `node scripts/validate/forbidden-language.mjs` | Yes |
| CSEO-02 | OG meta present (title/desc/image/url/locale) | automated | `node scripts/validate/seo.mjs` (after SAMPLES update) | Needs update |

### Wave 0 Gaps

- [ ] `seo.mjs` SAMPLES array must be extended with first-subdir heuristic for `dist/crime-ranking/` and `dist/es/ranking-delito/` (or equivalent new path) — covers ItemList R-assertion and OG N/O/P assertions on new pages.
- [ ] New Astro page files: `site/src/pages/crime-ranking/[crime].astro` (EN) and `site/src/pages/es/ranking-delito/[crime].astro` (ES)

---

## Security Domain

No new security surface — purely static pre-rendered pages. No user input, no API calls, no auth. Existing ASVS V5 (input validation) is N/A for static generation. CEAD data is read-only at build time from committed JSON.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)

- `site/src/pages/crime/[family].astro` — complete template to replicate for Phase 15 EN pages
- `site/src/pages/es/delito/[family].astro` — complete template to replicate for Phase 15 ES pages
- `site/src/lib/jsonld.ts` — `buildItemList`, `buildBreadcrumb` API + editorial guard
- `site/src/lib/data.ts` — `CommuneData` type, `loadCommune`, `loadIndex`, `loadCatalog`, `latestCompleteYear` enrichment
- `site/src/config/i18n.ts` — `FAMILY_SLUGS`, `EN_STRINGS`, `ES_STRINGS`, `regionNameEs()`
- `site/src/lib/familyDefs.ts` — `FAMILY_LABELS_EN/ES`, `FAMILY_DEFS_EN/ES`, `homicidios` entry confirmed
- `site/src/layouts/BaseLayout.astro` — hreflang, canonical, OG injection from `enPath`/`esPath`
- `data/cead/comunas/10101.json` — confirmed `featured_rates.homicidios[year]` data shape
- `site/scripts/validate/forbidden-language.mjs` — full forbidden term list
- `site/scripts/validate/seo.mjs` — SAMPLES array, OG/ItemList assertions
- `site/scripts/validate/all.mjs` — 12-validator suite registry
- `data/cead/meta/index.json` — 346 communes, 256 non-low-pop confirmed via Node inspection

### Secondary (MEDIUM confidence)

- Project memory `i18n-localized-slug-pitfall` — getRelativeLocaleUrl does not translate ES slugs; confirmed by `es/delito/[family].astro` which hardcodes esPath as a constant.

---

## Metadata

**Confidence breakdown:**
- Data shape (homicide in featured_rates): HIGH — directly inspected commune JSON
- Template pattern (getStaticPaths, BaseLayout, jsonld): HIGH — directly read source files
- URL scheme (new namespace vs. extend): ASSUMED — architectural decision pending
- Sitemap auto-detection: HIGH — existing crime pages are already in sitemap via same mechanism
- Forbidden terms: HIGH — validator source read directly

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 (stable data schema; Astro 6.x stable)

---

## Data Mapping: 6 Aggregated Crime Ranking Categories

**Researched:** 2026-06-16
**Method:** Direct inspection of `data/cead/meta/catalog.json`, `pipeline/cead/catalog.py`, `pipeline/cead/normalizer.py`, `data/cead/comunas/13101.json` (Santiago, reference commune), all 346 commune JSON files (secuestros emptiness check), `site/src/lib/familyDefs.ts`.

---

### 1. Exact Delito Taxonomy in the Data

The CEAD pipeline produces **two levels** of crime data in the JSON files:

**Level A — 7 pre-aggregated family keys** (in every commune's `series[].by_family`):

```
"vida"            — family ID 1 (Life Crimes: homicide, assault, etc.)
"robos_violentos" — family ID 2 (Violent Robbery)
"vif"             — family ID 3 (Domestic/Intra-family Violence)
"drogas"          — family ID 4 (Drug offences)
"armas"           — family ID 5 (Weapons offences)
"propiedad"       — family ID 6 (Property Crimes: theft, burglary, fraud)
"incivilidades"   — family ID 7 (Disorder/public nuisance)
```

These 7 keys are the ONLY per-family keys available in `series[].by_family`. There is no finer-grained breakdown of individual delitos (e.g. "hurto" vs. "robo en lugar habitado") stored per commune in any existing JSON file. The pipeline accumulates family-level totals, not sub-family delito-level totals.

[VERIFIED: `data/cead/meta/catalog.json` — `family_keys` array; `pipeline/cead/catalog.py` — `FAMILIA_IDS` dict; `data/cead/comunas/13101.json` — `series[].by_family` keys]

**Level B — 2 featured subgroup series** (in `featured_rates`, top-level of each commune JSON):

```
"homicidios"       — rate_per_100k per year {year_str: float}, subgroup CEAD ID 101
"homicidios_count" — raw case count per year {year_str: int}
"secuestros"       — rate_per_100k per year — EMPTY {} in ALL 346 communes (subgroup ID not yet confirmed in pipeline)
"propiedad"        — rate_per_100k per year (duplicates series[].by_family.propiedad for convenience)
```

[VERIFIED: `data/cead/comunas/13101.json`; `pipeline/cead/normalizer.py` — `FEATURED_SUBGROUPS` dict; Python loop over all 346 commune JSONs confirmed `secuestros: {}` in 346/346 files]

**There is no per-delito granularity below the 7 families.** CEAD serves data at family level. Individual delito codes (e.g. "robo con violencia", "robo con intimidación", "hurto", "manejo en estado de ebriedad") are NOT available as separate series in the committed JSON data — only their combined family totals.

---

### 2. Mapping Table: 6 Categories to Data Keys

| # | Requested Category | Underlying Delitos (per CEAD taxonomy) | Data Key Available | Rate Source | Gap / Flag |
|---|-------------------|----------------------------------------|-------------------|-------------|-----------|
| a | **Homicidios** | Homicidio, parricidio, infanticidio, femicidio, etc. | `featured_rates.homicidios[latestCompleteYear]` | rate_per_100k | **AVAILABLE** — full time series, all 346 communes. Subgroup 101 scraped separately. |
| b | **Robos violentos** | Robo con violencia, robo con intimidación, robo en lugar habitado, etc. | `series[].by_family["robos_violentos"]` at `latestCompleteYear` | rate_per_100k | **AVAILABLE** — family key `robos_violentos` in every commune's series. |
| c | **Hurtos** | Hurtos (theft without violence) | NOT AVAILABLE as standalone | — | **GAP — BLOCKED.** Hurtos are a sub-type within `propiedad` (family 6). The `propiedad` family aggregates hurtos + robos en bienes + fraudes + others. No separate `hurtos` key exists in any commune JSON. Displaying `propiedad` would misrepresent the category as "hurtos". |
| d | **Trafico y microtrafico de drogas** | Tráfico de drogas, microtráfico, porte, etc. | `series[].by_family["drogas"]` at `latestCompleteYear` | rate_per_100k | **AVAILABLE** — family key `drogas` covers drug offences. Note: `drogas` includes porte (possession) + tráfico — not pure trafficking. Label must reflect this. |
| e | **Secuestros** | Secuestro | `featured_rates.secuestros[latestCompleteYear]` | rate_per_100k | **GAP — NO DATA.** `featured_rates.secuestros` is `{}` in ALL 346 communes. The pipeline stores the key but the CEAD subgroup ID is `null` in `normalizer.py:FEATURED_SUBGROUPS`. No data has ever been scraped for this subgroup. Ranking would show 0 for every commune. |
| f | **Manejo en estado de ebriedad** | Manejo en estado de ebriedad, conducción bajo influencia | NOT AVAILABLE as standalone | — | **GAP — BLOCKED.** This is a sub-type within `incivilidades` (family 7). No separate key exists in any commune JSON. Displaying `incivilidades` would misrepresent the category. |

[VERIFIED: All keys confirmed by direct inspection of `data/cead/comunas/13101.json`, `data/cead/meta/catalog.json`, and Python scan of all 346 commune files for `secuestros`]

**Summary of gaps:**
- **Hurtos (c):** No standalone data. Options: (i) label the `propiedad` family page as "Delitos contra la propiedad (incluye hurtos y robos)" and use `propiedad`, clearly explaining what the family covers; (ii) descope until CEAD subgroup-level scraping is added to the pipeline.
- **Secuestros (e):** No data at all. Must be descoped or marked "datos no disponibles" with a note, not shown as a ranking.
- **Manejo en estado de ebriedad (f):** No standalone data. Options: (i) use `incivilidades` family with clear labeling; (ii) descope.

---

### 3. Aggregation Point Recommendation

**Where existing aggregation happens:** All family-level aggregation (rate_per_100k per family per year) is computed **at pipeline scrape time** in `pipeline/scrape_cead.py` and stored in the per-commune JSON files (`data/cead/comunas/{cut}.json`). The Astro build reads these pre-aggregated values at SSG time — it does NOT re-aggregate raw delito counts.

The homicide featured rate is also computed at pipeline time (subgroup 101 scraped in a separate CEAD request) and stored in `featured_rates.homicidios`.

**Recommendation for the 6 categories:**

- **Categories with a direct family key** (robos_violentos, drogas): aggregate at **Astro build time** in `getStaticPaths`/page frontmatter, exactly as `crime/[family].astro` already does. Read `series[].by_family[key]` at `latestCompleteYear` and sort. No pipeline changes needed.
- **Homicidios**: aggregate at **Astro build time**, reading `featured_rates.homicidios[latestCompleteYear]`. This is already the pattern documented above.
- **Hurtos / Manejo en ebriedad** (if descoped to their parent family): same as family key approach, but requires honest labeling that the page covers the full family, not just the sub-type.
- **Secuestros**: no viable aggregation at any layer — data is absent. Descope.

There is **no need for a new Python precomputation step** for the 4 available categories. The values are already in the per-commune JSON at the right granularity. Adding a precomputed JSON (e.g. `data/cead/rankings/robos_violentos.json`) would duplicate what `getStaticPaths` already computes efficiently at build time via `loadIndex()` + `loadCommune()` (memoized).

[VERIFIED: `pipeline/scrape_cead.py`, `site/src/lib/data.ts` memoization pattern, `site/src/pages/crime/[family].astro` aggregation pattern]

---

### 4. Slug and H1 Proposals for the 6 Categories

URL namespace confirmed by scope decision: `/crime-ranking/[crime]/` (EN) + `/es/ranking-delito/[crime]/` (ES).

All H1 and `buildItemList` name strings have been checked against:
- `forbidden-language.mjs` FORBIDDEN_TERMS list: "zona peligrosa", "area peligrosa", "comuna peligrosa", "barrio peligroso", "ranking definitivo", "zona segura garantizada", "zona segura", "100% seguro", "seguridad garantizada", "la mas segura", "dangerous zone", "dangerous area", "dangerous commune", "dangerous neighborhood", "definitive ranking", "guaranteed safe", "100% safe", "guaranteed safety", "the safest"
- `jsonld.ts` assertSafeName guard: 'safest', 'most dangerous', 'safe', 'dangerous'

[VERIFIED: `site/scripts/validate/forbidden-language.mjs` — FORBIDDEN_TERMS array; `site/src/lib/jsonld.ts` — FORBIDDEN const]

| # | Category | EN Slug | ES Slug | EN H1 | ES H1 | ItemList `name` (EN) | Data available? |
|---|----------|---------|---------|-------|-------|---------------------|----------------|
| a | Homicidios | `homicide` | `homicidios` | "Communes with the Highest Reported Homicide Incidence in Chile" | "Comunas con mayor incidencia de homicidios reportados en Chile" | "Communes by reported homicide incidence (descending)" | YES |
| b | Robos violentos | `violent-robbery` | `robos-violentos` | "Communes with the Highest Reported Violent Robbery Incidence in Chile" | "Comunas con mayor incidencia de robos violentos reportados en Chile" | "Communes by reported violent robbery incidence (descending)" | YES |
| c | Hurtos | `property-theft` | `hurtos` | "Communes with the Highest Reported Property Crime Incidence in Chile" | "Comunas con mayor incidencia de delitos contra la propiedad reportados en Chile" | "Communes by reported property crime incidence (descending)" | PARTIAL — uses `propiedad` family; label must explain scope |
| d | Trafico drogas | `drug-trafficking` | `trafico-drogas` | "Communes with the Highest Reported Drug Offence Incidence in Chile" | "Comunas con mayor incidencia de delitos de drogas reportados en Chile" | "Communes by reported drug offence incidence (descending)" | YES — uses `drogas` family |
| e | Secuestros | — | — | — | — | — | NO DATA — descope |
| f | Manejo ebriedad | `public-disorder` | `incivilidades` | "Communes with the Highest Reported Public Disorder Incidence in Chile" | "Comunas con mayor incidencia de incivilidades reportadas en Chile" | "Communes by reported public disorder incidence (descending)" | PARTIAL — uses `incivilidades` family; label must explain scope |

**Collision check:** EN slugs `homicide`, `violent-robbery`, `property`, `drug-crimes`, `disorder` are currently used by the existing `crime/[family].astro` pages via `FAMILY_SLUGS`. The new `/crime-ranking/` namespace is a separate directory, so there is no file-level collision. [VERIFIED: `site/src/pages/crime/` only contains `[family].astro`; new pages go in `site/src/pages/crime-ranking/`]

**Note on slug re-use for (c) and (f):** Since the "hurtos" and "manejo en ebriedad" categories resolve to the `propiedad` and `incivilidades` family data respectively, the category pages for (c) and (f) in `/crime-ranking/` would be functionally identical to the existing `/crime/property/` and `/crime/disorder/` family pages — the same data, just with different framing. The planner should consider whether to create these as distinct pages (different URL, methodology-focused framing) or skip them and expand the existing family pages with methodology notes instead.

---

### 5. Methodological Note — Copy Location and Validator Compliance

Each category page must display a short methodological explanation stating:
1. Which underlying CEAD delito group the aggregate covers
2. That figures are "reported incidence" (denuncias), not convictions
3. CEAD as the source, with the year of data

**Where the copy lives:** In the existing `crime/[family].astro` pattern this is handled by `FAMILY_DEFS_EN` / `FAMILY_DEFS_ES` from `site/src/lib/familyDefs.ts`. The text is rendered as a `<p>` element inside the page component.

For the 6 new categories, the same pattern applies:
- Add entries to `familyDefs.ts` (or create a parallel `RANKING_DEFS_EN` / `RANKING_DEFS_ES` object in the new page file or a new `rankingDefs.ts` lib file)
- Pass the string as a prop to the page template
- Render as `<p class="methodology-note">` below the H1

**Example copy that passes both validators** (no forbidden terms, CEAD attribution):

```
// EN — homicidios
"Reported homicide incidence per 100,000 inhabitants by commune. Includes homicide,
femicide, parricide, infanticide, and related offences (CEAD subgroup 101 within
the Life Crimes family). Source: CEAD — Ministry of Interior and Public Security,
official police statistics."

// ES — homicidios
"Incidencia reportada de homicidios por 100.000 habitantes por comuna. Incluye
homicidio, femicidio, parricidio, infanticidio y delitos relacionados (subgrupo CEAD
101 dentro de Delitos contra la Vida). Fuente: CEAD — Ministerio del Interior y
Seguridad Pública, estadísticas policiales oficiales."
```

**Validator compliance check:**
- None of the proposed copy strings contain terms from `FORBIDDEN_TERMS` or `jsonld.ts` FORBIDDEN. [VERIFIED: compared against both lists directly]
- The `forbidden-language.mjs` validator scans visible text extracted from dist/ HTML — the methodology note is visible text, so it is scanned. The proposed framing passes.
- The `buildItemList` guard only applies to the `name` parameter, not to page body text.

**Where to store the copy:** Add to `site/src/lib/familyDefs.ts` as new entries alongside the existing 7+1 entries, or inline in the new `[crime].astro` page as a per-param constant map. The `familyDefs.ts` approach is preferred for consistency (single source of truth, matches existing pattern). [VERIFIED: `site/src/lib/familyDefs.ts` — existing structure is exactly a Record keyed by crime type string]

---

### Gap Summary for Planner

| Category | Action |
|----------|--------|
| Homicidios (a) | Implement — data ready in `featured_rates.homicidios` |
| Robos violentos (b) | Implement — data ready in `series[].by_family["robos_violentos"]` |
| Hurtos (c) | Decision required: use `propiedad` family with expanded methodology note, OR descope and revisit when pipeline adds hurto subgroup scraping |
| Trafico drogas (d) | Implement — data ready in `series[].by_family["drogas"]`; label as "drug offences" not "trafficking only" |
| Secuestros (e) | Descope — zero data across all 346 communes. Consider a placeholder page with "datos no disponibles en CEAD a nivel comunal" if the URL is needed for SEO purposes |
| Manejo ebriedad (f) | Decision required: use `incivilidades` family with expanded methodology note, OR descope and revisit when pipeline adds sub-family scraping |

---

## RESEARCH COMPLETE
