# Phase 09: UX / Readability / Accessibility Polish - Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 13 (4 new, 9 modified)
**Analogs found:** 13 / 13 (every new file has a strong in-repo analog — this is a polish phase, no greenfield patterns)

## File Classification

| New/Modified File | New? | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|------|-----------|----------------|---------------|
| `site/src/lib/familyDefs.ts` | NEW | utility (shared data module) | transform / static-export | `site/src/config/i18n.ts` (record-of-strings export) | exact (role + flow) |
| `site/src/components/RateTooltip.astro` | NEW | component (Astro, zero-JS) | request-response (SSR static) | `site/src/components/DataCallout.astro` | exact (role) |
| `site/src/components/map/RateTooltipReact.tsx` | NEW | component (React island) | request-response (client render) | `site/src/components/map/PanelFamilyBars.tsx` (presentational, props-only) | exact (role + flow) |
| `site/src/pages/glossary.astro` | NEW | route (Astro page, EN) | request-response (SSG) | `site/src/pages/crime/[family].astro` | role-match (static vs param) |
| `site/src/pages/es/glosario.astro` | NEW | route (Astro page, ES) | request-response (SSG) | `site/src/pages/es/delito/[family].astro` | role-match |
| `site/src/components/map/Legend.tsx` | EDIT | component (React island) | transform (props → swatches) | self (extend) + `colors.ts` (data source) | exact |
| `site/src/components/map/ResultPanel.tsx` | EDIT | component (React island) | CRUD-read (fetch-on-open) + transform | self (extend; D-01 tooltip + D-04 bar) | exact |
| `site/src/components/map/PanelFamilyBars.tsx` | EDIT | component (React island) | transform | self (add per-family glossary tooltip/anchor) | exact |
| `site/src/pages/map.astro` + `es/mapa.astro` | EDIT | route (Astro page) | prop-threading (build → island) | self + `is-santiago-safe.astro` (build-time `loadNationalAverage`) | exact |
| `site/src/styles/global.css` | EDIT | config (global CSS) | n/a | self (add `:focus-visible` + prose rhythm) | n/a |
| `site/src/config/i18n.ts` | EDIT | config (bilingual strings) | static-export | self (add Phase-9 keys) | exact |
| `site/src/pages/es/metodologia.astro` | EDIT | route (Astro page, ES) | request-response (SSG) | `site/src/pages/methodology.astro` (EN, for parity) | exact (READ-02 parity) |
| `site/src/components/CommuneRankingTable.astro` + crime/region pages | EDIT | component / route | request-response | self (add `<RateTooltip>` + glossary cross-link) | exact |

---

## Pattern Assignments

### `site/src/lib/familyDefs.ts` (NEW — utility, shared data module)

**Analog:** `site/src/config/i18n.ts` (existing record-of-strings export pattern) — and the constants to HOIST live in `site/src/pages/crime/[family].astro` lines 35-54 and `site/src/pages/es/delito/[family].astro` lines 28-35+.

**Source constants to copy verbatim (do NOT rewrite — RESEARCH §"Hoist FAMILY_DEFS"):**

From `crime/[family].astro` lines 35-54:
```typescript
const FAMILY_LABELS_EN: Record<string, string> = {
  vida:            'Life Crimes',
  robos_violentos: 'Violent Robbery',
  vif:             'Domestic Violence',
  drogas:          'Drug Crimes',
  armas:           'Weapons Offences',
  propiedad:       'Property Crimes',
  incivilidades:   'Disorder',
};

const FAMILY_DEFS_EN: Record<string, string> = {
  vida:            'Reported offences against life and physical integrity, including homicide and serious assault, sourced from official CEAD police statistics.',
  // ... all 7, copy lines 46-54 verbatim
};
```
ES labels/defs live in `es/delito/[family].astro` lines 28-35+ — copy verbatim into the same module.

**Export pattern to follow** (mirror `PanelFamilyBars.tsx` lines 30-38 for FAMILY_ORDER):
```typescript
export const FAMILY_ORDER = [
  'vida', 'propiedad', 'robos_violentos', 'incivilidades', 'vif', 'drogas', 'armas'
] as const;
```

**After hoisting:** update BOTH `crime/[family].astro` (remove lines 35-54, add `import { FAMILY_LABELS_EN, FAMILY_DEFS_EN } from '../../lib/familyDefs.ts'`) and `es/delito/[family].astro` (remove lines 28-35+, import from `'../../../lib/familyDefs.ts'`). Net behaviour change: zero.

---

### `site/src/components/RateTooltip.astro` (NEW — Astro zero-JS component, D-01/D-02 static surface)

**Analog:** `site/src/components/DataCallout.astro` (props interface + scoped `<style>` + zero `client:*`).

