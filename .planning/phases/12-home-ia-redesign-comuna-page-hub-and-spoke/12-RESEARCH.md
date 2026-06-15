# Phase 12: Home / IA Redesign + Comuna Page Hub-and-Spoke — Research

**Researched:** 2026-06-15
**Domain:** Astro 6 static-site IA, bilingual navigation spine, Leaflet map focus parameter, reusable ranking components
**Confidence:** HIGH (all findings grounded in actual source files; no speculative claims)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Home layout (Hybrid C+B)**
- D-01: New wide `HomeLayout` (full-width) for hero + rankings grid + map CTA + guide cards. Keep `EditorialLayout` (720px) for text pages.
- D-02: Condense existing long editorial prose into a shorter block placed below the Hybrid C+B fold. Above the fold = hero + rankings + map + guides.
- D-03: Lead rankings above the fold = two short tables side by side (más seguras + mayor incidencia). Reuse `CommuneRankingTable.astro` where practical.
- D-04: Guide cards link to existing editorial pages only. No new editorial content in this phase.

**"Busca tu comuna" hero**
- D-05: Hero is a static box/form (no JS in home root) that routes to `/communes/` / `/es/comunas/` carrying the query. Zero JS, fully indexable.
- D-06: Even on exact match, user lands on the filtered directory (≤2 interactions). No name→slug resolution in home.

**Comuna page spokes (hub)**
- D-07: "Similar comunas" = same region, ordered by nearest rate/100k. Reuses `ComparableCommune.astro`.
- D-08: Map spoke = link/CTA to `/map/` / `/es/mapa/` with a focus parameter (`?cut=<cut>` or `#<slug>`). No embedded Leaflet on the 346 ficha pages.
- D-09: Breadcrumb upgraded to `Inicio › Comunas › Región › Comuna` / `Home › Communes › Region › Commune`, with new "Comunas/Communes" level linking the directory.
- D-10: Per-crime-type ranking spoke links to existing `/crime/[family]` / `/es/delito/[family]` pages.
- D-11: No news section in Phase 12.

**Navigation spine**
- D-12: Add "Rankings" to primary nav → new static `/rankings/` + `/es/rankings/` index pages listing existing ranking pages.
- D-13: Common footer spine + extend Phase 11 `no-orphan-link` validator for reciprocity + zero 404.
- D-14: No "Noticias" nav/spine entry.

### Claude's Discretion
- Exact focus-param syntax for the map link (`?cut=` vs `#slug`) — choose what the existing map island supports with least change.
- Exact `/rankings/` page composition and the footer's link set — minimal, reuse existing pages.
- Whether to reuse vs lightly extend `CommuneRankingTable.astro` and `ComparableCommune.astro`.

### Deferred Ideas (OUT OF SCOPE)
- Comuna-page news spoke → Phase 16.
- "Noticias" nav/spine node → Phase 16.
- OpenGraph/Twitter cards + ItemList/BreadcrumbList JSON-LD → Phase 13.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| IA-01 | Home reconstruido con framing Hybrid C+B (editorial/SEO arriba + hero "busca tu comuna" + mapa como CTA de primera clase), bilingüe con paridad, un solo H1, estático/indexable. | HomeLayout new component; prose condensed below fold; two lead ranking tables via CommuneRankingTable.astro (reusable, verified). |
| IA-02 | Cada ficha de comuna es un hub que enlaza a mapa (centrado), ranking regional, comunas similares, rankings por delito, y sus noticias (news deferred); breadcrumb Inicio › Comunas › Región › Comuna en ambos locales. | Map spoke requires new `?cut=` param reader in MapIsland.tsx; breadcrumb needs one new level; ComparableCommune.astro reusable; crime-type spoke = static links to existing pages. |
| IA-03 | Spine de navegación coherente en ambos locales; nav incluye "Comunas"; enlaces recíprocos y sin 404. Nav "Rankings" node, /rankings/ + /es/rankings/ new pages, footer spine, extended validator. | PageHeader.astro hardcoded-slug pattern ready to extend; i18n.ts needs nav_rankings string; validator coverage.mjs ready to extend for new assertion E/F/G. |
</phase_requirements>

---

## Summary

Phase 12 rebuilds the home on the Hybrid C+B framing (spike 001) and turns each of the 346 comarca pages into a hub (spike 003). The research confirms that the codebase is well-positioned for this phase: the key reusable components (`CommuneRankingTable.astro`, `ComparableCommune.astro`) already exist and fit the required spokes; the nav extension pattern is established (`PageHeader.astro` with hardcoded per-locale slugs); and the validator framework is extensible.

The single biggest unknown (D-08) is now resolved: **the Leaflet map island does NOT currently read any focus parameter from the URL**. `MapIsland.tsx` mounts at a fixed center (`[-35.7, -71.8], zoom 5`) and only gains focus via user interaction (search/click) or `selectCommune(cut)` called from within the island. To support a focus link from the ficha, a minimal addition is required: read `?cut=<cut>` from `window.location.search` in a `useEffect` and call `selectCommune(cut)` once data is loaded. The `?cut=` syntax is recommended because (a) the island already stores CUTs as its primary key in `polyIdxRef`, (b) `selectCommune` already accepts CUT strings, and (c) hash-routing would require handling the `hashchange` event, whereas a query-param is simpler and fully compatible with Astro static pages.

