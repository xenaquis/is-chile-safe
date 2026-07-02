# Phase 25: UI/UX 360 Remediation — Research

**Researched:** 2026-07-02
**Domain:** Astro 6 static site, React islands, Leaflet map, Python news pipeline
**Confidence:** HIGH (pure codebase reconnaissance — no speculative web research)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Execute ALL fixes from `.planning/UI-360-DIAGNOSTIC-260702.md` in reported priority order.
- Each P0 item is its own independent atomic commit, first.
- New editorial visuals (P1-5) must be static HTML at build time — not client-rendered.
- DeepSeek model IDs: `deepseek-v4-flash` / `deepseek-v4-pro` only (never `deepseek-chat`).

### Claude's Discretion
Exact breakpoint values within specified ranges, favicon glyph design, sparkline SVG approach,
pagination vs date-grouping for news, chip styling.

### Deferred Ideas (OUT OF SCOPE)
- P2-2 home vs `/is-chile-safe/` keyword cannibalization re-targeting.
- Home `<title>` lengthening (bundle with cannibalization decision).
- AdSense CLS measurement (only relevant once ads are inserted).
</user_constraints>

---

## Summary

This research is a pure codebase reconnaissance to map each diagnostic defect to its exact
file and line, so the planner can write concrete, zero-ambiguity tasks.

The most critical finding for P0-1: `site/public/_redirects` does **not exist** in the repo.
The soft-404 is almost certainly produced by Cloudflare Pages' built-in SPA-fallback behavior
when no `404.html` exists — it serves the root `index.html` for any unmatched path. Fix is to
create `site/src/pages/404.astro` (Astro outputs `dist/404.html`) and leave `_redirects` absent.
No catch-all to remove — just add the missing 404 page.

P0-3 (favicon): `BaseLayout.astro` has no `<link rel="icon">` in the `<head>`. The public
directory contains `icon-192.png` and `icon-512.png` (PWA manifest icons) but no `favicon.ico`
and no SVG favicon. The fix is cheap: add an SVG favicon to `public/`, add the `<link>` in
BaseLayout, and the `.ico` serving bug (P0-1) disappears once the real 404 is in place.

For P1-1 (number formatting): `ResultPanel.tsx` unconditionally uses `'es-CL'` locale, so EN
users see `4.984` (comma thousands separator). There is no shared `formatNumber` helper anywhere
in `site/src/` — each component/island calls `.toLocaleString()` independently with inconsistent
or hardcoded locale arguments. Creating `site/src/lib/formatNumber.ts` and wiring it in ~8
touch-points will close all instances.

For P0-2 (tablet overflow): the hamburger trigger is `@media (min-width: 640px)` in
`PageHeader.astro`. At 772 px viewport the full nav is displayed (8 items) but overflows. The
fix is raising the breakpoint to `≥1100px` for all four `640px` queries inside `PageHeader.astro`
and stacking the two `.lead-table-col` blocks on the home index page at ≤900px.

**Primary recommendation:** Execute P0 fixes first (each its own commit), then follow the
diagnostic report's stated order. All fixes are scoped to well-identified files with clear
line-level anchors — no architectural changes required.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 404 page | Cloudflare Pages CDN | Astro static build | CF Pages serves `dist/404.html` with real 404 status automatically when no catch-all redirect exists |
| Favicon | Browser / `<head>` | Astro BaseLayout | Single injection point in BaseLayout.astro |
| Nav breakpoints | Browser CSS | PageHeader.astro | Zero-JS CSS checkbox-toggle hamburger |
| Number formatting | Browser / React islands | Astro static pages | Both SSR (Astro) and CSR (islands) paths need the same helper |
| Map init bounds | Browser / Leaflet island | MapIsland.tsx | `L.fitBounds` replaces `L.setView` — island-only change |
| News heading semantics | Astro static (SSG) | — | `news.astro` is static; `<div>` → `<h2>` fix in template |
| Classifier filter | Python pipeline | classifier.py | System prompt edit + optional post-filter |
| JSON-LD WebSite/Org | Astro BaseLayout (SSG) | — | Add to `BaseLayout.astro` `jsonLd` prop on home page |

---

## Defect-to-File Map (the planner's primary reference)

### P0-1: Soft-404 / catch-all

