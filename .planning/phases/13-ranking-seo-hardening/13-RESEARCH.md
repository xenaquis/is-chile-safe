# Phase 13: Ranking SEO Hardening - Research

**Researched:** 2026-06-15
**Domain:** Static-site SEO meta + schema.org structured data (OpenGraph/Twitter Card, ItemList/BreadcrumbList JSON-LD) in Astro 6, plus an offline dist-reading validator
**Confidence:** HIGH

## Summary

This phase is **purely additive head-meta + structured-data work**. No body content, layout, copy, or data changes. Two deliverables land almost entirely in two files plus one new validator:

1. **RSEO-01 (OG/Twitter):** All injection happens in `BaseLayout.astro` `<head>` — the single SEO inject point that already owns `<title>`, description, hreflang, canonical, and PWA meta. The page `<title>` and meta `description` are *already* computed per-locale and passed in, so OG title/description reuse them verbatim (D-02). The only genuinely new inputs are (a) a page-type signal prop for image selection and og:type, and (b) the per-locale `og:locale` value. Both `HomeLayout` and `EditorialLayout` already wrap `BaseLayout` and pass props straight through, so a single new optional prop on `BaseLayout` cascades site-wide with zero per-page frontmatter for the common case.

2. **RSEO-02 (JSON-LD):** Both `ItemList` and `BreadcrumbList` flow through the **same `jsonLd` slot** already in `BaseLayout`, which must be widened from `object | null` to `object | object[] | null`. The XSS-safe `JSON.stringify(...).replace(/<\//g,'<\\/')` injector is preserved by mapping over the array and emitting one `<script type="application/ld+json">` per object. **Array-of-scripts is strongly preferred over `@graph`** (rationale below). The existing single-object `jsonLd` callers (commune Dataset+Place, region Dataset+Place, crime Dataset, editorial FAQPage) keep working unchanged because the widened type still accepts a lone object.

**Critical wrinkle the planner must know:** The `/rankings/` index page (`src/pages/rankings.astro` + ES) is a **hand-coded `<ul>` of links — it does NOT use `CommuneRankingTable`**. So the D-05 "ItemList on /rankings/" cannot come from the shared component; that page must build its own small ItemList in frontmatter. The shared `CommuneRankingTable.astro` covers home lead tables, region pages, and "similar comunas", but the crime-type page renders its **own inline `<table>`** (not the shared component either), and `/rankings/` and the crime page need bespoke ItemList construction.

**Primary recommendation:** Centralize OG/Twitter in `BaseLayout` with a `pageType` prop + per-type static images under `site/public/og/`; widen `jsonLd` to accept an array and emit one script per object; build ItemList/BreadcrumbList JSON-LD in each template's frontmatter (a small shared helper in `src/lib/` reduces duplication) and pass through the existing slot; mirror `spine.mjs` into a new `seo.mjs` validator that regex-extracts meta tags + `JSON.parse`s every ld+json block on one sampled page per template type × both locales.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OG/Twitter meta emission | Frontend build (Astro `BaseLayout` head) | — | Static pre-render; meta must be in the served HTML for crawlers/scrapers. No client JS. |
| og:image asset hosting | CDN / Static (`public/og/`) | — | Static files served at `/og/...`; referenced as absolute URLs. |
| ItemList JSON-LD construction | Frontend build (page frontmatter / lib helper) | — | Built at SSG time from the same data the table renders. |
| BreadcrumbList JSON-LD construction | Frontend build (page frontmatter / lib helper) | — | Mirrors the static visual breadcrumb already in the template. |
| Offline shape validation | Build tooling (Node ESM, reads `dist/`) | — | No network (per ~$0 / offline constraint); runs after build like every existing validator. |

## Project Constraints (from CLAUDE.md)

