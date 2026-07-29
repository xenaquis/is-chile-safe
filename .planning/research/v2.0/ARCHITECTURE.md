# Architecture Patterns — v2.0 New Feature Integration

**Domain:** Chile Safety Map — composite index, commune comparator, A-vs-B SEO pages
**Researched:** 2026-06-19
**Scope:** NEW features only; existing architecture is not redesigned

---

## Current Architecture Baseline (integrate with)

```
pipeline/                    Python 3.12 data pipeline
  scrape_cead.py             → orchestrates CEAD fetch + all normalizer steps
  cead/normalizer.py         → compute_trend, compute_ranks, compute_level,
                               attach_featured (featured_rates)
  scripts/                   → fetch_ine_population.py, build_centroids.py,
                               verify_data_quality.py, audit_incidents.py
  snapshots/                 (symlinked from data/snapshots/)

data/
  cead/
    comunas/{CUT}.json       346 per-commune JSON files (schema below)
    regions/{id}.json        16 region files
    national.json
    map-payload.json         latest year compact map payload (~30 KB uncompressed)
    map-payload-{year}.json  per-year compact payloads (2005–2025)
    geo/
      communes.topo.json     85.6 KB gzip TopoJSON geometry
  ine/
    poblacion_comunal.json   INE 2024 populations by CUT
  snapshots/
    spd_homicide.json        SPD VHC victim-level rows (2018–2025, REFERENCE-ONLY)
    sii_exposure.json        SII empresas+trabajadores by CUT/year (REFERENCE-ONLY)
    fiscalia_secuestro.json  Fiscalía regional secuestro counts (REFERENCE-ONLY)

site/src/
  lib/data.ts                Build-time loaders (process.cwd() pattern, NOT import.meta.url)
  components/map/
    ChoroplethLayer.ts       L.geoJSON + L.canvas(); reads CommunaPayload[]
    MapIsland.tsx            client:only="react" island
  pages/
    commune/[slug].astro     346 EN commune pages
    es/comuna/[slug].astro   346 ES commune pages
    crime-ranking/           crime-type ranking pages
```

### Per-Commune JSON Schema (current — `data/cead/comunas/{CUT}.json`)

```jsonc
{
  "id": "13101",
  "name": "Santiago",
  "slug": "santiago",
  "region_id": "13",
  "population": 544388,
  "low_population": false,
  "national_rank": 11,       // ranked by latest-year total rate/100k
  "regional_rank": 2,
  "trend": "stable",
  "featured_rates": {
    "propiedad": { "2005": 6273.1, ... "2025": 2943.5 },
    "homicidios": { "2005": 2.66, ... "2025": 8.69 },  // CEAD grupo 101 rate/100k
    "homicidios_count": { "2005": 7, ... "2025": 48 }, // CEAD raw count
    "secuestros": {}
  },
  "series": [
    {
      "year": 2005, "rate_per_100k": 19481.9,
      "by_family": { "vida": 1442, "robos_violentos": 2118, "vif": 359,
                     "drogas": 76, "armas": 49, "propiedad": 6273, "incivilidades": 9163 },
      "partial": false
    },
    ...
  ]
}
```

### Map Payload Schema (current — compact for bundle budget)

```jsonc
// data/cead/map-payload.json  ~30 KB uncompressed
{
  "generated": "2026-06-16T13:56:05Z",
  "year": 2025,
  "comunas": [
    { "id": "13101", "rate": 5053, "level": 2, "by_family": [1337,76,1107,25,115,776,1617], "hr": 4 }
    // by_family = ARRAY indexed by CHIP_DEFS order: 0=vida,1=robos_violentos,2=vif,3=drogas,4=armas,5=propiedad,6=incivilidades
    // hr = homicide rate/100k (compact key; null when no data)
  ]
}
```

---

## (a) Composite Index: Pipeline Integration & Schema Migration

### Where the Index Is Computed

