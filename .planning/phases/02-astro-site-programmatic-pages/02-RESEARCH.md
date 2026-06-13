# Phase 2: Astro Site + Programmatic Pages — Research

**Researched:** 2026-06-13
**Domain:** Astro 6 static site generation, bilingual i18n routing, programmatic SEO, server-rendered SVG data viz
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Deterministic Astro template prose — no LLM at build time.
- **D-02:** High-variation engine: 3 trend branches × national-rank tiers × vs-national/regional comparison × dominant/secondary crime family phrasing × named comparable commune × low-pop caveat × region-context sentence.
- **D-03:** Parallel hand-maintained ES/EN templates — zero runtime translation.
- **D-04:** 5 canonical unique dimensions per commune page: (1) rate vs national avg, (2) rate vs regional avg, (3) trend, (4) dominant crime family, (5) comparable commune.
- **D-05:** Editorial sobriety: "incidencia reportada", "tasa por 100.000 habitantes", etc. Never "zona peligrosa", "ranking definitivo", etc.
- **D-06:** Sparse-data / low_population communes: fill with regional context + comparable neighbours + statistical-volatility caveat. All 346 pages kept.
- **D-07:** Server-side static data viz: inline SVG sparkline (2005–present), national + regional rank, crime-family breakdown bars, vs-national/vs-regional callouts, comparable-commune block, map-placeholder slot.
- **D-08:** Comparable commune = nearest by total rate per 100k within same region (excluding low_population), fallback to national.
- **D-09:** Component porting to .astro — zero React JS on content pages.
- **D-10:** 7 crime families only (vida, robos_violentos, vif, drogas, armas, propiedad, incivilidades).
- **D-11:** Crime-type pages national-only in Phase 2 — 7 × 2 = 14 pages.
- **D-12:** Featured categories (vida, propiedad) visually prioritized.
- **D-13:** Crime-type pages: national ranking + map-placeholder slot.
- **D-14:** Region pages: regional aggregates + commune ranking.
- **D-15:** `prefixDefaultLocale: false` — EN at root, ES under `/es/`.
- **D-16:** Localized URL segments: commune EN `/commune/{slug}/` ES `/es/comuna/{slug}/`; region EN `/region/{slug}/` ES `/es/region/{slug}/`; crime-type EN `/crime/{family}/` ES `/es/delito/{family}/`.
- **D-17:** Crime-family slug values translated per locale (EN: property/violent-robbery/homicide/…; ES: propiedad/robos-violentos/homicidios/…). Commune slugs shared.
- **D-18:** hreflang + canonical driven by central slug-pair map from meta/index.json; base layout injects reciprocal hreflang (`en`, `es`, `x-default`) + self-referential canonical via `Astro.currentLocale`.
- **D-19:** Sitemap via `@astrojs/sitemap` with per-locale entries.
- **D-20:** Schema.org `Dataset` + `Place` JSON-LD on territorial pages; PWA meta (manifest + theme color, no service worker).
- **D-21:** Port prototype visual language: teal `#0f766e`, 5-level incidence scale via chroma-js.
- **D-22:** Detailed design tokens deferred to UI-SPEC (already produced — see 02-UI-SPEC.md).
- **D-23:** Build-only phase — no live Cloudflare deploy (that is Phase 6).
- **D-24:** Batch gate = `site/src/config/rollout.json` allowlist of CUT codes; `ROLLOUT_ALL=true` env flag overrides.
- **D-25:** Initial batch ~12 editorial-priority communes: Santiago (13101), Providencia, Las Condes, Maipú, Valparaíso, Viña del Mar, Concepción, La Serena, Antofagasta, Temuco, Puerto Montt, Punta Arenas.
- **D-26:** Non-batch communes not built (true 404). Regions and crime-type pages not batch-gated.

### Claude's Discretion

- Astro scaffold layout under `/site/`, component file organization — follow UI-SPEC + research.
- Exact SVG sparkline rendering (hand-rolled vs tiny build-time helper), exact rank-tier thresholds, exact Schema.org property set.
- How crime-family breakdown bars are computed (which year, featured-category ordering).
- How `/data/` is served at build (symlink vs CI copy) — follow `.planning/research/ARCHITECTURE.md`.

### Deferred Ideas (OUT OF SCOPE)

- Crime-type pages crossed by region/commune.
- Enriched 7–8 dimension set per commune page.
- Detailed design system / design tokens (handled by gsd:ui-phase already done).
- Live Cloudflare Pages deploy + custom domain + GSC submission (Phase 6).
- Forbidden-language build gate EDIT-05 and AdSense (Phase 4).
- Interactive map, year/crime-type filters, commune popup panel, geolocation (Phase 3).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAGES-01 | 346 commune pages ES+EN, 500+ words, 5+ unique data dimensions | D-01..D-06 template engine; data shape from 13101.json confirms all 5 dimensions available in `series`, `trend`, `national_rank`, `regional_rank`, `by_family` |
| PAGES-02 | 16 region pages ES+EN with aggregates and commune ranking | `data/cead/regions/*.json` confirmed in Phase 1; region slug from meta/index.json `region_id` field |
| PAGES-03 | Crime-type pages ES+EN with ranking and map-placeholder | 7 families from catalog.json confirmed; D-11: national-only = 14 pages |
| PAGES-04 | Batch rollout: 10–20 pages first; D-24 rollout.json config; D-25 ~12 priority communes | Build-time allowlist pattern; D-23 Phase 2 is build-only so batch gate is a build-config concern |
| SEO-01 | Reciprocal hreflang on all pages | D-18 central slug-pair map + base layout injection — verified pattern; see Pitfall 6 in prior research |
| SEO-02 | sitemap.xml + canonical tags | `@astrojs/sitemap` 3.7.3 confirmed; canonical from base layout |
| SEO-03 | Schema.org Dataset/Place JSON-LD | UI-SPEC provides exact JSON-LD shape; no library needed (inline `<script type="application/ld+json">`) |
| SEO-04 | PWA manifest + theme color, no service worker | `public/manifest.json` static file; `<meta name="theme-color">` in base layout |
</phase_requirements>

