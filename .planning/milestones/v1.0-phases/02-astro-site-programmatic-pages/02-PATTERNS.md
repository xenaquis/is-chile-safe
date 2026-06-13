# Phase 2: Astro Site + Programmatic Pages — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 27 new files
**Analogs found:** 12 / 27 (from prototype JSX); 15 / 27 marked NEW (greenfield Astro patterns from RESEARCH.md)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/astro.config.mjs` | config | — | NEW | no analog |
| `site/tsconfig.json` | config | — | NEW | no analog |
| `site/package.json` | config | — | NEW | no analog |
| `site/src/layouts/BaseLayout.astro` | layout | request-response | `ischilesafe.com/home-view.jsx` (header/footer/meta structure) | partial |
| `site/src/components/PageHeader.astro` | component | — | `ischilesafe.com/components.jsx` `Header` (lines 21–39) | role-match (port) |
| `site/src/components/PageFooter.astro` | component | — | `ischilesafe.com/home-view.jsx` `<footer>` (lines 134–138) | role-match (port) |
| `site/src/components/LevelChip.astro` | component | — | `ischilesafe.com/components.jsx` `LevelChip` (lines 119–126) | exact (port) |
| `site/src/components/TrendChip.astro` | component | — | `ischilesafe.com/components.jsx` `TrendLabel` (lines 128–133) | exact (port) |
| `site/src/components/StatCard.astro` | component | — | `ischilesafe.com/map-view.jsx` `.stat-card` block (lines 27–31) | role-match (port) |
| `site/src/components/Sparkline.astro` | component | transform | `ischilesafe.com/components.jsx` `Sparkline` (lines 135–150) | exact (port, SVG) |
| `site/src/components/FamilyBreakdownBars.astro` | component | transform | `ischilesafe.com/map-view.jsx` `.type-bars` block (lines 52–60) | exact (port) |
| `site/src/components/ComparisonCallout.astro` | component | — | NEW (no prototype analog) | no analog |
| `site/src/components/ComparableCommune.astro` | component | — | `ischilesafe.com/map-view.jsx` `.panel-similar` block (lines 79–86) | partial (data.js `similarComunas`) |
| `site/src/components/MapPlaceholderSlot.astro` | component | — | NEW | no analog |
| `site/src/components/MethodologyCaveat.astro` | component | — | `ischilesafe.com/home-view.jsx` `.method-inner` (lines 114–130) | partial |
| `site/src/components/CommuneRankingTable.astro` | component | CRUD | NEW | no analog |
| `site/src/pages/commune/[slug].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/pages/region/[slug].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/pages/crime/[family].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/pages/es/comuna/[slug].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/pages/es/region/[slug].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/pages/es/delito/[family].astro` | route | CRUD | NEW (RESEARCH.md Pattern 1) | no analog |
| `site/src/lib/data.ts` | utility | file-I/O | NEW (RESEARCH.md Pattern 1 companion) | no analog |
| `site/src/lib/slugMaps.ts` | utility | transform | NEW (RESEARCH.md Pattern 2) | no analog |
| `site/src/lib/proseEngine.ts` | utility | transform | `ischilesafe.com/data.js` `I18N` + `rateFor`/`rankingFor` (lines 86–112) | partial (logic port) |
| `site/src/lib/colorScale.ts` | utility | transform | `ischilesafe.com/data.js` (palette passed as props); RESEARCH.md chroma-js example | partial |
| `site/src/config/rollout.json` | config | — | NEW | no analog |
| `site/src/config/i18n.ts` | config | — | `ischilesafe.com/data.js` `I18N` object (lines 135–222) | exact (port) |
| `site/src/styles/global.css` | config | — | `ischilesafe.com/Chile Safety Map.html` (CSS vars) | role-match |
| `site/public/manifest.json` | config | — | NEW | no analog |
| `site/scripts/validate-build.mjs` | utility | batch | NEW | no analog |

---

## Pattern Assignments

### `site/src/components/PageHeader.astro` (component, static)

**Analog:** `ischilesafe.com/components.jsx` — `Header` function, lines 21–39

**Port relationship:** React `Header` → static Astro component. Remove all state (`route`, `navigate`, `setLang`) — use `Astro.currentLocale` and `getRelativeLocaleUrl()` instead. Remove demo pill. Keep nav structure, lang toggle layout.

**Core pattern to port** (components.jsx lines 21–39):
```jsx
function Header({ t, lang, setLang, route, navigate, onMethod }) {
  return (
    <header className="csm-header">
      <Wordmark onClick={() => navigate('home')} />
      <nav className="csm-nav">
        <button className={'nav-link' + (route === 'home' ? ' active' : '')} onClick={() => navigate('home')}>{t.nav_home}</button>
        <button className={'nav-link' + (route === 'map' ? ' active' : '')} onClick={() => navigate('map')}>{t.nav_map}</button>
        <button className="nav-link" onClick={onMethod}>{t.nav_method}</button>
      </nav>
      <div className="header-right">
        <div className="lang-toggle" role="group" aria-label="Idioma">
          <button className={lang === 'es' ? 'active' : ''} onClick={() => setLang('es')}>ES</button>
          <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>EN</button>
        </div>
      </div>
    </header>
  );
}
```

**Astro port pattern (replace onClick/state with static links):**
```astro
---
import { getRelativeLocaleUrl } from 'astro:i18n';
interface Props { locale: 'en' | 'es'; currentPath: string; }
const { locale, currentPath } = Astro.props;
const t = locale === 'en' ? EN_STRINGS : ES_STRINGS;
const altLocale = locale === 'en' ? 'es' : 'en';
const altPath = getRelativeLocaleUrl(altLocale, currentPath);
---
<header class="csm-header">
  <a href={getRelativeLocaleUrl(locale, '/')} class="wordmark">...</a>
  <nav class="csm-nav">
    <a href={getRelativeLocaleUrl(locale, '/')} class="nav-link">{t.nav_home}</a>
    <a href={getRelativeLocaleUrl(locale, '/map')} class="nav-link">{t.nav_map}</a>
  </nav>
  <div class="header-right">
    <div class="lang-toggle" role="group" aria-label="Idioma">
      <a href={altPath} class={locale === 'es' ? 'active' : ''}>{locale === 'en' ? 'ES' : 'EN'}</a>
      <span class={locale === 'en' ? 'active' : ''}>EN</span>
    </div>
  </div>
