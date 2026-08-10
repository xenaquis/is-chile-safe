/**
 * bandStats.ts — MAPV2: pure helpers for the interactive legend.
 *
 * computeLayerStats() derives, for the CURRENT layer (mode + family/homicide),
 * a CUT → level index, the quantile breaks, per-band commune counts and the
 * raw value list (for the histogram). It mirrors — never replaces — the
 * classification logic of the ChoroplethLayer builders:
 *   - composite → precomputed c.ci (null → excluded from counts, level 3 fill)
 *   - family    → quantile breaks over positive by_family[i] (same as
 *                 buildStyleMapFromFamily)
 *   - homicide  → quantile breaks over positive hr (same as
 *                 buildStyleMapFromHomicide)
 *   - total     → precomputed c.level (same as buildStyleMapFromLevel), with
 *                 breaks recomputed for display only (matches what Legend
 *                 already showed via computeQuantileBreaks on rates)
 *
 * applyBandDim() mutates a freshly-built style map IN PLACE (before
 * applyStyleMap) so band isolation still respects D-12: setStyle in place,
 * never re-mount.
 */

import type L from 'leaflet';
import { computeQuantileBreaks, levelFromBreaks } from './colors';
import type { CommunaPayload } from './ChoroplethLayer';

export type Level = 1 | 2 | 3 | 4 | 5;

export interface LayerStats {
  /** CUT → level (1–5) under the current layer. */
  levelIdx: Map<string, Level>;
  /** 4 quantile thresholds, or null in composite mode (index has no rate unit). */
  breaks: number[] | null;
  /** Communes per band, index 0 = level 1. */
  counts: number[];
  /** Raw values (per-100k rates), empty in composite mode. */
  values: number[];
  /** Isolated legend band (1–5) or null — mirrors MapIsland's `band` state
   *  so consumers (dot layer) can read it without adding it as a dep. */
  band?: number | null;
  /** Homicide layer only: communes with 0 reported homicides (excluded from
   *  the positive-quantile classification but must still be accounted for
   *  — MPX-A4: zero is not the same thing as "band 1"). */
  zeroCount?: number;
}

export function computeLayerStats(
  comunas: CommunaPayload[],
  mode: 'composite' | 'family',
  familyIndex: number | null,
  isHomicide: boolean
): LayerStats {
  const levelIdx = new Map<string, Level>();
  const counts = [0, 0, 0, 0, 0];

  if (mode === 'composite') {
    // MPX-C5: count EVERY commune, including ci === null — those paint band
    // 3 (see buildStyleMapFromCompositeIndex), so the count must describe
    // what's actually shown, not just the communes with a real index.
    for (const c of comunas) {
      const lv = (c.ci ?? 3) as Level;
      levelIdx.set(c.id, lv);
      counts[lv - 1]++;
    }
    return { levelIdx, breaks: null, counts, values: [] };
  }

  if (isHomicide) {
    const val = (c: CommunaPayload) => c.hr ?? 0;
    const positive = comunas.map(val).filter((r) => r > 0);
    const breaks = computeQuantileBreaks(positive, 5);
    let zeroCount = 0;
    for (const c of comunas) {
      const v = val(c);
      // MPX-A4: classify by breaks for the fill color, but only count
      // communes with v > 0 toward the band counts — a commune with zero
      // reported homicides is not the same thing as "band 1".
      const lv = levelFromBreaks(v, breaks);
      levelIdx.set(c.id, lv);
      if (v > 0) {
        counts[lv - 1]++;
      } else {
        zeroCount++;
      }
    }
    return { levelIdx, breaks, counts, values: comunas.map(val), zeroCount };
  }

  if (familyIndex !== null) {
    const val = (c: CommunaPayload) => c.by_family[familyIndex] ?? 0;
    const positive = comunas.map(val).filter((r) => r > 0);
    const breaks = computeQuantileBreaks(positive, 5);
    for (const c of comunas) {
      const lv = levelFromBreaks(val(c), breaks);
      levelIdx.set(c.id, lv);
      counts[lv - 1]++;
    }
    return { levelIdx, breaks, counts, values: comunas.map(val) };
  }

  // Total rate: levels are the pipeline-precomputed c.level (identical to
  // buildStyleMapFromLevel). MPX-A5: breaks must describe the SAME
  // classification as the color/count — derive them from the actual
  // per-level partition instead of recomputing independent quantiles
  // (which could disagree with c.level near a boundary).
  const breaks: number[] = [];
  for (const l of [1, 2, 3, 4] as const) {
    const ratesInLevel = comunas.filter((c) => c.level === l).map((c) => c.rate);
    breaks.push(ratesInLevel.length > 0 ? Math.max(...ratesInLevel) : (breaks[l - 2] ?? 0));
  }
  for (const c of comunas) {
    levelIdx.set(c.id, c.level);
    counts[c.level - 1]++;
  }
  return { levelIdx, breaks, counts, values: comunas.map((c) => c.rate) };
}

/**
 * Dim every commune OUTSIDE the isolated band. Mutates the style map before
 * applyStyleMap (D-12 — one setStyle pass, no re-mount). No-op when band is null.
 */
export function applyBandDim(
  styleMap: Map<string, L.PathOptions>,
  levelIdx: Map<string, Level>,
  band: number | null
): void {
  if (band === null) return;
  for (const [cut, st] of styleMap) {
    if (levelIdx.get(cut) !== band) {
      styleMap.set(cut, { ...st, fillOpacity: 0.06 });
    }
  }
}

/**
 * Histogram bins for the legend strip. Bins the positive values into `nBins`
 * equal-width buckets over [0, p97] (p97 keeps one outlier commune from
 * flattening the whole strip). Returns per-bin count share (0–1) and the
 * band (1–5) the bin's midpoint falls in, so bins can reuse INCIDENCE_COLORS.
 */
export function computeHistBins(
  values: number[],
  breaks: number[],
  nBins = 24
): Array<{ share: number; band: Level; count: number; lo: number; hi: number }> {
  const positive = values.filter((v) => v > 0).sort((a, b) => a - b);
  if (positive.length === 0) return [];
  const cap = positive[Math.min(positive.length - 1, Math.floor(positive.length * 0.97))] ?? 1;
  if (cap <= 0) return [];
  const counts = new Array<number>(nBins).fill(0);
  for (const v of positive) {
    counts[Math.min(nBins - 1, Math.floor((v / cap) * nBins))]++;
  }
  const max = Math.max(1, ...counts);
  return counts.map((n, i) => ({
    share: n / max,
    band: levelFromBreaks(((i + 0.5) / nBins) * cap, breaks),
    count: n,
    lo: Math.round((i / nBins) * cap),
    hi: Math.round(((i + 1) / nBins) * cap),
  }));
}
