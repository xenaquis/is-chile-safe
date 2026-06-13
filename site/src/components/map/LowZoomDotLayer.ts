/**
 * LowZoomDotLayer.ts — L.layerGroup of circleMarkers shown at zoom < 8.
 *
 * Rules:
 * - Do NOT set a global canvas renderer on circleMarkers (Pitfall 6).
 *   The L.canvas() renderer is declared only on the L.geoJSON choropleth layer.
 * - Radius formula: 4.5 + level * 1.1 (UI-SPEC exact).
 * - Lat/lng derived from GeoJSON feature centroid (ring centroid computed here).
 */
import L from 'leaflet';
import { INCIDENCE_COLORS } from './colors';

export interface DotCommune {
  id: string;  // CUT
  lat: number;
  lng: number;
  name: string;
  level: 1 | 2 | 3 | 4 | 5;
}

/**
 * Compute a simple centroid from a GeoJSON feature's geometry.
 * Handles Polygon (first ring) and MultiPolygon (first ring of largest polygon by point count).
 */
export function computeCentroid(
  feature: GeoJSON.Feature
): { lat: number; lng: number } | null {
  const geom = feature.geometry;
  if (!geom) return null;

  let ring: GeoJSON.Position[] = [];

  if (geom.type === 'Polygon') {
    ring = geom.coordinates[0] ?? [];
  } else if (geom.type === 'MultiPolygon') {
    // Use the first ring of the largest sub-polygon
    let maxLen = 0;
    for (const poly of geom.coordinates) {
      const r = poly[0] ?? [];
      if (r.length > maxLen) {
        maxLen = r.length;
        ring = r;
      }
    }
  } else {
    return null;
  }

  if (ring.length === 0) return null;

  let sumLng = 0;
  let sumLat = 0;
  for (const pt of ring) {
    sumLng += pt[0] ?? 0;
    sumLat += pt[1] ?? 0;
  }
  return { lat: sumLat / ring.length, lng: sumLng / ring.length };
}

/**
 * Build dot commune list from loaded GeoJSON features and payload data.
 *
 * @param features - Decoded GeoJSON features from communes.topo.json
 * @param comunas - Map-payload commune array
 */
export function buildDotComunas(
  features: GeoJSON.Feature[],
  comunas: Array<{ id: string; level: 1 | 2 | 3 | 4 | 5; rate?: number; by_family?: number[] }>
): DotCommune[] {
  // Index features by CUT for O(1) lookup
  const featureIdx = new Map<string, GeoJSON.Feature>();
  for (const f of features) {
    const id = f.properties?.id as string | undefined;
    if (id) featureIdx.set(id, f);
  }

  const dots: DotCommune[] = [];
  for (const c of comunas) {
    const f = featureIdx.get(c.id);
    if (!f) continue;
    const centroid = computeCentroid(f);
    if (!centroid) continue;
    dots.push({
      id: c.id,
      lat: centroid.lat,
      lng: centroid.lng,
      name: (f.properties?.name as string) ?? c.id,
      level: c.level,
    });
  }
  return dots;
}

/**
 * Mount the low-zoom dot overview layer.
 * Called when zoom < 8; removed when zoom >= 8.
 *
 * @param map - The L.Map instance
 * @param comunas - Dot commune list with lat/lng/level
 * @param onClickCut - Callback when a dot is clicked (receives CUT string)
 */
export function mountLowZoomDots(
  map: L.Map,
  comunas: DotCommune[],
  onClickCut: (cut: string) => void
): L.LayerGroup {
  const layer = L.layerGroup();

  for (const c of comunas) {
    L.circleMarker([c.lat, c.lng], {
      // Do NOT set renderer: L.canvas() here (Pitfall 6 — markers use DOM, not canvas path)
      radius: 4.5 + c.level * 1.1,
      color: '#ffffff',
      weight: 1.2,
      fillColor: INCIDENCE_COLORS[c.level - 1]!,
      fillOpacity: 0.92,
    })
      .bindTooltip(c.name, { direction: 'top', offset: [0, -8] })
      .on('click', () => onClickCut(c.id))
      .addTo(layer);
  }

  return layer.addTo(map);
}
