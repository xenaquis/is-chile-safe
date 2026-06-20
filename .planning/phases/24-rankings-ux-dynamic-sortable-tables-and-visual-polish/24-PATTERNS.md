# Phase 24: Rankings UX — Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 3 (2 primary targets + 1 support file)
**Analogs found:** 3 / 3

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/src/pages/safest-cities-in-chile.astro` | page (editorial) | request-response + CRUD | `site/src/pages/crime-ranking/[crime].astro` | exact — same role, same table + enhancer wiring task |
| `site/src/pages/es/comunas-mas-seguras-chile.astro` | page (editorial, ES) | request-response + CRUD | `site/src/pages/es/ranking-delito/[crime].astro` | exact — ES mirror, identical structural gap |
| `site/src/config/i18n.ts` | config / string registry | transform | `site/src/config/i18n.ts` (self — verify existing keys) | self-reference — verify only, no new keys needed |

**Out-of-scope surfaces (already wired — do NOT modify):**
- `site/src/pages/index.astro` / `site/src/pages/es/index.astro` — wired via `CommuneRankingTable`
- `site/src/pages/crime-ranking/[crime].astro` / `site/src/pages/es/ranking-delito/[crime].astro` — already have `data-ranking-table` + `RankingTableEnhancer`
- `site/src/pages/communes/index.astro` — A-Z directory, no rate column, no wiring needed

---

## Pattern Assignments

### `site/src/pages/safest-cities-in-chile.astro` (page, request-response + CRUD)

**Analog:** `site/src/pages/crime-ranking/[crime].astro`

**Current state of target file:** Raw `<table class="ranking-table">` at lines 117–145. No `data-ranking-table`, no `data-rates` on rows, no `RankingTableEnhancer` import or render. The frontmatter `communeRates` map (lines 31–44) does NOT collect `ratesByYear` — this is the primary data gap.

---

#### Step 1 — Enrich frontmatter data map with `ratesByYear`

**Analog source:** `site/src/pages/crime-ranking/[crime].astro` lines 101–124

Current frontmatter builds `communeRates` at lines 31–44 of the target without `ratesByYear`. Extend each entry to include a `ratesByYear` built from `data.series`:

```typescript
// ANALOG PATTERN — crime-ranking/[crime].astro lines 101–115
// Build ratesByYear: complete years only (D-3)
const ratesByYear: Record<number, number> = {};
commune.series.filter((s) => !s.partial).forEach((s) => {
  ratesByYear[s.year] = s.rate_per_100k;   // ← use rate_per_100k for total rate (not by_family)
});
```

Applied to the target's existing map at lines 31–44 of `safest-cities-in-chile.astro`:

```typescript
// MODIFIED communeRates map — add ratesByYear per row
const communeRates = eligibleMeta.map((meta) => {
  const data = loadCommune(meta.cut);
  const rate = latestCompleteYearRate(data);
  // Build ratesByYear from complete series entries
  const ratesByYear: Record<number, number> = {};
  data.series.filter((s: any) => !s.partial).forEach((s: any) => {
    ratesByYear[s.year] = s.rate_per_100k;
  });
  return {
    cut: meta.cut,
    name: meta.name,
    slug: meta.slug,
    regionName: data.regionName,
    rate,
    nationalRank: data.national_rank,
    trend: data.trend,
    year: data.latestCompleteYear,
    ratesByYear,                             // ← new field
  };
});
```

---

#### Step 2 — Add import for `RankingTableEnhancer`

**Analog source:** `site/src/components/CommuneRankingTable.astro` line 15 / `site/src/pages/crime-ranking/[crime].astro` (imports block)

```typescript
// Add to existing import block in safest-cities-in-chile.astro
import RankingTableEnhancer from '../components/RankingTableEnhancer.astro';
```

---

#### Step 3 — Wire `data-ranking-table` and `data-default-sort-dir` on the `<table>` element

**Analog source:** `site/src/pages/crime-ranking/[crime].astro` line 255

Current target (line 117):
```html
<table class="ranking-table">
```

Required replacement:
```html
<table
  class="ranking-table"
  data-ranking-table
  data-rate-col="3"
  data-name-col="1"
  data-rate-format="round"
  data-locale="en"
  data-default-sort-dir="asc"
