# Phase 8: Bug Fixes & Data Correctness — Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 7 (files to modify this phase)
**Analogs found:** 7 / 7

---

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `site/src/pages/region/[slug].astro` | page/template | CRUD (build-time data) | `site/src/pages/crime/[family].astro` | exact — same ranking-table pattern |
| `site/src/pages/es/region/[slug].astro` | page/template | CRUD (build-time data) | `site/src/pages/region/[slug].astro` | exact — ES mirror |
| `site/src/pages/crime/[family].astro` | page/template | CRUD (build-time data) | `site/src/pages/region/[slug].astro` | exact — same ranking-table pattern |
| `site/src/pages/es/delito/[family].astro` | page/template | CRUD (build-time data) | `site/src/pages/crime/[family].astro` | exact — ES mirror |
| `site/src/pages/es/delitos-por-comuna.astro` | editorial page | static | `site/src/pages/es/region/[slug].astro` | partial — same ES locale context |
| `site/src/components/map/ResultPanel.tsx` | React component | request-response (fetch) | self — fix is 3 inline string literals | self-contained |
| `site/src/components/AdSlot.astro` | component | static | self — remove `.ad-placeholder` border styles | self-contained |
| `site/src/components/PageHeader.astro` | component | static | self — add hamburger pattern | self-contained |

---

## Pattern Assignments

### F-005 — Rollout Gating in Region & Crime Ranking Tables

**Decision:** D-01/D-02 — gate displayed rows to `loadRolloutCuts()` CUT set; non-rollout rows removed entirely; rank denominators (`#N of 346`, `#N of 16`) unchanged.

---

#### `site/src/pages/region/[slug].astro` + `site/src/pages/es/region/[slug].astro`

**The ranking data source** (lines 73–87 in EN, lines 66–80 in ES — identical structure):

```astro
// Load commune data for ranking table (rate + trend + national_rank + low_population)
const rankingRows = regionCommunes.map((c) => {
  const data = loadCommune(c.cut);
  const rate = latestCompleteYearRate(data);
  return {
    name: c.name,
    slug: c.slug,
    rate,
    national_rank: data.national_rank,
    trend: data.trend,
    low_population: c.low_population,
  };
});

// Sort by rate descending (low-pop communes at bottom within their rate order)
rankingRows.sort((a, b) => b.rate - a.rate);
```

**Where to insert the gate** — add `loadRolloutCuts` import and a `Set` filter immediately after the sort, before passing `rankingRows` to `<CommuneRankingTable>`:

```astro
// Import addition (lines 14–27 in EN — add loadRolloutCuts to the existing import):
import {
  loadRegion,
  loadIndex,
  loadCommune,
  loadNationalAverage,
  loadNational,
  latestCompleteYearRate,
  loadRolloutCuts,          // ADD THIS
} from '../../lib/data.ts';

// After rankingRows.sort(...) — insert gate:
const rolloutCuts = new Set(loadRolloutCuts());
const displayedRows = rankingRows.filter((row) => {
  // find the CUT for this row via regionCommunes index
  const meta = regionCommunes.find((c) => c.slug === row.slug);
  return meta ? rolloutCuts.has(meta.cut) : false;
});
const hiddenCount = rankingRows.length - displayedRows.length;
```

**The table render** (lines 200–205 in EN region template):

```astro
<!-- 5. CommuneRankingTable -->
<section class="ranking-section" aria-label="Commune ranking">
  <h2 class="section-heading">
    Communes in {region.name} — by reported incidence rate ({latestCompleteYear})
  </h2>
  <CommuneRankingTable rows={rankingRows} locale="en" />
</section>
```

Change `rows={rankingRows}` to `rows={displayedRows}` and add the minimal "showing N" affordance (D-03) after the table:

```astro
<CommuneRankingTable rows={displayedRows} locale="en" />
{hiddenCount > 0 && (
  <p class="rollout-note">
    Showing {displayedRows.length} of {rankingRows.length} communes — more coming soon.
  </p>
)}
```

**Rank denominator is NOT gated** — `national_rank` in the row data (`#N of 346`) comes from `data.national_rank` (pre-computed in CEAD JSON) and `TOTAL_COMMUNES = 346` is never modified. The `rankingRows.length` used in the affordance counts all communes in the region, not the 346 total.

**ES mirror** (`site/src/pages/es/region/[slug].astro`) — identical pattern; locale strings differ. The `CommuneRankingTable` component already handles locale via `locale="es"` prop. The affordance text in ES: `Mostrando {displayedRows.length} de {rankingRows.length} comunas — más próximamente.`