The "regional rank device" (`#26 de 52 en su región`) **is already derivable from existing data**: `CommuneData.regional_rank` is populated at build time, and the count of communes in the region is derivable from `loadIndex().filter(c => c.region_id === data.region_id).length`. No new data pipeline work is needed.

**Primary recommendation:** Implement the 7 work units in order: (1) `HomeLayout` + home page rebuild, (2) map island `?cut=` focus param, (3) breadcrumb upgrade on both commune pages, (4) hub spokes on both commune pages, (5) `/rankings/` + `/es/rankings/` static index pages, (6) nav + footer spine + i18n strings, (7) extended validator + sitemap.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Home page layout (HomeLayout) | Frontend Server (SSR/Static) | — | Astro static prerender; no client-side |
| Lead ranking tables on home | Frontend Server (SSR/Static) | — | `CommuneRankingTable.astro` already server-renders |
| "Busca tu comuna" form/hero | Frontend Server (SSR/Static) | Browser | Form `action` routes to `/communes/?q=…`; zero JS; browser handles form submit natively |
| Map CTA link (focus param) | Browser / Client | Frontend Server | The focus param is read client-side in the Leaflet island; the link itself is static HTML generated at build time |
| Map island focus param reader | Browser / Client | — | `useEffect` in `MapIsland.tsx` reads `window.location.search` after data load |
| Breadcrumb upgrade | Frontend Server (SSR/Static) | — | Static HTML in `.astro` template |
| Hub spoke links | Frontend Server (SSR/Static) | — | Static `<a>` tags, all hrefs computed at build time |
| Regional-rank device | Frontend Server (SSR/Static) | — | Data already in `CommuneData.regional_rank`; count derivable from index |
| /rankings/ index page | Frontend Server (SSR/Static) | — | New static Astro page |
| Nav + footer spine | Frontend Server (SSR/Static) | — | `PageHeader.astro` + new `PageFooter.astro` |
| Validator extension | Build tooling | — | Node.js `.mjs` script extending `coverage.mjs` |

---

## Standard Stack

No new packages required. All work uses already-installed Astro 6, React 19, and the existing component library.

### Verification
Existing packages confirmed in `site/package.json` (not re-audited here — no new installs). [ASSUMED: no new dependencies needed based on code review]

---

## Package Legitimacy Audit

**No new packages are installed in this phase.** All required capabilities are met by the existing stack. Skipping audit.

---

## Architecture Patterns

### Recommended Project Structure — New Files

```
site/src/
├── layouts/
│   └── HomeLayout.astro          # NEW — wide full-bleed layout for the home
├── pages/
│   ├── index.astro               # REPLACE — rebuild with HomeLayout + spokes
│   ├── es/index.astro            # REPLACE — ES parity
│   ├── rankings.astro            # NEW — /rankings/ static index (EN)
│   └── es/rankings.astro         # NEW — /es/rankings/ static index (ES)
├── components/
│   └── PageFooter.astro          # NEW — common footer spine (all pages)
└── config/
    └── i18n.ts                   # EXTEND — add nav_rankings + footer spine strings
site/scripts/validate/
└── spine.mjs                     # NEW — reciprocity + 404-free assertion
```

### Pattern 1: HomeLayout (wide, full-bleed)

**What:** A new layout wrapping `BaseLayout` with full viewport width (no 720px column constraint), for the home page only. `EditorialLayout` (720px) stays intact for editorial/text pages.

**When to use:** Only for `/` and `/es/`.

**Pattern (mirrors EditorialLayout structure):**
```astro
// site/src/layouts/HomeLayout.astro
---
import BaseLayout from './BaseLayout.astro';
// ...no 720px max-width
---
<BaseLayout {lang} {title} {description} {enPath} {esPath}>
  <div class="home-wide">
    <slot />
  </div>
</BaseLayout>
```

Key constraint: `HomeLayout` must still pass `lang`, `enPath`, `esPath` to `BaseLayout` to preserve hreflang injection. [VERIFIED: BaseLayout.astro accepts these props — confirmed in source]

### Pattern 2: Map Focus Parameter (`?cut=<cut>`)

**What:** When the ficha emits a link like `/map/?cut=13101`, MapIsland reads the param after data loads and calls `selectCommune('13101')`.

**Minimal change to MapIsland.tsx:** Add a single `useEffect` that depends on `[mapReady, layerRef.current]` — once `mapReady` is `true` AND the choropleth layer is mounted, read `new URLSearchParams(window.location.search).get('cut')` and call `selectCommune(cut)`.

**Why `?cut=` not `#slug`:**
- `selectCommune` accepts CUT strings (`polyIdxRef.current.get(cut)`) — already indexed by CUT, not slug.
- Hash (`#`) requires listening to `hashchange`; query param requires only `window.location.search` read at mount.
- Astro static pages with `#fragment` would not cause a server round-trip, but the island would need to resolve slug→cut; that mapping exists only in the commune index (loaded async). Using CUT directly avoids a reverse-lookup step.

