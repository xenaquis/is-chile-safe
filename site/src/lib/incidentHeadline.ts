// RED stub — Task 1 (36-03). Implementation follows in the GREEN commit.
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

export function headlineFor(_incident: HeadlineInput, _locale: 'en' | 'es'): HeadlineResult {
  throw new Error('not implemented');
}

export const HEADLINE_LABELS: Record<'en' | 'es', Partial<Record<HeadlineKind, string>>> = {
  en: {},
  es: {},
};

export function headlineLabel(_kind: HeadlineKind, _locale: 'en' | 'es'): string | null {
  throw new Error('not implemented');
}