---

## Summary

Phase 2 creates a greenfield Astro 6 static site at `/site/` that reads the completed `/data/cead/` JSON from Phase 1 and emits fully pre-rendered bilingual HTML for all programmatic territorial pages. The critical technical challenge is **translated URL segments** — Astro 6's built-in i18n does not support per-locale path translation (EN `/commune/` vs ES `/es/comuna/`). The solution is a **manual parallel file-tree strategy**: two independent dynamic route files per entity type (`pages/commune/[slug].astro` and `pages/es/comuna/[slug].astro`), each with its own `getStaticPaths()`. This is more explicit than middleware routing and has zero runtime cost on a static site.

Reading `data/cead/` from outside `/site/src/` is straightforward: use `import fs from 'node:fs'` with `path.resolve()` from the build context, or configure a Vite alias `@data` → `../data/` in `astro.config.mjs`. The per-page lazy-read pattern (load index.json in `getStaticPaths`, read individual commune JSON in the page component) prevents the memory OOM that occurs when all 346 JSON files are loaded simultaneously.

The `@astrojs/sitemap` 3.7.3 integration supports a `filter()` callback that gates on the rollout allowlist at build time, ensuring only built pages enter the sitemap. chroma-js runs purely at build time for generating the 5-stop incidence color array — zero bytes shipped to the browser.

**Primary recommendation:** Use manual parallel page trees (not Astro i18n routing) for translated URL segments. Use `node:fs` + Vite alias for data access. Use `@astrojs/sitemap` with `filter()` for rollout-gated sitemap generation.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTML page generation | Astro SSG (build time) | — | All SEO-critical content must be in static HTML |
| i18n URL routing (translated segments) | File-system page tree | Astro i18n config (prefix only) | Astro i18n cannot translate path segments; file-tree handles it natively |
| Data reading (commune JSON) | Astro build / Node.js fs | Vite alias for import paths | JSON lives outside /site/src — Node.js fs with path.resolve() is the standard pattern |
| hreflang + canonical injection | BaseLayout.astro (build time) | Central slug-pair map module | One authoritative source of truth for all alternate URLs |
| Sitemap generation | @astrojs/sitemap integration | filter() callback reads rollout.json | Integration crawls actual built routes; filter prunes un-gated communes |
| Incidence color scale | chroma-js (build time, Node.js only) | — | Color array computed once and inlined as CSS custom properties — not shipped to browser |
| SVG sparkline | Astro component (.astro) | Server-side string templating | Server-rendered inline SVG — no JS, no charting library on content pages |
| Schema.org JSON-LD | BaseLayout.astro / page components | — | Inline `<script type="application/ld+json">` injected at build time |
| PWA manifest | public/manifest.json (static) | `<meta name="theme-color">` in layout | No dynamic behavior — fully static file |
| CSS theming / design tokens | global.css custom properties | Per-component scoped CSS | Matches UI-SPEC: scoped CSS, no Tailwind |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| astro | 6.4.6 | Static site framework, programmatic page generation | [VERIFIED: npm registry] Current major version; pre-renders all pages to HTML; island architecture; built-in i18n routing prefix support |
| @astrojs/react | 5.0.7 | React island integration (reserved for Phase 3 map) | [VERIFIED: npm registry] Official Astro integration; needed for `client:only="react"` directive on Phase 3 Leaflet island |
| react + react-dom | 19.2.7 | Peer dep of @astrojs/react | [VERIFIED: npm registry] Required peer dep; zero React JS ships on content pages in Phase 2 |
| @astrojs/sitemap | 3.7.3 | Auto-generate sitemap.xml | [VERIFIED: npm registry] Official integration; `filter()` option gates on rollout allowlist |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| chroma-js | 3.2.0 | 5-level incidence color scale | [VERIFIED: npm registry] Build-time only (Node.js); generates `['#dbeef0','#9fd0cd','#f4d58d','#e8a05c','#c96b5a']` array; zero browser bytes |
| topojson-client | 3.1.0 | TopoJSON → GeoJSON conversion | [VERIFIED: npm registry] Phase 3 dependency for GeoJSON compression; included now so Phase 3 doesn't require a new dep install cycle |
| @astrojs/check | (current) | TypeScript checking for .astro files | Run in CI; catches type errors in Astro components before deploy |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual parallel page trees for translated segments | Astro i18n `routing.manual` + middleware | Middleware adds runtime complexity on a static site; file-tree is explicit, zero-overhead, and correct |
| `node:fs` + Vite alias for data reading | `import.meta.glob('../../data/**')` | glob can traverse `../` but is designed for in-project files; fs.readFileSync with path.resolve is more explicit and avoids Vite bundling JSON at build |
| Inline SVG sparkline | Chart.js or similar | Any JS charting lib ships browser bytes; inline SVG is zero-cost, fully SEO-readable, server-rendered |
| chroma-js build-time only | Hard-coded hex array | chroma-js generates perceptually uniform steps correctly; hard-coded values from prototype already match — either approach valid |

**Installation (from `/site/` directory):**
```bash
npm create astro@latest . -- --template minimal --no-install
npm install astro @astrojs/react @astrojs/sitemap react react-dom chroma-js topojson-client
npm install --save-dev @astrojs/check typescript
```

---

## Package Legitimacy Audit