---

#### `site/src/pages/crime/[family].astro` + `site/src/pages/es/delito/[family].astro`

**The ranking data build** (lines 82–109 in EN crime template):

```astro
const allRows: RankRow[] = [];
let latestYear = new Date().getFullYear() - 1;
for (const meta of index) {
  const commune = loadCommune(meta.cut);
  if (!meta.low_population) {
    latestYear = Math.max(latestYear, commune.latestCompleteYear);
  }
  const entry = commune.series.find(
    (s) => s.year === commune.latestCompleteYear && !s.partial
  );
  const rate = entry?.by_family?.[familyKey] ?? 0;
  allRows.push({ name: meta.name, slug: meta.slug, regionName: commune.regionName,
    regionFileIdStr: regionFileId(meta.region_id), rate, trend: commune.trend,
    low_population: meta.low_population });
}

// Sort descending; low-pop at bottom
const eligibleRows = allRows.filter((r) => !r.low_population).sort((a, b) => b.rate - a.rate);
const lowPopRows   = allRows.filter((r) => r.low_population).sort((a, b) => b.rate - a.rate);
const rankingRows  = [...eligibleRows, ...lowPopRows];
```

**Where to insert the gate** — add `loadRolloutCuts` to imports, then filter `rankingRows` after it is assembled:

```astro
// Import addition — add loadRolloutCuts to existing import from '../../lib/data.ts'
import { loadIndex, loadCommune, loadCatalog, regionFileId, loadRolloutCuts } from '../../lib/data.ts';

// After rankingRows is assembled (after line 109):
const rolloutCuts   = new Set(loadRolloutCuts());
const displayedRows = rankingRows.filter((row) => {
  const meta = index.find((c) => c.slug === row.slug);
  return meta ? rolloutCuts.has(meta.cut) : false;
});
const hiddenCount = rankingRows.length - displayedRows.length;
```

**The inline ranking table** (lines 209–246 in EN crime template) — the `<tbody>` maps `rankingRows`:

```astro
<tbody>
  {rankingRows.map((row, i) => (
    <tr class={row.low_population ? 'low-pop' : ''}>
      <td class="col-num col-rank">
        {row.low_population ? '—' : `#${i + 1}`}
      </td>
      <td>
        <a href={`/commune/${row.slug}/`} class="commune-link">
          {row.name}
        </a>
        ...
      </td>
      ...
    </tr>
  ))}
</tbody>
```

Change `rankingRows.map(...)` to `displayedRows.map(...)` and add the affordance below the table (same pattern as region pages). The rank column `#${i + 1}` is the *displayed* row position within the gated list — this is expected; the *national rank* (`#N of 346`) appears in `ResultPanel` and commune pages only, not in this table.

**Note on index lookup** — the crime template already has `index` in scope (`const index = loadIndex()` line 69). The gate filter uses `index.find((c) => c.slug === row.slug)` to retrieve the CUT from the slug. This is safe because slugs are unique in `index.json`.

---

### F-001 — ES H1 "Commune" → "Comuna" (`site/src/pages/es/delitos-por-comuna.astro`)

**The bug** (line 69):

```astro
<h1>Delitos en Chile por Commune: una perspectiva basada en datos</h1>
```

**The fix** — change the single word "Commune" to "Comuna":

```astro
<h1>Delitos en Chile por Comuna: una perspectiva basada en datos</h1>
```

**Also fix body text occurrences** — the same file uses "commune" (lowercase EN) inline in body copy at lines 41, 89, 170, 173 (FAQ answer text). These are not H1 SEO headings but should also be corrected to "comuna" for consistency. Scan with grep: `grep -n "commune" site/src/pages/es/delitos-por-comuna.astro`.

**i18n pattern for reference** — the `CommuneRankingTable` component (lines 32–33) shows the locale-keyed pattern for "Commune"/"Comuna":

```ts
// site/src/components/CommuneRankingTable.astro lines 32-33
const communeColLabel = locale === 'en' ? 'Commune' : 'Comuna';
```

This page does not use that helper (it is a static editorial page, not a template). The fix is a direct string replacement in the `.astro` source. No i18n dict entry needed — the `ES_STRINGS` / `EN_STRINGS` objects in `site/src/config/i18n.ts` do not contain a generic "commune" label; the fix is inline.

