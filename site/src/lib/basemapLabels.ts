/**
 * basemapLabels.ts — pure helpers for the self-drawn basemap (no Leaflet, no DOM).
 *
 * The map no longer uses any third-party tile service (quick-261124-bmp), so
 * place names are drawn by the island itself. This module decides WHICH names
 * are candidates at a zoom level and culls collisions; BasemapLayer.ts turns
 * the survivors into non-interactive Leaflet divIcon markers.
 *
 * Kept in lib/ so vitest can assert the zoom cap and the tier/collision logic.
 */
import labelPointsFile from '../data/commune-label-points.json';

/** Zoom limits set on L.map itself. Without a tile layer Leaflet's max zoom is
 *  Infinity, so the cap MUST live on the map. 13 ≈ commune polygons + pins are
 *  still meaningful; deeper zoom would only show a blank single-colour canvas. */
export const MAP_MIN_ZOOM = 4;
export const MAP_MAX_ZOOM = 13;

/** Pan limits ([[south, west], [north, east]]). Leaflet keeps the view inside
 *  them while it is smaller; a larger view is centred on them and overhangs. */
export const MAP_MAX_BOUNDS: [[number, number], [number, number]] = [[-60, -80], [-14, -60]];

/** The 16 regional capitals (CUT, unpadded — same format as index.json / topo ids). */
export const REGIONAL_CAPITAL_CUTS: readonly string[] = [
  '15101', // Arica
  '1101',  // Iquique
  '2101',  // Antofagasta
  '3101',  // Copiapó
  '4101',  // La Serena
  '5101',  // Valparaíso
  '13101', // Santiago
  '6101',  // Rancagua
  '7101',  // Talca
  '16101', // Chillán
  '8101',  // Concepción
  '9101',  // Temuco
  '14101', // Valdivia
  '10101', // Puerto Montt
  '11101', // Coyhaique
  '12101', // Punta Arenas
];

/**
 * Label anchor [lat, lng] of each regional capital = the CITY, hand-checked.
 * A capital's commune can be huge (Antofagasta, Punta Arenas, Iquique): any
 * point derived from the polygon lands 50-140 km from the city the label names,
 * and with no street layer nothing else shows where the city is. Points are
 * nudged a few hundred metres inland where the simplified coast would leave the
 * exact centre outside the polygon (vitest asserts each lies inside its commune).
 */
export const CAPITAL_LABEL_POINTS: Readonly<Record<string, readonly [number, number]>> = {
  '15101': [-18.478, -70.305], // Arica
  '1101': [-20.235, -70.135],  // Iquique
  '2101': [-23.65, -70.385],   // Antofagasta
  '3101': [-27.366, -70.332],  // Copiapó
  '4101': [-29.905, -71.245],  // La Serena
  '5101': [-33.055, -71.615],  // Valparaíso
  '13101': [-33.45, -70.66],   // Santiago
  '6101': [-34.17, -70.74],    // Rancagua
  '7101': [-35.43, -71.66],    // Talca
  '16101': [-36.607, -72.103], // Chillán
  '8101': [-36.827, -73.05],   // Concepción
  '9101': [-38.739, -72.598],  // Temuco
  '14101': [-39.81, -73.22],   // Valdivia (east bank; the river mouth is cut out of the simplified polygon)
  '10101': [-41.465, -72.94],  // Puerto Montt
  '11101': [-45.571, -72.068], // Coyhaique
  '12101': [-53.155, -70.925], // Punta Arenas
};

/** Interior point of every commune polygon, built offline (scripts/build-basemap.mjs). */
const INTERIOR_POINTS = (labelPointsFile as { points: Record<string, number[]> }).points;

/**
 * Where a commune's name is drawn: the city for a regional capital, otherwise an
 * interior point of the commune polygon. Returns null for an unknown CUT (the
 * caller falls back to the dot-layer centroid). Never a vertex average: that
 * fell outside the commune for 16 of 346 (e.g. "Chillán" on Chillán Viejo).
 */
export function labelAnchor(cut: string): { lat: number; lng: number } | null {
  const p = CAPITAL_LABEL_POINTS[cut] ?? INTERIOR_POINTS[cut];
  if (!p || p.length < 2 || !Number.isFinite(p[0]) || !Number.isFinite(p[1])) return null;
  return { lat: p[0], lng: p[1] };
}

/** Well-spaced subset shown at the national overview (zoom 4-5). */
export const ANCHOR_CITY_CUTS: readonly string[] = ['15101', '2101', '4101', '13101', '8101', '10101', '12101'];

/** Never labelled: Antártica placeholder polygon and Isla de Pascua (outside the pan bounds). */
export const LABEL_SKIP_CUTS: readonly string[] = ['12202', '5201'];

/** Max commune labels on screen after collision culling. */
export const MAX_COMMUNE_LABELS = 40;

export interface CommuneLabelSource {
  cut: string;
  name: string;
  /** Label anchor (labelAnchor): used when the name is centred on the place (zoom >= 8). */
  lat: number;
  lng: number;
  /** Position of this commune's low-zoom dot, when known: below zoom 8 the name
   *  is drawn beside that dot, so it must follow the dot, not the anchor. */
  dotLat?: number;
  dotLng?: number;
  /** INE population from meta/index.json; 0 when the index failed to load. */
  population: number;
}

export interface ContextLabel {
  id: string;
  lat: number;
  lng: number;
  en: string;
  es: string;
  kind: 'country' | 'ocean';
}