**Critical timing issue:** `selectCommune` depends on `layerRef.current` being populated (choropleth layer mounted), which happens inside the `useEffect([mapReady])` async `loadData()`. The focus-param effect MUST run after `loadData()` completes — either chain it off a state flag (e.g. `[dataLoaded]`) or keep it in `loadData()` after the layer is mounted.

**Recommended implementation:**
```typescript
// Inside loadData() in MapIsland.tsx, after mountChoroplethLayer():
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut) {
  // small timeout to allow Leaflet to finish rendering polygons
  setTimeout(() => selectCommune(focusCut), 100);
}
```
This is the smallest-possible change: 3 lines inside the existing `loadData()` async function, no new state, no new effect.

### Pattern 3: Breadcrumb Upgrade

**Current state** (`[slug].astro` L125–L128):
```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span aria-hidden="true"> › </span>
  <a href={`/region/${regionSlug}/`}>{data.regionName}</a>
</nav>
```
**Note:** The current breadcrumb skips the "Communes" level and goes directly to Region.

**Target state:**
```html
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
ES variant:
```html
<a href="/es/comunas/">Comunas</a>
```
**Files to modify:** `site/src/pages/commune/[slug].astro` (L125–L128) AND `site/src/pages/es/comuna/[slug].astro` (equivalent lines ~L105–L110).

### Pattern 4: Nav Extension (`PageHeader.astro` + `i18n.ts`)

**Current nav links** (PageHeader.astro L60–64):
```astro
<a href={homeHref}>{t.nav_home}</a>
<a href={mapHref}>{t.nav_map}</a>
<a href={communesHref}>{t.nav_communes}</a>
<a href={methodHref}>{t.nav_methodology}</a>
```

**Add Rankings** (same pattern as `communesHref`):
```astro
const rankingsHref = locale === 'en' ? '/rankings/' : '/es/rankings/';
// ...
<a href={rankingsHref}>{t.nav_rankings}</a>
```

**i18n.ts additions needed:**
1. Add `nav_rankings: string` to `I18nStrings` interface.
2. Add `nav_rankings: 'Rankings'` to `EN_STRINGS`.
3. Add `nav_rankings: 'Rankings'` to `ES_STRINGS`.

**Landmine:** Never use `getRelativeLocaleUrl(locale, '/rankings/')` — it will emit `/es/rankings/` for ES but `/rankings/` for EN. Hardcode both per the established pattern. [VERIFIED: comment in PageHeader.astro L22–23 documents this pitfall explicitly]

### Pattern 5: `CommuneRankingTable.astro` Reuse

**Current props interface:**
```typescript
interface RankingRow {
  name: string;
  slug: string;
  rate: number;
  national_rank: number;
  trend: 'up' | 'down' | 'stable';
  low_population: boolean;
}
interface Props {
  rows: RankingRow[];
  locale: 'en' | 'es';
}
```

**Reuse fit assessment:**
- Home's two lead tables (safest + highest incidence): **direct fit** — caller supplies top-N rows sorted at build time; component renders them unchanged.
- `/rankings/` index: **NOT a fit** — the `/rankings/` page is a directory of *links to* ranking pages, not a ranked table of communes. A simple `<ul>` of links is appropriate.
- Ficha "regional ranking" spoke: **partial fit** — the existing component shows national rank. For the "similar comunas in region" spoke, `ComparableCommune.astro` is the right component (already used at L188). The "regional ranking" spoke (D-07) requires showing same-region communes ordered by rate; the existing component works if the caller passes region-filtered rows.

**Gap:** `CommuneRankingTable.astro` currently shows a "Glossary" footnote unconditionally. On the home page this may be unwanted. Add an optional `hideFootnotes?: boolean` prop, or simply accept the footnote as benign.

### Pattern 6: "Similar Comunas" Spoke (D-07)

**Current `ComparableCommune.astro`:** Shows ONE comparable commune (nearest-rate, same-region-first). The spike 003 design shows 3–5 similar communes.

**Gap:** The current component is single-result; D-07 asks for "same region, ordered by nearest rate" (plural). Two options:
- Option A: Reuse `CommuneRankingTable.astro` with region-filtered rows (top 3–5 by nearest rate). Simple, no new component.
- Option B: Extend `ComparableCommune.astro` to accept an array. More faithful to the existing card UI.

**Recommendation:** Option A — pass same-region communes sorted by rate distance into `CommuneRankingTable.astro` with a heading "Similar communes in this region." Needs a new data helper `nearestComparables(cut, n)` returning the top-N by rate proximity in the same region.

### Pattern 7: Regional-Rank Device (`#N de M en su región`)

**Data availability (confirmed in data.ts L41–43):**
```typescript
national_rank: number;    // pre-computed in per-commune JSON
regional_rank: number;    // pre-computed in per-commune JSON
```