**Imports/props pattern** (DataCallout.astro lines 15-23):
```astro
---
interface Props {
  value: string;
  label: string;
  source: string;
  locale: 'en' | 'es';
}
const { value, label, source } = Astro.props;
---
```
RateTooltip mirrors this with `{ tip, lang, label }`. Use `<details>/<summary>` per RESEARCH Pattern 1 (zero-JS, keyboard + touch accessible). Reuse CSS tokens (`--card`, `--line`, `--radius`, `--primary`, `--text-label`) exactly as DataCallout does (lines 31-61) — scoped `<style>` block.

**Editorial constraint:** `tip` text comes from `i18n.ts` (`rate_tooltip_body`) or `familyDefs.ts` — never inline "peligroso/seguro".

---

### `site/src/components/map/RateTooltipReact.tsx` (NEW — React twin, D-01/D-02 island surface)

**Analog:** `site/src/components/map/PanelFamilyBars.tsx` — presentational, props-only, no hooks, no fetch.

**Component shape to copy** (PanelFamilyBars.tsx lines 53-59):
```tsx
interface Props {
  byFamily: number[];
  locale: 'en' | 'es';
  level: 1 | 2 | 3 | 4 | 5;
}
export function PanelFamilyBars({ byFamily, locale, level }: Props) { ... }
```
RateTooltipReact uses `{ label, tip, lang }` and renders the SAME `<details>/<summary>` HTML as the Astro twin (RESEARCH Pattern 1, lines 177-202) so one CSS block in `global.css` styles both. Note PanelFamilyBars uses `className` (React) and `aria-hidden="true"` on decorative spans (line 84, 88) — copy that a11y convention.

---

### `site/src/pages/glossary.astro` (NEW — EN route, D-02) / `site/src/pages/es/glosario.astro` (NEW — ES route)

**Analog:** `site/src/pages/crime/[family].astro` (BaseLayout usage, JSON-LD, family iteration) and its ES mirror `es/delito/[family].astro`.

**BaseLayout invocation pattern** (crime/[family].astro lines 192-200):
```astro
<BaseLayout
  lang="en"
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
  jsonLd={jsonLd}
>
```
Glossary is a STATIC page (no `getStaticPaths`) — closer to a fixed editorial page. Set literal `enPath="/glossary/"` / `esPath="/es/glosario/"` (RESEARCH Bilingual Glossary Wiring table). hreflang + canonical are automatic via BaseLayout (lines 56-59).

**Iterate families** using the hoisted `FAMILY_ORDER` + `FAMILY_DEFS_*` from `familyDefs.ts` (RESEARCH Pattern 4, lines 361-368). Each `<section>` = `<h2>` label + definition prose + link to `/crime/{slug}/`.

**Thin-content guard (Pitfall 3):** 80-120 words per family entry, ~600+ words total. Link ONLY to `/crime/*` and `/region/*` — never `/commune/*` (rollout 404 risk, Pitfall 5).

**Cross-reference for hreflang** — both pages declare the SAME `enPath`/`esPath` pair (mirror crime/[family].astro lines 163-164).

---

### `site/src/components/map/Legend.tsx` (EDIT — D-03 numeric bands)

**Analog:** self (current 5-swatch render, lines 11-31) + data source `colors.ts`.

**Current signature to extend** (Legend.tsx lines 7-11):
```tsx
interface Props { lang: 'en' | 'es'; }
export function Legend({ lang }: Props) {
```
Add `breaks?: number[]`. The break source already exists — `computeQuantileBreaks` in `colors.ts` lines 33-38:
```typescript
export function computeQuantileBreaks(sorted: number[], classes = 5): number[] {
  const s = [...sorted].sort((a, b) => a - b);
  return Array.from({ length: classes - 1 }, (_, i) =>
    s[Math.floor((s.length * (i + 1)) / classes)] ?? 0);
}
```
**Threading note (IMPORTANT — differs from RESEARCH assumption):** `computeQuantileBreaks` is currently called inside `ChoroplethLayer.ts`, NOT `MapIsland.tsx` (RESEARCH lines 277/299 assumed MapIsland). The breaks must be surfaced from ChoroplethLayer up to MapIsland state, then passed to `<Legend>`. MapIsland renders `<Legend lang={lang} />` at line 410 — extend to `<Legend lang={lang} breaks={breaks} />`.

**Reuse** `INCIDENCE_COLORS` (colors.ts lines 13-16) for swatch fills (already imported, Legend.tsx line 5). Locale number format: `n.toLocaleString('es-CL' | 'en-US')` — same convention as ResultPanel.tsx line 167 and crime/[family].astro line 214. Qualitative labels go in `i18n.ts` (`legend_qual_1..5`, RESEARCH Code Examples lines 510-528).

---

### `site/src/components/map/ResultPanel.tsx` (EDIT — D-01 tooltip + D-04 multiplier/bar)