All packages verified on the npm registry (not PyPI — this is a Node.js phase).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| astro | npm | 5 yrs (2021-03) | ~4M/wk | github.com/withastro/astro | N/A (npm) | Approved |
| @astrojs/react | npm | ~4 yrs (2022-03) | ~2M/wk | github.com/withastro/astro (monorepo) | N/A (npm) | Approved |
| @astrojs/sitemap | npm | ~4 yrs (2022-03) | ~2M/wk | github.com/withastro/astro (monorepo) | N/A (npm) | Approved |
| chroma-js | npm | 15 yrs (2011-12) | ~5M/wk | github.com/gka/chroma.js | N/A (npm) | Approved |
| topojson-client | npm | ~10 yrs (2016-10) | ~2M/wk | github.com/topojson/topojson-client | N/A (npm) | Approved |
| react | npm | ~13 yrs | ~50M/wk | github.com/facebook/react | N/A (npm) | Approved |

**Note:** slopcheck checked PyPI (Python registry). All packages in this phase are npm packages — verified directly via `npm view` against the npm registry. All packages are official first-party or long-standing well-known packages with no suspicious postinstall scripts detected.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
data/cead/ (Phase 1 output — repo root)
├── meta/index.json          — 346 commune list: cut, name, slug, region_id, population, low_population
├── meta/catalog.json        — 7 crime families
├── comunas/{cut}.json       — per-commune series + trend + ranks + by_family
├── regions/{region_id}.json — regional aggregates + commune list
└── national.json            — national aggregates

         READ AT BUILD TIME (node:fs / Vite @data alias)
                        │
                        ▼
site/src/pages/
├── commune/[slug].astro          getStaticPaths() → EN commune pages /commune/{slug}/
├── region/[slug].astro           getStaticPaths() → EN region pages /region/{slug}/
├── crime/[family].astro          getStaticPaths() → EN crime-type pages /crime/{family}/
└── es/
    ├── comuna/[slug].astro       getStaticPaths() → ES commune pages /es/comuna/{slug}/
    ├── region/[slug].astro       getStaticPaths() → ES region pages /es/region/{slug}/
    └── delito/[family].astro     getStaticPaths() → ES crime-type pages /es/delito/{family}/

Each page:
  1. Reads commune/region JSON from node:fs
  2. Computes derived values (comparable commune, comparison deltas, family percentages)
  3. Renders BaseLayout.astro → injects hreflang + canonical + JSON-LD + PWA meta
  4. Renders page-specific Astro components (Sparkline, FamilyBreakdownBars, etc.)
  5. Emits fully pre-rendered static HTML — zero JS shipped

astro.config.mjs
├── site: 'https://ischilesafe.com'
├── i18n: { locales: ['en', 'es'], defaultLocale: 'en', routing: { prefixDefaultLocale: false } }
├── integrations: [react(), sitemap({ filter: (url) => isInRollout(url) })]
└── vite: { resolve: { alias: { '@data': path.resolve('./..', 'data') } } }

Output: dist/
├── commune/{slug}/index.html      (12 initial → 346 with ROLLOUT_ALL)
├── region/{slug}/index.html       (16 × always built)
├── crime/{family}/index.html      (7 × always built)
├── es/comuna/{slug}/index.html
├── es/region/{slug}/index.html
├── es/delito/{family}/index.html
└── sitemap.xml / sitemap-index.xml
```

### Recommended Project Structure

```
site/
  src/
    layouts/
      BaseLayout.astro       — <head> meta, hreflang, canonical, JSON-LD, manifest link, PWA theme-color
    components/
      PageHeader.astro
      PageFooter.astro
      LevelChip.astro
      TrendChip.astro
      StatCard.astro
      Sparkline.astro        — inline SVG, props: series[], latestYear
      FamilyBreakdownBars.astro
      ComparisonCallout.astro
      ComparableCommune.astro
      MapPlaceholderSlot.astro
      MethodologyCaveat.astro
      CommuneRankingTable.astro
    pages/
      commune/[slug].astro
      region/[slug].astro
      crime/[family].astro
      es/
        comuna/[slug].astro
        region/[slug].astro
        delito/[family].astro
      index.astro             — EN home placeholder (Phase 4 editorial content)
      es/index.astro          — ES home placeholder
    config/
      rollout.json            — { "enabled": ["13101","13119",...] }
      i18n.ts                 — string maps, crime-family slug translations, UI copy
    lib/
      data.ts                 — loadCommune(cut), loadRegion(id), loadIndex(), loadCatalog()
      slugMaps.ts             — buildSlugPairMap(), getFamilySlug(key, locale)
      proseEngine.ts          — deterministic variation engine (5 dimensions → prose)
      colorScale.ts           — chroma-js incidence color array (build-time)
    styles/
      global.css              — CSS custom properties from UI-SPEC, reset, Nunito Sans import
  public/
    manifest.json
    icon-192.png
    icon-512.png
  astro.config.mjs
  tsconfig.json
  package.json
```

### Pattern 1: Manual Parallel Page Trees for Translated URL Segments

**What:** Two independent dynamic route files per entity type, one per locale, in different directory paths. Each file has its own `getStaticPaths()`. No shared routing logic — the file system IS the routing.

**When to use:** Whenever Astro's i18n prefix routing is insufficient — specifically when EN and ES URL segments differ (commune vs. comuna, crime vs. delito).

**Example:**
```typescript
// site/src/pages/commune/[slug].astro
// Source: [VERIFIED: Astro docs.astro.build/en/guides/routing/]
---
import fs from 'node:fs';
import path from 'node:path';
import { getRelativeLocaleUrl } from 'astro:i18n';
import rollout from '../../config/rollout.json';
import BaseLayout from '../../layouts/BaseLayout.astro';
import { loadCommune, loadIndex } from '../../lib/data.ts';

export async function getStaticPaths() {
  const index = loadIndex();              // reads data/cead/meta/index.json
  const allowedCuts = process.env.ROLLOUT_ALL === 'true'
    ? index.map(c => c.cut)
    : rollout.enabled;
  return allowedCuts.map(cut => {
    const commune = index.find(c => c.cut === cut);
    return { params: { slug: commune.slug }, props: { cut } };
  });
}

