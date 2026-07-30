/**
 * mapFilterDefs.test.ts — vitest spec for mapFilterDefs.ts (Phase 30 Wave 1).
 * Guards the highest-damage silent regression in the phase (premortem §6):
 * CHIP_DEFS losing an entry, or the homicide entry being keyed on familyIndex
 * instead of key.
 */
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { CHIP_DEFS, AVAILABLE_YEARS } from './mapFilterDefs';

describe('mapFilterDefs', () => {
  it('Test 5: CHIP_DEFS matches exact key/familyIndex order (9 entries)', () => {
    expect(CHIP_DEFS.map((c) => [c.key, c.familyIndex])).toEqual([
      [null, null],
      ['vida', 0],
      ['propiedad', 5],
      ['robos_violentos', 1],
      ['incivilidades', 6],
      ['vif', 2],
      ['drogas', 3],
      ['armas', 4],
      ['homicidios', null],
    ]);
  });

  it('Test 6: only "todos" and "homicidios" have familyIndex === null', () => {
    expect(CHIP_DEFS.filter((c) => c.familyIndex === null).map((c) => c.key)).toEqual([
      null,
      'homicidios',
    ]);
  });

  it('Test 7: non-null familyIndex matches real catalog.json family_keys order', () => {
    const catalogPath = path.resolve(__dirname, '../../../data/cead/meta/catalog.json');
    const catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
    const familyKeys: string[] = catalog.family_keys;

    for (const c of CHIP_DEFS) {
      if (c.familyIndex !== null && c.key !== 'homicidios') {
        expect(familyKeys[c.familyIndex]).toBe(c.key);
      }
    }
  });

  it('Test 8: AVAILABLE_YEARS spans current year down to 2005', () => {
    expect(AVAILABLE_YEARS[0]).toBe(new Date().getFullYear());
    expect(AVAILABLE_YEARS[AVAILABLE_YEARS.length - 1]).toBe(2005);
  });
});
