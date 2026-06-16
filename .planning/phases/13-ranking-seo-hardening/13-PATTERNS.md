# Phase 13: Ranking SEO Hardening - Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 17 (13 modified, 3 created, 1 optional)
**Analogs found:** 16 / 17 (1 new asset class — OG PNGs — has no code analog)

This phase is purely additive head-meta + structured-data work. Every file is a near-mechanical
extension of three already-established in-repo patterns: (1) centralized SEO injection in
`BaseLayout.astro`, (2) XSS-safe `set:html` JSON-LD, (3) dist-reading ESM validators. No body
content, copy, layout, or data changes.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/src/layouts/BaseLayout.astro` | layout (SEO inject) | transform (props→head) | self (existing hreflang/jsonLd block) | exact (extend self) |
| `site/src/layouts/HomeLayout.astro` | layout (wrapper) | request-response (prop pass-through) | `EditorialLayout.astro` (sibling) | exact |
| `site/src/layouts/EditorialLayout.astro` | layout (wrapper) | request-response (prop pass-through) | `HomeLayout.astro` (sibling) | exact |
| `site/src/lib/jsonld.ts` (CREATE, optional) | utility (lib helper) | transform (rows→JSON-LD) | `site/src/lib/slugMaps.ts` | role-match |
| `site/src/pages/commune/[slug].astro` (+ES) | route (page template) | transform (data→jsonLd[]) | self (existing single-object jsonLd) | exact (widen to array) |
| `site/src/pages/region/[slug].astro` (+ES) | route (page template) | transform (data→jsonLd[]) | `commune/[slug].astro` | exact |
| `site/src/pages/crime/[family].astro` (+ES) | route (page template) | transform (data→jsonLd[]) | `region/[slug].astro` | exact |
| `site/src/pages/rankings.astro` (+ES) | route (page template) | transform (links→ItemList) | `is-chile-safe.astro` (Editorial+jsonLd) | role-match |
| `site/src/pages/index.astro` (+ES) | route (home template) | transform (rows→ItemList) | `region/[slug].astro` (ItemList build) | role-match |
| `site/scripts/validate/seo.mjs` (CREATE) | test (dist validator) | file-I/O (read dist/) | `site/scripts/validate/spine.mjs` | exact (mirror) |
| `site/scripts/validate/all.mjs` | config (validator registry) | batch (spawn children) | self (VALIDATORS array) | exact (one-line add) |
| `site/public/og/*.png` (CREATE) | asset (static image) | file-I/O (served static) | none (no existing OG images) | NO ANALOG |

## Shared / Cross-Cutting Patterns

These three are referenced by nearly every Pattern Assignment below; copy them once and reuse.

### Shared A — XSS-safe JSON-LD injection (PRESERVE, widen to array)
**Source:** `site/src/layouts/BaseLayout.astro` lines 71-75
**Apply to:** BaseLayout (the widen point) + every page passing `jsonLd`
```astro
<!-- EXISTING single-object block (lines 73-75) -->
{jsonLd !== null && (
  <script is:inline type="application/ld+json" set:html={JSON.stringify(jsonLd).replace(/<\//g, '<\\/')} />
)}
```
Widen to (D-08, array-of-scripts — NOT @graph):
```astro
{jsonLd !== null && (Array.isArray(jsonLd) ? jsonLd : [jsonLd])
  .filter(Boolean)
  .map((block) => (
    <script is:inline type="application/ld+json" set:html={JSON.stringify(block).replace(/<\//g, '<\\/')} />
  ))
}
```
The `.replace(/<\//g, '<\\/')` is the CR-01 XSS fix — it MUST survive the map. `Array.isArray(...) ? ... : [...]`
keeps every existing single-object caller (commune Dataset+Place, region Dataset+Place, crime Dataset,
editorial FAQPage) working unchanged.

### Shared B — Centralized canonical/locale computation (REUSE for og:url, og:locale)
**Source:** `site/src/layouts/BaseLayout.astro` lines 35-36, 56-59
```astro
const BASE_URL = 'https://ischilesafe.com';
const canonicalPath = lang === 'en' ? enPath : esPath;
// ...
<link rel="canonical" href={`${BASE_URL}${canonicalPath}`} />
```
`og:url` = `${BASE_URL}${canonicalPath}` — already locale-correct for free (D-04). `og:locale` derived
from `lang`: `en` → `en_US`, `es` → `es_CL` (Pattern 3, ogp.me `language_TERRITORY` form).
**Project-memory pitfall (`i18n-localized-slug-pitfall`):** every absolute URL on an ES page must use the
hardcoded `/es/...` path segment — NEVER `getRelativeLocaleUrl`. `canonicalPath` already does this
(esPath is hardcoded per page), so og:url is safe; breadcrumb `item` URLs must be hardcoded the same way.

### Shared C — dist-reading validator scaffold (COPY verbatim into seo.mjs)
**Source:** `site/scripts/validate/spine.mjs` lines 21-31, 36-49, 356-365
The exact ESM harness: `import { readFileSync, existsSync, readdirSync } from 'node:fs'` +
`fileURLToPath`/`path`; `const SITE_ROOT = path.resolve(__dirname, '../..')`; `const DIST_DIR = path.join(SITE_ROOT, 'dist')`;
`let failures = 0`; per-assertion `console.log('PASS ...')` / `console.error('FAIL ...'); failures++`;
final `if (failures > 0) { ...; process.exit(1); } ... process.exit(0)`. Copy this skeleton, then swap
the assertions. **Editorial guard:** new JSON-LD `name` strings must contain no forbidden absolute term
(`forbidden-language.mjs` guards visible text only).

---

## Pattern Assignments

### `site/src/layouts/BaseLayout.astro` (layout, transform) — CORE of RSEO-01 + D-08

**Analog:** self. Extend the existing head + the existing single-object jsonLd block.

**Existing Props interface to widen** (lines 16-24):
```astro
interface Props {
  lang: 'en' | 'es';
  title: string;
  description: string;
  enPath: string;
  esPath: string;
  jsonLd?: object | null;          // → WIDEN to: object | object[] | null  (D-08)
  mountType?: string;
}
// ADD: pageType?: 'home'|'commune'|'region'|'crime'|'ranking'|'editorial';  (D-03)
```

**Existing destructure to extend** (lines 26-33): add `pageType` (default `'default'`).

**Existing head inject point** — the OG/Twitter `<meta>` block goes right after the hreflang/canonical block
(lines 55-59) and before PWA meta (lines 61-63). og:* use `property=`, twitter:* use `name=` (spec split;
Astro auto-escapes attribute values so no XSS handling needed for `<meta content=...>`).

**Frontmatter additions** (D-03/D-04, og:image-by-type + og:type + og:locale):
```astro
const OG_IMAGE_BY_TYPE = {
  home: '/og/home.png', commune: '/og/commune.png', region: '/og/region.png',
  crime: '/og/crime.png', ranking: '/og/ranking.png', editorial: '/og/editorial.png',
  default: '/og/default.png',
};
const ogImage = `${BASE_URL}${OG_IMAGE_BY_TYPE[pageType] ?? OG_IMAGE_BY_TYPE.default}`;
const ogType = pageType === 'editorial' ? 'article' : 'website';
const ogLocale    = lang === 'en' ? 'en_US' : 'es_CL';
const ogLocaleAlt = lang === 'en' ? 'es_CL' : 'en_US';
```

**Meta block** (place after line 59):
```astro
<meta property="og:site_name" content="Chile Safety Map" />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:type" content={ogType} />
<meta property="og:url" content={`${BASE_URL}${canonicalPath}`} />
<meta property="og:image" content={ogImage} />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content={ogLocale} />
<meta property="og:locale:alternate" content={ogLocaleAlt} />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content={title} />
<meta name="twitter:description" content={description} />
<meta name="twitter:image" content={ogImage} />
```

**jsonLd block:** replace lines 73-75 with the widened array map (Shared A).

---

### `site/src/layouts/HomeLayout.astro` (layout wrapper) — forward pageType + array jsonLd

**Analog:** self + sibling `EditorialLayout.astro` (identical wrap pattern).

**Existing Props** (lines 20-27) and pass-through (lines 35-42): widen `jsonLd?: object | null` →
`object | object[] | null`; add `pageType?: ...` to the interface and the destructure; forward both to
`<BaseLayout>`. `index.astro` currently passes NO jsonLd — after this phase it passes `pageType="home"`
plus the two ItemLists.
```astro
// add to destructure (line 29):  pageType
// add to <BaseLayout ...> (lines 35-42):  pageType={pageType}
```

---

### `site/src/layouts/EditorialLayout.astro` (layout wrapper) — default pageType='editorial'

**Analog:** self + sibling `HomeLayout.astro`. Same edit as HomeLayout, but **default `pageType = 'editorial'`**
(→ og:type=article, editorial.png). Existing Props lines 19-26, pass-through lines 34-41.
```astro
const { lang, title, description, enPath, esPath, jsonLd = null, pageType = 'editorial' } = Astro.props;
// forward pageType={pageType} to <BaseLayout>
```
**Pitfall 4:** `/rankings/` uses EditorialLayout but must override to `pageType="ranking"` (it's an index,
not an article). Confirm a passed `pageType` wins over the `'editorial'` default (it does — explicit prop
overrides default).

---

### `site/src/lib/jsonld.ts` (CREATE, optional) — shared builders

**Analog:** `site/src/lib/slugMaps.ts` — same `src/lib/` convention: top-of-file JSDoc comment,
`const BASE_URL = 'https://ischilesafe.com';`, named `export function`s returning plain objects, locale-aware
`/commune/` vs `/es/comuna/` prefixes built inline.

**buildItemList** (D-06 — position+url+name only; rate stays OUT — see Assumption A1, schema.org `ListItem`
has no honest rate slot):
```ts
export function buildItemList(
  rows: { name: string; slug: string }[],
  locale: 'en' | 'es',
  opts?: { name?: string; order?: 'Ascending' | 'Descending' | 'Unordered' }
) {
  const prefix = locale === 'en' ? '/commune/' : '/es/comuna/';
  const base = 'https://ischilesafe.com';
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    ...(opts?.name ? { name: opts.name } : {}),
    numberOfItems: rows.length,
    itemListElement: rows.map((row, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `${base}${prefix}${row.slug}/`,
      name: row.name,
    })),
  };
}
```

**buildBreadcrumb** (D-07 — last item omits `item`):
```ts
export function buildBreadcrumb(crumbs: { name: string; url?: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      ...(c.url ? { item: c.url } : {}),
    })),
  };
}
```
**Editorial guard:** ItemList `name` must NEVER contain "safest"/"most dangerous"/"safe"/"dangerous" —
reuse "reported incidence (ascending/descending)" phrasing.

---

### `site/src/pages/commune/[slug].astro` (+ `es/comuna/[slug].astro`) (route, transform)

**Analog:** self — existing single-object `jsonLd` (lines 108-123) + visual breadcrumb (lines 137-145).

**Existing jsonLd (KEEP, becomes array element 0)** lines 109-123: `['Dataset','Place']` with `spatialCoverage`,
`temporalCoverage`, CEAD `creator`. Do NOT rewrite — wrap into an array.

**Existing visual breadcrumb to mirror in JSON-LD** (lines 137-145), 4 levels:
`Home › Communes › {data.regionName} › {data.name}`. `regionSlug` already computed (line 77);
`data.regionName`, `data.name` already in scope.
```astro
import { buildBreadcrumb, buildItemList } from '../../lib/jsonld.ts';
const breadcrumb = buildBreadcrumb([
  { name: 'Home',           url: 'https://ischilesafe.com/' },
  { name: 'Communes',       url: 'https://ischilesafe.com/communes/' },
  { name: data.regionName,  url: `https://ischilesafe.com/region/${regionSlug}/` },
  { name: data.name },  // current — no item
]);
// "similar comunas" table = similarComunas (line 94), rendered via CommuneRankingTable (line 218)
const similarList = buildItemList(similarComunas, 'en', { order: 'Unordered' }); // proximity, NOT a rank
const jsonLdArray = [jsonLd, breadcrumb, similarList];
// pass jsonLd={jsonLdArray} pageType="commune"
```
**ES page** (`es/comuna/[slug].astro`): identical, but breadcrumb URLs hardcode `/es/`, `/es/comunas/`,
`/es/region/{regionSlug}/` and labels `Inicio › Comunas › {región} › {comuna}`; `buildItemList(..., 'es', ...)`.

---

### `site/src/pages/region/[slug].astro` (+ `es/region/[slug].astro`) (route, transform)

**Analog:** self (existing jsonLd lines 133-150) + `commune/[slug].astro` (array pattern).

**Existing visual breadcrumb** lines 164-168 — only **2 levels**: `Home › Regions` (`Regions` is a plain
`<span>`, no link). The ranking table is `CommuneRankingTable rows={rankingRows}` (line 204).
```astro
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Regions' },   // current (mirror the 2-element visual crumb — Assumption A2)
]);
const ranking = buildItemList(rankingRows, 'en', {
  name: `Communes in ${region.name} by reported CEAD incidence (descending)`,
  order: 'Descending',
});
const jsonLdArray = [jsonLd, breadcrumb, ranking]; // pageType="region"
```
**A2 open choice:** 2-element (strict visual mirror) vs append trailing `{region.name}` for a 3-element
richer SERP breadcrumb — both schema-valid; planner's call.

---

### `site/src/pages/crime/[family].astro` (+ `es/delito/[family].astro`) (route, transform)

**Analog:** `region/[slug].astro` (2-level breadcrumb + ranking ItemList). NOTE: crime page renders its
**own inline `<table>`** (lines 197-228) — NOT `CommuneRankingTable`. Build ItemList from `rankingRows`
in frontmatter (the same array the inline table maps over, line 209).

**Existing jsonLd** lines 145-161: `Dataset` only (NO Place) — KEEP as array element 0.
**Existing breadcrumb** lines 175-179: `Home › Crime Types` (`Crime Types` is a plain `<span>`).
```astro
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Crime Types' },  // current
]);
const ranking = buildItemList(rankingRows, 'en', {
  name: `Communes by reported ${familyLabel.toLowerCase()} incidence (descending)`,
  order: 'Descending',
});
const jsonLdArray = [jsonLd, breadcrumb, ranking]; // pageType="crime"
```
ES (`es/delito/[family].astro`): breadcrumb URL hardcodes `/es/`, label `Inicio › Tipos de delito`;
ItemList prefix `/es/comuna/`.

---

### `site/src/pages/rankings.astro` (+ `es/rankings.astro`) (route, transform) — hand-rolled, no shared component

**Analog:** `is-chile-safe.astro` (EditorialLayout page carrying jsonLd). **CRITICAL:** rankings.astro uses
`EditorialLayout`, a hand-coded `<ul>` of links (lines 38-62), and currently passes **NO jsonLd**. It does
NOT use `CommuneRankingTable` — build a small ItemList in frontmatter. **NO breadcrumb here** (D-07: no
visual breadcrumb → no BreadcrumbList). Pass `pageType="ranking"` to override EditorialLayout's editorial
default (Pitfall 4).
```astro
import { buildItemList } from '../lib/jsonld.ts';
// ItemList of the ranking-page links (position+url+name, no rate, Unordered) — D-06 weaker-semantic table.
// Links here are crime-type/index pages, not /commune/ pages — buildItemList's /commune/ prefix does NOT
// fit; either generalize buildItemList to accept full urls, or inline a bespoke ItemList object here.
// pass jsonLd={[itemList]} pageType="ranking"  — NO breadcrumb
```
**Planner note:** because rankings links are not commune slugs, either (a) add a `urls` overload to
`buildItemList`, or (b) hand-build the ItemList object inline (still `position`+`url`+`name`, `Unordered`).

---

### `site/src/pages/index.astro` (+ `es/index.astro`) (home, transform) — two lead tables → ItemList(s)

**Analog:** `region/[slug].astro` (ItemList from rows) + self. Home uses `HomeLayout`, currently NO jsonLd
(lines 51-57). Two lead tables: `lowestRows` (ascending, line 45) and `highestRows` (descending, line 48),
both `CommuneRankingTable` (lines 92, 98). **NO breadcrumb** (D-07). Pass `pageType="home"`.
```astro
import { buildItemList } from '../lib/jsonld.ts';
const lowestList  = buildItemList(lowestRows,  'en', { name: 'Communes by reported CEAD incidence (ascending)',  order: 'Ascending' });
const highestList = buildItemList(highestRows, 'en', { name: 'Communes by reported CEAD incidence (descending)', order: 'Descending' });
// pass jsonLd={[lowestList, highestList]} pageType="home"  to <HomeLayout>
```
Editorial guard: names must NOT say "safest"/"most dangerous". `rows` already have `name`+`slug`
(lines 34-35) so `buildItemList` works as-is.

---

### `site/scripts/validate/seo.mjs` (CREATE) (test, file-I/O) — MIRROR spine.mjs

**Analog:** `site/scripts/validate/spine.mjs` (scaffold, Shared C) + `schema.mjs` lines 33-42 (the
`extractJsonLd` regex — but EXTEND to extract-ALL with a `g`-flag loop; Pitfall 3).

**extractJsonLd → extractAllJsonLd** (schema.mjs grabs only the FIRST block via single `.match`; seo.mjs
pages now have 2-3 blocks, so loop):
```js
function extractAllJsonLd(html) {
  const re = /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  const blocks = []; let m;
  while ((m = re.exec(html)) !== null) {
    try { blocks.push(JSON.parse(m[1])); }
    catch (e) { blocks.push({ _parseError: e.message, _raw: m[1] }); }
  }
  return blocks;
}
```

**Representative sample** (one page per template type × both locales; pick first dir entry deterministically
like spine.mjs lines 308-318):
| type | EN | ES |
|------|----|----|
| home | `dist/index.html` | `dist/es/index.html` |
| commune | `dist/commune/<first>/index.html` | `dist/es/comuna/<first>/index.html` |
| region | `dist/region/<first>/index.html` | `dist/es/region/<first>/index.html` |
| crime | `dist/crime/<first>/index.html` | `dist/es/delito/<first>/index.html` |
| ranking | `dist/rankings/index.html` | `dist/es/rankings/index.html` |
| editorial | `dist/is-chile-safe/index.html` | `dist/es/delitos-por-comuna/index.html` |

**Assertions (cheap `content.includes` like spine.mjs):**
- OG presence ×6 types ×2 locales: `property="og:title"`, `og:description`, `og:type`, `og:url`,
  `og:image`, `og:locale` + `name="twitter:card"` content `summary_large_image`.
- og:url locale: EN page's og:url has no `/es/`; ES page's contains `/es/` (mirror spine.mjs EN/ES URL
  discrimination, lines 113-114).
- og:image absolute under `/og/`: matches `https://ischilesafe.com/og/`.
- (optional, offline-possible) `existsSync(path.join(DIST_DIR,'og',file))` — catches the missing-asset case
  (Pitfall 1).
- JSON-LD parse: `extractAllJsonLd`, every block `JSON.parse`s (catch → FAIL).
- ItemList shape (home/region/crime/ranking): find block `@type==='ItemList'`; assert
  `Array.isArray(itemListElement)`, length>0, every element numeric `position` + string `url` (D-10).
- BreadcrumbList shape (commune/region/crime): find `@type==='BreadcrumbList'`; every element `position` +
  `name` + (`item` on all but possibly last) (D-10).
- (optional) no parsed JSON-LD string value contains a forbidden absolute term.

OG assertion helper to copy (mirrors spine.mjs style):
```js
const OG_KEYS = ['og:title','og:description','og:type','og:url','og:image','og:locale'];
function checkOg(htmlPath, label, expectEsUrl) {
  if (!existsSync(htmlPath)) { console.error(`FAIL [OG] ${label}: file missing`); failures++; return; }
  const html = readFileSync(htmlPath, 'utf-8');
  for (const k of OG_KEYS)
    if (!html.includes(`property="${k}"`)) { console.error(`FAIL [OG] ${label}: missing ${k}`); failures++; }
  if (!html.includes('name="twitter:card" content="summary_large_image"'))
    { console.error(`FAIL [OG] ${label}: twitter card not summary_large_image`); failures++; }
  const m = html.match(/property="og:url"\s+content="([^"]+)"/);
  if (m) { const isEs = /\/es\//.test(m[1]);
    if (expectEsUrl !== isEs) { console.error(`FAIL [OG] ${label}: og:url locale mismatch (${m[1]})`); failures++; } }
}
```

---

### `site/scripts/validate/all.mjs` (config, batch) — register seo.mjs

**Analog:** self — the `VALIDATORS` array (lines 31-43). Add `'seo.mjs'` as the 12th entry (after
`'spine.mjs'`). Update the header doc comment count (`9 validation scripts` → 12; add a `12. seo.mjs` line).
It runs with `ROLLOUT_ALL=true` like the rest (line 61) — fine, sampled pages exist in any rollout with ≥1 commune.
```js
const VALIDATORS = [
  // ...existing 11...
  'spine.mjs',
  'seo.mjs',   // NEW
];
```

---

## Shared Patterns (consolidated)

### OG/Twitter meta (RSEO-01)
**Source:** new block in `BaseLayout.astro` (Pattern Assignment above).
**Apply to:** ALL pages automatically (single inject point; wrappers forward `pageType`).

### JSON-LD multiplicity (D-08)
**Source:** `BaseLayout.astro` lines 73-75 widened (Shared A).
**Apply to:** every page passing `jsonLd` (single object still works; arrays now allowed).

### Locale-correct absolute URLs (project memory pitfall)
**Source:** `BaseLayout.astro` lines 35-36 (`canonicalPath`) + `slugMaps.ts` (`/commune/` vs `/es/comuna/`).
**Apply to:** og:url (free via canonicalPath), every breadcrumb `item` URL, every ItemList `url`. Hardcode
`/es/...` segments on ES pages — never `getRelativeLocaleUrl`.

### Validator harness (Shared C)
**Source:** `spine.mjs` lines 21-31, 36-49, 356-365.
**Apply to:** `seo.mjs` (copy verbatim, swap assertions) + `all.mjs` registration.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `site/public/og/*.png` (7 files) | static asset | file-I/O | `site/public/og/` does NOT exist yet (verified — public/ has only `data/`, `icon-192.png`, `icon-512.png`, `manifest.json`). No existing OG image to copy. This is an **asset-authoring task**, not a code task: produce 7 × 1200×630 PNG (home, commune, region, crime, ranking, editorial, default). Must exist before build or `og:image` 404s (offline validator can assert the file exists on disk but cannot fetch it). Flag for human/design step or a simple branded placeholder. |

## Metadata

**Analog search scope:** `site/src/layouts/`, `site/src/components/`, `site/src/pages/` (+ `es/`),
`site/src/lib/`, `site/scripts/validate/`, `site/public/`.
**Files read for excerpts:** BaseLayout.astro, HomeLayout.astro, EditorialLayout.astro, CommuneRankingTable.astro,
commune/[slug].astro, region/[slug].astro, crime/[family].astro, rankings.astro, index.astro, slugMaps.ts,
spine.mjs, schema.mjs, all.mjs.
**Verified facts:** rankings.astro = EditorialLayout + hand-rolled `<ul>`, no jsonLd, no CommuneRankingTable;
crime page = own inline `<table>` (not shared component); index.astro = HomeLayout, no jsonLd; commune jsonLd
is single `['Dataset','Place']` object; `site/public/og/` absent.
**Pattern extraction date:** 2026-06-15
