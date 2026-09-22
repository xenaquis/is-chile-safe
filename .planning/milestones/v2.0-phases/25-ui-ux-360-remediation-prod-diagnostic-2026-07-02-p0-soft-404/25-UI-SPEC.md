---
phase: 25
slug: ui-ux-360-remediation-prod-diagnostic-2026-07-02-p0-soft-404
status: approved
reviewed_at: 2026-07-02
shadcn_initialized: false
preset: none
created: 2026-07-02
---

# Phase 25 — UI Design Contract
## UI/UX 360 Remediation (prod diagnostic 2026-07-02)

> Visual and interaction contract for all P0/P1/P2 fixes in the 2026-07-02 production audit.
> This is a REMEDIATION phase — the design system is inherited, not invented here.
> Source: `.planning/UI-360-DIAGNOSTIC-260702.md` + `.planning/phases/25-…/25-CONTEXT.md`

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (bespoke CSS custom-properties, no shadcn) |
| Preset | not applicable |
| Component library | none (hand-rolled components in `src/components/`) |
| Icon library | inline SVG only (no external icon library) |
| Font | Nunito Sans 400 + 700 (Google Fonts, already in `global.css`) |

Source: `site/src/styles/global.css` — tokens confirmed in codebase, not invented.

---

## Spacing Scale

All tokens already declared in `global.css :root`. Reuse exclusively — do not add new values.

| Token | Value | Usage |
|-------|-------|-------|
| --xs | 4px | Icon gaps, dot margins, inline badge padding |
| --sm | 8px | Compact element spacing, chip gap, badge row gap |
| --md | 16px | Default padding, section internal spacing |
| --lg | 24px | Section padding, header side padding |
| --xl | 32px | Layout gaps |
| --2xl | 48px | Major section breaks |
| --3xl | 64px | Header height (fixed), page-level spacing |

Exceptions:
- Tooltip trigger: 18×18px (existing, approved in Phase 3).
- Legend compact overlay: 12px font-size (approved named exception in `map.css`).
- Nav-link horizontal padding: 14px (non-multiple of 4, existing, do not change).
- Touch targets: minimum 44×44px for all buttons and interactive chips (existing `.chip` and `.zoom-ctl button` and `.panel-close` patterns — enforce uniformly in new elements).

---

## Typography

All roles already declared in `global.css`. Do not add new sizes or weights.

| Role | Size | Weight | Line Height | CSS Token |
|------|------|--------|-------------|-----------|
| Display (h1) | 28px | 700 | 1.15 | `--text-display` / `--weight-strong` |
| Heading (h2, h3) | 20px | 700 | 1.25 | `--text-heading` / `--weight-strong` |
| Body (p, default) | 16px | 400 | 1.5 | `--text-body` / `--weight-body` |
| Label (.label, nav, chips, badges) | 14px | 700 | 1.4 | `--text-label` / `--weight-strong` |

**Phase-25-specific typography rules:**

1. **News card titles** — must be `<h2>` (or `<h3>` inside a dated group `<h2>`) at heading size (20px/700). Currently `<div>` — fix is semantic only, no visual restyling required.
2. **Year badges on map panel** — use label size (14px/700) in a `<span class="year-badge">` styled as inline pill. See Year Badge spec below.
3. **404 page** — h1 at display size (28px/700), body paragraph at body size (16px/400).
4. **Editorial visual tables** (rate tables on `/is-santiago-safe/` etc.) — thead: label (14px/700); tbody: label (14px/400 for data cells, 700 for commune name column); caption: label (14px/400, `--muted` color).
5. **Sparkline axis labels** — existing `sparkline-axis` class (12px/muted) — reuse, do not change.

---

## Color

All brand tokens already in `global.css :root`. Do not add new hex values — reference existing tokens.

