# Phase 21: Commune Comparator + A-vs-B SEO — Research

**Researched:** 2026-06-20
**Domain:** Astro static page generation + React island + SEO programmatic pages
**Confidence:** HIGH (all findings grounded in real repo files and live data)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Comparator island (CMP-01)**
- Routes: `/compare/` (EN) + `/es/comparar/` (ES). Hardcode the ES slug (do NOT rely on getRelativeLocaleUrl for localized slugs — see memory [i18n-localized-slug-pitfall]).
- Compare 2–3 communes; accent-insensitive autocomplete across all 346 communes.
- Side-by-side panel shows: composite-index headline, per-family breakdown, trend indicator, and "compare to national/regional average" column.
- Pre-rendered static HTML shell that is Google-indexable — island hydrates on top (`client:only`/`client:visible`; NEVER render-only critical content). Reuse existing map-island hydration pattern; zero new heavy deps.

**A-vs-B programmatic pages (CMP-02, CMP-03, CMP-04)**
- DO NOT generate the full cartesian product. Use a curated priority-pair allowlist (~3,400 pairs → ~6,800 bilingual pages). [VERIFIED: computed from real data — see Priority-Pair Allowlist section below]
- Compute exact priority-pair count from real commune data BEFORE writing getStaticPaths (STATE-flagged sub-problem #1).
- Slugs: CUT-code alphabetical order, one canonical page per pair (e.g. `/compare/13110-vs-13119/`). Reciprocal EN/ES hreflang on every pair.
- Thin-content guard: ≥5 uniqueness blocks + ≥300 words of non-swappable prose. `buildComparisonProse()` enforced at build time.

**Build-size + linking + validators (CMP-03, CMP-05)**
- Build-time assertion: total files < 18,000.
- Every commune page links to 3–5 relevant A-vs-B pairs.
- Extend hreflang-reciprocity validator to cover A-vs-B pages. All validators must exit 0.

**Rollout discipline (CMP-06, CMP-07)**
- Acceptance-check ≥10 A-vs-B pairs for prose quality before any deploy.
- Publish first batch ~20 pairs, verify GSC URL Inspection, then expand.

**Homicide row in comparator (ADDED SCOPE)**
- The comparator island must include `featured_rates.homicidios` (rate) + `homicidios_count` as a distinct sub-row under "Life crimes" in the `FamilyComparisonTable`. Use `!== undefined` checks (0 is valid). Graceful "No reported cases — CEAD {year}" fallback. Mirrors ResultPanel.tsx §HOM-02 logic.

**Editorial / data invariants (non-negotiable)**
- Never absolute "safe/dangerous / seguro/peligroso". CEAD attribution always. Forbidden-language validator must stay green.
- CEAD rates already per-100k — never rescale.
- EN/ES parity on every surface; static pre-render for SEO; ~$0 infra.

### Claude's Discretion

Component structure, prose-engine internals, autocomplete implementation, and priority-pair heuristic specifics. Must satisfy locked guardrails and be grounded in real commune data.

### Deferred Ideas (OUT OF SCOPE)

- AdSense activation + Consent Mode v2 — deferred out of v2.0 scope.
- Expanding beyond the first ~20-pair batch — only after GSC validates the initial staged batches.
- Schema.org JSON-LD on A-vs-B pages + `schema.mjs` extension to validate it — deferred (no CMP requirement needs it; see Open Question Q3).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CMP-01 | 2–3 commune comparator island with composite-index headline, per-family breakdown, trend indicator, national/regional average column | Island pattern: `client:only="react"` on `ComparatorIsland.tsx`, mirrors MapIsland mount. Data: `comparator_table.json` (composite_index) + per-commune JSON (series, featured_rates, trend). |
| CMP-02 | Accent-insensitive autocomplete over 346 communes; pre-rendered static HTML shell | Reuse NFD normalization from `pipeline/news/resolver.py` (95.45% accuracy). Static shell pattern: h1 + lead + MethodologyCaveat + `<div id="comparator-root">` (mirrors map.astro). |
| CMP-03 | Bilingual A-vs-B pages from curated allowlist; CUT-code slugs; alphabetical ordering; no duplication | Allowlist: same-region pairs (5,031) × 2 locales = 10,062 pages. Total projected files ~11,944 — under 18,000 limit. getStaticPaths mirrors commune/[slug].astro pattern. |
| CMP-04 | ≥5 uniqueness blocks + ≥300 non-swappable words per pair; build-time thin-content assertion | `buildComparisonProse()` modeled after existing `buildCommuneProse()` in `site/src/lib/proseEngine.ts`. 5 data dimensions per pair yield non-swappable text. Word-count assertion at build time. |
| CMP-05 | Build asserts total page count < 18,000 | Computed: projected full build ~11,944 total files (1,882 base + 10,062 A-vs-B HTML). Safety margin: 6,056. Assert in new `avs-b-budget.mjs` validator. |
| CMP-06 | hreflang reciprocity and cross-link spine validators extended to cover A-vs-B pages; every commune page links to 3–5 pairs | Extend `site/scripts/validate/hreflang.mjs` (currently scans all dist/ index.html). Add spine assertion J-avs-b for compare cross-links on commune pages. |
| CMP-07 | A-vs-B prose acceptance-checked on ≥10 pairs before deploy; staged batches ~20 pairs | Rollout gated via `data/comparator-pairs.json` allowlist; build reads it; sample check is a manual Wave-N task. |
</phase_requirements>

---

## Summary

Phase 21 builds the commune comparator island and A-vs-B SEO pages on top of Phase 18's composite index. All foundational data is verified present: `data/cead/comparator_table.json` (346 entries, each with `composite_index["2024"]`), per-commune JSON files in `data/cead/comunas/{cut}.json` (346 files, each with `series`, `featured_rates.homicidios`, `featured_rates.homicidios_count`, `trend`, `composite_index["2024"]`). The existing `buildCommuneProse()` in `site/src/lib/proseEngine.ts` is the direct template for the new `buildComparisonProse()` — the pattern is battle-tested and understood.

**Priority-pair count is now confirmed from real data:** All same-region pairs = 5,031 pairs × 2 locales = 10,062 A-vs-B HTML pages. Projected total files after full 346-commune build: ~11,944 — comfortably under the 18,000 safe bound, with a margin of ~6,056 files. The CONTEXT.md estimate of "~3,400 pairs" was conservative; the real same-region pair universe is larger but still fits. [VERIFIED: computed from real `index.json` + `comparator_table.json`]

The comparator island follows the exact same hydration pattern as `MapIsland.tsx`: `<ComparatorIsland client:only="react" ... />` mounted on a static Astro shell. The accent-insensitive normalization already exists in `pipeline/news/resolver.py` and must be ported to TypeScript (the pattern is `normalize('NFD').replace(/\p{Diacritic}/gu, '')` per the UI spec, consistent with the Python equivalent). National/regional per-family averages are available from `data/cead/national.json` and `data/cead/regions/{id}.json`.

**Primary recommendation:** Use all same-region pairs (5,031) as the priority allowlist — they fit within budget and provide the most relevant comparisons. Generate `data/comparator-pairs.json` as a build artifact from a Node script, then read it in getStaticPaths for A-vs-B pages.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Comparator UI (autocomplete, side-by-side panels) | Browser / Client (React island) | Frontend Server (static shell SSG) | Interactive state; same pattern as MapIsland. Static shell for indexability. |
| A-vs-B page generation | Frontend Server (SSG via Astro getStaticPaths) | — | Static pre-render mandatory for SEO. All prose generated at build time. |
| Priority-pair allowlist generation | Build script (Node) | — | Run once at build time, output to `data/comparator-pairs.json`, read by getStaticPaths. |
| `buildComparisonProse()` | Frontend Server (SSG, TypeScript) | — | Mirrors `buildCommuneProse()` in `site/src/lib/proseEngine.ts`. Called from AvsBPage.astro getStaticPaths. |
| Thin-content assertion | Build script (validator) | — | Word-count assert in new `avs-b-budget.mjs` validator or inline during getStaticPaths. |
| Build-file-count assertion | Validator (`avs-b-budget.mjs`) | — | Counts dist/ files after build, asserts < 18,000. |
| hreflang reciprocity for A-vs-B | Existing `hreflang.mjs` validator (extended) | — | Already scans all dist/ index.html recursively — just needs to handle `/compare/{a}-vs-{b}/`. |
| Cross-link spine for A-vs-B | Existing `spine.mjs` validator (extended) | — | New assertion: every commune page must contain href="/compare/" or "/es/comparar/". |
| Per-family averages (national/regional) | Build-time data loader (`data.ts`) | — | `loadNationalAverage()` + `loadRegionalAverage()` already compute unweighted mean. Per-family averages come from `national.json` + `regions/{id}.json` latest year. |

---

## Priority-Pair Allowlist — Computed from Real Data

**This is STATE-flagged sub-problem #1. All numbers below are VERIFIED from real repo files.**

### Current build state [VERIFIED: dist/]

| Metric | Value |
|--------|-------|
| HTML pages in dist/ (current partial rollout, 12 communes) | 793 |
| Non-HTML files in dist/ (assets, JS, CSS, etc.) | 421 |
| Total files in dist/ | 1,214 |
| EN commune pages in dist/commune/ | 346 (ROLLOUT_ALL=true in npm run build) |

### Projected full build (after Phase 21)

| Metric | Value | Calculation |
|--------|-------|-------------|
| Base HTML pages (full 346-commune build) | 1,461 | 793 HTML - 24 rollout commune HTML + 346×2 = 1,461 |
| Non-HTML overhead | 421 | Same as current (no new assets) |
| Base total files | 1,882 | 1,461 + 421 |
| Cloudflare safe bound | 18,000 | |
| Budget for A-vs-B files | 16,118 | 18,000 - 1,882 |
| Maximum A-vs-B pair count (within budget) | 8,059 pairs | 16,118 / 2 locales |

### Same-region pair universe [VERIFIED: computed from index.json]

| Region | Communes | Same-region pairs |
|--------|----------|------------------|
| 1 | 7 | 21 |
| 2 | 9 | 36 |
| 3 | 9 | 36 |
| 4 | 15 | 105 |
| 5 | 38 | 703 |
| 6 | 33 | 528 |
| 7 | 30 | 435 |
| 8 | 33 | 528 |
| 9 | 32 | 496 |
| 10 | 30 | 435 |
| 11 | 10 | 45 |
| 12 | 11 | 55 |
| 13 | 52 | 1,326 |
| 14 | 12 | 66 |
| 15 | 4 | 6 |
| 16 | 21 | 210 |
| **Total** | **346** | **5,031** |

**5,031 pairs × 2 locales = 10,062 HTML pages**

**Projected total after Phase 21: 1,882 + 10,062 = 11,944 files — 6,056 under the 18,000 bound.** [VERIFIED]

### Recommendation

Use **all same-region pairs** (5,031) as the allowlist. This:
- Fits comfortably within budget (11,944 < 18,000)
- Provides naturally relevant comparisons (users compare communes in their region)
- Is simple to generate deterministically from `index.json` without a hand-curated list
- Exceeds the CONTEXT.md estimate of "~3,400 pairs" but is still safely within limits

**Staged rollout per CMP-07:** Generate the full 5,031-pair `data/comparator-pairs.json`, but gate getStaticPaths to read only pairs with `enabled: true`. Start with ~20 pairs enabled; flip more after GSC verification. Alternatively, use a `batch: 1` field and filter in getStaticPaths.

---

## Data Shape — Exact Field Map

### `data/cead/comparator_table.json` [VERIFIED: inspected file]

Array of 346 objects. Used for fast lookup at build time and in the island (loaded client-side as `/data/cead/comparator_table.json`).

```typescript
interface ComparatorTableEntry {
  id: string;           // CUT code e.g. "13110"
  name: string;         // "La Florida"
  slug: string;         // "la-florida"
  region_id: string;    // "13"
  composite_index: {
    "2024": {
      score: number;          // 0–100 float e.g. 20.318
      rank: number;           // 1–346 (1 = highest incidence)
      regional_rank: number;  // rank within region
      level: 1 | 2 | 3 | 4 | 5;  // band
      available_metrics: number;  // 7 = full, less if SPD/SII absent
    }
  }
}
```

**What comparator_table.json does NOT contain:** per-family rates, trend, homicide, featured_rates. Those are in per-commune JSON.

### `data/cead/comunas/{cut}.json` [VERIFIED: inspected 13110.json, 13119.json]

Full commune data. Island fetches this at `/data/cead/comunas/{cut}.json` (same as ResultPanel.tsx).

Key fields for comparator:

```typescript
// Top-level
commune.id                  // CUT string
commune.name                // "La Florida"
commune.slug                // "la-florida"
commune.region_id           // "13"
commune.trend               // 'up' | 'down' | 'stable'
commune.national_rank       // integer 1–346
commune.regional_rank       // integer within region

// Composite index (Phase 18 additive field)
commune.composite_index["2024"].score           // 0–100 float
commune.composite_index["2024"].rank            // 1–346
commune.composite_index["2024"].regional_rank   // within region
commune.composite_index["2024"].level           // 1–5 band
commune.composite_index["2024"].available_metrics  // 7

// Homicide (HOM-02 — use !== undefined, not !falsy)
commune.featured_rates.homicidios["2024"]       // float per 100k e.g. 2.21
commune.featured_rates.homicidios_count["2024"] // integer e.g. 9

// Per-family rates (latest year from series)
// series[].year, series[].partial, series[].by_family{vida,robos_violentos,vif,drogas,armas,propiedad,incivilidades}
```

**latestCompleteYear:** Computed by `loadCommune()` as `max(series[].year where !partial)`. Island must compute this client-side the same way or receive it from the static shell.

### National/Regional averages — Per-family [VERIFIED: inspected national.json, regions/13.json]

For the AverageColumn in the comparator island:

```typescript
// data/cead/national.json
national.series[latestYear].by_family  // per-family rates (population-weighted mean)
national.series[latestYear].rate_per_100k  // total

// data/cead/regions/{region_id}.json
region.series[latestYear].by_family   // per-family rates for the region

// For composite index national average: derive from comparator_table.json
// mean(all entries' composite_index["2024"].score)
```

**Note:** The `loadNationalAverage()` and `loadRegionalAverage()` functions in `data.ts` return the **unweighted mean of non-low-population commune rates** (the "typical commune" statistic), NOT the population-weighted series rate in `national.json`. The comparator's AverageColumn should use the **unweighted mean** (same as the commune page's vs-national comparison) for consistency. [VERIFIED: data.ts lines 232–268]