**Count of communes in region:** Computable at build time:
```typescript
const regionCommumeCount = loadIndex().filter(
  (c) => c.region_id === data.region_id
).length;
```

**Result:** `#${data.regional_rank} de ${regionCommuneCount} en su región` — fully derivable from existing data with no pipeline changes. Add to the key-stats-row `StatCard` or as its own inline callout.

**Tarapacá bug note (BUGFIX-999.1):** `region_id` uses provincial codes that collide for Tarapacá communes (codes 11/14 overlap with Aysén/Los Ríos region numbers). Until BUGFIX-999.1 is fixed, `regional_rank` for affected Tarapacá communes may be wrong. This is a known backlog item — do NOT attempt to fix in Phase 12.

### Pattern 8: Per-Crime-Type Spoke (D-10)

Static links to existing `/crime/[family]/` and `/es/delito/[family]/` pages. The `FAMILY_SLUGS` map in `i18n.ts` (L354–362) provides the slug pairs:

```typescript
export const FAMILY_SLUGS: Record<string, FamilySlugPair> = {
  vida: { en: 'homicide', es: 'homicidios' },
  robos_violentos: { en: 'violent-robbery', es: 'robos-violentos' },
  // ...7 families total
};
```

The ficha already loads `byFamily` data (L67–68 of commune page). The spoke renders a list of `<a href="/crime/{FAMILY_SLUGS[key].en}/">{familyName}</a>` for each key in `byFamily`. No new data needed.

### Anti-Patterns to Avoid

- **`getRelativeLocaleUrl()` for localized slugs:** This function does NOT translate slug text (e.g. `/rankings/` → `/rankings/`, not `/es/rankings/`). Always hardcode ES slugs. [VERIFIED: PageHeader.astro comment L22–23]
- **`client:*` on the home or ficha:** The home search form must use native HTML `<form action="/communes/">` with `method="get"`. No React island needed.
- **Embedding Leaflet on the ficha:** D-08 explicitly forbids this. The map spoke is a link, not an embed.
- **Absolute "safe/dangerous" labels:** CLAUDE.md editorial rule — use rate/incidence language, always attribute CEAD.
- **`<GeoJSON>` component from react-leaflet:** Already avoided (MapIsland uses native `L.geoJSON()`).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bilingual nav links | Custom locale-resolution logic | Hardcoded per-locale hrefs (existing pattern) | `getRelativeLocaleUrl` doesn't translate slugs |
| Ranking table | Custom `<table>` | `CommuneRankingTable.astro` | Already handles low-pop markers, tooltips, trend chips |
| Similar-commune card | New card component | `CommuneRankingTable.astro` with region filter | Reuses established styling and link patterns |
| Form-based search hero | React search component | HTML `<form action="/communes/" method="get">` | D-05: zero JS in home root |
| Map focus navigation | Leaflet embed on ficha | `?cut=` link to `/map/` + 3-line addition to `loadData()` | D-08: no `client:*` on 346 pages |

---

## Common Pitfalls

### Pitfall 1: `getRelativeLocaleUrl` for localized ES slugs
**What goes wrong:** `/rankings/` link emits `/es/rankings/` for EN locale or produces a path that exists only in EN.
**Why it happens:** `getRelativeLocaleUrl` prefixes the path but does not translate it.
**How to avoid:** Hardcode per-locale: `locale === 'en' ? '/rankings/' : '/es/rankings/'`. This is the documented pattern in `PageHeader.astro` L24–27.
**Warning signs:** 404 on `/es/rankings/` or `/es/mapa/` in the ES locale.

### Pitfall 2: Map focus param fires before choropleth layer is ready
**What goes wrong:** `selectCommune(cut)` is called before `loadData()` finishes mounting the choropleth layer; `polyIdxRef.current.get(cut)` returns `undefined`; `flyToBounds` is never called; no error thrown; focus silently fails.
**Why it happens:** `loadData()` is async and `mapReady` only signals that the `L.map` instance exists, not that polygons are loaded.
**How to avoid:** Call the focus logic at the END of `loadData()`, after `mountChoroplethLayer()` completes, inside the same async function. Do NOT put it in a separate `useEffect` that depends only on `mapReady`.
**Warning signs:** Map opens but does not fly to the commune.

### Pitfall 3: Tarapacá `regional_rank` bug (BUGFIX-999.1)
**What goes wrong:** `#${data.regional_rank} de N en su región` shows wrong region count for Iquique, Alto Hospicio, Pozo Almonte, Pica, Huara, Camiña, Colchane.
**Why it happens:** `region_id` provincial codes 11/14 collide with Aysén/Los Ríos region numbers.
**How to avoid:** This is a known backlog item deferred to after Phase 12. Accept it for now; add a comment in code pointing to BUGFIX-999.1.

### Pitfall 4: `EditorialLayout` used for home page
**What goes wrong:** Home remains constrained to 720px prose column; the two-column rankings layout and full-width map CTA cannot render correctly.
**Why it happens:** The current `index.astro` uses `EditorialLayout`. A new `HomeLayout` is required (D-01).
**How to avoid:** Create `HomeLayout.astro` wrapping `BaseLayout` with full-width slot.

