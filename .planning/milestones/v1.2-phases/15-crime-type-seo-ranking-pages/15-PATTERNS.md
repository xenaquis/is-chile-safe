# Phase 15: Crime-Type SEO Ranking Pages — Pattern Map

**Mapped:** 2026-06-16
**Files analyzed:** 4 new/modified files
**Analogs found:** 4 / 4

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `site/src/pages/crime-ranking/[crime].astro` | page (controller) | CRUD / request-response (SSG) | `site/src/pages/crime/[family].astro` | exact |
| `site/src/pages/es/ranking-delito/[crime].astro` | page (controller) | CRUD / request-response (SSG) | `site/src/pages/es/delito/[family].astro` | exact |
| `site/src/lib/familyDefs.ts` | config / utility | transform | `site/src/lib/familyDefs.ts` (extend in-place) | self |
| `site/scripts/validate/seo.mjs` | validator / utility | batch | `site/scripts/validate/seo.mjs` (extend in-place) | self |

---

## Pattern Assignments

### `site/src/pages/crime-ranking/[crime].astro` (page, SSG)

**Analog:** `site/src/pages/crime/[family].astro`

**Imports pattern** (lines 21–33 of analog):
```typescript
import BaseLayout from '../../layouts/BaseLayout.astro';
import MapPlaceholderSlot from '../../components/MapPlaceholderSlot.astro';
import MethodologyCaveat from '../../components/MethodologyCaveat.astro';
import TrendChip from '../../components/TrendChip.astro';
import {
  loadIndex,
  loadCommune,
  loadCatalog,
  regionFileId,
} from '../../lib/data.ts';
import { FAMILY_SLUGS } from '../../config/i18n.ts';
import { FAMILY_LABELS_EN, FAMILY_DEFS_EN } from '../../lib/familyDefs';
import { buildBreadcrumb, buildItemList } from '../../lib/jsonld.ts';
```

**IMPORTANT path adjustment:** New page lives at `site/src/pages/crime-ranking/[crime].astro` (one level deeper than `crime/[family].astro`), so relative imports need one additional `../`:
```typescript
import BaseLayout from '../../../layouts/BaseLayout.astro';
// etc.
```
Verify depth: `pages/crime-ranking/` → `../../` reaches `src/`, so three `../` needed for `layouts/`. Check `pages/crime/[family].astro` uses `../../layouts/` — same depth (file is inside `crime/`). New file is inside `crime-ranking/` — same depth. Import paths are identical.

---

**getStaticPaths pattern** — REPLACE catalog.family_keys iteration with explicit crime-type list (analog lines 35–41, but adapted):

```typescript
// Analog (crime/[family].astro lines 35–41) — for reference:
export async function getStaticPaths() {
  const catalog = loadCatalog();
  return catalog.family_keys.map((key) => ({
    params: { family: FAMILY_SLUGS[key]!.en },
    props: { familyKey: key },
  }));
}

// Phase 15 replacement — explicit list, static paths, no catalog dependency:
const CRIME_RANKING_DEFS = [
  { param: 'homicide',        familyKey: 'homicidios',      dataSource: 'featured_rates' as const },
  { param: 'violent-robbery', familyKey: 'robos_violentos', dataSource: 'by_family'      as const },
  { param: 'drug-crimes',     familyKey: 'drogas',          dataSource: 'by_family'      as const },
  { param: 'property',        familyKey: 'propiedad',       dataSource: 'by_family'      as const },
  { param: 'domestic-violence', familyKey: 'vif',           dataSource: 'by_family'      as const },
  { param: 'weapons',         familyKey: 'armas',           dataSource: 'by_family'      as const },
  { param: 'disorder',        familyKey: 'incivilidades',   dataSource: 'by_family'      as const },
  { param: 'life-crimes',     familyKey: 'vida',            dataSource: 'by_family'      as const },
] as const;

export async function getStaticPaths() {
  return CRIME_RANKING_DEFS.map((def) => ({
    params: { crime: def.param },
    props: def,
  }));
}
```

**URL slug wiring** — hardcode enPath/esPath, never use getRelativeLocaleUrl (i18n-localized-slug-pitfall):