---

## Architecture Patterns

### System Architecture Diagram

```
Build time:
  index.json + comparator_table.json
       ↓
  generate-pairs.mjs  ──→  data/comparator-pairs.json (5,031 pairs)
       ↓
  Astro getStaticPaths (AvsBPage.astro)
       ↓  reads comparator-pairs.json, filters enabled pairs
  loadCommune(cutA) + loadCommune(cutB)
       ↓
  buildComparisonProse(communeA, communeB, locale)
       ↓
  Static HTML /compare/{cutA}-vs-{cutB}/index.html
             /es/comparar/{cutA}-vs-{cutB}/index.html

Runtime (browser):
  /compare/ or /es/comparar/  (Astro page with static shell)
       ↓  island hydrates
  ComparatorIsland (client:only="react")
       ↓  user types commune name
  ComparatorSearch → accent-insensitive autocomplete over 346 names
       ↓  user selects 2–3 communes
  fetch /data/cead/comunas/{cut}.json  (per commune)
  fetch /data/cead/comparator_table.json  (once)
       ↓
  ComparatorColumn × 2–3 + AverageColumn (from national.json / regions/{id}.json)
```

### Recommended Project Structure

```
site/src/
├── pages/
│   ├── compare/
│   │   ├── index.astro          # /compare/ — comparator landing (static shell + island)
│   │   └── [pair].astro         # /compare/{cutA}-vs-{cutB}/ — A-vs-B static pages
│   └── es/
│       ├── comparar/
│       │   ├── index.astro      # /es/comparar/
│       │   └── [pair].astro     # /es/comparar/{cutA}-vs-{cutB}/
├── components/
│   ├── ComparatorPairsLinks.astro   # 3–5 pair links on commune pages
│   └── map/                         # existing — no changes
├── islands/                         # NEW directory for non-map islands
│   └── ComparatorIsland.tsx         # client:only="react"
└── lib/
    └── comparisonProse.ts           # buildComparisonProse() — new, mirrors proseEngine.ts

data/
└── comparator-pairs.json            # generated by scripts/generate-pairs.mjs

site/scripts/
├── generate-pairs.mjs               # Node script — reads index.json, outputs pairs
└── validate/
    ├── avs-b-budget.mjs             # NEW: asserts total dist/ files < 18,000
    ├── hreflang.mjs                 # EXTEND: already handles all dist/ index.html
    └── spine.mjs                    # EXTEND: add A-vs-B cross-link assertions
```