/**
 * Neighbouring-country and ocean names. Positions are hand-picked to sit inside
 * the phone viewport at zoom 4 and clear of the Chilean city labels — they are
 * NOT true centroids. Deliberately no label for Antarctica, the Falkland/Malvinas
 * islands or any border: the surrounding land is visual context only.
 */
export const CONTEXT_LABELS: readonly ContextLabel[] = [
  { id: 'arg', lat: -39.2, lng: -65.0, en: 'Argentina', es: 'Argentina', kind: 'country' },
  { id: 'bol', lat: -17.2, lng: -64.8, en: 'Bolivia', es: 'Bolivia', kind: 'country' },
  { id: 'per', lat: -14.6, lng: -73.6, en: 'Peru', es: 'Perú', kind: 'country' },
  { id: 'pry', lat: -23.3, lng: -58.3, en: 'Paraguay', es: 'Paraguay', kind: 'country' },
  { id: 'ury', lat: -32.9, lng: -56.0, en: 'Uruguay', es: 'Uruguay', kind: 'country' },
  { id: 'bra', lat: -19.5, lng: -50.0, en: 'Brazil', es: 'Brasil', kind: 'country' },
  { id: 'pac', lat: -28.5, lng: -80.5, en: 'Pacific Ocean', es: 'Océano Pacífico', kind: 'ocean' },
  { id: 'atl', lat: -47.0, lng: -57.5, en: 'Atlantic Ocean', es: 'Océano Atlántico', kind: 'ocean' },
];

/** Country/ocean names are only shown on the wide overview. */
export const CONTEXT_LABEL_MAX_ZOOM = 6;

/** Below this zoom the low-zoom dot layer is visible, so commune labels are
 *  drawn beside the dot instead of centred on it. Mirrors MapIsland's `lowZoom`. */
export const DOT_LAYER_MAX_ZOOM = 8;

export function contextLabelsForZoom(zoom: number): readonly ContextLabel[] {
  return zoom <= CONTEXT_LABEL_MAX_ZOOM ? CONTEXT_LABELS : [];
}

function insidePanBounds(c: CommuneLabelSource): boolean {
  const [[s, w], [n, e]] = MAP_MAX_BOUNDS;
  return c.lat >= s && c.lat <= n && c.lng >= w && c.lng <= e;
}

/**
 * Commune label candidates for a zoom level, in PRIORITY order (first = most
 * important; the collision pass keeps earlier entries).
 *   z ≤ 5   : anchor cities
 *   z 6-7   : the 16 regional capitals
 *   z 8-9   : capitals, then communes with population ≥ 100k
 *   z ≥ 10  : capitals, then every commune by population
 */
export function communeLabelCandidates(
  zoom: number,
  communes: readonly CommuneLabelSource[]
): CommuneLabelSource[] {
  const usable = communes.filter((c) => !LABEL_SKIP_CUTS.includes(c.cut) && insidePanBounds(c));
  const byCut = new Map(usable.map((c) => [c.cut, c]));
  const pick = (cuts: readonly string[]) =>
    cuts.map((cut) => byCut.get(cut)).filter((c): c is CommuneLabelSource => c !== undefined);

  if (zoom <= 5) return pick(ANCHOR_CITY_CUTS);

  const capitals = pick(REGIONAL_CAPITAL_CUTS);
  if (zoom <= 7) return capitals;

  const capitalSet = new Set(REGIONAL_CAPITAL_CUTS);
  const rest = usable
    .filter((c) => !capitalSet.has(c.cut) && (zoom >= 10 || c.population >= 100_000))
    .sort((a, b) => b.population - a.population || a.name.localeCompare(b.name));
  return [...capitals, ...rest];
}

// ---------------------------------------------------------------------------
// Collision culling
// ---------------------------------------------------------------------------

export interface LabelBox {
  id: string;
  /** Screen-space anchor (container pixels). */
  x: number;
  y: number;
  /** Estimated box size in pixels. */
  w: number;
  h: number;
  /** 'center' = box centred on the anchor; 'right' = box starts dx px right of it. */
  align: 'center' | 'right';
  dx?: number;
}

/** Rough text width for an 11-12px sans label (no DOM measurement needed). */
export function estimateLabelWidth(text: string, charPx = 6.4, padPx = 6): number {
  const longestLine = text.split('\n').reduce((m, l) => Math.max(m, l.length), 0);
  return Math.ceil(longestLine * charPx + padPx);
}

function rect(b: LabelBox): [number, number, number, number] {
  const left = b.align === 'center' ? b.x - b.w / 2 : b.x + (b.dx ?? 0);
  const top = b.y - b.h / 2;
  return [left, top, left + b.w, top + b.h];
}

/**
 * Greedy rectangle-collision pass: boxes are visited in the given (priority)
 * order and kept only when they overlap no previously kept box. `max` caps the
 * number of survivors. Returns the kept ids in order.
 */
export function cullCollisions(boxes: readonly LabelBox[], max = Infinity, gap = 2): string[] {
  const kept: Array<[number, number, number, number]> = [];
  const out: string[] = [];
  for (const b of boxes) {
    if (out.length >= max) break;
    const [l, t, r, btm] = rect(b);
    const hit = kept.some(([kl, kt, kr, kb]) => l < kr + gap && r > kl - gap && t < kb + gap && btm > kt - gap);
    if (hit) continue;
    kept.push([l, t, r, btm]);
    out.push(b.id);
  }
  return out;
}
