# Phase 25: UI/UX 360 Remediation — Pattern Map

**Mapped:** 2026-07-02
**Files analyzed:** 18 new/modified files
**Analogs found:** 17 / 18

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `site/src/pages/404.astro` | page | request-response | `site/src/pages/is-santiago-safe.astro` | role-match (editorial static page) |
| `site/public/favicon.svg` | static asset | — | `site/src/components/PageHeader.astro` lines 43–47 (PinGlyph SVG) | exact-source |
| `site/src/lib/formatNumber.ts` | utility | transform | `site/src/lib/data.ts` (module export pattern) + `site/src/components/map/ResultPanel.tsx` line 319 (locale-aware pattern) | role-match |
| `pipeline/tests/test_classifier_traffic.py` | test | — | `pipeline/tests/test_classifier.py` | exact |
| `site/src/layouts/BaseLayout.astro` (modify) | layout | request-response | self — reading existing head/JSON-LD pattern | self |
| `site/src/components/PageHeader.astro` (modify) | component | — | self — 4× `@media (min-width: 640px)` | self |
| `site/src/components/map/ResultPanel.tsx` (modify) | component | request-response | self — existing locale-aware pattern line 319 | self |
| `site/src/islands/ComparatorIsland.tsx` (modify) | island | request-response | self — existing `useEffect` patterns | self |
| `site/src/components/map/MapIsland.tsx` (modify) | island | request-response | self — `map.setView` line 125 | self |
| `site/src/components/map/IncidentPinLayer.ts` (modify) | utility | event-driven | self — `L.marker` line 154 | self |
| `site/src/components/map/map.css` (modify) | style | — | self — `.ev-dot` rule | self |
| `site/src/pages/news.astro` (modify) | page | batch | self — incident list template | self |
| `site/src/pages/rankings.astro` (modify) | page | CRUD | self — "By region" section lines 78–83 | self |
| `site/src/pages/region/[slug].astro` (modify) | page | CRUD | `site/src/pages/is-santiago-safe.astro` (editorial KPI + data pattern) | role-match |
| `site/src/config/i18n.ts` (modify) | config | — | self — `glossary_link` key line 296 | self |
| `pipeline/news/classifier.py` (modify) | service | event-driven | self — SYSTEM_PROMPT Rules block line 105–110 | self |
| `site/src/lib/jsonld.ts` (modify) | utility | transform | self — existing `buildBreadcrumb` / `buildItemList` pattern | self |
| `site/src/pages/is-santiago-safe.astro` (modify) | page | batch | self — editorial page with `loadIndex()` + `Sparkline.astro` pattern | self |

---

## Pattern Assignments

### `site/src/pages/404.astro` (new page, request-response)

**Analog:** `site/src/pages/is-santiago-safe.astro` (editorial static page using EditorialLayout + BaseLayout)

**Imports pattern** (is-santiago-safe.astro lines 11–14):
```astro
import EditorialLayout from '../layouts/EditorialLayout.astro';
import DataCallout from '../components/DataCallout.astro';
import FAQBlock from '../components/FAQBlock.astro';
import { loadCommune, loadNationalAverage, latestCompleteYearRate } from '../lib/data.ts';
```
For 404: only `EditorialLayout` is needed (no data loading).

**Layout invocation pattern** (is-santiago-safe.astro lines 66–73):
```astro
<EditorialLayout
  lang="en"
  title="Is Santiago Safe? Crime Data by Commune — Chile Safety Map"
  description="..."
  enPath="/is-santiago-safe/"
  esPath="/es/mapa-seguridad-santiago/"
  jsonLd={jsonLd}
>
```
For 404 adapt to:
```astro
<EditorialLayout
  lang="en"
  title="Page not found — Chile Safety Map"
  description="The page you were looking for doesn't exist or has moved."
  enPath="/404/"
  esPath="/404/"
  pageType="editorial"
>
```
No `jsonLd` prop — no schema needed for 404.

