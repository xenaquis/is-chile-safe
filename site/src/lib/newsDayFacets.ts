/**
 * newsDayFacets.ts — build-time day-histogram buckets for /news/ and
 * /es/noticias/ (news UX pass).
 *
 * Module Published Contract:
 * - Pure: no DOM, no `document`/`window`, no filesystem I/O. Receives the
 *   already-parsed incident dates as a plain string array.
 * - UTC/string-only arithmetic, ported verbatim from newsFacets.ts:87-90 —
 *   never local-time `new Date(y, m, d)`, never a locale-formatted date used
 *   as a key. Bucket keys are always YYYY-MM-DD.
 * - The bucket list is DENSE: every day in the window is emitted, including
 *   days with count 0. The histogram must show gaps as gaps; a sparse list
 *   would silently compress quiet days out of the axis and misrepresent the
 *   shape of the data.
 * - `anchorDate` is the newest incident's date (newsFacets.ts `anchorDate`),
 *   NOT build wall-clock. Passing wall-clock here would drift the histogram
 *   off the data whenever the news feed pauses.
 *
 * This module deliberately does NOT touch newsFacets.ts: that module's
 * published contract (F-20) and its assertions in scripts/validate/facets.mjs
 * are stable, and a day dimension is additive UI state, not part of the
 * indexed facet projection.
 */

export interface DayBucket {
  /** YYYY-MM-DD */
  date: string;
  count: number;
  /** 0-100, share of the busiest day in the window; 0 stays 0 (never floored up). */
  pct: number;
}

export const DAY_WINDOW_WIDTH = 30;

/**
 * lowerBoundDate — UTC-anchored lower-bound date string, ported verbatim from
 * newsFacets.ts:87-90.
 */
function lowerBoundDate(anchorMs: number, days: number): string {
  const ms = anchorMs - days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

/**
 * addDays — UTC string-only day arithmetic. Same discipline as lowerBoundDate,
 * expressed forwards so the caller can walk the window in order.
 */
function addDays(dateStr: string, days: number): string {
  const ms = Date.parse(dateStr + 'T00:00:00Z') + days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

/**
 * computeDayBuckets — one bucket per day in the inclusive window
 * [anchor - (width-1), anchor]. Returns [] when anchorDate is null (no
 * incidents), so the caller can skip rendering the histogram entirely rather
 * than render an empty axis.
 *
 * Dates outside the window are counted nowhere — that is intentional and
 * mirrors byWindow.thirtyDay in newsFacets.ts. The histogram is a control for
 * the 30-day window, not a full archive view.
 */
export function computeDayBuckets(
  dates: string[],
  anchorDate: string | null,
  width: number = DAY_WINDOW_WIDTH
): DayBucket[] {
  if (!anchorDate) return [];

  const anchorMs = Date.parse(anchorDate + 'T00:00:00Z');
  if (Number.isNaN(anchorMs)) return [];

  const lower = lowerBoundDate(anchorMs, width - 1);

  const counts = new Map<string, number>();
  for (const d of dates) {
    if (d < lower || d > anchorDate) continue;
    counts.set(d, (counts.get(d) ?? 0) + 1);
  }

  const days: string[] = [];
  for (let d = lower; d <= anchorDate; d = addDays(d, 1)) days.push(d);

  let max = 0;
  for (const d of days) max = Math.max(max, counts.get(d) ?? 0);

  return days.map((date) => {
    const count = counts.get(date) ?? 0;
    return {
      date,
      count,
      pct: max === 0 || count === 0 ? 0 : Math.round((count / max) * 100),
    };
  });
}

/**
 * peakBucket — the busiest day in the window, for the histogram's caption.
 * Ties resolve to the EARLIEST date (stable, and the earlier date is the one
 * a reader scanning left-to-right reaches first). Returns null for an empty
 * or all-zero window, so the caller can omit the caption instead of printing
 * a meaningless "peak 0".
 */
export function peakBucket(buckets: DayBucket[]): DayBucket | null {
  let peak: DayBucket | null = null;
  for (const b of buckets) {
    if (b.count === 0) continue;
    if (!peak || b.count > peak.count) peak = b;
  }
  return peak;
}