const { cut } = Astro.props;
const data = loadCommune(cut);            // reads data/cead/comunas/{cut}.json
const esPath = `/es/comuna/${data.slug}/`;
const enPath = `/commune/${data.slug}/`;
---
<BaseLayout
  lang="en"
  title={`${data.name} Crime Data — Chile Safety Map`}
  enPath={enPath}
  esPath={esPath}
  jsonLd={buildJsonLd(data, 'en')}
>
  <!-- page content -->
</BaseLayout>
```

```typescript
// site/src/pages/es/comuna/[slug].astro — mirrors EN, different locale
// Same getStaticPaths pattern, locale="es", different labels from i18n.ts
```

**Companion: loadCommune() using node:fs**
```typescript
// site/src/lib/data.ts
// Source: [CITED: dev.solita.fi/2024/12/02/building-static-websites-with-astro.html]
import fs from 'node:fs';
import path from 'node:path';

const DATA_ROOT = path.resolve(process.cwd(), '..', 'data', 'cead');

export function loadIndex() {
  return JSON.parse(fs.readFileSync(path.join(DATA_ROOT, 'meta', 'index.json'), 'utf-8'));
}

export function loadCommune(cut: string) {
  return JSON.parse(fs.readFileSync(path.join(DATA_ROOT, 'comunas', `${cut}.json`), 'utf-8'));
}

export function loadRegion(regionId: string) {
  return JSON.parse(fs.readFileSync(path.join(DATA_ROOT, 'regions', `${regionId}.json`), 'utf-8'));
}
```

**Note on `process.cwd()`:** When Astro builds from inside `/site/`, `process.cwd()` resolves to `/site/`. Therefore `path.resolve(process.cwd(), '..', 'data', 'cead')` correctly reaches the repo-root `/data/cead/` directory. Verify this assumption at scaffold time.

### Pattern 2: Central Slug-Pair Map for hreflang

**What:** A module built once at startup (or at the top of the base layout) that maps every entity to its EN and ES URL, used to inject reciprocal hreflang on every page.

**Why:** Per-page frontmatter hreflang is error-prone at 700+ pages. A central map derived from meta/index.json is the single source of truth.

**Example:**
```typescript
// site/src/lib/slugMaps.ts
// Source: [ASSUMED] — derived from D-18 spec; pattern is standard Astro practice
import { loadIndex } from './data.ts';
import { FAMILY_SLUGS } from './i18n.ts';

export type SlugPair = { en: string; es: string };

export function buildCommoneSlugPairMap(): Record<string, SlugPair> {
  const index = loadIndex();
  return Object.fromEntries(
    index.map(c => [c.cut, {
      en: `/commune/${c.slug}/`,
      es: `/es/comuna/${c.slug}/`
    }])
  );
}

export function buildFamilySlugPairMap(): Record<string, SlugPair> {
  return Object.fromEntries(
    Object.keys(FAMILY_SLUGS).map(key => [key, {
      en: `/crime/${FAMILY_SLUGS[key].en}/`,
      es: `/es/delito/${FAMILY_SLUGS[key].es}/`
    }])
  );
}
```

**hreflang injection in BaseLayout:**
```astro
---
// BaseLayout.astro (excerpt)
// Source: [CITED: developers.google.com/search/docs/specialty/international/localization]
const { lang, enPath, esPath } = Astro.props;
const baseUrl = 'https://ischilesafe.com';
---
<head>
  <link rel="alternate" hreflang="en" href={`${baseUrl}${enPath}`} />
  <link rel="alternate" hreflang="es" href={`${baseUrl}${esPath}`} />
  <link rel="alternate" hreflang="x-default" href={`${baseUrl}${enPath}`} />
  <link rel="canonical" href={`${baseUrl}${lang === 'en' ? enPath : esPath}`} />
</head>
```

### Pattern 3: Rollout-Gated Sitemap

**What:** `@astrojs/sitemap` `filter()` callback reads `rollout.json` and only includes URLs matching enabled communes.

**Example:**
```javascript
// astro.config.mjs
// Source: [VERIFIED: docs.astro.build/en/guides/integrations-guide/sitemap/]
import sitemap from '@astrojs/sitemap';
import rollout from './src/config/rollout.json' assert { type: 'json' };

const ENABLED_SLUGS = new Set(/* map cut codes to slugs at config time */);

export default defineConfig({
  site: 'https://ischilesafe.com',
  integrations: [
    sitemap({
      filter: (url) => {
        // Regions and crime pages always included
        if (url.includes('/region/') || url.includes('/crime/') || url.includes('/delito/')) return true;
        // Communes only if in rollout
        const slug = url.split('/commune/')[1]?.split('/')[0]
                  || url.split('/comuna/')[1]?.split('/')[0];
        return slug ? ENABLED_SLUGS.has(slug) : true;
      },
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', es: 'es' }
      }
    })
  ]
});
```

**Key insight:** `@astrojs/sitemap` 3.x automatically generates `xhtml:link` hreflang alternates in the sitemap XML when `i18n` config is provided. This handles sitemap-level hreflang without manual construction. [VERIFIED: docs.astro.build/en/guides/integrations-guide/sitemap/]

### Pattern 4: Inline SVG Sparkline (Server-Rendered, No Library)

**What:** A pure Astro component that takes a series of `{year, rate_per_100k, partial}` objects and emits SVG bar chart markup at build time.

**Why no library:** Any JS charting lib ships browser bytes. Content pages ship zero JS in Phase 2.

**Example:**
```astro
---
// Sparkline.astro
// Source: [ASSUMED] — hand-rolled SVG pattern; standard for build-time Astro
interface Props {
  series: Array<{ year: number; rate_per_100k: number; partial: boolean }>;
  activeYear?: number;
  width?: number;
  height?: number;
}
const { series, activeYear, width = 480, height = 44 } = Astro.props;
const maxRate = Math.max(...series.map(s => s.rate_per_100k));
const barW = Math.floor(width / series.length) - 1;
---
<svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
  {series.map((s, i) => {
    const barH = Math.max(2, Math.round((s.rate_per_100k / maxRate) * height));
    const x = i * (barW + 1);
    const isActive = s.year === activeYear;
    const opacity = s.partial ? 0.5 : 1;
    return (
      <rect
        x={x} y={height - barH} width={barW} height={barH}
        fill={isActive ? 'var(--primary)' : 'var(--muted)'}
        opacity={opacity}
      />
    );
  })}
