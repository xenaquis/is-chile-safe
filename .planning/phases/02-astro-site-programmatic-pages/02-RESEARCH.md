# Phase 2: Astro Site + Programmatic Pages — Research

**Researched:** 2026-06-13
**Domain:** Astro 6 SSG, bilingual programmatic SEO, static data consumption, Schema.org, PWA meta
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Prose is deterministic Astro template interpolation — no LLM prose generation in this phase.
- **D-02:** High-variation engine: 3 trend branches × rank tiers × vs-national/regional comparison × dominant crime family × comparable commune × low_population caveat × region context.
- **D-03:** Parallel hand-maintained EN/ES templates; no runtime translation.
- **D-04:** 5 canonical unique dimensions per commune: (1) rate vs national avg, (2) rate vs regional avg, (3) trend, (4) dominant crime family, (5) comparable commune.
- **D-05:** Editorial sobriety — use "incidencia reportada", "tasa por 100.000 hab.", etc. Never "zona peligrosa", "ranking definitivo", etc.
- **D-06:** Sparse-data / low_population communes fill with regional context + comparable neighbours + statistical-volatility caveat to reach 500+ words.
- **D-07:** Server-side static data viz: inline SVG sparkline (2005–present), rank, family breakdown bars, vs-national/regional callouts, comparable-commune block, map-placeholder slot (reserved for Phase 3).
- **D-08:** Comparable commune = nearest by total rate per 100k within same region (excl. low_population); fallback to nearest nationally.
- **D-09:** Prototype components ported to .astro; zero React JS on content pages.
- **D-10:** 7 crime families only (from `by_family`); 22 groups not in current data.
- **D-11:** Crime-type pages: national only, 7 families × 2 locales = 14 pages.
- **D-12:** Featured categories (homicidios, secuestros, propiedad) visually prioritized.
- **D-13:** Crime-type page content: national ranking + family trend + sober methodology intro + map-placeholder slot.
- **D-14:** Region pages: regional aggregates + ranking of region's communes.
- **D-15:** `prefixDefaultLocale: false` — EN at root, ES under `/es/`.
- **D-16:** Localized URL segments: EN `/commune/{slug}/`, `/region/{slug}/`, `/crime/{family}/`; ES `/es/comuna/{slug}/`, `/es/region/{slug}/`, `/es/delito/{family}/`.
- **D-17:** Crime-family slugs translated per locale; commune slugs shared across locales.
- **D-18:** hreflang + canonical driven by central slug-pair map from `meta/index.json`; no per-page frontmatter hreflang.
- **D-19:** Sitemap via `@astrojs/sitemap` with per-locale entries.
- **D-20:** Schema.org Dataset + Place JSON-LD on territorial pages; PWA manifest + theme color, no service worker.
- **D-21:** Port prototype visual language: teal `#0f766e`, 5-level chroma-js scale, header/footer, Nunito Sans.
- **D-22:** Detailed design tokens deferred to UI-SPEC (already delivered — use 02-UI-SPEC.md).
- **D-23:** Phase 2 is build-only — no Cloudflare deploy.
- **D-24:** Batch gate = `site/src/config/rollout.json`; `ROLLOUT_ALL=true` env flag overrides to 346.
- **D-25:** Initial batch (~12 communes): Santiago (13101), Providencia (13123), Las Condes (13114), Maipú (13119), Valparaíso (5101), Viña del Mar (5109), Concepción (8101), La Serena (4101), Antofagasta (2101), Temuco (9101), Puerto Montt (10101), Punta Arenas (12101).
- **D-26:** Non-batch communes NOT built (true 404); regions and crime-type pages always built.

### Claude's Discretion

- Astro scaffold layout under `/site/`, CSS choice (scoped CSS, no Tailwind — per UI-SPEC).
- Exact SVG sparkline rendering, exact rank-tier thresholds, exact Schema.org property set.
- How crime-family breakdown bars are computed (which year, featured-category ordering).
- How `/data/` is served at build (symlink vs CI copy).

### Deferred Ideas (OUT OF SCOPE)

