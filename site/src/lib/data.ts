/**
 * Build-time data loader for Phase 1 CEAD JSON output.
 *
 * DATA_ROOT is resolved via fileURLToPath(import.meta.url) parent traversal:
 *   site/src/lib/data.ts -> (4 levels up) -> repo-root -> data/cead
 *
 * NEVER use process.cwd() or import.meta.glob — both are CWD-dependent or
 * bundler-dependent and break cross-platform at build time.
 *
 * national.json and regions/{id}.json series[].rate_per_100k are POPULATION-
 * WEIGHTED MEAN rates (true per-capita incidence) as of quick-260616-klv — they
 * are valid rates, no longer the meaningless cross-commune SUMs they once were.
 * For the site's headline figures we still use loadNationalAverage() /
 * loadRegionalAverage(), which compute the UNWEIGHTED mean of non-low-population
 * commune rates (a "typical commune" statistic, distinct from the pop-weighted
 * incidence in the series). Pick deliberately: pop-weighted = true incidence;
 * unweighted = typical commune.
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

export interface CompositeIndexEntry {
  score: number;
  rank: number;
  regional_rank: number;
  level: 1 | 2 | 3 | 4 | 5;
  available_metrics: number;
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
  // Phase 18-04 additive field (D-12) — rides along in per-commune JSON
  composite_index?: Record<string, CompositeIndexEntry>;
  // Phase 23 additive field — present for 136 ENUSC-covered comunas, absent for 210
  enusc_vhdv?: {
    vhdv_rate: number;           // proportion 0–1 (e.g. 0.0478 = 4.78%); NOT per-100k
    ci_lower: number;            // 95% CI lower bound (proportion)
    ci_upper: number;            // 95% CI upper bound (proportion)
    tipo_estimacion: string;     // "Directa y sintética" | "Sintética"
    cv: number;                  // coefficient of variation (logarithmic)
    vintage: number;             // 2024
  };
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
 * Returns the Chilean administrative region file ID (1–16) for a commune's
 * region_id.
 *
 * As of backlog 999.1 (quick-260616-ldi) the pipeline derives region_id from
 * the CUT by length, so region_id is ALREADY the clean 1–16 region number —
 * this function is now an identity pass-through. It previously had to map
 * stored CEAD province codes (e.g. "56" → 5) back to regions, a lossy step
 * that collided "11"/"14" across Tarapacá and Aysén/Los Ríos. Kept as a named
 * indirection so call sites stay explicit; the legacy floor() fallback guards
 * against any not-yet-migrated data.
 */
export function regionFileId(regionId: string): string {
  const n = parseInt(regionId, 10);
  if (n >= 1 && n <= 16) return String(n);
  return String(Math.floor(n / 10)); // legacy guard — unreached for migrated data
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
 * NOTE: loadNational().series[].rate_per_100k is now the population-weighted
 * national rate (true incidence). This function returns a DIFFERENT statistic:
 * the unweighted mean of non-low-population commune rates ("typical commune").
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
 * NOTE: loadRegion(regionId).series[].rate_per_100k is now the population-
 * weighted regional rate (true incidence). This function returns a DIFFERENT
 * statistic: the unweighted mean of non-low-population commune rates.
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
 * RESOLVED (999.1, quick-260616-ldi): region_id is now derived from the CUT by
 * length, so it is the clean 1–16 region — the old Tarapacá 11/14 collision with
 * Aysén/Los Ríos is gone and same-region grouping is exact.
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
  ratesByYear: Record<number, number>;
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
    // Build ratesByYear from complete (non-partial) series entries using rate_per_100k.
    // This matches the displayed `rate` (latestCompleteYearRate) so the default-year
    // cell value is identical to the previous static render.
    const ratesByYear: Record<number, number> = {};
    comm.series.filter((s) => !s.partial).forEach((s) => {
      ratesByYear[s.year] = s.rate_per_100k;
    });
    return {
      name: c.name,
      slug: c.slug,
      rate: rateMap.get(c.cut) ?? 0,
      national_rank: comm.national_rank,
      trend: comm.trend,
      low_population: c.low_population,
      ratesByYear,
    };
  });
}

// ---------------------------------------------------------------------------
// Enabled comparator pair slugs (BUG-2 fix)
// ---------------------------------------------------------------------------

/**
 * Returns a Set of enabled comparator pair slugs in "${cutA}-vs-${cutB}" form.
 * cutA < cutB (lexicographic) — matches the canonical slug in compare/[pair].astro.
 * Memoized: the 5031-entry JSON is read once across all 692×2 commune page builds.
 */
let _enabledPairSlugsCache: Set<string> | null = null;

export function loadEnabledPairSlugs(): Set<string> {
  if (_enabledPairSlugsCache !== null) return _enabledPairSlugsCache;
  const pairsPath = path.resolve(process.cwd(), '..', 'data', 'comparator-pairs.json');
  const raw: Array<{ cutA: string; cutB: string; region_id: string; enabled: boolean }> =
    JSON.parse(readFileSync(pairsPath, 'utf-8'));
  const result = new Set<string>();
  for (const p of raw) {
    if (p.enabled === true) {
      result.add(`${p.cutA}-vs-${p.cutB}`);
    }
  }
  _enabledPairSlugsCache = result;
  return result;
}