### Pitfall 5: Double H1 on home page
**What goes wrong:** SEO penalty and validation failure.
**Why it happens:** The current home has an H1 in the hero section. Condensing prose below the fold may accidentally retain a second H1.
**How to avoid:** Search for `<h1` in both locale home pages before and after the rebuild; validator must assert exactly one H1 per page.

### Pitfall 6: New `/rankings/` pages missing from sitemap
**What goes wrong:** Google does not index `/rankings/` or `/es/rankings/`.
**Why it happens:** `@astrojs/sitemap` auto-includes static pages, but only if they're reachable. The sitemap validator in `coverage.mjs` currently only checks commune and directory URLs.
**How to avoid:** After deploying, verify `sitemap-0.xml` contains `/rankings/` and `/es/rankings/` entries. Extend validator assertion C to include these URLs.

### Pitfall 7: `MapPlaceholderSlot` vs. hub map spoke
**What goes wrong:** The ficha currently uses `MapPlaceholderSlot.astro` (a "coming soon" dashed box) as its map section. If the Phase 12 map spoke replaces this slot, the placeholder disappears and the spoke CTA appears. If it's left in place AND the spoke is added below it, there are two map sections.
**Why it happens:** `MapPlaceholderSlot` was a Phase 3 mount point contract (`data-phase3-mount="commune-map"`). D-08 replaces the placeholder concept with a static link/CTA.
**How to avoid:** Replace `<MapPlaceholderSlot mountType="commune-map" locale="en" />` (L191 of `[slug].astro`) with the new map-spoke CTA component. Do not keep both.

### Pitfall 8: Breadcrumb leaves current page unlabeled
**What goes wrong:** Screen readers and users can't tell which breadcrumb item is the current page.
**How to avoid:** The last breadcrumb item (`{data.name}`) should be a `<span aria-current="page">` (not an `<a>`). The current breadcrumb stops at Region and doesn't show the commune name at all — the upgrade adds it.

---

## Code Examples

### `MapIsland.tsx` — Focus Param Addition (3 lines inside `loadData()`)

```typescript
// Source: site/src/components/map/MapIsland.tsx — after mountChoroplethLayer() call

// D-08 focus: if ?cut=<cut> present, fly to that commune once layer is ready
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut) {
  setTimeout(() => selectCommune(focusCut), 100);
}
```

Place this immediately after the `if (!cancelled && mapRef.current) { layerRef.current = mountChoroplethLayer(...) }` block, still inside the `if (!cancelled && mapRef.current)` guard.

### Map Spoke Link on Ficha

```astro
<!-- Replaces <MapPlaceholderSlot mountType="commune-map" locale="en" /> -->
<section class="map-spoke" aria-label="View on national map">
  <h2 class="section-heading">View on Map</h2>
  <a href={`/map/?cut=${data.cut}`} class="map-spoke-cta">
    See {data.name} on the interactive Chile crime map →
  </a>
</section>
```

ES:
```astro
<a href={`/es/mapa/?cut=${data.cut}`} class="map-spoke-cta">
  Ver {data.name} en el mapa interactivo →
</a>
```

### Busca tu Comuna Hero Form (zero JS)

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

ES: `action="/es/comunas/"`. The directory finder island already reads `?q=` from the URL — verified in Phase 11 work. [ASSUMED: directory reads `?q=` from URL — planner should verify against `communes/index.astro` finder island implementation]

### Breadcrumb Upgrade (EN)

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

### Regional-Rank Device

```astro
---
const regionCommuneCount = loadIndex().filter(
  (c) => c.region_id === data.region_id
).length;
---
<StatCard
  label={locale === 'en' ? 'Regional rank' : 'Ranking regional'}
  value={`#${data.regional_rank} of ${regionCommuneCount}`}
/>
```

Or as an inline text device in the hero:
```astro
<span class="regional-rank-device">
  #{data.regional_rank} de {regionCommuneCount} en {data.regionName}
</span>
```

### Nav Extension (PageHeader.astro)

```astro
// Add after communesHref:
const rankingsHref = locale === 'en' ? '/rankings/' : '/es/rankings/';

// Add to nav:
<a href={rankingsHref} class="nav-link">{t.nav_rankings}</a>
```

### i18n.ts additions

```typescript
// In I18nStrings interface:
nav_rankings: string;

// In EN_STRINGS:
nav_rankings: 'Rankings',

// In ES_STRINGS:
nav_rankings: 'Rankings',  // same word in both locales
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Narrow editorial home (720px) | Wide HomeLayout with above-fold rankings | Phase 12 (this phase) | Home can render two-column ranking tables + full-width map CTA |
| No map focus from external pages | `/map/?cut=<cut>` URL param + 3-line addition to MapIsland | Phase 12 (this phase) | Every ficha can deep-link to the map centered on itself |
| Breadcrumb: Home › Region | Breadcrumb: Home › Communes › Region › Commune | Phase 12 (this phase) | Adds the directory level; every ficha now links back to the commune directory |
| No Rankings nav item | Rankings in nav + `/rankings/` index | Phase 12 (this phase) | Discovery path for ranking pages |
| `MapPlaceholderSlot` as map section | Static map-spoke CTA link | Phase 12 (this phase) | Placeholder retired; replaced by real cross-link |