**Analog:** self. Existing stat-card (lines 232-240), mini-stats-row (lines 242-256), and family bars (lines 272-280) are the insertion anchors.

**D-01 — tooltip next to the rate** goes beside the stat-unit (lines 234-239):
```tsx
<div className="stat-unit">
  {lang === 'es' ? `Tasa por 100.000 hab. (${year})` : `Rate per 100,000 inhab. (${year})`}
  {/* + <RateTooltip lang={lang} ... /> */}
</div>
```

**D-04 — multiplier + comparison bar.** Add a `nationalAvg: number` prop to `Props` (lines 65-70). Compute multiplier from the existing `rate` (line 166). Use the bar markup from RESEARCH Pattern 3 (lines 324-338) — CSS-only `width %` bar, NO chart lib. Color via `var(--s${level})` exactly as PanelFamilyBars.tsx line 91 and the level-chip dot (ResultPanel.tsx line 223).

**Existing a11y conventions to preserve:** `aria-hidden="true"` on decorative SVG/markers (lines 223, 295), `aria-label` on close button (line 215). The comparison bar wrapper must carry `aria-hidden="true"` with the text label readable (RESEARCH Pattern 3 lines 325, 333).

**Pitfall 2 (clipping):** `<details>` tooltip body uses `position: absolute`; verify `.stat-card`/`.mini-stats-row` ancestors don't `overflow: hidden`. Set `overflow: visible` if clipped.

---

### `site/src/components/map/PanelFamilyBars.tsx` (EDIT — D-02 per-family glossary affordance)

**Analog:** self. Each row label (lines 81-87) is the anchor for a per-family tooltip or `#vida`/`#propiedad` glossary anchor link (zero-JS anchor nav, RESEARCH lines 654). Reuse `FAMILY_LABELS` (lines 43-51) — or switch to importing from the new `familyDefs.ts` to dedupe. Keep `aria-hidden="true"` accent-dot pattern (line 84).

---

### `site/src/pages/map.astro` + `site/src/pages/es/mapa.astro` (EDIT — build-time prop threading for D-04)

**Analog:** `is-santiago-safe.astro` lines 14-19 — the canonical build-time `loadNationalAverage()` usage (must NOT be called inside the React island; Pitfall 1):
```astro
import { loadCommune, loadNationalAverage, latestCompleteYearRate } from '../lib/data.ts';
const nationalAvg = loadNationalAverage();
```
**Current map.astro** (lines 14-37) imports only `MapIsland` and mounts `<MapIsland client:only="react" lang="en" />` (line 37). Extend frontmatter to call `loadNationalAverage()` and thread it: `<MapIsland client:only="react" lang="en" nationalAvg={nationalAvg} />`. `data.ts` `loadNationalAverage` (lines 182-191) is `fs`-backed = build-time only — confirmed.

MapIsland Props (MapIsland.tsx lines 54-56) currently `{ lang }` only — add `nationalAvg` and forward to `<ResultPanel ... />` (line 417).

---

### `site/src/styles/global.css` (EDIT — A11Y-01 focus states + READ-01 prose rhythm)

**Analog:** self. Confirmed gaps: NO `:focus-visible` rules exist (Grep returned only token + `:focus`-free matches); `p` rule at line 124 has no `margin-bottom`.

