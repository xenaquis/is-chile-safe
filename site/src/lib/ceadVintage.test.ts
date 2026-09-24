import { describe, it, expect } from 'vitest';
import { ceadVintage, formatCeadDate } from './ceadVintage.ts';
import type { SeriesEntry } from './data.ts';

function series2005to2026(): SeriesEntry[] {
  const out: SeriesEntry[] = [];
  for (let year = 2005; year <= 2025; year++) {
    out.push({ year, rate_per_100k: 1000, by_family: {} });
  }
  out.push({ year: 2026, rate_per_100k: 1380.3, by_family: {}, partial: true });
  return out;
}

describe('ceadVintage', () => {
  it('derives lastUpdated, partialYear and latestCompleteYear from a normal series', () => {
    const result = ceadVintage(series2005to2026(), '2026-06-16');
    expect(result).toEqual({
      lastUpdated: '2026-06-16',
      partialYear: 2026,
      latestCompleteYear: 2025,
    });
  });

  it('returns partialYear null and latestCompleteYear = max year when no entry is partial', () => {
    const series: SeriesEntry[] = [
      { year: 2023, rate_per_100k: 100, by_family: {} },
      { year: 2024, rate_per_100k: 110, by_family: {} },
      { year: 2025, rate_per_100k: 120, by_family: {} },
    ];
    const result = ceadVintage(series, '2026-06-16');
    expect(result.partialYear).toBeNull();
    expect(result.latestCompleteYear).toBe(2025);
  });

  it('returns lastUpdated null for undefined', () => {
    const result = ceadVintage(series2005to2026(), undefined);
    expect(result.lastUpdated).toBeNull();
  });

  it('returns lastUpdated null for empty string', () => {
    const result = ceadVintage(series2005to2026(), '');
    expect(result.lastUpdated).toBeNull();
  });

  it('returns lastUpdated null for an unparsable date', () => {
    const result = ceadVintage(series2005to2026(), 'not-a-date');
    expect(result.lastUpdated).toBeNull();
  });
});

describe('formatCeadDate', () => {
  it('formats an EN date as "June 16, 2026"', () => {
    expect(formatCeadDate('2026-06-16', 'en')).toBe('June 16, 2026');
  });

  it('formats an ES date as "16 de junio de 2026"', () => {
    expect(formatCeadDate('2026-06-16', 'es')).toBe('16 de junio de 2026');
  });

  it('formats a year-boundary EN date correctly under UTC regardless of system TZ', () => {
    // Negative control (see plan verify step): without timeZone:'UTC', running
    // this test under TZ=America/Santiago would render 'December 31, 2025'
    // instead, because local midnight 2026-01-01 is still 2025-12-31 in UTC-3/-4.
    expect(formatCeadDate('2026-01-01', 'en')).toBe('January 1, 2026');
  });
});