The composite index is computed by a **new dedicated script**
`pipeline/build_composite_index.py`, run as a separate GitHub Actions step after
`scrape_cead.py` exits 0. It reads the three snapshot files plus INE populations
and enriches the per-commune JSON files in-place, then emits the comparator table.

This isolation is deliberate: the risky index computation (new logic, new data
sources) must not gate the stable CEAD scraper. If the index step fails, CEAD data
still refreshes and deploys.

**Outputs of `build_composite_index.py`:**

1. Updates `data/cead/comunas/{CUT}.json` — adds `composite_index`, `spd_homicide_rate`, `sii_exposure_index`
2. Writes `data/cead/comparator_table.json` — all-communes index summary for comparator island
3. (Does NOT write map-payloads — see Step 3 below)

### The 7 Metrics

Based on STATE.md Wave-0 inputs and PROJECT.md Phase 18 description:

| # | Key | Source | Unit | Notes |
|---|-----|---------|------|-------|
| M1 | `cead_total_rate` | CEAD tipoVal=1,2 (casos policiales) | rate/100k residents | Existing `series[].rate_per_100k`; INE pop denominator |
| M2 | `cead_vida_rate` | CEAD familia "vida" (grupos 100–199) | rate/100k | From `series[].by_family.vida` |
| M3 | `cead_robos_rate` | CEAD familia "robos_violentos" | rate/100k | From `series[].by_family.robos_violentos` |
| M4 | `cead_propiedad_rate` | CEAD familia "propiedad" | rate/100k | From `series[].by_family.propiedad` |
| M5 | `spd_homicide_rate` | SPD VHC xlsx (victim rows) | rate/100k residents | SPD truth — replaces CEAD grupo 101 for the composite only (see switch note) |
| M6 | `sii_exposure_index` | SII empresas+trabajadores per CUT / INE pop | activity index | Exposure proxy; adjusts for daytime-population concentration in business-district communes |
| M7 | `cead_vif_rate` | CEAD familia "vif" | rate/100k | Domestic violence as standalone dimension |

**SPD homicide switch (M5 vs existing `featured_rates.homicidios`):**

The existing `featured_rates.homicidios` = CEAD grupo 101, tipoVal=1,2 (denuncias +
detenciones). The detenciones component double-counts per-offence. SPD VHC counts
victim-level rows — one row per victim, cleaner truth. M5 uses SPD for the index.

`featured_rates.homicidios` is NOT overwritten. It stays for backwards compatibility
with the existing choropleth "homicide" filter and commune pages. The SPD rate is
stored separately as `spd_homicide_rate` and the methodology page must document the
difference.

SPD data spans 2018–2025 only; M5 is null/absent for 2005–2017. The composite index
is only emitted for years where >= 4 of 7 metrics are available. The `available_metrics`
count in each year's index entry lets the UI flag partial scores.

### Exposure Denominator Join (SII by CUT)

`data/snapshots/sii_exposure.json` stores records as `{ cut, name, year, empresas, trabajadores }`.
The CUT strings match the commune JSON `id` field directly (no padding transform needed —
both use raw CEAD CUT format confirmed from the snapshot file).

~15 communes may be absent from SII (genuinely low economic activity). Assign
`sii_exposure_index: null` for those; exclude M6 from their composite score and
decrement `available_metrics` accordingly.

~31 communes have zero SPD VHC rows (genuinely zero homicides 2018–2025, per the
snapshot caveat). These are not missing — assign `spd_homicide_rate: 0.0` for those
years; they are valid data points.

### Schema Migration: `featured_rates` → 7-metric (Additive, Non-Breaking)

Existing fields remain intact. New fields added alongside.

**New per-commune JSON fields:**