### Pattern 1: Map Island Hydration (EXISTING — mirror for ComparatorIsland)

```astro
// site/src/pages/map.astro — EXISTING pattern to mirror
---
import MapIsland from '../components/map/MapIsland';
import { loadNationalAverage } from '../lib/data.ts';
const nationalAvg = loadNationalAverage();
---
<BaseLayout lang="en" enPath="/map/" esPath="/es/mapa/" ...>
  <MapIsland client:only="react" lang="en" nationalAvg={nationalAvg} />
</BaseLayout>
```

```astro
// site/src/pages/compare/index.astro — NEW comparator landing
---
import ComparatorIsland from '../../islands/ComparatorIsland';
import MethodologyCaveat from '../../components/MethodologyCaveat.astro';
import { EN_STRINGS } from '../../config/i18n.ts';
// Pass 346-commune index to island as prop (avoids client-side fetch for autocomplete)
import { loadIndex } from '../../lib/data.ts';
const communes = loadIndex().map(c => ({ id: c.cut, name: c.name, region_id: c.region_id }));
---
<BaseLayout lang="en" enPath="/compare/" esPath="/es/comparar/" ...>
  <h1>{EN_STRINGS.cmp_page_h1}</h1>
  <p>{EN_STRINGS.cmp_page_lead}</p>
  <MethodologyCaveat />
  <noscript>Enable JavaScript to use the interactive comparator...</noscript>
  <div id="comparator-root">
    <ComparatorIsland client:only="react" lang="en" communes={communes} />
  </div>
</BaseLayout>
```