| Item | Finding |
|------|---------|
| `site/public/_redirects` | **Does not exist** — confirmed `FILE NOT FOUND`. No catch-all to remove. |
| `site/src/pages/404.astro` | Does not exist. Astro will output `dist/404.html` when this file is created. |
| Cloudflare behavior | [ASSUMED] CF Pages serves the root `index.html` for unmatched paths when `404.html` is absent. Adding `dist/404.html` to the build causes CF to serve it with real 404 status. No `_redirects` changes needed. |
| `robots` tag in soft-404 | Currently `index,follow` because the 200-returned homepage has it. Real 404 page should have `<meta name="robots" content="noindex">`. |
| Favicon 200/html symptom | Caused by the same CF SPA-fallback (no `favicon.ico` → CF returns homepage HTML). Resolved automatically once real 404 is in place AND `public/favicon.ico` exists. |
| Fix location | Create `site/src/pages/404.astro` using `BaseLayout` with `lang="en"` (bilingual content inline), `<meta name="robots" content="noindex">` override, links to `/`, `/map/`, `/rankings/`. |

### P0-3: Favicon

| Item | Finding |
|------|---------|
| `<link rel="icon">` in BaseLayout | **Absent** — `site/src/layouts/BaseLayout.astro` lines 63–113: no favicon link tag anywhere in `<head>`. |
| Existing assets | `site/public/icon-192.png` and `site/public/icon-512.png` exist (used by `manifest.json`). No SVG, no `.ico`. |
| Brand glyph | `PageHeader.astro` lines 43–47 contains an inline SVG map-pin mark (circle + ellipse + path, fill `var(--primary)` `#0f766e`). This same glyph should be the basis for the favicon. |
| Fix | Create `site/public/favicon.svg` (the pin glyph, simplified, with `#0f766e` fill). Create `site/public/favicon.ico` (16×16 or 32×32, same glyph). Add to `BaseLayout.astro` `<head>`: `<link rel="icon" href="/favicon.svg" type="image/svg+xml" />` + `<link rel="icon" href="/favicon.ico" sizes="any" />` + `<link rel="apple-touch-icon" href="/icon-192.png" />`. |

### P0-2: Tablet overflow (640–1080px)

| Item | Finding |
|------|---------|
| Hamburger breakpoint | `PageHeader.astro` has **four** `@media (min-width: 640px)` blocks (lines 130–134, 204–206, 227–229, 255–263). All must be raised to `1100px`. |
| Nav items | 8 items in `<nav class="csm-nav">`: Home, Map, Compare, Communes, Rankings, Methodology, News, Glossary. At ~100px average width × 8 = ~800px nav alone, leaving no room at 772px. |
| Glossary label | `glossary_link: 'Crime type glossary'` (i18n.ts line 296, ES: 'Glosario de tipos de delito' line 495). Shorten EN to `'Glossary'`, ES to `'Glosario'`. Edit `site/src/config/i18n.ts` then update the display in `PageHeader.astro` nav. |
| `.lead-table-col` | Not yet found in `site/src/pages/index.astro` — planner must verify. But the diagnostic attributes the 504px-wide columns to the home page. Fix: `flex-wrap: wrap` or `grid 1-col` at ≤900px. |
| `.header-right` / `.lang-toggle` | Already `margin-left: auto` (line 155) — should reflow fine once nav collapses earlier. |

### P1-1: Number formatting inconsistency

All call sites found via grep. No `formatNumber` helper exists anywhere in `site/src/`.

**Root cause in ResultPanel.tsx (React island):**
- Line 200: `Math.round(rate).toLocaleString('es-CL')` — **hardcoded `'es-CL'`** regardless of `lang` prop. This is the "~4.984" bug in the EN map panel.
- Line 393: `Math.round(homRate!).toLocaleString('es-CL')` — same hardcoding.
- Line 305: `<div className="stat-big">~{displayRate}</div>` — the literal `~` prefix here.
- Line 319: `multiplierNum.toLocaleString(lang === 'es' ? 'es-CL' : 'en-US', ...)` — correctly locale-aware (good pattern to generalize).

**Other call sites needing the helper:**
| File | Line(s) | Bug |
|------|---------|-----|
| `site/src/components/map/ResultPanel.tsx` | 200, 393 | hardcoded `'es-CL'` |
| `site/src/components/map/Legend.tsx` | 37 | `toLocaleString(lang==='es'?'es-CL':'en-US')` — already correct pattern, just centralise |
| `site/src/components/CommuneRankingTable.astro` | 78 | `toLocaleString()` — no locale arg, uses system locale |
| `site/src/components/ComparableCommune.astro` | 51 | `toLocaleString()` — no locale arg |
| `site/src/islands/ComparatorIsland.tsx` | 620 | `rate.toFixed(1)` — no thousands separator at all (the "2871.5" bug) |
| `site/src/islands/ComparatorIsland.tsx` | 644 | `homRate!.toFixed(2)` — 2 decimal places (vs 1 elsewhere) |

