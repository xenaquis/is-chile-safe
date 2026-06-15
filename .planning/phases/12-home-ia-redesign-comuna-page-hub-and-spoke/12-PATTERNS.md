# Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke — Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 10 new/modified files
**Analogs found:** 9 / 10

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/src/layouts/HomeLayout.astro` | layout | request-response | `site/src/layouts/EditorialLayout.astro` | role-match (same wrap pattern, different width constraint) |
| `site/src/pages/index.astro` | page (replace) | request-response | `site/src/pages/index.astro` (existing) | exact (same file, rebuilt) |
| `site/src/pages/es/index.astro` | page (replace) | request-response | `site/src/pages/es/index.astro` (existing) | exact (same file, rebuilt) |
| `site/src/pages/rankings.astro` | page (new) | request-response | `site/src/pages/index.astro` | role-match (static editorial page, same layout pattern) |
| `site/src/pages/es/rankings.astro` | page (new) | request-response | `site/src/pages/es/index.astro` | role-match |
| `site/src/pages/commune/[slug].astro` | page (modify) | request-response | itself | exact (breadcrumb + spoke additions) |
| `site/src/pages/es/comuna/[slug].astro` | page (modify) | request-response | `site/src/pages/commune/[slug].astro` | exact (ES mirror) |
| `site/src/components/PageHeader.astro` | component (modify) | request-response | itself | exact (add 5th nav link) |
| `site/src/config/i18n.ts` | config (modify) | transform | itself | exact (add interface field + string values) |
| `site/src/components/map/MapIsland.tsx` | component (modify) | event-driven | itself | exact (3-line addition to loadData) |
| `site/scripts/validate/spine.mjs` | utility (new) | batch | `site/scripts/validate/coverage.mjs` | role-match (same Node.js mjs validator pattern) |

---

## Pattern Assignments

### `site/src/layouts/HomeLayout.astro` (layout, new)

**Analog:** `site/src/layouts/EditorialLayout.astro`

**Imports pattern** (EditorialLayout.astro lines 15–18):
```astro
import BaseLayout from './BaseLayout.astro';
import AdSlot from '../components/AdSlot.astro';
import CookieConsent from '../components/CookieConsent.astro';
```

**Props interface pattern** (EditorialLayout.astro lines 19–28):
```astro
interface Props {
  lang: 'en' | 'es';
  title: string;
  description: string;
  enPath: string;
  esPath: string;
  jsonLd?: object | null;
}
const { lang, title, description, enPath, esPath, jsonLd = null } = Astro.props;
const adsenseEnabled = import.meta.env.ADSENSE_ENABLED === 'true';
```

**Core wrap pattern** (EditorialLayout.astro lines 34–50):
```astro
<BaseLayout
  lang={lang}
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
  jsonLd={jsonLd}
>
  <div class="editorial-prose">
    <slot />
    <slot name="ad-content" />
    <AdSlot position="bottom" />
  </div>
  {adsenseEnabled && <CookieConsent locale={lang} />}
</BaseLayout>
```

**HomeLayout deviation:** Replace `<div class="editorial-prose">` (which sets `max-width: 720px`) with `<div class="home-wide">` with no max-width constraint. Retain the same `lang/title/description/enPath/esPath/jsonLd` prop pass-through to `BaseLayout` to preserve hreflang injection (BaseLayout.astro lines 55–59 depend on these).

**Critical:** `BaseLayout` already imports and renders `PageHeader` and `PageFooter` at lines 78 and 82 — HomeLayout does NOT need to add them separately.

---

### `site/src/pages/index.astro` (page, rebuild) + `site/src/pages/es/index.astro`

**Analog:** Current `site/src/pages/index.astro` (the file being replaced)

**Data loading pattern** (index.astro lines 12–19):
```astro
import { loadNationalAverage, loadIndex, loadCommune, latestCompleteYearRate } from '../lib/data.ts';

const nationalAvg = loadNationalAverage();
const index = loadIndex();
const sampleCut = index.find((c) => !c.low_population)?.cut ?? '13101';
const sampleCommune = loadCommune(sampleCut);
const referenceYear = sampleCommune.latestCompleteYear;
```

**Layout usage pattern** (index.astro lines 22–28) — replace `EditorialLayout` with `HomeLayout`:
```astro
<EditorialLayout
  lang="en"
  title="Is Chile Safe — Chile Safety Map"
  description="..."
  enPath="/"
  esPath="/es/"