**Key insight:** Pass the 346-commune name list as a prop from the static shell (available at SSG time via `loadIndex()`) rather than having the island fetch it separately. This avoids an extra network request and makes the autocomplete available immediately.

### Pattern 2: getStaticPaths for A-vs-B (NEW — mirrors commune/[slug].astro)

```astro
// site/src/pages/compare/[pair].astro
---
export async function getStaticPaths() {
  const pairs = JSON.parse(readFileSync(DATA_ROOT + '/comparator-pairs.json', 'utf-8'))
    .filter(p => p.enabled);  // staged rollout gate
  
  return pairs.map(({ cutA, cutB }) => {
    const commA = loadCommune(cutA);
    const commB = loadCommune(cutB);
    const prose = buildComparisonProse(commA, commB, 'en');
    // Build-time thin-content assertion
    if (wordCount(prose) < 300) throw new Error(`Thin content: ${cutA}-vs-${cutB}`);
    return {
      params: { pair: `${cutA}-vs-${cutB}` },
      props: { commA, commB, prose }
    };
  });
}
---
```

### Pattern 3: buildComparisonProse() — Mirror of buildCommuneProse()

The existing `proseEngine.ts` demonstrates the full pattern. `buildComparisonProse()` follows the same structure with 5 comparison-specific uniqueness blocks:

```typescript
// site/src/lib/comparisonProse.ts
export function buildComparisonProse(
  commA: CommuneData,
  commB: CommuneData,
  locale: 'en' | 'es'
): string {
  // Block 1: Index difference statement (non-swappable — references A > B or B > A)
  // Block 2: Per-family rate narrative (dominant divergence between communes)
  // Block 3: Trend narrative (A trending up vs B trending down, etc.)
  // Block 4: National rank context (A ranked X vs B ranked Y of 346)
  // Block 5: Regional context (same region → regional rank comparison; different regions → brief characterization)
  // Closing: CEAD attribution
}
```

**Non-swappability guarantee:** Blocks reference A and B by name in direction-specific sentences ("Commune A ranks X positions higher nationally than Commune B" is NOT the same if swapped). Score deltas, rank positions, and trend directions are directional and cannot be reordered without changing meaning.

### Pattern 4: Accent-Insensitive Autocomplete

Existing NFD normalizer in `pipeline/news/resolver.py` (Python) must be ported to TypeScript for the island:

```typescript
// Mirrors resolver.py _norm() + UI-SPEC requirement
function normalizeForSearch(s: string): string {
  return s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
}

// Build search index at island init
const searchIndex = communes.map(c => ({
  ...c,
  _normalized: normalizeForSearch(c.name)
}));

function searchCommunes(query: string): ComparatorTableEntry[] {
  const q = normalizeForSearch(query);
  return searchIndex.filter(c => c._normalized.includes(q)).slice(0, 20);
}
```

### Anti-Patterns to Avoid