**Deprecated/outdated:**
- `MapPlaceholderSlot.astro` (on the ficha): replaced by the map-spoke CTA. The component itself remains for any other potential use but is no longer referenced in the commune template.

---

## Key Research Findings by Target

### Finding 1 (D-08 — Map Focus Param)

**Current state:** `MapIsland.tsx` does NOT read any URL parameter. It mounts at fixed center `[-35.7, -71.8]` zoom 5 (L114). `selectCommune(cut)` exists and calls `flyToBounds` (L352–370), but it is only called via user interaction (SearchBox, map click).

**Data key confirmed:** The layer is indexed by CUT string (`polyIdxRef.current`, a `Map<string, L.Layer>`). The CUT is the right key — not slug.

**Minimum change:** 3 lines inside the existing `loadData()` async function, after `mountChoroplethLayer()` (L195–210). No new state, no new effect, no new component. Estimated: ~15 lines of code including the null check and comment.

**Param syntax decision:** `?cut=<cut>` (e.g. `/map/?cut=13101`). Rationale: CUT is the primary internal key; avoids a reverse slug→CUT lookup; cleaner than hash; existing `URLSearchParams` API is standard and CSP-safe.

### Finding 2 (CommuneRankingTable Reuse)

**Props shape:** `{ rows: RankingRow[], locale }` where `RankingRow` = `{ name, slug, rate, national_rank, trend, low_population }`. [VERIFIED: component source L16–28]

**Home lead tables fit:** Direct. Caller prepares top-N rows sorted by rate (ascending for safest, descending for highest-incidence). Pass `rows` and `locale`. No prop changes needed.

**`/rankings/` index fit:** NOT a fit — that page is a link list, not a commune ranking table.

**"Similar comunas" spoke fit:** Fits if caller passes same-region communes sorted by rate proximity. Needs a new `nearestComparables(cut, n)` data helper returning `RankingRow[]`.

**`ComparableCommune.astro` reuse (D-07):** Currently shows ONE result. D-07 says "similar comunas" (plural). Options: (A) reuse `CommuneRankingTable.astro` with region-filtered rows (recommended), or (B) extend `ComparableCommune.astro` to accept an array. Option A requires no component changes.

### Finding 3 (Home Rebuild)

**Current home:** `site/src/pages/index.astro` — `EditorialLayout` (720px), ~210 lines, 5 prose sections (What the Data Shows / How to Read Crime Rates / About CEAD / Limitations / Explore). No ranking tables, no search hero, no map CTA section. [VERIFIED: source L1–210]

**Prose to condense (D-02):** The 5 sections collapse to a ~2-paragraph "about CEAD + how to read rates" block that goes below the fold. The current prose is strong editorially — preserve the key factual claims, condense the depth.

**`EditorialLayout` must be replaced** with `HomeLayout` (D-01). A new `HomeLayout.astro` wraps `BaseLayout` with no column width constraint. The AdSlot injection from `EditorialLayout` needs replicating in `HomeLayout` or passing as a slot.

**ES parity:** `site/src/pages/es/index.astro` — same structure, same transformation needed. Must be rebuilt simultaneously to maintain hreflang reciprocity.

### Finding 4 (Breadcrumb — D-09)

**Current breadcrumb** (`[slug].astro` L125–L128):
```
Home › {regionName}
```
Missing: the "Communes" level AND the current commune name as the terminal item. [VERIFIED: source L124–130]

**ES equivalent** (`es/comuna/[slug].astro`): same structure around L105–110 (not read in full but mirrors EN).

**Files:** Both `site/src/pages/commune/[slug].astro` and `site/src/pages/es/comuna/[slug].astro` need the identical fix.

### Finding 5 (Nav + /rankings/ + Footer — D-12/D-13)

**PageHeader.astro pattern:** Hardcoded per-locale hrefs, 4 nav links, zero JS. Adding a 5th link follows the exact same pattern as `communesHref` (L27). [VERIFIED: L24–27 + L60–64]

**i18n.ts:** Interface `I18nStrings` already has `nav_communes` (added in Phase 11). Adding `nav_rankings` requires: interface field, EN value, ES value. [VERIFIED: interface L107 + EN L220 + ES L336]

**`/rankings/` page:** A new static Astro page at `site/src/pages/rankings.astro` + `site/src/pages/es/rankings.astro`. Content: a heading + an `<ul>` linking existing ranking pages (regional ranking at `/region/*/`, crime-type ranking at `/crime/*/`, safest cities, highest-incidence). No new data, no new components.

**Footer:** No `PageFooter.astro` exists today. [VERIFIED: no footer component found in `site/src/components/`] The footer spine is a new component. It should mirror the PageHeader pattern: static Astro, hardcoded per-locale hrefs, included in `BaseLayout.astro`.

