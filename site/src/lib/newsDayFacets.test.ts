import { describe, it, expect } from 'vitest';
import { computeDayBuckets, peakBucket, DAY_WINDOW_WIDTH } from './newsDayFacets';

describe('computeDayBuckets', () => {
  it('returns [] when there is no anchor date', () => {
    expect(computeDayBuckets(['2026-08-01'], null)).toEqual([]);
  });

  it('emits one dense bucket per day of the inclusive window', () => {
    const buckets = computeDayBuckets(['2026-08-07'], '2026-08-07');
    expect(buckets).toHaveLength(DAY_WINDOW_WIDTH);
    expect(buckets[0].date).toBe('2026-07-09');
    expect(buckets[buckets.length - 1].date).toBe('2026-08-07');
  });

  it('keeps zero-count days in the series rather than dropping them', () => {
    const buckets = computeDayBuckets(['2026-08-07', '2026-08-05'], '2026-08-07', 5);
    expect(buckets.map((b) => b.date)).toEqual([
      '2026-08-03',
      '2026-08-04',
      '2026-08-05',
      '2026-08-06',
      '2026-08-07',
    ]);
    expect(buckets.map((b) => b.count)).toEqual([0, 0, 1, 0, 1]);
  });

  it('scales pct against the busiest day and never floors a zero up', () => {
    const buckets = computeDayBuckets(
      ['2026-08-07', '2026-08-07', '2026-08-07', '2026-08-07', '2026-08-05'],
      '2026-08-07',
      3
    );
    expect(buckets.map((b) => b.pct)).toEqual([25, 0, 100]);
  });

  it('excludes dates outside the window on both ends', () => {
    const buckets = computeDayBuckets(
      ['2026-06-01', '2026-08-05', '2026-09-01'],
      '2026-08-07',
      5
    );
    expect(buckets.reduce((n, b) => n + b.count, 0)).toBe(1);
  });

  it('uses UTC arithmetic across a month boundary', () => {
    const buckets = computeDayBuckets([], '2026-03-02', 4);
    expect(buckets.map((b) => b.date)).toEqual([
      '2026-02-27',
      '2026-02-28',
      '2026-03-01',
      '2026-03-02',
    ]);
  });

  it('returns [] for a malformed anchor rather than throwing', () => {
    expect(computeDayBuckets(['2026-08-07'], 'not-a-date')).toEqual([]);
  });
});

describe('peakBucket', () => {
  it('returns null for an all-zero window', () => {
    expect(peakBucket(computeDayBuckets([], '2026-08-07', 3))).toBeNull();
  });

  it('returns the busiest day', () => {
    const buckets = computeDayBuckets(
      ['2026-08-06', '2026-08-06', '2026-08-07'],
      '2026-08-07',
      3
    );
    expect(peakBucket(buckets)?.date).toBe('2026-08-06');
    expect(peakBucket(buckets)?.count).toBe(2);
  });

  it('resolves ties to the earliest date', () => {
    const buckets = computeDayBuckets(['2026-08-06', '2026-08-07'], '2026-08-07', 3);
    expect(peakBucket(buckets)?.date).toBe('2026-08-06');
  });
});