</header>
```

**PinGlyph SVG to inline** (components.jsx lines 4–10):
```jsx
function PinGlyph({ size = 22 }) {
  return (
    <span className="wordmark-glyph" style={{ width: size, height: size }}>
      <span className="wordmark-dot"></span>
    </span>
  );
}
```

---

### `site/src/components/LevelChip.astro` (component, static)

**Analog:** `ischilesafe.com/components.jsx` — `LevelChip`, lines 119–126

**Exact port** (components.jsx lines 119–126):
```jsx
function LevelChip({ t, level, palette }) {
  return (
    <span className="level-chip">
      <span className="level-dot" style={{ background: palette[level - 1] }}></span>
      {t['level_' + level]}
    </span>
  );
}
```

**Astro port note:** Replace `palette[level - 1]` with CSS custom property `var(--s{level})` (defined in global.css). Replace `t['level_' + level]` with prop from `i18n.ts` labels array. `style` becomes a scoped CSS var or inline style attribute.

---

### `site/src/components/TrendChip.astro` (component, static)

**Analog:** `ischilesafe.com/components.jsx` — `TrendLabel`, lines 128–133

**Exact port** (components.jsx lines 128–133):
```jsx
function TrendLabel({ t, trend }) {
  const label = trend < 0 ? t.trend_down : trend > 0 ? t.trend_up : t.trend_flat;
  const arrow = trend < 0 ? '↓' : trend > 0 ? '↑' : '→';
  const cls = trend < 0 ? 'down' : trend > 0 ? 'up' : 'flat';
  return <span className={'trend ' + cls}><span className="trend-arrow">{arrow}</span>{label}</span>;
}
```

**Data contract change:** Phase 1 uses string trend (`"up"` / `"down"` / `"stable"`) not numeric (-1/0/1). Props: `trend: 'up' | 'down' | 'stable'`, `locale: 'en' | 'es'`. Derive `cls` and `arrow` from string.

---

### `site/src/components/Sparkline.astro` (component, transform)

**Analog:** `ischilesafe.com/components.jsx` — `Sparkline`, lines 135–150

**Core SVG pattern to port** (components.jsx lines 135–150):
```jsx
function Sparkline({ comuna, type, year }) {
  const C = window.CSM;
  const vals = C.YEARS.map((y) => C.rateFor(comuna, type, y));
  const max = Math.max(...vals);
  const w = 18, gap = 8;
  const totalW = C.YEARS.length * (w + gap) - gap;
  return (
    <svg className="sparkline" viewBox={'0 0 ' + totalW + ' 44'} width="100%" height="44" preserveAspectRatio="none">
      {vals.map((v, i) => {
        const h = Math.max(4, (v / max) * 40);
        const active = C.YEARS[i] === year;
        return <rect key={i} x={i * (w + gap)} y={44 - h} width={w} height={h} rx="3" className={active ? 'bar active' : 'bar'}></rect>;
      })}
    </svg>
  );
}
```

**Astro port note:** `vals` come from `series[]` prop (array of `{year, rate_per_100k, partial}` from Phase 1 JSON). Partial bars rendered at 50% opacity (UI-SPEC). Replace `window.CSM.rateFor` with direct `s.rate_per_100k`. The RESEARCH.md Pattern 4 provides the complete Astro version of this component.

**RESEARCH.md Pattern 4 reference (Sparkline.astro):**
```astro
---
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
      <rect x={x} y={height - barH} width={barW} height={barH}
        fill={isActive ? 'var(--primary)' : 'var(--muted)'}
        opacity={opacity}
      />
    );
  })}