```jsonc
{
  // --- EXISTING (unchanged) ---
  "featured_rates": {
    "propiedad": { "2005": 6273.1, ... },
    "homicidios": { "2005": 2.66, ... },    // CEAD grupo 101 rate — PRESERVED
    "homicidios_count": { "2005": 7, ... }, // CEAD count — PRESERVED
    "secuestros": {}
  },

  // --- NEW in v2.0 ---
  "spd_homicide_rate": { "2018": 3.68, "2019": 4.6, ..., "2025": 8.81 },
  "sii_exposure_index": { "2005": 0.42, ..., "2024": 0.51 },
  "composite_index": {
    "2022": { "score": 62.4, "rank": 18, "level": 4, "available_metrics": 7 },
    "2023": { "score": 58.1, "rank": 22, "level": 3, "available_metrics": 7 },
    "2024": { "score": 55.7, "rank": 25, "level": 3, "available_metrics": 7 }
  }
}
```

`composite_index` covers only years where data is available (expected: 2018–2024
at minimum; 2025 if SPD VHC 2025 is considered reliable — the snapshot caveat flags
it as "partial and unconsolidated", so cap at 2024 for scored years).

**New TypeScript additions in `site/src/lib/data.ts`:**

```typescript
interface CompositeIndexEntry {
  score: number;
  rank: number;
  level: 1 | 2 | 3 | 4 | 5;
  available_metrics: number;
}

// Added to CommuneData interface:
spd_homicide_rate?: Record<string, number>;
sii_exposure_index?: Record<string, number | null>;
composite_index?: Record<string, CompositeIndexEntry>;
```

---

## (b) Comparator Island: Data Requirements & Page-Count Budget

### All-Communes Index Table (`data/cead/comparator_table.json`)

The comparator island needs a client-loadable all-communes summary for
autocomplete/search. This is a new file written by `build_composite_index.py`.

```jsonc
// data/cead/comparator_table.json  — all 346 communes, compact
{
  "generated": "2026-06-19T...",
  "latest_year": 2024,
  "communes": [
    {
      "cut": "13101",
      "name": "Santiago",
      "slug": "santiago",
      "region_id": "13",
      "population": 544388,
      "low_population": false,
      "national_rank": 11,
      "composite_score": 55.7,
      "composite_rank": 25,
      "composite_level": 3,
      "total_rate": 4952,
      "by_family": [1337, 76, 1107, 25, 115, 776, 1617],
      "spd_homicide_rate": 5.69,
      "trend": "stable"
    },
    ...
  ]
}
```

Estimated size: 346 communes × ~250 bytes = **~86 KB raw / ~28 KB gzip**. Loaded
only on pages with the comparator island (map page + comparator landing pages), not
injected into every commune/region page.

For sparkline data (multi-year series), the island fetches `data/cead/comunas/{CUT}.json`
on demand when a commune is selected. This keeps the initial comparator_table.json
compact and avoids bundling 346 full commune histories.

### Cloudflare File-Count Budget

| Source | Count |
|--------|-------|
| Current pages (v1.3) | ~792 |
| New: comparator landing pages (EN + ES) | 2 |
| New: A-vs-B programmatic pages (see below) | ~7,000 |
| New: JSON data files (comparator_table.json + updated map-payloads) | ~5 |
| **Projected total** | **~7,800** |
| **Free-tier limit** | **20,000** |
| **Remaining headroom** | **~12,200** |

### A-vs-B Programmatic Pages: Bounding the Combinatorial Explosion

**The risk:** C(346, 2) = 59,685 unique commune pairs × 2 locales = **119,370 pages** —
6× over the 20K limit.

**Recommended bound (Approach A — priority-pair subset):**

Generate A-vs-B pages only for pairs where at least one commune falls into a
priority tier:

- **Tier 1** (10 editorial-priority communes from PROJECT.md): Santiago, Providencia,
  Las Condes, Ñuñoa, Valparaíso, Viña del Mar, Concepción, La Serena, Antofagasta, Temuco
- **Tier 2** (non-low-population communes, national_rank ≤ 50)

Pair budget calculation:
- Tier 1 × all non-low-population communes: 10 × ~280 = 2,800 pairs (with dedup ≈ 2,800)
- Tier 2 × Tier 2 (excluding T1×T1 already counted): ~50 × 49 / 2 = 1,225 pairs
- Union with dedup ≈ **~3,400 unique pairs** × 2 locales = **~6,800 A-vs-B pages**