>
```
Becomes:
```astro
<HomeLayout
  lang="en"
  title="Is Chile Safe — Chile Safety Map"
  description="..."
  enPath="/"
  esPath="/es/"
>
```

**"Busca tu comuna" hero form (zero JS, D-05):**
```astro
<form action="/communes/" method="get" class="search-hero-form">
  <label for="q" class="search-label">Find your commune</label>
  <input
    type="search"
    id="q"
    name="q"
    placeholder="e.g. Ñuñoa, Valparaíso…"
    autocomplete="off"
    class="search-input"
  />
  <button type="submit" class="search-btn">Search →</button>
</form>
```
ES variant uses `action="/es/comunas/"`.

**Lead ranking tables (D-03):** Prepare top-N rows sorted by rate at build time and pass to `CommuneRankingTable.astro`. Data helper pattern from commune page (index.astro lines 77–81 of `[slug].astro`):
```astro
const allRates = loadIndex()
  .filter((c) => !c.low_population)
  .map((c) => latestCompleteYearRate(loadCommune(c.cut)))
  .sort((a, b) => a - b);
// Safest: take first N; Highest: take last N
```

**Editorial prose to condense (D-02):** The 5 sections in the existing index.astro (lines 39–167) collapse into a ~2-paragraph block placed BELOW the fold (after search hero + ranking tables + map CTA + guide cards). Content source: existing lines 39–167; strip to key claims only. Single H1 must remain on the hero.

**Guide cards (D-04):** Static links to existing editorial pages only:
```astro
<!-- Copy pattern from existing home-links ul (index.astro lines 111–122) -->
<ul class="home-links">
  <li><a href="/chile-crime-map/">Chile Crime Map</a></li>
  <li><a href="/is-chile-safe/">Is Chile Safe?</a></li>
  <li><a href="/is-santiago-safe/">Is Santiago Safe?</a></li>
  <li><a href="/safest-cities-in-chile/">Safest Communes</a></li>
  <li><a href="/methodology/">Methodology</a></li>
</ul>
```

---

### `site/src/pages/rankings.astro` + `site/src/pages/es/rankings.astro` (new, static index)

**Analog:** `site/src/pages/index.astro` (same static editorial pattern)

**Layout pattern:** Use `EditorialLayout` (NOT HomeLayout) — the rankings index is a text/link page, not a wide hub.

```astro
---
import EditorialLayout from '../layouts/EditorialLayout.astro';
---
<EditorialLayout
  lang="en"
  title="Crime Rankings — Chile Safety Map"
  description="Browse commune and region crime incidence rankings by rate, by crime type, and by region."
  enPath="/rankings/"
  esPath="/es/rankings/"
>
  <h1>Crime Incidence Rankings</h1>
  <ul>
    <li><a href="/safest-cities-in-chile/">Communes with lowest reported rates</a></li>
    <li><a href="/crime/property/">Property crime national ranking</a></li>
    <!-- one <li> per existing ranking page; no new data created -->
  </ul>
</EditorialLayout>
```

ES variant (`es/rankings.astro`): `lang="es"`, `enPath="/"`, `esPath="/es/rankings/"`, all hrefs in ES locale.

**No new data pipeline needed.** Content is a curated `<ul>` linking to pages that already exist.

---

### `site/src/pages/commune/[slug].astro` (modify — breadcrumb + spokes)

**Analog:** Itself — only targeted additions.

**Breadcrumb upgrade (D-09)** — current lines 125–128:
```astro
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span aria-hidden="true"> › </span>
  <a href={`/region/${regionSlug}/`}>{data.regionName}</a>
</nav>
```
Replace with (insert "Communes" level, add terminal commune name):
```astro
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span aria-hidden="true"> › </span>
  <a href="/communes/">Communes</a>
  <span aria-hidden="true"> › </span>
  <a href={`/region/${regionSlug}/`}>{data.regionName}</a>
  <span aria-hidden="true"> › </span>
  <span aria-current="page">{data.name}</span>