</svg>
```

---

### `site/src/components/FamilyBreakdownBars.astro` (component, transform)

**Analog:** `ischilesafe.com/map-view.jsx` — `ResultPanel` `.type-bars` block, lines 52–60

**Core pattern to port** (map-view.jsx lines 52–60):
```jsx
const barTypes = ['robos', 'hurtos', 'lesiones', 'vif'];
const barVals = barTypes.map((k) => C.rateFor(comuna, k, year));
const barMax = Math.max(...barVals);
// ...
<div className="type-bars">
  {barTypes.map((k, i) => (
    <div className="type-bar-row" key={k}>
      <span className="type-bar-label">{t['type_' + k]}</span>
      <span className="type-bar-track">
        <span className="type-bar-fill" style={{ width: Math.round((barVals[i] / barMax) * 100) + '%' }}></span>
      </span>
      <span className="type-bar-val">~{barVals[i]}</span>
    </div>
  ))}
</div>
```

**Phase 2 changes:** 7 families from Phase 1 JSON (not 4 from prototype). Order: `vida` first (featured), `propiedad` second (featured), then `robos_violentos`, `incivilidades`, `vif`, `drogas`, `armas`. Featured families get `--primary` accent dot on label. Width MUST be CSS percentage string `Math.round((val / max) * 100) + '%'` — not a bare number (RESEARCH.md anti-pattern). Data comes from `series[latestCompleteYear].by_family`.

---

### `site/src/components/StatCard.astro` (component, static)

**Analog:** `ischilesafe.com/map-view.jsx` — `.stat-card` / `.mini-stat` blocks, lines 27–42

**Pattern to port** (map-view.jsx lines 27–42):
```jsx
<div className="stat-card">
  <div className="stat-big">~{rate}</div>
  <div className="stat-unit">{t.panel_rate}</div>
  <div className="stat-ctx">{t['type_' + type]} · {year}</div>
