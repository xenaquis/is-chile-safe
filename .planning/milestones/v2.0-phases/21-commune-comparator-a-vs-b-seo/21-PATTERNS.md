# Phase 21: Commune Comparator + A-vs-B SEO — Pattern Map

**Mapped:** 2026-06-20
**Files analyzed:** 11 new/modified files
**Analogs found:** 11 / 11

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/generate-pairs.mjs` | utility / build script | batch transform | `site/scripts/sync-data.mjs` | role-match |
| `site/src/lib/comparisonProse.ts` | utility / prose engine | transform | `site/src/lib/proseEngine.ts` | exact |
| `site/src/islands/ComparatorIsland.tsx` | React island (component) | request-response + event-driven | `site/src/components/map/MapIsland.tsx` | role-match |
| `site/src/pages/compare/index.astro` | page / static shell | request-response | `site/src/pages/map.astro` | exact |
| `site/src/pages/es/comparar/index.astro` | page / static shell | request-response | `site/src/pages/map.astro` (ES mirror) | exact |
| `site/src/pages/compare/[pair].astro` | page / programmatic static | CRUD (getStaticPaths) | `site/src/pages/commune/[slug].astro` | exact |
| `site/src/pages/es/comparar/[pair].astro` | page / programmatic static | CRUD (getStaticPaths) | `site/src/pages/es/comuna/[slug].astro` | exact |
| `site/src/components/ComparatorPairsLinks.astro` | component / snippet | request-response | `site/src/components/ComparableCommune.astro` (similar list) | role-match |
| `site/scripts/validate/avs-b-budget.mjs` | validator / build assertion | batch | `site/scripts/validate/structure.mjs` | role-match |
| `site/scripts/validate/hreflang.mjs` (EXTEND) | validator | batch | self | exact |
| `site/scripts/validate/spine.mjs` (EXTEND) | validator | batch | self | exact |
| `site/src/config/i18n.ts` (EXTEND) | config | — | self | exact |

---

## Pattern Assignments

### `scripts/generate-pairs.mjs` (utility, batch transform)

**Analog:** `site/scripts/sync-data.mjs`

**Imports pattern** (sync-data.mjs lines 21–26):
```javascript
import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
```

**Path resolution pattern** (sync-data.mjs lines 28–31 — use `process.cwd()` style or `__dirname` anchoring; NOT `import.meta.url` in prerender):
```javascript
// script lives at scripts/ (repo root), so reach data/ via:
const SRC = path.resolve(__dirname, '..', 'data', 'cead', 'meta', 'index.json');
const OUT = path.resolve(__dirname, '..', 'data', 'comparator-pairs.json');
```

**Core pattern** — this script has NO direct analog (new pattern); closest is sync-data.mjs's defensive exit-on-missing-source:
```javascript
if (!existsSync(SRC)) {
  console.error(`[generate-pairs] FATAL: index.json not found at ${SRC}`);
  process.exit(1);
}
```

**Output shape** (from RESEARCH.md — new, no existing analog):
```javascript
// Output: data/comparator-pairs.json
// Array of pair objects; enabled flag gates staged rollout in getStaticPaths
[
  { cutA: "13101", cutB: "13110", region_id: "13", enabled: false },
  ...
]
// cutA < cutB lexicographically (sorted before join — deduplication guarantee)
// enabled: true for the first ~20 pairs in Wave-1; false for rest
```

**Pair generation algorithm** (no codebase analog — implement from RESEARCH.md):
```javascript
// Read index.json → group by region_id → for each region, generate C(n,2) pairs
// Sort CUT codes: [cutA, cutB].sort() to ensure canonical ordering
// Total: 5,031 pairs across 16 regions
```

---

### `site/src/lib/comparisonProse.ts` (utility, transform)

**Analog:** `site/src/lib/proseEngine.ts` (EXACT — mirror the full structure)

**Imports pattern** (proseEngine.ts lines 27–35):
```typescript
import {
  loadNationalAverage,
  loadRegionalAverage,
  nearestComparable,
  latestCompleteYearRate,
  type CommuneData,
  type ComparableResult,
} from './data.ts';
import { regionNameEs } from '../config/i18n.ts';
```

**Internal types pattern** (proseEngine.ts lines 41–49):
```typescript
type Locale = 'en' | 'es';
type Trend = 'up' | 'down' | 'stable';
type RankTier = 'top10' | 'top25' | 'mid' | 'bottom25' | 'bottom10';
type ComparisonBand = 'high_above' | 'mid_above' | 'near' | 'mid_below' | 'high_below';
```

**Helper functions pattern** (proseEngine.ts lines 69–118 — copy rankTier, comparisonBand, dominantFamily, familyName, fmt verbatim or adapt):
```typescript
function rankTier(nationalRank: number, total = 346): RankTier { ... }
function comparisonBand(signedPct: number): ComparisonBand { ... }
function dominantFamily(byFamily: Record<string, number>): [string, string] { ... }
function fmt(n: number): string {
  return n.toLocaleString('en-US', { maximumFractionDigits: 1 });
}
```

**Template interpolation helper** (proseEngine.ts lines 326–330):
```typescript
function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    key in vars ? String(vars[key as keyof typeof vars]) : `{${key}}`
  );
}
```

**Main export signature** (mirrors proseEngine.ts line 346 — adapt for two communes):
```typescript
// proseEngine.ts (existing):
export function buildCommuneProse(commune: CommuneData, locale: Locale): string

