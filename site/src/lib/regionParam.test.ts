/**
 * regionParam.test.ts — vitest spec for regionParam.ts (Phase 30 Wave 1).
 * Pure-function module, no DOM/fetch needed.
 */
import { describe, it, expect } from 'vitest';
import { resolveRegionFocus } from './regionParam';
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
});