</div>
<div className="mini-stat">
  <span className="mini-stat-label">{t.panel_trend}</span>
  <TrendLabel t={t} trend={comuna.trend} />
</div>
<div className="mini-stat">
  <span className="mini-stat-label">{t.panel_ranking}</span>
  <span className="mini-stat-val">#{rank} <em>{t.panel_ranking_of} {window.CSM.COMUNAS.length}</em></span>
</div>
```

**Astro port:** Props `label: string`, `value: string | number`, `sublabel?: string`. Renders the 28px/700 value + 14px/700 label pattern from UI-SPEC. Used 3× in `KeyStatsRow` on commune pages.

---

### `site/src/components/ComparableCommune.astro` (component, static)

**Analog:** `ischilesafe.com/map-view.jsx` — `.panel-similar` and `data.js` `similarComunas`, lines 79–86 / 109–114

**Similarity algorithm from prototype** (data.js lines 109–113):
```js
function similarComunas(comuna, n) {
  return COMUNAS.filter(c => c.id !== comuna.id && c.level === comuna.level)
    .sort((a, b) => (a.region === comuna.region ? 1 : 0) - (b.region === comuna.region ? 1 : 0))
    .slice(0, n || 3);
}
```

**Phase 2 algorithm differs (D-08):** nearest by total rate per 100k within same region (not by `level`); excludes `low_population`; fallback to national. Computed in `proseEngine.ts`, not inline in the component. The component receives a pre-computed `comparable` prop.

**Display pattern from prototype** (map-view.jsx lines 79–86):
```jsx
<div className="panel-section">
  <h4>{t.panel_similar}</h4>
  <div className="similar-chips">
    {similar.map((c) => (
      <button key={c.id} className="chip" onClick={() => onSelect(c)}>{c.name}</button>
    ))}
  </div>
</div>
```

**Phase 2 version:** Card layout with rate, rank, trend chip, and `<a href>` link (not button/onClick). Heading: "Comparable commune (same region)" or "(national)" per UI-SPEC.

---

### `site/src/components/MapPlaceholderSlot.astro` (component, static)

**Analog:** NEW — no prototype analog. Design specified in 02-UI-SPEC.md.

**UI-SPEC contract** (02-UI-SPEC.md lines 319–341):
```html
<div
  class="map-placeholder-slot"
  data-phase3-mount="{commune-map | region-map | crime-type-map}"
  aria-label="Interactive map — coming soon"
  role="img"
>
  <div class="map-placeholder-inner">
    <!-- PinGlyph SVG, 40px -->
    <p class="map-placeholder-label">{locale-aware placeholder text}</p>
  </div>
</div>
```

**CSS contract from UI-SPEC:**
- `min-height: 320px` mobile / `480px` desktop
- `border: 2px dashed var(--line)`
- `border-radius: 14px`
- `background: var(--bg)`
- `display: flex; align-items: center; justify-content: center`

**PinGlyph SVG to use:** `ischilesafe.com/components.jsx` lines 4–10 (port as inline SVG).

---

### `site/src/components/MethodologyCaveat.astro` (component, static)

**Analog:** `ischilesafe.com/home-view.jsx` — `.method-inner` section, lines 114–130

**Pattern to port** (home-view.jsx lines 114–130):
```jsx
<section className="method" id="metodologia">
  <div className="method-inner">
    <h2>{t.method_title}</h2>
    <p>{t.method_body}</p>
  </div>
