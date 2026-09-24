/**
 * FRESH-05: CEAD vintage disclosure helper.
 *
 * Pure functions, no fs — derives the "as of" download date and the
 * partial-year cutoff from a series + last_updated string. See V-13:
 * scrape_cead.py:67-89 has NO month-level cutoff, only a boolean partial
 * flag on the current calendar year. Callers must not invent a month range.
 */
import type { SeriesEntry } from './data.ts';

export interface CeadVintage {
  lastUpdated: string | null;
  partialYear: number | null;
  latestCompleteYear: number | null;
}

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Derives the vintage triple from a series and the raw last_updated string.
 * lastUpdated is valid iff it matches YYYY-MM-DD and parses to a real date.
 */
export function ceadVintage(
  series: SeriesEntry[],
  lastUpdated?: string | null
): CeadVintage {
  let validLastUpdated: string | null = null;
  if (
    typeof lastUpdated === 'string' &&
    ISO_DATE_RE.test(lastUpdated) &&
    !Number.isNaN(Date.parse(lastUpdated))
  ) {
    validLastUpdated = lastUpdated;
  }

  let partialYear: number | null = null;
  let latestCompleteYear: number | null = null;

  for (const entry of series) {
    if (entry.partial === true) {
      if (partialYear === null || entry.year > partialYear) {
        partialYear = entry.year;
      }
    } else {
      if (latestCompleteYear === null || entry.year > latestCompleteYear) {
        latestCompleteYear = entry.year;
      }
    }
  }

  return {
    lastUpdated: validLastUpdated,
    partialYear,
    latestCompleteYear,
  };
}

/**
 * Formats an ISO YYYY-MM-DD date for display, per locale.
 * Always uses timeZone: 'UTC' — omitting it flips near-midnight dates under
 * non-UTC system timezones (e.g. America/Santiago), per the facets.mjs
 * assertion-11 date-formatting rule.
 */
export function formatCeadDate(iso: string, locale: 'en' | 'es'): string {
  const date = new Date(iso);
  const intlLocale = locale === 'es' ? 'es-CL' : 'en-US';
  return date.toLocaleDateString(intlLocale, {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}
