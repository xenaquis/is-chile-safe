/**
 * newsFacets.ts — shared build-time facet-computation module for /news/ and
 * /es/noticias/ (Phase 27, FACET-01..06).
 *
 * Module Published Contract (F-20 — Phase 28 inherits this without re-deriving it):
 * - Facet counts are unfiltered totals over the window — a cross-filtered UI
 *   recomputes client-side from `facetKeys` in Phase 28; Phase 27 ships the
 *   base index only (Decision 7).
 * - `regionId` is always a string matching `region_id` in index.json verbatim
 *   — never coerced to a number anywhere in the output shape (Decision 7).
 * - `cut` is coerced with `String(cut)` at every lookup boundary (Pitfall 3).
 *
 * "Today" is anchored to the newest incident's date, using UTC/string-only
 * arithmetic (Planning Decision 1) — never build wall-clock, never local-time
 * `Date` construction. `byWindow`'s three arrays are for build-time consumption
 * only — never serialize them into rendered HTML; only their `.length`s may be
 * surfaced downstream.
 *
 * `computeNewsFacets` receives already-parsed `incidents` as a parameter — it
 * never does its own current.json I/O (Pitfall 4). It DOES own archive-directory
 * reading with per-file existsSync/try-catch.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import type { CommuneMeta } from './data';

// --- Types ---

export interface IncidentLike {
  cut: string | number;
  date: string;
  family?: string;
  [k: string]: unknown;
}

export interface FacetBucket {
  key: string;
  count: number;
}

export interface WindowFacet {
  today: IncidentLike[];
  sevenDay: IncidentLike[];
  thirtyDay: IncidentLike[];
}

export interface MonthBucket {
  yearMonth: string;
  count: number;
  source: 'archive' | 'current' | 'both';
  currentCount?: number;
}

export interface FacetKeyEntry {
  id: string;
  family: string | null;
  regionId: string | null;
  yearMonth: string;
  window: 'today' | '7d' | '30d' | 'older';
}

export interface NewsFacetIndex {
  byFamily: FacetBucket[];
  byRegion: Array<{ regionId: string; count: number }>;
  byWindow: WindowFacet;
  byMonth: MonthBucket[];
  facetKeys: FacetKeyEntry[];
}

// --- Internal helpers ---

/**
 * lower(days) computes the UTC-anchored lower-bound date string for a window,
 * per Planning Decision 1. anchorMs is Date.parse(newestDate + 'T00:00:00Z').
 * Never local-time Date construction; never locale-formatted date strings;
 * never a Date object's local month accessor.
 */
function lowerBoundDate(anchorMs: number, days: number): string {
  const ms = anchorMs - days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

interface ArchiveFile {
  generated?: string;
  window_days?: number;
  incidents?: IncidentLike[];
}

function loadArchiveMonths(archiveDir: string): Map<string, number> {
  const result = new Map<string, number>();
  if (!existsSync(archiveDir)) return result;
  let files: string[] = [];
  try {
    files = readdirSync(archiveDir).filter((f) => /^\d{4}-\d{2}\.json$/.test(f));
  } catch {
    return result;
  }
  for (const file of files) {
    const yearMonth = file.replace('.json', '');
    try {
      const raw = JSON.parse(readFileSync(path.join(archiveDir, file), 'utf-8')) as ArchiveFile;
      const count = (raw.incidents ?? []).length;
      result.set(yearMonth, count);
    } catch {
      // Malformed archive month — skip, don't crash the build (Pitfall 4 discipline)
    }
  }
  return result;
}

// --- Main export ---

export function computeNewsFacets(
  incidents: IncidentLike[],
  index: CommuneMeta[],
  archiveDir?: string
): NewsFacetIndex {
  // --- byFamily: derived from data actually present, never familyDefs.ts keys ---
  const familyCounts = new Map<string, number>();
  for (const inc of incidents) {
    if (!inc.family) continue;
    familyCounts.set(inc.family, (familyCounts.get(inc.family) ?? 0) + 1);
  }
  const byFamily: FacetBucket[] = Array.from(familyCounts.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);

  // --- byRegion: via existing region_id in index.json, String(cut) coercion ---
  const cutToRegion = new Map<string, string>(index.map((c) => [c.cut, c.region_id]));
  const regionCounts = new Map<string, number>();
  for (const inc of incidents) {
    const regionId = cutToRegion.get(String(inc.cut));
    if (!regionId) continue;
    regionCounts.set(regionId, (regionCounts.get(regionId) ?? 0) + 1);
  }
  const byRegion: Array<{ regionId: string; count: number }> = Array.from(
    regionCounts.entries()
  )
    .map(([regionId, count]) => ({ regionId, count }))
    .sort((a, b) => Number(a.regionId) - Number(b.regionId));

  // --- byWindow + facetKeys: UTC/string-only arithmetic, anchored to newest incident date ---
  let newestDate: string | null = null;
  for (const inc of incidents) {
    if (!newestDate || inc.date > newestDate) newestDate = inc.date;
  }

  const byWindow: WindowFacet = { today: [], sevenDay: [], thirtyDay: [] };
  const facetKeys: FacetKeyEntry[] = [];

  if (newestDate) {
    const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
    const lower7 = lowerBoundDate(anchorMs, 6);
    const lower30 = lowerBoundDate(anchorMs, 29);

    for (const inc of incidents) {
      const isToday = inc.date === newestDate;
      const is7d = inc.date >= lower7;
      const is30d = inc.date >= lower30;

      if (isToday) byWindow.today.push(inc);
      if (is7d) byWindow.sevenDay.push(inc);
      if (is30d) byWindow.thirtyDay.push(inc);

      let windowTag: FacetKeyEntry['window'] = 'older';
      if (isToday) windowTag = 'today';
      else if (is7d) windowTag = '7d';
      else if (is30d) windowTag = '30d';

      const regionId = cutToRegion.get(String(inc.cut)) ?? null;
      facetKeys.push({
        id: String(inc.id ?? `${inc.cut}-${inc.date}-${facetKeys.length}`),
        family: inc.family ?? null,
        regionId,
        yearMonth: inc.date.slice(0, 7),
        window: windowTag,
      });
    }
  }

  // --- byMonth: union of archive months and months observed in incidents (Decision 2) ---
  const archiveMonths = archiveDir ? loadArchiveMonths(archiveDir) : new Map<string, number>();
  const currentMonths = new Map<string, number>();
  for (const inc of incidents) {
    const yearMonth = inc.date.slice(0, 7);
    currentMonths.set(yearMonth, (currentMonths.get(yearMonth) ?? 0) + 1);
  }

  const allMonths = new Set<string>([...archiveMonths.keys(), ...currentMonths.keys()]);
  const byMonth: MonthBucket[] = Array.from(allMonths)
    .map((yearMonth) => {
      const inArchive = archiveMonths.has(yearMonth);
      const inCurrent = currentMonths.has(yearMonth);
      if (inArchive && inCurrent) {
        return {
          yearMonth,
          count: archiveMonths.get(yearMonth)!,
          source: 'both' as const,
          currentCount: currentMonths.get(yearMonth)!,
        };
      }
      if (inArchive) {
        return { yearMonth, count: archiveMonths.get(yearMonth)!, source: 'archive' as const };
      }
      return { yearMonth, count: currentMonths.get(yearMonth)!, source: 'current' as const };
    })
    .sort((a, b) => b.yearMonth.localeCompare(a.yearMonth));

  return { byFamily, byRegion, byWindow, byMonth, facetKeys };
}