</section>
```

**Phase 2 version:** Grey box (not full section). 2–3 sentences on subregistro, CEAD attribution, rate-per-100k definition. Font 14px/400. Include link to `/methodology/` (EN) or `/es/metodologia/` (ES). Background `var(--bg)`, border `var(--line)`, `border-radius: 14px`.

---

### `site/src/config/i18n.ts` (config, static)

**Analog:** `ischilesafe.com/data.js` — `I18N` object, lines 135–222

**Full EN/ES string map to port** (data.js lines 135–222):

Key strings to preserve (adapting to Phase 2 sober tone):
```js
const I18N = {
  es: {
    nav_home: 'Inicio', nav_map: 'Mapa', nav_method: 'Metodología',
    trend_down: 'A la baja', trend_flat: 'Estable', trend_up: 'Al alza',
    panel_rate: 'casos por 10 mil hab.',   // → phase 2: 'tasa por 100.000 hab.'
    panel_trend: 'Tendencia general',
    panel_ranking: 'Ranking nacional', panel_ranking_of: 'de',
    panel_evolution: 'Evolución',
    level_1: 'Incidencia baja', level_2: 'Incidencia media-baja',
    level_3: 'Incidencia media', level_4: 'Incidencia media-alta', level_5: 'Incidencia alta',
    // ... (full set in data.js)
  },
  en: { /* mirror */ }
};
```

**Phase 2 additions needed** (from 02-UI-SPEC.md Copywriting Contract, not in prototype):
- Crime-family slug translations (7 EN + 7 ES slugs for `/crime/` and `/es/delito/` URLs)
- Page h1 patterns: `"{Name} Crime Data"` / `"{Nombre} — Datos de Incidencia"`
- Comparison callout copy: `"{N}% above/below national average"`
- Comparable commune headings (same-region / national fallback variants)
- Low-population caveat full text
- Partial-year badge: `"Partial year ({year})"`

---

### `site/src/lib/proseEngine.ts` (utility, transform)

**Analog:** `ischilesafe.com/data.js` — `rateFor`, `rankingFor`, `similarComunas` functions (lines 86–113); `I18N` bilingual strings (lines 135–222)

**Prototype logic to adapt** (data.js lines 86–113):
```js
// Deterministic value derivation pattern (adapt for prose branching)
function rateFor(comuna, type, year) {
  const base = 40 + comuna.level * 55;
  const v = (hash(comuna.id + type + year) % 30) - 15;
  const trendF = 1 + comuna.trend * 0.04 * (year - 2021);
  return Math.max(5, Math.round(val / 10) * 10);
}

function rankingFor(comunaId, type, year) {
  const sorted = COMUNAS.slice().sort((a, b) => rateFor(b, type, year) - rateFor(a, type, year));
  return sorted.findIndex(c => c.id === comunaId) + 1;
}
```

**Phase 2 version:** Replace computed values with real Phase 1 data reads. Branch structure from RESEARCH.md Pattern 5:
- `trend: 'up' | 'down' | 'stable'` → 3 sentence branches per locale
- `nationalRankTier: 'top10' | 'top25' | 'mid' | 'bottom25' | 'bottom10'` → 5 branches
- `vsNationalSign + magnitude` → 6 branches
- `vsRegionalSign + magnitude` → 6 branches
- `dominantFamily` (7 keys) → 7 branches
- `lowPopulation` → caveat inserted/omitted

---

### `site/src/lib/colorScale.ts` (utility, transform)

**Analog:** `ischilesafe.com/data.js` palette passed as props (5-level array); RESEARCH.md chroma-js code example

**Prototype palette reference** (prototype CSS vars from Chile Safety Map.html, confirmed in 02-UI-SPEC.md):
```
--s1: #dbeef0  (level 1 — Low)
--s2: #9fd0cd  (level 2 — Medium-low)
--s3: #f4d58d  (level 3 — Medium)
--s4: #e8a05c  (level 4 — Medium-high)
--s5: #c96b5a  (level 5 — High)
```

**RESEARCH.md chroma-js pattern:**
```typescript
// site/src/lib/colorScale.ts — runs ONLY at build time (Node.js)
import chroma from 'chroma-js';

