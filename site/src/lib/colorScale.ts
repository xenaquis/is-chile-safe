/**
 * Build-time incidence color scale using chroma-js.
 * This module MUST only be imported in build-time code (Astro pages, getStaticPaths, server-side).
 * Never re-export or import in client-side React islands — chroma-js is a Node-only build dep.
 */
import chroma from 'chroma-js';

// 5-stop incidence color scale matching the prototype palette (UI-SPEC D-21)
// Level 1 (low) → Level 5 (high)
export const INCIDENCE_COLORS: string[] = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);

/**
 * Compute incidence level (1–5) for a given rate by quintile position.
 *
 * NOTE (WR-06): levels are VALUE-THRESHOLD quintiles, not equal-COUNT buckets.
 * The breakpoints are the rate values at the 20/40/60/80th index positions of
 * the sorted rate array, and assignment uses `rate <= q(p)`. When many communes
 * share the same rate (rates are rounded to integers upstream), a single value
 * can span several breakpoints, so adjacent levels may hold unequal counts.
 * This is intentional: the choropleth colors by rate threshold, not by rank.
 * If equal-count quintiles are ever required, assign by index rank (position / n)
 * instead of by value comparison.
 *
 * @param rate - The commune's rate_per_100k
 * @param sortedRates - All non-low-population commune rates, sorted ascending
 * @returns Level 1 (lowest) to 5 (highest)
 */
export function levelForRate(rate: number, sortedRates: number[]): 1 | 2 | 3 | 4 | 5 {
  const n = sortedRates.length;
  if (n === 0) return 3;
  const q = (p: number) => sortedRates[Math.floor(n * p)] ?? sortedRates[n - 1]!;
  if (rate <= q(0.2)) return 1;
  if (rate <= q(0.4)) return 2;
  if (rate <= q(0.6)) return 3;
  if (rate <= q(0.8)) return 4;
  return 5;
}
