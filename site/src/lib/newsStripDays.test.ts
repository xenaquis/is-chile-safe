/**
 * newsStripDays.test.ts — behavior fixtures for computeStripDays (R2/F35-R1-06,
 * G-22(b)). See the plan's <behavior> list; each `it` below is one bullet.
 */
import { describe, it, expect } from 'vitest';
import { computeStripDays } from './newsStripDays';
import type { CoverageGap } from './newsCoverageGaps';

const GAPS: CoverageGap[] = [
  { from: '2026-09-05', to: '2026-09-22', source: 'G-18 classifier outage' },
];

function range(fromISO: string, toISO: string): string[] {
  const out: string[] = [];
  for (let d = fromISO; d <= toISO; ) {
    out.push(d);
    const ms = Date.parse(d + 'T00:00:00Z') + 86400000;
    d = new Date(ms).toISOString().slice(0, 10);
  }
  return out;
}

describe('computeStripDays', () => {
  it('gives 12 days, 08-24..09-04, all gap=false, with anchor 2026-09-04 and prod dates 08-24..09-04', () => {
    const dates = range('2026-08-24', '2026-09-04');
    const days = computeStripDays('2026-09-04', 30, dates, GAPS);
    expect(days.map((d) => d.date)).toEqual(range('2026-08-24', '2026-09-04'));
    expect(days.length).toBe(12);
    expect(days.every((d) => d.gap === false)).toBe(true);
  });

  it('gives days 08-26..09-25 (store window = windowDays+1 dates) with anchor 2026-09-25 and the same dates plus 09-23..09-25; 09-05..09-22 are gap=true', () => {
    const dates = [...range('2026-08-24', '2026-09-04'), ...range('2026-09-23', '2026-09-25')];
    const days = computeStripDays('2026-09-25', 30, dates, GAPS);
    expect(days[0]!.date).toBe('2026-08-26');
    expect(days[days.length - 1]!.date).toBe('2026-09-25');
    const gapDates = days.filter((d) => d.gap).map((d) => d.date);
    expect(gapDates).toEqual(range('2026-09-05', '2026-09-22'));
  });

  it('gives gap=false on 09-22 when a real incident is added on that date', () => {
    const dates = [...range('2026-08-24', '2026-09-04'), '2026-09-22', ...range('2026-09-23', '2026-09-25')];
    const days = computeStripDays('2026-09-25', 30, dates, GAPS);
    const day0922 = days.find((d) => d.date === '2026-09-22');
    expect(day0922?.gap).toBe(false);
  });

  it('never lets malformed dates become the start, and anchor "" gives []', () => {
    const dates = ['bad', '', '2026-09-01', '2026-09-02'];
    const days = computeStripDays('2026-09-02', 30, dates, GAPS);
    expect(days[0]!.date).toBe('2026-09-01');
    expect(computeStripDays('', 30, dates, GAPS)).toEqual([]);
  });

  it('gives no gap days when gaps is []', () => {
    const dates = range('2026-08-24', '2026-09-04');
    const days = computeStripDays('2026-09-04', 30, dates, []);
    expect(days.every((d) => d.gap === false)).toBe(true);
  });

  it('decides gap on the UNFILTERED dates — a family filter with no incident on 09-10 while another family has one still gives gap=false', () => {
    // unfilteredDates always includes 09-10 (from another family); the
    // caller passes the full unfiltered set, so 09-10 is never a gap.
    const dates = [...range('2026-08-24', '2026-09-04'), '2026-09-10', ...range('2026-09-23', '2026-09-25')];
    const days = computeStripDays('2026-09-25', 30, dates, GAPS);
    const day0910 = days.find((d) => d.date === '2026-09-10');
    expect(day0910?.gap).toBe(false);
  });
});

describe('computeStripDays — store window parity (review F1)', () => {
  it('keeps the oldest store-window day (anchor - windowDays) when it holds an incident', () => {
    const days = computeStripDays('2026-09-30', 30, ['2026-08-31', '2026-09-30'], []);
    expect(days[0]!.date).toBe('2026-08-31');
    expect(days.length).toBe(31);
  });
});
