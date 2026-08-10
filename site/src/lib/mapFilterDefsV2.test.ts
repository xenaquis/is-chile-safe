/**
 * mapFilterDefsV2.test.ts — vitest spec for the MAPV2 LAYER_DEFS additions.
 * Companion to mapFilterDefs.test.ts (which keeps guarding CHIP_DEFS verbatim).
 */
import { describe, it, expect } from 'vitest';
import { CHIP_DEFS, LAYER_DEFS, activeLayerId } from './mapFilterDefs';

describe('mapFilterDefs — LAYER_DEFS (MAPV2)', () => {
  it('has ci + total + every non-null CHIP_DEFS key, in order', () => {
    expect(LAYER_DEFS.map((l) => l.id)).toEqual([
      'ci',
      'total',
      ...CHIP_DEFS.filter((c) => c.key !== null).map((c) => c.key as string),
    ]);
  });

  it('only ci is composite; every other layer is family mode', () => {
    expect(LAYER_DEFS.filter((l) => l.mode === 'composite').map((l) => l.id)).toEqual(['ci']);
  });

  it('key/familyIndex pairs are lifted verbatim from CHIP_DEFS', () => {
    for (const l of LAYER_DEFS.slice(2)) {
      const chip = CHIP_DEFS.find((c) => c.key === l.id);
      expect(chip).toBeDefined();
      expect(l.key).toBe(chip!.key);
      expect(l.familyIndex).toBe(chip!.familyIndex);
    }
  });

  it('activeLayerId maps every (mode, crimeFamily) state back to one layer', () => {
    expect(activeLayerId('composite', null)).toBe('ci');
    expect(activeLayerId('composite', 'vida')).toBe('ci'); // composite wins
    expect(activeLayerId('family', null)).toBe('total');
    expect(activeLayerId('family', 'homicidios')).toBe('homicidios');
    expect(activeLayerId('family', 'propiedad')).toBe('propiedad');
  });
});
