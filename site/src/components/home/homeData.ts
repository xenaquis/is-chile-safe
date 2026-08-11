/**
 * homeData.ts — build-time data assembly for the Home v2 dashboard.
 *
 * NEW module (Landing v2 / proposal 6b). Build-time ONLY: imports colorScale
 * (chroma-js, Node-only) and lib/data loaders. Never import from a client
 * <script> — client modules read the inline #home-communes JSON blob instead.
 */
import {
  loadIndex,
  loadCommune,
  latestCompleteYearRate,
  loadNationalAverage,
  loadRegion,
  regionFileId,
} from '../../lib/data.ts';
import { levelForRate } from '../../lib/colorScale.ts';
import centroids from '../../data/comuna-centroids.json';

export interface HomeCommune {
  cut: string;
  name: string;
  slug: string;
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  national_rank: number;
  trend: 'up' | 'down' | 'stable';
  low_population: boolean;
  regionName: string;
  population: number;
  lat: number | null;
  lng: number | null;
  ratesByYear: Record<number, number>;
}

export interface HomeData {
  rows: HomeCommune[];          // all 346, enriched
  ranked: HomeCommune[];        // non-low-population, rate ascending
  lowest6: HomeCommune[];
  highest6: HomeCommune[];
  bandCounts: number[];         // index 0..4 = level 1..5, eligible only (!low_population, 256)
  nationalAvg: number;
  referenceYear: number;
  maxRate: number;
}

/** Compact per-commune record for the inline #home-communes JSON blob. */
export interface HomeBlobEntry {
  n: string;   // name
  s: string;   // slug
  r: number;   // rate (latest complete year)
  l: number;   // incidence level 1..5
  g: string;   // region name
  p: 0 | 1;    // low_population
}

const centroidByCut = new Map<string, { lat: number; lng: number }>(
  (centroids as Array<{ cut: string; lat: number; lng: number }>).map((c) => [
    c.cut,
    { lat: c.lat, lng: c.lng },
  ]),
);

let cached: HomeData | null = null;

export function buildHomeData(): HomeData {
  if (cached) return cached;

  const index = loadIndex();

  // region_id → name (loadRegion is process-cached: 16 reads at build, 0 at runtime)
  const regionNames: Record<string, string> = {};
  for (const id of new Set(index.map((c) => c.region_id))) {
    try {
      regionNames[id] = loadRegion(regionFileId(id)).name;
    } catch {
      // Missing region file must never fail the build — degrade to no label.
    }
  }

  const sampleCut = index.find((c) => !c.low_population)?.cut ?? '13101';
  const referenceYear = loadCommune(sampleCut).latestCompleteYear;

  const raw = index.map((c) => {
    const commune = loadCommune(c.cut);
    const ratesByYear: Record<number, number> = {};
    commune.series
      .filter((s) => !s.partial)
      .forEach((s) => {
        ratesByYear[s.year] = s.rate_per_100k;
      });
    const cen = centroidByCut.get(c.cut) ?? null;
    return {
      cut: c.cut,
      name: c.name,
      slug: c.slug,
      rate: latestCompleteYearRate(commune),
      national_rank: commune.national_rank,
      trend: commune.trend,
      low_population: c.low_population,
      regionName: regionNames[c.region_id] ?? '',
      population: c.population,
      lat: cen ? cen.lat : null,
      lng: cen ? cen.lng : null,
      ratesByYear,
    };
  });

  // WR-06 quintiles: value-threshold, over non-low-population rates ascending
  const sortedRates = raw
    .filter((c) => !c.low_population)
    .map((c) => c.rate)
    .sort((a, b) => a - b);

  // LPX-9: a 0 reported rate is a data gap, not "lowest incidence" — route it to
  // the neutral band 3, matching the guard used elsewhere in the directory.
  const rows: HomeCommune[] = raw.map((c) => ({
    ...c,
    level: c.rate > 0 ? levelForRate(c.rate, sortedRates) : 3,
  }));

  const ranked = rows
    .filter((c) => !c.low_population)
    .sort((a, b) => a.rate - b.rate);

  // Quintile strip counts the same universe as the extremes-card note
  // (!low_population, 256) — never the full 346, or the strip and the note
  // would disagree.
  const bandCounts = [0, 0, 0, 0, 0];
  rows.filter((c) => !c.low_population).forEach((c) => {
    bandCounts[c.level - 1] += 1;
  });

  cached = {
    rows,
    ranked,
    lowest6: ranked.slice(0, 6),
    highest6: ranked.slice(-6).reverse(),
    bandCounts,
    nationalAvg: loadNationalAverage(),
    referenceYear,
    maxRate: ranked.length ? ranked[ranked.length - 1].rate : 1,
  };
  return cached;
}

/** Serialize the compact blob consumed by the search + extremes enhancers. */
export function homeBlob(rows: HomeCommune[]): HomeBlobEntry[] {
  return rows.map((c) => ({
    n: c.name,
    s: c.slug,
    r: Math.round(c.rate),
    l: c.level,
    g: c.regionName,
    p: c.low_population ? 1 : 0,
  }));
}