// comparisonProse.ts (new):
export function buildComparisonProse(
  commA: CommuneData,
  commB: CommuneData,
  locale: 'en' | 'es'
): string
```

**5-paragraph prose structure** (mirrors proseEngine.ts lines 407–501 — each paragraph corresponds to one uniqueness block):
```typescript
const paragraphs: string[] = [];
// Block 1: Index difference statement (non-swappable — direction A→B)
// Block 2: Per-family dominant divergence (A vs B, gap factor)
// Block 3: Trend narrative (each commune's trend direction)
// Block 4: National rank context (A rank #X vs B rank #Y of 346)
// Block 5: Regional context (same-region → regional ranks; diff region → characterization)
// Closing: CEAD attribution (mirrors EN_CLOSING / ES_CLOSING)
return paragraphs.join('\n\n');
```

**Non-swappability requirement** (from RESEARCH.md thin-content strategy):
```typescript
// Every block must include at least one DIRECTIONAL data point
// "Commune A scored 35.2, which is 14.8 points higher than Commune B's 20.4"
// is non-swappable — referencing score delta + direction by name.
```

**Forbidden language** — same constraint as proseEngine.ts (D-05 comment lines 18–20):
```typescript
// D-05 Sober language: never "zona peligrosa", "ranking definitivo",
//   "zona segura garantizada", unqualified "the safest" / "la más segura".
// Use: "higher reported incidence", "lower reported rate", "ranked {X} nationally"
```

**Word count gate** (build-time, used in getStaticPaths):
```typescript
// NOT in comparisonProse.ts itself — called from [pair].astro getStaticPaths:
const words = prose.split(/\s+/).filter(Boolean).length;
if (words < 300) throw new Error(`[CMP-04] Thin content ${cutA}-vs-${cutB}: ${words} words`);
```

---

### `site/src/islands/ComparatorIsland.tsx` (React island, event-driven)

**Analog:** `site/src/components/map/MapIsland.tsx`

**File header comment pattern** (MapIsland.tsx lines 1–13):
```typescript
/**
 * ComparatorIsland.tsx — React island for commune-to-commune comparison.
 * client:only="react" — prevents SSR; mounted on /compare/ and /es/comparar/ only.
 * No Leaflet dependency — pure React table/form; no double-init guard needed.
 */
