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
 *
 * `byMonth` de-duplication rule (fix cycle 1, H-1): a month present in BOTH the
 * archive and `current.json` (`source: 'both'`) reports the size of the UNION of
 * incident IDs across the two sources, never the archive count alone. The archive
 * is a point-in-time snapshot; incidents added to that month after the snapshot
 * was written exist only in `current.json` and must not be silently dropped from
 * the count. IDs are de-duplicated so a genuinely overlapping incident is not
 * double-counted. `currentCount` still reports the raw current.json-only count
 * for that month, unchanged.
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
  anchorDate: string | null;
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

/**
 * escapeForInlineScript (H-2, fix cycle 1) — `JSON.stringify` does NOT escape
 * `</script>`, and the facets projection is emitted into the page via
 * `set:html`, which is unescaped by definition. A `</script>` sequence inside
 * any serialized string (e.g. a poisoned `byFamily[].key`, which derives from
 * the LLM-classified `family` field over untrusted scraped press headlines)
 * would close the surrounding <script> element early and let the remainder be
 * parsed as markup — a live XSS breakout. Escaping `<` as `<` keeps the
 * result valid JSON (`JSON.parse` round-trips identically) while making a
 * literal `</script` sequence impossible to reconstruct from the output.
 */
export function escapeForInlineScript(json: string): string {
  return json.replace(/</g, '\\u003c');
}

interface ArchiveFile {
  generated?: string;
  window_days?: number;
  incidents?: IncidentLike[];
}

/**
 * Returns, per archive month, the Set of incident IDs it contains (not just a
 * count) — the union-of-IDs rule for 'both' months (H-1) needs the actual ID
 * sets, not pre-aggregated counts.
 */
function loadArchiveMonths(archiveDir: string): Map<string, Set<string>> {
  const result = new Map<string, Set<string>>();
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
      const ids = new Set(
        (raw.incidents ?? []).map((inc, i) => String((inc as IncidentLike).id ?? `${file}-${i}`))
      );
      result.set(yearMonth, ids);
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
  // L-2: a `cut` that fails to resolve here (e.g. malformed/unresolvable) is
  // DELIBERATELY dropped from every region bucket — that is the intended guard,
  // because facets.mjs assertion 2 then hard-fails the build on the data-quality
  // event (region sum stops matching total incident count). Do NOT "fix" this
  // into a silent `?? 'unknown'` bucket; that would hide the data problem instead
  // of failing the build on it.
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
  const archiveMonths = archiveDir ? loadArchiveMonths(archiveDir) : new Map<string, Set<string>>();
  const currentMonths = new Map<string, Set<string>>();
  for (const inc of incidents) {
    const yearMonth = inc.date.slice(0, 7);
    const id = String(inc.id ?? `${inc.cut}-${inc.date}`);
    if (!currentMonths.has(yearMonth)) currentMonths.set(yearMonth, new Set());
    currentMonths.get(yearMonth)!.add(id);
  }

  const allMonths = new Set<string>([...archiveMonths.keys(), ...currentMonths.keys()]);
  const byMonth: MonthBucket[] = Array.from(allMonths)
    .map((yearMonth) => {
      const archiveIds = archiveMonths.get(yearMonth);
      const currentIds = currentMonths.get(yearMonth);
      if (archiveIds && currentIds) {
        // H-1: count the UNION of IDs, not the archive count alone — a month
        // can hold incidents that exist only in current.json (added after the
        // archive snapshot was written).
        const union = new Set<string>([...archiveIds, ...currentIds]);
        return {
          yearMonth,
          count: union.size,
          source: 'both' as const,
          currentCount: currentIds.size,
        };
      }
      if (archiveIds) {
        return { yearMonth, count: archiveIds.size, source: 'archive' as const };
      }
      return { yearMonth, count: currentIds!.size, source: 'current' as const };
    })
    .sort((a, b) => b.yearMonth.localeCompare(a.yearMonth));

  return { byFamily, byRegion, byWindow, byMonth, facetKeys, anchorDate: newestDate };
}