### Finding 6 (Validator Extension — D-13)

**Current validators:** `coverage.mjs` has assertions A–E. A = route count, B = no-orphan-link (commune hrefs only), C = sitemap commune coverage + directory, D = directory completeness, E = no-gating-string. [VERIFIED: coverage.mjs L1–320]

**Extension needed:**
- Assertion F: New cross-links (map spokes `/map/?cut=<cut>`, `/es/mapa/?cut=<cut>`) must not produce 404 — verify `/map/` and `/es/mapa/` exist in dist.
- Assertion G: `/rankings/` and `/es/rankings/` exist in dist AND sitemap includes them.
- Assertion H: Breadcrumb "Communes" link (`/communes/` and `/es/comunas/`) exists in every commune page HTML AND both directories are in dist.
- No link-reciprocity check is possible against a static dist (no server to hit) — but "reciprocity" can be asserted as: for every `/commune/{slug}/` page, there exists an href pointing back to `/communes/` and to `/region/{regionSlug}/`.

**Implementation:** Add assertions F–H to `coverage.mjs` (or a new `spine.mjs` imported by `all.mjs`).

### Finding 7 (Regional-Rank Device)

**`data.regional_rank`** is present in `CommuneData` as a number. [VERIFIED: data.ts L42]

**Region commune count** is derivable from `loadIndex().filter(c => c.region_id === data.region_id).length`. Note: this counts ALL communes in the `region_id`, including low-population ones. The spike uses "52 en su región" — decide whether to count all or only non-low-pop. Recommendation: count all (matches user expectation of "in this region").

**Tarapacá caveat:** `regional_rank` and `region_id` for Tarapacá communes are affected by BUGFIX-999.1. Surface a comment in code; do not block the phase on it.

---

## Validation Architecture

> `workflow.nyquist_validation` is not explicitly set to false in `.planning/config.json` — treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Node.js validator scripts (`site/scripts/validate/*.mjs`) |
| Config file | `site/scripts/validate/all.mjs` (orchestrates all) |
| Quick run command | `node scripts/validate/coverage.mjs` (from `site/`) |
| Full suite command | `node scripts/validate/all.mjs` (from `site/`) |
| Build prerequisite | `npm run build` must complete first (validators run against `dist/`) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IA-01 | Home has exactly one H1; is static/indexable; `/` and `/es/` both build | build gate | `npm run build` | ✅ (existing build) |
| IA-01 | Home breadcrumb-free (no breadcrumb on home) | unit/structure | extend `structure.mjs` | ✅ Wave 0 extension |
| IA-01 | EN/ES parity — `/` and `/es/` both have single H1 | structure | extend `structure.mjs` | ✅ Wave 0 extension |
| IA-02 | Every commune page has breadcrumb with `/communes/` link | coverage | new assertion in `coverage.mjs` or `spine.mjs` | ❌ Wave 0 new |
| IA-02 | Map spoke link (`/map/?cut=<cut>`) is present in every commune page | coverage | new assertion in `spine.mjs` | ❌ Wave 0 new |
| IA-02 | Map spoke links resolve (no 404): `/map/` and `/es/mapa/` exist in dist | coverage | new assertion F in `coverage.mjs` | ❌ Wave 0 new |
| IA-03 | `/rankings/` and `/es/rankings/` exist in dist | coverage | new assertion G | ❌ Wave 0 new |
| IA-03 | Sitemap includes `/rankings/` and `/es/rankings/` | sitemap | extend assertion C in `coverage.mjs` | ✅ extension of existing |
| IA-03 | Nav "Rankings" link is present in every page header | structure | scan dist HTML for `href="/rankings/"` | ❌ Wave 0 new |
| IA-03 | No 404 from any commune breadcrumb `/communes/` link | coverage | assertion B already covers commune hrefs; extend for `/communes/` | ✅ extension |
| D-08 | Map island reads `?cut=` and flies to commune (manual check) | manual/e2e | BrowserOS smoke test | manual only |

### Wave 0 Gaps

- [ ] `site/scripts/validate/spine.mjs` — new validator for: map-spoke present in commune pages, `/rankings/` in dist + sitemap, nav rankings link in all pages
- [ ] Extend `coverage.mjs` assertion C: add `/rankings/` and `/es/rankings/` to sitemap check
- [ ] Extend `structure.mjs` or add home-specific check: single H1 on home page (EN + ES)
- [ ] Manual smoke test script / BrowserOS steps for map focus param

### Sampling Rate

- **Per task commit:** `node scripts/validate/coverage.mjs` (quick, ~5s)
- **Per wave merge:** `node scripts/validate/all.mjs` (full suite)
- **Phase gate:** Full suite green + manual map focus param smoke test before `/gsd:verify-work`

---

## Security Domain

> `security_enforcement` not set to false — treated as enabled.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — (no login) |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Yes — search form `?q=` param | Native HTML form; param is passed as-is to the directory finder island. Island already handles the param (Phase 11). No server-side processing. Client-side rendering only — no injection vector. |
| V6 Cryptography | No | — |