Total projected: 792 + 6,800 + 10 overhead = **~7,600 pages** — well under 20K.

**SEED-001 hybrid rollout compliance:** Communes not in any pair are still
accessible via the interactive comparator island. No 404 for non-rollout communes.
Only the programmatic A-vs-B pages are bounded; the island handles the rest.

**Page generation pattern** (follows `commune/[slug].astro`):

```
site/src/pages/compare/[pair].astro        EN: /compare/santiago-vs-providencia/
site/src/pages/es/comparar/[par].astro     ES: /es/comparar/santiago-vs-providencia/
```

`getStaticPaths()` reads `comparator_table.json` at build time, generates the
approved pair list. Each page pre-renders both communes' data statically (SEO
content is server-side; the comparator island is layered on top for interactivity).

**Thin-content guard (critical):** Each A-vs-B page must render differentiated prose
via `buildComparisonProse(communeA, communeB)` in `proseEngine.ts` — real rate
deltas, composite score comparison, trend narrative. Pages that are structurally
identical except for commune names will be deindexed. The prose engine must produce
non-identical output for each pair.

---

## (c) Data-Flow Changes to `build_map_payload` and Choropleth

### Extracting `build_map_payload` from `scrape_cead.py`

Currently the map-payload generation is embedded inside `scrape_cead.py`. It must
be extracted to `pipeline/build_map_payload.py` so it can run **after** the
composite index step enriches the commune files.

**New pipeline step order in GitHub Actions:**

```yaml
# .github/workflows/scrape-cead.yml
steps:
  - run: python pipeline/scrape_cead.py         # writes base communas/*.json
  - run: python pipeline/build_composite_index.py  # enriches communas + writes comparator_table.json
  - run: python pipeline/build_map_payload.py   # reads enriched communas + writes map-payload*.json
  - run: git add data/ && git diff --staged --quiet || git commit -m "data: refresh"
```

### Map Payload: Adding `ci` Field

Each commune entry in `map-payload*.json` gains a compact `ci` field:

```jsonc
// map-payload entry — v2.0
{ "id": "13101", "rate": 5053, "level": 2, "by_family": [1337,76,1107,25,115,776,1617], "hr": 4, "ci": 3 }
// ci = composite_index[year].level (1-5 integer); omitted/null for years without composite data
```

For year payloads where composite data is unavailable (2005–2017), `ci` is omitted.
The choropleth handles this gracefully: if `ci` is null/absent for all communes in
a given year-payload, the composite filter chip is disabled for that year.

Payload size impact: +1 key per commune entry ≈ +346 × 7 bytes ≈ **+2.4 KB per
year-payload file**. Negligible.

### ChoroplethLayer.ts Changes

```typescript
// Updated CommunaPayload (ChoroplethLayer.ts)
export interface CommunaPayload {
  id: string;
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
  hr: number | null;
  homicide_count: number | null;
  ci: number | null;  // NEW: composite index level (1-5) or null
}

// New export:
export function buildStyleMapFromCompositeIndex(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  // Same pattern as buildStyleMapFromHomicide
  // Reads c.ci; falls back to c.level when ci is null
  ...
}
```

New "Composite Index" chip in `FiltersRow.tsx`. Recommend placing it as a
separate "View" selector (distinct from the 7 crime-family chips) to avoid
semantic confusion between "filter by crime family" and "view composite score".

---

## Recommended Build Order

The hard dependency: **composite index must be computed before comparator data exists
and before map payloads can embed the `ci` field.**

