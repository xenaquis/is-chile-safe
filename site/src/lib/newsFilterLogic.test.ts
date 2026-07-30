/**
 * newsFilterLogic.test.ts — vitest spec for newsFilterLogic.ts (Phase 28
 * Wave 0, Task 1). Pure-function module, no filesystem fixtures needed.
 */
import { describe, it, expect } from 'vitest';
import {
  norm,
  parseFilterParams,
  serializeFilterParams,
  computeNewestDate,
  matchesWindow,
  cardMatchesFilters,
  computeFacetCounts,
  FILTER_LOGIC_MARKER,
  WINDOW_7D_WIDTH_DAYS,
  WINDOW_30D_WIDTH_DAYS,
  type CardFilterState,
  type FilterParams,
} from './newsFilterLogic';

function makeCards(): CardFilterState[] {
  return [
    { family: 'robos_violentos', regionId: '13', date: '2026-07-28', communeNorm: 'santiago' },
    { family: 'robos_violentos', regionId: '13', date: '2026-07-20', communeNorm: 'providencia' },
    { family: 'drogas', regionId: '13', date: '2026-07-15', communeNorm: 'santiago' },
    { family: 'drogas', regionId: '8', date: '2026-07-10', communeNorm: 'concepcion' },
    { family: 'robos_violentos', regionId: '8', date: '2026-06-01', communeNorm: 'lota' },
    { family: 'vif', regionId: '8', date: '2026-05-01', communeNorm: 'concepcion' },
  ];
}