export const INCIDENCE_COLORS = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);
// Returns: ['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a']
```

---

### `site/src/pages/commune/[slug].astro` (route, CRUD)

**Analog:** NEW — greenfield. Pattern from RESEARCH.md Pattern 1.

**Complete getStaticPaths + page pattern** (RESEARCH.md lines 276–299):
```typescript
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
<BaseLayout lang="en" title={`${data.name} Crime Data — Chile Safety Map`}
  enPath={enPath} esPath={esPath} jsonLd={buildJsonLd(data, 'en')}>
  <!-- page content -->
</BaseLayout>
```

**ES mirror:** `site/src/pages/es/comuna/[slug].astro` — identical `getStaticPaths` (same rollout gate), `lang="es"`, different label strings from `i18n.ts`. See RESEARCH.md Pattern 1.

---

### `site/src/lib/data.ts` (utility, file-I/O)

**Analog:** NEW. Pattern from RESEARCH.md Pattern 1 companion.

**node:fs data loader** (RESEARCH.md lines 309–326):
```typescript
// site/src/lib/data.ts
import fs from 'node:fs';
import path from 'node:path';

const DATA_ROOT = path.resolve(process.cwd(), '..', 'data', 'cead');
// NOTE: Use import.meta.url-based path in astro.config.mjs to avoid CWD ambiguity (Pitfall 1)

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

**CWD safety:** RESEARCH.md Pitfall 1 — use `import.meta.url`-based `__dirname` in astro.config.mjs, pass as Vite define constant. `loadCommune` should also derive `latestCompleteYear` (last series entry where `partial === false`) and return it alongside the raw data (needed by `FamilyBreakdownBars` and sparkline).

**Phase 1 data shape confirmed** (from `data/cead/comunas/13101.json`):
```json
{
  "id": "13101", "name": "Santiago", "slug": "santiago",
  "region_id": "13", "population": 544388, "low_population": false,
  "national_rank": 11, "regional_rank": 2, "trend": "stable",
  "featured_rates": { "propiedad": { "2005": 6273.13, ... }, "homicidios": {}, "secuestros": {} },
  "series": [
    { "year": 2005, "rate_per_100k": 19481.93,
      "by_family": { "vida": 1442.09, "robos_violentos": 2118.29, "vif": 359.19,
                     "drogas": 76.40, "armas": 49.41, "propiedad": 6273.14, "incivilidades": 9163.40 },
      "partial": false }
    // ... through 2026 (partial: true for 2026)
  ]
}
```

**Index shape confirmed** (from `data/cead/meta/index.json`):
```json
{ "cut": "5602", "name": "Algarrobo", "slug": "algarrobo",
  "region_id": "56", "population": 16095, "low_population": false }
```

---

### `site/src/lib/slugMaps.ts` (utility, transform)

**Analog:** NEW. Pattern from RESEARCH.md Pattern 2.

**Full slug-pair map pattern** (RESEARCH.md lines 340–364):
```typescript
// site/src/lib/slugMaps.ts
import { loadIndex } from './data.ts';
import { FAMILY_SLUGS } from '../config/i18n.ts';

export type SlugPair = { en: string; es: string };

export function buildCommuneSlugPairMap(): Record<string, SlugPair> {
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

---

### `site/src/layouts/BaseLayout.astro` (layout, request-response)

**Analog:** Partial analog from `ischilesafe.com/home-view.jsx` footer + header structure. hreflang is NEW (RESEARCH.md Pattern 2).

**hreflang + canonical injection pattern** (RESEARCH.md lines 367–380):
```astro
---
// BaseLayout.astro (excerpt)
const { lang, enPath, esPath } = Astro.props;
const baseUrl = 'https://ischilesafe.com';
---
<head>
  <link rel="alternate" hreflang="en" href={`${baseUrl}${enPath}`} />
  <link rel="alternate" hreflang="es" href={`${baseUrl}${esPath}`} />
  <link rel="alternate" hreflang="x-default" href={`${baseUrl}${enPath}`} />
  <link rel="canonical" href={`${baseUrl}${lang === 'en' ? enPath : esPath}`} />
  <meta name="theme-color" content="#0f766e" />
  <link rel="manifest" href="/manifest.json" />