```
Phase 18 — Composite Crime Index  [BLOCKS Phase 21]
  18.a  pipeline/build_composite_index.py
        - Reads: data/cead/comunas/*.json + data/snapshots/spd_homicide.json
                 + data/snapshots/sii_exposure.json + data/ine/poblacion_comunal.json
        - Writes: data/cead/comunas/*.json (enriched), data/cead/comparator_table.json
  18.b  Extract pipeline/build_map_payload.py (from scrape_cead.py)
        - Reads: data/cead/comunas/*.json (enriched)
        - Writes: data/cead/map-payload*.json (adds ci field)
  18.c  CommunaPayload + ChoroplethLayer: add ci, buildStyleMapFromCompositeIndex
  18.d  MapIsland: composite filter chip, ResultPanel composite score display
  18.e  Commune pages: show composite_index score + spd_homicide_rate alongside CEAD homicidios
  18.f  GitHub Actions workflow: insert build_composite_index step between scraper and build_map_payload
  18.g  Methodology page: document composite formula, SPD switch, SII caveat

Phase 21 — Commune Comparator + A-vs-B SEO  [requires Phase 18 complete]
  21.a  Verify comparator_table.json schema (written by Phase 18)
  21.b  ComparatorIsland.tsx: loads comparator_table.json; lazy-fetches communas/{CUT}.json for sparklines
  21.c  /compare/ and /es/comparar/ landing pages (Astro shell + island)
  21.d  A-vs-B programmatic pages: getStaticPaths reads comparator_table.json,
        generates priority-pair set (~3,400 pairs × 2 locales = ~6,800 pages),
        proseEngine.buildComparisonProse() generates differentiated content
  21.e  Internal links: commune pages → comparator pre-filled; ranking pages → "Compare" CTA

Phase 22 — Go-Live Ops  [parallel with 21; no code dependency]
  22.a  CF_DEPLOY_HOOK_URL secret → manual CF deploy (human step)
  22.b  Live news run + 50-incident commune audit
  22.c  GSC submission + hreflang validation
  22.d  Flip ADSENSE_ENABLED + Consent Mode
```

---

## Component Boundaries: New vs Modified

| File/Dir | Status | What Changes |
|----------|--------|--------------|
| `pipeline/build_composite_index.py` | **NEW** | Computes 7-metric composite; joins SPD/SII/CEAD; enriches communas; writes comparator_table.json |
| `pipeline/build_map_payload.py` | **NEW (extracted)** | Same logic as current embedded step in scrape_cead.py + adds `ci` field |
| `pipeline/scrape_cead.py` | **MODIFIED** | Remove embedded build_map_payload call; document that enrichment runs separately |
| `data/cead/comunas/{CUT}.json` | **MODIFIED** | Adds `composite_index`, `spd_homicide_rate`, `sii_exposure_index` (non-breaking; existing fields unchanged) |
| `data/cead/map-payload*.json` | **MODIFIED** | Each commune entry gains `ci` field (omitted for pre-2018 years) |
| `data/cead/comparator_table.json` | **NEW** | All-communes compact summary; ~86 KB raw / ~28 KB gzip |
| `site/src/lib/data.ts` | **MODIFIED** | Add `CompositeIndexEntry`, 3 new optional fields to `CommuneData`, `loadComparatorTable()` loader |
| `site/src/components/map/ChoroplethLayer.ts` | **MODIFIED** | Add `ci` to `CommunaPayload`; add `buildStyleMapFromCompositeIndex()` |
| `site/src/components/map/FiltersRow.tsx` | **MODIFIED** | Add composite index view selector |
| `site/src/components/map/ResultPanel.tsx` | **MODIFIED** | Show composite score + rank |
| `site/src/components/ComparatorIsland.tsx` | **NEW** | React island for comparator (client:load on comparator pages) |
| `site/src/pages/compare/[pair].astro` | **NEW** | EN A-vs-B programmatic pages (~3,400) |
| `site/src/pages/es/comparar/[par].astro` | **NEW** | ES A-vs-B programmatic pages (~3,400) |
| `site/src/pages/compare/index.astro` | **NEW** | EN comparator landing |
| `site/src/pages/es/comparar/index.astro` | **NEW** | ES comparator landing |
| `site/src/lib/proseEngine.ts` | **MODIFIED** | Add `buildComparisonProse(communeA, communeB)` |
| `.github/workflows/scrape-cead.yml` | **MODIFIED** | Insert `build_composite_index.py` step + `build_map_payload.py` step after scraper |