- Crime-type pages crossed by region/commune.
- Enriched 7–8 dimension set.
- Live Cloudflare Pages deploy + custom domain + GSC submission (Phase 6).
- Forbidden-language build gate EDIT-05 (Phase 4).
- Interactive map, year/crime-type filters, commune popup panel (Phase 3).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAGES-01 | 346 commune pages ES+EN, 500+ words, 5+ unique data dimensions | D-01..D-06, variation engine patterns, SVG sparkline, chroma-js level computation |
| PAGES-02 | 16 region pages ES+EN with aggregates + commune ranking | regions/*.json contract confirmed, CommuneRankingTable component |
| PAGES-03 | Crime-type pages ES+EN with national ranking (7 families × 2 = 14 pages) | catalog.json confirmed 7 families; D-10/D-11 |
| PAGES-04 | Batch rollout gate: 10–20 first; rollout.json allowlist + ROLLOUT_ALL env flag | D-24/D-25; getStaticPaths filter pattern documented |
| SEO-01 | Bilingual hreflang correct and reciprocal on all pages | D-15/D-18; manual injection pattern documented below |
| SEO-02 | sitemap.xml automatic + canonical tags | @astrojs/sitemap 3.7.3 confirmed; canonical pattern |
| SEO-03 | Schema.org Dataset/Place JSON-LD on territorial pages | JSON-LD shape documented in UI-SPEC + below |
| SEO-04 | PWA meta: manifest + theme color, no service worker | manifest.json shape in UI-SPEC; no service worker confirmed |
</phase_requirements>

---

## Summary

Phase 2 is a greenfield Astro 6 SSG site (`/site/`) that consumes the complete Phase 1 `/data/cead/` JSON output and emits pre-rendered bilingual pages: 12 initial batch commune pages × 2 locales = 24, plus all 16 regions × 2 = 32, plus 7 crime-type families × 2 = 14, for 70 total initial pages. At full rollout (ROLLOUT_ALL=true): 346 × 2 + 32 + 14 = 738 pages. Every page is server-rendered HTML with zero client JS in Phase 2.

The stack is fully locked in CLAUDE.md: Astro 6.4.6 (confirmed on npm registry), @astrojs/sitemap 3.7.3, chroma-js 3.2.0. All version numbers verified against npm registry during this research session.

The two technically novel elements for this phase are (1) the bilingual localized-path routing with manual hreflang injection at scale, and (2) the combinatorial prose variation engine that prevents thin-content deindexing for 346 near-identical statistical pages. Both are solvable in pure Astro with build-time TypeScript helpers — no external libraries needed beyond the locked stack.

Data access is straightforward: Astro's `getStaticPaths()` uses Node.js `fs` to read `data/cead/meta/index.json` at build time. Because the `/site/` directory is a child of the repo root and `/data/` is at the repo root, the chosen approach (Q3 RESOLVED) is direct parent-directory traversal from `import.meta.url` via `fileURLToPath` — NO symlink. A single `DATA_ROOT` constant in `src/lib/data.ts` resolves `../../..` to repo root and descends into `data/cead/`; this works cross-platform at build time and avoids Windows symlink fragility.

**One critical data quality finding:** both `national.json` AND each `regions/{id}.json` series rate are aggregate SUMS across communes — NOT per-capita averages. The vs-national and vs-regional comparison computations must derive the average from the MEAN of non-low-population commune rates at build time (`loadNationalAverage()` / `loadRegionalAverage()` in plan 02-01).

**Primary recommendation:** Scaffold the Astro project first (Wave 0), then implement the three page types in dependency order: commune pages (most complex, validates the variation engine) → region pages → crime-type pages. Build chroma-js level computation and the comparable-commune algorithm as pure TypeScript utilities called at build time.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTML page rendering | Build (Astro SSG) | — | SEO requires pre-rendered HTML; no CSR |
| Data reading | Build-time Node.js fs | — | JSON files consumed once at getStaticPaths + per-page |
| i18n routing | Astro i18n config | Build-time URL map | `prefixDefaultLocale:false` + localized path segments via separate page files |
| hreflang injection | BaseLayout.astro (build-time) | Central slug-pair map utility | Computed from meta/index.json; no per-page frontmatter |
| Canonical injection | BaseLayout.astro (build-time) | Astro.url | Self-referential canonical computed from canonicalUrl prop |
| Sitemap | @astrojs/sitemap (build-time) | — | Integration auto-generates per-locale entries |
| Prose variation | Build-time TypeScript utility | .astro templates | Deterministic functions called inside getStaticPaths/page props |
| SVG sparkline | Astro component (build-time) | — | Inline SVG, no charting lib, zero client JS |
| Incidence level computation | Build-time utility (chroma-js) | — | chroma-js runs in Node; outputs level integer + hex |
| Comparable commune | Build-time utility | — | Pure sort over meta/index.json filtered by region |
| CSS styling | Scoped CSS per component | global.css tokens | No Tailwind per UI-SPEC; scoped style in .astro |
| Schema.org JSON-LD | BaseLayout.astro | — | Prop-driven; injected in head as script type=application/ld+json |
| PWA manifest | public/manifest.json | BaseLayout link tag | Static file; no service worker |
| Interactive map | DEFERRED Phase 3 | — | Map-placeholder slot reserves space in DOM |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| astro | 6.4.6 | SSG framework, i18n routing, page generation | CLAUDE.md locked; [VERIFIED: npm registry] |
| @astrojs/sitemap | 3.7.3 | Auto-generate sitemap.xml with i18n locale entries | CLAUDE.md locked; [VERIFIED: npm registry] |
| chroma-js | 3.2.0 | 5-level incidence color scale at build time | CLAUDE.md locked; [VERIFIED: npm registry] |

### Supporting (build-time types only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @types/chroma-js | 2.4.x | TypeScript types for chroma-js | Install alongside chroma-js |

### NOT needed in Phase 2 (reserved for Phase 3)

| Package | Why deferred |
|---------|-------------|
| @astrojs/react | React islands for Leaflet map — zero React in Phase 2 |
| react, react-dom | Peer dep of @astrojs/react; not needed yet |
| leaflet, react-leaflet | Phase 3 map only |

**Installation (inside `/site/`):**

```bash
npm create astro@latest . -- --template minimal --no-install
npm install
npm install @astrojs/sitemap chroma-js
npm install --save-dev @types/chroma-js
```

**Version verification confirmed 2026-06-13:**
- astro: 6.4.6
- @astrojs/sitemap: 3.7.3
- chroma-js: 3.2.0

---

## Package Legitimacy Audit

All packages are well-established, long-lived npm packages from official maintainers.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| astro | npm | 4+ yrs | Millions/wk | github.com/withastro/astro | [OK] | Approved |
| @astrojs/sitemap | npm | 3+ yrs | Hundreds of K/wk | github.com/withastro/astro (monorepo) | [OK] | Approved |
| chroma-js | npm | 10+ yrs | Millions/wk | github.com/gka/chroma.js | [OK] | Approved |
| @types/chroma-js | npm | 6+ yrs | Hundreds of K/wk | DefinitelyTyped | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*slopcheck CLI was not available in this Windows environment. All packages are confirmed via npm view and are long-established with multi-year track records. Versions confirmed against npm registry.*

---

## Architecture Patterns

### System Architecture Diagram

```
/data/cead/                          /data/cead/
  meta/index.json (346 communes)       comunas/{cut}.json
  meta/catalog.json (7 families)       regions/{id}.json
  national.json (sum — not avg)
        │
        │ fs.readFileSync at build time
        ▼
┌──────────────────────────────────────────────────────┐
│              Build-Time Utilities (src/lib/)          │
│                                                       │
│  data.ts         — readMetaIndex, readCommuneData    │
│  level.ts        — computeBreakpoints, computeLevel  │
│  comparable.ts   — findComparable algorithm          │
│  variation.ts    — computeVariationKey               │
│  slugPairMap.ts  — EN↔ES URL pair builder            │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│                Astro getStaticPaths()                 │
│                                                       │
│  commune/[slug].astro  filter by rollout.json        │
│  es/comuna/[slug].astro  same allowlist              │
│  region/[slug].astro   all 16 regions × 2           │
│  crime/[family].astro  7 families × 2               │
└──────────────────┬───────────────────────────────────┘
                   │ page props with pre-computed values
                   ▼
┌──────────────────────────────────────────────────────┐
│           .astro Page Templates                       │
│                                                       │
│  BaseLayout.astro                                    │
│    head: title, meta, hreflang, canonical, JSON-LD   │
│    body: PageHeader + slot + PageFooter              │
│                                                       │
│  CommunePage  RegionPage  CrimeTypePage              │
│  (sections per UI-SPEC layout order)                 │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
         /dist/ static HTML files (70 initial / 738 full)
```

### Recommended Project Structure

```
/site/
  astro.config.mjs
  package.json
  tsconfig.json
  public/
    manifest.json
    icon-192.png
    icon-512.png
  src/
    config/
      rollout.json               (allowlist of enabled CUT codes)
      i18n.ts                    (EN/ES string map + crime-family slug map)
    lib/
      data.ts                    (build-time JSON readers with import.meta.url parent traversal; loadNationalAverage / loadRegionalAverage)
      level.ts                   (chroma-js quintile computation)
      comparable.ts              (comparable-commune nearest-rate algorithm)
      variation.ts               (prose variation key builder)
      slugPairMap.ts             (hreflang EN/ES URL pair helpers)
    layouts/
      BaseLayout.astro           (head: meta, hreflang, canonical, JSON-LD, manifest)
    components/
      PageHeader.astro
      PageFooter.astro
      LevelChip.astro
      TrendChip.astro
      StatCard.astro
      Sparkline.astro            (inline SVG bar chart — zero client JS)
      FamilyBreakdownBars.astro
      ComparisonCallout.astro
      ComparableCommune.astro
      MapPlaceholderSlot.astro
      MethodologyCaveat.astro
      CommuneRankingTable.astro
    pages/
      commune/
        [slug].astro             (EN commune pages)
      region/
        [slug].astro             (EN region pages)
      crime/
        [family].astro           (EN crime-type pages)
      es/
        comuna/
          [slug].astro           (ES commune pages)
        region/
          [slug].astro           (ES region pages)
        delito/
          [family].astro         (ES crime-type pages)
    styles/
      global.css                 (CSS custom properties from UI-SPEC)
  scripts/
    validate-build.mjs           (post-build validation: page counts, hreflang, word count, JSON-LD)
```

**Note (Q3 RESOLVED):** the earlier `public/data -> ../../data/` symlink is NOT used. Build-time data access is via `fileURLToPath` parent traversal from `src/lib/data.ts` directly to repo-root `/data/cead/`. No symlink is created, committed, or relied on.

---

### Pattern 1: Astro i18n Config with Localized Path Segments

**What:** Astro i18n handles locale prefix (EN root / ES `/es/`) but does NOT translate path segment names. Localized segments (`/commune/` vs `/es/comuna/`) require separate page files per locale at different directory paths. Both page files use identical TypeScript logic; only the `locale` prop differs.

**astro.config.mjs:**

```typescript
// Source: https://docs.astro.build/en/guides/internationalization/
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://ischilesafe.com',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es'],
    routing: {
      prefixDefaultLocale: false,  // EN at root, ES at /es/
    },
  },
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', es: 'es' },
      },
    }),
  ],
});
```

---

### Pattern 2: getStaticPaths — Reading /data/ at Build Time

**What:** Read meta/index.json once, filter by rollout.json, then read each commune's detail JSON per route. Use `import.meta.url` + `fileURLToPath` for cross-platform path resolution. NO symlink (Q3 RESOLVED).

**Path resolution:** From `src/lib/data.ts`, `import.meta.url` resolves to that file's location. Parent traversal reaches the repo root where `/data/` lives; descend into `data/cead/`. Define a single `DATA_ROOT` constant there and import it everywhere.

```typescript
// In src/lib/data.ts
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

// site/src/lib/data.ts -> climb lib/ -> src/ -> site/ -> repo root, then data/cead
const DATA_ROOT = path.resolve(fileURLToPath(import.meta.url), '../../..', 'data', 'cead');

export function loadIndex() {
  return JSON.parse(readFileSync(path.join(DATA_ROOT, 'meta', 'index.json'), 'utf8'));
}
```

---

### Pattern 3: Manual hreflang + Canonical in BaseLayout

**What:** BaseLayout.astro accepts `canonicalUrl` and `alternateUrl` as absolute URL strings, injects all three hreflang tags plus self-referential canonical. Computed by slug-pair utilities before calling the layout.

```astro
---
// src/layouts/BaseLayout.astro
interface Props {
  title: string;
  description: string;
  locale: 'en' | 'es';
  canonicalUrl: string;    // absolute URL for this page's locale
  alternateUrl: string;    // absolute URL for the other locale
  jsonLd?: object;
}
const { title, description, locale, canonicalUrl, alternateUrl, jsonLd } = Astro.props;
const enUrl = locale === 'en' ? canonicalUrl : alternateUrl;
const esUrl = locale === 'es' ? canonicalUrl : alternateUrl;
---
<html lang={locale}>
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <meta name="description" content={description} />
  <meta name="theme-color" content="#0f766e" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="canonical" href={canonicalUrl} />
  <link rel="alternate" hreflang="en" href={enUrl} />
  <link rel="alternate" hreflang="es" href={esUrl} />
  <link rel="alternate" hreflang="x-default" href={enUrl} />
  {jsonLd && <script type="application/ld+json" set:html={JSON.stringify(jsonLd)} />}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap" rel="stylesheet" />
</head>
<body><slot /></body>
</html>
```

**slug-pair utilities:**

```typescript
// src/lib/slugPairMap.ts
const BASE = 'https://ischilesafe.com';

export const communeUrls = (slug: string, locale: 'en' | 'es') => ({
  canonicalUrl: locale === 'en' ? `${BASE}/commune/${slug}/` : `${BASE}/es/comuna/${slug}/`,
  alternateUrl: locale === 'en' ? `${BASE}/es/comuna/${slug}/` : `${BASE}/commune/${slug}/`,
});

export const regionUrls = (slug: string, locale: 'en' | 'es') => ({
  canonicalUrl: locale === 'en' ? `${BASE}/region/${slug}/` : `${BASE}/es/region/${slug}/`,
  alternateUrl: locale === 'en' ? `${BASE}/es/region/${slug}/` : `${BASE}/region/${slug}/`,
});

// Crime-family slugs per locale (D-17) — see i18n.ts for full mapping
export const crimeTypeUrls = (familyKey: string, locale: 'en' | 'es', enSlug: string, esSlug: string) => ({
  canonicalUrl: locale === 'en' ? `${BASE}/crime/${enSlug}/` : `${BASE}/es/delito/${esSlug}/`,
  alternateUrl: locale === 'en' ? `${BASE}/es/delito/${esSlug}/` : `${BASE}/crime/${enSlug}/`,
});
```

---

### Pattern 4: chroma-js Level Computation at Build Time

**What:** Compute quintile breakpoints from all non-low-population commune rates for the latest complete year, then derive each commune's 1–5 level. Runs once during `getStaticPaths()`.

```typescript
// src/lib/level.ts
import chroma from 'chroma-js';

// UI-SPEC palette: low → high incidence
export const SCALE_COLORS = ['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'];

export function computeBreakpoints(rates: number[]): [number, number, number, number] {
  const sorted = [...rates].sort((a, b) => a - b);
  const q = (p: number) => sorted[Math.floor(sorted.length * p)];
  return [q(0.2), q(0.4), q(0.6), q(0.8)];
}

export function computeLevel(rate: number, bp: [number, number, number, number]): 1 | 2 | 3 | 4 | 5 {
  if (rate <= bp[0]) return 1;
  if (rate <= bp[1]) return 2;
  if (rate <= bp[2]) return 3;
  if (rate <= bp[3]) return 4;
  return 5;
}

export function levelColor(level: 1 | 2 | 3 | 4 | 5): string {
  return SCALE_COLORS[level - 1];
}
```

**When to compute breakpoints:** In a shared helper called once per `getStaticPaths()` invocation, not inside each per-page mapping. Pass `breakpoints` as part of the `params/props` payload or compute it in a module-level constant within the page file (Astro runs `getStaticPaths()` once at build time, not once per page).

---

### Pattern 5: SVG Sparkline (Inline, Build-Time)

**What:** Inline SVG bar chart of total rate per 100k by year. Rendered entirely in a `.astro` component — zero client JS.

```astro
---
// src/components/Sparkline.astro
interface Props {
  series: { year: number; rate_per_100k: number; partial: boolean }[];
  activeYear?: number;
}
const { series, activeYear } = Astro.props;
const W = 480, H = 44, GAP = 2;
const barW = Math.floor((W - GAP * (series.length - 1)) / series.length);
const maxRate = Math.max(...series.map(s => s.rate_per_100k));
---
<svg width="100%" viewBox={`0 0 ${W} ${H}`} aria-hidden="true" class="sparkline">
  {series.map((s, i) => {
    const x = i * (barW + GAP);
    const bH = Math.max(2, Math.round((s.rate_per_100k / maxRate) * H));
    return (
      <rect
        x={x} y={H - bH} width={barW} height={bH}
        fill={s.year === activeYear ? 'var(--primary)' : 'var(--line)'}
        opacity={s.partial ? 0.5 : 1}
        rx="1"
      />
    );
  })}
</svg>
```

---

### Pattern 6: Rollout Gate

**What:** `rollout.json` is a plain JSON array of CUT codes. `getStaticPaths()` filters by this array unless `ROLLOUT_ALL=true`.

```json
// site/src/config/rollout.json — D-25 initial batch
["13101","13123","13114","13119","5101","5109","8101","4101","2101","9101","10101","12101"]
```

Regions and crime-type pages do NOT check rollout.json — they always build all entries (D-26).

---

### Pattern 7: Comparable Commune Algorithm

```typescript
// src/lib/comparable.ts
export function findComparable(
  targetCut: string,
  targetRate: number,
  targetRegionId: string,
  metaIndex: CommuneMeta[],
  rateMap: Record<string, number>  // cut → latest complete year rate_per_100k
): CommuneMeta {
  const pool = metaIndex.filter(c => !c.low_population && c.cut !== targetCut);
  const regional = pool.filter(c => c.region_id === targetRegionId);
  const candidates = regional.length >= 2 ? regional : pool;  // D-08 fallback
  return candidates.reduce((best, c) => {
    const d = Math.abs((rateMap[c.cut] ?? 0) - targetRate);
    return d < Math.abs((rateMap[best.cut] ?? 0) - targetRate) ? c : best;
  });
}
```

**rateMap construction:** Read all enabled commune JSONs during `getStaticPaths()`, extract `series.find(s => !s.partial && s.year === latestYear).rate_per_100k`. This requires loading all non-low-population communes to build the map, even for the 12-commune initial batch — acceptable since the full 346 load is ~3.5MB total. The same per-commune latest-complete-year rates feed `loadNationalAverage()` / `loadRegionalAverage()` (the mean-based comparison helpers — see Pitfall 1).

---

### Pattern 8: Schema.org JSON-LD

Commune and region pages emit Dataset + Place; crime-type pages emit Dataset only. Passed as `jsonLd` prop to BaseLayout and injected in head.

```typescript
// In commune page
const jsonLd = {
  "@context": "https://schema.org",
  "@type": ["Dataset", "Place"],
  "name": `${meta.name} — Reported Crime Incidence`,
  "description": `Annual reported crime incidence rates per 100,000 inhabitants for ${meta.name}, sourced from CEAD, Chile.`,
  "url": canonicalUrl,
  "spatialCoverage": {
    "@type": "Place",
    "name": meta.name,
    "containedInPlace": { "@type": "AdministrativeArea", "name": regionName }
  },
  "temporalCoverage": `2005/${latestYear}`,
  "measurementTechnique": "Rate per 100,000 inhabitants, official CEAD police statistics",
  "creator": { "@type": "Organization", "name": "CEAD — Centro de Estudios y Análisis del Delito" }
};
```

**XSS note:** `set:html={JSON.stringify(jsonLd)}` is safe here because `jsonLd` is a typed object constructed from data fields, not raw user input. Ensure none of the data fields contain `</script>` — unlikely in CEAD municipality names but worth noting.

---

### Pattern 9: Prose Variation Engine

**What:** A TypeScript function builds a `VariationKey` object from commune data. Templates use this key to select branch-specific sentence strings.

**VariationKey shape:**

```typescript
interface VariationKey {
  trend: 'up' | 'down' | 'stable';
  vsNationalBucket: 'significantly_above' | 'above' | 'near' | 'below' | 'significantly_below';
  vsRegionalSign: 'above' | 'near' | 'below';
  dominantFamily: 'vida' | 'robos_violentos' | 'vif' | 'drogas' | 'armas' | 'propiedad' | 'incivilidades';
  comparableCommune: CommuneMeta;  // pre-computed
  isLowPopulation: boolean;
}
```

**Note:** `vsNationalBucket` and `vsRegionalSign` are derived from the commune rate vs the per-capita MEANS (`loadNationalAverage()` / `loadRegionalAverage()`), NOT vs the national.json / region.json SUM (Pitfall 1).

**Prose block structure (per UI-SPEC D-07, targeting 500+ words):**

1. Introduction sentence with commune name + latest year rate (30–50 words)
2. Trend sentence — branch on `trend` (40–60 words)
3. vs-national sentence — branch on `vsNationalBucket` (40–60 words)
4. vs-regional sentence — branch on `vsRegionalSign` (30–50 words)
5. Dominant crime family sentence — branch on `dominantFamily` (50–80 words)
6. Comparable commune sentence — always unique per page (50–80 words)
7. Region context sentence (40–60 words)
8. Low-population caveat paragraph (if `isLowPopulation`) (50–80 words)
9. Historical context sentence (2005 vs latest year delta) (40–60 words)
10. Methodology/attribution paragraph (60–80 words)

**Total target:** 430–620 words minimum with 8–10 paragraphs. Each paragraph includes at least one data figure (`<strong>`-wrapped per UI-SPEC).

---

### Anti-Patterns to Avoid

- **`client:*` directives on any component:** Zero React in Phase 2. No `client:load`, `client:visible`, `client:only`. All components are `.astro`.
- **`prefixDefaultLocale: true`:** CLAUDE.md locked; forces `/en/` prefix, hurts SEO for English audience.
- **`<GeoJSON>` react-leaflet component:** CLAUDE.md forbidden; deferred to Phase 3 anyway.
- **Using `national.json.series[].rate_per_100k` (or `regions/{id}.json` series rate) as an average:** Both are a SUM of commune rates, not a per-capita average. See Pitfall 1.
- **Relying on a `public/data` symlink:** Q3 RESOLVED — use `fileURLToPath` parent traversal in `src/lib/data.ts`; no symlink.
- **Loading all 346 commune JSONs into a single array in memory:** Load only the enabled (rollout-filtered) communes for page generation. Load all non-low-pop communes only for the comparable-commune rateMap + national/regional average computation.
- **Hardcoding crime-family URL slugs in multiple places:** Define once in `i18n.ts`, reference everywhere. These become permanent indexed URLs.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sitemap generation | Manual XML builder | `@astrojs/sitemap` integration | Auto-picks up all i18n routes; handles alternates; 700+ page sitemaps are error-prone to hand-build |
| Color interpolation for 5-level scale | CSS gradient hack | `chroma-js` (build-time, Node only) | Perceptually uniform; matches existing prototype palette exactly |
| i18n locale routing prefix | Custom middleware | Astro built-in i18n `prefixDefaultLocale: false` | Native, zero config |

---

## Data Contract Verification

Verified by reading actual Phase 1 JSON output during this research session:

**`data/cead/meta/index.json`** — 346 entries. Each entry: `cut` (string, no zero-pad), `name`, `slug`, `region_id`, `population`, `low_population` (bool). No region name — must be joined from region files.

**`data/cead/comunas/13101.json` (Santiago)**:
- Fields present: `id`, `name`, `slug`, `region_id`, `population`, `low_population`, `national_rank`, `regional_rank`, `trend`, `featured_rates`, `series`, `last_updated`
- `featured_rates.propiedad` has data; `featured_rates.homicidios` and `featured_rates.secuestros` are empty `{}`
- `series` array: years 2005–2026; 2026 has `partial: true`; each entry has `rate_per_100k` + `by_family` with 7 keys

**`data/cead/meta/catalog.json`**:
- 7 family keys: vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades
- `featured_subgroups.homicidios: 101`, `featured_subgroups.secuestros: null`
- `families.vida.featured: true`, `families.propiedad.featured: true`; others false

**`data/cead/regions/13.json`** — has `id`, `name`, `slug`, `series` with `rate_per_100k` and `by_family`. Does NOT have `commune_count` or `population` fields. Region pages must derive commune count from `meta/index.json`. NOTE: `series[].rate_per_100k` is a SUM of that region's commune rates (same pipeline behaviour as national.json) — NOT a per-capita regional average (Pitfall 1).

**`data/cead/national.json`** — `rate_per_100k` values are in the millions (e.g. 1,666,425 for 2005) — confirmed to be a sum of all commune rates, not a national per-capita rate. Do not use for vs-national comparison math.

---

## Common Pitfalls

### Pitfall 1: national.json (and region.json) Rate Is a Sum, Not an Average

**What goes wrong:** Using `national.json.series[n].rate_per_100k` (or `regions/{id}.json` series rate) directly as "national/regional average" produces absurd comparisons (e.g. Santiago at ~9,870/100k would appear "99.4% below national").
**Why it happens:** The pipeline sums raw rates across all communes (nationally and per region).
**How to avoid:** Compute averages at build time as MEANS of non-low-pop commune rates: `loadNationalAverage() = mean(nonLowPopCommunes.map(c => latestCompleteYearRate(c)))` and `loadRegionalAverage(regionId) = mean(region's nonLowPop communes' latestCompleteYearRate)`. Defined in plan 02-01 `src/lib/data.ts`, consumed by commune pages (02-03). Run once, store as constants.
**Warning signs:** vs-national/vs-regional callout showing >95% below for all communes.
**Status:** RESOLVED — averages implemented as build-time means in 02-01; commune pages (02-03) call them instead of the sum.

### Pitfall 2: Astro i18n Does NOT Translate URL Segments

**What goes wrong:** Expecting Astro to auto-rename `/commune/` → `/es/comuna/` based on locale config.
**Why it happens:** Astro i18n only adds/removes locale prefixes; it cannot rename path segments.
**How to avoid:** Separate page files at `src/pages/commune/[slug].astro` and `src/pages/es/comuna/[slug].astro`. Share a TypeScript helper that both call identically; differ only in the `locale: 'en'|'es'` prop.

### Pitfall 3: import.meta.url Path Depth Miscalculation

**What goes wrong:** Path to `/data/cead/` resolves incorrectly, causing ENOENT at build time.
**Why it happens:** The number of `../` jumps depends on where the file is in the `src/` hierarchy.
**How to avoid:** Define a single `DATA_ROOT` constant in `src/lib/data.ts` using `import.meta.url` parent traversal from that file (`path.resolve(fileURLToPath(import.meta.url), '../../..', 'data', 'cead')`), then import it everywhere. One canonical path definition eliminates the per-file miscalculation risk. No symlink (Q3 RESOLVED). Plan 02-01 includes an acceptance criterion that `loadIndex()` parses 346 entries via this path.

### Pitfall 4: @astrojs/sitemap Excludes Pages with No Internal Links

**What goes wrong:** `@astrojs/sitemap` generates entries for all routes that Astro generates. If `getStaticPaths()` returns 0 routes (empty or missing rollout.json), commune pages are absent from sitemap.
**How to avoid:** Ensure `rollout.json` exists and has the 12 D-25 CUT codes before any build. Verify after build: `grep -c '<loc>' dist/sitemap-0.xml` should equal total page count ÷ some factor.

### Pitfall 5: Low-Population Communes Generating Short Pages

**What goes wrong:** A low_population commune with sparse data produces a page with fewer than 500 words, risking thin-content deindexing.
**How to avoid:** D-06 mandates regional context paragraph + comparable commune block + low-pop caveat paragraph. The caveat paragraph alone (UI-SPEC specifies its exact text) is 40+ words. Prose template must always render all 10 prose blocks, adjusting content for low_population flag (skip rank-based sentences, add caveat, expand regional context).

### Pitfall 6: Region Pages Missing Commune Count / Population

**What goes wrong:** Trying to read `commune_count` or `population` from `regions/13.json` — these fields don't exist.
**How to avoid:** Compute `commune_count` from `metaIndex.filter(c => c.region_id === region.id).length`. Compute region `population` from `sum(metaIndex.filter(c => c.region_id === region.id).map(c => c.population))`.

### Pitfall 7: Crime-Type Page — secuestros Has No Rate Data

**What goes wrong:** `featured_rates.secuestros` is always `{}` (null subgroup ID per catalog.json). A crime-type page for "secuestros" cannot show subgroup rates at commune level.
**How to avoid:** The crime-type page for the `vida` family covers all crimes-against-persons including secuestros/homicidios. For the commune breakdown on that page, use `by_family.vida` rates — do not attempt to render `featured_rates.secuestros`. Homicidios (subgroup ID 101) is available in `featured_rates.homicidios` where non-empty.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate astro-i18next / Paraglide library | Astro built-in i18n routing | Astro v4 (2023) | One less dependency; native prefixDefaultLocale config |
| `<GeoJSON>` react-leaflet component | Native `L.geoJSON()` in useEffect | Phase 3 concern | Eliminates per-hover re-render (CLAUDE.md: forbidden) |
| Tailwind CSS | Scoped CSS + CSS custom properties | UI-SPEC decision (Phase 2) | Cleaner HTML for content scrapers; data-driven styles via CSS variables |
| `client:load` on all interactive components | `client:only="react"` on map island only | CLAUDE.md | Eliminates Leaflet JS from 346 content pages |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build runtime | ✓ | v22.21.1 | — |
| npm | Package install | ✓ | 10.9.4 | — |
| /data/cead/ (Phase 1 output) | getStaticPaths(), all pages | ✓ | Complete (346 communes, 16 regions, national, catalog) | — |
| astro (npm) | Site framework | to install | 6.4.6 on registry | — |
| @astrojs/sitemap (npm) | Sitemap | to install | 3.7.3 on registry | — |
| chroma-js (npm) | Level color computation | to install | 3.2.0 on registry | — |
| /site/ directory | All Phase 2 work | ✗ (not yet created) | — | Create in Wave 0 |

**Missing dependencies with no fallback:**
- `/site/` directory: must be bootstrapped with `npm create astro@latest` in Wave 0

**Missing dependencies with fallback:**
- none

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Astro build + Node.js post-build validation script (no unit test framework needed for pure SSG) |
| Config file | none — validation via build output inspection |
| Quick run command | `cd site && npm run build` |
| Full suite command | `cd site && npm run build && node scripts/validate-build.mjs` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAGES-01 | Initial 12 commune pages × 2 locales = 24 HTML files; each has 500+ words in `.prose-summary` | smoke: count files + word count check | `node scripts/validate-build.mjs --pages --words` | ❌ Wave 0 |
| PAGES-02 | 16 region × 2 = 32 HTML files; each has `<table` (CommuneRankingTable) | smoke: count + grep | `node scripts/validate-build.mjs --regions` | ❌ Wave 0 |
| PAGES-03 | 14 crime-type HTML files (7 families × 2); each has `<table` (NationalRankingTable) | smoke: count + grep | `node scripts/validate-build.mjs --crime-types` | ❌ Wave 0 |
| PAGES-04 | Default build produces exactly 12 commune pages × 2 = 24 (not 346×2); ROLLOUT_ALL=true produces 346×2 | smoke: count HTML in /commune/ and /es/comuna/ | `node scripts/validate-build.mjs --rollout-count 12` | ❌ Wave 0 |
| SEO-01 | Every page has hreflang en, es, x-default; each alternate URL exists in dist/ | smoke: grep + reciprocity check | `node scripts/validate-build.mjs --hreflang` | ❌ Wave 0 |
| SEO-02 | sitemap.xml exists; ≥ 70 `<loc>` entries for initial build; canonical on all pages | smoke: grep entry count + canonical check | `node scripts/validate-build.mjs --sitemap --canonical` | ❌ Wave 0 |
| SEO-03 | `<script type="application/ld+json">` with `@type` containing `Dataset` present on all commune + region pages | smoke: grep JSON-LD presence | `node scripts/validate-build.mjs --jsonld` | ❌ Wave 0 |
| SEO-04 | `<link rel="manifest">` present; `<meta name="theme-color" content="#0f766e">` present; dist/manifest.json is valid JSON | smoke: grep head elements | `node scripts/validate-build.mjs --pwa` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd site && npm run build` (full SSG build is the primary validation; ~30–60 seconds for 70-page initial build)
- **Per wave merge:** `npm run build && node scripts/validate-build.mjs` (all 8 checks)
- **Phase gate:** All 8 validations green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `/site/` — Astro project bootstrap (`npm create astro@latest`)
- [ ] `site/src/config/rollout.json` — must exist before first build
- [ ] `site/public/icon-192.png`, `site/public/icon-512.png` — PWA icons (can be placeholder 1×1 PNGs initially)
- [ ] `site/scripts/validate-build.mjs` — post-build validation covering all 8 requirements
- [ ] `src/lib/data.ts` DATA_ROOT — `fileURLToPath` parent traversal to repo-root `/data/cead/` (NO symlink — Q3 RESOLVED)

---

## Security Domain

(security_enforcement enabled; ASVS level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Static site; no auth |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | All pages publicly readable; rollout gate is build-time only |
| V5 Input Validation | Partial | Build-time: Astro auto-escapes all interpolated expressions in .astro templates — no XSS risk from commune names in data fields; only `set:html` use is for JSON-LD (typed object, not raw string) |
| V6 Cryptography | No | No secrets in this phase; DeepSeek key not used |

### Known Threat Patterns for Static SSG

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Template injection via commune name containing `<script>` in JSON | Tampering | Astro auto-escapes all `{expression}` in .astro; never use `set:html` with raw commune data fields |
| Canonical URL mismatch enabling duplicate indexing | Spoofing | Self-referential canonical in BaseLayout; sitemap entries reinforce |
| Google discovering and indexing non-rollout commune URLs | Information Disclosure | Non-batch communes simply return 404 (not built); no noindex needed per D-26 |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `import.meta.url` path traversal from `src/lib/data.ts` resolves to repo root correctly on Windows dev + Linux CI | Pattern 2, all data reading | Build fails with ENOENT; mitigated by 02-01 acceptance criterion asserting loadIndex() parses 346 entries |
| A2 | EN crime-family URL slugs (homicide, violent-robbery, domestic-violence, drug-crimes, weapons, property, disorder) are acceptable to the user as permanent indexed URLs | Pattern 3, slugPairMap | Locked in 02-01 `<family_slugs>`; URL change post-indexing requires 301 redirects |
| A3 | `national.json.rate_per_100k` (and region.json series rate) is a sum of commune rates, not a true per-capita rate | Data Contract section, Pitfall 1 | Confirmed a sum; vs-national/vs-regional now use build-time means (loadNationalAverage/loadRegionalAverage) |
| A4 | `featured_rates.secuestros` remains empty `{}` for all communes in Phase 2 | Data Contract section, Pitfall 7 | If CEAD data is re-scraped with secuestros resolved, templates must handle gracefully |
| A5 | chroma-js 3.2.0 imports cleanly in Astro 6 / Node 22 ESM context without compatibility issues | Standard Stack | Build error on import; mitigation: chroma-js is a dual CJS/ESM package with no known Astro incompatibilities [ASSUMED — not tested in this session] |

---

## Open Questions (RESOLVED)

1. **EN crime-family URL slugs (A2)** — **RESOLVED**
   - What we knew: D-17 delegates exact slug values to Claude's Discretion.
   - Resolution: Locked in plan 02-01 `<family_slugs>` — vida→homicide, robos_violentos→violent-robbery, vif→domestic-violence, drogas→drug-crimes, armas→weapons, propiedad→property, incivilidades→disorder. These are the permanent indexed EN URL slugs (ES slugs mirror the Spanish family names).

2. **national.json rate interpretation (A3)** — **RESOLVED**
   - What we knew: The value is ~1.6M for 2005, far too large for a per-capita rate.
   - Resolution: Confirmed a SUM (of all commune rates), not a per-capita average. The same holds for `regions/{id}.json` series rate. vs-national and vs-regional comparisons now use a build-time computed MEAN of non-low-pop commune rates (`loadNationalAverage()` / `loadRegionalAverage()` defined in 02-01 `src/lib/data.ts`, consumed by 02-03 commune pages). See Pitfall 1 / Blocker 1 fix.

3. **/data/ access: symlink vs CI copy** — **RESOLVED**
   - What we knew: ARCHITECTURE.md documented a symlink `public/data -> ../../data/`; Windows symlinks in git are fragile.
   - Resolution: Do NOT rely on a symlink. The data loader in 02-01 (`src/lib/data.ts`) reads `data/cead/` directly via `node:fs` + `fileURLToPath(import.meta.url)` parent-directory traversal (`path.resolve(fileURLToPath(import.meta.url), '../../..', 'data', 'cead')`). Relative parent traversal works cross-platform at build time with no symlink and no CI copy step. 02-01 includes an acceptance criterion asserting `data/cead/meta/index.json` resolves and parses 346 entries.

