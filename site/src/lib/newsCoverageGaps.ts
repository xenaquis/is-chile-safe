/**
 * newsCoverageGaps.ts — declared classification-outage ranges (G-18, R-01).
 *
 * These are days on which no incidents were collected because of a known
 * pipeline outage, not because nothing happened. See
 * .planning/phases/34-news-classification-restore/34-BACKFILL-AUDIT.md for
 * the outage timeline (started 2026-09-04 ~20:12Z per G-17; fix shipped
 * 2026-09-23 ~03:2xZ).
 *
 * Ranges are declared, not inferred from a min-gap-length heuristic — a
 * heuristic would also flag genuine quiet days. A range is NEVER removed
 * from this list, because per-day count > 0 already self-disables the flag
 * for that day (see computeDayBuckets in newsDayFacets.ts): if a partial
 * backfill later publishes incidents inside the range, those specific days
 * stop being flagged automatically, while days still missing data keep the
 * gap flag. Removing the range entirely would risk presenting a
 * still-unbackfilled day as a true zero-incident day (A-R1-08).
 */

export interface CoverageGap {
  from: string;
  to: string;
  source: string;
}

export const COVERAGE_GAPS: CoverageGap[] = [
  { from: '2026-09-05', to: '2026-09-22', source: 'G-18 classifier outage' },
];