---

## Known Integration Risks

### Risk 1: SPD year coverage gap
SPD VHC covers only 2018–2025; 2025 is flagged as "partial and unconsolidated" in
the snapshot caveat. Score 2018–2024 only for safe index years. The choropleth
composite chip must disable itself for year-payloads with no `ci` data (2005–2017)
and show a UI caveat tooltip explaining why the composite view is unavailable for
older years.

### Risk 2: SII commune absence / HQ artifact
~15 communes may be absent from SII data. The composite score for those communes
uses 6 of 7 metrics and sets `available_metrics: 6`. The HQ-domicile artifact
(multi-site firms attribute all workers to headquarters) concentrates exposure in
Las Condes, Providencia, Santiago centro — these communes will appear lower-risk
after exposure adjustment, which may surprise users. The methodology page must
document this clearly.

### Risk 3: CEAD homicidios vs SPD discrepancy
`featured_rates.homicidios` (CEAD tipoVal=1,2) and `spd_homicide_rate` (SPD VHC
victims) will differ — sometimes substantially. Both figures now appear in the
commune page. The methodology page must explain why two homicide figures exist and
which is used in the composite (SPD).

### Risk 4: A-vs-B thin content
~6,800 A-vs-B pages with identical template structure but only commune names
changed will be deindexed by Google. The prose engine must generate substantively
different text per pair (computed rate deltas, trend narrative, composite rank
comparison). A CI step should sample-check prose uniqueness before deploy.

### Risk 5: Build time with ~6,800 new pages
Astro's static generation of ~6,800 new pages adds ~3–5 minutes to the build.
Must stay under the 20-minute Cloudflare build timeout. Mitigation: measure build
time after Phase 18 (no new pages) before committing to the A-vs-B page count in
Phase 21; reduce pair count if build time approaches 15 minutes.

### Risk 6: OneDrive desync during multi-step pipeline
The existing known pitfall: `dist/` artifacts desync between separate processes
when the repo lives inside OneDrive. The multi-step pipeline (`scrape_cead` →
`build_composite_index` → `build_map_payload`) must be chained in a single command
in local dev, same as the existing `cd site && npm run build && npm run validate`
pattern. In GitHub Actions this is not an issue (Linux runner, no OneDrive sync).

---

## Sources

- `data/cead/comunas/13101.json` — confirmed `featured_rates` schema and `series` structure
- `data/cead/map-payload.json` — confirmed compact payload schema (`rate`, `level`, `by_family[7]`, `hr`)
- `data/cead/geo/communes.topo.json` — 353,696 bytes raw confirmed (`wc -c`)
- `data/snapshots/spd_homicide.json` — confirmed SPD record schema (`cut`, `name`, `year`, `homicides`) + caveat on 2025 partial data
- `data/snapshots/sii_exposure.json` — confirmed SII record schema (`cut`, `name`, `year`, `empresas`, `trabajadores`) + HQ-domicile caveat
- `pipeline/cead/normalizer.py` — confirmed `attach_featured`, `compute_level`, CHIP_DEFS ordering (0=vida..6=incivilidades)
- `pipeline/scrape_cead.py` — confirmed `region_id_from_cut` and overall pipeline structure
- `site/src/lib/data.ts` — confirmed `CommuneData` interface and `process.cwd()` loader pattern
- `site/src/components/map/ChoroplethLayer.ts` — confirmed `CommunaPayload`, `buildStyleMapFrom*` pattern
- `.planning/STATE.md` — Phase 17 Wave-0 decisions; CHIP_DEFS order; by_family record-vs-array distinction
- `.planning/PROJECT.md` — Phase 18 scope, SEED-001 hybrid rollout constraints, priority editorial communes
- `.planning/seeds/SEED-001-v12-discovery-seo.md` — hybrid rollout rule (never 404 to non-rollout communes)
- CLAUDE.md — Cloudflare Pages 20,000-file free-tier limit confirmed