</head>
```

**Schema.org JSON-LD injection** (RESEARCH.md lines 617–642):
```typescript
function buildCommuneJsonLd(data, locale) {
  return {
    "@context": "https://schema.org",
    "@type": ["Dataset", "Place"],
    "name": locale === 'en'
      ? `${data.name} — Reported Crime Incidence`
      : `${data.name} — Incidencia Delictiva Reportada`,
    "url": `https://ischilesafe.com${locale === 'en' ? `/commune/${data.slug}/` : `/es/comuna/${data.slug}/`}`,
    "spatialCoverage": {
      "@type": "Place", "name": data.name,
      "containedInPlace": { "@type": "AdministrativeArea", "name": data.regionName }
    },
    "temporalCoverage": `2005/${data.latestCompleteYear}`,
    "measurementTechnique": "Rate per 100,000 inhabitants, official CEAD police statistics",
    "creator": { "@type": "Organization", "name": "CEAD — Centro de Estudios y Análisis del Delito" }
  };
}
// Inject as: <script type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
```

---

### `site/astro.config.mjs` (config)

**Analog:** NEW. Pattern from RESEARCH.md Code Examples section.

**Full scaffold** (RESEARCH.md lines 554–594):
```javascript
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
        if (!url.includes('/commune/') && !url.includes('/comuna/')) return true;
        if (process.env.ROLLOUT_ALL === 'true') return true;
        // Map slugs from rollout CUT codes (see RESEARCH.md Pattern 3 for full impl)
        return rollout.enabledSlugs?.some((s) => url.includes(`/${s}/`)) ?? false;
      },
      i18n: { defaultLocale: 'en', locales: { en: 'en', es: 'es' } }
    })
  ],
  vite: {
    resolve: {
      alias: { '@data': path.resolve(__dirname, '..', 'data') }
    }
  }
});
```

---

### `site/src/config/rollout.json` (config)

**Analog:** NEW. Shape from CONTEXT.md D-24/D-25.

**Exact shape:**
```json
{
  "enabled": ["13101","13119","13114","13108","5101","5109","8101","4101","2101","9101","10101","12101"]
}
```
CUT codes for: Santiago, Providencia, Las Condes, Maipú, Valparaíso, Viña del Mar, Concepción, La Serena, Antofagasta, Temuco, Puerto Montt, Punta Arenas. Verify against `data/cead/meta/index.json` at plan time.

---

### `site/src/styles/global.css` (config)

**Analog:** `ischilesafe.com/Chile Safety Map.html` (inline CSS variables)

**CSS custom properties to port** (from 02-UI-SPEC.md Design System + prototype vars):
```css
:root {
  --primary: #0f766e;
  --bg:      #f5f8f8;
  --ink:     #1c2a2b;
  --muted:   #5d6c6d;
  --line:    #e2e9e8;
  --card:    #ffffff;
  --s1:      #dbeef0;
  --s2:      #9fd0cd;
  --s3:      #f4d58d;
  --s4:      #e8a05c;
  --s5:      #c96b5a;
  --radius:  14px;
  /* spacing scale */
  --xs: 4px; --sm: 8px; --md: 16px; --lg: 24px;
  --xl: 32px; --2xl: 48px; --3xl: 64px;
  /* typography */
  --font: 'Nunito Sans', 'Segoe UI', system-ui, sans-serif;
}
```

---

### `site/scripts/validate-build.mjs` (utility, batch)

**Analog:** NEW — no codebase analog. Pattern from RESEARCH.md Validation Architecture.

**Test map** (RESEARCH.md lines 744–758): Node.js `assert` module, no Jest/Vitest. Checks: page counts, HTML structure, hreflang reciprocity, sitemap URLs, JSON-LD presence, PWA meta. Run as `node site/scripts/validate-build.mjs --full`.

---

## Shared Patterns

### Incidence Color Scale
**Source:** `ischilesafe.com/data.js` palette (5 hex values) + `ischilesafe.com/Chile Safety Map.html` CSS `--s1..--s5`
**Apply to:** `LevelChip.astro`, `FamilyBreakdownBars.astro`, `colorScale.ts`, `global.css`
```
--s1: #dbeef0  --s2: #9fd0cd  --s3: #f4d58d  --s4: #e8a05c  --s5: #c96b5a
```

### hreflang + Canonical
**Source:** RESEARCH.md Pattern 2 (lines 332–380)
**Apply to:** `BaseLayout.astro` — injected once, consumed by all 700+ pages via props `enPath` / `esPath` / `lang`

### Sober Language Contract
**Source:** CONTEXT.md D-05; 02-UI-SPEC.md Copywriting Contract
**Apply to:** `proseEngine.ts`, ALL component label strings in `i18n.ts`
- Never: "zona peligrosa", "ranking definitivo", "zona segura garantizada"
- Always: "incidencia reportada", "tasa por 100.000 habitantes", "evolución anual"

### node:fs Data Loading
**Source:** RESEARCH.md Pattern 1 + Pitfall 1
**Apply to:** `lib/data.ts`, all `getStaticPaths()` implementations
- Use `import.meta.url`-based `__dirname` (not `process.cwd()`) for the data root path
- Load `index.json` in `getStaticPaths`, individual commune JSON in page body (prevents OOM)
- Never use `import.meta.glob` for large JSON outside `/src/`

### Rollout Gate
**Source:** CONTEXT.md D-24; RESEARCH.md Pattern 3
**Apply to:** All 6 `[slug].astro` route files (commune EN + ES only), `sitemap filter()` in `astro.config.mjs`
- Commune routes gated by `rollout.enabled` CUT list
- Region and crime-type routes NOT gated (always build all)
- `ROLLOUT_ALL=true` env flag overrides the gate

### Zero JS on Content Pages
**Source:** CONTEXT.md D-09; CLAUDE.md "What NOT to Use"
**Apply to:** ALL `.astro` component files
- No `client:*` directives in Phase 2
- No `import.meta.glob` bundling of data into JS
- Sparkline = inline SVG, family bars = CSS `width` percentage, color scale = CSS vars

---

## No Analog Found (Greenfield)

Files with no close match in the codebase — planner uses RESEARCH.md patterns directly:

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `site/astro.config.mjs` | config | — | No Astro project exists yet |
| `site/src/layouts/BaseLayout.astro` | layout | — | No Astro layouts exist; hreflang pattern is novel |
| `site/src/components/ComparisonCallout.astro` | component | — | No prototype analog; new UI element |
| `site/src/components/MapPlaceholderSlot.astro` | component | — | New element for Phase 3 hydration |
| `site/src/components/CommuneRankingTable.astro` | component | CRUD | No table component in prototype |
| `site/src/lib/data.ts` | utility | file-I/O | No TypeScript/Node.js files exist; new pattern |
| `site/src/lib/slugMaps.ts` | utility | transform | New bilingual routing concern |
| `site/src/config/rollout.json` | config | — | New batch-gate mechanism |
| `site/public/manifest.json` | config | — | New PWA file |
| `site/scripts/validate-build.mjs` | utility | batch | No build validation exists |
| All 6 `[slug].astro` route files | route | CRUD | No getStaticPaths exist in repo |

---

## Metadata

**Analog search scope:** `ischilesafe.com/` (prototype JSX/JS), `pipeline/` (Python, conventions only), `data/cead/` (JSON contract verification)
**Files scanned:** 9 prototype files, 2 pipeline files, 2 data files (index + commune sample)
**Pattern extraction date:** 2026-06-13