```

**Imports pattern** (MapIsland.tsx lines 15–46 — adapt; drop Leaflet, keep React hooks):
```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
// NO Leaflet imports — this island is a pure React table component
// Import internal sub-components when extracted:
// import { ComparatorSearch } from './ComparatorSearch';
// import { ComparatorColumn } from './ComparatorColumn';
// import { FamilyComparisonTable } from './FamilyComparisonTable';
// import { AverageColumn } from './AverageColumn';
```

**Props interface pattern** (MapIsland.tsx lines 58–61):
```typescript
// MapIsland (existing):
interface Props {
  lang: 'en' | 'es';
  nationalAvg?: number;
}

// ComparatorIsland (new — extend with 346-commune index prop):
interface ComparatorEntry {
  id: string;       // CUT code
  name: string;
  region_id: string;
}
interface Props {
  lang: 'en' | 'es';
  communes: ComparatorEntry[];          // 346-item index from loadIndex() at SSG time
  nationalCompositeScore?: number;      // optional: mean composite score for avg column
}
export default function ComparatorIsland({ lang, communes, nationalCompositeScore = 0 }: Props)
```

**safeFetch helper pattern** (MapIsland.tsx lines 64–74 — copy verbatim for commune JSON fetches):
```typescript
async function safeFetch<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
```

**Accent-insensitive autocomplete** (no existing TS analog — port from resolver.py pattern per RESEARCH.md):
```typescript
// Build at island init from communes prop (no extra fetch)
const normalizeForSearch = (s: string) =>
  s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

const searchIndex = communes.map(c => ({
  ...c,
  _norm: normalizeForSearch(c.name)
}));

function searchCommunes(query: string): ComparatorEntry[] {
  const q = normalizeForSearch(query);
  return searchIndex.filter(c => c._norm.includes(q)).slice(0, 20);
}
```

**Homicide sub-row pattern** (from ResultPanel.tsx HOM-02 — existing, verified from RESEARCH.md):
```typescript
// Use !== undefined, never !falsy — 0 is valid (0 homicides, not "no data")
const homRate = data.featured_rates?.homicidios?.[String(year)];
const homCount = data.featured_rates?.homicidios_count?.[String(year)];
const hasHom = homRate !== undefined && homCount !== undefined;
// Fallback: "No reported cases — CEAD {year}" / "Sin casos reportados — CEAD {year}"
```

**latestCompleteYear client-side** (from RESEARCH.md Pitfall 3):
```typescript
// Must reproduce same filter as loadCommune() — never use partial years
const latestCompleteYear = Math.max(
  ...data.series.filter(s => !s.partial).map(s => s.year)
);
```

**Mount directive** — from map.astro line 40 (apply in Astro shell, not inside this file):
```astro
<ComparatorIsland client:only="react" lang="en" communes={communes} />
```

---

### `site/src/pages/compare/index.astro` (static shell, request-response)

**Analog:** `site/src/pages/map.astro` (EXACT)

**Full page pattern** (map.astro lines 1–41):
```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import ComparatorIsland from '../../islands/ComparatorIsland';
import MethodologyCaveat from '../../components/MethodologyCaveat.astro';
import { loadIndex } from '../../lib/data.ts';
import { EN_STRINGS } from '../../config/i18n.ts';

// Pass 346-commune index as prop — avoids client-side fetch for autocomplete
const communes = loadIndex().map(c => ({ id: c.cut, name: c.name, region_id: c.region_id }));
---

<BaseLayout
  lang="en"
  title="Compare Chile Communes — Reported Crime Data — Is Chile Safe"
  description="Select 2 or 3 communes to view reported crime statistics side by side. Source: CEAD official statistics."
  enPath="/compare/"
  esPath="/es/comparar/"
>
  <h1>{EN_STRINGS.cmp_page_h1}</h1>
  <p>{EN_STRINGS.cmp_page_lead}</p>
  <MethodologyCaveat locale="en" />
  <noscript>Enable JavaScript to use the interactive comparator. See individual commune pages for reported crime data.</noscript>
  <div id="comparator-root">
    <ComparatorIsland client:only="react" lang="en" communes={communes} />
  </div>
