/**
 * incidentHeadline.ts — single rule for headline text + disclosure label
 * across all 6 news surfaces (FID-01, G-28/G-36).
 *
 * Policy:
 *  - Spanish surfaces render the outlet's verbatim headline (title_src) when present.
 *  - English surfaces render a machine translation of that headline (title_en) and
 *    carry a disclosure label, UNLESS the 36-04 kinship-guard fallback kicked in
 *    (title_en === title_src — the translation was rejected, so the original
 *    Spanish text is shown instead, labelled as such).
 *  - Legacy rows (no title_src) never had a real outlet headline captured: title_es
 *    is itself an LLM-written headline (classifier.py:176-177). ES gets a "generated"
 *    note; EN's translation of that generated headline is NOT a "machine-translated
 *    headline" — attributing that phrase to the outlet would misrepresent whose words
 *    they are (G-36, premortem R-01). It gets "Automatically generated headline" instead.
 *
 * Neutral copy: no safety verdict, implicit attribution to the outlet where earned.
 */

export type HeadlineKind = 'verbatim' | 'machine_translated' | 'original_spanish' | 'legacy_generated';

export interface HeadlineInput {
  title_src?: string | null;
  title_es: string;
  title_en: string;
}

export interface HeadlineResult {
  text: string;
  kind: HeadlineKind;
}

function hasContent(s: string | null | undefined): s is string {
  return typeof s === 'string' && s.trim().length > 0;
}

/**
 * headlineFor — decide the displayed headline text and its kind for one locale.
 */
export function headlineFor(incident: HeadlineInput, locale: 'en' | 'es'): HeadlineResult {
  const srcPresent = hasContent(incident.title_src);
  const src = srcPresent ? (incident.title_src as string) : '';

  if (locale === 'es') {
    if (srcPresent) {
      return { text: src, kind: 'verbatim' };
    }
    return { text: incident.title_es, kind: 'legacy_generated' };
  }

  // locale === 'en'
  if (!srcPresent) {
    // Legacy row: title_en (or title_es fallback) translates an LLM-written
    // headline, not the outlet's own words.
    const text = hasContent(incident.title_en) ? incident.title_en : incident.title_es;
    return { text, kind: 'legacy_generated' };
  }

  // title_src is present. The 36-04 kinship guard sets title_en === title_src
  // when a translation is rejected for changing a family-relationship term.
  if (incident.title_en === src) {
    return { text: src, kind: 'original_spanish' };
  }

  const text = hasContent(incident.title_en) ? incident.title_en : src;
  return { text, kind: 'machine_translated' };
}

// HEADLINE_LABELS — every kind except 'verbatim' (no disclosure needed: the ES
// text IS the outlet's own headline).
export const HEADLINE_LABELS: Record<'en' | 'es', Partial<Record<HeadlineKind, string>>> = {
  en: {
    machine_translated: 'Machine-translated headline',
    original_spanish: 'Original Spanish headline (not translated)',
    legacy_generated: 'Automatically generated headline',
  },
  es: {
    machine_translated: 'Titular traducido automáticamente',
    original_spanish: 'Titular original en español',
    legacy_generated: 'Titular generado automáticamente',
  },
};

/**
 * headlineLabel — the disclosure label for a given kind/locale, or null when
 * no disclosure is needed (the ES verbatim case).
 */
export function headlineLabel(kind: HeadlineKind, locale: 'en' | 'es'): string | null {
  return HEADLINE_LABELS[locale][kind] ?? null;
}
