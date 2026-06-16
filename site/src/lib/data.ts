/**
 * Build-time data loader for Phase 1 CEAD JSON output.
 *
 * DATA_ROOT is resolved via fileURLToPath(import.meta.url) parent traversal:
 *   site/src/lib/data.ts -> (4 levels up) -> repo-root -> data/cead
 *
 * NEVER use process.cwd() or import.meta.glob — both are CWD-dependent or
 * bundler-dependent and break cross-platform at build time.
 *
 * PITFALL: national.json and regions/{id}.json rate_per_100k are SUM totals
 * across communes, NOT per-capita averages. Use loadNationalAverage() and
 * loadRegionalAverage() which compute MEAN of non-low-population commune rates.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

// Use process.cwd() (stable = site/ root during astro build/prerender) rather than
// import.meta.url which changes in bundled prerender chunks (dist/.prerender/).
// site/ -> .. -> repo-root -> data/cead
const DATA_ROOT = path.resolve(process.cwd(), '..', 'data', 'cead');

// --- Types ---

export interface CommuneMeta {
  cut: string;
  name: string;
  slug: string;
  region_id: string;
  population: number;
  low_population: boolean;
}

export interface SeriesEntry {
  year: number;
  rate_per_100k: number;
  by_family: Record<string, number>;
  partial?: boolean;
}

export interface CommuneData extends CommuneMeta {
  national_rank: number;
  regional_rank: number;
  trend: 'up' | 'down' | 'stable';
  featured_rates: {
    propiedad: Record<string, number>;
    homicidios: Record<string, number>;
    /** Homicide case count per year (subgroup 101). Dropped from map-payload per budget (D-09); lives here in per-commune JSON. */
    homicidios_count: Record<string, number>;
    secuestros: Record<string, number>;
  };
  series: SeriesEntry[];
  last_updated?: string;
  // Enriched by loadCommune()
  latestCompleteYear: number;
  regionName: string;
}

export interface RegionData {
  id: string;
  name: string;
  slug: string;
  series: SeriesEntry[];
  comuna_ranking?: Array<{ cut: string; name: string; rank: number }>;
}

export interface NationalData {
  name: string;
  series: SeriesEntry[];
}

export interface CatalogFamily {
  name: string;
  name_es: string;
  featured: boolean;
}

export interface CatalogData {
  family_keys: string[];
  families: Record<string, CatalogFamily>;
  featured_subgroups: Record<string, number | null>;
}

export interface ComparableResult extends CommuneMeta {
  rate: number;
  national_rank: number;
  trend: 'up' | 'down' | 'stable';
  regionName: string;
  fallback: boolean;
}

export interface RolloutConfig {
  enabled: string[];
}

// --- Region ID mapping ---

/**
 * Maps CEAD sub-regional grouping IDs (as stored in commune region_id) to
 * the Chilean administrative region file IDs (1–16).
 *
 * The index stores CEAD provincial codes (e.g. 56 for a Valparaíso sub-group)
 * but the region files use the standard Chilean region numbers (1–16).
 * Regions 10–16 are stored as-is; sub-regional codes ≥20 map to their
 * parent region by integer division: floor(56 / 10) = 5.
 */
export function regionFileId(regionId: string): string {
  const n = parseInt(regionId, 10);
  if (n >= 1 && n <= 16) return String(n);
  return String(Math.floor(n / 10));
}

// --- Module-level memoization caches (build-time only — data is immutable within a build) ---
// Safe because Astro builds are single-pass over static JSON (Assumption A2).
// No cache invalidation or TTL needed — caches are valid for the lifetime of the process.

let _indexCache: CommuneMeta[] | null = null;
const _communeCache = new Map<string, CommuneData>();
const _regionCache = new Map<string, RegionData>();
let _natAvg: number | null = null;
const _regAvg = new Map<string, number>();

// --- Core loaders ---

export function loadIndex(): CommuneMeta[] {
  if (_indexCache) return _indexCache;
  _indexCache = JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'meta', 'index.json'), 'utf-8')
  ) as CommuneMeta[];
  return _indexCache;
}

export function loadCatalog(): CatalogData {
  return JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'meta', 'catalog.json'), 'utf-8')
  ) as CatalogData;
}