</BaseLayout>
```

**Critical constraint** — hardcode `esPath="/es/comparar/"` (NOT `getRelativeLocaleUrl`):
See memory note `i18n-localized-slug-pitfall` — `getRelativeLocaleUrl('es', '/compare/')` produces `/es/compare/` not `/es/comparar/`.

---

### `site/src/pages/es/comparar/index.astro` (static shell, ES mirror)

**Analog:** `site/src/pages/map.astro` + `site/src/pages/es/mapa/index.astro` pattern

Same structure as EN but:
- `lang="es"`, `enPath="/compare/"`, `esPath="/es/comparar/"`
- Import paths: `'../../../layouts/BaseLayout.astro'`, `'../../../islands/ComparatorIsland'`, etc.
- Use `ES_STRINGS.cmp_page_h1`, `ES_STRINGS.cmp_page_lead`
- `<ComparatorIsland client:only="react" lang="es" communes={communes} />`
- `<noscript>` ES text: "Activa JavaScript para usar el comparador interactivo. Consulta las páginas de cada comuna para ver datos de incidencia."

---

### `site/src/pages/compare/[pair].astro` (programmatic static, CRUD)

**Analog:** `site/src/pages/commune/[slug].astro` (EXACT getStaticPaths shape)

**Imports pattern** (commune/[slug].astro lines 15–41):
```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import MethodologyCaveat from '../../components/MethodologyCaveat.astro';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import {
  loadCommune,
  loadIndex,
} from '../../lib/data.ts';
import { buildComparisonProse } from '../../lib/comparisonProse.ts';
import { EN_STRINGS } from '../../config/i18n.ts';
```

**getStaticPaths pattern** (mirrors commune/[slug].astro lines 43–52 — adapted for pairs):
```astro
export async function getStaticPaths() {
  // Read generated allowlist — filter enabled pairs for staged rollout (CMP-07)
  const DATA_ROOT = path.resolve(process.cwd(), '..', 'data');
  const pairs = JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'comparator-pairs.json'), 'utf-8')
  ).filter(p => p.enabled);

  return pairs.map(({ cutA, cutB }) => {
    const commA = loadCommune(cutA);
    const commB = loadCommune(cutB);
    const prose = buildComparisonProse(commA, commB, 'en');
    // CMP-04 build-time thin-content assertion
    const words = prose.split(/\s+/).filter(Boolean).length;
    if (words < 300) {
      throw new Error(`[CMP-04] Thin content: ${cutA}-vs-${cutB} (${words} words, need ≥300)`);
    }
    return {
      params: { pair: `${cutA}-vs-${cutB}` },
      props: { commA, commB, prose }
    };
  });
}
```

**process.cwd() for data loading** (commune/[slug].astro pattern — enforced by memory note `news-page-build-path-drift`):
```typescript
// CORRECT: use process.cwd() in Astro pages/getStaticPaths
const DATA_ROOT = path.resolve(process.cwd(), '..', 'data');
// WRONG: import.meta.url breaks in bundled prerender chunks
```

**Page-level data extraction** (mirrors commune/[slug].astro lines 55–109):
```astro
const { commA, commB, prose } = Astro.props;
const year = commA.latestCompleteYear; // use commA's year for title/meta
const enPath = `/compare/${commA.cut}-vs-${commB.cut}/`;
const esPath = `/es/comparar/${commA.cut}-vs-${commB.cut}/`;
const title = `${commA.name} vs ${commB.name} Reported Crime Data — Is Chile Safe`;
const description = buildMetaDescription(commA, commB, 'en'); // 140–155 chars
```

**BaseLayout props pattern** (A-vs-B pages — pass lang/title/description/enPath/esPath ONLY):
```astro
<!-- NOTE: do NOT pass a jsonLd prop here. A-vs-B Schema.org JSON-LD is DEFERRED
     out of Phase 21 (21-RESEARCH.md Open Question Q3 / 21-CONTEXT.md Deferred Ideas).
     No Phase 21 plan touches site/scripts/validate/schema.mjs. BaseLayout's jsonLd
     prop is optional; omitting it is correct for A-vs-B pages (the commune page DOES
     pass jsonLd, but that wiring is out of scope for the comparison pages). -->
