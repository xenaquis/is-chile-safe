/**
 * Island-internal incidence color constants.
 * Imported by ChoroplethLayer.ts, LowZoomDotLayer.ts, Legend.tsx, etc.
 *
 * IMPORTANT: Do NOT import colorScale.ts here — that module is Node-only (build-time).
 * chroma-js is imported directly in this client-side module.
 */
import chroma from 'chroma-js';
import type L from 'leaflet';

// 5-stop incidence color scale: level 1 (low) → level 5 (high)
// Matches colorScale.ts exactly — same chroma call, same colors
export const INCIDENCE_COLORS: string[] = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);

/** Default polygon style for communes with no data */
export const DEFAULT_STYLE: L.PathOptions = {
  fillColor: '#cccccc',
  fillOpacity: 0.4,
  color: '#ffffff',
  weight: 1.2,
};

/**
 * Compute quantile break thresholds from a sorted (ascending) array of rates.
 * Returns (classes - 1) threshold values.
 *
 * @param sorted - Rate values sorted ascending (already filtered, e.g. no zeros)
 * @param classes - Number of quantile classes (default 5)
 */
export function computeQuantileBreaks(sorted: number[], classes = 5): number[] {
  const s = [...sorted].sort((a, b) => a - b);
  return Array.from({ length: classes - 1 }, (_, i) =>
    s[Math.floor((s.length * (i + 1)) / classes)] ?? 0
  );
}

/**
 * Map a rate to a level (1–5) given pre-computed quantile break thresholds.
 *
 * @param rate - Commune rate to classify
 * @param breaks - Array of (classes - 1) threshold values from computeQuantileBreaks
 */
export function levelFromBreaks(rate: number, breaks: number[]): 1 | 2 | 3 | 4 | 5 {
  if (rate <= (breaks[0] ?? Infinity)) return 1;
  if (rate <= (breaks[1] ?? Infinity)) return 2;
  if (rate <= (breaks[2] ?? Infinity)) return 3;
  if (rate <= (breaks[3] ?? Infinity)) return 4;
  return 5;
}
