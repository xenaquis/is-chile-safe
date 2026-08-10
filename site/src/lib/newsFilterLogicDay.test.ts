/**
 * Additive coverage for the `day` dimension introduced by the news UX pass.
 * Kept in its own file so newsFilterLogic.test.ts stays untouched — the
 * pre-existing suite is the regression guard that the day dimension did not
 * change any previously-specified behaviour.
 */
import { describe, it, expect } from 'vitest';
import {
  parseFilterParams,
  serializeFilterParams,
  cardMatchesFilters,
  computeFacetCounts,
  type FilterParams,
  type CardFilterState,
} from './newsFilterLogic';

const EMPTY: FilterParams = { family: [], region: [], window: '', q: '' };
const ANCHOR = '2026-08-07';

const card = (over: Partial<CardFilterState> = {}): CardFilterState => ({
  family: 'vida',
  regionId: '13',
  date: ANCHOR,
  communeNorm: 'santiago',
  ...over,
});

describe('parseFilterParams — day', () => {
  it('reads a well-formed day', () => {
    expect(parseFilterParams('?day=2026-08-05').day).toBe('2026-08-05');
  });

  it('defaults to empty when absent', () => {
    expect(parseFilterParams('').day).toBeFalsy();
  });

  it('degrades a malformed day to empty rather than throwing', () => {
    expect(parseFilterParams('?day=yesterday').day).toBeFalsy();
    expect(parseFilterParams('?day=2026-8-5').day).toBeFalsy();
    expect(parseFilterParams('?day=' + '9'.repeat(500)).day).toBeFalsy();
  });

  it('leaves the pre-existing dimensions untouched', () => {
    const p = parseFilterParams('?family=vida&region=13&window=7d&q=santiago&day=2026-08-05');
    expect(p.family).toEqual(['vida']);
    expect(p.region).toEqual(['13']);
    expect(p.window).toBe('7d');
    expect(p.q).toBe('santiago');
  });
});

describe('serializeFilterParams — day', () => {
  it('omits an empty day', () => {
    expect(serializeFilterParams(EMPTY)).toBe('');
  });

  it('round-trips a day', () => {
    const p: FilterParams = { ...EMPTY, day: '2026-08-05' };
    expect(parseFilterParams(serializeFilterParams(p)).day).toBe('2026-08-05');
  });
});

describe('cardMatchesFilters — day', () => {
  it('matches only the exact date', () => {
    const active: FilterParams = { ...EMPTY, day: ANCHOR };
    expect(cardMatchesFilters(card(), active, ANCHOR)).toBe(true);
    expect(cardMatchesFilters(card({ date: '2026-08-06' }), active, ANCHOR)).toBe(false);
  });

  it('is inert when day is empty', () => {
    expect(cardMatchesFilters(card({ date: '2026-01-01' }), EMPTY, ANCHOR)).toBe(true);
  });

  it('self-excludes when counting the day dimension', () => {
    const active: FilterParams = { ...EMPTY, day: ANCHOR };
    expect(cardMatchesFilters(card({ date: '2026-08-06' }), active, ANCHOR, 'day')).toBe(true);
  });

  it('still applies the other dimensions while day is excluded', () => {
    const active: FilterParams = { ...EMPTY, day: ANCHOR, family: ['drogas'] };
    expect(cardMatchesFilters(card({ date: '2026-08-06' }), active, ANCHOR, 'day')).toBe(false);
  });

  it('applies the cross-cutting comuna query even when day is excluded', () => {
    const active: FilterParams = { ...EMPTY, day: ANCHOR, q: 'valpo' };
    expect(cardMatchesFilters(card({ date: '2026-08-06' }), active, ANCHOR, 'day')).toBe(false);
  });
});

describe('computeFacetCounts — day', () => {
  it('counts per date with self-exclusion, so every bar stays reachable', () => {
    const cards = [
      card({ date: '2026-08-05' }),
      card({ date: '2026-08-06' }),
      card({ date: '2026-08-06' }),
    ];
    const active: FilterParams = { ...EMPTY, day: '2026-08-05' };
    const counts = computeFacetCounts(cards, active, ANCHOR, 'day', [
      '2026-08-05',
      '2026-08-06',
      '2026-08-07',
    ]);
    expect(counts).toEqual({ '2026-08-05': 1, '2026-08-06': 2, '2026-08-07': 0 });
  });

  it('narrows the bars by the other active dimensions', () => {
    const cards = [
      card({ date: '2026-08-05', family: 'vida' }),
      card({ date: '2026-08-06', family: 'drogas' }),
    ];
    const active: FilterParams = { ...EMPTY, family: ['vida'] };
    const counts = computeFacetCounts(cards, active, ANCHOR, 'day', ['2026-08-05', '2026-08-06']);
    expect(counts).toEqual({ '2026-08-05': 1, '2026-08-06': 0 });
  });
});