</nav>
```

**Map spoke (D-08)** — replace `<MapPlaceholderSlot mountType="commune-map" locale="en" />` at line 191:
```astro
<section class="map-spoke" aria-label="View on national map">
  <h2 class="section-heading">View on Map</h2>
  <a href={`/map/?cut=${data.cut}`} class="map-spoke-cta">
    See {data.name} on the interactive Chile crime map →
  </a>
</section>
```

**Regional-rank device** — `data.regional_rank` already exists (line 153 uses it in StatCard). Add region commune count (D-07/RESEARCH Pattern 7):
```astro
---
// Add after existing data loading block
const regionCommuneCount = loadIndex().filter(
  (c) => c.region_id === data.region_id
).length;
// NOTE: Tarapacá regional_rank may be wrong (BUGFIX-999.1 — region_id provincial code collision).
---
<StatCard
  label={t.regional_rank_label}
  value={`#${data.regional_rank} of ${regionCommuneCount}`}
/>
```

**Per-crime-type ranking spoke (D-10):** `byFamily` is already loaded at line 68. Use `FAMILY_SLUGS` from i18n.ts:
```astro
---
import { FAMILY_SLUGS } from '../../config/i18n.ts';
---
<section class="crime-type-spoke">
  <h2 class="section-heading">Rankings by Crime Type</h2>
  <ul>
    {Object.entries(byFamily).map(([key]) => (
      <li>
        <a href={`/crime/${FAMILY_SLUGS[key]?.en ?? key}/`}>
          {/* family label from t or raw key */}
        </a>
      </li>
    ))}
  </ul>
</section>
```

**Similar comunas spoke (D-07):** Pass same-region communes sorted by rate proximity to `CommuneRankingTable.astro`. Needs new data helper `nearestComparables(cut, n)` in `site/src/lib/data.ts` (no analog yet — see "No Analog Found" section).

---

### `site/src/pages/es/comuna/[slug].astro` (modify)

**Analog:** `site/src/pages/commune/[slug].astro` (mirrors EN exactly; all changes are ES-localized versions of the above)

- Breadcrumb: `href="/es/comunas/"` label `Comunas`
- Map spoke: `href={``/es/mapa/?cut=${data.cut}``}`
- Crime-type links: `href={``/es/delito/${FAMILY_SLUGS[key]?.es ?? key}/``}`

---

### `site/src/components/PageHeader.astro` (modify — add Rankings nav link)

**Analog:** Itself — add one link following the established hardcoded-slug pattern.

**Current nav href pattern** (PageHeader.astro lines 24–27):
```astro
const mapHref  = locale === 'en' ? '/map/' : '/es/mapa/';
const methodHref = locale === 'en' ? '/methodology/' : '/es/metodologia/';
const communesHref = locale === 'en' ? '/communes/' : '/es/comunas/';
```

**Add Rankings** (same pattern, after communesHref):
```astro
const rankingsHref = locale === 'en' ? '/rankings/' : '/es/rankings/';
```

**Current nav links** (PageHeader.astro lines 60–63):
```astro
<a href={homeHref} class="nav-link">{t.nav_home}</a>
<a href={mapHref}  class="nav-link">{t.nav_map}</a>
<a href={communesHref} class="nav-link">{t.nav_communes}</a>
<a href={methodHref} class="nav-link">{t.nav_methodology}</a>
```

**Add after `communesHref` line:**
```astro
<a href={rankingsHref} class="nav-link">{t.nav_rankings}</a>
```

**Landmine:** NEVER use `getRelativeLocaleUrl(locale, '/rankings/')` — the comment at lines 22–23 of PageHeader.astro explicitly documents this pitfall: it does NOT translate slug text.

---

### `site/src/config/i18n.ts` (modify — add nav_rankings)

**Analog:** Itself — follow the `nav_communes` addition pattern from Phase 11.

**Interface addition** (after `nav_communes: string;` at line 107):
```typescript
nav_rankings: string;
```

**EN_STRINGS addition** (after `nav_communes: 'Communes'`):
```typescript
nav_rankings: 'Rankings',
```

**ES_STRINGS addition** (same word both locales per RESEARCH.md):
```typescript
nav_rankings: 'Rankings',
```

**Footer spine strings** — the footer spine links (map / directory / rankings / key editorial) also need i18n entries if the footer uses the `t` object. Follow the `footer_privacy` / `footer_terms` pattern from the existing interface (lines 73–76).

---

### `site/src/components/map/MapIsland.tsx` (modify — `?cut=` focus param)

**Analog:** Itself — minimal 3-line addition inside existing `loadData()`.

**Insertion point** (MapIsland.tsx lines 195–210 — inside the `if (!cancelled && mapRef.current)` block, after `mountChoroplethLayer()` call):
```typescript
// Current code (lines 195–210):
if (!cancelled && mapRef.current) {
  layerRef.current = mountChoroplethLayer(
    mapRef.current,
    geoData,
    styleMapRef,
    polyIdxRef,
    (cut) => { ... }
  );
  // ADD HERE: D-08 focus param
  const focusCut = new URLSearchParams(window.location.search).get('cut');
  if (focusCut) {
    // Small timeout to allow Leaflet to finish rendering polygons
    setTimeout(() => selectCommune(focusCut), 100);
  }
}
```

**Why here (not a separate useEffect):** `selectCommune` (lines 352–371) calls `polyIdxRef.current.get(cut)` — this Map is only populated after `mountChoroplethLayer()` completes. A separate `useEffect([mapReady])` would fire before polygons are loaded. RESEARCH Pitfall 2 documents this explicitly.

**`selectCommune` signature** (MapIsland.tsx lines 352–371):
```typescript
const selectCommune = useCallback((cut: string) => {
  const map = mapRef.current;
  setSelected((prev) => {
    if (layerRef.current) {
      highlightSelected(layerRef.current, polyIdxRef, cut, prev);
    }
    return cut;
  });
  if (!map) return;
  const ly = polyIdxRef.current.get(cut);
  if (ly && 'getBounds' in ly) {
    map.flyToBounds((ly as L.Polygon).getBounds(), { ... });
  }
}, []);
```

---

### `site/scripts/validate/spine.mjs` (new, validator)

**Analog:** `site/scripts/validate/coverage.mjs` — same Node.js ESM validator pattern.

**File header + imports pattern** (coverage.mjs lines 1–45):
```javascript
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

