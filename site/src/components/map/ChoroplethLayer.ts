/**
 * ChoroplethLayer.ts — Native L.geoJSON + L.canvas() layer factory.
 *
 * Rules:
 * - L.canvas() renderer declared ONLY inside L.geoJSON options (Pitfall 6).
 * - Never re-mount the layer on filter change — use applyStyleMap (D-12).
 * - Join key: feature.properties.id = CUT string.
 */
import L from 'leaflet';
import type { MutableRefObject } from 'react';
import { INCIDENCE_COLORS, DEFAULT_STYLE, computeQuantileBreaks, levelFromBreaks } from './colors';

export interface CommunaPayload {
  id: string; // CUT code
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
  /** Homicide rate per 100k (abbreviated key 'hr' from map-payload — D-09 compact encoding). null when no data. */
  hr: number | null;
  /** Homicide count (dropped from map-payload per budget; read from per-commune JSON featured_rates.homicidios_count). null in map-payload context. */
  homicide_count: number | null;
  /** Composite crime index level (1-5, pre-computed by pipeline). null when not yet computed. */
  ci: number | null;
}

/**
 * Build a CUT → PathOptions style map from precomputed levels.
 * Called once on initial data load (D-11).
 */
export function buildStyleMapFromLevel(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[c.level - 1]!,
      fillOpacity: 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}

/**
 * Mount the choropleth layer on the map.
 * Called once geoData is loaded; never called again on filter change.
 *
 * @param map - The L.Map instance
 * @param geoData - FeatureCollection with features keyed by properties.id (CUT)
 * @param styleMapRef - Ref to the CUT → PathOptions style map (memoized)
 * @param polyIdxRef - Ref to the CUT → L.Layer index (populated by this fn)
 * @param onClickCut - Callback when a polygon is clicked (receives CUT string)
 */
export function mountChoroplethLayer(
  map: L.Map,
  geoData: GeoJSON.FeatureCollection,
  styleMapRef: MutableRefObject<Map<string, L.PathOptions>>,
  polyIdxRef: MutableRefObject<Map<string, L.Layer>>,
  onClickCut: (cut: string) => void
): L.GeoJSON {
  const renderer = L.canvas(); // D-16: canvas renderer scoped to this layer only

  const layer = L.geoJSON(geoData, {
    // renderer is valid at runtime but missing from @types/leaflet GeoJSONOptions
    ...(({ renderer } as unknown) as object),
    style: (f) =>
      styleMapRef.current.get(f!.properties!.id as string) ?? DEFAULT_STYLE,
    onEachFeature: (f, ly) => {
      const cut = f.properties!.id as string;
      const name = f.properties!.name as string;

      ly.bindTooltip(name, { sticky: true, direction: 'top' });
      ly.on('click', () => onClickCut(cut));
      ly.on('mouseover', () => {
        // Hover: only restyle non-selected polygons
        (ly as L.Path).setStyle({ fillOpacity: 0.74, weight: 1.8 });
      });
      ly.on('mouseout', () => layer.resetStyle(ly as L.Path));

      polyIdxRef.current.set(cut, ly);
    },
  }).addTo(map);

  return layer;
}

/**
 * Build a CUT → PathOptions style map from a specific crime family (by_family index).
 * Called on crime-type chip change; computes quantile breaks client-side (D-11).
 */
export function buildStyleMapFromFamily(
  comunas: CommunaPayload[],
  familyIndex: number
): Map<string, L.PathOptions> {
  const rates = comunas.map((c) => c.by_family[familyIndex] ?? 0);
  const positiveRates = rates.filter((r) => r > 0);
  const breaks = computeQuantileBreaks(positiveRates, 5);
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = c.by_family[familyIndex] ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}

/**
 * Build a CUT → PathOptions style map for the homicide layer (D-05 independent scale).
 *
 * Reads `c.hr` (abbreviated 'hr' key from map-payload, D-09) for the homicide rate.
 * Quantile breaks are computed on positive rates ONLY so the scale is not compressed
 * by zero-homicide comunas (D-05 mandate: independent scale, not shared family scale).
 * Zero/null rate comunas map to the lightest bucket with reduced fillOpacity (0.25)
 * to visually distinguish them from comunas with actual homicide data.
 */
export function buildStyleMapFromHomicide(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const rates = comunas.map((c) => c.hr ?? 0);
  const positiveRates = rates.filter((r) => r > 0);
  const breaks = computeQuantileBreaks(positiveRates, 5);
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = c.hr ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: rate === 0 ? 0.25 : 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}

/**
 * Build a CUT → PathOptions style map from the precomputed composite index level (ci).
 * No client-side quantile recompute — the pipeline pre-computed the level (1-5).
 * Null-ci communes fall back to level 3 with reduced fillOpacity (0.25) to visually
 * distinguish them from communes with actual composite data (T-18-09 mitigation).
 */
export function buildStyleMapFromCompositeIndex(
  comunas: CommunaPayload[]
): Map<string, L.PathOptions> {
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const level = c.ci ?? 3;
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: c.ci === null ? 0.25 : 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  }
  return m;
}

/**
 * Apply a new style map to the existing layer in place (D-12 — never re-mount).
 * Called on every year or crime-family filter change.
 */
export function applyStyleMap(
  layer: L.GeoJSON,
  styleMapRef: MutableRefObject<Map<string, L.PathOptions>>
): void {
  layer.setStyle((f) =>
    styleMapRef.current.get(f!.properties!.id as string) ?? DEFAULT_STYLE
  );
}

/**
 * Highlight the selected commune polygon (D-12 selected state).
 * Reverts the previously selected polygon to its default style.
 */
export function highlightSelected(
  layer: L.GeoJSON,
  polyIdxRef: MutableRefObject<Map<string, L.Layer>>,
  cut: string,
  prevCut: string | null
): void {
  if (prevCut) {
    const prev = polyIdxRef.current.get(prevCut);
    if (prev) layer.resetStyle(prev as L.Path);
  }
  const ly = polyIdxRef.current.get(cut);
  if (ly) {
    (ly as L.Path).setStyle({ color: '#0f766e', weight: 2.5, fillOpacity: 0.78 });
    (ly as L.Path).bringToFront();
  }
}
