/**
 * regionParam.test.ts — vitest spec for regionParam.ts (Phase 30 Wave 1).
 * Pure-function module, no DOM/fetch needed.
 */
import { describe, it, expect } from 'vitest';
import { resolveRegionFocus, shouldApplyRegionFocus } from './regionParam';
import type { CommuneIndexEntry } from '../components/map/SearchBox';

function makeIdx(): CommuneIndexEntry[] {
  return [
    { cut: '13101', name: 'Santiago', slug: 'santiago', region_id: '13' },
    { cut: '13102', name: 'Cerrillos', slug: 'cerrillos', region_id: '13' },
    { cut: '8101', name: 'Concepcion', slug: 'concepcion', region_id: '8' },
  ];
}

describe('resolveRegionFocus', () => {
  it('Test 1: ?region=13 returns every matching CUT', () => {
    const result = resolveRegionFocus('?region=13', makeIdx());
    expect(result).not.toBeNull();
    expect(result!.sort()).toEqual(['13101', '13102']);
  });

  it('Test 2: ?region=99 (no matching region_id) returns null', () => {
    const result = resolveRegionFocus('?region=99', makeIdx());
    expect(result).toBeNull();
  });

  it('Test 3: no ?region= param at all returns null', () => {
    const result = resolveRegionFocus('', makeIdx());
    expect(result).toBeNull();
  });

  it('Test 4: ?region=13&cut=13101 still resolves region and ignores cut', () => {
    const result = resolveRegionFocus('?region=13&cut=13101', makeIdx());
    expect(result).not.toBeNull();
    expect(result!.sort()).toEqual(['13101', '13102']);
  });

  // M-07: padded region_id forms must resolve the same as the unpadded form.
  it('Test 5: ?region=08 resolves the same CUTs as ?region=8', () => {
    const padded = resolveRegionFocus('?region=08', makeIdx());
    const unpadded = resolveRegionFocus('?region=8', makeIdx());
    expect(padded).toEqual(unpadded);
    expect(padded).toEqual(['8101']);
  });

  it('Test 6: ?region=13 with a trailing space resolves', () => {
    const result = resolveRegionFocus('?region=13%20', makeIdx());
    expect(result).not.toBeNull();
    expect(result!.sort()).toEqual(['13101', '13102']);
  });

  it('Test 7: an unknown padded value still returns null', () => {
    const result = resolveRegionFocus('?region=099', makeIdx());
    expect(result).toBeNull();
  });
});

describe('shouldApplyRegionFocus', () => {
  it('Test 8: true when there is no ?cut= param', () => {
    expect(shouldApplyRegionFocus('?region=13')).toBe(true);
  });

  it('Test 9: true when ?cut= is present but not a valid 4-5 digit CUT', () => {
    expect(shouldApplyRegionFocus('?region=13&cut=abc')).toBe(true);
    expect(shouldApplyRegionFocus('?region=13&cut=123')).toBe(true);
  });

  it('Test 10: false when a valid 4-5 digit ?cut= is present', () => {
    expect(shouldApplyRegionFocus('?region=13&cut=13101')).toBe(false);
    expect(shouldApplyRegionFocus('?cut=5101')).toBe(false);
  });
});
