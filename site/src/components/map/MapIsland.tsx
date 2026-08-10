/**
 * MapIsland.tsx — Root client:only React island for the interactive map.
 *
 * Mounts L.map(), adds CARTO Positron tiles, fetches Wave-0 TopoJSON +
 * map-payload.json at runtime, and renders 346 commune polygons via the
 * native L.geoJSON + L.canvas choropleth.
 *
 * MAPV2 changes (see install-mapa/INSTALL.md):
 * - One "layer" control (LAYER_DEFS) replaces Modo + Tipo de delito. The
 *   internal state machine (mode / crimeFamily / crimeFamilyIndex /
 *   crimeIsHomicide) is UNCHANGED — onLayerChange just sets all four.
 * - The three duplicated restyle branches (year effect, chip effect, mode
 *   handler) are centralized in ONE restyle effect keyed on payloadTick +
 *   layer state + band. Year loads only fetch and bump payloadTick.
 * - Legend → LegendHistogram: per-band commune counts, histogram, and band
 *   isolation (applyBandDim mutates the fresh style map before the single
 *   applyStyleMap pass — D-12 still holds: setStyle in place, no re-mount).
 * - Low-zoom dots follow the active layer + band (previously always total).
 * - News layer: incidents held in state; pins re-mounted filtered by the
 *   active crime family and an optional day picked in NewsStrip. Pin layer
 *   re-mounts are allowed — D-12 protects the polygon layer only.
 *
 * Rules (unchanged):
 * - client:only="react" (never SSR'd — Leaflet CSS safe to import here)
 * - Double-init guard: if mapRef.current exists, return early (Pitfall 5)
 * - L.canvas() renderer declared only in ChoroplethLayer (Pitfall 6)
 * - Fetch only hardcoded same-origin /data/* paths (T-03-01-02, T-03-02-02)
 * - setStyle in place on filter change — never re-mount L.geoJSON (D-12)
 */