---

## Sources

### Primary (HIGH confidence)
- `data/cead/meta/index.json` — 346 commune list; D-25 CUT codes confirmed [VERIFIED: read in session]
- `data/cead/comunas/13101.json` — commune data contract; all fields verified [VERIFIED: read in session]
- `data/cead/meta/catalog.json` — 7 family keys; secuestros null confirmed [VERIFIED: read in session]
- `data/cead/regions/13.json` — region data shape; slug field present; series rate is a sum [VERIFIED: read in session]
- `data/cead/national.json` — rate_per_100k confirmed as large sum values [VERIFIED: read in session]
- `.planning/phases/02-astro-site-programmatic-pages/02-CONTEXT.md` — 26 locked decisions [VERIFIED: read in session]
- `.planning/phases/02-astro-site-programmatic-pages/02-UI-SPEC.md` — approved visual contract [VERIFIED: read in session]
- `.planning/research/ARCHITECTURE.md` — data flow [VERIFIED: read in session]
- `CLAUDE.md` — locked stack, i18n approach, What NOT to Use [VERIFIED: read in session]
- npm registry: astro 6.4.6, @astrojs/sitemap 3.7.3, chroma-js 3.2.0 [VERIFIED: npm view in session]

### Secondary (MEDIUM confidence)
- [Astro i18n routing docs](https://docs.astro.build/en/guides/internationalization/) — prefixDefaultLocale, locales config [CITED: docs.astro.build]
- [Astro getStaticPaths API](https://docs.astro.build/en/reference/api-reference/#getstaticpaths) [CITED: docs.astro.build]
- [chroma-js docs](https://gka.github.io/chroma.js/) — scale API [CITED: gka.github.io]
- [schema.org/Dataset](https://schema.org/Dataset), [schema.org/Place](https://schema.org/Place) [CITED: schema.org]

### Tertiary (LOW confidence)
- chroma-js ESM/Node 22 compatibility: [ASSUMED] — not tested in this session

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions confirmed via npm registry
- Architecture: HIGH — data contracts verified from actual Phase 1 output; ARCHITECTURE.md authoritative baseline
- Pitfalls: HIGH for P1/P6/P7 (verified from data inspection); MEDIUM for P2–P5 (logical analysis)
- Prose variation engine: MEDIUM — pattern is sound; exact word counts need validation test run

**Research date:** 2026-06-13
**Valid until:** 2026-09-13 (Astro SSG patterns and sitemap API are stable; data contract is locked by Phase 1)
</content>