```typescript
// Per-slug ES mapping (hardcoded — no getRelativeLocaleUrl)
const ES_CRIME_SLUGS: Record<string, string> = {
  homicide:          'homicidios',
  'violent-robbery': 'robos-violentos',
  'drug-crimes':     'drogas',
  property:          'propiedad',
  'domestic-violence': 'violencia-intrafamiliar',
  weapons:           'armas',
  disorder:          'incivilidades',
  'life-crimes':     'delitos-contra-la-vida',
};

const { crime, familyKey, dataSource } = Astro.props;
const enPath = `/crime-ranking/${crime}/`;
const esPath = `/es/ranking-delito/${ES_CRIME_SLUGS[crime]}/`;
```

**Rate extraction — CRITICAL BRANCH** (analog lines 73–77 show by_family path; Phase 15 adds homicide branch):

```typescript
// Analog (crime/[family].astro lines 69–87) — by_family path:
for (const meta of index) {
  const commune = loadCommune(meta.cut);
  if (!meta.low_population) {
    latestYear = Math.max(latestYear, commune.latestCompleteYear);
  }
  const entry = commune.series.find(
    (s) => s.year === commune.latestCompleteYear && !s.partial
  );
  const rate = entry?.by_family?.[familyKey] ?? 0;
  allRows.push({ name: meta.name, slug: meta.slug, cut: meta.cut,
    regionName: commune.regionName, regionFileIdStr: regionFileId(meta.region_id),
    rate, trend: commune.trend, low_population: meta.low_population });
}

// Phase 15 adaptation — branch on dataSource prop:
for (const meta of index) {
  const commune = loadCommune(meta.cut);
  if (!meta.low_population) {
    latestYear = Math.max(latestYear, commune.latestCompleteYear);
  }
  let rate: number;
  if (dataSource === 'featured_rates') {
    // Homicide subgroup — lives in featured_rates, NOT by_family
    rate = commune.featured_rates?.homicidios?.[commune.latestCompleteYear] ?? 0;
  } else {
    const entry = commune.series.find(
      (s) => s.year === commune.latestCompleteYear && !s.partial
    );
    rate = entry?.by_family?.[familyKey] ?? 0;
  }
  allRows.push({ name: meta.name, slug: meta.slug, cut: meta.cut,
    regionName: commune.regionName, regionFileIdStr: regionFileId(meta.region_id),
    rate, trend: commune.trend, low_population: meta.low_population });
}
```

**Rank assignment + region breakdown** — copy verbatim from analog (lines 90–128). No changes needed.

**JSON-LD construction** (analog lines 146–178):
```typescript
// Copy Dataset block from analog lines 146–162, substituting familyLabel.
// Breadcrumb for ranking pages — 2-level: Home › Crime Rankings
const breadcrumb = buildBreadcrumb([
  { name: 'Home', url: 'https://ischilesafe.com/' },
  { name: 'Crime Rankings' },  // current page — no url
]);

// ItemList — name MUST NOT contain: safe, dangerous, safest, most dangerous
const eligibleRankingRows = rankingRows.filter((r) => !r.low_population);
const ranking = buildItemList(eligibleRankingRows, 'en', {
  name: `Communes by reported ${familyLabel.toLowerCase()} incidence (descending)`,
  order: 'Descending',
});

const jsonLd = [jsonLdDataset, breadcrumb, ranking];
```

**BaseLayout invocation** (analog lines 181–190):
```astro
<BaseLayout
  lang="en"
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
  jsonLd={jsonLd}
  mountType="crime-type-map"
  pageType="crime"
>
```

**H1 pattern** (sober framing — passes forbidden-language validator):
```astro
<h1 class="crime-h1">
  Communes with the Highest Reported {familyLabel} Incidence in Chile
</h1>
<p class="crime-def">{familyDef}</p>
```

**Commune table link** (analog line 233):
```astro
<a href={`/commune/${row.slug}/`} class="commune-link">{row.name}</a>
```

**Styles block** — copy `<style>` section verbatim from analog (lines 283–504). Identical CSS classes.

---

### `site/src/pages/es/ranking-delito/[crime].astro` (page, SSG)

**Analog:** `site/src/pages/es/delito/[family].astro`

This is the exact ES mirror of the EN page above. All patterns identical except:

