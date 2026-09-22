# Phase 27: News Facet Data Model - Pattern Map

**Mapped:** 2026-07-30
**Files analyzed:** 4 (1 new lib module, 2 modified pages, 1 new validator + registration)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `site/src/lib/newsFacets.ts` (NEW) | utility/lib (build-time data-derivation module) | transform (batch aggregation over an already-loaded array) | `site/src/lib/data.ts` | exact — same role (build-time lib module), same conventions (memoization, typed exports, `process.cwd()`/`readFileSync` I/O), closely related domain (`familyDefs.ts` supplies the vocabulary this module counts against) |
| `site/src/pages/news.astro` (MODIFIED) | route/page (Astro SSG page, frontmatter data prep) | request-response (build-time render) | itself (pre-refactor version) / `site/src/pages/es/noticias.astro` | exact — this is a refactor-in-place; the ES sibling is the best "before" reference for what must stay byte-parity after the shared-module extraction |
| `site/src/pages/es/noticias.astro` (MODIFIED) | route/page | request-response | `site/src/pages/news.astro` | exact — near-byte-identical twin; same refactor shape applies verbatim, only `FAMILY_LABELS_ES`/locale strings swap |
| `site/scripts/validate/facets.mjs` (NEW, optional) | test/validator | batch (offline JSON assertion script) | `site/scripts/validate/freshness.mjs` | exact — same role (standalone `.mjs` validator reading `data/incidents/*.json` via `path.resolve(__dirname, ...)`, single-purpose exit-0/1 script) |
| `site/scripts/validate/all.mjs` (MODIFIED) | config/registry | batch (sequential script runner) | itself (pre-registration version) | exact — trivial one-line-plus-header-comment addition to an existing array |

## Pattern Assignments

### `site/src/lib/newsFacets.ts` (utility/lib, transform)

**Analog:** `site/src/lib/data.ts` (for module shape/conventions) + `site/src/lib/familyDefs.ts` (for the vocabulary it must consume, not redefine) + `site/src/pages/news.astro` (for the exact inline logic being generalized)

