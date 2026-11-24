/**
 * BasemapLayer.ts — the map's own basemap. No third-party raster/vector map
 * service, no API key, no map-specific font or sprite host (quick-261124-bmp).
 * Labels use the site-wide web font and fall back to a system font without it.
 *
 * Layers, bottom to top:
 *   ocean          — CSS background of .map-canvas (map.css, --bm-ocean)
 *   pane "basemap" (z 200, below overlayPane 400, pointer-events none)
 *     1. neighbour land  — /data/cead/geo/basemap.topo.json (Natural Earth,
 *                          public domain; Chile already erased offline by
 *                          scripts/build-basemap.mjs). OPTIONAL: if the fetch
 *                          fails the map still works.
 *     2. Chile silhouette — merged at runtime from the commune topology that is
 *                          already loaded, so its edge IS the commune edge (no
 *                          double coast). Near-white so the translucent
 *                          choropleth fills keep matching the legend swatches;
 *                          its stroke (painted under the fill) outlines the
 *                          Chilean edge and hides sub-pixel hairlines between
 *                          the two datasets along the Andes.
 *   overlayPane    — choropleth canvas + low-zoom dots (untouched, D-12)
 *   pane "basemapLabels" (z 450, below markerPane 600, pointer-events none)
 *     place names as non-interactive, non-focusable divIcon markers.
 *
 * Rules:
 * - This module never touches the choropleth layer, its refs or React state.
 * - Every entry point swallows its own errors: the basemap is decoration.
 * - SVG renderer bound to the pane (NOT L.canvas — Pitfall 6): the SVG root is
 *   pointer-events:none, and class-based fills can use the CSS tokens.
 */
import L from 'leaflet';
import { feature as topoFeature, merge as topoMerge } from 'topojson-client';
import type { Topology, GeometryCollection, Polygon, MultiPolygon } from 'topojson-specification';
import {
  communeLabelCandidates,
  contextLabelsForZoom,
  cullCollisions,
  estimateLabelWidth,
  DOT_LAYER_MAX_ZOOM,
  MAX_COMMUNE_LABELS,
  type CommuneLabelSource,
  type LabelBox,
} from '../../lib/basemapLabels';

export const BASEMAP_URL = '/data/cead/geo/basemap.topo.json';
const BASEMAP_PANE = 'basemap';
const LABELS_PANE = 'basemapLabels';

// Fallback colours (CSS classes .bm-land / .bm-chile override them with tokens).
const LAND_FILL = '#dcdad2';
const LAND_LINE = '#c4c2b9';
const CHILE_FILL = '#fcfdfd';
const CHILE_LINE = '#b3bfc3';

export interface Basemap {
  /** Chile silhouette from the already-loaded commune topology. */
  setChile(topo: Topology, communes: GeometryCollection): void;
  /** Neighbour land from basemap.topo.json. Returns false when the payload is unusable. */
  setLand(raw: unknown): boolean;
  /** Commune label sources (name + centroid + population). */
  setCommunes(list: CommuneLabelSource[]): void;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (ch) =>
    ch === '&' ? '&amp;' : ch === '<' ? '&lt;' : ch === '>' ? '&gt;' : ch === '"' ? '&quot;' : '&#39;'
  );
}

interface Candidate {
  box: LabelBox;
  lat: number;
  lng: number;
  html: string;
  cls: string;
}

/**
 * Create the panes + label controller. Call once, right after L.map().
 * Panes are created synchronously so layer order never depends on fetch order.
 */