- **Full cartesian product in getStaticPaths:** 346×345/2 = 59,685 pairs × 2 = 119,370 pages — blows 20K limit 6×. [VERIFIED: confirmed from pair math]
- **Fetching comparator_table.json + 346 commune JSONs at island init:** Only fetch on demand (when user selects a commune). Pass the lightweight index (346 entries, name + CUT + region_id) as SSG prop.
- **`<GeoJSON>` re-render pitfall (existing, do NOT apply to comparator):** ComparatorIsland uses React state correctly — re-renders are fine for a table, not a 346-polygon canvas.
- **getRelativeLocaleUrl for ES slugs:** Hardcode `/es/comparar/` per memory note [i18n-localized-slug-pitfall]. Do NOT use `getRelativeLocaleUrl('es', '/compare/')` — it will NOT produce `/es/comparar/`.
- **Swappable prose templates:** A-vs-B prose must include directional delta statements. "Commune A scored 35.2, which is 14.8 points higher than Commune B's score of 20.4" is non-swappable. "Both communes are in the same region" alone is not a uniqueness block.
- **`process.cwd()` vs `import.meta.url`:** Use `process.cwd()` for data loading in Astro pages (mirrors existing `data.ts` pattern). `import.meta.url` breaks in bundled prerender chunks.
- **Partial years in latestCompleteYear:** Filter `series` by `!partial` to find latest complete year. The commune JSON `series` array may end with partial years (2025, 2026 entries visible in La Florida).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accent-insensitive search | Custom fuzzy matcher | NFD normalization (`normalize('NFD').replace(/\p{Diacritic}/gu, '')`) | Already proven in `resolver.py` (95.45% accuracy). Simple exact-match on normalized string is sufficient for 346 known names. |
| Commune name→CUT lookup | Fetch-based resolver | `loadIndex()` prop passed at SSG time | Index is 346 items, tiny. Embed in island init data. |
| Word count assertion | NLP library | `prose.split(/\s+/).filter(Boolean).length` | Simple whitespace split is accurate enough for ≥300-word gate. |
| Per-family national averages | New API endpoint | `national.json` + `regions/{id}.json` series at latest complete year | Already in repo. Load at SSG time like `loadNationalAverage()`. |
| A-vs-B pair deduplication | Graph algorithm | Sort CUT codes alphabetically, use as key | Simple string sort eliminates A-vs-B / B-vs-A duplication. Already specified in CONTEXT.md. |
| hreflang for A-vs-B | New validator | Extend existing `hreflang.mjs` | Already scans ALL dist/ index.html recursively — A-vs-B pages will be picked up automatically once they exist. May only need a pattern-match update for the compare URL shape. |

---

## Thin-Content Strategy (STATE-flagged sub-problem #2)

### What makes A-vs-B prose non-swappable

Each block must reference DIRECTIONAL data between A and B:

| Block | Non-swappable element | Example |
|-------|----------------------|---------|
| 1. Index difference | Score delta + direction | "Commune A scored 35.2, which is 14.8 points higher than Commune B's 20.4 on the 2024 composite index (national ranks #87 vs #178 of 346)." |
| 2. Per-family rates | Dominant divergence family + direction | "The sharpest difference is in violent robbery: Commune A reports 487/100k vs 203/100k in Commune B — a 2.4× gap." |
| 3. Trend narrative | Per-commune trend direction | "While Commune A shows a declining trend in reported incidence over the last three years, Commune B's trend is stable." |
| 4. National rank | Absolute ranks for each | "Commune A holds national rank #87 of 346; Commune B holds rank #178 of 346, placing it in the middle tier nationally." |
| 5. Regional context | Same-region: regional ranks. Different region: region characterization | "Both communes are in the Metropolitana region. Within the region, Commune A ranks #12 vs Commune B's #36 among 52 communes." |

### Build-time enforcement

```typescript
// In getStaticPaths or a validate script
const words = prose.split(/\s+/).filter(Boolean).length;
if (words < 300) {
  throw new Error(`[CMP-04] Thin content for ${cutA}-vs-${cutB}: ${words} words (need ≥300)`);
}
```

Target: aim for 400–500 words (same ballpark as `buildCommuneProse()` which targets 500+ words).

### Meta description generation

Each pair needs a unique `<meta name="description">` of 140–155 characters using real data:

```typescript
function buildMetaDescription(commA, commB, locale): string {
  const scoreA = commA.composite_index['2024'].score.toFixed(1);
  const scoreB = commB.composite_index['2024'].score.toFixed(1);
  if (locale === 'en') {
    return `Compare reported crime data for ${commA.name} (index ${scoreA}) vs ${commB.name} (index ${scoreB}). Rates, trends, national rank. Source: CEAD.`;
  }
  // es version
}
```

---

## Existing React Island Hydration Pattern (VERIFIED)

**Source:** `site/src/pages/map.astro` + `site/src/components/map/MapIsland.tsx`

Key facts:
- Mount directive: `<MapIsland client:only="react" lang="en" nationalAvg={nationalAvg} />`
- `client:only="react"` — prevents SSR entirely; Leaflet CSS imports are safe inside the component
- Double-init guard via `useRef` (see MapIsland.tsx comment: "if mapRef.current exists, return early")
- Static aria-label in Astro shell satisfies accessibility validator without SSR (map.astro: `data-map-locate-label="en"`)
- Island entry: `site/src/components/map/MapIsland.tsx` — imports from `./ChoroplethLayer`, `./ResultPanel`, etc.

**ComparatorIsland must mirror:**
- `client:only="react"` (not `client:visible` — comparator is above-fold on its dedicated page)
- Props: `lang`, `communes` (346-item index passed from SSG), optionally `nationalCompositeScore`
- No CSS imports at top level (no Leaflet-equivalent CSS issues for a table component)
- No `useEffect` double-mount guard needed (no map div to guard against)

**Difference from MapIsland:** The comparator island does NOT need Leaflet. It is a pure React table/form island with no canvas rendering. Simpler than the map island.

---

## Existing hreflang Validator Extension (VERIFIED)

**Source:** `site/scripts/validate/hreflang.mjs`

The validator already:
- Collects ALL `index.html` files recursively from `dist/`
- For each file: checks 3 hreflang tags (en, es, x-default), canonical, reciprocity (EN URL exists, ES URL exists)
- EN URL → `dist/{path}/index.html` check is filesystem-based