export function loadNational(): NationalData {
  return JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'national.json'), 'utf-8')
  ) as NationalData;
}

export function loadRegion(regionId: string): RegionData {
  const hit = _regionCache.get(regionId);
  if (hit) return hit;
  const data = JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'regions', `${regionId}.json`), 'utf-8')
  ) as RegionData;
  _regionCache.set(regionId, data);
  return data;
}

/**
 * Load commune data with enriched fields:
 * - latestCompleteYear: max series[].year where partial !== true
 * - regionName: resolved from region JSON (the `name` field, no "Región de" prefix)
 */
export function loadCommune(cut: string): CommuneData {
  const hit = _communeCache.get(cut);
  if (hit) return hit;

  const raw = JSON.parse(
    readFileSync(path.join(DATA_ROOT, 'comunas', `${cut}.json`), 'utf-8')
  ) as Omit<CommuneData, 'latestCompleteYear' | 'regionName'>;

  const latestCompleteYear = raw.series
    .filter((s) => !s.partial)
    .reduce((max, s) => Math.max(max, s.year), 0);

  const region = loadRegion(regionFileId(raw.region_id));
  const regionName = region.name;

  // The per-commune JSON identifies the commune via `id` (e.g. "13101"), but
  // CommuneData/CommuneMeta model the CUT as `cut`. Populate `cut` from the
  // requested CUT (which equals the file's id) so downstream consumers that
  // read `commune.cut` (e.g. proseEngine's nearestComparable) work instead of
  // silently throwing and falling back to a self-referential comparable.
  const enriched: CommuneData = { ...raw, cut, latestCompleteYear, regionName };
  _communeCache.set(cut, enriched);
  return enriched;
}

// --- Build-time helpers ---

/**
 * Returns the latest complete year rate_per_100k for a commune.
 * Pitfall 5: never use partial:true entries for rate/family figures.
 */
export function latestCompleteYearRate(commune: CommuneData): number {
  const entry = commune.series.find(
    (s) => s.year === commune.latestCompleteYear && !s.partial
  );
  return entry?.rate_per_100k ?? 0;
}

/**
 * Compute the TRUE national average: MEAN of non-low-population commune rates
 * at their latest complete year.
 *
 * WARNING: loadNational().series[].rate_per_100k is a SUM of all commune rates
 * (in the millions) — NOT a per-capita average. This function returns the
 * correct per-capita mean (hundreds-to-low-thousands range).
 */
export function loadNationalAverage(): number {
  if (_natAvg !== null) return _natAvg;
  const index = loadIndex();
  const eligible = index.filter((c) => !c.low_population);
  const rates = eligible.map((c) => {
    const commune = loadCommune(c.cut);
    return latestCompleteYearRate(commune);
  });
  const sum = rates.reduce((acc, r) => acc + r, 0);
  _natAvg = rates.length > 0 ? sum / rates.length : 0;
  return _natAvg;
}

/**
 * Compute the TRUE regional average: MEAN of non-low-population commune rates
 * within a region at their latest complete year.
 *
 * WARNING: loadRegion(regionId).series[].rate_per_100k is a SUM (same pipeline
 * behaviour as national.json) — NOT a per-capita regional average.
 */
export function loadRegionalAverage(regionId: string): number {
  const hit = _regAvg.get(regionId);
  if (hit !== undefined) return hit;
  const index = loadIndex();
  const eligible = index.filter(
    (c) => c.region_id === regionId && !c.low_population
  );
  const rates = eligible.map((c) => {
    const commune = loadCommune(c.cut);
    return latestCompleteYearRate(commune);
  });
  const sum = rates.reduce((acc, r) => acc + r, 0);
  const avg = rates.length > 0 ? sum / rates.length : 0;
  _regAvg.set(regionId, avg);
  return avg;
}

/**
 * Returns enabled CUT codes per rollout gate.
 * ROLLOUT_ALL=true overrides rollout.json and returns all 346 communes.
 */
export function loadRolloutCuts(): string[] {
  if (process.env.ROLLOUT_ALL === 'true') {
    return loadIndex().map((c) => c.cut);
  }
  // Use process.cwd() (stable = site/ root during astro build/prerender) to locate
  // rollout.json. import.meta.url breaks in bundled prerender chunks (dist/.prerender/).
  const rollout = JSON.parse(
    readFileSync(
      path.resolve(process.cwd(), 'src', 'config', 'rollout.json'),
      'utf-8'
    )
  ) as RolloutConfig;
  return rollout.enabled;
}