</svg>
```

### Pattern 5: Deterministic Prose Variation Engine

**What:** A TypeScript module that, given commune data, returns a prose string in either locale by selecting from pre-written sentence branches keyed off data tiers.

**Branch dimensions:**
1. `trend`: `'up' | 'down' | 'stable'` → 3 branches
2. `nationalRankTier`: `'top10' | 'top25' | 'mid' | 'bottom25' | 'bottom10'` → 5 branches
3. `vsNationalSign`: `'above' | 'below'` + magnitude band (>50%, 20-50%, <20%) → 6 branches
4. `vsRegionalSign`: same structure → 6 branches
5. `dominantFamily`: one of 7 keys → 7 × (primary / secondary phrasing) branches
6. `hasComparableInRegion`: bool → 2 branches
7. `lowPopulation`: bool → caveat inserted/omitted

**Practical branching:** Each commune lands on a unique combination of (trend × nationalRankTier) as the primary differentiator — 15 distinct narrative frames. With vs-national/regional magnitude and family phrasing, combinatorial uniqueness is high enough for Google's scaled-content threshold.

### Anti-Patterns to Avoid

- **Using Astro `<GeoJSON>` component:** Causes per-hover re-renders (documented pitfall from CLAUDE.md). Phase 3 should use native `L.geoJSON()` inside `useEffect`.
- **Loading all 346 commune JSON files in one `getStaticPaths` call:** Leads to heap OOM. Load index.json in getStaticPaths (small), then load per-commune JSON in the page body component.
- **Using `client:load` on map island:** Ships Leaflet JS to all 700+ content pages. Use `client:only="react"` exclusively.
- **`prefixDefaultLocale: true`:** Adds `/en/` prefix to all EN URLs, harming SEO on primary target.
- **Per-page frontmatter hreflang:** Error-prone at scale; use the central slug-pair map in BaseLayout.
- **CSS `width` as computed number without units:** The family breakdown bars use CSS `width: {pct}%` — this must be a CSS percentage string, not a raw number.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sitemap XML generation with i18n hreflang | Custom sitemap script | `@astrojs/sitemap` 3.7.3 | Integration handles `xhtml:link` hreflang alternates, i18n URL variants, filter callbacks, and sitemap index automatically |
| Color interpolation for incidence scale | Manual hex math | `chroma-js` build-time | Perceptually uniform scale; edge cases around mid-range interpolation handled correctly |
| TypeScript checking for .astro files | Custom TS checker | `@astrojs/check` | Astro components need a special checker; standard `tsc` misses frontmatter errors |
| Responsive CSS reset | Custom reset | Native CSS custom properties + mobile-first media queries | Astro ships no CSS by default; a minimal reset in `global.css` is all that's needed |

**Key insight:** For a 100% static site with no JS on content pages, nearly all complexity lives in build-time TypeScript/Node.js. The "don't hand-roll" list is short precisely because the stack avoids runtime complexity.

---

## Common Pitfalls

### Pitfall 1: `process.cwd()` Resolves Differently in Dev vs. Build

**What goes wrong:** In `astro dev`, `process.cwd()` is the directory where the `astro` binary was invoked. In Cloudflare Pages builds, the build runs from `/site/`. If data loading logic assumes a specific CWD, it silently fails in one environment.

**Why it happens:** `path.resolve(process.cwd(), '..', 'data')` assumes CWD = `/site/`. If someone runs `astro dev` from the repo root, CWD = `/` and the path resolves to `/../data` which is wrong.

**How to avoid:** In `astro.config.mjs`, compute the data root using `import.meta.url` (always resolves relative to the config file):
```javascript
import { fileURLToPath } from 'node:url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_ROOT = path.resolve(__dirname, '..', 'data', 'cead');
```
Pass `DATA_ROOT` as a Vite define constant or use the Vite alias approach. [ASSUMED — standard Node.js ESM pattern]

**Warning signs:** `ENOENT` errors on JSON reads only in one environment but not another.

### Pitfall 2: hreflang Reciprocity Breaks for Non-Rollout Communes

**What goes wrong:** The EN page for Santiago exists (in rollout) and declares `hreflang="es" href="/es/comuna/santiago/"`. If the ES version is also not built (both locales gated by rollout), Google encounters a broken hreflang reference.

**Why it happens:** Each locale page is built/skipped independently, but hreflang references the partner regardless.

**How to avoid:** Both locales of a commune must be built or not built together. The rollout gate in `getStaticPaths` must be symmetric — same `rollout.enabled` CUT list used by both `commune/[slug].astro` AND `es/comuna/[slug].astro`. Since communes share slugs across locales (D-17), the CUT-code allowlist naturally gates both. Add a build-time assertion verifying parity.

**Warning signs:** Google Search Console "Alternate page with proper canonical tag" errors.

### Pitfall 3: Sitemap i18n Config Mismatch With Actual URL Structure

**What goes wrong:** `@astrojs/sitemap` is told the default locale is `en` but the actual EN commune URL is `/commune/` not `/en/commune/`. The integration assumes `prefixDefaultLocale: false` maps pages to the base URL, which is correct — but if the page file structure uses non-standard paths (e.g., `es/comarca/` instead of `es/comuna/`), hreflang in sitemap points to URLs that don't exist.

**How to avoid:** The sitemap integration's `i18n` config must exactly match `astro.config.mjs` i18n config. Validate by checking the generated `sitemap-0.xml` against actual built `dist/` file tree after first build.

### Pitfall 4: `import.meta.glob` Cannot Reach `../../data/` Reliably

**What goes wrong:** `import.meta.glob('../../data/cead/comunas/*.json')` appears to work in dev but Vite processes all matching files into the JS bundle at build time — 346 × ~15KB JSON files bundled into the JS chunk. This wastes build time and can cause OOM.

**How to avoid:** Use `node:fs` with `fs.readFileSync()` for data loading. Reserve `import.meta.glob` for in-project content (`.md`, `.mdx` files, component discovery). The `@data` Vite alias is useful for `import` statements but should only be used for small, frequently-needed files (like `meta/index.json` or `config/rollout.json`). [CITED: dev.solita.fi/2024/12/02/building-static-websites-with-astro.html]

### Pitfall 5: Crime-Family Breakdown Bar Widths Require Latest Complete Year

**What goes wrong:** Using `series[latest].by_family` where `latest` is the last array entry — which may be a partial year (2026). Partial-year family rates are artificially low, making the family breakdown misleading.

**How to avoid:** In the data loading layer, identify the last year where `partial: false`. Use `by_family` from that year for breakdown bars. The 2026 partial-year entry should only appear in the sparkline (at 50% opacity per UI-SPEC), never in family breakdown or primary rate comparisons.

**Implementation note:** From `13101.json`, 2025 is the last non-partial year. The data-loading helper `loadCommune()` should return a `latestCompleteYear` derived value.

### Pitfall 6: Comparable Commune Algorithm Fails for Small Regions

**What goes wrong:** A commune in a small region (e.g., Región de Aysén with few non-low_population communes) has no qualifying comparable within the region. The fallback to national comparable is not implemented, causing a null reference in the ComparableCommune component.

**How to avoid:** The `proseEngine.ts` / comparable-commune logic must implement: (1) filter region communes by `!low_population`, (2) exclude self, (3) if fewer than 2 qualifying remain, fall back to national. The `ComparableCommune.astro` component must accept an optional `fallbackLabel` prop for the heading copy variant (D-08 specifies exact fallback copy in UI-SPEC).

---

## Code Examples

### astro.config.mjs Scaffold
```javascript
// Source: [CITED: docs.astro.build/en/reference/configuration-reference/]
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  site: 'https://ischilesafe.com',
  i18n: {
    locales: ['en', 'es'],
    defaultLocale: 'en',
    routing: { prefixDefaultLocale: false }
  },
  integrations: [
    react(),
    sitemap({
      filter: (url) => {
        // Regions, crime-type, and home always included
        if (!url.includes('/commune/') && !url.includes('/comuna/')) return true;
        // Communes gated unless ROLLOUT_ALL
        if (process.env.ROLLOUT_ALL === 'true') return true;
        const rollout = require('./src/config/rollout.json');
        // URL contains slug; must map slug → CUT for exact matching
        // Simplest: check if any enabled commune slug appears in URL
        return rollout.enabledSlugs?.some((s: string) => url.includes(`/${s}/`)) ?? false;
      },
      i18n: { defaultLocale: 'en', locales: { en: 'en', es: 'es' } }
    })
  ],
  vite: {
    resolve: {
      alias: {
        '@data': path.resolve(__dirname, '..', 'data')
      }
    }
  }
});
```

### chroma-js Build-Time Color Scale
```javascript
// site/src/lib/colorScale.ts
// Source: [CITED: docs.astro.build/en/guides/integrations-guide/] + CLAUDE.md stack lock
// chroma-js runs ONLY at build time (Node.js). Never import in client-side components.
import chroma from 'chroma-js';

