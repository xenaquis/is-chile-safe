// cead-vintage.test.ts — mutation/behavior tests for the FRESH-05 pure checker (35-05).
//
// Imports only from the side-effect-free `cead-vintage.lib.mjs` module: cead-vintage.mjs
// itself performs file IO and process.exit at module-load time, so it is never imported
// here (figure-registry.test.ts precedent).

import { describe, it, expect } from 'vitest';
import {
  expectedFromJson,
  formatDate,
  checkCeadVintagePage,
  findBannedPartialLabels,
} from './cead-vintage.lib.mjs';

const EN_EXPECTED = { lastUpdated: '2026-06-16', partialYear: 2026, latestCompleteYear: 2025 };
const ES_EXPECTED = EN_EXPECTED;

function enNode({
  lastUpdated = '2026-06-16',
  partialYear = '2026',
  latestComplete = '2025',
  text = 'CEAD data as of June 16, 2026 (date of our last download from CEAD) 2026 is a partial year: its figures include only what CEAD had published by June 16, 2026. It is not used for the headline rate or rankings, and appears as a faded point in the trend charts. The latest complete year is 2025.',
} = {}) {
  return `<p class="cead-vintage" data-cead-last-updated="${lastUpdated}" data-partial-year="${partialYear}" data-latest-complete-year="${latestComplete}"><time datetime="${lastUpdated}">${text}</time></p>`;
}

function esNode({
  lastUpdated = '2026-06-16',
  partialYear = '2026',
  latestComplete = '2025',
  text = 'Datos CEAD al 16 de junio de 2026 (fecha de nuestra última descarga desde el CEAD) 2026 es un año parcial: sus cifras incluyen solo lo que el CEAD había publicado al 16 de junio de 2026. No se usa para la tasa principal ni los rankings, y aparece como un punto atenuado en los gráficos de evolución. El último año completo es 2025.',
} = {}) {
  return `<p class="cead-vintage" data-cead-last-updated="${lastUpdated}" data-partial-year="${partialYear}" data-latest-complete-year="${latestComplete}"><time datetime="${lastUpdated}">${text}</time></p>`;
}

describe('expectedFromJson', () => {
  it('derives lastUpdated, partialYear, latestCompleteYear from a series', () => {
    const json = {
      last_updated: '2026-06-16',
      series: [
        { year: 2024, partial: false },
        { year: 2025, partial: false },
        { year: 2026, partial: true },
      ],
    };
    expect(expectedFromJson(json)).toEqual({ lastUpdated: '2026-06-16', partialYear: 2026, latestCompleteYear: 2025 });
  });

  it('returns null lastUpdated for a malformed date', () => {
    expect(expectedFromJson({ last_updated: 'not-a-date', series: [] }).lastUpdated).toBeNull();
  });

  it('returns null partialYear when no year is partial', () => {
    const json = { last_updated: '2026-06-16', series: [{ year: 2024, partial: false }, { year: 2025, partial: false }] };
    expect(expectedFromJson(json).partialYear).toBeNull();
    expect(expectedFromJson(json).latestCompleteYear).toBe(2025);
  });
});

describe('formatDate', () => {
  it('formats long-month EN under UTC', () => {
    expect(formatDate('2026-06-16', 'en')).toBe('June 16, 2026');
  });
  it('formats long-month ES under UTC', () => {
    expect(formatDate('2026-06-16', 'es')).toBe('16 de junio de 2026');
  });
});