/**
 * Find the nearest comparable commune (D-08).
 * Algorithm:
 * 1. Filter same-region communes: !low_population, cut !== targetCut
 * 2. If fewer than 2 candidates, fall back to national (all !low_population)
 * 3. Pick nearest by absolute rate difference to targetRate
 */
export function nearestComparable(targetCut: string): ComparableResult {
  const index = loadIndex();
  const target = index.find((c) => c.cut === targetCut);
  if (!target) throw new Error(`CUT ${targetCut} not found in index`);

  const targetCommune = loadCommune(targetCut);
  const targetRate = latestCompleteYearRate(targetCommune);

  const pool = index.filter((c) => !c.low_population && c.cut !== targetCut);
  const regional = pool.filter((c) => c.region_id === target.region_id);
  const candidates = regional.length >= 2 ? regional : pool;
  const fallback = regional.length < 2;

  // Build rate map for candidates
  const rateMap = new Map<string, number>();
  for (const c of candidates) {
    const comm = loadCommune(c.cut);
    rateMap.set(c.cut, latestCompleteYearRate(comm));
  }

  const best = candidates.reduce((prev, curr) => {
    const dPrev = Math.abs((rateMap.get(prev.cut) ?? 0) - targetRate);
    const dCurr = Math.abs((rateMap.get(curr.cut) ?? 0) - targetRate);
    return dCurr < dPrev ? curr : prev;
  });

  const bestCommune = loadCommune(best.cut);

  return {
    ...best,
    rate: rateMap.get(best.cut) ?? 0,
    national_rank: bestCommune.national_rank,
    trend: bestCommune.trend,
    regionName: bestCommune.regionName,
    fallback,
  };
}

/**
 * Find the N nearest comparable communes in the same region (D-07).
 * Used by the "similar comunas" spoke on the ficha hub page.
 *
 * Algorithm:
 * 1. Filter same-region communes: !low_population, cut !== targetCut
 * 2. Sort by ascending absolute rate distance to target's latest-complete-year rate
 * 3. Slice to n results
 *
 * NOTE (BUGFIX-999.1): Tarapacá region_id province codes 11/14 collide with
 * Aysén/Los Ríos — same-region grouping may be skewed for Tarapacá comunas.
 * Accept this known issue here; fix is to derive region from CUT (v1.2 backlog).
 *
 * Unlike nearestComparable (singular), there is NO national fallback —
 * same-region only per D-07.
 */
export interface RankingRow {
  name: string;
  slug: string;
  rate: number;
  national_rank: number;
  trend: 'up' | 'down' | 'stable';
  low_population: boolean;
}

export function nearestComparables(targetCut: string, n: number): RankingRow[] {
  const index = loadIndex();
  const target = index.find((c) => c.cut === targetCut);
  if (!target) throw new Error(`CUT ${targetCut} not found in index`);

  const targetCommune = loadCommune(targetCut);
  const targetRate = latestCompleteYearRate(targetCommune);

  // Same-region pool: exclude target itself and low_population communes
  const pool = index.filter(
    (c) => c.region_id === target.region_id && !c.low_population && c.cut !== targetCut
  );

  // Build rate map for pool
  const rateMap = new Map<string, number>();
  for (const c of pool) {
    const comm = loadCommune(c.cut);
    rateMap.set(c.cut, latestCompleteYearRate(comm));
  }

  // Sort by ascending absolute rate distance
  const sorted = pool
    .slice()
    .sort(
      (a, b) =>
        Math.abs((rateMap.get(a.cut) ?? 0) - targetRate) -
        Math.abs((rateMap.get(b.cut) ?? 0) - targetRate)
    )
    .slice(0, n);

  return sorted.map((c) => {
    const comm = loadCommune(c.cut);
    return {
      name: c.name,
      slug: c.slug,
      rate: rateMap.get(c.cut) ?? 0,
      national_rank: comm.national_rank,
      trend: comm.trend,
      low_population: c.low_population,
    };
  });
}