<BaseLayout
  lang="en"
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
>
```

**Homicide sub-row** in per-family table (from commune/[slug].astro lines 220–243 — the HOM-02 block):
```astro
{(() => {
  const homA = commA.featured_rates?.homicidios;
  const homCountA = commA.featured_rates?.homicidios_count;
  // 0 is valid — use !== undefined, never truthiness
  const homRateA = homA !== undefined && homA[String(year)] !== undefined ? homA[String(year)] : null;
  const countA = homCountA !== undefined && homCountA[String(year)] !== undefined ? homCountA[String(year)] : null;
  // Repeat for commB...
})()}
```

**MethodologyCaveat** — mandatory at bottom (commune/[slug].astro line 335):
```astro
<MethodologyCaveat locale="en" />
```

---

### `site/src/pages/es/comparar/[pair].astro` (ES mirror, CRUD)

**Analog:** `site/src/pages/es/comuna/[slug].astro` (EXACT)

Same structure as EN `[pair].astro` but:
- Import paths: `'../../../layouts/BaseLayout.astro'`, `'../../../lib/comparisonProse.ts'`, etc.
- `buildComparisonProse(commA, commB, 'es')`
- `lang="es"`, `enPath="/compare/{pair}/"`, `esPath="/es/comparar/{pair}/"`
- Use `ES_STRINGS` for UI labels
- IDENTICAL `getStaticPaths` pairs list + `enabled` filter as EN route (same commitment as ES commune mirror — guarantees hreflang reciprocity)
- Same BaseLayout-props rule: NO `jsonLd` prop (JSON-LD deferred — see EN `[pair].astro` note)

---

### `site/src/components/ComparatorPairsLinks.astro` (component, request-response)

**Analog:** `site/src/components/ComparableCommune.astro` (similar-communes list)

**Pattern** — simple Astro component rendering a `<ul>` of `<a>` links, no client JS:
```astro
---
interface Props {
  pairs: Array<{ cutA: string; cutB: string; nameA: string; nameB: string }>;
  locale: 'en' | 'es';
}
const { pairs, locale } = Astro.props;
const heading = locale === 'en' ? 'Compare with other communes' : 'Comparar con otras comunas';
const prefix = locale === 'en' ? '/compare/' : '/es/comparar/';
---
<section class="comparator-pairs-spoke">
  <h2 class="section-heading">{heading}</h2>
  <ul class="pairs-list">
    {pairs.map(({ cutA, cutB, nameA, nameB }) => (
      <li>
        <a href={`${prefix}${cutA}-vs-${cutB}/`}>{nameA} vs {nameB}</a>
      </li>
    ))}
  </ul>
</section>
```

**Style tokens** — reuse existing tokens from commune/[slug].astro:
```astro
<style>
  .comparator-pairs-spoke { margin: var(--xl) 0; }
  .pairs-list { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: var(--sm); }
  .pairs-list li a {
    display: inline-block; padding: var(--xs) var(--sm);
    border: 1px solid var(--line); border-radius: var(--radius);
    font-size: var(--text-label); color: var(--primary); text-decoration: none;
  }