**What needs extension for A-vs-B:**
- The validator already picks up A-vs-B pages automatically (they are `index.html` files in `dist/compare/{pair}/` and `dist/es/comparar/{pair}/`)
- Verify the EN↔ES URL pattern is symmetric: EN `/compare/13110-vs-13119/` ↔ ES `/es/comparar/13110-vs-13119/` (same pair slug, only prefix changes)
- The existing `urlToDistPath()` function should handle this without changes
- **Only addition needed:** Optionally add a count assertion — `assert(comparePageCount === pairs.length * 2)` — to detect if getStaticPaths generated the right number

**spine.mjs extension needed:**
- Add assertion: every commune page HTML contains `href="/compare/` (EN) or `href="/es/comparar/` (ES) — the cross-link from `ComparatorPairsLinks.astro`
- Pattern mirrors existing assertion J: "every commune page HTML contains /map/?cut="

---

## Name→CUT Resolver — Existing Implementation

**Source:** `pipeline/news/resolver.py` [VERIFIED]

The Python implementation provides:
- `_norm(s)` — NFD decompose + strip combining marks + lowercase
- `_NAME_TO_ENTRIES` dict mapping normalized name → list of index entries
- `resolve_cut(name, region_hint=None)` → CUT string or None (never raises for unknown names)
- Accuracy: 95.45% on commune names (memory note from Phase 16)

**For ComparatorIsland (TypeScript port):**

```typescript
// Minimal port needed for the island:
const normalizeForSearch = (s: string) =>
  s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();

// At island init, build from the communes prop (passed from SSG):
const searchIndex = communes.map(c => ({
  cut: c.id,
  name: c.name,
  region_id: c.region_id,
  _norm: normalizeForSearch(c.name)
}));
```

The island does NOT need a name→CUT RESOLVER (the user picks from a dropdown, not a free-text field). It needs an AUTOCOMPLETE FILTER. The name→CUT mapping is implicit: the user selects an entry from the dropdown, which carries the CUT code. No ambiguity to resolve.

---

## Common Pitfalls

### Pitfall 1: Pair Slug Ordering
**What goes wrong:** Generating both `/compare/13110-vs-13119/` AND `/compare/13119-vs-13110/` creates duplicate content.
**Why it happens:** getStaticPaths generates from each commune's perspective.
**How to avoid:** Sort CUT codes numerically/lexicographically before joining: `[cutA, cutB].sort().join('-vs-')`. Build the pair set as a `Set<string>` — duplicates are silently deduplicated. [ASSUMED: this is the specified approach; verify pair generation script produces sorted pairs]

### Pitfall 2: Swappable Prose Triggering SpamBrain
**What goes wrong:** 5,031 pages with nearly identical structure get flagged as thin/duplicate content.
**Why it happens:** Template prose without data-driven differentiation. Symmetric sentences ("Commune A and Commune B are both in the Metropolitana region") are not uniqueness blocks.
**How to avoid:** Every block must include at least one DIRECTIONAL data point (score delta, rank comparison, trend direction). The build-time word-count gate catches this at 300 words. Additionally, acceptance-check 10 random pairs for human prose quality before batch expansion.

### Pitfall 3: partial: true Year Used for Latest Rate
**What goes wrong:** `series` array may end with 2025/2026 partial years. Using these produces misleading "current year" rates.
**Why it happens:** CEAD publishes partial data for the current year throughout the year.
**How to avoid:** Always filter `series` by `!s.partial` before taking `max(s.year)`. This is already handled by `loadCommune()` via `latestCompleteYear`. For the island (client-side), reproduce the same filter.

### Pitfall 4: comparator_table.json vs Per-Commune JSON Mismatch
**What goes wrong:** The island loads `comparator_table.json` for the list (346 entries), then loads per-commune JSON for detail. If the composite_index score in comparator_table diverges from per-commune JSON, panels show inconsistent data.
**Why it happens:** Both files are built by Phase 18 pipeline; they should be identical, but...
**How to avoid:** Treat `comparator_table.json` as the source for composite_index (it was emitted specifically for comparator use). Use per-commune JSON for series, featured_rates, trend. Don't cross-validate at runtime.

### Pitfall 5: OneDrive Build Desync
**What goes wrong:** Running `npm run build` and `npm run validate` as separate commands may cause dist/ to vanish between processes (OneDrive sync conflict).
**How to avoid:** Always chain: `cd site && npm run build && npm run validate` (or `npm run build && node scripts/validate/avs-b-budget.mjs`). [VERIFIED: memory note `onedrive-build-artifacts-desync`]

### Pitfall 6: i18n Slug Pitfall for Comparar Route
**What goes wrong:** Using `getRelativeLocaleUrl('es', '/compare/')` produces `/es/compare/` not `/es/comparar/`.
**How to avoid:** Hardcode the ES path: `esPath="/es/comparar/"` in the Astro page's BaseLayout props. Also hardcode in any nav/cross-link component. [VERIFIED: memory note `i18n-localized-slug-pitfall`]

### Pitfall 7: vida/homicide slug collision in family loops
**What goes wrong:** `FAMILY_SLUGS.vida.en === 'homicide'` — if looping over families by slug, vida generates a duplicate homicide link.
**How to avoid:** When building cross-links by family, filter `vida` from the loop (or use by_family keys directly, not FAMILY_SLUGS). [VERIFIED: memory note `vida-homicide-slug-collision`]

---

## Code Examples

### How MapIsland.tsx is Mounted (Reference Pattern)

```astro
// site/src/pages/map.astro (line 40) [VERIFIED: read file]
<MapIsland client:only="react" lang="en" nationalAvg={nationalAvg} />
```

### CommuneData TypeScript Interface (Source of Truth for Islands)