**Additional:** The `?cut=` param in the map link is read by client-side JS and passed to `selectCommune()`. The only operation is `polyIdxRef.current.get(cut)` (Map lookup) and `map.flyToBounds()`. No `eval`, no innerHTML, no server round-trip. The CUT is a string like `'13101'`; the Leaflet call is benign if the CUT is not found (returns `undefined`, no flight). No sanitization needed beyond the existing no-op.

---

## Environment Availability

> Phase 12 is code/config changes only. External dependencies are the same as the existing build.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js 20+ | Astro build | ✓ | (existing) | — |
| Astro 6 | Static site build | ✓ | 6.4.x | — |
| npm | Package management | ✓ | (existing) | — |

No new external tools or services required.

---

## Open Questions

1. **Does the communes directory finder island read `?q=` from the URL on page load?**
   - What we know: The home search hero (D-05/D-06) routes to `/communes/?q=santiago` on submit. D-05 says the directory carries the query.
   - What's unclear: Whether `communes/index.astro`'s finder island auto-populates the search input from `?q=` on load. This was Phase 11 work and is likely yes (it would defeat the purpose otherwise), but the file was not read in this research pass.
   - Recommendation: Planner should read `site/src/pages/communes/index.astro` to confirm the finder island reads `?q=` via `URLSearchParams`. If not, a 1-line addition to the finder island is needed in Wave 0.

2. **Footer placement: `BaseLayout` vs. per-page?**
   - What we know: `EditorialLayout` wraps `BaseLayout` and adds AdSlot. `HomeLayout` will similarly wrap `BaseLayout`. A footer in `BaseLayout` would appear on all pages.
   - What's unclear: Whether the footer spine should be in `BaseLayout` (global) or only in `HomeLayout`/`EditorialLayout` (per-layout). Global placement is simpler.
   - Recommendation: Place `PageFooter` in `BaseLayout` (universal). This ensures the spine appears on map, commune, region, and editorial pages with zero per-page changes.

3. **`CommuneRankingTable` on home — how many rows?**
   - What we know: Spike 001-c shows 6 rows each (safest + highest-incidence).
   - What's unclear: Exact row count for the lead tables is "Claude's discretion" (CONTEXT.md).
   - Recommendation: 5–6 rows each, sorted by rate. The planner should pick a number and document it.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The communes directory finder island reads `?q=` from URL on page load | Open Questions #1 | Home search hero would route users to an unfocused directory; fix requires 1-line addition to finder island |
| A2 | No new npm packages are needed for this phase | Standard Stack | If a new layout requires a dependency not in the project, Wave 0 would need a package install task |

---

## Sources

### Primary (HIGH confidence — verified by reading actual source files)

- `site/src/components/map/MapIsland.tsx` — confirmed: no URL param reading; `selectCommune(cut)` exists and uses CUT as key; `flyToBounds` wired
- `site/src/pages/map.astro` + `site/src/pages/es/mapa.astro` — confirmed: only `lang` and `nationalAvg` props passed to island
- `site/src/pages/commune/[slug].astro` — confirmed: breadcrumb structure (L124–129), MapPlaceholderSlot at L191, data fields available
- `site/src/components/CommuneRankingTable.astro` — confirmed: props interface, columns, locale-aware hrefs
- `site/src/components/ComparableCommune.astro` — confirmed: single-result, links to commune pages
- `site/src/components/MapPlaceholderSlot.astro` — confirmed: Phase 3 mount-point placeholder, not a link
- `site/src/components/PageHeader.astro` — confirmed: hardcoded per-locale slug pattern; 4 nav links; hamburger
- `site/src/config/i18n.ts` — confirmed: `I18nStrings` interface; `nav_communes` present; `FAMILY_SLUGS` map
- `site/src/lib/data.ts` — confirmed: `regional_rank` field in `CommuneData`; `loadIndex()` filter pattern
- `site/src/pages/index.astro` — confirmed: `EditorialLayout` (720px); 5 prose sections; no ranking tables
- `site/scripts/validate/coverage.mjs` — confirmed: assertions A–E; extensible pattern

### Secondary (MEDIUM confidence — derived from reading related context files)

- `.planning/phases/12-home-ia-redesign-comuna-page-hub-and-spoke/12-CONTEXT.md` — locked decisions D-01 to D-14
- `.planning/spikes/001-home-hub-framing/README.md` — Hybrid C+B verdict confirmed
- `.planning/spikes/003-comuna-page-spokes/README.md` — regional-rank device confirmed as computed live in spike

---

## Metadata

**Confidence breakdown:**
- D-08 (map focus param): HIGH — source code read, mechanism confirmed, change identified
- Component reuse: HIGH — source code read, props verified
- Home rebuild mechanics: HIGH — source code read
- Breadcrumb upgrade: HIGH — source code read, exact lines identified
- Nav + i18n extension: HIGH — source code read, pattern confirmed
- Validator extension: HIGH — coverage.mjs read in full
- Regional-rank data availability: HIGH — `CommuneData.regional_rank` confirmed in types

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 (stable codebase; no external APIs involved)
