/**
 * formatNumber.ts — Locale-aware number formatting helpers.
 *
 * Single source of truth for all rate/number display across the site.
 * No imports — pure Intl.NumberFormat / toLocaleString wrapper.
 *
 * Contract (from 25-02-PLAN.md):
 *   formatRate(4984.1, 'en') === '4,984'
 *   formatRate(4984.1, 'es') === '4.984'
 *   formatDecimal(2871.5, 'en') === '2,871.5'
 *   formatDecimal(8.69, 'es', 1) === '8,7'
 */

const LOCALE_MAP: Record<'en' | 'es', string> = {
  en: 'en-US',
  es: 'es-CL',
};

/**
 * Format a rate value as a rounded integer with locale-correct thousands separator.
 * EN: 4,984   ES: 4.984
 */
export function formatRate(value: number, locale: 'en' | 'es'): string {
  return Math.round(value).toLocaleString(LOCALE_MAP[locale]);
}

/**
 * Format a decimal number with a fixed number of decimal places and locale-correct
 * thousands/decimal separators.
 * EN: 2,871.5   ES: 2.871,5
 * Default decimals = 1.
 */
export function formatDecimal(value: number, locale: 'en' | 'es', decimals = 1): string {
  return value.toLocaleString(LOCALE_MAP[locale], {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