let failures = 0;
```

**Assertion pattern** (coverage.mjs lines 52–97 — Assertion A structure to copy):
```javascript
// ASSERTION F: /map/ and /es/mapa/ exist in dist (map-spoke targets)
const mapEnPage = path.join(DIST_DIR, 'map', 'index.html');
const mapEsPage = path.join(DIST_DIR, 'es', 'mapa', 'index.html');

if (!existsSync(mapEnPage)) {
  console.error(`FAIL [F] map-spoke: dist/map/index.html not found`);
  failures++;
} else {
  console.log(`PASS [F] map-spoke: /map/ exists in dist`);
}
```

**HTML scan pattern** (coverage.mjs lines 107–120 — `collectHtmlFiles` + regex scan):
```javascript
function collectHtmlFiles(dir) {
  if (!existsSync(dir)) return [];
  const result = [];
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) result.push(...collectHtmlFiles(full));
    else if (entry.isFile() && entry.name.endsWith('.html')) result.push(full);
  }
  return result;
}
```

**Exit pattern** (coverage.mjs final lines):
```javascript
if (failures > 0) {
  console.error(`\n${failures} assertion(s) failed.`);
  process.exit(1);
} else {
  console.log('\nAll spine assertions passed.');
  process.exit(0);
}
```

**Assertions to implement:**
- **F:** `/map/` and `/es/mapa/` exist in dist (map-spoke link targets are real pages)
- **G:** `/rankings/` and `/es/rankings/` exist in dist
- **H:** Sitemap includes `/rankings/` and `/es/rankings/` `<loc>` entries (extend coverage.mjs Assertion C pattern at lines 180–222 — same regex approach but for rankings URLs)
- **I:** Every commune page HTML contains `href="/communes/"` (EN) or `href="/es/comunas/"` (ES) — breadcrumb link present

---

## Shared Patterns

### Layout Wrap Pattern (all layouts)
**Source:** `site/src/layouts/EditorialLayout.astro` lines 34–50
**Apply to:** `HomeLayout.astro` (new)

The wrap pattern is: `<BaseLayout {props}><div class="..."><slot /></div></BaseLayout>`. Never declare `<html>`/`<head>` in a layout that wraps BaseLayout — BaseLayout owns the document.

### Hardcoded Per-Locale Slug Pattern
**Source:** `site/src/components/PageHeader.astro` lines 22–27
**Apply to:** All new nav hrefs in PageHeader, all spoke links in commune pages, form `action` in hero

```astro
// CORRECT
const rankingsHref = locale === 'en' ? '/rankings/' : '/es/rankings/';