| Role | Token / Hex | Usage |
|------|-------------|-------|
| Dominant (60%) | `--bg` #f5f8f8 | Page background, map topbar background |
| Secondary (30%) | `--card` #ffffff | Cards, panels, header, dropdowns, legend |
| Accent (10%) | `--primary` #0f766e | See reserved-for list below |
| Ink | `--ink` #1c2a2b | All body text, headings |
| Muted | `--muted` #5d6c6d | Labels, meta text, axis labels, attribution |
| Border | `--line` #e2e9e8 | Dividers, card borders, input borders |
| Destructive / trend-up | `--trend-up` / `--s5` #c96b5a | Destructive actions; trend "↑ worsening" |
| Trend down (improvement) | `--trend-down` #0f766e | Trend "↓ improving" (same as --primary) |
| Trend stable | `--trend-stable` #5d6c6d | Trend "→ stable" |
| Incidence scale | `--s1`…`--s5` (#dbeef0 → #c96b5a) | Choropleth fills and LevelChip dots only |

Accent (`--primary`) reserved for:
- CTA buttons (`panel-cta`, primary action buttons on 404 page)
- Active nav link hover and active lang-btn
- Active chip state (`.chip.active`)
- Focus-visible outlines globally (already `*:focus-visible` rule in `global.css`)
- Tooltip trigger border and color
- Wordmark SVG glyph
- User geolocation dot (`.user-dot`)
- `ci-caveat` left-border accent
- Skip-to-main link background (new, P2)

**Incident pin color — NEW (P1-3):**
- Current: `#e8a05c` (`.ev-dot`) — same orange as `--s4` choropleth level → confuses figure/fondo.
- New color: `#6d28d9` (CSS var `--pin` to be added to `:root` in `global.css`). This purple is distinct from all 5 incidence levels and from `--primary`. Named `--pin`.
- New shape: keep 14×14px circle; ADD a white 2px border (`border: 2px solid #ffffff`) to lift the pin off the polygon fill visually. This matches the `user-dot` approach.
- Mini-dot in legend/topbar (`.ev-dot-mini`): update to same `--pin` color.
- When incident layer is active, legend must show a pin row: swatch = 10×10px filled circle in `--pin` + label "Reported incidents / Incidentes reportados".

Destructive color: `--trend-up` #c96b5a. Used exclusively for: trend arrows indicating worsening crime, delete/remove actions (none exist in this phase). Not used decoratively.

---

## Breakpoints

The codebase currently uses 640px and 1024px. Phase 25 adds two intermediate breakpoints to fix the tablet overflow. These are the ONLY new breakpoint values allowed.

| Breakpoint | Value | Purpose |
|------------|-------|---------|
| `mobile` (existing) | < 640px | Single column, hamburger nav |
| `tablet-sm` (NEW) | ≤ 900px | Stack home `.lead-table-col` to single column |
| `tablet` (NEW) | ≤ 1100px | Collapse `csm-nav` to hamburger (currently collapses at 640px) |
| `desktop-sm` (existing) | ≥ 1024px | Desktop max-width + padding |

**Hamburger nav rule change:**
- Current: nav shows at `min-width: 640px`.
- New: nav shows at `min-width: 1100px`. Hamburger visible up to 1099px. This is a CSS-only change in `PageHeader.astro` `<style>` — shift all three `@media (min-width: 640px)` blocks inside the header to `@media (min-width: 1100px)`.
- The nav-toggle-input `display: none` and `.nav-toggle-btn display: none` both shift to 1100px.

**Home lead-table stacking rule:**
- The two `.lead-table-col` divs (currently 504px each) must wrap at ≤ 900px.
- Implementation: parent flex container → add `flex-wrap: wrap` + breakpoint: `@media (max-width: 900px) { .lead-table-col { width: 100%; } }`.

**Map filter pills stacking (P1-3):**
- Mode toggle pills (Index / By crime) overlap search box at ≤ 480px.
- At ≤ 480px: `.map-topbar-row1` wraps to column; `.mode-toggle` position changes from `position: absolute; top: 8px; right: 16px` to `position: static` and appears as a second row inside the topbar.

---

## Component Contracts

### Favicon (P0-3)

- **Primary:** `/public/favicon.svg` — SVG using the existing wordmark PinGlyph motif from `PageHeader.astro` (circle cx=11 cy=9 r=5 fill=`#0f766e`, inner ellipse fill=`white`, tail path fill=`#0f766e`) on transparent background, viewBox="0 0 22 22".
- **Fallback:** `/public/favicon.ico` — 32×32 and 16×16 combined ICO (generate from SVG via `sharp` or equivalent build script).
- **Apple touch icon:** `/public/apple-touch-icon.png` — 180×180px, same glyph on `#f5f8f8` background (no transparency).
- **Layout injection** (in base layout `<head>`):
  ```html
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  ```

### 404 Page (P0-1)

- **File:** `site/src/pages/404.astro` (Astro automatically serves with HTTP 404).
- **Remove:** any `/* /index.html 200` catch-all from `public/_redirects`. After removal, Cloudflare Pages serves `404.html` with real 404 status.
- **Layout:** use existing `BaseLayout` with `pageType="editorial"`.
- **Content (EN):** h1 "Page not found", body "The page you were looking for doesn't exist or has moved.", links: "Go to home", "Explore the map", "View rankings".
- **Content (ES):** h1 "Página no encontrada", body "La página que buscas no existe o fue movida.", links: "Ir al inicio", "Explorar el mapa", "Ver rankings".
- **No indexing:** the page gets a real 404 status from Cloudflare — no noindex meta needed (Googlebot ignores 404 pages by default). Do NOT add `<meta name="robots" content="noindex">` (redundant and signals incorrectly for 200 soft-404 pattern we're eliminating).
- **CTA buttons:** use `<a class="panel-cta">` pattern (existing, 44px height, `--primary` bg, white text, 8px border-radius). Render as inline-flex row at ≥ 640px, stacked column at < 640px.

### Nav Copy Fix (P0-2 / P2-3)

- "Crime type glossary" → **"Glossary"** (EN) / **"Glosario"** (ES). Change in `i18n.ts` `glossary_link` key. No CSS change.

### Year Badge (P1-4)

New inline component for map result panel grouping:

```
.year-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 var(--sm);            /* 0 8px */
  border-radius: 4px;
  background: var(--line);         /* #e2e9e8 */
  color: var(--muted);             /* #5d6c6d */
  font-size: var(--text-label);    /* 14px */
  font-weight: var(--weight-strong); /* 700 */
  margin-left: var(--xs);          /* 4px */
}
```

Usage: inline after section label, e.g. `<span>Composite Crime Index</span> <span class="year-badge">2024</span>`.

Tooltip for year divergence: reuse existing `<details class="rate-tooltip">` pattern with the `?` trigger and `.tooltip-body` at `bottom: calc(100% + 4px)`. Tooltip copy:
- EN: "Why do years differ? The Composite Index uses 2024 as the latest complete CEAD year. The incident rate uses 2025 (partial data). Rankings may differ because they come from two calculation methods."
- ES: "¿Por qué difieren los años? El Índice Compuesto usa 2024 como el año completo más reciente de CEAD. La tasa de incidentes usa 2025 (datos parciales). Los rankings pueden diferir al provenir de dos métodos de cálculo."

Drop `~` prefix from all numbers in the result panel. No replacement character — display the number directly.

### Map Legend — Incident Layer Entry (P1-3)

When incidents layer is active, append a row to the legend below the 5 choropleth bands:

```html
<div class="legend-band-row">
  <span class="legend-swatch" style="background: var(--pin); border-radius: 50%;"></span>
  <div class="legend-band-label">
    <span class="legend-qual-label">Reported incidents</span>  <!-- EN -->
    <!-- or: Incidentes reportados (ES) -->
  </div>
</div>
```

### Collapsible Mobile Legend (P1-3)

At ≤ 480px:
- Wrap legend in `<details>` with `<summary class="legend-title">` as toggle (reuse `.tooltip-trigger` styles for the `<summary>` marker).
- Default state: collapsed (`<details>` closed). Opens on tap.
- Summary label: "Crime Index ▸" / "Índice delictivo ▸" (closed), "Crime Index ▾" / "Índice delictivo ▾" (open).
- Use CSS `details[open] .legend-body { display: block; }` (same pattern as existing `.tooltip-body`).
- Min-width 100px; max-width 160px. Remove `min-width: 140px` at this breakpoint.

### Compare Island — Composite Crime Index Label (P1-2)

- Big number (e.g. "39.0") must be followed by:
  - Label: `<span class="stat-unit">Composite Crime Index</span>` / `<span class="stat-unit">Índice Compuesto de Criminalidad</span>`
  - Level chip: `Very High` / `Muy Alto` must appear ONLY in context of the index label — never floating standalone.
  - Attribution link: `<a href="/methodology/">` / `<a href="/es/metodologia/">` — `(what is this?)` / `(¿qué es esto?)` at label size 14px, `--muted` color.
- Chile avg card: must show the index value (not empty). If not available, show "—" not a blank.

### Compare Island — URL Sync (P1-2)

- On selection of commune A or B: `history.replaceState(null, '', '?a={slug-a}&b={slug-b}')`.
- On page load: read `?a=` and `?b=` params, pre-fill the search boxes and trigger comparison.
- Slug format must match existing `/compare/{slug-a}-vs-{slug-b}/` page slug pattern (from Phase 21).
- This is a client-side JS addition inside the existing CompareIsland React component.

### Compare Island — Popular Comparison Chips (P1-2, empty state)

Empty state layout: below the two search inputs, show a row of suggestion chips.

```
.compare-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sm);
  margin-top: var(--md);
}
.compare-chip {
  /* same as .chip but smaller — 36px height */
  display: inline-flex;
  align-items: center;
  height: 36px;
  border-radius: 999px;
  padding: 0 var(--md);
  font-size: var(--text-label);
  font-weight: var(--weight-strong);
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--ink);
  cursor: pointer;
  white-space: nowrap;
}
.compare-chip:hover {
  background: var(--bg);
  border-color: var(--primary);
  color: var(--primary);
}
```

Pairs (both EN/ES):
1. Santiago vs Las Condes (EN) / Santiago vs Las Condes (ES — same commune names)
2. Providencia vs Ñuñoa
3. Viña del Mar vs Valparaíso

Chip label format: `{Commune A} vs {Commune B}`. On click: fill both inputs and trigger comparison.

### Editorial Visuals — Static Tables (P1-5)

These tables are generated at build time from `public/data` JSON. They must be static HTML in the output — no client-side rendering.

**Table structure (top/bottom 10 commune rate table):**

```html
<figure class="rate-table-figure">
  <figcaption class="rate-table-caption">{caption}</figcaption>
  <table class="rate-table">
    <thead>
      <tr>
        <th scope="col">#</th>
        <th scope="col">Commune / Comuna</th>
        <th scope="col">Rate per 100k / Tasa por 100k</th>
        <th scope="col">Trend / Tendencia</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="rate-rank">{n}</td>
        <td class="rate-commune"><a href="/{locale}/commune/{slug}/">{name}</a></td>
        <td class="rate-value">{value formatted by locale}</td>
        <td class="rate-trend">{↑ / ↓ / →}</td>
      </tr>
    </tbody>
  </table>
  <p class="rate-table-source">Source: CEAD – Ministry of Interior, {year}. Reported cases per 100,000 inhabitants.</p>
</figure>
```

**Table CSS (new, to be added to relevant editorial page `<style>` block):**

```css
.rate-table-figure { margin: var(--lg) 0; overflow-x: auto; }
.rate-table-caption {
  font-size: var(--text-label);
  font-weight: var(--weight-strong);
  color: var(--ink);
  margin-bottom: var(--sm);
}
.rate-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-label);
}
.rate-table th {
  font-weight: var(--weight-strong);
  color: var(--muted);
  text-align: left;
  padding: var(--xs) var(--sm);
  border-bottom: 2px solid var(--line);
}
.rate-table td {
  padding: var(--xs) var(--sm);
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  vertical-align: middle;
}
.rate-rank { color: var(--muted); width: 2rem; }
.rate-commune a { color: var(--primary); font-weight: var(--weight-strong); }
.rate-value { font-weight: var(--weight-strong); text-align: right; }
.rate-trend { text-align: center; }
.rate-table-source {
  font-size: var(--text-label);
  color: var(--muted);
  margin-top: var(--xs);
}
```

**Trend arrow colors in tables:** ↑ = `color: var(--trend-up)` / ↓ = `color: var(--trend-down)` / → = `color: var(--trend-stable)`.

**Sparkline SVG (static, inline):**
- Reuse the existing `Sparkline.astro` component (already used on commune pages).
- Dimensions: 180×40px for editorial page context (inline within prose).
- Stroke color: `--primary`, stroke-width: 2.
- No axes — these are decorative trend lines. Pair with the rate table above.
- Generation approach: pass `values` array to `Sparkline.astro` — already designed for this pattern.

### News Page — Semantic Headings (P1-6)

Current: all 129 items in a `<div>` list with no heading structure. Zero `<h2>` or `<h3>` on the page.

Required structure after fix:

```html
<h1>Recent Crime Incidents in Chile</h1>  <!-- already exists or add -->

<!-- Option A: date grouping (preferred) -->
<section>
  <h2 class="news-date-group">July 2, 2026</h2>
  <article class="news-card">
    <h3 class="news-title"><a href="{source-url}">{title}</a></h3>
    <p class="news-meta">{commune chip} · {type chip} · {source} · {date}</p>
  </article>
</section>

<!-- Option B: flat list (fallback if date grouping is complex) -->
<ul class="news-list">
  <li class="news-card">
    <h2 class="news-title"><a href="{source-url}">{title}</a></h2>
    <p class="news-meta">…</p>
  </li>
</ul>
```

Implementation: Option A (date grouping) is preferred per the diagnostic. Group by `published_date` descending, emit `<h2>` per date group, `<h3>` per article within.

**Crime type chip on news card:**

```html
<span class="news-type-chip">{crime_type_label}</span>
<span class="news-commune-chip"><a href="/{locale}/commune/{slug}/">{commune_name}</a></span>
```

```css
.news-type-chip, .news-commune-chip {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 var(--sm);
  border-radius: 4px;
  font-size: 12px;   /* named exception: compact badge in dense news list */
  font-weight: 700;
  background: var(--line);
  color: var(--ink);
  margin-right: var(--xs);
}
.news-commune-chip a {
  color: var(--ink);
  text-decoration: none;
}
.news-commune-chip:hover {
  background: var(--bg);
}
```

**"View commune" link text:** replace with `"View {CommuneName}"` / `"Ver {NombreComuna}"` — never a bare "View commune" that hides the destination.

### Map Panel — Number Formatting (P1-1)

A new utility function `formatNumber(value: number, locale: string): string` using `Intl.NumberFormat`:
- EN locale: thousands separator = comma, decimal = period. Example: `4,984`.
- ES locale: thousands separator = period, decimal = comma. Example: `4.984`.
- Implementation: `new Intl.NumberFormat(locale === 'es' ? 'es-CL' : 'en-US', { maximumFractionDigits: 1 }).format(value)`.
- Rate display: 1 decimal place for all rates. Homicide rate also 1 decimal (not 2) for consistency.
- No `~` prefix ever. Remove from all call sites.
- Consumers to audit: `MapIsland.tsx` (result panel), `CompareIsland.tsx`, ES commune table "Similar Communes", ES hero KPI.

### Accessibility (P2-1)

**Incident marker aria-labels:**
- Each Leaflet `L.divIcon` marker for incidents: add `aria-label="{incident.title} — {incident.commune}"` on the container element.
- Implementation: `L.marker(latlng, { icon: L.divIcon({ html: `<div class="ev-dot" role="img" aria-label="${title} — ${commune}"></div>` }) })`.
- Fallback: if aria-label on divIcon is not supported cleanly, use `aria-hidden="true"` on the marker and add an `<ul class="sr-only">` incidents list on the page (outside the map div).

**Skip link (P2-1):**
```html
<!-- First child of <body> in BaseLayout -->
<a href="#main-content" class="skip-link">Skip to main content</a>
<!-- ES: Ir al contenido principal -->
```
```css
.skip-link {
  position: absolute;
  top: -40px;
  left: var(--md);
  background: var(--primary);
  color: #ffffff;
  padding: var(--xs) var(--md);
  border-radius: 4px;
  font-size: var(--text-label);
  font-weight: var(--weight-strong);
  z-index: 9999;
  text-decoration: none;
  transition: top 0.1s;
}
.skip-link:focus {
  top: var(--sm);
}
```

**Focus-visible:** `global.css` already has `*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`. Verify no override `outline: none` on `a` without `:focus-visible` guard. If found, remove unconditional `outline: none` on `a` elements.

### Rankings Page — Region Links (P2-2)

In the "By region" section of `/rankings/` (and `/es/rankings/`), the text "usa el mapa" / "use the map" must be replaced with a complete list of the 16 region links:

```html
<ul class="region-links-list">
  <li><a href="/{locale}/region/{region-slug}/">{region-name}</a></li>
  <!-- × 16 regions -->
</ul>
```

Style: no custom CSS needed — inherits base `<ul>` and `<a>` styles. No bullets: `list-style: none`.

### Region KPI Directional Label (P2-3)

Current: `#13 of 16` without direction.
Required: `#13 of 16 (1 = highest reported)` in the same KPI display element.
EN: `(1 = highest reported)` / ES: `(1 = mayor incidencia reportada)`.
Font: `--text-label`, `--muted` color, inline after the rank number.

### Region Evolution Chart Title (P2-3)

Current: `(2005–2025)` but chart includes 2026 partial bar.
Required: `(2005–2026*)` with asterisk. Add footnote below chart: `* 2026: partial year data (Jan–Jun)` / `* 2026: año parcial (ene–jun)`.

### Plural Fix (P2-3)

Pattern: `n === 1 ? 'case' : 'cases'` / `n === 1 ? 'caso' : 'casos'`. Apply wherever `(n cases)` appears in MapIsland result panel and CompareIsland.

### Placeholder Map Slot (P2-3)

The gray box with a pin on region pages that looks like a failed map load. Style as an intentional CTA card:

```css
.map-placeholder-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sm);
  height: 200px;
  background: var(--line);
  border-radius: var(--radius);
  border: 1.5px dashed var(--muted);
  color: var(--muted);
  font-size: var(--text-body);
  font-weight: var(--weight-strong);
  text-decoration: none;
}
.map-placeholder-card:hover {
  background: var(--bg);
  color: var(--primary);
  border-color: var(--primary);
}
```

Replace current ambiguous gray box with `<a href="/map/?region={region-slug}" class="map-placeholder-card">`. Label: "View interactive map →" / "Ver mapa interactivo →".

### JSON-LD Additions (P2-2)

Add to home page `<head>`:
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Chile Safety Map",
  "url": "https://ischilesafe.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://ischilesafe.com/map/?search={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
```
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Chile Safety Map",
  "url": "https://ischilesafe.com",
  "description": "Interactive crime data map of Chile using official CEAD statistics."
}
```

---

## Copywriting Contract

Editorial constraint: never label territories safe/dangerous in absolute terms. "Very High" etc. must always be attributed to the named index.

| Element | EN | ES |
|---------|----|----|
| 404 page h1 | "Page not found" | "Página no encontrada" |
| 404 page body | "The page you were looking for doesn't exist or has moved." | "La página que buscas no existe o fue movida." |
| 404 CTA 1 | "Go to home" | "Ir al inicio" |
| 404 CTA 2 | "Explore the map" | "Explorar el mapa" |
| 404 CTA 3 | "View rankings" | "Ver rankings" |
| Skip link | "Skip to main content" | "Ir al contenido principal" |
| Compare empty state heading | "Compare any two communes" | "Compara dos comunas" |
| Compare empty state body | "Search for a commune above, or pick a popular comparison below." | "Busca una comuna arriba, o elige una comparación popular a continuación." |
| Compare level chip attribution | "Composite Crime Index" | "Índice Compuesto de Criminalidad" |
| Compare attribution link | "(what is this?)" | "(¿qué es esto?)" |
| Compare trend tooltip (all →) | "Trend data unavailable for this commune." | "Datos de tendencia no disponibles para esta comuna." |
| Year badge tooltip title | "Why do years differ?" | "¿Por qué difieren los años?" |
| Year badge tooltip body | "The Composite Index uses 2024 as the latest complete CEAD year. The incident rate uses 2025 (partial data). Rankings may differ because they use two different calculation methods." | "El Índice Compuesto usa 2024 como el último año completo de CEAD. La tasa de incidentes usa 2025 (datos parciales). Los rankings pueden diferir al usar dos métodos de cálculo distintos." |
| Nav "Glossary" | "Glossary" | "Glosario" |
| Incident legend row | "Reported incidents" | "Incidentes reportados" |
| Mobile legend toggle (closed) | "Crime Index ▸" | "Índice delictivo ▸" |
| Mobile legend toggle (open) | "Crime Index ▾" | "Índice delictivo ▾" |
| Map placeholder CTA | "View interactive map →" | "Ver mapa interactivo →" |
| Region KPI direction | "(1 = highest reported)" | "(1 = mayor incidencia reportada)" |
| Region chart partial year footnote | "* 2026: partial year data (Jan–Jun)" | "* 2026: año parcial (ene–jun)" |
| Rate table source attribution | "Source: CEAD – Ministry of Interior, {year}. Reported cases per 100,000 inhabitants." | "Fuente: CEAD – Ministerio del Interior, {year}. Casos reportados por 100.000 habitantes." |
| News page h1 | "Recent Crime Incidents in Chile" | "Incidentes delictivos recientes en Chile" |
| Rankings region list header | "By region" | "Por región" |
| "(1 cases)" plural fix (EN) | "{n} case" (n=1) / "{n} cases" (n≠1) | "{n} caso" (n=1) / "{n} casos" (n≠1) |

Destructive actions in this phase: none. No confirmation dialogs required.

---

## Number Formatting Contract

| Locale | Thousands | Decimal | Example (4984.1) |
|--------|-----------|---------|-----------------|
| en | , (comma) | . (period) | 4,984.1 |
| es | . (period) | , (comma) | 4.984,1 |

- Rates: always 1 decimal place (`maximumFractionDigits: 1, minimumFractionDigits: 0`).
- Rank integers: no decimals.
- Population: no decimals, thousands separator per locale.
- Never rescale rates — values are already per 100,000 inhabitants.
- No `~` prefix anywhere.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable |
| third-party | none | not applicable |

No third-party component registries in this phase. All new UI elements use existing tokens and patterns.

---

## New CSS Additions Summary

All new CSS tokens or classes to be added in this phase:

| Addition | File | Purpose |
|----------|------|---------|
| `--pin: #6d28d9` | `global.css :root` | Incident marker color |
| `.year-badge` | `map.css` | Inline year annotation pill |
| `.skip-link` | `global.css` | Keyboard skip-to-main link |
| `.compare-suggestions` / `.compare-chip` | `CompareIsland.tsx` (inline CSS or module) | Empty-state popular comparisons |
| `.news-type-chip` / `.news-commune-chip` | news page `<style>` | Compact badge on news cards |
| `.rate-table-figure` and sub-classes | editorial page `<style>` | Static rate tables |
| `.map-placeholder-card` | `MapPlaceholderSlot.astro` `<style>` | Intentional CTA card on region pages |
| `.region-links-list` | rankings page `<style>` | No-bullets list for 16 region links |
| `.compare-chip` mobile legend `details/summary` pattern | `map.css` | Collapsible legend on mobile |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