export function initBasemap(map: L.Map, lang: 'en' | 'es'): Basemap {
  const basePane = map.createPane(BASEMAP_PANE);
  basePane.style.zIndex = '200';
  basePane.style.pointerEvents = 'none';

  const labelPane = map.createPane(LABELS_PANE);
  labelPane.style.zIndex = '450';
  labelPane.style.pointerEvents = 'none';
  labelPane.setAttribute('aria-hidden', 'true');

  // padding 1 = draw one extra viewport on every side, so drags and flyTo do
  // not expose ocean-coloured strips before the next redraw.
  const renderer = L.svg({ pane: BASEMAP_PANE, padding: 1 });

  let landLayer: L.GeoJSON | null = null;
  let communes: CommuneLabelSource[] = [];
  let markers: L.Marker[] = [];
  let timer: ReturnType<typeof setTimeout> | null = null;
  let disposed = false;

  const vectorOptions = (className: string): L.GeoJSONOptions =>
    ({
      pane: BASEMAP_PANE,
      interactive: false,
      className,
      // renderer is valid at runtime but missing from @types/leaflet GeoJSONOptions
      ...(({ renderer } as unknown) as object),
    }) as L.GeoJSONOptions;

  function refreshLabels(): void {
    if (disposed) return;
    try {
      for (const m of markers) m.remove();
      markers = [];

      const zoom = map.getZoom();
      const size = map.getSize();
      const beside = zoom < DOT_LAYER_MAX_ZOOM; // dots visible → label beside the dot
      const cands: Candidate[] = [];

      const onScreen = (x: number, y: number) => x > -40 && y > -20 && x < size.x + 40 && y < size.y + 20;

      // Chilean place names first: they win collisions against context names.
      for (const c of communeLabelCandidates(zoom, communes)) {
        // Beside mode: follow the dot. Centred mode: the label anchor (city / interior point).
        const useDot = beside && c.dotLat !== undefined && c.dotLng !== undefined;
        const lat = useDot ? (c.dotLat as number) : c.lat;
        const lng = useDot ? (c.dotLng as number) : c.lng;
        const p = map.latLngToContainerPoint([lat, lng]);
        if (!onScreen(p.x, p.y)) continue;
        cands.push({
          box: {
            id: `c${c.cut}`,
            x: p.x,
            y: p.y,
            w: estimateLabelWidth(c.name),
            h: 15,
            align: beside ? 'right' : 'center',
            dx: 12,
          },
          lat,
          lng,
          html: escapeHtml(c.name),
          cls: `bm-label bm-label--place${beside ? ' bm-label--beside' : ''}`,
        });
      }
      const communeIds = cullCollisions(cands.map((c) => c.box), MAX_COMMUNE_LABELS);

      const ctx: Candidate[] = [];
      for (const l of contextLabelsForZoom(zoom)) {
        const p = map.latLngToContainerPoint([l.lat, l.lng]);
        if (!onScreen(p.x, p.y)) continue;
        const text = (lang === 'es' ? l.es : l.en).toUpperCase();
        const lines = l.kind === 'ocean' ? text.split(' ') : [text];
        ctx.push({
          box: {
            id: `x${l.id}`,
            x: p.x,
            y: p.y,
            w: estimateLabelWidth(lines.join('\n'), 8.2, 6),
            h: 14 * lines.length,
            align: 'center',
          },
          lat: l.lat,
          lng: l.lng,
          html: lines.map(escapeHtml).join('<br>'),
          cls: `bm-label bm-label--${l.kind}`,
        });
      }

      const keptCommunes = cands.filter((c) => communeIds.includes(c.box.id));
      const keptAll = new Set(
        cullCollisions([...keptCommunes.map((c) => c.box), ...ctx.map((c) => c.box)])
      );

      for (const c of [...keptCommunes, ...ctx]) {
        if (!keptAll.has(c.box.id)) continue;
        const marker = L.marker([c.lat, c.lng], {
          pane: LABELS_PANE,
          interactive: false,
          keyboard: false,
          icon: L.divIcon({
            className: 'bm-label-anchor',
            html: `<span class="${c.cls}">${c.html}</span>`,
            iconSize: [0, 0],
            iconAnchor: [0, 0],
          }),
        });
        marker.addTo(map);
        markers.push(marker);
      }
    } catch {
      /* labels are decoration — never break the map */
    }
  }

  function scheduleLabels(): void {
    if (disposed) return;
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      refreshLabels();
    }, 60);
  }

  // Plain Leaflet handlers (no React state); map.remove() unbinds them.
  map.on('zoomend moveend resize', scheduleLabels);
  map.on('unload', () => {
    disposed = true;
    if (timer !== null) clearTimeout(timer);
    markers = [];
  });
  map.whenReady(scheduleLabels);

  return {
    setChile(topo, communesObject) {
      if (disposed) return;
      try {
        const geoms = communesObject.geometries.filter(
          (g): g is Polygon | MultiPolygon => g.type === 'Polygon' || g.type === 'MultiPolygon'
        );
        const merged = topoMerge(topo, geoms);
        const chile = L.geoJSON(
          { type: 'Feature', properties: {}, geometry: merged } as GeoJSON.Feature,
          {
            ...vectorOptions('bm-chile'),
            style: {
              // Painted under the fill (map.css `paint-order`), so ~1.5 px shows
              // outside the edge: a thin outline that also covers the sub-pixel
              // hairlines between the two datasets along the border.
              stroke: true,
              color: CHILE_LINE,
              weight: 3,
              opacity: 1,
              fillColor: CHILE_FILL,
              fillOpacity: 1,
            },
          }
        );
        chile.addTo(map);
        // Neighbour land (if it arrived first) must stay underneath.
        if (landLayer) landLayer.bringToBack();
      } catch {
        /* silhouette is optional */
      }
    },

    setLand(raw) {
      if (disposed || landLayer) return false;
      try {
        const topo = raw as Topology;
        const obj = topo && topo.type === 'Topology' ? topo.objects?.land : undefined;
        if (!obj) return false;
        const geo = topoFeature(topo, obj) as unknown as GeoJSON.GeoJsonObject;
        landLayer = L.geoJSON(geo, {
          ...vectorOptions('bm-land'),
          style: {
            stroke: true,
            color: LAND_LINE,
            weight: 0.8,
            opacity: 1,
            fillColor: LAND_FILL,
            fillOpacity: 1,
          },
        });
        landLayer.addTo(map);
        landLayer.bringToBack(); // below the Chile silhouette whatever the load order
        return true;
      } catch {
        landLayer = null;
        return false;
      }
    },

    setCommunes(list) {
      communes = list;
      scheduleLabels();
    },
  };
}