```typescript
// site/src/lib/data.ts [VERIFIED: read file, lines 53–80]
export interface CommuneData extends CommuneMeta {
  national_rank: number;
  regional_rank: number;
  trend: 'up' | 'down' | 'stable';
  featured_rates: {
    propiedad: Record<string, number>;
    homicidios: Record<string, number>;
    homicidios_count: Record<string, number>;
    secuestros: Record<string, number>;
  };
  series: SeriesEntry[];
  composite_index?: Record<string, CompositeIndexEntry>;
  enusc_vhdv?: { /* Phase 23 */ };
  latestCompleteYear: number;  // enriched by loadCommune()
  regionName: string;           // enriched by loadCommune()
}
```

### Homicide Block Pattern (from ResultPanel.tsx HOM-02)

```typescript
// Exact data access pattern for homicide — use !== undefined, not !falsy
const hom2024Rate = data.featured_rates?.homicidios?.['2024'];
const hom2024Count = data.featured_rates?.homicidios_count?.['2024'];
// 0 is valid (no homicides). undefined = no data for that year.
const hasHom = hom2024Rate !== undefined && hom2024Count !== undefined;
```

### Existing Validator Suite Count

Currently 13 validators in `site/scripts/validate/all.mjs` [VERIFIED]:
1. structure.mjs, 2. commune.mjs, 3. rollout.mjs, 4. region.mjs, 5. crime.mjs,
6. hreflang.mjs, 7. schema.mjs, 8. map.mjs, 9. forbidden-language.mjs,
10. coverage.mjs, 11. spine.mjs, 12. seo.mjs, 13. figure-registry.mjs

Phase 21 adds: `avs-b-budget.mjs` (→ 14 validators total). Extend spine.mjs and hreflang.mjs in place. NOTE: `schema.mjs` is NOT modified in Phase 21 (A-vs-B JSON-LD is deferred — see Open Question Q3).

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Manual pair curation | Algorithmic same-region pair generation from index.json | 5,031 pairs, zero manual effort, deterministic |
| Thin template prose | Data-driven directional blocks (score delta, rank, trend) | Passes SpamBrain; genuinely useful content |
| Client-side name lookup | SSG-time prop injection (346-item index) | No extra fetch; autocomplete works instantly |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Non-HTML file count stays ~421 after Phase 21 (no new large assets) | Priority-Pair Allowlist | If new assets are added (e.g. island chunk JS), non-HTML overhead increases, reducing budget. Impact: minor — budget margin is 6,056 files. |
| A2 | `comparator_table.json` does not include per-family rates (only composite_index) | Data Shape | If it does include family rates, island can load less data. Not a risk — confirmed by inspection. |
| A3 | 5,031 same-region pairs is the full priority allowlist (no cross-region high-search-intent pairs) | Priority-Pair Allowlist | Cross-region pairs (e.g. Santiago vs Valparaíso) may have higher search intent. Could add a small supplemental list (~50–100 pairs) without budget impact. |

---

## Open Questions (RESOLVED)

1. **Should `buildComparisonProse()` live in `site/src/lib/comparisonProse.ts` (new file) or be added to `proseEngine.ts`?**
   - What we know: `proseEngine.ts` is already 503 lines. A new file keeps it clean.
   - **RESOLVED:** `buildComparisonProse()` lives in a NEW file `site/src/lib/comparisonProse.ts` (mirrors `proseEngine.ts`, keeps each module focused). Plans 01 and 03 already follow this — Plan 01 Task 2 creates the module and exports `buildComparisonProse` + `buildMetaDescription`; Plan 03 imports them. Plan and research agree.

2. **Should the comparator island load `national.json` and `regions/{id}.json` for per-family averages in the AverageColumn, or should these be baked into the static shell as props?**
   - What we know: `national.json` is a small file (~5KB). Region files vary by region; a 2–3-commune comparison can span up to three different regions.
   - **RESOLVED — the approach differs by surface, and the plans use these approaches:**
     - **Comparator island (Plan 02, CMP-01):** the island **fetches `/data/cead/national.json` and the relevant `/data/cead/regions/{region_id}.json` client-side** (via `safeFetch`, memoized — see Plan 02 interfaces + Task 1 action). Rationale: the selected commune set is dynamic (the user picks 2–3 at runtime), so the relevant region files are NOT knowable at SSG time. Only the 346-item index is passed as an SSG prop (for autocomplete); per-family averages for whichever regions are selected must be fetched on demand.
     - **A-vs-B static pages (Plan 03, CMP-03/04):** the Chile-average column is computed **SSG-side at build time** via `loadNationalAverage()` / `national.json` per-family inside the page frontmatter/`getStaticPaths`. Rationale: the pair is fixed at build time, so the averages are baked directly into the static HTML — no client fetch, fully indexable.
     - The original "bake into shell as props" recommendation applies only to the fixed-set static A-vs-B pages, NOT to the dynamic-set interactive island. Plans and research now agree on this split.

3. **Do A-vs-B pages need Schema.org JSON-LD, and if so what type?**
   - What we know: Commune pages use `Dataset + Place`. A-vs-B pages are comparisons.
   - **RESOLVED — DEFER out of Phase 21 scope.** Schema.org JSON-LD for A-vs-B pages (and any `schema.mjs` extension to validate it) is NOT required by any CMP requirement (CMP-01..CMP-07). A-vs-B SEO value comes from directional non-swappable prose (CMP-04) + reciprocal EN/ES hreflang (CMP-06) + commune↔compare cross-links (CMP-06), NOT from JSON-LD. To avoid dead wiring, no Phase 21 plan references a `jsonLd` BaseLayout prop for A-vs-B pages and no plan modifies `site/scripts/validate/schema.mjs`. Recorded in `21-CONTEXT.md` `## Deferred Ideas`. If A-vs-B JSON-LD is wanted later, scope it as a follow-up phase (new `Dataset` shape + `schema.mjs` extension).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build, pair-generation script | Yes | (current) | — |