---

### F-007 — ResultPanel `aria-label="Cerrar"` → locale-aware (`site/src/components/map/ResultPanel.tsx`)

**All three occurrences** of the hardcoded `aria-label="Cerrar"` in `ResultPanel.tsx`:

1. **Loading skeleton** (line 138):
```tsx
<button className="panel-close" onClick={onClose} aria-label="Cerrar">×</button>
```

2. **Error state** (line 153):
```tsx
<button className="panel-close" onClick={onClose} aria-label="Cerrar">×</button>
```

3. **Main panel** (line 215):
```tsx
<button className="panel-close" onClick={onClose} aria-label="Cerrar">×</button>
```

**The existing locale pattern in ResultPanel.tsx** — all other strings already use inline `lang` ternary (lines 131, 152, 197–201, 229–230, etc.):

```tsx
// Existing pattern (line 131 — skeleton aria-label):
aria-label={lang === 'es' ? 'Cargando datos de la comuna' : 'Loading commune data'}

// Existing pattern (line 228-229 — badge):
{lang === 'es' ? `Nivel ${level}` : `Level ${level}`}

// Existing pattern (line 253):
#{data.national_rank} {lang === 'es' ? 'de' : 'of'} {TOTAL_COMMUNES}
```

**Fix pattern** — replace all three `aria-label="Cerrar"` with the same inline ternary:

```tsx
<button className="panel-close" onClick={onClose} aria-label={lang === 'es' ? 'Cerrar' : 'Close'}>×</button>
```

Apply identically to all 3 occurrences (lines 138, 153, 215).

---

### F-009 — Mobile nav (hamburger) (`site/src/components/PageHeader.astro`)

**Current state** — `csm-nav` is hidden at mobile via CSS (lines 96–106):

```css
.csm-nav {
  display: none;        /* hidden at all widths by default */
  align-items: center;
  gap: var(--sm);
  flex: 1;
}

@media (min-width: 640px) {
  .csm-nav {
    display: flex;      /* shown only at ≥ 640px */
  }
}
```

The header structure (lines 29–63):

```astro
<header class="csm-header">
  <a href={homeHref} class="wordmark" ...>...</a>

  <nav class="csm-nav" aria-label="Main navigation">
    <a href={homeHref} class="nav-link">{t.nav_home}</a>
    <a href={mapHref}  class="nav-link">{t.nav_map}</a>
    <a href={methodHref} class="nav-link">{t.nav_methodology}</a>
  </nav>

  <div class="header-right">
    <div class="lang-toggle" ...>...</div>
  </div>
</header>
```

**Pattern to add** — a zero-JS hamburger using a hidden `<input type="checkbox">` + CSS `:checked` sibling selector (no `client:*` directive — D-09 forbids it). This is the lightest pattern consistent with the codebase's "zero client directives" rule:

```astro
<!-- Insert between wordmark and csm-nav -->
<input type="checkbox" id="nav-toggle" class="nav-toggle-input" aria-hidden="true" />
<label for="nav-toggle" class="nav-toggle-btn" aria-label={t.nav_menu_open ?? 'Menu'}>
  <span class="burger-bar"></span>
  <span class="burger-bar"></span>
  <span class="burger-bar"></span>
</label>
```

CSS additions needed:

```css
/* Hide the checkbox itself */
.nav-toggle-input { display: none; }

/* Hamburger button: visible only below 640px */
.nav-toggle-btn {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  cursor: pointer;
  margin-left: auto;    /* push to right before lang-toggle */
}

@media (min-width: 640px) {
  .nav-toggle-btn { display: none; }
}

.burger-bar {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--ink);
  border-radius: 2px;
}

/* When checked, show the nav as a dropdown */
.nav-toggle-input:checked ~ .csm-nav {
  display: flex;
  flex-direction: column;
  position: absolute;
  top: var(--3xl);          /* below header (64px) */
  left: 0;
  right: 0;
  background: var(--card);
  border-bottom: 1px solid var(--line);
  padding: var(--sm) var(--lg);
  z-index: 99;
  gap: 0;
}

/* Keep desktop layout unchanged */
@media (min-width: 640px) {
  .nav-toggle-input:checked ~ .csm-nav {
    position: static;
    flex-direction: row;
    border-bottom: none;
    padding: 0;
  }
}
```

**Required i18n string** — add `nav_menu_open` to `I18nStrings` interface and both `EN_STRINGS` / `ES_STRINGS` in `site/src/config/i18n.ts`:

```ts
// In I18nStrings interface (after nav_methodology):
nav_menu_open: string;

// In EN_STRINGS:
nav_menu_open: 'Open navigation menu',

// In ES_STRINGS:
nav_menu_open: 'Abrir menú de navegación',
```

**Verification** — after build, DOM-check: `document.querySelector('.nav-toggle-btn')` must have `offsetParent !== null` at 375px; nav links must be reachable when checkbox is checked.

---

### D-06 — AdSlot placeholder cleanup (`site/src/components/AdSlot.astro`)

**Current state** (lines 30–33 markup, lines 52–58 style):

```astro
<!-- Markup (line 31-33) -->
  ) : (
    <div class="ad-placeholder" aria-hidden="true"></div>
  )}
```

```css
/* Style (lines 52–58) */
.ad-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg);
  border: 2px dashed var(--line);
  border-radius: var(--radius);
}
```

**Fix** — remove the dashed border; keep the reserved height by keeping the `.ad-slot--content` / `.ad-slot--bottom` height rules (lines 44–49) intact. The `<div class="ad-placeholder">` can stay as a structural element (fills the reserved height with a blank), but remove the visible border styles:

```css
/* AFTER fix — blank, invisible placeholder; height inherited from parent .ad-slot--{position} */
.ad-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg);
  /* Remove: border: 2px dashed var(--line); */
  /* Remove: border-radius: var(--radius);    */
}
```

**Preserved invariants:**
- Line 18: `const enabled = import.meta.env.ADSENSE_ENABLED === 'true';` — exact string compare, do not change.
- Lines 23–30: `<ins class="adsbygoogle" ...>` renders only when `enabled && publisherId` — do not change.
- Lines 44–49: height reservations (`90px` desktop, `50px` mobile) — do not change (CLS-safe).

---

## Shared Patterns

### i18n string resolution
**Source:** `site/src/config/i18n.ts` — `EN_STRINGS` / `ES_STRINGS` exported as `I18nStrings`
**Usage pattern** (from `CommuneRankingTable.astro` line 30, `PageHeader.astro` line 19):
```ts
const t = locale === 'en' ? EN_STRINGS : ES_STRINGS;
// then use t.nav_home, t.low_population_caveat, etc.
```
**Apply to:** F-009 (add `nav_menu_open` string); F-007 does NOT use the dict (inline ternary in TSX is the existing pattern there).

### Locale-conditional inline strings (React components)
**Source:** `site/src/components/map/ResultPanel.tsx` — all existing string branches use `lang === 'es' ? '...' : '...'` inline
**Apply to:** F-007 — copy this exact form for the 3 `aria-label` fixes.

### `loadRolloutCuts()` usage
**Source:** `site/src/lib/data.ts` lines 217–230
```ts
export function loadRolloutCuts(): string[] {
  if (process.env.ROLLOUT_ALL === 'true') {
    return loadIndex().map((c) => c.cut);
  }
  const rollout = JSON.parse(
    readFileSync(path.resolve(process.cwd(), 'src', 'config', 'rollout.json'), 'utf-8')
  ) as RolloutConfig;
  return rollout.enabled;
}
```
Returns `string[]` of CUT codes. Wrap in `new Set(loadRolloutCuts())` for O(1) membership test. Import alongside other loaders from `'../../lib/data.ts'` (or `'../../../lib/data.ts'` for ES pages). **Do not hardcode slug list** (D-02).

### CommuneRankingTable props interface
**Source:** `site/src/components/CommuneRankingTable.astro` lines 15–28
```ts
interface RankingRow {
  name: string;
  slug: string;      // used by the gate filter to look up CUT in index
  rate: number;
  national_rank: number;
  trend: 'up' | 'down' | 'stable';
  low_population: boolean;
}
```
The `slug` field is the bridge between `rankingRows` entries and the `index` array for CUT lookup. Both region and crime templates populate `slug` from `c.slug` (index entry) / `meta.slug`.

---

## No Analog Found

None — all changes have direct codebase anchors.

---

## Metadata

**Files read:** `data.ts`, `AdSlot.astro`, `ResultPanel.tsx`, `region/[slug].astro` (EN+ES), `crime/[family].astro`, `es/delitos-por-comuna.astro`, `PageHeader.astro`, `BaseLayout.astro`, `CommuneRankingTable.astro`, `i18n.ts`
**Pattern extraction date:** 2026-06-15