**Imports pattern** (`site/src/lib/data.ts:19-20`):
```typescript
import { readFileSync } from 'node:fs';
import path from 'node:path';
```
For the archive-directory read this phase newly introduces, also import `readdirSync` and `existsSync` (per RESEARCH.md's `loadArchiveMonths` example) — matches the exact style already used in `news.astro:14` (`import { existsSync, readFileSync } from 'node:fs';`).

**Path resolution — CRITICAL divergence to note explicitly:**
`data.ts` resolves `DATA_ROOT` via `path.resolve(process.cwd(), '..', 'data', 'cead')` (line 25) — i.e. `process.cwd()` is `site/`, and `data/` lives one level up at repo root. But `news.astro` resolves `current.json` via `path.resolve(process.cwd(), 'public/data/incidents/current.json')` (line 22) — the **synced public copy inside `site/`**, not the repo-root `data/` tree. `newsFacets.ts` must follow the `news.astro` convention (`site/public/data/incidents/...`) for `current.json`, and the same `public/data/incidents/archive/` for archive months — NOT the `data.ts` `../data/cead` pattern, which is for CEAD stats only. Mixing these two path bases is the single most likely defect in this phase.

**Type export pattern** (`site/src/lib/data.ts:29-36`):
```typescript
export interface CommuneMeta {
  cut: string;
  name: string;
  slug: string;
  region_id: string;
  population: number;
  low_population: boolean;
}
```
Follow this exact convention for `newsFacets.ts`: one exported `interface` per shape, e.g. `NewsFacetIndex`, `FacetBucket { key: string; count: number }`, `IncidentLike` (mirroring the inline incident shape already typed in `news.astro:25-35`).

**Memoization pattern** (`site/src/lib/data.ts:143-157`):
```typescript
let _indexCache: CommuneMeta[] | null = null;
// ...
export function loadIndex(): CommuneMeta[] {
  if (_indexCache) return _indexCache;
  _indexCache = JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'meta', 'index.json'), 'utf-8')
  ) as CommuneMeta[];
  return _indexCache;
}
```
Apply the same module-level `let _cache | null` + early-return guard if `newsFacets.ts` owns any repeated file reads (e.g. archive-month listing) — per RESEARCH.md, single-pass-per-build is safe to cache identically.

**Core aggregation pattern — reduce-into-Map, generalized** (`site/src/pages/news.astro:98-104`, to be lifted into `newsFacets.ts`):
```typescript
const monthGroups = new Map<string, typeof incidents>();
for (const incident of incidents) {
  const yearMonth = incident.date.slice(0, 7);
  if (!monthGroups.has(yearMonth)) monthGroups.set(yearMonth, []);
  monthGroups.get(yearMonth)!.push(incident);
}
```
Reuse this exact shape for `byFamily`/`byRegion`, keyed by `incident.family` / resolved `region_id` instead of `yearMonth` (RESEARCH.md Pattern 1). Do NOT enumerate `FAMILY_LABELS_EN`/`ES` keys for the family set — derive the key set from `new Set(incidents.map(i => i.family))` (Pitfall 2), then use `FAMILY_LABELS_EN[key]` purely for display.

**CUT→region resolution pattern** (`site/src/pages/news.astro:47-63`, generalize per RESEARCH.md Pattern 2):
```typescript
const _index = loadIndex(); // from site/src/lib/data.ts
const cutToCommune = new Map<string, { name: string; slug: string }>(
  _index.map((c) => [c.cut, { name: c.name, slug: c.slug }])
);
function getCommuneInfo(incident: { cut?: string | number; slug?: string }) {
  if (incident.cut != null) return cutToCommune.get(String(incident.cut));
  if (incident.slug) return slugToCommune.get(incident.slug);
  return undefined;
}
```
Build an analogous `cutToRegion = new Map<string, string>(_index.map((c) => [c.cut, c.region_id]))` and always coerce `String(incident.cut)` before `.get()` (Pitfall 3). Never re-derive `region_id` from CUT length — read it from `loadIndex()` (`CommuneMeta.region_id`, `data.ts:33`) exclusively.

**Error handling / graceful-degradation pattern** (`site/src/pages/news.astro:37-45`):
```typescript
if (existsSync(dataPath)) {
  try {
    const raw = JSON.parse(readFileSync(dataPath, 'utf-8'));
    generated = raw.generated ?? null;
    incidents = raw.incidents ?? [];
  } catch {
    // Malformed JSON — empty fallback
  }
}
```
Per Pitfall 4: `computeNewsFacets()` itself should accept already-parsed `incidents: IncidentLike[]` as a parameter (each page keeps owning this `existsSync`/try-catch exactly as today) — but if `newsFacets.ts` also owns archive-file reading (new I/O this phase), apply the identical per-file `existsSync` + try/catch discipline shown in RESEARCH.md's `loadArchiveMonths` example, never a single try/catch around the whole directory.

**Sort/family-count pattern** (RESEARCH.md Code Examples, mirrors ranking-page convention elsewhere in repo):
```typescript
function computeFamilyFacet(incidents: IncidentLike[]): Array<{ key: string; count: number }> {
  const counts = new Map<string, number>();
  for (const inc of incidents) {
    if (!inc.family) continue;
    counts.set(inc.family, (counts.get(inc.family) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);
}
```

---

### `site/src/pages/news.astro` / `site/src/pages/es/noticias.astro` (route/page, request-response)

**Analog:** each other (near-byte-identical twins) — the refactor target is to replace each page's inline `monthGroups`/`cutToCommune`/`familyLabel` block (lines ~47-104 in `news.astro`) with a single import + call:

```typescript
import { computeNewsFacets } from '../lib/newsFacets';
// ... existing existsSync/readFileSync/incidents loading UNCHANGED (Pitfall 4) ...
const facets = computeNewsFacets(incidents, loadIndex(), /* buildTimestamp or newest-incident logic internal to the module */);
```

Card rendering markup (`news.astro:152-187`) stays unchanged — only the data-prep frontmatter (imports + the block currently building `monthGroups`/`cutToCommune`/`slugToCommune`/`getCommuneInfo`/`familyLabel`) is replaced by the shared module call. The `safeUrl()` helper (lines 106-117) and JSON-LD block are page-local and NOT part of this extraction — leave as-is per RESEARCH.md scope (Phase 27 ships zero UI/markup changes, data-derivation only).

**hreflang/hydration note:** Neither page uses any client-side JS (`client:load`/`client:only`) — confirms FACET-06/07's "zero new shipped frontend JS" constraint is trivially satisfied; do not introduce any `client:*` directive in this refactor.

---

### `site/scripts/validate/facets.mjs` (NEW, optional validator)

**Analog:** `site/scripts/validate/freshness.mjs`

**Imports + path resolution pattern** (`freshness.mjs:18-25`):
```javascript
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const CURRENT_JSON_PATH = path.join(REPO_ROOT, 'data', 'incidents', 'current.json');
```
Note: this validator reads from **repo-root `data/incidents/current.json`** (via `fileURLToPath`/`__dirname`), which is a DIFFERENT path base than `news.astro`'s `process.cwd()`-relative `site/public/data/incidents/current.json`. Since `facets.mjs` runs standalone via `node scripts/validate/facets.mjs` (not through Astro), it should follow the `freshness.mjs` `__dirname`-based resolution, and validate consistency against whichever copy the built pages actually consumed (likely also worth reading the synced `site/public/data/...` copy if that's what `dist/` reflects — confirm which copy is authoritative for `dist/` output before writing the assertion).