describe('checkCeadVintagePage', () => {
  it('a good EN page gives []', () => {
    expect(checkCeadVintagePage(enNode(), EN_EXPECTED, 'en')).toEqual([]);
  });

  it('a good ES page gives []', () => {
    expect(checkCeadVintagePage(esNode(), ES_EXPECTED, 'es')).toEqual([]);
  });

  it('a missing node gives an error containing "no .cead-vintage"', () => {
    const errors = checkCeadVintagePage('<html><body>nothing here</body></html>', EN_EXPECTED, 'en');
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.some((e) => e.includes('no .cead-vintage'))).toBe(true);
  });

  it('two nodes gives "expected exactly 1"', () => {
    const html = enNode() + enNode();
    const errors = checkCeadVintagePage(html, EN_EXPECTED, 'en');
    expect(errors.some((e) => e.includes('expected exactly 1'))).toBe(true);
  });

  it('a wrong data-cead-last-updated names both values', () => {
    const html = enNode({ lastUpdated: '2026-03-01' });
    const errors = checkCeadVintagePage(html, EN_EXPECTED, 'en');
    expect(errors.some((e) => e.includes('2026-03-01') && e.includes('2026-06-16'))).toBe(true);
  });

  it('expected partial year missing its label is an error', () => {
    const html = enNode({
      text: 'CEAD data as of June 16, 2026 (date of our last download from CEAD)',
    });
    const errors = checkCeadVintagePage(html, EN_EXPECTED, 'en');
    expect(errors.some((e) => e.toLowerCase().includes('partial-year label'))).toBe(true);
  });

  it('expected partialYear null with data-partial-year "" and no label gives []', () => {
    const expected = { lastUpdated: '2026-06-16', partialYear: null, latestCompleteYear: 2025 };
    const html = enNode({
      partialYear: '',
      text: 'CEAD data as of June 16, 2026 (date of our last download from CEAD)',
    });
    expect(checkCeadVintagePage(html, expected, 'en')).toEqual([]);
  });

  it('a wrong-locale visible date format (EN text on an ES page) is an error', () => {
    const html = esNode({
      text: 'CEAD data as of June 16, 2026 2026 es un año parcial: ... El último año completo es 2025.',
    });
    const errors = checkCeadVintagePage(html, ES_EXPECTED, 'es');
    expect(errors.length).toBeGreaterThan(0);
  });

  it('methodology mode: "(currently 2024)" when expected 2025 is an error', () => {
    const html = `<html><body>displayed (currently 2024)${enNode()}</body></html>`;
    const errors = checkCeadVintagePage(html, EN_EXPECTED, 'en', { methodology: true });
    expect(errors.some((e) => e.includes('(currently 2025)'))).toBe(true);
  });

  it('methodology mode: "(actualmente 2025)" on ES gives []', () => {
    const html = `<html><body>pasado (actualmente 2025)${esNode()}</body></html>`;
    expect(checkCeadVintagePage(html, ES_EXPECTED, 'es', { methodology: true })).toEqual([]);
  });

  it('R-05: a node whose text contains "or trends" (EN) is an error', () => {
    const html = enNode({
      text: 'CEAD data as of June 16, 2026 2026 is a partial year: it is excluded from rates or trends. The latest complete year is 2025.',
    });
    const errors = checkCeadVintagePage(html, EN_EXPECTED, 'en');
    expect(errors.some((e) => e.includes('R-05'))).toBe(true);
  });

  it('R-05: a node whose text contains "ni las tendencias" (ES) is an error', () => {
    const html = esNode({
      text: 'Datos CEAD al 16 de junio de 2026 2026 es un año parcial: no se usa ni las tendencias. El último año completo es 2025.',
    });
    const errors = checkCeadVintagePage(html, ES_EXPECTED, 'es');
    expect(errors.some((e) => e.includes('R-05'))).toBe(true);
  });
});

describe('findBannedPartialLabels', () => {
  it('finds "Jan–Jun"', () => {
    expect(findBannedPartialLabels('* 2025: partial year data (Jan–Jun)')).toEqual(['Jan–Jun']);
  });
  it('finds "ene–jun"', () => {
    expect(findBannedPartialLabels('año parcial (ene–jun)')).toEqual(['ene–jun']);
  });
  it('finds "(partial data)"', () => {
    expect(findBannedPartialLabels('<p>(partial data)</p>')).toEqual(['(partial data)']);
  });
  it('finds "(datos parciales)"', () => {
    expect(findBannedPartialLabels('<p>(datos parciales)</p>')).toEqual(['(datos parciales)']);
  });
  it('clean HTML returns []', () => {
    expect(findBannedPartialLabels('<p>CEAD data as of June 16, 2026</p>')).toEqual([]);
  });
});