**Import depth** (analog lines 14–26 — three `../../../` levels up):
```typescript
import BaseLayout from '../../../layouts/BaseLayout.astro';
import MapPlaceholderSlot from '../../../components/MapPlaceholderSlot.astro';
import MethodologyCaveat from '../../../components/MethodologyCaveat.astro';
import TrendChip from '../../../components/TrendChip.astro';
import { loadIndex, loadCommune, loadCatalog, regionFileId } from '../../../lib/data.ts';
import { FAMILY_SLUGS } from '../../../config/i18n.ts';
import { FAMILY_LABELS_ES, FAMILY_DEFS_ES } from '../../../lib/familyDefs';
import { buildBreadcrumb, buildItemList } from '../../../lib/jsonld.ts';
```

**IMPORTANT path check:** `pages/es/ranking-delito/[crime].astro` is 3 levels deep from `src/` — same as analog `pages/es/delito/[family].astro`. Import paths are identical to analog.

**getStaticPaths** — same CRIME_RANKING_DEFS list as EN, but params key is the ES slug:
```typescript
export async function getStaticPaths() {
  return CRIME_RANKING_DEFS.map((def) => ({
    params: { crime: ES_CRIME_SLUGS[def.param] },  // ES slug as param
    props: def,
  }));
}
```

**enPath/esPath** — derived from same ES_CRIME_SLUGS map:
```typescript
const enPath = `/crime-ranking/${crime_en_param}/`;  // stored in props
const esPath = `/es/ranking-delito/${crime}/`;        // crime is the ES slug param
```
Practical approach: store BOTH en and es params in props from getStaticPaths.

**Breadcrumb ES** (analog lines 156–159):
```typescript
const breadcrumb = buildBreadcrumb([
  { name: 'Inicio', url: 'https://ischilesafe.com/es/' },
  { name: 'Ranking de Delitos' },  // current page — no url
]);
```

**ItemList ES** (analog lines 163–167):
```typescript
const ranking = buildItemList(eligibleRankingRows, 'es', {
  name: `Comunas por incidencia reportada de ${familyLabel.toLowerCase()} (descendente)`,
  order: 'Descending',
});
```

**BaseLayout ES** (analog lines 172–181):
```astro
<BaseLayout
  lang="es"
  title={title}
  description={description}
  enPath={enPath}
  esPath={esPath}
  jsonLd={jsonLd}
  mountType="crime-type-map"
  pageType="crime"
>
```

**H1 ES** (sober framing):
```astro
<h1 class="crime-h1">
  Comunas con mayor incidencia de {familyLabel.toLowerCase()} reportados en Chile
</h1>
<p class="crime-def">{familyDef}</p>
```

**Commune table link ES** (analog line 224):
```astro
<a href={`/es/comuna/${row.slug}/`} class="commune-link">{row.name}</a>
```

**Styles block** — copy `<style>` section verbatim from ES analog (lines 274–495). Identical to EN styles.

---

### `site/src/lib/familyDefs.ts` (config, extend in-place)

**Analog:** `site/src/lib/familyDefs.ts` (self — extend existing records)

**Current state** (lines 1–63): File already exports `FAMILY_LABELS_EN/ES`, `FAMILY_DEFS_EN/ES`, and `FAMILY_ORDER`. The `homicidios` key is already present in all four records (lines 27, 38, 50, 62).

**What Phase 15 needs:** The existing entries may serve as-is for the 8 crime types. However, the ranking pages need methodology notes that are more detailed than the one-liners in `FAMILY_DEFS_EN/ES`. Two options:

**Option A (minimal):** Reuse existing `FAMILY_DEFS_EN/ES` as the methodology paragraph. No changes to `familyDefs.ts`.

**Option B (preferred per RESEARCH.md):** Add `RANKING_METHODOLOGY_EN` and `RANKING_METHODOLOGY_ES` records with fuller methodology text. Follow the exact Record<string, string> pattern:

```typescript
// Add after existing FAMILY_DEFS_ES block (after line 63)

// Extended methodology notes for crime-ranking pages
export const RANKING_METHODOLOGY_EN: Record<string, string> = {
  homicidios:      'Reported homicide incidence per 100,000 inhabitants by commune. Includes homicide, femicide, parricide, infanticide, and related offences (CEAD subgroup 101 within the Life Crimes family). Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  robos_violentos: 'Reported violent robbery incidence per 100,000 inhabitants by commune. Includes robbery with violence and robbery with intimidation. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  drogas:          'Reported drug offence incidence per 100,000 inhabitants by commune. Includes possession (porte) and trafficking (tráfico and microtráfico). Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  propiedad:       'Reported property crime incidence per 100,000 inhabitants by commune. Includes burglary, theft (hurto), and fraud — the full CEAD "Delitos contra la Propiedad" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  vif:             'Reported domestic and intra-family violence incidence per 100,000 inhabitants by commune. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  armas:           'Reported weapons offence incidence per 100,000 inhabitants by commune. Includes illegal possession and trafficking of firearms. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  incivilidades:   'Reported public disorder incidence per 100,000 inhabitants by commune. Includes the full CEAD "Incivilidades" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
  vida:            'Reported life crimes incidence per 100,000 inhabitants by commune. Includes all offences against life and physical integrity in the CEAD "Delitos contra la Vida" family aggregate. Figures represent police reports (denuncias), not convictions. Source: CEAD — Ministry of Interior and Public Security, official police statistics.',
};

export const RANKING_METHODOLOGY_ES: Record<string, string> = {
  homicidios:      'Incidencia reportada de homicidios por 100.000 habitantes por comuna. Incluye homicidio, femicidio, parricidio, infanticidio y delitos relacionados (subgrupo CEAD 101 dentro de Delitos contra la Vida). Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  robos_violentos: 'Incidencia reportada de robos violentos por 100.000 habitantes por comuna. Incluye robo con violencia y robo con intimidación. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  drogas:          'Incidencia reportada de delitos de drogas por 100.000 habitantes por comuna. Incluye porte y tráfico (tráfico y microtráfico). Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  propiedad:       'Incidencia reportada de delitos contra la propiedad por 100.000 habitantes por comuna. Incluye robos en lugar habitado, hurtos y fraudes — el total de la familia CEAD "Delitos contra la Propiedad". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  vif:             'Incidencia reportada de violencia intrafamiliar por 100.000 habitantes por comuna. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  armas:           'Incidencia reportada de delitos de armas por 100.000 habitantes por comuna. Incluye porte ilegal y tráfico de armas de fuego. Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  incivilidades:   'Incidencia reportada de incivilidades por 100.000 habitantes por comuna. Incluye el total de la familia CEAD "Incivilidades". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
  vida:            'Incidencia reportada de delitos contra la vida por 100.000 habitantes por comuna. Incluye todos los delitos contra la vida e integridad física de la familia CEAD "Delitos contra la Vida". Las cifras corresponden a denuncias policiales, no a condenas. Fuente: CEAD — Ministerio del Interior y Seguridad Pública, estadísticas policiales oficiales.',
};
```

All strings verified against `forbidden-language.mjs` FORBIDDEN_TERMS and `jsonld.ts` FORBIDDEN guard — none of the proposed strings contain blocked terms.

---

### `site/scripts/validate/seo.mjs` (validator, extend in-place)

**Analog:** `site/scripts/validate/seo.mjs` (self — extend SAMPLES array)

**Current SAMPLES array** (lines 179–193):
```javascript
const enCrimeDir = path.join(DIST_DIR, 'crime');          // line 169
const esCrimeDir = path.join(DIST_DIR, 'es', 'delito');   // line 170
const firstCrimeEn = firstSubdir(enCrimeDir);              // line 176
const firstCrimeEs = firstSubdir(esCrimeDir);              // line 177

// SAMPLES array includes:
...(firstCrimeEn ? [[path.join(enCrimeDir, firstCrimeEn, 'index.html'), `crime/${firstCrimeEn} (EN)`, false]] : []),
...(firstCrimeEs ? [[path.join(esCrimeDir, firstCrimeEs, 'index.html'), `crime/${firstCrimeEs} (ES)`, true]] : []),
```

**What to add** — mirror the exact pattern for the new URL namespaces. Insert after the existing `enCrimeDir`/`esCrimeDir` variable declarations (after line 170) and after line 177:

```javascript
// Add after line 170:
const enCrimeRankingDir = path.join(DIST_DIR, 'crime-ranking');
const esCrimeRankingDir = path.join(DIST_DIR, 'es', 'ranking-delito');

// Add after line 177:
const firstCrimeRankingEn = firstSubdir(enCrimeRankingDir);
const firstCrimeRankingEs = firstSubdir(esCrimeRankingDir);
```

