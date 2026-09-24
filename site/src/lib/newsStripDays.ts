/**
 * newsStripDays.ts — build/render-time day range for the map NewsStrip
 * (/map/, /es/mapa/). R2/F35-R1-06, G-22(b).
 *
 * Pure: no DOM, no fetch. Mirrors the UTC string-arithmetic discipline of
 * newsDayFacets.ts (never local-time `new Date(y, m, d)`, bucket keys are
 * always YYYY-MM-DD).
 *
 * The window starts at max(anchor-(windowDays-1), the earliest valid
 * UNFILTERED incident date) — the same coverage clip as computeDayBuckets —
 * replacing NewsStrip.tsx's old pre-coverage extension. Gap is decided on
 * the caller-supplied `unfilteredDates`, never on a family-filtered subset:
 * a family filter with no incident on a given day must not turn a covered
 * day into a false gap.
 */

import { COVERAGE_GAPS, type CoverageGap } from './newsCoverageGaps';

export interface StripDay {
  /** YYYY-MM-DD */
  date: string;
  /** true iff no incident in `unfilteredDates` falls on this date AND the
   *  date is inside a declared COVERAGE_GAPS range. */
  gap: boolean;
}

const CANONICAL_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function isValidDateStr(d: string): boolean {
  return CANONICAL_DATE_RE.test(d) && !Number.isNaN(Date.parse(d + 'T00:00:00Z'));
}

function earliestValidDate(dates: string[]): string | null {
  let earliest: string | null = null;
  for (const d of dates) {
    if (!isValidDateStr(d)) continue;
    if (earliest === null || d < earliest) earliest = d;
  }
  return earliest;
}

function addDays(dateStr: string, days: number): string {
  const ms = Date.parse(dateStr + 'T00:00:00Z') + days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

function lowerBoundDate(anchorMs: number, days: number): string {
  const ms = anchorMs - days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

/**
 * computeStripDays — one entry per day in the inclusive window
 * [max(anchor-(windowDays-1), earliest valid unfilteredDates), anchor].
 *
 * Returns [] when `anchor` is missing or malformed (no incidents / no valid
 * anchor to render a strip against).
 */
export function computeStripDays(
  anchor: string,
  windowDays: number,
  unfilteredDates: string[],
  gaps: CoverageGap[] = COVERAGE_GAPS
): StripDay[] {
  if (!anchor || !isValidDateStr(anchor)) return [];

  const anchorMs = Date.parse(anchor + 'T00:00:00Z');

  let lower = lowerBoundDate(anchorMs, windowDays - 1);
  const earliest = earliestValidDate(unfilteredDates);
  if (earliest !== null && earliest > lower) lower = earliest;

  const unfilteredSet = new Set(unfilteredDates.filter(isValidDateStr));

  const days: StripDay[] = [];
  for (let d = lower; d <= anchor; d = addDays(d, 1)) {
    const gap = !unfilteredSet.has(d) && gaps.some((g) => g.from <= d && d <= g.to);
    days.push({ date: d, gap });
  }
  return days;
}