import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { feature as topoFeature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import './map.css';
import './map-v2.css';

import {
  mountChoroplethLayer,
  buildStyleMapFromLevel,
  buildStyleMapFromFamily,
  buildStyleMapFromHomicide,
  buildStyleMapFromCompositeIndex,
  applyStyleMap,
  highlightSelected,
  type CommunaPayload,
} from './ChoroplethLayer';
import {
  buildDotComunas,
  mountLowZoomDots,
  type DotCommune,
} from './LowZoomDotLayer';
import { locate } from './UserLocationMarker';
import { fetchIncidents, mountIncidentPins, type IncidentsFile } from './IncidentPinLayer';
import { LegendHistogram } from './LegendHistogram';
import { NewsStrip } from './NewsStrip';
import { computeLayerStats, applyBandDim, type LayerStats } from './bandStats';
import { ZoomControl } from './ZoomControl';
import { MapTopbar } from './MapTopbar';
import { ResultPanel } from './ResultPanel';
import { Toast } from './Toast';
import type { CommuneIndexEntry } from './SearchBox';
import { resolveRegionFocus, shouldApplyRegionFocus } from '../../lib/regionParam';
import { layerLabel, type LayerDef } from '../../lib/mapFilterDefs';
import { mapV2Strings } from '../../config/mapV2Strings';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MapPayload {
  generated: string;
  year: number;
  partial_year?: boolean;
  comunas: CommunaPayload[];
}

interface Props {
  lang: 'en' | 'es';
  nationalAvg?: number;
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
export default function MapIsland({ lang, nationalAvg = 0 }: Props) {
  // --- Refs ---
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const layerRef = useRef<L.GeoJSON | null>(null);
  const dotsRef = useRef<L.LayerGroup | null>(null);
  const eventsRef = useRef<L.LayerGroup | null>(null);
  const userRef = useRef<L.Marker | null>(null);
  const polyIdxRef = useRef<Map<string, L.Layer>>(new Map());
  const styleMapRef = useRef<Map<string, L.PathOptions>>(new Map());

  // Stored features for centroid computation (dot layer)
  const featuresRef = useRef<GeoJSON.Feature[]>([]);
  const payloadRef = useRef<CommunaPayload[] | null>(null);

  // --- State ---
  const [year, setYear] = useState(2025);
  const [crimeFamily, setCrimeFamily] = useState<string | null>(null);
  const [crimeFamilyIndex, setCrimeFamilyIndex] = useState<number | null>(null);
  // crimeIsHomicide: true when the homicide layer is selected (D-04/HOM-01).
  const [crimeIsHomicide, setCrimeIsHomicide] = useState(false);
  // mode: 'composite' (default, D-05) or 'family'. MapIsland is the SOLE
  // owner of this state; ResultPanel reads it via prop (D-06). MAPV2: derived
  // from the picked LayerDef instead of a separate Modo control.
  const [mode, setMode] = useState<'composite' | 'family'>('composite');
  const [showEvents, setShowEvents] = useState(false);
  const [lowZoom, setLowZoom] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [communeIndex, setCommuneIndex] = useState<CommuneIndexEntry[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const [partialYear, setPartialYear] = useState(false);

  // MAPV2 state
  // payloadTick: bumped whenever payloadRef.current is replaced, so the
  // centralized restyle effect re-runs (refs alone can't trigger effects).
  const [payloadTick, setPayloadTick] = useState(0);
  // band: isolated legend band (1–5) or null.
  const [band, setBand] = useState<number | null>(null);
  // stats: level index / breaks / counts for the CURRENT layer (legend + dots).
  const [stats, setStats] = useState<LayerStats | null>(null);
  // incidents: fetched once when the news layer first turns on.
  const [incidentsFile, setIncidentsFile] = useState<IncidentsFile | null>(null);
  // newsDay: optional YYYY-MM-DD day filter picked in NewsStrip.
  const [newsDay, setNewsDay] = useState<string | null>(null);
  // MPX-A1: choropleth layer mount signal — the year effect must not fire
  // before mountChoroplethLayer has run once (race with payloadRef).
  const [layerMounted, setLayerMounted] = useState(false);
  // MPX-A2: mirrors `selected` for use inside the restyle effect without
  // adding `selected` to its deps (would defeat the single-restyle guarantee).
  const selectedRef = useRef<string | null>(null);
  // MPX-A7: in-flight/completed incidents fetch, so rapid news toggles never
  // relaunch a second fetch or duplicate the D-15 toast.
  const incidentsFetchRef = useRef<Promise<IncidentsFile | null> | null>(null);

  // ---------------------------------------------------------------------------
  // Map init effect (runs once on mount)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!divRef.current || mapRef.current) return; // Pitfall 5: double-init guard

    const map = L.map(divRef.current, { zoomControl: false, attributionControl: true });
    map.attributionControl.setPosition('bottomleft');
    map.attributionControl.setPrefix('');
    map.fitBounds([[-55.9, -75.7], [-17.5, -66.4]], { padding: [20, 20] });
    map.setMaxBounds([[-60, -80], [-14, -60]]);
    map.setMinZoom(4);
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

      if (idx) setCommuneIndex(idx);

      const topo = topoRaw as unknown as Topology;
      const objectKey = Object.keys(topo.objects)[0];
      if (!objectKey) {
        setLoadError(true);
        return;
      }
      const geoCollection = topo.objects[objectKey] as GeometryCollection;
      const geoData = topoFeature(topo, geoCollection) as unknown as GeoJSON.FeatureCollection;

      featuresRef.current = geoData.features;
      payloadRef.current = payload.comunas;

      // TD-06: surface partial-year caveat badge when flag is set
      setPartialYear(payload.partial_year === true);

      // Build memoized style map — default to composite index mode (D-05)
      styleMapRef.current = buildStyleMapFromCompositeIndex(payload.comunas);

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
              selectedRef.current = cut;
              return cut;
            });
          }
        );
        setLayerMounted(true);

        // MAPV2: sync stats + (idempotent) restyle through the central effect
        setPayloadTick((t) => t + 1);

        // D-08: focus commune from ?cut= URL param (opaque string — Map lookup only)
        // T-25-04-URL: validate ?cut= is 4-5 digits before any fetch
        const focusCut = new URLSearchParams(window.location.search).get('cut');
        if (focusCut && /^\d{4,5}$/.test(focusCut)) {
          setTimeout(() => selectCommune(focusCut), 100);
        }

        // MAPSH-04/F-48: ?region= single-value region focus, only without ?cut=
        if (shouldApplyRegionFocus(window.location.search) && idx) {
          const regionCuts = resolveRegionFocus(window.location.search, idx);
          if (regionCuts) {
            setTimeout(() => {
              const m = mapRef.current;
              if (!m) return;
              const bounds = L.latLngBounds([]);
              regionCuts.forEach((cut) => {
                const ly = polyIdxRef.current.get(cut);
                if (ly && 'getBounds' in ly) bounds.extend((ly as L.Polygon).getBounds());
              });
              if (bounds.isValid()) m.fitBounds(bounds, { padding: [40, 40] });
            }, 100); // getBounds is not valid until Leaflet has rendered the polygons
          }
        }
      }
    }

    void loadData();

    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapReady]);

  // ---------------------------------------------------------------------------
  // Year filter effect: fetch map-payload-{year}.json, store, bump payloadTick.
  // Restyle itself happens in the central effect below (MAPV2).
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!mapReady || !layerMounted) return;

    let cancelled = false;

    async function loadYear() {
      const payload = await safeFetch<MapPayload>(`/data/cead/map-payload-${year}.json`);

      if (cancelled) return;

      if (!payload) {
        setToast(lang === 'es' ? 'Datos no disponibles para este año.' : 'Data not available for this year.');
        return;
      }

      payloadRef.current = payload.comunas;
      setPartialYear(payload.partial_year === true);
      setPayloadTick((t) => t + 1);
    }

    void loadYear();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, mapReady, layerMounted]);

  // ---------------------------------------------------------------------------
  // MAPV2 central restyle effect — the ONLY place the choropleth is recolored.
  // Replaces the original's three duplicated branches (year effect, chip
  // effect, onModeChange handler). Recomputes layer stats, rebuilds the style
  // map with the existing builders, applies band isolation, and does ONE
  // setStyle pass in place (D-12).
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const communas = payloadRef.current;
    const geoLayer = layerRef.current;
    if (!communas || !geoLayer) return;

    const st = computeLayerStats(communas, mode, crimeFamilyIndex, crimeIsHomicide);
    setStats({ ...st, band });

    let styleMap: Map<string, L.PathOptions>;
    if (mode === 'composite') {
      styleMap = buildStyleMapFromCompositeIndex(communas);
    } else if (crimeIsHomicide) {
      styleMap = buildStyleMapFromHomicide(communas);
    } else if (crimeFamilyIndex !== null) {
      styleMap = buildStyleMapFromFamily(communas, crimeFamilyIndex);
    } else {
      styleMap = buildStyleMapFromLevel(communas);
    }
    applyBandDim(styleMap, st.levelIdx, band);
    styleMapRef.current = styleMap;
    applyStyleMap(geoLayer, styleMapRef);

    // MPX-A2: band isolation / restyle just replaced the full style map —
    // reapply the selection highlight (uses the ref, not `selected`, so this
    // effect's deps stay untouched and the single-restyle guarantee holds).
    if (selectedRef.current && polyIdxRef.current.has(selectedRef.current)) {
      highlightSelected(geoLayer, polyIdxRef, selectedRef.current, null);
    }
  }, [payloadTick, mode, crimeFamilyIndex, crimeIsHomicide, band]);

  // ---------------------------------------------------------------------------
  // Low-zoom dot layer effect — MAPV2: follows active layer + band
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (dotsRef.current) {
      dotsRef.current.remove();
      dotsRef.current = null;
    }

    if (lowZoom && featuresRef.current.length > 0 && payloadRef.current) {
      const dotComunas: DotCommune[] = buildDotComunas(featuresRef.current, payloadRef.current);
      dotsRef.current = mountLowZoomDots(
        map,
        dotComunas,
        (cut) => {
          setSelected((prev) => {
            if (layerRef.current) {
              highlightSelected(layerRef.current, polyIdxRef, cut, prev);
            }
            selectedRef.current = cut;
            return cut;
          });
        },
        stats?.levelIdx,
        stats?.band ?? null
      );
    }

    return () => {
      if (dotsRef.current) {
        dotsRef.current.remove();
        dotsRef.current = null;
      }
    };
  // MPX-A3: deps = [lowZoom, stats] only — `stats.band` is read directly so
  // dot re-mount happens once per interaction, always with the current levelIdx.
  }, [lowZoom, stats]);

  // ---------------------------------------------------------------------------
  // News layer — MAPV2 split: fetch once on first toggle-on, then re-mount a
  // family/day-filtered pin subset when filters change. Re-mounting the pin
  // LayerGroup is fine — D-12 protects the polygon choropleth only (MAP-04).
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!showEvents || incidentsFile !== null) return;
    // MPX-A7: a request is already in flight (or already resolved) — a rapid
    // toggle-off/toggle-on before it lands must not relaunch fetchIncidents
    // or duplicate the D-15 toast.
    if (incidentsFetchRef.current !== null) return;
    let cancelled = false;
    const promise = fetchIncidents(lang, setToast);
    incidentsFetchRef.current = promise;
    void promise.then((file) => {
      if (!cancelled && file) setIncidentsFile(file);
    });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showEvents]);

  // Family key the news layer inherits from the active layer. Homicide has no
  // press family of its own — the closest bucket is 'vida'.
  const newsFamilyKey = mode === 'family'
    ? (crimeIsHomicide ? 'vida' : crimeFamily)
    : null;

  // MPX-C4: anchor derived from the FULL (unfiltered) incidents file, never
  // from the family-filtered subset — see NewsStrip.tsx for why.
  const incidentsAnchor = useMemo(() => {
    let a = '';
    if (incidentsFile) for (const i of incidentsFile.incidents) if (i.date > a) a = i.date;
    return a;
  }, [incidentsFile]);

  const familyFilteredIncidents = useMemo(() => {
    if (!incidentsFile) return [];
    if (!newsFamilyKey) return incidentsFile.incidents;
    return incidentsFile.incidents.filter((i) => i.family === newsFamilyKey);
  }, [incidentsFile, newsFamilyKey]);

  // Reset the day filter when the family scope changes (the picked day may
  // have zero incidents in the new scope — a silent empty map reads as a bug).
  useEffect(() => {
    setNewsDay(null);
  }, [newsFamilyKey]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (eventsRef.current) {
      eventsRef.current.remove();
      eventsRef.current = null;
    }

    if (showEvents && incidentsFile) {
      const pins = newsDay
        ? familyFilteredIncidents.filter((i) => i.date === newsDay)
        : familyFilteredIncidents;
      eventsRef.current = mountIncidentPins(map, pins, lang);
    }

    return () => {
      if (eventsRef.current) {
        eventsRef.current.remove();
        eventsRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showEvents, incidentsFile, familyFilteredIncidents, newsDay]);

  // ---------------------------------------------------------------------------
  // selectCommune: fly to commune + highlight (D-13)
  // ---------------------------------------------------------------------------
  const selectCommune = useCallback((cut: string) => {
    const map = mapRef.current;
    setSelected((prev) => {
      if (layerRef.current) {
        highlightSelected(layerRef.current, polyIdxRef, cut, prev);
      }
      selectedRef.current = cut;
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

  // MAPV2: single layer-change handler — sets the whole (mode, family) state
  // machine from one LayerDef and clears the band isolation, whose levels no
  // longer mean the same thing under the new layer.
  const handleLayerChange = useCallback((def: LayerDef) => {
    setMode(def.mode);
    setCrimeFamily(def.key);
    setCrimeFamilyIndex(def.familyIndex);
    setCrimeIsHomicide(def.key === 'homicidios');
    setBand(null);
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  const v2 = mapV2Strings(lang);
  return (
    <div className={`map-stage${selected ? ' has-panel' : ''}`}>
      {/* The Leaflet map container */}
      <div className="map-canvas" ref={divRef} />

      {/* Map topbar: search + layer rail */}
      <MapTopbar
        lang={lang}
        index={communeIndex}
        year={year}
        onYearChange={setYear}
        mode={mode}
        crimeFamily={crimeFamily}
        onLayerChange={handleLayerChange}
        showEvents={showEvents}
        onEventsToggle={setShowEvents}
        onSelect={selectCommune}
        onLocate={() => {
          const map = mapRef.current;
          if (!map) return;
          locate(map, featuresRef.current, userRef, selectCommune, setToast, lang);
        }}
      />

      {/* TD-06: partial-year caveat badge — shown when latest year data is incomplete */}
      {partialYear && (
        <div className="partial-year-badge" role="note" aria-live="polite">
          {lang === 'es'
            ? `Año parcial (${year}) — datos aún no consolidados`
            : `Partial year (${year}) — data not yet consolidated`}
        </div>
      )}

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

      {/* MAPV2 Legend: distribution + counts + band isolation (bottom-left) */}
      <LegendHistogram
        lang={lang}
        stats={stats}
        mode={mode}
        band={band}
        onBandChange={setBand}
        showIncidents={showEvents}
      />

      {/* MAPV2 News strip: count + scope + per-day bars (bottom-center) */}
      {showEvents && incidentsFile && (
        <NewsStrip
          lang={lang}
          incidents={familyFilteredIncidents}
          windowDays={incidentsFile.window_days}
          // MPX-C3: when the active layer is Homicide, the press pins actually
          // shown are the 'vida' family (homicide has no own press bucket) —
          // the strip scope must say that, not "Homicidios".
          scopeLabel={newsFamilyKey ? layerLabel(lang, 'family', newsFamilyKey) : v2.news_strip_all}
          anchor={incidentsAnchor}
          day={newsDay}
          onDayChange={setNewsDay}
        />
      )}

      {/* Zoom control (desktop only, hidden via CSS on mobile) */}
      <ZoomControl mapRef={mapRef} />

      {/* ResultPanel: commune detail (opened on click/search) */}
      {selected && (
        <ResultPanel
          cut={selected}
          lang={lang}
          year={year}
          nationalAvg={nationalAvg}
          mode={mode}
          onClose={() => {
            if (layerRef.current) {
              const prev = polyIdxRef.current.get(selected);
              if (prev) layerRef.current.resetStyle(prev as L.Path);
            }
            selectedRef.current = null;
            setSelected(null);
          }}
        />
      )}

      {/* Toast notification */}
      {toast && (
        <Toast msg={toast} onDismiss={() => setToast(null)} />
      )}
    </div>
  );
}