export const INCIDENCE_COLORS = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);

// Returns: ['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a']
// Used to generate CSS custom properties in global.css or BaseLayout <style>
```

### Schema.org JSON-LD for Commune Page
```javascript
// Source: [CITED: 02-UI-SPEC.md Schema.org section]
// Exact shape from UI-SPEC D-20
function buildCommuneJsonLd(data: CommuneData, locale: 'en' | 'es') {
  const siteUrl = 'https://ischilesafe.com';
  const path = locale === 'en'
    ? `/commune/${data.slug}/`
    : `/es/comuna/${data.slug}/`;
  return {
    "@context": "https://schema.org",
    "@type": ["Dataset", "Place"],
    "name": locale === 'en'
      ? `${data.name} — Reported Crime Incidence`
      : `${data.name} — Incidencia Delictiva Reportada`,
    "description": locale === 'en'
      ? `Annual reported crime incidence rates per 100,000 inhabitants for ${data.name}, sourced from CEAD.`
      : `Tasas anuales de incidencia delictiva por 100.000 habitantes en ${data.name}, fuente: CEAD.`,
    "url": `${siteUrl}${path}`,
    "spatialCoverage": {
      "@type": "Place",
      "name": data.name,
      "containedInPlace": { "@type": "AdministrativeArea", "name": data.regionName }
    },
    "temporalCoverage": `2005/${data.latestCompleteYear}`,
    "measurementTechnique": "Rate per 100,000 inhabitants, official CEAD police statistics",
    "creator": { "@type": "Organization", "name": "CEAD — Centro de Estudios y Análisis del Delito" }
  };
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Astro v5 i18n (experimental pathnames) | Astro v6 built-in i18n (stable, no pathnames support) | v5→v6 | Translated segments require manual file-tree approach — not a regression, just a design choice |
| `import.meta.glob` for data loading | `node:fs` readFileSync for large JSON outside src | Documented practice as of 2024 | Better memory control; prevents Vite from bundling data into JS |
| `@astrojs/sitemap` auto i18n detection | Explicit `i18n` config in sitemap options | v3.x | Must match astro.config.mjs i18n settings explicitly |

**Deprecated/outdated:**
- Astro v5 and below: Do NOT use — CLAUDE.md locked to v6.4.x.
- `react-leaflet <GeoJSON>` component: Do NOT use — documented re-render pitfall in CLAUDE.md and prior research.
- `client:load` on map island: Do NOT use — ships Leaflet to all content pages.

---

## File Count Math (Cloudflare 20k Limit)

| Page Type | Count (initial batch) | Count (full) |
|-----------|----------------------|--------------|
| EN commune | 12 | 346 |
| ES commune | 12 | 346 |
| EN region | 16 | 16 |
| ES region | 16 | 16 |
| EN crime-type | 7 | 7 |
| ES crime-type | 7 | 7 |
| Home/static | ~5 | ~5 |
| **Total HTML** | **75** | **743** |
| Static assets (CSS, manifest, icons, JS for React island ~1 file) | ~10 | ~10 |
| **Total files** | **~85** | **~755** |

**Well within the 20k free-tier limit.** Even with Phase 3 JS bundles (+5 files), Phase 4 editorial pages (+~25 files), and Phase 5 news JSON assets (+5 files), total remains far below 5,000 files. [VERIFIED: Cloudflare Pages free tier = 20,000 files]

**Individual file size concern:** Commune HTML pages with full 500+ word prose + SVG sparkline + Schema.org JSON-LD will be ~30–60 KB each. The 25 MiB individual file limit is not a concern.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `process.cwd()` inside Astro build = `/site/` directory, making `path.resolve(process.cwd(), '..', 'data')` correct | Pattern 1, Pitfall 1 | Data files not found at build time — mitigated by using `import.meta.url`-based path in astro.config.mjs |
| A2 | `@astrojs/sitemap` `filter()` function receives the full URL string including `/commune/{slug}/` path | Pattern 3 | Sitemap filter logic incorrect — verify by checking generated sitemap-0.xml after first build |
| A3 | Region files exist at `data/cead/regions/{region_id}.json` (Phase 1 contract) | Everywhere | Region pages would fail to build — confirm by checking data/cead/regions/ before starting |
| A4 | `rollout.json` should store enabled CUT codes (not slugs), since CUT is the canonical join key | D-24 | Slug-based filtering in sitemap filter becomes complex — keeping CUT codes + deriving slugs at build is cleaner |
| A5 | Crime-family slug translations (EN: `property`, `violent-robbery`, `homicide`...; ES: `propiedad`, `robos-violentos`, `homicidios`...) must be defined in `site/src/config/i18n.ts` — exact slug strings are not yet established | D-17 | URL structure for crime-type pages; needs to be locked before Wave 1 |

---

## Open Questions

1. **Crime-family English slugs for URLs**
   - What we know: D-17 says EN uses translated slugs but exact values are not specified
   - What's unclear: Should EN crime-type URL be `/crime/property-crimes/` or `/crime/property/` or `/crime/propiedad/`?
   - Recommendation: Define the 7 EN slugs in `site/src/config/i18n.ts` at Wave 0; use simple English nouns (property, homicide, drug-crimes, weapons, domestic-violence, disorder, violent-robbery)

2. **Region data file structure**
   - What we know: `data/cead/regions/` exists per Phase 1 architecture; region_id is in meta/index.json as a string (`"13"`, `"56"`, etc.)
   - What's unclear: Are region JSON files named `{region_id}.json` (e.g., `13.json`) or do they use padded CUT codes?
   - Recommendation: Check `data/cead/regions/` before Wave 1 starts

3. **`rollout.json` shape: CUT codes vs slugs**
   - What we know: D-24 says "allowlist of enabled commune CUT codes"
   - What's unclear: Sitemap filter receives URL strings containing slugs, not CUT codes — need a mapping
   - Recommendation: Store CUT codes in rollout.json; build a `rolloutSlugs` Set at config time by joining with index.json

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build runtime | ✓ | (from package.json engines) | — |
| npm | Package install | ✓ | (system) | — |
| data/cead/ JSON files | All getStaticPaths() calls | ✓ | Phase 1 complete | — |
| data/cead/regions/*.json | Region pages | Assumed ✓ | Phase 1 output | Verify before Wave 1 |
| data/cead/national.json | Crime-type national ranking | Assumed ✓ | Phase 1 output | Verify before Wave 1 |

**Missing dependencies with no fallback:** None detected. Phase 1 is complete.

**Missing dependencies with fallback:** Region and national files assumed present — verify before Wave 1 region/crime-type tasks begin.

---

## Validation Architecture

> `workflow.nyquist_validation: true` in config.json — this section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Node.js built-in `assert` + custom build validation scripts (no Jest/Vitest — build-only phase with no interactive components) |
| Config file | `site/scripts/validate-build.mjs` — Wave 0 creation |
| Quick run command | `node site/scripts/validate-build.mjs --quick` (check page counts + one sample page) |
| Full suite command | `node site/scripts/validate-build.mjs --full` (all assertions below) |

**Rationale for custom scripts over Jest/Vitest:** This is a static site build-only phase. The "tests" are build output assertions — file existence, HTML structure checks, hreflang reciprocity — not unit tests of functions. A 60-line Node.js script with `assert` runs faster and has zero extra dependencies.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAGES-01 | Each commune HTML page ≥ 500 words, contains 5 data dimensions | Build output assertion | `node site/scripts/validate-build.mjs --check-wordcount --check-dimensions` | ❌ Wave 0 |
| PAGES-01 | 346 commune pages exist (ROLLOUT_ALL=true build) | Build output count | `ls dist/commune/ | wc -l` → assert 346 | ❌ Wave 0 |
| PAGES-02 | 16 EN region + 16 ES region pages exist | Build output count | `ls dist/region/ | wc -l` + `ls dist/es/region/ | wc -l` | ❌ Wave 0 |
| PAGES-03 | 7 EN crime-type + 7 ES crime-type pages exist | Build output count | `ls dist/crime/ | wc -l` + `ls dist/es/delito/ | wc -l` | ❌ Wave 0 |
| PAGES-04 | Batch build (default rollout) produces exactly 12 commune pages per locale | Build output count | `ls dist/commune/ | wc -l` → assert 12 (without ROLLOUT_ALL) | ❌ Wave 0 |
| SEO-01 | Every built page has 3 hreflang tags (en, es, x-default) AND the alternate URL resolves to a real page | HTML structure + reciprocity | `node site/scripts/validate-build.mjs --check-hreflang` | ❌ Wave 0 |
| SEO-02 | sitemap.xml exists; contains exactly (12×2 + 16×2 + 7×2) = 70 URLs in batch mode | sitemap assertion | `node site/scripts/validate-build.mjs --check-sitemap` | ❌ Wave 0 |
| SEO-02 | Every page has `<link rel="canonical">` pointing to itself | HTML structure | `node site/scripts/validate-build.mjs --check-canonical` | ❌ Wave 0 |
| SEO-03 | Every commune and region page has `<script type="application/ld+json">` with `@type: ["Dataset","Place"]` | HTML structure | `node site/scripts/validate-build.mjs --check-jsonld` | ❌ Wave 0 |
| SEO-04 | `dist/manifest.json` exists; `<meta name="theme-color" content="#0f766e">` present in all pages | File existence + HTML | `node site/scripts/validate-build.mjs --check-pwa` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd site && astro check` (TypeScript type checking, ~10s)
- **Per wave merge:** `cd site && npm run build && node scripts/validate-build.mjs --quick`
- **Phase gate:** Full `ROLLOUT_ALL=true npm run build && node scripts/validate-build.mjs --full` — must pass before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `site/scripts/validate-build.mjs` — build output assertion script covering all REQ IDs above
- [ ] `site/package.json` — must include `"validate": "node scripts/validate-build.mjs --full"` script
- [ ] Framework install: `npm install astro @astrojs/react @astrojs/sitemap react react-dom chroma-js topojson-client && npm install --save-dev @astrojs/check typescript`
- [ ] `astro.config.mjs` with i18n, sitemap, react integrations, Vite alias
- [ ] `site/src/config/rollout.json` with initial 12 CUT codes

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` in config.json.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in Phase 2 — fully public static site |
| V3 Session Management | No | No sessions — static HTML only |
| V4 Access Control | No | No access-controlled routes |
| V5 Input Validation | Partial | Build-time only — JSON data from Phase 1 is trusted pipeline output. No user input in Phase 2. |
| V6 Cryptography | No | No cryptographic operations |

### Known Threat Patterns for Static Site Generation

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in data loading | Tampering | `path.resolve()` with fixed base directory; never use user input to construct file paths |
| XSS via unescaped data in templates | Tampering | Astro auto-escapes template expressions by default. Verify no `set:html` usage with unescaped JSON values |
| Sensitive data in generated HTML | Information disclosure | No API keys or personal data in commune JSON — only aggregate statistics from CEAD |
| Supply chain attack via npm packages | Tampering | All packages verified against npm registry; no suspicious postinstall scripts |

**XSS note for Phase 2:** Astro auto-escapes `{expression}` interpolations in `.astro` files. The only risk is if Schema.org JSON-LD or SVG content uses `set:html` with unescaped data. Commune names from CEAD are ASCII/Spanish — low XSS risk, but use `JSON.stringify()` for the `<script type="application/ld+json">` block to ensure valid JSON.

---

## Sources

### Primary (HIGH confidence)
- [docs.astro.build/en/guides/internationalization/](https://docs.astro.build/en/guides/internationalization/) — i18n config, prefixDefaultLocale, getRelativeLocaleUrl; confirmed Astro 6 does NOT support per-locale path translation natively
- [docs.astro.build/en/guides/integrations-guide/sitemap/](https://docs.astro.build/en/guides/integrations-guide/sitemap/) — filter(), i18n config, hreflang xhtml:link generation
- [docs.astro.build/en/reference/configuration-reference/#vite](https://docs.astro.build/en/reference/configuration-reference/#vite) — Vite resolve.alias for @data path outside /site/
- npm registry — astro@6.4.6, @astrojs/react@5.0.7, @astrojs/sitemap@3.7.3, chroma-js@3.2.0, topojson-client@3.1.0, react@19.2.7

### Secondary (MEDIUM confidence)
- [dev.solita.fi/2024/12/02/building-static-websites-with-astro.html](https://dev.solita.fi/2024/12/02/building-static-websites-with-astro.html) — node:fs pattern for reading data outside /src/, memory-efficient per-page lazy read
- [developers.cloudflare.com/pages/platform/limits](https://developers.cloudflare.com/pages/platform/limits) — 20,000 file limit confirmed (Phase 1 research)

### Tertiary (LOW confidence)
- WebSearch results on Astro 6 monorepo scaffolding — used only for `npm create astro@latest ./site` command syntax

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against npm registry
- Architecture: HIGH — based on official Astro docs + Solita build patterns article
- i18n translated segments: HIGH — confirmed absent from Astro 6; manual file-tree is the correct approach, verified against official docs
- Pitfalls: HIGH — drawn from PITFALLS.md prior research + new Phase 2-specific patterns
- Build validation strategy: MEDIUM — custom script approach is standard for build-only phases but exact implementation is new

**Research date:** 2026-06-13
**Valid until:** 2026-08-13 (Astro 6.x stable; no breaking changes expected in this timeframe)
