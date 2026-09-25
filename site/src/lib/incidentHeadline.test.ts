import { describe, it, expect } from 'vitest';
import { headlineFor, headlineLabel, HEADLINE_LABELS } from './incidentHeadline';

describe('headlineFor', () => {
  it('es + title_src -> verbatim, no label', () => {
    const incident = { title_src: 'Detienen a yerno de X', title_es: 'X detenido por delito', title_en: 'X detained' };
    const result = headlineFor(incident, 'es');
    expect(result).toEqual({ text: 'Detienen a yerno de X', kind: 'verbatim' });
    expect(headlineLabel(result.kind, 'es')).toBeNull();
  });

  it('es + no title_src -> legacy_generated, labelled', () => {
    const incident = { title_es: 'Titular generado por el clasificador', title_en: 'Classifier-generated headline' };
    const result = headlineFor(incident, 'es');
    expect(result).toEqual({ text: 'Titular generado por el clasificador', kind: 'legacy_generated' });
    expect(headlineLabel(result.kind, 'es')).toBe('Titular generado automáticamente');
  });

  it('en + title_src + title_en different -> machine_translated, labelled', () => {
    const incident = { title_src: 'Detienen a yerno de X', title_es: 'Detienen a yerno de X', title_en: 'Son-in-law of X arrested' };
    const result = headlineFor(incident, 'en');
    expect(result).toEqual({ text: 'Son-in-law of X arrested', kind: 'machine_translated' });
    expect(headlineLabel(result.kind, 'en')).toBe('Machine-translated headline');
  });

  it('en + title_en === title_src (kinship guard fallback) -> original_spanish, labelled', () => {
    const incident = { title_src: 'Detienen a yerno de X', title_es: 'Detienen a yerno de X', title_en: 'Detienen a yerno de X' };
    const result = headlineFor(incident, 'en');
    expect(result).toEqual({ text: 'Detienen a yerno de X', kind: 'original_spanish' });
    expect(headlineLabel(result.kind, 'en')).toBe('Original Spanish headline (not translated)');
  });

  it('en + legacy row (no title_src) -> legacy_generated, labelled "Automatically generated headline" (G-36)', () => {
    const incident = { title_es: 'Titular generado por el clasificador', title_en: 'Classifier-generated headline' };
    const result = headlineFor(incident, 'en');
    expect(result).toEqual({ text: 'Classifier-generated headline', kind: 'legacy_generated' });
    expect(headlineLabel(result.kind, 'en')).toBe('Automatically generated headline');
  });

  it('whitespace-only title_src counts as absent', () => {
    const incident = { title_src: '   ', title_es: 'Titular ES', title_en: 'EN title' };
    const es = headlineFor(incident, 'es');
    expect(es).toEqual({ text: 'Titular ES', kind: 'legacy_generated' });
    const en = headlineFor(incident, 'en');
    expect(en).toEqual({ text: 'EN title', kind: 'legacy_generated' });
  });

  it('empty title_en falls back to title_src, then title_es', () => {
    const withSrc = { title_src: 'Titular fuente', title_es: 'Titular fuente', title_en: '' };
    expect(headlineFor(withSrc, 'en')).toEqual({ text: 'Titular fuente', kind: 'machine_translated' });

    const noSrc = { title_es: 'Titular ES fallback', title_en: '' };
    expect(headlineFor(noSrc, 'en')).toEqual({ text: 'Titular ES fallback', kind: 'legacy_generated' });
  });

  it('HEADLINE_LABELS has both locales for every kind except verbatim', () => {
    expect(HEADLINE_LABELS.es.machine_translated).toBe('Titular traducido automáticamente');
    expect(HEADLINE_LABELS.es.original_spanish).toBe('Titular original en español');
    expect(HEADLINE_LABELS.en.legacy_generated).toBe('Automatically generated headline');
    expect(HEADLINE_LABELS.es.verbatim).toBeUndefined();
    expect(HEADLINE_LABELS.en.verbatim).toBeUndefined();
  });
});