- **Astro 6.4.x** (v6.4.6 installed — verified) + React islands; `prefixDefaultLocale: false` (EN clean URLs, ES `/es/` prefix).
- **All pages static pre-rendered & indexable** — nothing SEO-critical may be render-only/client. OG/Twitter/JSON-LD must be in the built HTML.
- **~$0 build** — validation is **offline only, no network calls** (no live schema.org validator API, no Google Rich Results API). Matches D-10.
- **Editorial rule (load-bearing):** NEVER imply a territory is absolutely safe/dangerous. Structured data must inherit the existing CEAD-attributed "reported incidence" framing — no `ItemList` named "safest communes", no rate presented as a risk score.
- **GSD workflow enforcement:** edits go through a GSD command (this is planning, not editing).
- **i18n localized-slug pitfall (project memory):** `getRelativeLocaleUrl` does NOT translate ES slugs. ES slugs are hardcoded per-locale (`/es/comuna/`, `/es/delito/`, `/es/region/`, `/es/rankings/`). `og:url`, absolute `og:image` URLs (image filenames are language-neutral, but the URL host is constant), and every BreadcrumbList `item` URL MUST use the locale-correct hardcoded path.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**OpenGraph / Twitter meta (RSEO-01)**
- **D-01:** Inject OG (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:locale`) + Twitter Card meta **site-wide in `BaseLayout.astro` `<head>`** — the same single inject point that already handles hreflang/canonical. No per-page frontmatter duplication.
- **D-02:** **Reuse existing text** — `og:title` = the page `<title>`, `og:description` = the page meta description (both already passed per-locale into BaseLayout). DRY, inherits the existing non-absolute phrasing.
- **D-03:** **og:image = static images per page TYPE** (home, comuna, region, ranking, editorial), stored under `site/public/og/`, referenced as absolute `https://ischilesafe.com/og/<type>.<ext>`. BaseLayout selects the image from a page-type signal (a new optional prop, e.g. `ogType`/`pageType`), with a site-wide default fallback. **Twitter card = `summary_large_image`**. NOT a single site-wide image; NOT per-page generated cards (deferred).
- **D-04:** `og:url` = the lang-correct canonical already computed in BaseLayout (`enPath`/`esPath`). Emit `og:locale` per `lang` + an `og:locale:alternate`. `og:type` defaults to `website`, `article` for editorial pages (exact mapping = Claude's discretion).

**ItemList JSON-LD (RSEO-02)**
- **D-05:** **Full coverage** — emit `ItemList` JSON-LD on every ranking table: regional ranking (region pages + the ficha's regional context), `/crime/[family]` + `/es/delito/[family]`, the home's two lead tables (lowest/highest), the `/rankings/` index, and the ficha "similar comunas" table.
- **D-06:** ListItems carry `position` + `url` (the comuna page) + `name`; include the **rate** where the table shows an absolute reported rate (regional, crime-type, home lead). For the semantically weaker tables: `/rankings/` index = ItemList of links (`position`+`url`+`name`, no rate); **"similar comunas" position reflects the displayed proximity order, NOT a safety ranking** — represent honestly, never as a rate-rank. Structured data must never imply absolute safe/dangerous.

**BreadcrumbList JSON-LD (RSEO-02)**
- **D-07:** Emit `BreadcrumbList` JSON-LD **only where a visual breadcrumb renders** — comuna, region, and crime-type pages (per SC2). Home and `/rankings/` have no visual breadcrumb → no BreadcrumbList there. Mirror the exact visual hierarchy + per-locale labels (comuna breadcrumb = `Inicio › Comunas › Región › Comuna`).

**JSON-LD emission mechanism**
- **D-08:** A single page can need BOTH `BreadcrumbList` + `ItemList`. BaseLayout's `jsonLd` prop currently accepts ONE object — **extend it to accept `object | object[]`** (one `<script>` per object) **or** a schema.org `@graph`; pick whichever is cleanest + schema-valid (Claude's discretion / confirm in research). **Preserve the existing XSS-safe `JSON.stringify(...).replace(/<\//g,'<\\/')` handling.**

**Validation (RSEO-01 / RSEO-02)**
- **D-09:** **Sampled validator** — a new build-time validator (mirror Phase-12 `spine.mjs` ESM pattern, reads `dist/`) asserts OG/Twitter meta + JSON-LD presence on **one representative page per template type** (home, comuna, region, crime, ranking, editorial) × both locales. Register it in `site/scripts/validate/all.mjs`. Not all 774 pages.
- **D-10:** "Validate against schema.org" = **offline shape check** (no network). Parse each JSON-LD block and assert `@context`/`@type` + required fields — `ItemList`: `itemListElement[].position` + `url`; `BreadcrumbList`: `itemListElement[].position` + `name` + `item`.

### Claude's Discretion
- Exact `og:type` mapping per template; `og:locale` value form (`en_US`/`es_CL` vs `en`/`es`); per-type OG image filenames + dimensions (1200×630 standard) and the default-fallback image; `jsonLd` as array-of-scripts vs `@graph`; which exact URLs are picked as each "template type" for the sampled validator.

### Deferred Ideas (OUT OF SCOPE)
- **Dynamically generated per-page OG card images** (satori / @vercel-og with comuna name + rate) → future enhancement; static per-type images ship now.
- Any change to page copy/content/layout to "improve SEO" → out of scope; additive meta/structured-data only.
- AdSense Consent Mode → unrelated, remains its own concern.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RSEO-01 | OpenGraph + Twitter Card site-wide via base layout (title/description/image/url/type), locale-correct; verified on ranking/editorial/comuna/region | OG/Twitter meta block added to `BaseLayout.astro` head (§Architecture Pattern 1); `pageType` prop + `public/og/<type>.png` selection (§Pattern 2); `og:locale=en_US/es_CL` confirmed authoritative (§Pattern 3); reuses existing `title`/`description`/`enPath`/`esPath` props (D-02/D-04). |
| RSEO-02 | `ItemList` JSON-LD on ranking tables + `BreadcrumbList` where breadcrumb visible; validate against schema.org; build check on sampled templates | Widen `jsonLd` to `object[]`, one script per block (§Pattern 4); ItemList shape with honest position/url/name + optional rate-out-of-structured-data (§Pattern 5); BreadcrumbList shape mirroring visual hierarchy (§Pattern 6); new `seo.mjs` offline validator mirroring `spine.mjs` (§Pattern 7). |
</phase_requirements>

## Standard Stack

**No new dependencies.** Everything needed is already installed and in-repo.

### Core (all already present — verified in `site/package.json`)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| astro | 6.4.6 | Static rendering of head meta + JSON-LD scripts via `set:html` / `is:inline` | Already the framework; `is:inline` + `set:html` is the established XSS-safe JSON-LD pattern in `BaseLayout`. [VERIFIED: package.json] |
| @astrojs/sitemap | 3.7.3 | (unchanged) sitemap — no change this phase | Already present. [VERIFIED: package.json] |
| node | 22.21.1 | Runs the ESM dist-reading validators | Matches existing `scripts/validate/*.mjs` runtime. [VERIFIED: node --version] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| node:fs / node:path / node:url | builtin | New `seo.mjs` reads `dist/` HTML | Mirror `spine.mjs` / `schema.mjs` exactly — `readFileSync`, `readdirSync`, regex extraction, `JSON.parse`. No HTML parser dependency needed (existing validators use regex). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex `<script type="application/ld+json">` extraction (as `schema.mjs` already does) | `node-html-parser` / `cheerio` | Adds a dependency for no benefit; existing `schema.mjs` already extracts + `JSON.parse`s LD blocks with a single regex. Stay consistent and dependency-free (~$0 build). |
| Astro native head injection in layout | `astro-seo` / `@astrolib/seo` integration | A third-party SEO component would duplicate logic already centralized in `BaseLayout` and conflict with the existing hand-rolled hreflang/canonical/JSON-LD. CLAUDE.md centralizes SEO in BaseLayout — keep it. Hand-written `<meta>` lines are trivial and fully controlled. |
| Static per-type OG images (`public/og/*.png`) | `@vercel/og` / `satori` dynamic cards | Explicitly DEFERRED (D-03 / Deferred Ideas). Dynamic generation needs a render step at build that costs build time + complexity. |

**Installation:** None. No `npm install` required for this phase.

## Package Legitimacy Audit

> Not applicable — this phase installs **zero** external packages. All work uses already-installed Astro 6.4.6 and Node builtins. slopcheck/registry verification is moot.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none) | — | No new packages introduced |

## Architecture Patterns

### System Architecture Diagram

```
                       BUILD TIME (astro build, SSG)
  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                        │
  │  page template (commune/region/crime/rankings/home/editorial)         │
  │     │                                                                  │
  │     │  frontmatter computes:                                          │
  │     │    • title, description (already exist)                          │
  │     │    • enPath, esPath    (already exist)                           │
  │     │    • jsonLd: builds [ItemList?, BreadcrumbList?] array  ← NEW    │
  │     │    • pageType: 'home'|'commune'|'region'|'crime'|                │
  │     │                'ranking'|'editorial'                  ← NEW prop │
  │     ▼                                                                  │
  │  ┌──────────────── BaseLayout.astro <head> ──────────────────────┐    │
  │  │  existing: <title>, description, hreflang×3, canonical, PWA    │    │
  │  │  NEW: og:title=title, og:description=description,              │    │
  │  │       og:url=BASE+canonicalPath, og:type=(map pageType),       │    │
  │  │       og:image=BASE+/og/<imageFor(pageType)>.png (1200×630),   │    │
  │  │       og:locale=(en_US|es_CL), og:locale:alternate,            │    │
  │  │       twitter:card=summary_large_image, twitter:title/desc/img │    │
  │  │  WIDENED jsonLd: object|object[]|null →                        │    │
  │  │       (Array.isArray? blocks : [blocks]).filter(Boolean)       │    │
  │  │         .map(o => <script ld+json set:html={escape(o)}/>)      │    │
  │  └────────────────────────────────────────────────────────────────┘    │
  │     │                                                                  │
  │     ▼  emits → dist/<route>/index.html  (static, crawlable)           │
  └──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼  (after build, separate process)
  ┌──────────────────────────────────────────────────────────────────────┐
  │  scripts/validate/seo.mjs  (NEW, mirrors spine.mjs)                    │
  │    reads dist/ → for each sampled page (1 per template type × en/es):  │
  │      • assert OG/Twitter <meta> present (regex)                        │
  │      • extract ALL <script ld+json> → JSON.parse each (offline)        │
  │      • assert ItemList/BreadcrumbList shape per D-10                    │
  │      • process.exit(1) on any failure                                  │
  │    registered in scripts/validate/all.mjs VALIDATORS array            │
  └──────────────────────────────────────────────────────────────────────┘

  Static assets: site/public/og/{home,commune,region,crime,ranking,
                 editorial,default}.png  → served at /og/*.png  (NEW)
```

### Component Responsibilities

| File | Responsibility | Change type |
|------|----------------|-------------|
| `site/src/layouts/BaseLayout.astro` | Emit OG/Twitter meta from existing props + new `pageType`; widen `jsonLd` to array; emit one `<script>` per LD block | EDIT (core of RSEO-01 + D-08) |
| `site/src/layouts/HomeLayout.astro` | Pass `pageType` + array `jsonLd` through to BaseLayout | EDIT (widen prop type, forward `pageType`) |
| `site/src/layouts/EditorialLayout.astro` | Pass `pageType` (default 'editorial' → og:type=article) + array `jsonLd` through | EDIT (widen prop type, forward `pageType`) |
| `site/src/pages/commune/[slug].astro` (+ ES) | Build `[Dataset+Place(existing), BreadcrumbList(new), ItemList(similar comunas, new)]`; pass `pageType="commune"` | EDIT |
| `site/src/pages/region/[slug].astro` (+ ES) | Build `[Dataset+Place(existing), BreadcrumbList(new), ItemList(ranking, new)]`; `pageType="region"` | EDIT |
| `site/src/pages/crime/[family].astro` (+ ES) | Build `[Dataset(existing), BreadcrumbList(new), ItemList(ranking, new)]`; `pageType="crime"` | EDIT |
| `site/src/pages/rankings.astro` (+ ES) | Build `[ItemList(link list, no rate)]`; `pageType="ranking"`; NO breadcrumb | EDIT |
| `site/src/pages/index.astro` (+ ES) | Build `[ItemList(lowest), ItemList(highest)]` (two lists) OR one ItemList; `pageType="home"`; NO breadcrumb | EDIT |
| Editorial pages (`is-chile-safe.astro` etc.) | Inherit `pageType="editorial"` default from EditorialLayout (og:type=article); existing FAQPage jsonLd unchanged | EDIT (mostly automatic via layout default) |
| `site/src/lib/jsonld.ts` (NEW, optional) | Shared `buildItemList(rows, locale, {includeRate})` + `buildBreadcrumb(crumbs, locale)` helpers to avoid duplicating shape logic across ~10 templates | NEW |
| `site/public/og/*.png` (NEW) | 7 static 1200×630 images (home, commune, region, crime, ranking, editorial, default) | NEW assets |
| `site/scripts/validate/seo.mjs` (NEW) | Offline sampled validator | NEW |
| `site/scripts/validate/all.mjs` | Register `seo.mjs` in VALIDATORS array | EDIT (one line) |

### Recommended Project Structure (additions only)
```
site/
├── public/
│   └── og/                  # NEW — static per-type OG images (1200×630 PNG)
│       ├── default.png      # site-wide fallback
│       ├── home.png
│       ├── commune.png
│       ├── region.png
│       ├── crime.png
│       ├── ranking.png
│       └── editorial.png
├── src/
│   └── lib/
│       └── jsonld.ts        # NEW (optional) — buildItemList + buildBreadcrumb helpers
└── scripts/validate/
    └── seo.mjs              # NEW — offline OG/Twitter + JSON-LD shape validator
```

### Pattern 1: OG/Twitter meta block in BaseLayout head

**What:** Hand-written `<meta property=... />` lines placed alongside the existing hreflang/canonical block. og:title/description reuse the existing `title`/`description` props (D-02). og:url reuses the already-computed `canonicalPath`.

**When to use:** Once, in `BaseLayout.astro`, covering every page.

```astro
---
// BaseLayout.astro frontmatter additions
interface Props {
  lang: 'en' | 'es';
  title: string;
  description: string;
  enPath: string;
  esPath: string;
  jsonLd?: object | object[] | null;   // WIDENED (D-08)
  mountType?: string;
  pageType?: 'home' | 'commune' | 'region' | 'crime' | 'ranking' | 'editorial'; // NEW (D-03)
}
const { lang, title, description, enPath, esPath, jsonLd = null, pageType = 'default' } = Astro.props;

const BASE_URL = 'https://ischilesafe.com';
const canonicalPath = lang === 'en' ? enPath : esPath;

// D-03: page-type → static OG image, with default fallback
const OG_IMAGE_BY_TYPE = {
  home: '/og/home.png', commune: '/og/commune.png', region: '/og/region.png',
  crime: '/og/crime.png', ranking: '/og/ranking.png', editorial: '/og/editorial.png',
  default: '/og/default.png',
};
const ogImage = `${BASE_URL}${OG_IMAGE_BY_TYPE[pageType] ?? OG_IMAGE_BY_TYPE.default}`;

// D-04: og:type — article only for editorial; website everywhere else
const ogType = pageType === 'editorial' ? 'article' : 'website';

// Pattern 3: og:locale must be language_TERRITORY (ogp.me)
const ogLocale = lang === 'en' ? 'en_US' : 'es_CL';
const ogLocaleAlt = lang === 'en' ? 'es_CL' : 'en_US';
---
<!-- OpenGraph (RSEO-01) -->
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
<!-- Twitter Card (D-03: summary_large_image) -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content={title} />
<meta name="twitter:description" content={description} />
<meta name="twitter:image" content={ogImage} />
```

Notes:
- og:* use `property=`, twitter:* use `name=` — this is the correct, spec-aligned split. [CITED: ogp.me, Twitter Cards docs]
- These are plain attribute interpolations; Astro HTML-escapes attribute values automatically, so no XSS handling needed for `<meta content=...>` (unlike JSON-LD inside `<script>`).

### Pattern 2: Page-type → image signal as a BaseLayout prop (D-03)

**What:** A single optional `pageType` prop drives both the OG image and og:type. Default falls back to `default.png` + `website`. The wrapper layouts set sensible defaults so most pages need zero per-page change:
- `EditorialLayout` defaults `pageType="editorial"` (→ article). Editorial pages inherit it automatically.
- `HomeLayout` is used by `index.astro` → pass `pageType="home"`.
- Commune/region/crime templates use `BaseLayout` directly → pass `pageType` explicitly.
- `/rankings/` uses `EditorialLayout` but should pass `pageType="ranking"` to override the editorial default (it's a ranking index, og:type=website is fine; image=ranking.png).

**Dimensions:** 1200×630 px is the standard `summary_large_image` / OG size (1.91:1). [CITED: Twitter/X Cards docs, Facebook sharing best-practice]. PNG is safe and universally supported; keep each under ~300 KB to stay well within CF Pages 25 MiB file limit (a non-issue) and to load fast in scrapers.

### Pattern 3: og:locale value form — `en_US` / `es_CL` (D-04)

**Confirmed authoritative:** OGP spec states og:locale is "of the format `language_TERRITORY`. Default is `en_US`." [VERIFIED: ogp.me] — so the bare `en`/`es` form is NOT spec-compliant. Use:
- EN pages: `og:locale = en_US`, `og:locale:alternate = es_CL`
- ES pages: `og:locale = es_CL`, `og:locale:alternate = en_US`

`es_CL` (Chile) is the correct territory for a Chile-focused Spanish audience (over generic `es_ES`/`es_419`). Facebook's supported-locale list includes `es_LA`/`es_ES`; `es_CL` is a valid BCP-47-style `language_TERRITORY` and is the honest signal. If a validator wants to be strict, `es_CL` is well-formed; this is low-risk.

### Pattern 4: JSON-LD multiplicity — array-of-scripts, NOT @graph (D-08)

**Recommendation: widen `jsonLd` to `object | object[] | null` and emit one `<script type="application/ld+json">` per object.** Rationale:

1. **Backward compatible by construction.** Every existing caller passes a single object (commune Dataset+Place, region Dataset+Place, crime Dataset, editorial FAQPage). `Array.isArray(jsonLd) ? jsonLd : [jsonLd]` keeps them all working with zero edits to those JSON-LD blocks. An `@graph` migration would force rewriting every existing block into graph nodes with `@id` cross-references — far more churn and risk.
2. **Google explicitly supports multiple separate `<script>` blocks per page** and treats them equivalently to a single combined block. Multiple top-level scripts is the simplest valid representation. [CITED: Google Search Central — structured data general guidelines]
3. **Preserves the XSS-safe escaping trivially** — the existing `.replace(/<\//g,'<\\/')` is applied per object in the `.map`.
4. **Cleaner mental model** — each block is an independent, self-contained `@context`-rooted object. `@graph` requires a single shared `@context` and `@id` plumbing to relate nodes, which is unnecessary here (Breadcrumb and ItemList are independent).

Implementation in BaseLayout head (replaces the current single-object block):

```astro
{jsonLd !== null && (Array.isArray(jsonLd) ? jsonLd : [jsonLd])
  .filter(Boolean)
  .map((block) => (
    <script is:inline type="application/ld+json" set:html={JSON.stringify(block).replace(/<\//g, '<\\/')} />
  ))
}
```

**Anti-pattern:** Do NOT switch to `@graph` — it breaks all existing single-object callers and adds `@id` complexity for no SEO benefit here.

### Pattern 5: ItemList shape — honest, rate OUT of structured data (D-06)

**schema.org finding:** `ListItem` has **no native property for a numeric rate/value**. [VERIFIED: schema.org/ItemList, schema.org/ListItem]. `ListItem` supports `position`, `item`, `name`, `url` (name/url inherited from Thing). There is no `value`/`rate` slot.

**Recommendation: keep the rate OUT of the structured data entirely** for ALL ItemLists — even the "absolute reported rate" tables. D-06 says "include the rate where the table shows an absolute reported rate," but:
- There is no schema.org-honest place to put it on a `ListItem`.
- The only way to attach it (e.g. wrapping each item in a `Dataset`/`Observation` with a `value`) would re-introduce exactly the "this is a measured safety value per commune" framing the editorial rule forbids in machine-readable form, and risks Google reading the ItemList as a ranked quantitative leaderboard of places.
- The safe, valid, honest representation is **position + url + name only** — a list of links in display order. This satisfies RSEO-02 ("rank position + comuna link") and D-10's required fields (`position` + `url`) without asserting a value.

If the planner/user insists on surfacing the rate (re-reading D-06 literally), the **only** schema-clean option is `ListItem.item` pointing to a minimal `Thing`/`Place` whose `name` includes the rate as descriptive text — but this still risks the leaderboard framing. **My strong recommendation, flagged for confirmation: emit position+url+name only.** This is the cleanest reconciliation of D-06's intent (honest, no safety-rank) with the editorial rule. [ASSUMED — D-06 says "include rate where shown"; schema.org has no honest slot, so this resolves the conflict toward honesty. Needs user confirmation.]

```ts
// src/lib/jsonld.ts — shared helper
export function buildItemList(
  rows: { name: string; slug: string }[],
  locale: 'en' | 'es',
  opts?: { name?: string }
) {
  const prefix = locale === 'en' ? '/commune/' : '/es/comuna/';
  const base = 'https://ischilesafe.com';
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    ...(opts?.name ? { name: opts.name } : {}),
    itemListOrder: 'https://schema.org/ItemListOrderDescending', // or Ascending for "lowest" / Unordered for similar
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

**Per-table honesty mapping (D-06):**
| Table | itemListOrder | Notes |
|-------|---------------|-------|
| Home "Lowest Reported Rate" | `ItemListOrderAscending` | Order reflects ascending reported rate. Name it neutrally, e.g. "Communes by reported CEAD incidence (ascending)" — NOT "Safest communes". |
| Home "Highest Reported Rate" | `ItemListOrderDescending` | "...(descending)". Never "most dangerous". |
| Region ranking | `ItemListOrderDescending` | Communes in region by reported rate. |
| Crime-type ranking | `ItemListOrderDescending` | Communes by reported family rate. |
| `/rankings/` index | `Unordered` (or omit) | List of ranking-page links, not communes. `position`+`url`+`name`. |
| "Similar comunas" | `Unordered` | **MUST be Unordered** — proximity order is NOT a rank. Do not imply ascending/descending safety. |

**Crucial editorial guard:** the ItemList `name` (if present) must NEVER contain "safest"/"most dangerous"/"safe"/"dangerous". Reuse the existing sober phrasing ("reported incidence", "reported rate"). The `forbidden-language.mjs` validator already guards visible text; the new `seo.mjs` should also assert the ItemList `name`/JSON-LD strings contain no forbidden term (cheap belt-and-suspenders).

### Pattern 6: BreadcrumbList shape mirroring the visual breadcrumb (D-07)

**What:** One `BreadcrumbList` per page that has a visual breadcrumb (commune, region, crime). Mirror the exact visual hierarchy and per-locale labels, using **locale-correct hardcoded URLs**.

**Visual hierarchies found in code:**
- Commune (`commune/[slug].astro`): `Home › Communes › {Region} › {Commune}` (EN) / `Inicio › Comunas › {Región} › {Comuna}` (ES). 4 levels. Last is `aria-current` (no link → in JSON-LD, last item has `name` but `item` may be the self URL or omitted).
- Region (`region/[slug].astro`): `Home › Regions` — only 2 levels, and "Regions" is plain text (no index page). The H1 is the region. So the honest BreadcrumbList = `Home › Regions(no url?) › {Region name}`. **Note:** the visual breadcrumb here is only `Home › Regions` (Regions is a non-link span; the region itself is the H1, not in the breadcrumb). The planner must decide whether the JSON-LD breadcrumb includes the region as a trailing item to match the page, or strictly mirrors the 2-element visual crumb. Recommend: 2 elements (`Home`, then `Regions` as current) to strictly mirror the visual, OR a 3rd trailing `{Region}` item — flag as a small decision.
- Crime (`crime/[family].astro`): visual = `Home › Crime Types` (Crime Types is a plain span). Same situation as region.

**schema.org required fields (D-10):** `BreadcrumbList` → `itemListElement[]` of `ListItem` with `position`, `name`, and `item` (the URL). Google's guidance: the **last** breadcrumb item may omit `item` (it's the current page). [CITED: Google Search Central — Breadcrumb structured data]

```ts
// src/lib/jsonld.ts
export function buildBreadcrumb(
  crumbs: { name: string; url?: string }[]   // url omitted on the current/last item
) {
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

```astro
// commune/[slug].astro example (EN)
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Communes', url: 'https://ischilesafe.com/communes/' },
  { name: data.regionName, url: `https://ischilesafe.com/region/${regionSlug}/` },
  { name: data.name }, // current page — no item
]);
// ES equivalent uses /es/, /es/comunas/, /es/region/{slug}/ — hardcoded ES slugs (memory pitfall)
const jsonLd = [datasetPlace, breadcrumb, similarItemList];
```

**ES URL hardcoding (memory pitfall):** every breadcrumb `item` URL on ES pages must be `/es/...` with the ES slug segment (`/es/comunas/`, `/es/region/`, `/es/comuna/`). NEVER `getRelativeLocaleUrl`. The region/commune *slug* itself is shared across locales (slugs aren't translated, only the path prefix segment differs), but the **path segment** (`comuna` vs `commune`, `comunas` vs `communes`, `region` vs `region`) must be the locale-correct literal.

### Pattern 7: Offline sampled validator (D-09/D-10) — mirror spine.mjs

**What:** New `site/scripts/validate/seo.mjs`, structurally identical to `spine.mjs` (`let failures=0`, helper fns, per-assertion PASS/FAIL `console.log`, `process.exit(failures>0?1:0)`). Reads `dist/`, picks **one representative page per template type × both locales**, and asserts OG/Twitter meta presence + JSON-LD shape — all offline, reusing `schema.mjs`'s `extractJsonLd` regex approach but extended to extract **all** ld+json blocks (not just the first).

**Representative sample (Claude's discretion on exact URLs — pick deterministically, first dir entry like spine.mjs does):**
| Template type | EN sample | ES sample |
|---------------|-----------|-----------|
| home | `dist/index.html` | `dist/es/index.html` |
| commune | `dist/commune/<firstSlug>/index.html` | `dist/es/comuna/<firstSlug>/index.html` |
| region | `dist/region/<firstSlug>/index.html` | `dist/es/region/<firstSlug>/index.html` |
| crime | `dist/crime/<firstSlug>/index.html` | `dist/es/delito/<firstSlug>/index.html` |
| ranking | `dist/rankings/index.html` | `dist/es/rankings/index.html` |
| editorial | `dist/is-chile-safe/index.html` | `dist/es/delitos-por-comuna/index.html` |

**Assertions:**
- **OG presence (all 6 sampled types × 2 locales):** HTML contains `property="og:title"`, `og:description`, `og:type`, `og:url`, `og:image`, `og:locale`, and `name="twitter:card"` with `summary_large_image`. Cheap `content.includes(...)` checks like spine.mjs.
- **og:url locale correctness:** EN sampled page's `og:url` content contains the EN path (no `/es/`); ES page's contains `/es/`. Mirrors spine.mjs's EN/ES URL discrimination (`/rankings/` vs `/es/rankings/`).
- **og:image absolute + under /og/:** `og:image` content matches `https://ischilesafe.com/og/`.
- **JSON-LD extract-all + parse:** regex `g`-flag loop over `<script type="application/ld+json">([\s\S]*?)</script>`, `JSON.parse` each (catch → FAIL with page label). This catches escaping bugs exactly like `schema.mjs` does.
- **ItemList shape (ranking/region/crime/home):** among parsed blocks, find `@type === 'ItemList'`; assert `Array.isArray(itemListElement)`, length > 0, and every element has numeric `position` + string `url`. (D-10)
- **BreadcrumbList shape (commune/region/crime):** find `@type === 'BreadcrumbList'`; assert every element has `position` + `name` + (`item` on all but possibly the last). (D-10)
- **Editorial honesty (optional belt-and-suspenders):** assert no parsed JSON-LD string value contains a forbidden absolute term.

**Extract-all helper (extend schema.mjs's single-match version):**
```js
function extractAllJsonLd(html) {
  const re = /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  const blocks = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    try { blocks.push(JSON.parse(m[1])); }
    catch (e) { blocks.push({ _parseError: e.message, _raw: m[1] }); }
  }
  return blocks;
}
```

**Registration:** add `'seo.mjs'` to the `VALIDATORS` array in `all.mjs` (one line; it runs with `ROLLOUT_ALL=true` like the others — fine, the sampled pages exist in any rollout that includes ≥1 commune).

### Anti-Patterns to Avoid
- **@graph migration for jsonLd** — breaks all existing single-object callers; unnecessary `@id` plumbing. Use array-of-scripts.
- **Putting the rate inside ListItem** — no honest schema.org slot; risks a quantitative "safety leaderboard" reading. Keep position+url+name.
- **`getRelativeLocaleUrl` for ES og:url / breadcrumb items** — produces wrong (untranslated-prefix) paths. Hardcode `/es/...` segments.
- **Per-page OG frontmatter duplication** — violates D-01/D-02. Drive everything from existing `title`/`description`/`enPath`/`esPath` + the single `pageType` prop.
- **Naming an ItemList "safest/most dangerous communes"** — editorial-rule violation in machine-readable form. Use "reported incidence (ascending/descending)".
- **Bare `og:locale` = `en`/`es`** — not spec-compliant; must be `en_US`/`es_CL`.
- **Extracting only the first ld+json block in the validator** — pages now have 2-3 blocks; the validator must extract ALL (the existing `schema.mjs` only grabs the first, which is fine for *its* Dataset assertion but `seo.mjs` must loop).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON-LD XSS-safe injection | A new escaping scheme | The existing `JSON.stringify(x).replace(/<\//g,'<\\/')` + `set:html` + `is:inline` | Already vetted (CR-01 fix); just map it over the array. |
| HTML/JSON-LD extraction in validator | A new parser dependency (cheerio) | The regex `extractJsonLd` pattern from `schema.mjs` (extended to extract-all) | Existing validators are dependency-free regex scanners; stay consistent, ~$0. |
| og:title/description text | New OG-specific strings | Reuse the page `title` + `description` props (D-02) | DRY; inherits sober phrasing automatically. |
| Validator scaffolding (file walk, PASS/FAIL, exit code) | A fresh harness | Copy `spine.mjs` structure verbatim | Establishes the exact `failures++`/`process.exit` pattern `all.mjs` expects. |
| Breadcrumb data | Re-deriving hierarchy | The values already in each template (`data.regionName`, `regionSlug`, etc.) | The visual breadcrumb already computes these; reuse them. |

**Key insight:** This phase is a near-mechanical extension of three already-established in-repo patterns (centralized BaseLayout SEO injection, XSS-safe `set:html` JSON-LD, dist-reading ESM validators). The risk is not technical novelty — it is (a) the editorial-honesty framing of the structured data, and (b) the ES-slug locale-correctness of every absolute URL.

## Runtime State Inventory

> Greenfield-additive phase (no rename/refactor/migration). Inventory is mostly N/A, but two non-code-edit items matter:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore stores OG/JSON-LD strings; all built from existing JSON at SSG time. Verified: data is `data/cead/*` JSON, untouched. | none |
| Live service config | None — no external service holds SEO config. (Google Search Console will re-crawl post-deploy, but that's not build state.) | none |
| OS-registered state | None. | none |
| Secrets/env vars | None — OG/Twitter need no keys. (`ADSENSE_*` unrelated, unchanged.) | none |
| Build artifacts / static assets | **NEW** `site/public/og/*.png` (7 images) must exist in the repo before build, else `og:image` 404s. These are committed assets, not generated. **Verified: `site/public/og/` does NOT exist yet** — must be created. | Create 7 PNG assets (1200×630). This is an asset-authoring task, not a code task — flag for the planner (may need a human/design step or a simple generated placeholder). |

**Verified:** `site/public/` currently contains `data/`, `icon-192.png`, `icon-512.png`, `manifest.json` — **no `og/` directory**. The OG images are a genuine new deliverable with no current source.

## Common Pitfalls

### Pitfall 1: Missing OG images → broken social cards (and validator can't catch a 404)
**What goes wrong:** Referencing `/og/commune.png` when no file exists ships a valid-looking `<meta>` but a 404 image. The offline validator asserts the *meta tag* is present and absolute, but cannot fetch the image (no network).
**Why:** `public/og/` doesn't exist yet; easy to wire the meta and forget the assets.
**How to avoid:** Add a task to create the 7 PNGs (or a single default + per-type variants) BEFORE or alongside the BaseLayout edit. Optionally add a validator assertion that the referenced file exists on disk under `dist/og/` (offline, filesystem check — `existsSync(path.join(DIST_DIR,'og', file))`), which IS possible offline and catches the missing-asset case.
**Warning signs:** `dist/og/` empty after build; social preview debuggers show blank image.

### Pitfall 2: ES og:url / breadcrumb item URLs using EN path segments
**What goes wrong:** `og:url` or BreadcrumbList `item` on an ES page points to `/commune/...` or `/communes/` instead of `/es/comuna/...` / `/es/comunas/`.
**Why:** Copy-paste from EN template, or using `getRelativeLocaleUrl` which doesn't translate the slug segment.
**How to avoid:** Use the already-computed `esPath` for og:url (D-04 — BaseLayout already picks `canonicalPath = lang==='en'?enPath:esPath`, so og:url is correct for free). For breadcrumb items, hardcode the `/es/` segment literals. Validator asserts ES sampled page's og:url + breadcrumb items contain `/es/`.
**Warning signs:** Validator EN/ES URL discrimination fails; hreflang and og:url disagree.

### Pitfall 3: Validator only extracts the first JSON-LD block
**What goes wrong:** Copying `schema.mjs`'s `extractJsonLd` (single `.match`) into `seo.mjs` would only see the Dataset block and miss the ItemList/BreadcrumbList.
**Why:** Pages now emit 2-3 blocks; the old helper stops at the first.
**How to avoid:** Use the `g`-flag `while(re.exec())` extract-all version (Pattern 7).
**Warning signs:** Breadcrumb/ItemList assertions never trigger because the block "isn't found."

### Pitfall 4: Editorial og:type=article applied to the rankings index
**What goes wrong:** `/rankings/` uses `EditorialLayout`, which (if defaulted to `pageType="editorial"`) would tag it `article` and serve `editorial.png`. It's a ranking index, not an article.
**Why:** Layout default leaks to a page that should override it.
**How to avoid:** `/rankings/` (+ ES) explicitly passes `pageType="ranking"`. Confirm EditorialLayout forwards a passed `pageType` and only defaults to `editorial` when unset.
**Warning signs:** rankings page og:type=article in dist.

### Pitfall 5: OneDrive dist desync (project memory)
**What goes wrong:** Building in one process and validating in another can leave `dist/` stale/missing because the repo lives in OneDrive.
**Why:** Documented in project memory (`onedrive-build-artifacts-desync`).
**How to avoid:** Chain build + validate in one command (e.g. `npm run build && node scripts/validate/seo.mjs`, or rely on the existing `all.mjs` invocation that runs post-build in the same shell). The planner's verification task must run build and validate together.
**Warning signs:** Validator reports "dist/ not found" or asserts against an old build.

## Code Examples

### Widened jsonLd emission (BaseLayout)
```astro
<!-- Source: existing BaseLayout.astro line 73-75, generalized to array (D-08) -->
{jsonLd !== null && (Array.isArray(jsonLd) ? jsonLd : [jsonLd])
  .filter(Boolean)
  .map((block) => (
    <script is:inline type="application/ld+json"
      set:html={JSON.stringify(block).replace(/<\//g, '<\\/')} />
  ))
}
```

### Region page: three-block jsonLd array
```astro
// region/[slug].astro — append to existing frontmatter
import { buildBreadcrumb, buildItemList } from '../../lib/jsonld.ts';
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Regions' },                       // current (Regions is the visual crumb tail)
]);
const ranking = buildItemList(rankingRows, 'en', {
  name: `Communes in ${region.name} by reported CEAD incidence (descending)`,
});
const jsonLdArray = [jsonLd /* existing Dataset+Place */, breadcrumb, ranking];
// pass jsonLd={jsonLdArray} pageType="region" to BaseLayout
```

### Validator OG assertion (mirrors spine.mjs style)
```js
// seo.mjs excerpt
const OG_KEYS = ['og:title','og:description','og:type','og:url','og:image','og:locale'];
function checkOg(htmlPath, label, expectEsUrl) {
  if (!existsSync(htmlPath)) { console.error(`FAIL [OG] ${label}: file missing`); failures++; return; }
  const html = readFileSync(htmlPath, 'utf-8');
  for (const k of OG_KEYS) {
    if (!html.includes(`property="${k}"`)) { console.error(`FAIL [OG] ${label}: missing ${k}`); failures++; }
  }
  if (!html.includes('name="twitter:card" content="summary_large_image"'))
    { console.error(`FAIL [OG] ${label}: twitter card not summary_large_image`); failures++; }
  // og:url locale correctness
  const m = html.match(/property="og:url"\s+content="([^"]+)"/);
  if (m) {
    const isEs = /\/es\//.test(m[1]);
    if (expectEsUrl !== isEs) { console.error(`FAIL [OG] ${label}: og:url locale mismatch (${m[1]})`); failures++; }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `jsonLd?: object` slot | `object | object[]` array, one script per block | This phase | Multiple structured-data types per page (Breadcrumb + ItemList + Dataset). |
| No social meta | OG + Twitter `summary_large_image` site-wide | This phase | Rich SERP/social cards. |
| `schema.mjs` validates Dataset/Place/FAQ only, first block | New `seo.mjs` validates OG/Twitter + all ld+json blocks, sampled | This phase | Coverage of the new structured data + meta. |

**Deprecated/outdated:** none relevant. `name` vs `property` attribute split for OG/Twitter is stable and unchanged. og:locale `language_TERRITORY` form is the long-standing spec.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Keep the **rate OUT of ItemList structured data** (position+url+name only), despite D-06 saying "include rate where shown" — because schema.org `ListItem` has no honest rate slot and embedding it risks a forbidden "safety leaderboard" reading. | Pattern 5 | If user wants the rate in JSON-LD, planner must choose a `ListItem.item`→`Thing` wrapper carrying the value, accepting some framing risk. Flag in discuss/plan. Low technical risk; editorial/intent decision. |
| A2 | Region & crime BreadcrumbList = mirror the **2-element visual crumb** (`Home › Regions` / `Home › Crime Types`); whether to append a 3rd trailing `{Region}`/`{Family}` item is a small open choice. | Pattern 6 | Either is schema-valid. If a 3-element breadcrumb is preferred for richer SERP breadcrumbs, add the trailing current item. No correctness risk. |
| A3 | `es_CL` is the right `og:locale` territory for ES pages. | Pattern 3 | `es_CL` is well-formed `language_TERRITORY`; if a strict consumer only accepts Facebook's enumerated locales, `es_ES`/`es_LA` are fallbacks. Very low risk (og:locale is advisory). |
| A4 | 1200×630 PNG is the chosen OG image dimension/format. | Pattern 2 | Standard; only risk is asset authoring effort. |
| A5 | Editorial pages should be `og:type=article`; all others `website`. | Pattern 1/D-04 | D-04 grants discretion; mapping is conventional. Low risk. |

## Open Questions

1. **Who authors the 7 OG images?**
   - What we know: `public/og/` doesn't exist; meta will 404 without assets; per-page generation is deferred.
   - What's unclear: whether design provides them, or the phase ships simple branded placeholders.
   - Recommendation: add an explicit asset-creation task (even a templated solid-color + logo + page-type label PNG is acceptable for MVP). Add an offline validator check that `dist/og/<type>.png` exists.

2. **Rate in ItemList — confirm A1 with user.**
   - What we know: D-06 literally says include rate where the table shows an absolute rate; schema.org has no honest slot.
   - Recommendation: default to position+url+name only; surface this as a one-line confirmation in planning/discuss.

3. **Region/crime breadcrumb depth (A2).**
   - Recommendation: 2-element to strictly mirror the visual crumb (lowest risk), or add trailing current item for richer breadcrumbs — planner's call, both valid.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Astro | build | ✓ | 6.4.6 | — |
| Node | validator + build | ✓ | 22.21.1 | — |
| @astrojs/sitemap | (unchanged) | ✓ | 3.7.3 | — |
| Image tooling (to author OG PNGs) | OG assets | ? (not verified) | — | Hand-place pre-made PNGs in `public/og/`; no build-time generation needed (static files). |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** OG image *authoring* is a content task, not a toolchain dependency — any source of 1200×630 PNGs works; no library install required.

## Validation Architecture

> `workflow.nyquist_validation` not confirmed false; including. The project uses a bespoke `scripts/validate/*.mjs` dist-reading suite (NOT a unit-test framework) — the phase's validation IS the new `seo.mjs` validator.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | In-repo ESM validators (`node scripts/validate/*.mjs`); no jest/vitest. |
| Config file | none — plain Node ESM scripts |
| Quick run command | `node scripts/validate/seo.mjs` (after a build) |
| Full suite command | `node scripts/validate/all.mjs` (runs all incl. new `seo.mjs`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSEO-01 | OG/Twitter meta present + locale-correct on sampled pages | dist assertion | `node scripts/validate/seo.mjs` | ❌ Wave 0 (new `seo.mjs`) |
| RSEO-02 | ItemList shape (position+url) on ranking templates | dist assertion | `node scripts/validate/seo.mjs` | ❌ Wave 0 |
| RSEO-02 | BreadcrumbList shape (position+name+item) on breadcrumb templates | dist assertion | `node scripts/validate/seo.mjs` | ❌ Wave 0 |
| RSEO-02 | All ld+json blocks parse (no escaping bug) | dist assertion | `node scripts/validate/seo.mjs` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd site && npm run build && node scripts/validate/seo.mjs` (chained — OneDrive desync guard).
- **Per wave merge:** `cd site && npm run build && node scripts/validate/all.mjs`.
- **Phase gate:** full `all.mjs` green (11 existing + `seo.mjs` = 12 validators) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `site/scripts/validate/seo.mjs` — new validator covering RSEO-01 + RSEO-02 (mirror `spine.mjs`).
- [ ] Register `'seo.mjs'` in `site/scripts/validate/all.mjs` VALIDATORS array.
- [ ] `site/public/og/*.png` — 7 assets (or default + variants) must exist before build for og:image to resolve.
- [ ] (optional) `site/src/lib/jsonld.ts` — shared `buildItemList` / `buildBreadcrumb` helpers.

## Security Domain

> `security_enforcement` not explicitly false; included. This is a static-content/meta phase with no auth/session/data-write surface — the only relevant control is output encoding of JSON-LD.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth) |
| V3 Session Management | no | — (static site) |
| V4 Access Control | no | — (public content) |
| V5 Input Validation / Output Encoding | yes | JSON-LD: `JSON.stringify` + escape `</` to `<\/` before `set:html` (prevents `</script>` breakout). `<meta content=...>` values are auto HTML-escaped by Astro. Data is build-time CEAD JSON (no user input), so injection surface is minimal, but the existing escaping is preserved across the array map. |
| V6 Cryptography | no | — |

### Known Threat Patterns for static Astro + JSON-LD
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `</script>` breakout via JSON-LD string value | Tampering / XSS | Existing `.replace(/<\//g,'<\\/')` applied per block (preserve in the array `.map`). |
| Reflected XSS via OG meta | XSS | OG content derives from build-time data + existing title/description (no request input); Astro escapes attribute values. No new surface. |
| Open-graph URL spoofing | Spoofing | og:url is the site's own absolute canonical (`BASE_URL + canonicalPath`), not user-controlled. |

## Sources

### Primary (HIGH confidence)
- `ogp.me` (Open Graph Protocol spec) — og:locale `language_TERRITORY` format; required properties (og:title/type/image/url); og:type website vs article. [VERIFIED]
- `schema.org/ItemList`, `schema.org/ListItem` — itemListElement/ListItem properties (position/item/name/url/itemListOrder); confirmed NO native rate slot. [VERIFIED]
- In-repo code (authoritative for integration): `BaseLayout.astro`, `CommuneRankingTable.astro`, `commune/[slug].astro`, `region/[slug].astro`, `crime/[family].astro`, `rankings.astro`, `index.astro`, `is-chile-safe.astro`, `EditorialLayout.astro`, `HomeLayout.astro`, `i18n.ts`, `spine.mjs`, `schema.mjs`, `all.mjs`. [VERIFIED: Read]
- `package.json` / `node --version` — astro 6.4.6, @astrojs/sitemap 3.7.3, node 22.21.1. [VERIFIED]
- `CONTEXT.md` D-01..D-10 — authoritative locked decisions.

### Secondary (MEDIUM confidence)
- Google Search Central guidance (training knowledge, cross-checked with spec): multiple `<script type="application/ld+json">` blocks per page are supported; last breadcrumb item may omit `item`. [CITED]
- Twitter/X Cards docs: `summary_large_image` uses ~1.91:1 (1200×630). [CITED]

### Tertiary (LOW confidence)
- `es_CL` as the optimal og:locale territory (well-formed, but advisory; not independently re-verified against Facebook's enumerated locale list this session). [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; all integration files read directly.
- Architecture (BaseLayout injection, array jsonLd, validator mirror): HIGH — directly mirrors existing in-repo patterns.
- OG/Twitter spec details (og:locale form, attribute split, required props): HIGH — confirmed against ogp.me.
- ItemList honesty resolution (rate out of structured data): MEDIUM — schema.org confirms no rate slot (HIGH), but the reconciliation with D-06 is a flagged assumption (A1) needing user confirmation.
- Pitfalls: HIGH — derived from read code + project memory.

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 (stable domain; OG/schema.org specs are slow-moving; only the OG-image authoring + A1/A2 decisions are open).
