import { describe, it, expect } from 'vitest';
import { computeDayBuckets, peakBucket, DAY_WINDOW_WIDTH } from './newsDayFacets';

describe('computeDayBuckets', () => {
  it('returns [] when there is no anchor date', () => {
    expect(computeDayBuckets(['2026-08-01'], null)).toEqual([]);
  });

  it('emits one dense bucket per day of the inclusive window', () => {
    const buckets = computeDayBuckets(['2026-07-09', '2026-08-07'], '2026-08-07');
    expect(buckets).toHaveLength(DAY_WINDOW_WIDTH);
    expect(buckets[0].date).toBe('2026-07-09');
    expect(buckets[buckets.length - 1].date).toBe('2026-08-07');
  });

  it('keeps zero-count days in the series rather than dropping them', () => {
    const buckets = computeDayBuckets(['2026-08-07', '2026-08-03'], '2026-08-07', 5);
    expect(buckets.map((b) => b.date)).toEqual([
      '2026-08-03',
      '2026-08-04',
      '2026-08-05',
      '2026-08-06',
      '2026-08-07',
    ]);
    expect(buckets.map((b) => b.count)).toEqual([1, 0, 0, 0, 1]);
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

  // --- FRESH-02: coverage clipping ---------------------------------------

  it('clips the window to the earliest incident date (prod shape: 08-24..09-04)', () => {
    const dates: string[] = [];
    for (let ms = Date.parse('2026-08-24T00:00:00Z'); ms <= Date.parse('2026-09-04T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    const buckets = computeDayBuckets(dates, '2026-09-04');
    expect(buckets).toHaveLength(12);
    expect(buckets[0].date).toBe('2026-08-24');
    expect(buckets[buckets.length - 1].date).toBe('2026-09-04');
    expect(buckets.every((b) => b.date >= '2026-08-24')).toBe(true);
  });

  it('an internal zero day inside the clipped coverage is still drawn', () => {
    const buckets = computeDayBuckets(['2026-08-07', '2026-08-03'], '2026-08-07', 5);
    expect(buckets.map((b) => b.date)).toEqual([
      '2026-08-03',
      '2026-08-04',
      '2026-08-05',
      '2026-08-06',
      '2026-08-07',
    ]);
    expect(buckets.map((b) => b.count)).toEqual([1, 0, 0, 0, 1]);
  });

  it('still caps at the width when data spans more than 30 days', () => {
    const buckets = computeDayBuckets(['2026-07-01', '2026-08-07'], '2026-08-07');
    expect(buckets).toHaveLength(30);
    expect(buckets[0].date).toBe('2026-07-09');
  });

  it('an empty dates array with an anchor leaves the window unclipped', () => {
    expect(computeDayBuckets([], '2026-03-02', 4).map((b) => b.date)).toEqual([
      '2026-02-27',
      '2026-02-28',
      '2026-03-01',
      '2026-03-02',
    ]);
  });

  it('a null anchor still gives []', () => {
    expect(computeDayBuckets(['2026-08-07'], null, 4)).toEqual([]);
  });

  it('a malformed anchor still gives []', () => {
    expect(computeDayBuckets(['2026-08-07'], 'not-a-date', 4)).toEqual([]);
  });

  it('malformed entries in dates never become the coverage start', () => {
    const buckets = computeDayBuckets(['bad', '', '2026-08-07'], '2026-08-07', 5);
    // Only '2026-08-07' is a valid date, so the coverage start clips to it,
    // even though 'bad' and '' sort before it lexically.
    expect(buckets).toHaveLength(1);
    expect(buckets[0].date).toBe('2026-08-07');
  });

  // --- R-01: declared coverage gaps ---------------------------------------

  it('flags every day 2026-09-05..2026-09-22 as a gap when there are no incidents there', () => {
    const dates: string[] = [];
    for (let ms = Date.parse('2026-08-24T00:00:00Z'); ms <= Date.parse('2026-09-04T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    for (let ms = Date.parse('2026-09-23T00:00:00Z'); ms <= Date.parse('2026-09-25T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    const buckets = computeDayBuckets(dates, '2026-09-25');
    for (const b of buckets) {
      const inGapRange = b.date >= '2026-09-05' && b.date <= '2026-09-22';
      expect(b.gap).toBe(inGapRange);
    }
  });

  it('a real incident inside the declared gap range self-disables the flag for that day only', () => {
    const dates: string[] = [];
    for (let ms = Date.parse('2026-08-24T00:00:00Z'); ms <= Date.parse('2026-09-04T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    for (let ms = Date.parse('2026-09-23T00:00:00Z'); ms <= Date.parse('2026-09-25T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    dates.push('2026-09-10');
    const buckets = computeDayBuckets(dates, '2026-09-25');
    const day0910 = buckets.find((b) => b.date === '2026-09-10');
    expect(day0910?.count).toBe(1);
    expect(day0910?.gap).toBe(false);

    const otherGapDay = buckets.find((b) => b.date === '2026-09-06');
    expect(otherGapDay?.gap).toBe(true);
  });

  it('an empty gaps argument matches the old behaviour (gap always false)', () => {
    const dates: string[] = [];
    for (let ms = Date.parse('2026-08-24T00:00:00Z'); ms <= Date.parse('2026-09-04T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    for (let ms = Date.parse('2026-09-23T00:00:00Z'); ms <= Date.parse('2026-09-25T00:00:00Z'); ms += 86400000) {
      dates.push(new Date(ms).toISOString().slice(0, 10));
    }
    const buckets = computeDayBuckets(dates, '2026-09-25', DAY_WINDOW_WIDTH, []);
    expect(buckets.every((b) => b.gap === false)).toBe(true);
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
