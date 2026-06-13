/**
 * Central slug-pair maps for hreflang EN/ES URL pairs.
 * Used by all page routes to compute canonical + alternate URLs.
 * No per-page frontmatter hreflang — computed from meta/index.json at build time (D-18).
 */
import { loadIndex, loadRegion } from './data.ts';
import { FAMILY_SLUGS, type FamilySlugPair } from '../config/i18n.ts';

export type SlugPair = { en: string; es: string };

const BASE_URL = 'https://ischilesafe.com';

/**
 * Build a map from CUT code to { en: /commune/{slug}/, es: /es/comuna/{slug}/ }
 */
export function buildCommuneSlugPairMap(): Record<string, SlugPair> {
  const index = loadIndex();
  return Object.fromEntries(
    index.map((c) => [
      c.cut,
      {
        en: `/commune/${c.slug}/`,
        es: `/es/comuna/${c.slug}/`,
      },
    ])
  );
}

/**
 * Build a map from region_id to { en: /region/{slug}/, es: /es/region/{slug}/ }
 * Requires all unique region_id values from meta/index.json.
 * Region slugs are read from region JSON files.
 */
export function buildRegionSlugPairMap(): Record<string, SlugPair> {
  const index = loadIndex();
  const regionIds = [...new Set(index.map((c) => c.region_id))];
  // Each region has its own slug in regions/{id}.json
  return Object.fromEntries(
    regionIds.map((rid) => {
      const region = loadRegion(rid);
      return [
        rid,
        {
          en: `/region/${region.slug}/`,
          es: `/es/region/${region.slug}/`,
        },
      ];
    })
  );
}

/**
 * Build a map from family key to { en: /crime/{enSlug}/, es: /es/delito/{esSlug}/ }
 */
export function buildFamilySlugPairMap(): Record<string, SlugPair> {
  return Object.fromEntries(
    Object.entries(FAMILY_SLUGS).map(([key, pair]: [string, FamilySlugPair]) => [
      key,
      {
        en: `/crime/${pair.en}/`,
        es: `/es/delito/${pair.es}/`,
      },
    ])
  );
}

/**
 * Get the URL slug for a family key in a given locale.
 */
export function getFamilySlug(key: string, locale: 'en' | 'es'): string {
  const pair = FAMILY_SLUGS[key];
  if (!pair) throw new Error(`Unknown family key: ${key}`);
  return pair[locale];
}

/**
 * Compute canonical + alternate URL pair for a commune page.
 */
export function communeUrls(
  slug: string,
  locale: 'en' | 'es'
): { canonicalUrl: string; alternateUrl: string } {
  const enPath = `/commune/${slug}/`;
  const esPath = `/es/comuna/${slug}/`;
  return {
    canonicalUrl: `${BASE_URL}${locale === 'en' ? enPath : esPath}`,
    alternateUrl: `${BASE_URL}${locale === 'en' ? esPath : enPath}`,
  };
}

/**
 * Compute canonical + alternate URL pair for a region page.
 */
export function regionUrls(
  slug: string,
  locale: 'en' | 'es'
): { canonicalUrl: string; alternateUrl: string } {
  const enPath = `/region/${slug}/`;
  const esPath = `/es/region/${slug}/`;
  return {
    canonicalUrl: `${BASE_URL}${locale === 'en' ? enPath : esPath}`,
    alternateUrl: `${BASE_URL}${locale === 'en' ? esPath : enPath}`,
  };
}

/**
 * Compute canonical + alternate URL pair for a crime-type page.
 */
export function crimeTypeUrls(
  familyKey: string,
  locale: 'en' | 'es'
): { canonicalUrl: string; alternateUrl: string } {
  const pair = FAMILY_SLUGS[familyKey];
  if (!pair) throw new Error(`Unknown family key: ${familyKey}`);
  const enPath = `/crime/${pair.en}/`;
  const esPath = `/es/delito/${pair.es}/`;
  return {
    canonicalUrl: `${BASE_URL}${locale === 'en' ? enPath : esPath}`,
    alternateUrl: `${BASE_URL}${locale === 'en' ? esPath : enPath}`,
  };
}