**Fix:** Create `site/src/lib/formatNumber.ts` exporting:
```typescript
export function formatRate(value: number, locale: 'en' | 'es'): string {
  return Math.round(value).toLocaleString(locale === 'es' ? 'es-CL' : 'en-US');
}
export function formatDecimal(value: number, locale: 'en' | 'es', decimals = 1): string {
  return value.toLocaleString(locale === 'es' ? 'es-CL' : 'en-US',
    { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
```
Astro components receive `locale` from frontmatter; React islands receive it as a `lang` prop.
`CommuneRankingTable.astro` and `ComparableCommune.astro` already receive a `locale` prop (confirmed via usage on commune pages).

**The `~` prefix** (P1-4 concern): `ResultPanel.tsx` line 305 is `~{displayRate}`. The tilde should be removed — or if kept, explained in a tooltip (P1-4 groups this). The rate display is approximate (rounded integer), not a "roughly" estimate in any meaningful sense.

### P1-3: Map — initial view, legend, pills, pin color, ?cut= guard

| Item | Finding | Fix Location |
|------|---------|-------------|
| Initial view | `MapIsland.tsx` line 125: `map.setView([-35.7, -71.8], 5)` — hardcoded | Replace with `map.fitBounds([[-55.9, -75.7], [-17.5, -66.4]], { padding: [20,20] })` for Chile continental bbox (lat/lng), then set `map.setMaxBounds(...)`. Keep zoom 5 as `minZoom`. |
| Incident pin color | `IncidentPinLayer.ts` line 155–160: `L.divIcon` with `html: '<div class="ev-dot"></div>'`. The `.ev-dot` CSS is in `map.css` — need to check its color. | Change `.ev-dot` fill color to `#7c3aed` (violet, clearly distinct from orange choropleth). |
| Pin aria-label | `IncidentPinLayer.ts` line 154: `L.marker([incident.lat, incident.lng], { icon: L.divIcon(...) })` — no `title` or accessible name. | Add `title: escHtml(lang === 'es' ? incident.title_es : incident.title_en)` to the marker options (Leaflet `title` creates a tooltip that screenreaders can use; also add `aria-label` via the divIcon html). |
| ?cut= guard | `MapIsland.tsx` lines 225–229: `const focusCut = new URLSearchParams(...).get('cut'); if (focusCut) { setTimeout(() => selectCommune(focusCut), 100); }` — **no validation before fetch**. An invalid CUT causes ResultPanel to fetch `/data/cead/comunas/99999.json`, get a 404, and show error state. | Add guard: `if (focusCut && communeIndex.length > 0 && communeIndex.some(c => c.cut === focusCut))` before the setTimeout. Wait for `communeIndex` state to be populated (it's set at line 181 after parallel fetch). |
| Legend mobile | `Legend.tsx` — need to verify CSS but the diagnostic says it takes 40% height at 375px. | Add a CSS class `.legend--collapsed` toggled by a `<details>` or a small expand button in Legend.tsx; auto-expand on desktop via media query. |
| Pills overlap | `MapTopbar.tsx` (or `FiltersRow.tsx`) — pills "Index / By crime" sit in same row as search at ≤480px. | Stack pills + search in `flex-direction: column` at ≤480px in `map.css`. |

### P1-2: Compare island — label, URL sync, trends, empty state

| Item | Finding | Fix |
|------|---------|-----|
| Missing "Composite Crime Index" label | `ComparatorIsland.tsx` line 579–583: shows `ci.score.toFixed(1)` with `bandLabel` below, but no label naming the index. | Add a row above the score: `<div style="...font-size:var(--text-label);...">Composite Crime Index</div>` + link to `/methodology/`. |
| Editorial risk | "Very High" bare label without index name risks violating the editorial rule. Adding the index name resolves this. | |
| URL sync | `ComparatorIsland.tsx` has no `useEffect` or `history.replaceState` for URL. No URL sync at all. | Add `useEffect` watching `selected`: `window.history.replaceState(null,'',`?a=${selected[0]?.id??''}&b=${selected[1]?.id??''}`)`. On mount, read `?a=` + `?b=` and pre-select communes from the index. Align slug format with `/compare/x-vs-y/` pre-generated pages which use slugs not CUT codes (check `[pair].astro`). |
| All trends "→" | `ComparatorIsland.tsx` line 630: `{TREND_ARROW[data.trend] ?? '→'}` — uses `data.trend` (commune overall trend) for **every** family row. This is correct behavior (there is no per-family trend in the JSON); the issue is visual. The "all same arrow" appearance is technically accurate but misleading. | Document: the commune JSON has one `trend` field (overall). Per-family trends don't exist in the data. Show the overall trend indicator once (in the header card) rather than repeating it on every row. |
| Empty state | `ComparatorIsland.tsx` lines 458–468: only a text prompt `{s.cmp_empty_heading}`. | Add a `<div class="cmp-popular-chips">` with clickable chips for: Santiago vs Las Condes, Providencia vs Ñuñoa, Viña del Mar vs Valparaíso. Clicking a chip calls `selectCommune` twice. |

### P1-4: Map panel — years mixed, "~" prefix, two rank systems

| Item | Finding | Fix |
|------|---------|-----|
| Composite year const | `ResultPanel.tsx` line 41: `const COMPOSITE_YEAR = 2024;` | Keep constant; add year badge next to composite score block |
| Rate year | `ResultPanel.tsx` receives `year` prop from MapIsland state (default 2025, from `useState(2025)` MapIsland line 96) | Add year badge next to rate display |
| Two rank systems | `ResultPanel.tsx` has `data.national_rank` (rate-based, all years) and `data.composite_index[COMPOSITE_YEAR].rank` (composite 2024). Displayed separately. | Group into two visual blocks with year badges: "Rate Ranking (2025)" and "Composite Index Ranking (2024)". Reuse the existing `RateTooltip`/tooltip pattern for a "?" explaining why years differ. |
| "~" prefix | `ResultPanel.tsx` line 305: `~{displayRate}`. No explanation of why "~". | Remove `~` (it adds noise; the rate is an integer approximation but not imprecise in the "roughly" sense). |
| Tilde rationale | The `~` may have been intended to signal rounding to integer. With `formatRate()` the integer rounding is inherent. Drop it. | |
| Tooltip pattern | Existing: `RateTooltip.tsx` and `RateTooltipReact.tsx` components are imported in ResultPanel already (line 21). The "?" tooltip pattern exists. | Reuse `RateTooltipReact` for the year-mismatch explanation. |

### P1-5: Editorial pages — add visuals

**Pages affected:** `site/src/pages/is-santiago-safe.astro`, `site/src/pages/is-chile-safe.astro`, `site/src/pages/safest-cities-in-chile.astro`.

| Item | Finding |
|------|---------|
| Data source | `site/src/lib/data.ts`: `loadCommune(cut)`, `loadIndex()`, `loadNationalAverage()` all read from `data/cead/` at build time. Available: full series per commune, `national_rank`, `featured_rates`, `population`, `low_population`. |
| `Sparkline.astro` | Exists at `site/src/components/Sparkline.astro`. Takes `series` array and renders inline SVG. Zero JS. Reuse directly. |
| `CommuneRankingTable.astro` | Exists. Takes `rows` and `locale`. Renders a full sortable table. Pattern: `commune/[slug].astro` comparable communes section uses `ComparableCommune.astro` for horizontal cards. |
| Gran Santiago filter | Filter `loadIndex()` by `region_id === '13'` to get Región Metropolitana communes (~52 communes). For the "Gran Santiago" table, further filter to well-known municipalities. Alternatively use national_rank to get top/bottom 10 from RM. |
| `is-santiago-safe.astro` current state | Lines 16–20: loads `santiago` commune (CUT 13101), `nationalAvg`, `year`, `rate`, `vsNationalPct`. Lines 29–63: 6 FAQs in text. Lines 66–138: `EditorialLayout` + text + `DataCallout` + `FAQBlock`. **Zero visual elements beyond two KPI callouts.** |
| Fix | After the intro `<p>` and before the FAQ: add `<CommuneRankingTable rows={top10RM} locale="en" />` + `<Sparkline series={santiago.series} activeYear={year} />`. Compute `top10RM` in frontmatter from `loadIndex()` filtered to `region_id='13'`, sorted by rate, top 10 and bottom 10. All at build time. |
| `/is-chile-safe/` and `/safest-cities-in-chile/` | Same pattern. Check these files' current state for available data hooks. |

### P1-6: News page — headings, metadata, classifier

| Item | Finding |
|------|---------|
| Card title element | `site/src/pages/news.astro` line 115: `<div class="incident-title">` — not a heading. 0 h2/h3 on page. | Change to `<h2 class="incident-title">` (or `<h3>` if a section-level `h2` groups by date). |
| Crime type chip | `current.json` schema includes `family` field on each incident (per `IncidentPinLayer.ts` type). `news.astro` does NOT surface the `family` field. | Add `family` to the destructured type in `news.astro` frontmatter and render a chip: `<span class="incident-chip">{incident.family}</span>`. |
| Comuna chip | The `slug` field is used for the "View commune" link but the commune **name** is not shown. | Map `incident.cut` → commune name via a lookup dict built from `loadIndex()` (same as editorial pages use). Show as `<span class="incident-chip">Carahue</span>`. |
| Date grouping / pagination | 129 items in a flat `<ul>`. Pagination requires client-side JS or server-side pagination (out of scope for static). Date grouping by week is achievable at build time by grouping the sorted array before rendering. | Use build-time grouping: group incidents by `date.slice(0,7)` (YYYY-MM) into `<section><h2>June 2026</h2><ul>...</ul></section>` blocks. No JS needed. |
| Classifier traffic filter | `pipeline/news/classifier.py` SYSTEM_PROMPT line 108: "If the article is not about a crime incident, set commune_name to null and confidence to 0.0." This instruction is too vague — a fatal traffic collision passes if the LLM classifies it under `vida` (crimes against life). The `FAMILY_KEYS` includes `vida` (crimes against life/homicide-adjacent). | Add to SYSTEM_PROMPT Rules: `"Traffic accidents, road collisions, and vehicle crashes are NOT crime incidents, even if fatal. If the article is primarily about a traffic accident, it is NOT a crime incident — set confidence to 0.0."` Also consider a post-classify heuristic filter in `scrape_news.py` that rejects items where `family=='vida'` and the title contains keywords like `colisión`, `accidente de tránsito`, `choque`, `atropello sin culpa`. |

### P2-1: Accessibility

| Item | Finding |
|------|---------|
| Leaflet marker aria-label | `IncidentPinLayer.ts` line 154: `L.marker(...)` with `L.divIcon` — no `alt`, no `title`, no `aria-label`. Leaflet converts `title` option into a DOM title attribute on the marker element. | Add `title: escHtml(lang === 'es' ? incident.title_es : incident.title_en)` to marker options. For better screen reader support, also add `aria-label` inside the divIcon html: `html: \`<div class="ev-dot" aria-label="${escHtml(title)}" role="img"></div>\``. |
| `:focus-visible` | `site/src/styles/global.css` lines 166–173: **already has `:focus-visible { outline: 2px solid var(--primary); }`** and `*:focus:not(:focus-visible) { outline: none; }`. The diagnostic noted `outline: none` on computed style — this is likely from a **component-scoped** CSS override on `.nav-link`, `.incident-source`, or similar. | Grep for `outline: none` in all component `<style>` blocks to find the override. Do NOT change the global rule. |
| Skip link | No skip-to-main link found in `BaseLayout.astro` or `PageHeader.astro`. | Add `<a href="#main-content" class="skip-link">Skip to main content</a>` as first child of `<body>` in BaseLayout, and `id="main-content"` on `<main class="page-content">`. Style `.skip-link` as visually hidden until focused. |

### P2-2: SEO — JSON-LD additions

| Item | Finding |
|------|---------|
| `WebSite` + `SearchAction` | `site/src/lib/jsonld.ts`: has `buildItemList` and `buildBreadcrumb`. No `WebSite` builder. | Add `buildWebSite()` to `jsonld.ts` returning `{ "@type": "WebSite", "@context": "...", "url": "https://ischilesafe.com", "name": "Chile Safety Map", "potentialAction": { "@type": "SearchAction", ... } }`. Inject on home `index.astro` only. |
| `Organization` | Same location. | Add `buildOrganization()` returning `{ "@type": "Organization", "@context": "...", "name": "Chile Safety Map", "url": "https://ischilesafe.com" }`. Inject on home. |
| `/rankings/` region links | `site/src/pages/rankings.astro` lines 78–83: "By region" section has a prose paragraph pointing to the map, **no links to the 16 region pages**. | Import `REGION_NAMES` (or use the same 16-region map from `ResultPanel.tsx`) in `rankings.astro` frontmatter. Render a `<ul>` of 16 `<a href="/region/{slug}/">` links. Region slugs can be derived from the region JSON files in `data/cead/regions/`. |

### P2-3: Visual consistency

| Item | Finding | Fix |
|------|---------|-----|
| Glossary nav label | `i18n.ts` line 296: `'Crime type glossary'` wraps in 3 lines at mid-desktop. | Change to `'Glossary'` (EN) and `'Glosario'` (ES) in `site/src/config/i18n.ts`. |
| Region KPI direction | `site/src/pages/region/[slug].astro` line 197: `value={`#${nationalPosition} of 16`}` — no direction indicator. | Change to `value={`#${nationalPosition} of 16`}` with `label` sub-text: `"1 = highest reported"`. Follow the commune page pattern (which already has directional labels per memory). |
| Region evolution title year | `region/[slug].astro` line 207: `<h2>Annual evolution (2005–{latestCompleteYear})</h2>`. If partial 2026 bar is in series, `latestCompleteYear` excludes it (filtered by `!s.partial`), but the chart itself renders all series including partial. | Either extend the title to `(2005–{allYears[last]})` with a `*partial` note, or ensure the chart only renders complete years. The commune page uses `partialYear` flag already — apply same pattern. |
| Homicide decimals | `ComparatorIsland.tsx` line 644: `homRate!.toFixed(2)` — 2 decimal places vs `toFixed(1)` elsewhere. | Change to `toFixed(1)` and wire through the new `formatDecimal` helper. |
| "(1 cases)" pluralization | `ComparatorIsland.tsx` line 644: `(${homCount})` — the surrounding text comes from `s.cmp_homicide_row` string `'Homicide (per 100k, {year})'`. The count `(1)` renders as `"8.69 (1)"` which is fine; but if the surrounding prose says "cases" it needs singular. Check `i18n.ts` for the `cmp_homicide_row` pattern. | Add `{homCount === 1 ? 'case' : 'cases'}` around the count in the island render (EN) and ES equivalent. |

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Favicon generation | Custom SVG-to-ICO build script | Pre-generate `favicon.ico` manually from brand SVG; commit as static asset |
| Locale-aware number format | Custom number formatter | `Intl.NumberFormat` / `.toLocaleString()` with explicit locale tag |
| 404 page routing | Cloudflare `_redirects` catch-all with custom response | Astro `src/pages/404.astro` → `dist/404.html` + CF Pages automatic 404 serving |
| Date grouping for news | Client-side pagination JS | Build-time array grouping in `news.astro` frontmatter (zero JS) |
| Region links in rankings | Dynamic API fetch | Static import of REGION_NAMES map already present in `ResultPanel.tsx` |
| Traffic accident heuristic | External NLP classifier | Simple keyword deny-list in `scrape_news.py` post-filter |

---

## Common Pitfalls

### Pitfall 1: Raising hamburger breakpoint only partially
Four separate `@media (min-width: 640px)` blocks in `PageHeader.astro` (lines 130, 204, 227, 255).
Missing any one of them leaves the nav in a broken state (e.g., the checked-state dropdown still
uses the wrong position at mid-range). All four must change together.

### Pitfall 2: formatNumber in React islands vs Astro templates
Astro templates run server-side at build time; React islands run in the browser. A helper in
`site/src/lib/formatNumber.ts` can be imported in both contexts. However, `CommuneRankingTable.astro`
and `ComparableCommune.astro` are Astro components — import the helper directly in frontmatter
(`---`). For React islands (`ResultPanel.tsx`, `ComparatorIsland.tsx`), import from the same
module (Vite bundles it into the island chunk).

### Pitfall 3: ?cut= guard timing
`MapIsland.tsx` sets `communeIndex` state after a parallel fetch with TopoJSON + map-payload.
The `focusCut` URL-param reading happens inside the same `useEffect` that runs after `mapReady`.
By the time this effect runs, `communeIndex` state may not yet be set (race). Guard against this:
check `communeIndex` in state OR validate against the raw index array before state is set.
Simplest: validate with a regex `if (/^\d{5}$/.test(focusCut))` (all Chilean CUTs are 5-digit
integers). This excludes clearly invalid params without waiting for the index.

### Pitfall 4: Astro `<script>` interpolation
`BaseLayout.astro` comment (line 9) already documents this: `{expr}` inside `<script>` renders
literally. Skip-link and JSON-LD additions use `set:html` or `is:inline` with prop passing.
No raw template interpolation inside `<script>` tags.

### Pitfall 5: OneDrive build+validate chaining
`site/package.json` has separate `"build"` and `"validate"` scripts. Must chain as
`npm run build && npm run validate` in a single shell invocation — do NOT split into separate
Bash tool calls, or `dist/` may vanish between calls (OneDrive sync moves built files).

### Pitfall 6: `FAMILY_SLUGS.vida.en === 'homicide'` in rankings/by-crime loops
`site/src/pages/rankings.astro` line 69: `Object.entries(FAMILY_SLUGS).map(...)` includes `vida`.
Adding the 16-region links is a separate section and unaffected. But any new `byFamily` loop
added to rankings for visuals must `filter(([key]) => key !== 'vida')` to avoid duplicate
homicide link.

### Pitfall 7: `is-santiago-safe.astro` esPath points to a different ES page
`esPath="/es/mapa-seguridad-santiago/"` (line 72) — the ES pair is not a direct translation of
the editorial page (it's the Santiago safety map page). This is existing behavior, not a bug to
fix in this phase. Do not change `esPath` or hreflang.

---

## Code Examples

### Creating `site/src/lib/formatNumber.ts`
```typescript
// Source: codebase pattern from ResultPanel.tsx line 319 (already locale-aware)
export function formatRate(value: number, locale: 'en' | 'es'): string {
  return Math.round(value).toLocaleString(locale === 'es' ? 'es-CL' : 'en-US');
}

export function formatDecimal(
  value: number,
  locale: 'en' | 'es',
  decimals = 1
): string {
  return value.toLocaleString(locale === 'es' ? 'es-CL' : 'en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
```

### Fixing ResultPanel.tsx displayRate (lines 200, 305, 393)
```typescript
// Before:
const displayRate = rate !== null ? Math.round(rate).toLocaleString('es-CL') : '—';
// <div className="stat-big">~{displayRate}</div>

// After:
import { formatRate } from '../../lib/formatNumber';
const displayRate = rate !== null ? formatRate(rate, lang) : '—';
// <div className="stat-big">{displayRate}</div>  // remove ~
```

### Chile continental bbox for MapIsland.tsx map init
```typescript
// Source: [ASSUMED] standard GeoJSON bbox for Chile continental territory
// Replaces line 125: map.setView([-35.7, -71.8], 5)
map.fitBounds([[-55.9, -75.7], [-17.5, -66.4]], { padding: [20, 20] });
map.setMaxBounds([[-60, -80], [-14, -60]]);
map.setMinZoom(4);
```

### Skip link in BaseLayout.astro
```html
<!-- Add as first child of <body>, before PageHeader -->
<a href="#main-content" class="skip-link">Skip to main content</a>
<!-- In global.css: -->
<!-- .skip-link { position:absolute; top:-40px; left:0; padding:8px; background:var(--primary);
     color:var(--card); z-index:1000; }
     .skip-link:focus { top:0; } -->
<!-- Change <main class="page-content"> to <main id="main-content" class="page-content"> -->
```

### Classifier traffic filter addition (classifier.py SYSTEM_PROMPT)
```python
# Add to Rules section (after line 110, before closing """):
"Traffic accidents, road collisions, and vehicle crashes are NOT crime incidents, "
"even if they result in fatalities. Set confidence to 0.0 for articles primarily "
"about traffic accidents."
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build | Yes | (project-standard) | — |
| `npx astro build` | Build verification | Yes | via package.json | — |
| `npx astro preview --port 4321 --host` | Preview server | Yes | confirmed in MEMORY.md | — |
| BrowserOS MCP | Visual verification | Yes (inline only) | — | Manual screenshots |
| Python 3.12+ | Pipeline classifier fix | Yes | (project-standard) | — |
| `npm run validate` | Post-build validation | Yes | `site/scripts/validate/all.mjs` | — |

**Chain command (OneDrive constraint):**
```bash
npm run build && npm run validate
# or for preview:
npm run build && npx astro preview --port 4321 --host
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Frontend build check | `npm run build` (Astro static build) |
| Validators | `npm run validate` (`site/scripts/validate/all.mjs`, 9 validators) |
| Preview server | `npx astro preview --port 4321 --host` |
| BrowserOS | Screenshots to `C:\Users\Carlo\bos-shots\` (no spaces), mobile via 375px iframe |
| Python pipeline tests | `pytest` in `pipeline/` |

### Phase Requirements → Test Map

| Req ID | Fix | Test Type | Verification Command / Method |
|--------|-----|-----------|-------------------------------|
| P0-1 | 404.astro created | Build output + HTTP status | `grep -r "404" dist/ --include="*.html" -l` confirms `dist/404.html` exists; BrowserOS `GET /404-test-nonexistent/` → confirm status is 404 (not 200) |
| P0-3 | favicon.svg + <link> | Build output grep | `grep -n "favicon" dist/index.html` must show two `<link rel="icon">` tags; `ls dist/favicon.*` |
| P0-2 | Hamburger at 1100px | BrowserOS visual | Screenshot at 375px iframe (hamburger) + screenshot at ~800px proxy (nav collapsed) |
| P1-1 | formatNumber helper | Build output grep + visual | `grep -n "es-CL" site/src/components/map/ResultPanel.tsx` must return 0 after fix; BrowserOS EN map panel shows "4,984" not "4.984" |
| P1-3 | fitBounds + pin color | BrowserOS visual | Open `/map/` at full width: Chile must be centered with minimal ocean. Pin color must be purple. Mobile 375px: legend collapsible visible. |
| P1-2 | Compare labels + URL | BrowserOS visual + URL check | Compare Santiago vs Las Condes → URL shows `?a=13101&b=13109`; card shows "Composite Crime Index" label |
| P1-4 | Year badges + no tilde | BrowserOS visual | Open map, click a commune: no `~` before rate; year badge visible on composite and rate blocks |
| P1-5 | Editorial visuals | Build output grep | `grep -c "<table\|sparkline" dist/is-santiago-safe/index.html` must be > 0 |
| P1-6 | News h2 headings | Build output grep | `grep -c "<h2" dist/news/index.html` must be > 0 |
| P1-6 | Classifier filter | Python unit test | Add `test_traffic_accident_rejected` to `pipeline/tests/` — classify a traffic headline, assert return is None |
| P2-1 | aria-label on pins | BrowserOS a11y | Open map, enable news layer, inspect a marker; title attribute must contain incident title |
| P2-1 | Skip link | Build output grep | `grep "skip-link" dist/index.html` |
| P2-2 | WebSite JSON-LD | Build output grep | `grep "WebSite" dist/index.html` |
| P2-2 | Rankings region links | Build output grep | `grep -c "<a href=\"/region/" dist/rankings/index.html` must be ≥ 16 |

### Wave 0 Gaps
- [ ] `pipeline/tests/test_classifier_traffic.py` — new test for traffic accident rejection
- [ ] `site/src/lib/formatNumber.ts` — new module (no tests required; pure Intl.NumberFormat wrapper)
- [ ] `site/public/favicon.svg` + `site/public/favicon.ico` — static assets (no test; verified by grep)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Cloudflare Pages serves `dist/404.html` with real 404 status when no `_redirects` catch-all exists | P0-1 | Low risk — CF Pages docs document this behavior; verified no `_redirects` file exists |
| A2 | Chile continental bbox `[[-55.9,-75.7],[-17.5,-66.4]]` is correct for `fitBounds` | P1-3 map init | Map would be off-center if wrong; easy to adjust in preview |
| A3 | `CommuneRankingTable.astro` accepts a `locale` prop | P1-1 | Build would error if wrong; check `CommuneRankingTable.astro` prop interface before wiring |
| A4 | `region/[slug].astro` region slugs map cleanly to a discoverable pattern in `data/cead/regions/` | P2-2 | Planner must verify slug generation pattern from existing region pages |

---

## Open Questions

1. **`ev-dot` CSS color in `map.css`**
   - What we know: `IncidentPinLayer.ts` uses `className: ''` and `html: '<div class="ev-dot"></div>'`. The `.ev-dot` class is defined in `map.css`.
   - What's unclear: exact current color to confirm it overlaps with orange choropleth.
   - Recommendation: Read `site/src/components/map/map.css` and confirm current `.ev-dot` fill before choosing the replacement color.

2. **`ComparatorIsland.tsx` URL sync — slug vs CUT**
   - What we know: pre-generated `/compare/x-vs-y/` pages use commune slugs (from `[pair].astro`). The island uses CUT codes internally.
   - What's unclear: should `?a=` params use CUT or slug for URL sync?
   - Recommendation: Use CUT codes for `?a=&b=` (simpler to decode back to commune on mount); the pre-generated pages at `/compare/x-vs-y/` are a separate SEO surface and don't need to match the URL sync format.

3. **Skip link `outline` override location**
   - What we know: global.css has correct `:focus-visible` rule. The diagnostic saw `outline:none` on computed style.
   - What's unclear: which component's `<style>` overrides it.
   - Recommendation: Run `grep -rn "outline" site/src --include="*.astro" --include="*.tsx" --include="*.css"` to find all overrides during Wave 0.

---

## Sources

### Primary (HIGH confidence — direct codebase reads)
- `site/src/layouts/BaseLayout.astro` — confirmed no favicon `<link>`, no WebSite JSON-LD
- `site/src/components/PageHeader.astro` — confirmed hamburger breakpoint at `640px` (4 occurrences)
- `site/src/components/map/ResultPanel.tsx` — confirmed hardcoded `'es-CL'`, tilde prefix, COMPOSITE_YEAR=2024
- `site/src/islands/ComparatorIsland.tsx` — confirmed no URL sync, per-family trend uses commune-level trend, no "Composite Crime Index" label, `toFixed(2)` on homicide
- `site/src/pages/news.astro` — confirmed `<div class="incident-title">` (not heading)
- `site/src/components/map/IncidentPinLayer.ts` — confirmed no aria-label/title on markers
- `site/src/pages/rankings.astro` — confirmed "By region" section has no links
- `pipeline/news/classifier.py` — confirmed system prompt has no traffic accident exclusion
- `site/src/components/Sparkline.astro` — confirmed static SVG, zero JS, reusable
- `site/src/lib/data.ts` — confirmed `loadCommune`, `loadIndex`, `loadNationalAverage` available at build time
- `site/src/styles/global.css` — confirmed `:focus-visible` rule exists (lines 166–170)
- `site/public/` listing — confirmed NO `_redirects`, NO `favicon.ico`, NO `404.html`

### Secondary
- [ASSUMED] Cloudflare Pages 404 behavior documented at developers.cloudflare.com/pages — absent `404.html` causes SPA-fallback behavior; present `404.html` in dist causes real 404 status

## Metadata

**Confidence breakdown:**
- Defect locations: HIGH — all mapped to exact file:line from direct reads
- Fix approaches: HIGH — follow existing codebase patterns
- CF Pages 404 behavior: ASSUMED (training knowledge, architecture matches documented behavior)

**Research date:** 2026-07-02
**Valid until:** 2026-08-01 (stable codebase; only invalidated by concurrent feature work on same files)
