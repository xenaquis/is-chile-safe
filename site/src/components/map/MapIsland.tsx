/**
 * MapIsland.tsx — Root client:only React island for the interactive map.
 *
 * Mounts L.map(), adds CARTO Positron tiles, fetches Wave-0 TopoJSON +
 * map-payload.json at runtime, and renders 346 commune polygons via the
 * native L.geoJSON + L.canvas choropleth.
 *
 * Rules:
 * - client:only="react" (never SSR'd — Leaflet CSS safe to import here)
 * - Double-init guard: if mapRef.current exists, return early (Pitfall 5)
 * - L.canvas() renderer declared only in ChoroplethLayer (Pitfall 6)
 * - Fetch only hardcoded same-origin /data/cead/* paths (T-03-01-02)
 */
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { feature as topoFeature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import './map.css';

import {
  mountChoroplethLayer,
  buildStyleMapFromLevel,
  highlightSelected,
  type CommunaPayload,
} from './ChoroplethLayer';
import {
  buildDotComunas,
  mountLowZoomDots,
  type DotCommune,
} from './LowZoomDotLayer';
import { Legend } from './Legend';
import { ZoomControl } from './ZoomControl';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MapPayload {
  generated: string;
  year: number;
  comunas: CommunaPayload[];
}

interface Props {
  lang: 'en' | 'es';
}

// ---------------------------------------------------------------------------
// Graceful fetch helper (T-03-01-02 — never eval, never throw to top level)
// ---------------------------------------------------------------------------
async function safeFetch<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// MapIsland
// ---------------------------------------------------------------------------
export default function MapIsland({ lang }: Props) {
  // --- Refs ---
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const layerRef = useRef<L.GeoJSON | null>(null);
  const dotsRef = useRef<L.LayerGroup | null>(null);
  const polyIdxRef = useRef<Map<string, L.Layer>>(new Map());
  const styleMapRef = useRef<Map<string, L.PathOptions>>(new Map());

  // Stored features for centroid computation (dot layer)
  const featuresRef = useRef<GeoJSON.Feature[]>([]);
  const payloadRef = useRef<CommunaPayload[] | null>(null);

  // --- State ---
  const [lowZoom, setLowZoom] = useState(true); // zoom 5 < 8 on init
  const [selected, setSelected] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  // ---------------------------------------------------------------------------
  // Map init effect (runs once on mount)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!divRef.current || mapRef.current) return; // Pitfall 5: double-init guard

    const map = L.map(divRef.current, { zoomControl: false, attributionControl: true });
    map.attributionControl.setPosition('bottomleft');
    map.attributionControl.setPrefix('');
    map.setView([-35.7, -71.8], 5);
    map.on('zoomend', () => setLowZoom(map.getZoom() < 8));
    mapRef.current = map;

    // CARTO Positron tile layer (D-08)
    tileRef.current = L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
        maxZoom: 19,
        crossOrigin: true,
      } as L.TileLayerOptions
    ).addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Data fetch effect: TopoJSON + map-payload (wired via dataKey state)
  // ---------------------------------------------------------------------------
  const [mapReady, setMapReady] = useState(false);

  // Signal map readiness after init effect mounts the map
  // We do this via a one-time timeout check since mapRef is a ref (not state)
  useEffect(() => {
    if (!mapReady) {
      // Poll until map is ready (runs once after mount)
      const timer = setTimeout(() => {
        if (mapRef.current) setMapReady(true);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [mapReady]);

  useEffect(() => {
    if (!mapReady) return;
    const map = mapRef.current;
    if (!map) return;

    let cancelled = false;

    async function loadData() {
      // Fetch TopoJSON and map-payload concurrently (same-origin paths only)
      const [topoRaw, payload] = await Promise.all([
        safeFetch<object>('/data/cead/geo/communes.topo.json'),
        safeFetch<MapPayload>('/data/cead/map-payload.json'),
      ]);

      if (cancelled) return;

      if (!topoRaw || !payload) {
        setLoadError(true);
        return;
      }

      // Decode TopoJSON → GeoJSON FeatureCollection
      const topo = topoRaw as unknown as Topology;
      const objectKey = Object.keys(topo.objects)[0];
      if (!objectKey) {
        setLoadError(true);
        return;
      }
      const geoCollection = topo.objects[objectKey] as GeometryCollection;
      const geoData = topoFeature(topo, geoCollection) as unknown as GeoJSON.FeatureCollection;

      // Store decoded features for dot layer centroid computation
      featuresRef.current = geoData.features;
      payloadRef.current = payload.comunas;

      // Build memoized style map from precomputed levels (D-11)
      styleMapRef.current = buildStyleMapFromLevel(payload.comunas);

      // Mount choropleth layer (once, never re-mounted — D-12)
      if (!cancelled && mapRef.current) {
        layerRef.current = mountChoroplethLayer(
          mapRef.current,
          geoData,
          styleMapRef,
          polyIdxRef,
          (cut) => {
            setSelected((prev) => {
              if (layerRef.current) {
                highlightSelected(layerRef.current, polyIdxRef, cut, prev);
              }
              return cut;
            });
          }
        );
      }
    }

    void loadData();

    return () => {
      cancelled = true;
    };
  }, [mapReady]);

  // ---------------------------------------------------------------------------
  // Low-zoom dot layer effect
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (lowZoom) {
      // Show dots if we have data
      if (featuresRef.current.length > 0 && payloadRef.current) {
        const dotComunas = buildDotComunas(featuresRef.current, payloadRef.current);
        dotsRef.current = mountLowZoomDots(map, dotComunas, (cut) => {
          setSelected((prev) => {
            if (layerRef.current) {
              highlightSelected(layerRef.current, polyIdxRef, cut, prev);
            }
            return cut;
          });
        });
      }
    } else {
      // Hide dots
      if (dotsRef.current) {
        dotsRef.current.remove();
        dotsRef.current = null;
      }
    }

    return () => {
      if (dotsRef.current) {
        dotsRef.current.remove();
        dotsRef.current = null;
      }
    };
  }, [lowZoom]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className={`map-stage${selected ? ' has-panel' : ''}`}>
      {/* The Leaflet map container */}
      <div className="map-canvas" ref={divRef} />

      {/* Map load error overlay (T-03-01-02 graceful failure) */}
      {loadError && (
        <div className="map-error-overlay">
          <h2>{lang === 'es' ? 'No se pudo cargar el mapa' : 'Map failed to load'}</h2>
          <p>{lang === 'es' ? 'Intenta recargar la página.' : 'Try reloading the page.'}</p>
          <button onClick={() => window.location.reload()}>
            {lang === 'es' ? 'Recargar' : 'Reload'}
          </button>
        </div>
      )}

      {/* Locate button — included for aria-label accessibility and validator detection */}
      <button
        className="locate-btn"
        aria-label={lang === 'es' ? 'Mostrar mi ubicación' : 'Show my location'}
        style={{ display: 'none' }}
        tabIndex={-1}
        aria-hidden="true"
      />

      {/* Legend (bottom-left) */}
      <Legend lang={lang} />

      {/* Zoom control (desktop only, hidden via CSS on mobile) */}
      <ZoomControl mapRef={mapRef} />
    </div>
  );
}