</style>
```

**Where it's used** — injected into commune/[slug].astro and es/comuna/[slug].astro; receives the 3–5 same-region pairs computed at getStaticPaths time.

---

### `site/scripts/validate/avs-b-budget.mjs` (validator, batch)

**Analog:** `site/scripts/validate/structure.mjs` (closest — Node script, asserts file counts)

**Boilerplate pattern** (structure.mjs lines 1–17):
```javascript
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');
```

**Graceful dist/ missing exit** (structure.mjs lines 42–45):
```javascript
if (!existsSync(DIST_DIR)) {
  console.log('avs-b-budget: dist/ not found — run npm run build first');
  process.exit(0);
}
```

**Core assertion pattern** (new logic — count all files in dist/ recursively):
```javascript
// Count total files in dist/ recursively
function countFiles(dir) {
  let count = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) count += countFiles(full);
    else count++;
  }
  return count;
}

const SAFE_BOUND = 18000;
const totalFiles = countFiles(DIST_DIR);

if (totalFiles >= SAFE_BOUND) {
  console.error(`FAIL [CMP-05] File budget exceeded: ${totalFiles} files in dist/ (limit ${SAFE_BOUND})`);
  process.exit(1);
}
console.log(`PASS [CMP-05] File budget: ${totalFiles} files in dist/ (limit ${SAFE_BOUND}, margin ${SAFE_BOUND - totalFiles})`);
```

**A-vs-B pair count assertion** (new — verify getStaticPaths generated expected pages):
```javascript
// Count generated compare pages — each pair = 2 HTML files (EN + ES)
const compareEnDir = path.join(DIST_DIR, 'compare');
const compareEsDir = path.join(DIST_DIR, 'es', 'comparar');
// Assert symmetry: EN page count === ES page count
```

**Exit pattern** (mirrors all validators — process.exit(1) on failure, process.exit(0) on pass):
```javascript
if (failures > 0) {
  console.error(`\navs-b-budget.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}
console.log('\navs-b-budget.mjs: PASSED');
process.exit(0);
```

---

### `site/scripts/validate/hreflang.mjs` (EXTEND existing validator)

**Source:** `site/scripts/validate/hreflang.mjs` — read in full above.

**What already works** (hreflang.mjs lines 32–59):
- `findIndexFiles(DIST_DIR)` recursively collects ALL `index.html` — A-vs-B pages at `dist/compare/{pair}/index.html` and `dist/es/comparar/{pair}/index.html` are picked up automatically.
- `urlToDistPath(url)` strips base URL and appends `/index.html` — the EN↔ES URL pattern for A-vs-B (`/compare/13110-vs-13119/` ↔ `/es/comparar/13110-vs-13119/`) uses the same slug, only the prefix changes, so existing reciprocity checks work without modification.

**What needs extension** — add one count assertion at the end (optional but recommended per RESEARCH.md):
```javascript
// After the main loop, optionally assert pair count symmetry:
const comparePages = htmlFiles.filter(f => f.includes(path.join('dist', 'compare')));
const comparaPages = htmlFiles.filter(f => f.includes(path.join('dist', 'es', 'comparar')));
if (comparePages.length !== comparaPages.length) {
  console.error(`FAIL hreflang: EN compare pages (${comparePages.length}) !== ES comparar pages (${comparaPages.length})`);
  failures++;
}
```

---

### `site/scripts/validate/spine.mjs` (EXTEND — add assertion M)

**Source:** `site/scripts/validate/spine.mjs` — read in full above.

**Assertion M pattern** (mirrors assertion J, lines 199–249):
```javascript
// ASSERTION M: comparator cross-link on commune ficha pages
// Every EN commune page must contain href="/compare/"
// Every ES commune page must contain href="/es/comparar/"

if (existsSync(enCommuneDir)) {
  const enCommuneDirs = readdirSync(enCommuneDir, { withFileTypes: true })
    .filter((d) => d.isDirectory()).map((d) => d.name);

  const enCmpOffenders = [];
  for (const slug of enCommuneDirs) {
    const htmlPath = path.join(enCommuneDir, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!content.includes('href="/compare/')) {  // matches /compare/{pair}/ links
        enCmpOffenders.push(slug);
        if (enCmpOffenders.length >= 5) break;
      }
    }
  }

  if (enCmpOffenders.length === 0) {
    console.log(`PASS [M] comparator-spoke: all EN commune pages contain href="/compare/"`);
  } else {
    console.error(`FAIL [M] comparator-spoke: ${enCmpOffenders.length}+ EN commune pages missing href="/compare/": ${enCmpOffenders.join(', ')}`);
    failures++;
  }
}
// Repeat for ES: check href="/es/comparar/"
```

---

### `site/src/config/i18n.ts` (EXTEND — add 15 new keys)

**Source:** `site/src/config/i18n.ts`

**Interface extension pattern** (i18n.ts lines 7–118 — add after existing keys, by phase grouping):
```typescript
// Phase 21 — Commune Comparator
nav_compare: string;
cmp_page_h1: string;
cmp_page_lead: string;
cmp_input_placeholder: string;
cmp_empty_heading: string;
cmp_add_prompt: string;
cmp_no_match: string;
cmp_max_reached: string;
cmp_avg_column: string;
cmp_remove_aria: string;
cmp_data_error: string;
cmp_homicide_row: string;
cmp_homicide_no_data: string;
cmp_cross_links_heading: string;
avs_b_h1_pattern: string;
```

**EN_STRINGS / ES_STRINGS values** (from UI-SPEC copywriting contract — all 15 keys):
```typescript
// EN_STRINGS additions:
nav_compare: 'Compare',
cmp_page_h1: 'Compare Chile Communes — Reported Crime Data',
cmp_page_lead: 'Select 2 or 3 communes to view reported crime statistics side by side. Source: CEAD official statistics.',
cmp_input_placeholder: 'Search commune name…',
cmp_empty_heading: 'Select 2 or 3 communes to compare',
cmp_add_prompt: 'Add another commune to compare',
cmp_no_match: 'No commune found — try removing accents',
cmp_max_reached: 'Maximum 3 communes reached',
cmp_avg_column: 'Chile avg.',
cmp_remove_aria: 'Remove {name}',
cmp_data_error: 'Could not load data for {name}. Try refreshing.',
cmp_homicide_row: 'Homicide (per 100k, {year})',
cmp_homicide_no_data: 'No reported cases — CEAD {year}',
cmp_cross_links_heading: 'Compare with other communes',
avs_b_h1_pattern: '{a} vs {b} — Reported Crime Comparison',

// ES_STRINGS additions:
nav_compare: 'Comparar',
cmp_page_h1: 'Comparar Comunas de Chile — Incidencia Delictiva Reportada',
cmp_page_lead: 'Selecciona 2 o 3 comunas para ver estadísticas de incidencia delictiva en paralelo. Fuente: estadísticas oficiales CEAD.',
cmp_input_placeholder: 'Buscar nombre de comuna…',
cmp_empty_heading: 'Selecciona 2 o 3 comunas para comparar',
cmp_add_prompt: 'Agrega otra comuna para comparar',
cmp_no_match: 'No se encontró la comuna — prueba sin tildes',
cmp_max_reached: 'Máximo 3 comunas alcanzado',
cmp_avg_column: 'Prom. Chile',
cmp_remove_aria: 'Quitar {name}',
cmp_data_error: 'No se pudieron cargar los datos de {name}. Intenta recargar.',
cmp_homicide_row: 'Homicidios (por 100k, {year})',
cmp_homicide_no_data: 'Sin casos reportados — CEAD {year}',
cmp_cross_links_heading: 'Comparar con otras comunas',
avs_b_h1_pattern: '{a} vs {b} — Comparación de Incidencia Delictiva',
```

---

## Shared Patterns

### Island Hydration Directive
**Source:** `site/src/pages/map.astro` line 40
**Apply to:** `compare/index.astro`, `es/comparar/index.astro`
```astro
<MapIsland client:only="react" lang="en" nationalAvg={nationalAvg} />
<!-- becomes: -->
<ComparatorIsland client:only="react" lang="en" communes={communes} />
```
Use `client:only="react"` (NOT `client:visible`) — comparator is the above-fold primary content on its dedicated page.

### Data Loading (SSG time)
**Source:** `site/src/pages/commune/[slug].astro` lines 55–99
**Apply to:** All Astro pages that read commune data
```typescript
// Always use process.cwd() for data paths in Astro pages / getStaticPaths
// NEVER import.meta.url (breaks in prerender chunks)
const data = loadCommune(cut);  // via site/src/lib/data.ts
const year = data.latestCompleteYear;  // enriched by loadCommune(), filters !partial
```

### Homicide Data Access (HOM-02)
**Source:** `site/src/pages/commune/[slug].astro` lines 220–243
**Apply to:** `ComparatorIsland.tsx` (FamilyComparisonTable homicide sub-row), `[pair].astro` per-family table
```typescript
// 0 is valid data — ALWAYS use !== undefined, never truthiness / !falsy
const homRate = data.featured_rates?.homicidios?.[String(year)];
const homCount = data.featured_rates?.homicidios_count?.[String(year)];
const hasHom = homRate !== undefined && homCount !== undefined;
// Fallback when !hasHom: "No reported cases — CEAD {year}"
```

### Error Handling in Validators
**Source:** `site/scripts/validate/spine.mjs` lines 359–365
**Apply to:** `avs-b-budget.mjs`, hreflang.mjs extension, spine.mjs extension
```javascript
if (failures > 0) {
  console.error(`\n{validator}.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}
console.log('\n{validator}.mjs: PASSED');
process.exit(0);
```

### Forbidden Language (editorial invariant)
**Source:** `site/src/lib/proseEngine.ts` lines 18–20 (D-05 comment)
**Apply to:** `comparisonProse.ts`, all A-vs-B page templates
```typescript
// NEVER emit: "safe", "dangerous", "seguro", "peligroso" unqualified
// ALWAYS use: "higher reported incidence", "lower reported rate",
//             "ranked {X} nationally", "reported incidence data"
// forbidden-language.mjs validator scans dist/ text at build time
```

### ES Slug Hardcoding
**Source:** Memory note `i18n-localized-slug-pitfall`; used in `site/src/pages/map.astro` line 26
**Apply to:** All pages linking to `/es/comparar/`
```astro
<!-- CORRECT — hardcode the ES slug -->
esPath="/es/comparar/"
<!-- WRONG — getRelativeLocaleUrl produces /es/compare/, not /es/comparar/ -->
```

### BaseLayout enPath/esPath
**Source:** `site/src/pages/map.astro` lines 21–27
**Apply to:** `compare/index.astro`, `es/comparar/index.astro`, `compare/[pair].astro`, `es/comparar/[pair].astro`
```astro
<BaseLayout
  lang="en"
  title={title}
  description={description}
  enPath="/compare/"
  esPath="/es/comparar/"
>
```

---

## No Analog Found

All files have analogs. The following new elements have no close codebase match and must be implemented from RESEARCH.md patterns:

| Element | Role | Reason |
|---------|------|--------|
| Pair generation algorithm in `generate-pairs.mjs` | batch transform | No existing script generates cartesian-product subsets from a JSON list |
| Accent-insensitive autocomplete (TypeScript) | utility | Python analog exists in `pipeline/news/resolver.py`; TS port is new |
| `buildComparisonProse()` 5-block structure | prose engine | Directional A-vs-B prose has no existing output; structure is new even if the engine pattern (proseEngine.ts) is exact |

---

## Metadata

**Analog search scope:** `site/src/`, `site/scripts/`, `site/src/pages/`, `site/src/lib/`, `site/src/components/map/`, `site/src/config/`
**Files read:** 10 source files (proseEngine.ts, commune/[slug].astro, es/comuna/[slug].astro, map.astro, MapIsland.tsx, hreflang.mjs, spine.mjs, structure.mjs, sync-data.mjs, i18n.ts)
**Pattern extraction date:** 2026-06-20