>
```

Column mapping for this page (5 columns: `#` / Commune / Region / Rate / National Rank):
- col 0 = `#` (rank number)
- col 1 = Commune name  ← `data-name-col="1"`
- col 2 = Region
- col 3 = Rate per 100k  ← `data-rate-col="3"`
- col 4 = National Rank

`data-default-sort-dir="asc"` overrides the global "desc" default — editorial intent is lowest-first.

---

#### Step 4 — Add `data-rates` per `<tr>` in `<tbody>`

**Analog source:** `site/src/pages/crime-ranking/[crime].astro` line 267 / `site/src/components/CommuneRankingTable.astro` line 60

Current target rows (lines 132–143):
```astro
{topCommunes.map((c, i) => (
  <tr>
    <td>{i + 1}</td>
    ...
  </tr>
))}
```

Required replacement:
```astro
{topCommunes.map((c, i) => (
  <tr data-rates={JSON.stringify(c.ratesByYear)}>
    <td>{i + 1}</td>
    ...
  </tr>
))}
```

Note: these communes are all non-low-population (filtered at line 26 of the target), so `data-low-pop` is not needed. No `low-pop` class required.

---

#### Step 5 — Update `<caption>` text to include sort hint

**Contract source:** UI-SPEC Copywriting Contract

```html
<caption>
  Communes with lowest reported crime incidence per 100,000 inhabitants —
  CEAD data for {dataYear}. Excludes communes with population below 10,000.
  Click column headers to sort.
</caption>
```

---

#### Step 6 — Mount `RankingTableEnhancer` after the table

**Analog source:** `site/src/pages/crime-ranking/[crime].astro` line 290 / `site/src/components/CommuneRankingTable.astro` line 85

Place immediately after the closing `</div>` of `.ranking-table-wrapper` (currently line 145):

```astro
<RankingTableEnhancer locale="en" />
```

---

#### Step 7 — New `data-default-sort-dir` attribute support in `RankingTableEnhancer`

**Analog source:** `site/src/components/RankingTableEnhancer.astro` lines 74–78 (table config read block) and line 106 (initial `sortDir` declaration)

The enhancer currently sets `sortDir = 'desc'` as a hardcoded default (line 106). Add one read of the new attribute after the existing config block:

```typescript
// After existing config reads (around line 78):
const defaultSortDir = (table.dataset.defaultSortDir === 'asc') ? 'asc' : 'desc';

// Replace line 106:
// let sortDir: 'asc' | 'desc' = 'desc';
// With:
let sortDir: 'asc' | 'desc' = defaultSortDir;
```

This is the ONLY change to `RankingTableEnhancer.astro`.

---

### `site/src/pages/es/comunas-mas-seguras-chile.astro` (page, request-response + CRUD, ES)

**Analog:** `site/src/pages/es/ranking-delito/[crime].astro`

This page is the structural mirror of `safest-cities-in-chile.astro` with ES strings and `/es/` URL prefixes. Apply the identical 7-step pattern above with these locale differences:

| Item | EN value | ES value |
|------|----------|----------|
| `data-locale` on `<table>` | `"en"` | `"es"` |
| `RankingTableEnhancer` prop | `locale="en"` | `locale="es"` |
| `<caption>` sort hint | "Click column headers to sort." | "Haga clic en los encabezados de columna para ordenar." |
| Commune link prefix | `/commune/${c.slug}/` | `/es/comuna/${c.slug}/` (already correct in existing file) |
| `toLocaleString` in `<td>` | `'en-US'` | `'es-CL'` (already correct) |

Import path differs (file is one level deeper):
```typescript
import RankingTableEnhancer from '../../components/RankingTableEnhancer.astro';
```

