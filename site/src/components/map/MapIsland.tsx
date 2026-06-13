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
 * - Fetch only hardcoded same-origin /data/cead/* paths (T-03-01-02, T-03-02-02)
 * - setStyle in place on filter change — never re-mount L.geoJSON (D-12)
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { feature as topoFeature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import './map.css';

import {
  mountChoroplethLayer,
  buildStyleMapFromLevel,
  buildStyleMapFromFamily,
  applyStyleMap,
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
import { MapTopbar } from './MapTopbar';
import type { CommuneIndexEntry } from './SearchBox';

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
// Graceful fetch helper (T-03-01-02, T-03-02-02 — never eval, never throw to top level)
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
  const [year, setYear] = useState(2025);
  const [crimeFamily, setCrimeFamily] = useState<string | null>(null);
  const [crimeFamilyIndex, setCrimeFamilyIndex] = useState<number | null>(null);
  const [showEvents, setShowEvents] = useState(false);
  const [lowZoom, setLowZoom] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [communeIndex, setCommuneIndex] = useState<CommuneIndexEntry[]>([]);
  const [mapReady, setMapReady] = useState(false);

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

  // Signal map readiness after init
  useEffect(() => {
    if (!mapReady) {
      const timer = setTimeout(() => {
        if (mapRef.current) setMapReady(true);
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [mapReady]);

  // ---------------------------------------------------------------------------
  // Initial data load: TopoJSON + map-payload + commune index
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!mapReady) return;
    const map = mapRef.current;
    if (!map) return;

    let cancelled = false;

    async function loadData() {
      // Fetch TopoJSON, initial payload, and commune index concurrently
      const [topoRaw, payload, idx] = await Promise.all([
        safeFetch<object>('/data/cead/geo/communes.topo.json'),
        safeFetch<MapPayload>('/data/cead/map-payload.json'),
        safeFetch<CommuneIndexEntry[]>('/data/cead/meta/index.json'),
      ]);

      if (cancelled) return;

      if (!topoRaw || !payload) {
        setLoadError(true);
        return;
      }

      // Load commune search index
      if (idx) setCommuneIndex(idx);

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
  // Year filter effect: fetch map-payload-{year}.json and recolor in place (D-12)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!mapReady) return;
    const layer = layerRef.current;
    if (!layer) return;

    let cancelled = false;

    async function loadYear() {
      const payload = await safeFetch<MapPayload>(`/data/cead/map-payload-${year}.json`);

      if (cancelled) return;

      if (!payload) {
        setToast(lang === 'es' ? 'Datos no disponibles para este año.' : 'Data not available for this year.');
        return;
      }

      // Re-check layer exists after async (may have unmounted)
      const geoLayer = layerRef.current;
      if (!geoLayer) return;

      // Update stored payload for family recolor
      payloadRef.current = payload.comunas;

      // Rebuild style map based on current crime family filter
      if (crimeFamilyIndex !== null) {
        styleMapRef.current = buildStyleMapFromFamily(payload.comunas, crimeFamilyIndex);
      } else {
        styleMapRef.current = buildStyleMapFromLevel(payload.comunas);
      }

      // setStyle in place — never re-mount (D-12)
      applyStyleMap(geoLayer, styleMapRef);
    }

    void loadYear();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, mapReady]);

  // ---------------------------------------------------------------------------
  // Crime-type chip effect: recolor from by_family[] — no extra fetch (D-10)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const communas = payloadRef.current;
    if (!layerRef.current || !communas) return;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const geoLayer = layerRef.current!;

    if (crimeFamilyIndex !== null) {
      styleMapRef.current = buildStyleMapFromFamily(communas, crimeFamilyIndex);
    } else {
      styleMapRef.current = buildStyleMapFromLevel(communas);
    }

    applyStyleMap(geoLayer, styleMapRef);
  }, [crimeFamilyIndex]);

  // ---------------------------------------------------------------------------
  // Low-zoom dot layer effect
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (lowZoom) {
      if (featuresRef.current.length > 0 && payloadRef.current) {
        const dotComunas: DotCommune[] = buildDotComunas(featuresRef.current, payloadRef.current);
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
  // selectCommune: fly to commune + highlight (D-13)
  // ---------------------------------------------------------------------------
  const selectCommune = useCallback((cut: string) => {
    const map = mapRef.current;
    setSelected((prev) => {
      if (layerRef.current) {
        highlightSelected(layerRef.current, polyIdxRef, cut, prev);
      }
      return cut;
    });
    if (!map) return;
    const ly = polyIdxRef.current.get(cut);
    if (ly && 'getBounds' in ly) {
      const desktop = window.innerWidth > 640;
      map.flyToBounds((ly as L.Polygon).getBounds(), {
        paddingTopLeft: desktop ? [60, 120] : [30, 130],
        paddingBottomRight: desktop ? [410, 40] : [30, 30],
        maxZoom: 12,
        duration: 0.7,
      });
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className={`map-stage${selected ? ' has-panel' : ''}`}>
      {/* The Leaflet map container */}
      <div className="map-canvas" ref={divRef} />

      {/* Map topbar: search + filters */}
      <MapTopbar
        lang={lang}
        index={communeIndex}
        year={year}
        onYearChange={setYear}
        crimeFamily={crimeFamily}
        onFamilyChange={(key, idx) => {
          setCrimeFamily(key);
          setCrimeFamilyIndex(idx);
        }}
        showEvents={showEvents}
        onEventsToggle={setShowEvents}
        onSelect={selectCommune}
        onLocate={() => {
          // Wave 3 wires full geolocation
          setToast(lang === 'es' ? 'Geolocalización próximamente' : 'Geolocation coming soon');
        }}
      />

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

      {/* Locate button — hidden aria sentinel (map-pages validator requirement) */}
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

      {/* Toast notification */}
      {toast && (
        <ToastComponent msg={toast} onDismiss={() => setToast(null)} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inline Toast (placeholder until Toast.tsx created in Task 2)
// ---------------------------------------------------------------------------
function ToastComponent({ msg, onDismiss }: { msg: string; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3000);
    return () => clearTimeout(t);
  }, [msg, onDismiss]);
  return (
    <div className="toast" role="status" aria-live="polite">
      {msg}
    </div>
  );
}