**CTA button pattern** — existing `.panel-cta` class (see map result panel). Render as:
```html
<a href="/" class="panel-cta">Go to home</a>
<a href="/map/" class="panel-cta">Explore the map</a>
<a href="/rankings/" class="panel-cta">View rankings</a>
```

**Key constraint from UI-SPEC lines 159–163:** Do NOT add `<meta name="robots" content="noindex">` — Cloudflare serves real 404 status, so the page won't be indexed. Adding noindex risks signaling the old 200-soft-404 pattern.

**Bilingual inline approach:** 404 page serves one language (EN primary). Inline both language blocks in the same page separated by `<hr>` since there are no ES/EN route pairs for 404. Alternative: use `lang="en"` throughout with a brief ES note below.

---

### `site/public/favicon.svg` (new static asset)

**Source glyph:** `site/src/components/PageHeader.astro` lines 43–47:
```html
<svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="11" cy="9" r="5" fill="var(--primary)" />
  <ellipse cx="11" cy="9" rx="2" ry="2" fill="white" />
  <path d="M11 14 Q7 18 11 22 Q15 18 11 14Z" fill="var(--primary)" />
</svg>
```
For the standalone SVG file, replace `var(--primary)` with literal `#0f766e` (CSS custom properties don't resolve in standalone SVG files). Keep `viewBox="0 0 22 22"` and `fill="none"` on root, with explicit fills on each element.

**Head injection in BaseLayout** — add after PWA meta block (BaseLayout.astro line 95):
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/x-icon" href="/favicon.ico" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

---

### `site/src/lib/formatNumber.ts` (new utility, transform)

**Module export pattern analog:** `site/src/lib/data.ts` lines 1–26 (module structure, `export function`, `export interface`, no default export, `import` from `node:*` at top).

**Core pattern** (derived from ResultPanel.tsx line 319 — the only already-correct locale-aware call site):
```typescript
// ResultPanel.tsx line 319 — existing correct pattern to generalize:
multiplierNum.toLocaleString(lang === 'es' ? 'es-CL' : 'en-US', ...)
```

**New module to create:**
```typescript
// site/src/lib/formatNumber.ts
// No imports needed — pure Intl.NumberFormat / toLocaleString wrapper.

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

**Call sites to update after creating the module:**

| File | Current | Fix |
|---|---|---|
| `ResultPanel.tsx` line 200 | `Math.round(rate).toLocaleString('es-CL')` | `formatRate(rate, lang)` |
| `ResultPanel.tsx` line 393 | `Math.round(homRate!).toLocaleString('es-CL')` | `formatRate(homRate!, lang)` |
| `ResultPanel.tsx` line 305 | `~{displayRate}` | `{displayRate}` (drop tilde) |
| `Legend.tsx` line 37 | `toLocaleString(lang==='es'?'es-CL':'en-US')` | `formatRate(val, lang)` |
| `CommuneRankingTable.astro` line 78 | `toLocaleString()` (no locale) | `formatRate(val, locale)` |
| `ComparableCommune.astro` line 51 | `toLocaleString()` (no locale) | `formatRate(val, locale)` |
| `ComparatorIsland.tsx` line 620 | `rate.toFixed(1)` | `formatDecimal(rate, lang)` |
| `ComparatorIsland.tsx` line 644 | `homRate!.toFixed(2)` | `formatDecimal(homRate!, lang)` |

Import in React islands (Vite bundles it):
```typescript
import { formatRate, formatDecimal } from '../../lib/formatNumber';
```
Import in Astro components (frontmatter `---`):
```typescript
import { formatRate } from '../lib/formatNumber.ts';
```

---

### `pipeline/tests/test_classifier_traffic.py` (new test file)

**Analog:** `pipeline/tests/test_classifier.py` (exact match — same module structure, same mock pattern)

**Module structure pattern** (test_classifier.py lines 1–17):
```python
"""
pipeline/tests/test_classifier_traffic.py

Tests for traffic accident rejection in pipeline/news/classifier.py.
DeepSeek NEVER called live — all responses mocked via unittest.mock.patch.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pipeline.news import classifier as classifier_mod
from pipeline.news.classifier import classify
```

**Mock response factory pattern** (test_classifier.py lines 18–21):
```python
def _make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(data)
    return mock_resp
```

**Base valid response pattern** (test_classifier.py lines 24–33):
```python
_VALID_RESPONSE = {
    "commune_name": "Carahue",
    "region_hint": "La Araucanía",
    "family": "vida",
    "title_es": "Colisión deja al menos un muerto en Carahue",
    "title_en": "Collision leaves at least one dead in Carahue",
    "summary": "A road collision in Carahue resulted in one fatality.",
    "confidence": 0.85,
}
```

**Test function pattern** (test_classifier.py lines 40–50 — `patch("pipeline.news.classifier.client")` pattern):
```python
def test_traffic_accident_rejected():
    """Classifier must return None for a traffic collision headline (not a crime incident)."""
    data = dict(_VALID_RESPONSE)

    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify(
            "Colisión deja al menos un muerto en Carahue",
            "Un accidente de tránsito en la ruta deja una víctima fatal.",
        )

    # After the SYSTEM_PROMPT traffic-accident rule, the LLM should set confidence=0.0
    # In the test we simulate the post-prompt behavior by testing that confidence=0.0
    # causes rejection:
    assert result is None, "Traffic accident headline must be rejected (confidence=0.0)"
```
Note: the actual rejection comes from `confidence < CONFIDENCE_THRESHOLD` in `classifier.py` line 164. The test should also include a variant where the mock returns `confidence=0.0` explicitly to verify the gate:
```python
def test_zero_confidence_traffic_rejected():
    data = dict(_VALID_RESPONSE, confidence=0.0)
    with patch("pipeline.news.classifier.client") as mock_client:
        mock_client.chat.completions.create.return_value = _make_mock_response(data)
        result = classify("Colisión en Carahue", "Accidente de tránsito.")
    assert result is None
```

---

### `site/src/layouts/BaseLayout.astro` (modify — favicon links + skip link + JSON-LD builders)

**Existing JSON-LD injection pattern** (BaseLayout.astro lines 107–112) — reuse exactly:
```astro
{jsonLd !== null && (Array.isArray(jsonLd) ? jsonLd : [jsonLd])
  .filter(Boolean)
  .map((block) => (
    <script is:inline type="application/ld+json" set:html={JSON.stringify(block).replace(/<\//g, '<\\/')} />
  ))
}
```
New `WebSite` and `Organization` blocks are passed as `jsonLd={[buildWebSite(), buildOrganization()]}` from `index.astro` — no BaseLayout change needed for JSON-LD content itself.

**Favicon link injection** — add after line 95 (`<link rel="manifest" href="/manifest.json" />`):
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="icon" type="image/x-icon" href="/favicon.ico" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

**Skip link** — add as first child of `<body>` (BaseLayout.astro line 114), before `<PageHeader>`:
```html
<a href="#main-content" class="skip-link">
  {lang === 'es' ? 'Ir al contenido principal' : 'Skip to main content'}
</a>
```
Also add `id="main-content"` to `<main class="page-content">` (line 116):
```html
<main id="main-content" class="page-content">
```

**Skip link CSS** — add to `site/src/styles/global.css` (after the `:focus-visible` block, lines 166–173):
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

---

### `site/src/components/PageHeader.astro` (modify — hamburger breakpoint)

**Existing pattern to change** — four occurrences of `@media (min-width: 640px)`:

| Lines | Current | New |
|---|---|---|
| 130–134 | `@media (min-width: 640px) { .csm-nav { display: flex; } }` | `@media (min-width: 1100px) { .csm-nav { display: flex; } }` |
| 204–206 | `@media (min-width: 640px) { .nav-toggle-input { display: none; } }` | `@media (min-width: 1100px) { .nav-toggle-input { display: none; } }` |
| 227–229 | `@media (min-width: 640px) { .nav-toggle-btn { display: none; } }` | `@media (min-width: 1100px) { .nav-toggle-btn { display: none; } }` |
| 255–263 | `@media (min-width: 640px) { .nav-toggle-input:checked ~ .csm-nav { position: static; ... } }` | `@media (min-width: 1100px) { ... }` |

All four must change together (Pitfall 1 in RESEARCH.md).

**Nav label change** — `site/src/config/i18n.ts` line 296:
Current: `glossary_link: 'Crime type glossary'`
New: `glossary_link: 'Glossary'` (EN) and corresponding ES key line 495: `'Glosario'`

---

### `site/src/components/map/ResultPanel.tsx` (modify — formatNumber + year badges + tilde removal)

**Existing locale-aware pattern to generalize** (ResultPanel.tsx line 319 — already correct):
```typescript
multiplierNum.toLocaleString(lang === 'es' ? 'es-CL' : 'en-US', {
  maximumFractionDigits: 1,
})
```

**Tilde pattern to remove** (line 305):
```tsx
// Before:
<div className="stat-big">~{displayRate}</div>
// After:
<div className="stat-big">{displayRate}</div>
```

**Existing tooltip pattern to reuse for year badges** (ResultPanel.tsx line 21 — already imported):
```typescript
import RateTooltipReact from './RateTooltipReact';
```
Reuse `<RateTooltipReact>` component with year-mismatch copy from UI-SPEC lines 191–193.

**COMPOSITE_YEAR constant** (line 41): `const COMPOSITE_YEAR = 2024;` — keep, reference for year badge text.

**Year badge CSS** — add `.year-badge` to `map.css` (UI-SPEC lines 175–188):
```css
.year-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 var(--sm);
  border-radius: 4px;
  background: var(--line);
  color: var(--muted);
  font-size: var(--text-label);
  font-weight: var(--weight-strong);
  margin-left: var(--xs);
}
```

---

### `site/src/islands/ComparatorIsland.tsx` (modify — label, URL sync, chips, trends)

**Existing empty-state pattern** (ComparatorIsland.tsx lines 458–468): the `{s.cmp_empty_heading}` text node.
Add below it:
```tsx
<div className="compare-suggestions">
  {[
    ['Santiago', 'Las Condes'],
    ['Providencia', 'Ñuñoa'],
    ['Viña del Mar', 'Valparaíso'],
  ].map(([a, b]) => (
    <button
      key={`${a}-${b}`}
      className="compare-chip"
      onClick={() => { selectCommune(a); selectCommune(b); }}
    >
      {a} vs {b}
    </button>
  ))}
</div>
```

**URL sync** — add `useEffect` after existing selection logic. Pattern from React islands in codebase uses `window.history.replaceState`:
```typescript
useEffect(() => {
  const a = selected[0]?.id ?? '';
  const b = selected[1]?.id ?? '';
  window.history.replaceState(null, '', `?a=${a}&b=${b}`);
}, [selected]);
```
On mount, read params and pre-select. Use CUT codes (not slugs) per RESEARCH.md open question resolution.

**Composite Crime Index label** (lines 579–583): add above score:
```tsx
<div style={{ fontSize: 'var(--text-label)', color: 'var(--muted)' }}>
  {lang === 'es' ? 'Índice Compuesto de Criminalidad' : 'Composite Crime Index'}
  {' '}<a href={lang === 'es' ? '/es/metodologia/' : '/methodology/'} style={{ color: 'var(--muted)' }}>
    {lang === 'es' ? '(¿qué es esto?)' : '(what is this?)'}
  </a>
</div>
```

**Trend rows fix** (line 630): move `{TREND_ARROW[data.trend]}` from per-row to the header card only (show once). Per-row: remove the trend arrow column entirely from the family breakdown table.

**Homicide decimals** (line 644): `homRate!.toFixed(2)` → `formatDecimal(homRate!, lang)`.

---

### `site/src/components/map/MapIsland.tsx` (modify — fitBounds + ?cut= guard)

**Existing setView to replace** (line 125):
```typescript
// Before:
map.setView([-35.7, -71.8], 5);
// After:
map.fitBounds([[-55.9, -75.7], [-17.5, -66.4]], { padding: [20, 20] });
map.setMaxBounds([[-60, -80], [-14, -60]]);
map.setMinZoom(4);
```

**?cut= guard pattern** (lines 225–229):
```typescript
// Before:
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut) { setTimeout(() => selectCommune(focusCut), 100); }

// After — validate with regex (Pitfall 3: race condition + invalid CUT):
const focusCut = new URLSearchParams(window.location.search).get('cut');
if (focusCut && /^\d{5}$/.test(focusCut)) {
  setTimeout(() => selectCommune(focusCut), 100);
}
```

---

### `site/src/components/map/IncidentPinLayer.ts` (modify — pin color + aria-label)

**Existing divIcon pattern** (line 154):
```typescript
// Before:
icon: L.divIcon({ html: '<div class="ev-dot"></div>', className: '' })

// After:
const escapedTitle = escHtml(lang === 'es' ? incident.title_es : incident.title_en);
icon: L.divIcon({
  html: `<div class="ev-dot" role="img" aria-label="${escapedTitle}"></div>`,
  className: '',
})
```
Also add `title: escapedTitle` to the marker options object (Leaflet converts this to a DOM `title` attribute).

**`.ev-dot` CSS change in `map.css`** — find current color and replace:
```css
/* Before (current orange): */
.ev-dot { background: #e8a05c; /* or similar */ }

/* After: */
.ev-dot {
  background: var(--pin);  /* #6d28d9 — set --pin in global.css :root */
  border: 2px solid #ffffff;
  /* keep existing width/height/border-radius */
}
```
Add to `global.css :root`: `--pin: #6d28d9;`

---

### `site/src/pages/news.astro` (modify — headings, chips, date grouping)

**Existing data load pattern** (news.astro lines 19–58) — keep exactly. Add `family` to the destructured incident type (line 27):
```typescript
let incidents: Array<{
  id: string;
  title_es: string;
  title_en: string;
  date: string;
  outlet: string;
  url: string;
  slug?: string;
  cut?: string;
  family?: string;   // ADD THIS
}> = [];
```

**Date grouping** — add in frontmatter after sort (after line 58):
```typescript
// Group by YYYY-MM
const grouped = new Map<string, typeof incidents>();
for (const inc of incidents) {
  const key = inc.date.slice(0, 7);
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key)!.push(inc);
}
```

**Template structure change** — current `<div class="incident-title">` → `<h3 class="news-title">` inside dated `<section><h2>` groups:
```html
{[...grouped.entries()].map(([month, items]) => (
  <section>
    <h2 class="news-date-group">{new Date(month + '-01').toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}</h2>
    {items.map(inc => (
      <article class="news-card">
        <h3 class="news-title"><a href={safeUrl(inc.url)}>{inc.title_en}</a></h3>
        <p class="news-meta">
          {inc.family && <span class="news-type-chip">{inc.family}</span>}
          {inc.slug && <span class="news-commune-chip"><a href={`/commune/${inc.slug}/`}>{inc.slug}</a></span>}
          {inc.outlet} · {inc.date.slice(0, 10)}
        </p>
      </article>
    ))}
  </section>
))}
```
Chip CSS from UI-SPEC lines 391–410 — add to news.astro `<style>` block.

---

### `site/src/pages/rankings.astro` (modify — region links)

**Existing structure** (lines 78–83): "By region" section with prose paragraph. Replace prose with:
```astro
---
// In frontmatter — import regions (reuse REGION_NAMES from ResultPanel.tsx or load from data/)
import { REGION_META } from '../config/regions.ts';  // check actual import path
---
<h2>By region</h2>
<ul class="region-links-list">
  {REGION_META.map(r => (
    <li><a href={`/region/${r.slug}/`}>{r.name}</a></li>
  ))}
</ul>
```
Style (add to rankings.astro `<style>`):
```css
.region-links-list { list-style: none; padding: 0; columns: 2; }
.region-links-list li { margin-bottom: var(--xs); }
```
**Pitfall:** `FAMILY_SLUGS.vida.en === 'homicide'` — any new `byFamily` loop must filter `key !== 'vida'` (existing loop at line 25–29 already iterates `FAMILY_SLUGS`; do not duplicate it).

---

### `site/src/lib/jsonld.ts` (modify — add buildWebSite + buildOrganization)

**Existing builder pattern** (jsonld.ts lines 133–144 — `buildBreadcrumb` is the simplest pattern):
```typescript
export function buildBreadcrumb(crumbs: BreadcrumbCrumb[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({ ... })),
  };
}
```

**New builders to add** (follow same shape — return `Record<string, unknown>`):
```typescript
export function buildWebSite(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Chile Safety Map',
    url: BASE_URL,
    potentialAction: {
      '@type': 'SearchAction',
      target: `${BASE_URL}/map/?search={search_term_string}`,
      'query-input': 'required name=search_term_string',
    },
  };
}

export function buildOrganization(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Chile Safety Map',
    url: BASE_URL,
    description: 'Interactive crime data map of Chile using official CEAD statistics.',
  };
}
```
Inject in `site/src/pages/index.astro` frontmatter:
```typescript
import { buildWebSite, buildOrganization } from '../lib/jsonld.ts';
const jsonLd = [buildWebSite(), buildOrganization()];
```
Pass to `<BaseLayout jsonLd={jsonLd}>` — the existing injection loop at BaseLayout lines 107–112 handles arrays automatically.

---

### `site/src/pages/is-santiago-safe.astro` (modify — add static rate tables + sparklines)

**Existing data load pattern** (lines 16–19):
```typescript
const santiago = loadCommune('13101');
const year = santiago.latestCompleteYear;
const rate = latestCompleteYearRate(santiago);
const nationalAvg = loadNationalAverage();
```
Add to frontmatter:
```typescript
import { loadIndex } from '../lib/data.ts';
import CommuneRankingTable from '../components/CommuneRankingTable.astro';
import Sparkline from '../components/Sparkline.astro';

const allCommunes = loadIndex();
const rmCommunes = allCommunes
  .filter(c => c.region_id === '13' && !c.low_population)
  .sort((a, b) => b.featured_rates?.total?.[year] - a.featured_rates?.total?.[year]);
const top10RM = rmCommunes.slice(0, 10);
const bottom10RM = rmCommunes.slice(-10).reverse();
```
Then in template after intro `<p>`:
```astro
<CommuneRankingTable rows={top10RM} locale="en" caption="Highest reported crime rates in Región Metropolitana (CEAD {year})" />
<Sparkline series={santiago.series.map(s => s.rate_per_100k)} activeYear={year} />
```

**Sparkline.astro** — already used on commune pages, takes `series` (number array) and renders inline SVG. No JS. UI-SPEC dimensions: 180×40px for editorial context.

**Table CSS** — copy `.rate-table-figure` block from UI-SPEC lines 308–343 into the editorial page `<style>` block.

---

### `pipeline/news/classifier.py` (modify — traffic accident exclusion in SYSTEM_PROMPT)

**Existing Rules block** (lines 105–110):
```python
Rules:
- commune_name MUST be exactly a commune name from the list above, spelled in Spanish, or null.
- NEVER invent or approximate a commune name. Copy it character-for-character from the list.
- region_hint helps disambiguate; set to the region number or name from the list entry if known.
- If the article is not about a crime incident, set commune_name to null and confidence to 0.0.
- family MUST be exactly one of: {_FAMILY_ENUM_STR}
```

**Add after line 108** (after the "not about a crime incident" rule):
```python
- Traffic accidents, road collisions, and vehicle crashes are NOT crime incidents, even if they
  result in fatalities. If the article is primarily about a traffic accident (colisión, accidente
  de tránsito, choque, atropello sin culpa), set confidence to 0.0.
```

---

## Shared Patterns

### JSON-LD Injection (all pages using BaseLayout)
**Source:** `site/src/layouts/BaseLayout.astro` lines 107–112
```astro
{jsonLd !== null && (Array.isArray(jsonLd) ? jsonLd : [jsonLd])
  .filter(Boolean)
  .map((block) => (
    <script is:inline type="application/ld+json"
      set:html={JSON.stringify(block).replace(/<\//g, '<\\/')} />
  ))
}
```
**Apply to:** All pages needing new JSON-LD (index.astro for WebSite/Org; pass `jsonLd` prop to BaseLayout — never raw `<script>` tags).

### Editorial Layout Pattern
**Source:** `site/src/pages/is-santiago-safe.astro` lines 66–73
**Apply to:** 404.astro, any new editorial pages.
Always use `EditorialLayout` (which wraps `BaseLayout`) for editorial content pages. `EditorialLayout` handles `pageType="editorial"` OG image, footer, cookie-consent injection.

### Data Loading at Build Time
**Source:** `site/src/lib/data.ts` + `site/src/pages/is-santiago-safe.astro` lines 16–19
**Apply to:** P1-5 editorial pages adding rate tables.
```typescript
// Always import from '../lib/data.ts' in Astro frontmatter
// Use process.cwd()-based path resolution (not import.meta.url)
import { loadCommune, loadIndex, loadNationalAverage, latestCompleteYearRate } from '../lib/data.ts';
```

### CSS Token Usage
**Source:** `site/src/styles/global.css` `:root` block
**Apply to:** ALL new CSS in this phase.
Never hardcode hex values — always reference `var(--primary)`, `var(--ink)`, `var(--muted)`, `var(--line)`, `var(--card)`, `var(--bg)`, `var(--sm)`, `var(--md)`, etc.
Exception allowed: `var(--pin)` will be a new token added to `:root` in `global.css`.

### Locale-Conditional Navigation Links
**Source:** `site/src/components/PageHeader.astro` lines 24–33
**Apply to:** any new cross-locale links added to components.
```typescript
// Hardcode ES slugs — getRelativeLocaleUrl() does NOT translate ES slugs
const mapHref  = locale === 'en' ? '/map/' : '/es/mapa/';
const methodHref = locale === 'en' ? '/methodology/' : '/es/metodologia/';
```

### Python Test Mock Pattern
**Source:** `pipeline/tests/test_classifier.py` lines 18–21, 45–50
**Apply to:** `pipeline/tests/test_classifier_traffic.py`
```python
with patch("pipeline.news.classifier.client") as mock_client:
    mock_client.chat.completions.create.return_value = _make_mock_response(data)
    result = classify(headline, description)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `site/public/favicon.ico` | static asset | — | No ICO generation tooling in repo; must be pre-generated manually from `favicon.svg` using a tool like Inkscape/ImageMagick and committed as a binary. The SVG source pattern exists (PageHeader.astro lines 43–47) but the ICO file itself has no analog to copy — it is a binary asset. |

---

## Metadata

**Analog search scope:** `site/src/`, `pipeline/tests/`, `pipeline/news/`
**Files read directly:** BaseLayout.astro, PageHeader.astro, jsonld.ts, classifier.py, test_classifier.py, data.ts, is-santiago-safe.astro, news.astro, rankings.astro
**Pattern extraction date:** 2026-07-02