The `ratesByYear` construction is identical — `data.series.filter(!s.partial).forEach(s => ratesByYear[s.year] = s.rate_per_100k)`.

---

### `site/src/config/i18n.ts` (config, string registry)

**Role:** Verify existing strings — no new keys required.

**Verification result from codebase scan:**

All strings consumed by `RankingTableEnhancer` already exist in both `EN_STRINGS` and `ES_STRINGS`:

| Key | EN value (line ~291–295) | ES value (line ~462–466) | Status |
|-----|--------------------------|--------------------------|--------|
| `sort_label` | `'Sort by {column}'` | `'Ordenar por {column}'` | EXISTS |
| `sort_ascending` | `'ascending'` | `'ascendente'` | EXISTS |
| `sort_descending` | `'descending'` | `'descendente'` | EXISTS |
| `year_select_label` | `'Year'` | `'Año'` | EXISTS |
| `year_select_aria` | `'Select data year'` | `'Seleccionar año de datos'` | EXISTS |

**Action required:** None. All keys are present. No edit to `i18n.ts` needed.

---

## Shared Patterns

### data-attribute wiring API (applies to both target pages)

**Source:** `site/src/components/RankingTableEnhancer.astro` lines 12–21 (docblock) + `site/src/pages/crime-ranking/[crime].astro` line 255

Complete attribute set for a 5-column table with the safest-cities column layout:

```html
<table
  class="ranking-table"
  data-ranking-table
  data-rate-col="3"
  data-name-col="1"
  data-rate-format="round"
  data-locale="en"
  data-default-sort-dir="asc"
>
```

Guard behavior (already in enhancer, line 86–87): if no `<tr>` has `data-rates`, the enhancer silently exits — no JS error.

---

### `data-rates` row pattern (applies to both target pages)

**Source:** `site/src/components/CommuneRankingTable.astro` line 60

```astro
<tr data-rates={JSON.stringify(row.ratesByYear)}>
```

`ratesByYear` must be `Record<number, number>` where keys are complete years (non-partial) and values are `rate_per_100k` floats. Build from `data.series.filter(s => !s.partial)`.

---

### `RankingTableEnhancer` mount placement (applies to both target pages)

**Source:** `site/src/pages/crime-ranking/[crime].astro` line 290

```astro
</div>  {/* closes .ranking-table-wrapper */}
<RankingTableEnhancer locale="en" />
```

Mount AFTER the wrapper `</div>`, not inside it. One enhancer per page is sufficient — it queries `document.querySelectorAll('table[data-ranking-table]')` and wires all matching tables.

---

### Mobile overflow pattern (already present in target pages)

**Source:** `site/src/pages/safest-cities-in-chile.astro` lines 263–269 (existing `<style>`)

Both target pages already have:
```css
.ranking-table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;  /* add this if missing */
  ...
}
```

Verify `-webkit-overflow-scrolling: touch` is present. The `CommuneRankingTable` analog has it (line 91); the current target pages only have `overflow-x: auto`. Add the webkit property to match the analog.

---

## No Analog Found

None — all files have close analogs.

---

## Data Flow Note

`loadCommune(cut)` returns the full commune JSON object with a `series` array. Each entry has `{ year, partial, rate_per_100k, by_family }`. The `ratesByYear` map for these pages uses `rate_per_100k` (total crime rate), not `by_family[familyKey]` (crime-family-specific rate used in `crime-ranking/[crime].astro`). This is the critical distinction: safest-cities pages rank by total incidence, not by crime family.

---

## Metadata

**Analog search scope:** `site/src/pages/`, `site/src/components/`, `site/src/config/`
**Files scanned:** 8 (RankingTableEnhancer, CommuneRankingTable, crime-ranking/[crime], es/ranking-delito/[crime], region/[slug], es/region/[slug], safest-cities-in-chile, es/comunas-mas-seguras-chile)
**Pattern extraction date:** 2026-06-19