describe('newsFilterLogic', () => {
  it('Test 1: norm() is accent-insensitive and lowercases', () => {
    expect(norm('Viña del Mar')).toBe(norm('Vina del Mar'));
    expect(norm('Viña del Mar')).toBe('vina del mar');
  });

  it('Test 2: parseFilterParams parses comma-separated family/region, window, q', () => {
    const result = parseFilterParams('?family=robos,drogas&region=13&window=7d&q=puerto');
    expect(result).toEqual({ family: ['robos', 'drogas'], region: ['13'], window: '7d', q: 'puerto' });
  });

  it('Test 3: parseFilterParams degrades an invalid window value to "" (never throws)', () => {
    expect(() => parseFilterParams('?window=bogus')).not.toThrow();
    const result = parseFilterParams('?window=bogus');
    expect(result.window).toBe('');
  });

  it('Test 4: parseFilterParams("") returns all-empty FilterParams, no throw', () => {
    expect(() => parseFilterParams('')).not.toThrow();
    expect(parseFilterParams('')).toEqual({ family: [], region: [], window: '', q: '' });
  });

  it('Test 5: serializeFilterParams(parseFilterParams(search)) round-trips for 3 distinct inputs', () => {
    const inputs = [
      '?family=robos,drogas&region=13&window=7d&q=puerto',
      '?region=13,8&window=30d',
      '?q=vina',
    ];
    for (const search of inputs) {
      const parsed = parseFilterParams(search);
      const serialized = serializeFilterParams(parsed);
      const reparsed = parseFilterParams(serialized);
      expect(reparsed).toEqual(parsed);
    }
  });

  it('Test 6: computeNewestDate returns null for empty array, max date otherwise', () => {
    expect(computeNewestDate([])).toBeNull();
    expect(computeNewestDate(['2026-07-20', '2026-07-27', '2026-07-15'])).toBe('2026-07-27');
  });

  it('Test 7 (mutation-tested): matchesWindow 7d boundary is inclusive at width-1 days back, exclusive one day further', () => {
    const newestDate = '2026-07-28';
    // WINDOW_7D_WIDTH_DAYS - 1 = 6 days back from anchor = 2026-07-22 (inclusive boundary)
    const boundaryDate = '2026-07-22';
    const oneDayFurther = '2026-07-21';
    expect(matchesWindow(boundaryDate, newestDate, '7d')).toBe(true);
    expect(matchesWindow(oneDayFurther, newestDate, '7d')).toBe(false);
    // Sanity: the constant used for this test is indeed 7 (mutation target).
    expect(WINDOW_7D_WIDTH_DAYS).toBe(7);
  });

  it('Test 8: matchesWindow returns false (never throws) when newestDate is null and window is not ""', () => {
    expect(() => matchesWindow('2026-07-20', null, '7d')).not.toThrow();
    expect(matchesWindow('2026-07-20', null, '7d')).toBe(false);
  });

  it('Test 9 (F-28 self-exclusion): computeFacetCounts for a dimension ignores that dimension\'s own active filter', () => {
    const cards = makeCards();
    const newestDate = computeNewestDate(cards.map((c) => c.date));

    // No filters active — region counts should be simple per-region totals restricted by nothing.
    const activeNone: FilterParams = { family: ['robos_violentos'], region: [], window: '', q: '' };
    const regionCountsNoRegionFilter = computeFacetCounts(cards, activeNone, newestDate, 'region', ['13', '8']);
    // family filter IS applied (excludeDimension is 'region', not 'family'):
    // robos_violentos cards: region 13 (x2), region 8 (x1)
    expect(regionCountsNoRegionFilter).toEqual({ '13': 2, '8': 1 });

    // Now activate a region filter too, and confirm the 'region' dimension's own
    // count ignores its own active filter (self-exclusion), while the 'family'
    // dimension's count still applies the active region filter.
    const activeWithRegion: FilterParams = { family: ['robos_violentos'], region: ['13'], window: '', q: '' };
    const regionCountsSelfExcluded = computeFacetCounts(cards, activeWithRegion, newestDate, 'region', ['13', '8']);
    // Self-exclusion: region filter not applied when computing region counts ->
    // same result as without the region filter active.
    expect(regionCountsSelfExcluded).toEqual({ '13': 2, '8': 1 });

    const familyCountsRegionApplied = computeFacetCounts(cards, activeWithRegion, newestDate, 'family', [
      'robos_violentos',
      'drogas',
      'vif',
    ]);
    // family dimension DOES apply the active region filter (region=13):
    // region 13 cards: robos_violentos x2, drogas x1, vif x0
    expect(familyCountsRegionApplied).toEqual({ robos_violentos: 2, drogas: 1, vif: 0 });
  });

  it('Test 10: cardMatchesFilters returns false for an unresolved regionId against an active region filter', () => {
    const card: CardFilterState = { family: 'robos_violentos', regionId: '', date: '2026-07-20', communeNorm: 'santiago' };
    const active: FilterParams = { family: [], region: ['13'], window: '', q: '' };
    expect(cardMatchesFilters(card, active, '2026-07-28')).toBe(false);
  });

  it('Test 11: FILTER_LOGIC_MARKER is the exact string-literal contract', () => {
    expect(FILTER_LOGIC_MARKER).toBe('newsFilterLogic/v1');
  });

  it('Test 12 (WR-01 regression): serializeFilterParams with an all-empty filter state returns an empty string', () => {
    const empty: FilterParams = { family: [], region: [], window: '', q: '' };
    expect(serializeFilterParams(empty)).toBe('');
  });

  it('Test 13 (WR-03, mutation-tested): matchesWindow 30d boundary is inclusive at width-1 days back, exclusive one day further', () => {
    const newestDate = '2026-07-28';
    // WINDOW_30D_WIDTH_DAYS - 1 = 29 days back from anchor = 2026-06-29 (inclusive boundary)
    const boundaryDate = '2026-06-29';
    const oneDayFurther = '2026-06-28';
    expect(matchesWindow(boundaryDate, newestDate, '30d')).toBe(true);
    expect(matchesWindow(oneDayFurther, newestDate, '30d')).toBe(false);
    // Sanity: the constant used for this test is indeed 30 (mutation target).
    expect(WINDOW_30D_WIDTH_DAYS).toBe(30);
  });

  it('Test 14 (WR-03, mutation-tested): matchesWindow "today" matches only the anchor date exactly', () => {
    expect(matchesWindow('2026-07-28', '2026-07-28', 'today')).toBe(true);
    expect(matchesWindow('2026-07-27', '2026-07-28', 'today')).toBe(false);
    expect(matchesWindow('2026-07-29', '2026-07-28', 'today')).toBe(false);
  });

  it('Test 16 (WR-06, mutation-tested): norm() trims leading/trailing whitespace so a comuna query with stray spaces matches the same set as the trimmed query', () => {
    expect(norm('  santiago  ')).toBe(norm('santiago'));
    expect(norm('santiago ')).toBe('santiago');
    expect(norm(' Viña del Mar')).toBe(norm('Vina del Mar'));
  });

  it('Test 15 (WR-03): computeFacetCounts window dimension uses matchesWindow per key', () => {
    const cards = makeCards();
    const newestDate = computeNewestDate(cards.map((c) => c.date));
    const active: FilterParams = { family: [], region: [], window: '', q: '' };
    // makeCards() dates: 2026-07-28 (today), 07-20, 07-15, 07-10, 2026-06-01, 2026-05-01
    // newestDate = 2026-07-28
    // today: only 07-28 -> 1
    // 7d (anchor-6 = 07-22): only 07-28 -> 1
    // 30d (anchor-29 = 06-29): 07-28, 07-20, 07-15, 07-10 -> 4
    const counts = computeFacetCounts(cards, active, newestDate, 'window', ['today', '7d', '30d']);
    expect(counts).toEqual({ today: 1, '7d': 1, '30d': 4 });
  });
});
