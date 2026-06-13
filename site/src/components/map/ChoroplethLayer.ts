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
import { INCIDENCE_COLORS, DEFAULT_STYLE } from './colors';

export interface CommunaPayload {
  id: string; // CUT code
  rate: number;
  level: 1 | 2 | 3 | 4 | 5;
  by_family: number[];
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