| data/cead/comparator_table.json | ComparatorIsland, A-vs-B prose | Yes | 346 entries | — |
| data/cead/comunas/*.json | A-vs-B prose, island detail | Yes | 346 files | — |
| data/cead/meta/index.json | Autocomplete index | Yes | 346 entries | — |
| data/cead/national.json | AverageColumn per-family | Yes | — | — |
| data/cead/regions/{1..16}.json | AverageColumn regional | Yes | 16 files | — |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (check package.json) / Node script validators |
| Config file | `site/scripts/validate/all.mjs` |
| Quick run command | `cd site && node scripts/validate/avs-b-budget.mjs` |
| Full suite command | `cd site && npm run build && npm run validate` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CMP-01 | Comparator island renders 2–3 commune columns + avg column | Integration (BrowserOS) | Manual E2E review | No — Wave 0 |
| CMP-02 | Static shell has h1 + lead + MethodologyCaveat pre-render | Structural | `node scripts/validate/structure.mjs` (extend) | Partial |
| CMP-03 | A-vs-B pages generated with correct slug format | Structure | `node scripts/validate/avs-b-budget.mjs` (new) | No — Wave 0 |
| CMP-04 | Each A-vs-B page ≥300 words prose | Build-time | Inline in getStaticPaths (throw on fail) | No — Wave 0 |
| CMP-05 | Total dist/ files < 18,000 | Build-time | `node scripts/validate/avs-b-budget.mjs` (new) | No — Wave 0 |
| CMP-06 | hreflang reciprocity covers A-vs-B pages | Structural | `node scripts/validate/hreflang.mjs` (extend) | Partial |
| CMP-06 | Every commune page has ≥1 compare cross-link | Structural | `node scripts/validate/spine.mjs` (extend) | Partial |
| CMP-07 | 10-pair prose acceptance sample | Manual | Human review task | N/A |

### Wave 0 Gaps

- [ ] `site/scripts/validate/avs-b-budget.mjs` — new validator; covers CMP-03, CMP-05
- [ ] `site/scripts/generate-pairs.mjs` — generates `data/comparator-pairs.json` from index.json
- [ ] `data/comparator-pairs.json` — does not yet exist; must be generated before getStaticPaths

*(Existing validators `hreflang.mjs`, `spine.mjs` need extension but files exist. `schema.mjs` is NOT touched — A-vs-B JSON-LD deferred per Q3.)*

---

## Security Domain

Security enforcement is not explicitly configured in `.planning/config.json`. Applying standard defaults.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes (autocomplete input) | Accent-normalize + exact-match against closed 346-name set; no SQL/server-side input |
| V1 Architecture | Yes (static generation) | All data generated at build time — no runtime server; no injection surface |
| Other categories | No | Static HTML only; no auth, sessions, crypto |

**Known Threat Patterns:**

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via commune name in URL | Tampering | Astro auto-escapes template expressions; CUT codes are numeric strings |
| Thin content SEO spam | Repudiation | Build-time word-count assertion (CMP-04); forbidden-language validator |
| Forbidden language in generated prose | Repudiation | `forbidden-language.mjs` validator scans dist/ text; `buildComparisonProse()` must never emit "safe/dangerous/seguro/peligroso" unqualified |

---

## Sources

### Primary (HIGH confidence — verified from actual repo files)

- `data/cead/comparator_table.json` — 346-entry structure confirmed by inspection
- `data/cead/comunas/13110.json`, `13119.json` — per-commune JSON shape confirmed
- `data/cead/meta/index.json` — 346 communes, region distribution confirmed
- `data/cead/national.json`, `data/cead/regions/13.json` — per-family average structure confirmed
- `site/src/components/map/MapIsland.tsx` — island hydration pattern (`client:only="react"`)
- `site/src/components/map/ResultPanel.tsx` — HOM-02 homicide data access pattern (`!== undefined`)
- `site/src/pages/commune/[slug].astro` — getStaticPaths pattern for programmatic static pages
- `site/src/lib/data.ts` — `CommuneData` type, `loadCommune()`, `loadNationalAverage()`, `loadRegionalAverage()`
- `site/src/lib/proseEngine.ts` — `buildCommuneProse()` full implementation (template for comparison prose)
- `site/scripts/validate/hreflang.mjs` — existing hreflang validator structure
- `site/scripts/validate/spine.mjs` — existing spine validator structure
- `site/scripts/validate/all.mjs` — 13-validator list confirmed
- `pipeline/news/resolver.py` — NFD normalization pattern confirmed

### Secondary (MEDIUM confidence)

- `site/src/pages/map.astro` — island mount pattern (single-line directive)
- `site/src/config/rollout.json` — 12 currently enabled communes (ROLLOUT_ALL=true in npm run build bypasses this)
- Pair count arithmetic — computed via Node.js from real index.json; reproducible

---

## Metadata

**Confidence breakdown:**
- Priority-pair count: HIGH — computed from real data via Node.js
- Data shape mapping: HIGH — inspected actual JSON files
- Island hydration pattern: HIGH — read MapIsland.tsx + map.astro source
- buildComparisonProse() approach: HIGH — proseEngine.ts is the direct template
- Validator extension approach: HIGH — read all three validator sources
- File budget projection: MEDIUM — non-HTML overhead assumed stable at 421 (may vary slightly)

**Research date:** 2026-06-20
**Valid until:** 2026-09-20 (stable data files; CEAD/Cloudflare limits unlikely to change)