Then add to SAMPLES array (insert after the existing crime entries at lines 187–188):
```javascript
...(firstCrimeRankingEn ? [[path.join(enCrimeRankingDir, firstCrimeRankingEn, 'index.html'), `crime-ranking/${firstCrimeRankingEn} (EN)`, false]] : []),
...(firstCrimeRankingEs ? [[path.join(esCrimeRankingDir, firstCrimeRankingEs, 'index.html'), `ranking-delito/${firstCrimeRankingEs} (ES)`,  true]] : []),
```

This follows the identical `firstSubdir` heuristic already used for all other template types. The guard (`firstCrimeRankingEn ?`) means the assertion is skipped (not failed) on builds that predate Phase 15.

---

## Shared Patterns

### getStaticPaths + RankRow computation
**Source:** `site/src/pages/crime/[family].astro` lines 35–128
**Apply to:** Both new `[crime].astro` pages
- `RankRow` type definition (lines 52–63) — copy verbatim
- `latestYear` capture loop with `Math.max` (lines 66–88) — copy, add homicide branch
- `eligibleRows` / `lowPopRows` sort + `rankCounter` assignment (lines 90–98) — copy verbatim
- `familyNationalMean` computation (lines 100–104) — copy verbatim
- Region breakdown `regionMap` loop (lines 113–128) — copy verbatim

### BaseLayout props
**Source:** `site/src/pages/crime/[family].astro` lines 181–190
**Apply to:** Both new pages
- `lang`, `title`, `description`, `enPath`, `esPath`, `jsonLd` — same prop names
- `mountType="crime-type-map"` — same value
- `pageType="crime"` — same value (triggers `/og/crime.png` OG image)

### JSON-LD Dataset shape
**Source:** `site/src/pages/crime/[family].astro` lines 146–162
**Apply to:** Both new pages — copy verbatim substituting `familyLabel` and `enPath`/`esPath`

### buildItemList editorial guard
**Source:** `site/src/lib/jsonld.ts` (FORBIDDEN const — verified in RESEARCH.md)
**Apply to:** All `buildItemList()` calls in both new pages
- Blocked words in `name` param: `'safest'`, `'most dangerous'`, `'safe'`, `'dangerous'`
- Compliant pattern: `"Communes by reported {familyLabel} incidence (descending)"`
- ES compliant: `"Comunas por incidencia reportada de {familyLabel} (descendente)"`

### Commune internal link pattern
**Source:** `site/src/pages/crime/[family].astro` line 233 (EN) and `es/delito/[family].astro` line 224 (ES)
**Apply to:** Ranking table rows in both new pages
```astro
<!-- EN -->
<a href={`/commune/${row.slug}/`} class="commune-link">{row.name}</a>
<!-- ES -->
<a href={`/es/comuna/${row.slug}/`} class="commune-link">{row.name}</a>
```

### Hardcoded esPath (no getRelativeLocaleUrl)
**Source:** Project memory `i18n-localized-slug-pitfall` + `es/delito/[family].astro` line 127
**Apply to:** Both new pages — never derive ES path from `getRelativeLocaleUrl`; hardcode as string constant.

---

## No Analog Found

None — all files have close analogs.

---

## Critical Anti-Patterns (from RESEARCH.md)

| Anti-Pattern | Why It Fails | Correct Approach |
|-------------|-------------|-----------------|
| `entry?.by_family?.['homicidios']` | Returns `undefined` → 0 for all 346 communes; ranking is meaningless | `commune.featured_rates?.homicidios?.[commune.latestCompleteYear] ?? 0` |
| New page at `/crime/homicide/` | Collides with existing `vida` family slug (`FAMILY_SLUGS.vida.en === 'homicide'`) | Use `/crime-ranking/homicide/` namespace |
| `getRelativeLocaleUrl('es', '/crime-ranking/homicide/')` | Returns `/es/crime-ranking/homicide/` — wrong; 404 | Hardcode `esPath = '/es/ranking-delito/homicidios/'` |
| `buildItemList({name: '...safe...'})` | Throws at build time from `assertSafeName()` in `jsonld.ts` | Use "by reported incidence (descending)" pattern |

---

## Metadata

**Analog search scope:** `site/src/pages/crime/`, `site/src/pages/es/delito/`, `site/src/lib/`, `site/scripts/validate/`
**Files scanned:** 4 primary analog files read in full
**Pattern extraction date:** 2026-06-16