**Guard-and-exit pattern** (`freshness.mjs:32-40`, `56-64`, `80-91`):
```javascript
if (!existsSync(CURRENT_JSON_PATH)) {
  console.error(`FAIL facets: ...`);
  process.exit(1);
}
let data;
try {
  data = JSON.parse(readFileSync(CURRENT_JSON_PATH, 'utf-8'));
} catch (err) {
  console.error(`FAIL facets: could not parse current.json — ${err.message}`);
  process.exit(1);
}
// ... assertion ...
if (/* assertion fails */) {
  console.error(`FAIL facets: <specific reason>`);
  process.exit(1);
}
console.log(`PASS facets: <summary>`);
```
Apply this exact guard-then-assert-then-exit(0/1) shape for each of FACET-01/02/03/04/05's sanity checks (sum-of-counts equality, region_id in 1..16, family set ⊆ 8-value VALID_FAMILIES, etc. — see RESEARCH.md's Validation Architecture table).

**Header-comment convention** (`freshness.mjs:1-16`): document validator number, purpose, exit codes 0/1 meaning, and usage command at the top of the file — matches every other validator in this directory.

---

### `site/scripts/validate/all.mjs` (MODIFIED, registry)

**Analog:** itself, pre-registration

**Registration pattern** (`all.mjs:38-54`):
```javascript
const VALIDATORS = [
  'structure.mjs',
  // ...
  'avs-b-budget.mjs',
  'freshness.mjs',
  'facets.mjs',        // NEW — add as entry #16
];
```
Also update the header doc-comment block (`all.mjs:2-19`) which enumerates all validators by number — add `16. facets.mjs — ...` and correct the numbering documentation, matching the exact style of the existing 15 numbered entries (e.g. line 19: `15.  freshness.mjs — data/incidents/current.json <= 3 days old`).

No other change to `all.mjs` is needed — the `spawnSync` loop (lines 58-84) and summary table (lines 86-110) are generic over the `VALIDATORS` array and require no modification.

---

## Shared Patterns

### `process.cwd()`-based build-time file I/O (two distinct path bases — do not conflate)
**Sources:**
- `site/src/lib/data.ts:22-25` — CEAD stats tree: `path.resolve(process.cwd(), '..', 'data', 'cead')` (repo-root `data/`, one level above `site/`)
- `site/src/pages/news.astro:19-22` — news incidents tree: `path.resolve(process.cwd(), 'public/data/incidents/current.json')` (synced copy INSIDE `site/public/`)

**Apply to:** `newsFacets.ts` must use the `news.astro` convention (`site/public/data/incidents/...`) for both `current.json` and the new `archive/` directory read — this is the single highest-risk pitfall in this phase per the analog mismatch above.

### Typed module exports (interfaces, not classes)
**Source:** `site/src/lib/data.ts:29-117` (11 exported interfaces, zero classes)
**Apply to:** `newsFacets.ts` — export `NewsFacetIndex`, `FacetBucket`, `IncidentLike` etc. as plain `interface`s; RESEARCH.md explicitly rejects a class-based `NewsFacetIndex` (Alternatives Considered) as inconsistent with every other `site/src/lib` module.

### Vocabulary reuse, never redefinition
**Source:** `site/src/lib/familyDefs.ts:18-28` (`FAMILY_LABELS_EN`/`_ES`), `site/src/lib/data.ts:151-157` (`loadIndex()` → `region_id`)
**Apply to:** `newsFacets.ts` must import `FAMILY_LABELS_EN`/`FAMILY_LABELS_ES` for display labels only (never enumerate their keys to build the facet value set — Pitfall 2) and `loadIndex()` for region_id lookup (never re-derive from CUT length — Anti-Pattern in RESEARCH.md).

### Standalone validator script shape
**Source:** `site/scripts/validate/freshness.mjs` (full file, 95 lines)
**Apply to:** `facets.mjs` — header comment block, `__dirname`-based path resolution, guard/parse/assert/exit(0|1) structure, `console.error`/`console.log` PASS/FAIL messaging convention.

## No Analog Found

None — all 4 files in scope have a strong (exact-match) analog already in the codebase; this phase is explicitly a generalization of existing, working code rather than a new pattern.

## Metadata

**Analog search scope:** `site/src/lib/`, `site/src/pages/` (news + es/noticias), `site/scripts/validate/`
**Files scanned:** `site/src/lib/data.ts` (435 lines, full read), `site/src/lib/familyDefs.ts` (122 lines, full read), `site/src/pages/news.astro` (279 lines, full read), `site/scripts/validate/all.mjs` (110 lines, full read), `site/scripts/validate/freshness.mjs` (95 lines, full read); `site/src/pages/es/noticias.astro` confirmed near-identical via RESEARCH.md (not re-read — RESEARCH.md already quoted/verified full parity)
**Pattern extraction date:** 2026-07-30