**A11Y-01 focus block** (RESEARCH lines 473-483) — add blanket rule first (Pitfall 4 — must cover `<summary>`, `.lang-btn`, nav label):
```css
*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
*:focus:not(:focus-visible) { outline: none; }
```
Reuse existing tokens `--primary: #0f766e` (line 12). **Pitfall 6:** do NOT lighten `--primary` or darken `--bg` (#0f766e on #f5f8f8 = 4.71:1, only 5% margin) — add the documenting CSS comment.

**READ-01 prose rhythm:** add `.editorial-prose p { margin-bottom: var(--md); }` (or `p + p`) — `EditorialLayout` already enforces the 720px column, so this is rhythm only.

---

### `site/src/config/i18n.ts` (EDIT — all new bilingual strings)

**Analog:** self. Add keys to `I18nStrings` interface (line 7) and to BOTH `EN_STRINGS` (line 87) and `ES_STRINGS` (line 169). New keys + values are fully specified in RESEARCH Code Examples lines 494-528 (`rate_tooltip_title/body`, `glossary_link`, `comparison_national`, `legend_qual_1..5`, `legend_per_100k_note`). Follow the existing inline-locale pattern — every prior phase added strings here.

---

### `site/src/pages/es/metodologia.astro` (EDIT — READ-02 parity)

**Analog:** `site/src/pages/methodology.astro` (EN canonical). Confirmed gap (RESEARCH lines 691-693, F-003): ES methodology ~4,174 chars vs EN ~8,849 — roughly half. Bring ES section structure to parity with EN. No new pattern — content/structure port only.

---

### `site/src/components/CommuneRankingTable.astro` + crime/region pages (EDIT — D-01/D-02 cross-links)

**Analog:** `crime/[family].astro` ranking table (lines 221-266). Add `<RateTooltip>` next to the "Rate per 100k" `<th>` (line 232) and a glossary cross-link footnote near `.rollout-note` (lines 263-265) / `MethodologyCaveat` (line 293). Reuse the zero-JS Astro `<RateTooltip>` (no `client:*`). Keep `scope="col"` header convention (lines 229-233).

---

## Shared Patterns

### Bilingual string storage
**Source:** `site/src/config/i18n.ts` (`I18nStrings` interface line 7, `EN_STRINGS`/`ES_STRINGS` lines 87/169) + inline `lang === 'es' ? ... : ...` ternaries used everywhere in React (e.g. ResultPanel.tsx lines 131, 138, 225).
**Apply to:** Every new file with user-facing copy. New keys go in i18n.ts; in-component one-offs use the inline ternary. NEVER add a new i18n library.

### CSS design tokens (no hardcoded values)
**Source:** `site/src/styles/global.css` `:root` (lines 12-17): `--primary #0f766e`, `--bg #f5f8f8`, `--ink #1c2a2b`, `--muted #5d6c6d`, `--card #ffffff`; plus `--s1..--s5` choropleth levels, `--radius`, `--line`, spacing `--xs/--sm/--md/--lg/--xl`, type `--text-label/--text-body/--text-heading/--text-display`, `--weight-strong`.
**Apply to:** All new components. DataCallout.astro (lines 31-61) and crime/[family].astro `<style>` (lines 296-517) are reference consumers. Level coloring: `var(--s${level})`.

### Locale number formatting
**Source:** `n.toLocaleString('es-CL')` (ResultPanel.tsx line 167) / `'en-US'` (crime/[family].astro line 214).
**Apply to:** Legend numeric bands (D-03), multiplier/bar values (D-04), any displayed rate.

### Zero-JS constraint (D-09)
**Source:** crime/[family].astro header comment line 19 ("Zero client:* directives (D-09)"); map.astro is the ONLY page with an island (`client:only="react"`, line 37).
**Apply to:** RateTooltip.astro, glossary pages, global.css, ranking-table edits — NO new `client:*`. The `<details>` element gives interactive tooltips with zero JS.

### Build-time data loaders are `fs`-backed (never call in browser)
**Source:** `data.ts` lines 14-20 (`node:fs`, `process.cwd()`); `loadNationalAverage` lines 182-191.
**Apply to:** D-04 — call `loadNationalAverage()` ONLY in `map.astro` frontmatter, pass result as a numeric prop (Pitfall 1).

### Decorative-element a11y
**Source:** `aria-hidden="true"` on decorative SVGs/markers/dots (ResultPanel.tsx lines 223, 295; PanelFamilyBars.tsx lines 84, 88); `aria-label` on icon-only controls (ResultPanel.tsx line 215; PageHeader home link).
**Apply to:** tooltip "?" glyph (`<span aria-hidden="true">?</span>` + `aria-label` on `<summary>`), comparison bar (`aria-hidden`, text label visible).

### JSON-LD safety
**Source:** BaseLayout.astro lines 73-74 — `JSON.stringify(jsonLd).replace(/<\//g, '<\\/')`.
**Apply to:** glossary pages if they emit a `WebPage`/`DefinedTermSet` schema — pass via the `jsonLd` prop; never hand-build a `<script>`.

---

## No Analog Found

None. Every Phase-9 file maps to a strong existing analog. This is a polish phase — all needed patterns (props-only React components, zero-JS Astro components, bilingual route pairs, CSS-token styling, build-time loaders, JSON-LD) already exist in the codebase.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | (none) |

---

## Metadata

**Analog search scope:** `site/src/components/`, `site/src/components/map/`, `site/src/pages/`, `site/src/layouts/`, `site/src/lib/`, `site/src/config/`, `site/src/styles/`
**Files scanned:** Legend.tsx, colors.ts, PanelFamilyBars.tsx, ResultPanel.tsx, crime/[family].astro, es/delito/[family].astro, BaseLayout.astro, DataCallout.astro, map.astro, is-santiago-safe.astro, data.ts (targeted), global.css (targeted), i18n.ts (targeted), MapIsland.tsx (targeted)
**Key correction vs RESEARCH:** `computeQuantileBreaks` is invoked in `ChoroplethLayer.ts`, not `MapIsland.tsx` — D-03 threading must surface breaks from ChoroplethLayer → MapIsland → Legend (RESEARCH lines 277/299 assumed MapIsland).
**Pattern extraction date:** 2026-06-15