// WRONG — never this for localized ES slugs
const rankingsHref = getRelativeLocaleUrl(locale, '/rankings/');
```

This applies to: `rankingsHref`, map spoke `href`, breadcrumb `/communes/` href, form `action`, guide card hrefs.

### Zero `client:*` on Static Pages
**Source:** CLAUDE.md + PageHeader.astro line 4 (`Zero client:* directives (D-09)`)
**Apply to:** HomeLayout, index.astro (rebuilt), rankings.astro, commune page modifications

Never add React islands to home, commune ficha, or rankings pages. The search hero is a plain HTML `<form>`. The map spoke is a plain `<a>`. Only `site/src/pages/map.astro` and `site/src/pages/es/mapa.astro` mount the MapIsland with `client:only="react"`.

### i18n String Addition Pattern
**Source:** `site/src/config/i18n.ts` lines 107–116 (Phase 11 `nav_communes` addition)
**Apply to:** `nav_rankings` addition

Add to: (1) `I18nStrings` interface, (2) `EN_STRINGS` object, (3) `ES_STRINGS` object. The string `'Rankings'` is identical in both locales.

### Editorial Tone Guard
**Source:** CLAUDE.md, `site/src/pages/index.astro` line 101
**Apply to:** All new prose in home rebuild, rankings page, commune spoke labels

Never write "safe" or "dangerous" as absolute descriptors. Always attribute rates to CEAD. The existing index.astro line 101 is the reference:
```astro
This site never assigns absolute "safe" or "dangerous" labels.
```

### BaseLayout Props (hreflang)
**Source:** `site/src/layouts/BaseLayout.astro` lines 16–33
**Apply to:** `HomeLayout.astro`, `rankings.astro`, `es/rankings.astro`

Every page MUST pass `enPath` and `esPath` to its layout so BaseLayout can inject the reciprocal `<link rel="alternate" hreflang>` tags (lines 56–59 of BaseLayout). Missing these causes hreflang breakage on the new pages.

---

## No Analog Found

| File | Role | Reason |
|------|------|--------|
| `site/src/lib/data.ts` — new `nearestComparables(cut, n)` helper | utility/transform | The existing `nearestComparable(cut)` (singular) returns one result; no plural version exists. Implement as: filter `loadIndex()` to same `region_id`, sort by `Math.abs(rate - thisRate)`, take top N, return as `RankingRow[]`. Pattern for the filter/sort logic exists in `loadIndex().filter(c => c.region_id === data.region_id)` used in the regional-rank device (RESEARCH Pattern 7). |

---

## PageFooter — Existing Component (Already in BaseLayout)

`site/src/components/PageFooter.astro` already exists (verified). It is already imported and rendered in `BaseLayout.astro` at line 82. The "common footer spine" (D-13) means **extending this existing component** to add nav links (map / directory / rankings / key editorial), NOT creating a new one.

**Current PageFooter content** (lines 26–51): wordmark + CEAD attribution + lang toggle + legal links.

**Extension pattern** (add a new `<nav>` row following the `footer-legal` nav pattern at lines 35–51):
```astro
<nav class="footer-spine page-content" aria-label="Site navigation">
  {locale === 'en' ? (
    <>
      <a href="/map/">Map</a>
      <a href="/communes/">Communes</a>
      <a href="/rankings/">Rankings</a>
      <a href="/is-chile-safe/">Is Chile Safe?</a>
    </>
  ) : (
    <>
      <a href="/es/mapa/">Mapa</a>
      <a href="/es/comunas/">Comunas</a>
      <a href="/es/rankings/">Rankings</a>
      <a href="/es/es-seguro-chile/">¿Es seguro Chile?</a>
    </>
  )}
</nav>
```

---

## Metadata

**Analog search scope:** `site/src/layouts/`, `site/src/pages/`, `site/src/components/`, `site/src/config/`, `site/scripts/validate/`
**Files read:** 12 source files
**Pattern extraction date:** 2026-06-15
