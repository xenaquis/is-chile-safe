# Phase 3: Leaflet Map Island — Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 20
**Analogs found:** 20 / 20

---

## File Classification

| New / Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------|------|-----------|----------------|---------------|
| `site/src/components/map/MapIsland.tsx` | component (island root) | event-driven | `ischilesafe.com/map-view.jsx` (MapView fn) | exact |
| `site/src/components/map/MapTopbar.tsx` | component | event-driven | `ischilesafe.com/map-view.jsx` (`.map-topbar` block, lines 284–299) | exact |
| `site/src/components/map/SearchBox.tsx` | component | request-response | `ischilesafe.com/components.jsx` SearchBox (lines 63–101) | exact |
| `site/src/components/map/FiltersRow.tsx` | component | event-driven | `ischilesafe.com/map-view.jsx` `.filters-row` block (lines 291–299) | exact |
| `site/src/components/map/ZoomControl.tsx` | component | event-driven | `ischilesafe.com/map-view.jsx` `.zoom-ctl` block (lines 303–306) | exact |
| `site/src/components/map/Legend.tsx` | component | transform | `ischilesafe.com/components.jsx` Legend fn (lines 103–117) | exact |
| `site/src/components/map/ResultPanel.tsx` | component | request-response | `ischilesafe.com/map-view.jsx` ResultPanel fn (lines 2–98) | exact |
| `site/src/components/map/PanelSparkline.tsx` | component | transform | `site/src/components/Sparkline.astro` | exact |
| `site/src/components/map/PanelFamilyBars.tsx` | component | transform | `site/src/components/FamilyBreakdownBars.astro` | exact |
| `site/src/components/map/IncidentsList.tsx` | component | request-response | `ischilesafe.com/map-view.jsx` events section (lines 63–77) | role-match |
| `site/src/components/map/Toast.tsx` | component | event-driven | `ischilesafe.com/components.jsx` Toast fn (lines 152–155) | exact |
| `site/src/components/map/ChoroplethLayer.ts` | hook/utility | event-driven | `ischilesafe.com/map-view.jsx` choropleth useEffect (lines 197–231) | exact |
| `site/src/components/map/LowZoomDotLayer.ts` | hook/utility | event-driven | `ischilesafe.com/map-view.jsx` low-zoom useEffect (lines 234–253) | exact |
| `site/src/components/map/IncidentPinLayer.ts` | hook/utility | event-driven | `ischilesafe.com/map-view.jsx` events useEffect (lines 256–278) | exact |
| `site/src/components/map/UserLocationMarker.ts` | hook/utility | event-driven | `ischilesafe.com/map-view.jsx` locate() fn (lines 136–162) | exact |
| `site/src/components/map/map.css` | config | — | `ischilesafe.com/map-view.jsx` + `site/src/components/FamilyBreakdownBars.astro` CSS blocks | role-match |
| `site/src/pages/map.astro` | page/route | request-response | `site/src/pages/commune/[slug].astro` | role-match |
| `site/src/pages/es/mapa.astro` | page/route | request-response | `site/src/pages/commune/[slug].astro` | role-match |
| `site/astro.config.mjs` | config | — | `site/astro.config.mjs` (modify existing) | exact |
| `site/scripts/validate/map-pages.mjs` | utility/test | CRUD | `site/scripts/validate/structure.mjs` | exact |

---

## Pattern Assignments

### `site/src/components/map/MapIsland.tsx` (island root, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` — MapView function (lines 100–322)

**Imports pattern** — port these imports; add TypeScript types:
```tsx
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import * as topojson from 'topojson-client';
import chroma from 'chroma-js';
// Do NOT import from site/src/lib/colorScale.ts — that is Node-only (see RESEARCH Pitfall 3)
```

**Refs pattern** (lines 103–110 of prototype, adapted):
```tsx
const divRef = useRef<HTMLDivElement>(null);
const mapRef = useRef<L.Map | null>(null);
const tileRef = useRef<L.TileLayer | null>(null);
const layerRef = useRef<L.GeoJSON | null>(null);
const dotsRef = useRef<L.LayerGroup | null>(null);
const eventsRef = useRef<L.LayerGroup | null>(null);
const userRef = useRef<L.Marker | null>(null);
const polyIdxRef = useRef<Map<string, L.Layer>>(new Map());
const styleMapRef = useRef<Map<string, L.PathOptions>>(new Map());
```

**State pattern** (lines 112–116):
```tsx
const [year, setYear] = useState(2025);          // latestCompleteYear
const [lowZoom, setLowZoom] = useState(true);
const [crimeFamily, setCrimeFamily] = useState<string | null>(null); // null = todos
const [showEvents, setShowEvents] = useState(false);
const [selected, setSelected] = useState<string | null>(null);       // CUT code
```

**Map init useEffect** (lines 165–183 of prototype, ported to TypeScript):
```tsx
useEffect(() => {
  if (!divRef.current || mapRef.current) return;         // Pitfall 5: double-init guard
  const map = L.map(divRef.current, { zoomControl: false, attributionControl: true });
  map.attributionControl.setPosition('bottomleft');
  map.attributionControl.setPrefix('');
  map.setView([-35.7, -71.8], 5);
  map.on('zoomend', () => setLowZoom(map.getZoom() < 8));
  mapRef.current = map;
  return () => { map.remove(); mapRef.current = null; }; // Pitfall 5: cleanup
}, []);
```

**CARTO Positron tile pattern** (lines 186–194, D-08):
```tsx
useEffect(() => {
  const map = mapRef.current;
  if (!map) return;
  if (tileRef.current) tileRef.current.remove();
  tileRef.current = L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    { attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19, crossOrigin: true }
  ).addTo(map);
}, []);
```

**flyTo / selectCommune pattern** (lines 118–134, adapted for CUT-keyed data):
```tsx
function selectCommune(cut: string, fly = true) {
  setSelected(cut);
  const map = mapRef.current;
  if (!map || !fly) return;
  const ly = polyIdxRef.current.get(cut);
  if (ly && 'getBounds' in ly) {
    const desktop = window.innerWidth > 640;
    map.flyToBounds((ly as L.Polygon).getBounds(), {
      paddingTopLeft: desktop ? [60, 120] : [30, 130],
      paddingBottomRight: desktop ? [410, 40] : [30, 30],
      maxZoom: 12, duration: 0.7,
    });
  }
}
```

**JSX return structure** (lines 281–320, renamed classes):
```tsx
return (
  <div className={`map-stage${selected ? ' has-panel' : ''}`}>
    <div className="map-canvas" ref={divRef} />
    <MapTopbar lang={lang} year={year} onYearChange={setYear}
               crimeFamily={crimeFamily} onFamilyChange={setCrimeFamily}
               showEvents={showEvents} onEventsToggle={setShowEvents}
               onSelect={selectCommune} onLocate={locate} />
    <ZoomControl mapRef={mapRef} />
    <Legend lang={lang} />
    {selected && (
      <ResultPanel cut={selected} lang={lang} year={year}
                   onClose={() => setSelected(null)}
                   onLocatePage={(slug) => { /* link to /commune/{slug}/ */ }} />
    )}
    {toast && <Toast msg={toast} onDismiss={() => setToast(null)} />}
  </div>
);
```

---

### `site/src/components/map/ChoroplethLayer.ts` (useEffect hook, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` choropleth useEffect (lines 197–231) + RESEARCH Pattern 3

**Core layer creation pattern** (D-05, D-16 — native L.geoJSON + L.canvas):
```typescript
// Called once geoData is loaded; never called again on filter change
export function mountChoroplethLayer(
  map: L.Map,
  geoData: GeoJSON.FeatureCollection,
  styleMapRef: React.MutableRefObject<Map<string, L.PathOptions>>,
  polyIdxRef: React.MutableRefObject<Map<string, L.Layer>>,
  onClickCut: (cut: string) => void
): L.GeoJSON {
  const renderer = L.canvas();                             // D-16: canvas renderer
  const layer = L.geoJSON(geoData, {
    renderer,
    style: (f) => styleMapRef.current.get(f!.properties.id as string) ?? DEFAULT_STYLE,
    onEachFeature: (f, ly) => {
      const cut = f.properties.id as string;
      ly.bindTooltip(f.properties.name as string, { sticky: true, direction: 'top' });
      ly.on('click', () => onClickCut(cut));
      ly.on('mouseover', () => {
        // Prototype lines 223-225: only hover-style non-selected
        ly.setStyle({ fillOpacity: 0.74, weight: 1.8 });
      });
      ly.on('mouseout', () => layer.resetStyle(ly));
      polyIdxRef.current.set(cut, ly);
    },
  }).addTo(map);
  return layer;
}
```

**setStyle in-place pattern** (D-12 — never re-mount):
```typescript
// Called on every year or crime-family filter change
export function applyStyleMap(
  layer: L.GeoJSON,
  styleMapRef: React.MutableRefObject<Map<string, L.PathOptions>>
): void {
  layer.setStyle((f) => styleMapRef.current.get(f!.properties.id as string) ?? DEFAULT_STYLE);
}
```

**Style map construction** (RESEARCH Pattern 8 — chroma-js client-side):
```typescript
import chroma from 'chroma-js';

export const INCIDENCE_COLORS = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);

// "todos" view: use precomputed level from map-payload (D-11)
export function buildStyleMapFromLevel(
  comunas: Array<{ id: string; level: 1|2|3|4|5 }>
): Map<string, L.PathOptions> {
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[c.level - 1]!,
      fillOpacity: 0.55, color: '#ffffff', weight: 1.2,
    });
  }
  return m;
}

// Per-family view: compute quantile breaks client-side (D-11)
export function buildStyleMapFromFamily(
  comunas: Array<{ id: string; by_family: number[] }>,
  familyIndex: number
): Map<string, L.PathOptions> {
  const rates = comunas.map(c => c.by_family[familyIndex] ?? 0);
  const breaks = computeQuantileBreaks(rates.filter(r => r > 0), 5);
  const m = new Map<string, L.PathOptions>();
  for (const c of comunas) {
    const rate = c.by_family[familyIndex] ?? 0;
    const level = levelFromBreaks(rate, breaks);
    m.set(c.id, {
      fillColor: INCIDENCE_COLORS[level - 1]!,
      fillOpacity: 0.55, color: '#ffffff', weight: 1.2,
    });
  }
  return m;
}

function computeQuantileBreaks(sorted: number[], classes: number): number[] {
  const s = [...sorted].sort((a, b) => a - b);
  return Array.from({ length: classes - 1 }, (_, i) =>
    s[Math.floor((s.length * (i + 1)) / classes)] ?? 0
  );
}
```

**Selected-state highlight** (lines 229 of prototype + UI-SPEC interaction states):
```typescript
// After setting selected cut — bringToFront + restyle border
export function highlightSelected(
  layer: L.GeoJSON,
  polyIdxRef: React.MutableRefObject<Map<string, L.Layer>>,
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
```

---

### `site/src/components/map/LowZoomDotLayer.ts` (useEffect hook, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` low-zoom useEffect (lines 234–253)

**Core pattern** — copy directly, add TypeScript types:
```typescript
export function mountLowZoomDots(
  map: L.Map,
  comunas: Array<{ id: string; lat: number; lng: number; name: string; level: 1|2|3|4|5 }>,
  onClickCut: (cut: string) => void
): L.LayerGroup {
  const layer = L.layerGroup();
  for (const c of comunas) {
    L.circleMarker([c.lat, c.lng], {
      radius: 4.5 + c.level * 1.1,                        // UI-SPEC: exact formula
      color: '#ffffff', weight: 1.2,
      fillColor: INCIDENCE_COLORS[c.level - 1]!,
      fillOpacity: 0.92,
    })
      .bindTooltip(c.name, { direction: 'top', offset: [0, -8] })
      .on('click', () => onClickCut(c.id))
      .addTo(layer);
  }
  return layer.addTo(map);
}
```

NOTE: circleMarker uses Leaflet's built-in canvas/SVG path — DO NOT set `renderer: L.canvas()` globally (Pitfall 6). The L.canvas() renderer is declared only on the L.geoJSON choropleth layer.

---

### `site/src/components/map/IncidentPinLayer.ts` (useEffect hook, request-response)

**Primary analog:** `ischilesafe.com/map-view.jsx` events useEffect (lines 256–278)

**Graceful empty-state pattern** (D-15):
```typescript
export async function fetchAndMountIncidents(
  map: L.Map,
  lang: 'en' | 'es',
  onToast: (msg: string) => void
): Promise<L.LayerGroup | null> {
  let data: IncidentsFile;
  try {
    const res = await fetch('/data/incidents/current.json');
    if (!res.ok) {
      // 404 = Phase 5 not yet deployed — graceful empty state
      onToast(lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon');
      return null;
    }
    data = await res.json() as IncidentsFile;
  } catch {
    onToast(lang === 'es' ? 'Capa de noticias próximamente' : 'News layer coming soon');
    return null;
  }

  const layer = L.layerGroup();
  for (const e of data.incidents) {
    const title = lang === 'es' ? e.title_es : e.title_en;
    const html = `<div class="ev-pop">
      <div class="ev-badges"><span>CEAD</span><span>${lang === 'es' ? 'Ubicación aproximada' : 'Approx. location'}</span></div>
      <strong>${title}</strong>
      <div class="ev-meta">${e.date} · ${e.outlet}</div>
      <div class="ev-meta"><a href="${e.url}" target="_blank" rel="noopener noreferrer">${lang === 'es' ? 'Fuente' : 'Source'}: ${e.outlet}</a></div>
    </div>`;
    // Prototype lines 272-274: L.divIcon ev-dot
    L.marker([e.lat, e.lng], {
      icon: L.divIcon({ className: '', html: '<div class="ev-dot"></div>', iconSize: [14, 14], iconAnchor: [7, 7] }),
    }).bindPopup(html, { closeButton: false, offset: [0, -4] }).addTo(layer);
    // SECURITY: html above uses JSX-equivalent escaping — never dangerouslySetInnerHTML with e.title_es
  }
  return layer.addTo(map);
}
```

---

### `site/src/components/map/UserLocationMarker.ts` (useEffect hook, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` locate() function (lines 136–162)

**Core geolocation pattern** (adapted: centroid-distance → point-in-polygon per D-14):
```typescript
export function locate(
  map: L.Map,
  geoFeatures: GeoJSON.Feature[],
  userRef: React.MutableRefObject<L.Marker | null>,
  onSelectCut: (cut: string) => void,
  onToast: (msg: string) => void,
  lang: 'en' | 'es'
): void {
  function finish(lat: number, lng: number, simulated: boolean) {
    if (userRef.current) { userRef.current.remove(); }
    // Prototype lines 143-144: L.divIcon user-dot
    userRef.current = L.marker([lat, lng], {
      icon: L.divIcon({
        className: '',
        html: '<div class="user-dot"></div>',
        iconSize: [18, 18], iconAnchor: [9, 9],
      }),
    }).bindTooltip(lang === 'es' ? 'Mi ubicación' : 'My location', { direction: 'top', offset: [0, -10] })
      .addTo(map);

    // D-14: point-in-polygon (not centroid distance like prototype)
    const cut = pointInPolygon(lat, lng, geoFeatures);
    if (cut) onSelectCut(cut);
    map.flyTo([lat, lng], 12, { duration: 0.8 });
    const name = cut ?? 'Santiago';
    onToast(simulated
      ? (lang === 'es' ? 'Ubicación aproximada: Santiago' : 'Approx. location: Santiago')
      : (lang === 'es' ? `Tu comuna: ${name}` : `Your commune: ${name}`)
    );
  }

  const simulate = () => finish(-33.44, -70.65, true);

  // Prototype lines 151-161: geolocation + Chile bounds check
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const { latitude: la, longitude: lo } = p.coords;
        if (la < -17 && la > -56.5 && lo < -66 && lo > -76.5) finish(la, lo, false);
        else simulate();
      },
      () => {
        onToast(lang === 'es' ? 'No se pudo obtener tu ubicación' : 'Location access denied');
      },
      { timeout: 5000 }
    );
  } else {
    simulate();
  }
}
```

**Point-in-polygon** (RESEARCH Pattern 5 — replaces prototype's centroid-distance `nearestComuna`):
```typescript
function pointInPolygon(lat: number, lng: number, features: GeoJSON.Feature[]): string | null {
  const pt: [number, number] = [lng, lat];
  for (const f of features) {
    if (containsPoint(f.geometry, pt)) return f.properties!.id as string;
  }
  return null;
}
```

---

### `site/src/components/map/SearchBox.tsx` (component, request-response)

**Primary analog:** `ischilesafe.com/components.jsx` SearchBox (lines 63–101)

**Import of inline SVG icons** (from `ischilesafe.com/components.jsx` lines 41–61):
```tsx
// Port these as island-internal constants (UI-SPEC: inline SVG only, no icon lib)
function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.8" />
      <line x1="12.2" y1="12.2" x2="16" y2="16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}
```

**Search pattern** (lines 63–101, adapted to use index array instead of window.CSM):
```tsx
interface SearchBoxProps {
  index: Array<{ id: string; name: string; region: string; slug: string }>;
  lang: 'en' | 'es';
  onSelect: (cut: string) => void;
  onLocate: () => void;
}

export function SearchBox({ index, lang, onSelect, onLocate }: SearchBoxProps) {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const results = q.trim()
    ? index.filter(c => c.name.toLowerCase().startsWith(q.toLowerCase())).slice(0, 8)
    : [];
  // ... rest mirrors prototype lines 68–100: pick(), input handlers, dropdown
}
```

---

### `site/src/components/map/FiltersRow.tsx` (component, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` `.filters-row` block (lines 291–299)

**Year select pattern** (line 291–293):
```tsx
<select
  className="chip select"
  value={year}
  onChange={(e) => onYearChange(Number(e.target.value))}
  aria-label={lang === 'es' ? 'Filtrar por año' : 'Filter by year'}
>
  {AVAILABLE_YEARS.map(y => <option key={y} value={y}>{y}</option>)}
</select>
```

**Crime-type chips pattern** (lines 294–297, adapted for 9 chips including "todos"):
```tsx
{CHIP_DEFS.map(({ key, labelEs, labelEn }) => (
  <button
    key={key}
    className={`chip${crimeFamily === key ? ' active' : ''}`}
    onClick={() => onFamilyChange(crimeFamily === key ? null : key)}
  >
    {lang === 'es' ? labelEs : labelEn}
  </button>
))}
```

CHIP_DEFS order per UI-SPEC: null (todos), vida, propiedad, robos_violentos, incivilidades, vif, drogas, armas. Family index mapping comes from `catalog.json` `family_keys` array, NOT chip order.

**Events toggle chip pattern** (lines 298–300):
```tsx
<button
  className={`chip ev-chip${showEvents ? ' active' : ''}`}
  onClick={() => onEventsToggle(!showEvents)}
>
  <span className="ev-dot-mini" />
  {lang === 'es' ? 'Noticias recientes' : 'Recent incidents'}
</button>
```

---

### `site/src/components/map/Legend.tsx` (component, transform)

**Primary analog:** `ischilesafe.com/components.jsx` Legend (lines 103–117)

**Pattern** — direct TypeScript port:
```tsx
export function Legend({ lang }: { lang: 'en' | 'es' }) {
  return (
    <div className="legend">
      <div className="legend-title">{lang === 'es' ? 'Incidencia reportada' : 'Reported incidence'}</div>
      <div className="legend-swatches">
        {INCIDENCE_COLORS.map((c, i) => <span key={i} style={{ background: c }} />)}
      </div>
      <div className="legend-labels">
        <span>{lang === 'es' ? 'Baja' : 'Low'}</span>
        <span>{lang === 'es' ? 'Alta' : 'High'}</span>
      </div>
      <div className="legend-unit">
        {lang === 'es' ? 'Tasa por 100.000 hab.' : 'Rate per 100,000 inhab.'}
      </div>
    </div>
  );
}
```

---

### `site/src/components/map/ResultPanel.tsx` (component, request-response)

**Primary analog:** `ischilesafe.com/map-view.jsx` ResultPanel (lines 2–98)

**Data fetch pattern** (D-13 — fetch on open, not bundled):
```tsx
export function ResultPanel({ cut, lang, year, onClose }: ResultPanelProps) {
  const [data, setData] = useState<CommuneData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setData(null);
    fetch(`/data/cead/comunas/${cut}.json`)
      .then(r => r.json())
      .then((d: CommuneData) => { setData(d); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, [cut]);
  // ...
}
```

**Panel head pattern** (prototype lines 14–22, keep close button):
```tsx
<aside className="result-panel">
  <div className="panel-head">
    <div>
      <h2>{data.name}</h2>
      <div className="panel-region">{data.regionName}</div>
    </div>
    <button className="panel-close" onClick={onClose} aria-label="Cerrar">×</button>
  </div>
  {/* LevelChip + CEAD badge */}
  {/* PanelStatCard (rate, 28px/700) */}
  {/* mini-stats row (trend + rank) */}
  {/* PanelSparkline */}
  {/* PanelFamilyBars */}
  {/* IncidentsList */}
  {/* CTA: Ver ficha completa → /commune/{slug}/ */}
  {/* official-row checkmark + CEAD attribution */}
</aside>
```

**Skeleton loading pattern** (UI-SPEC — show on fetch, not blank):
```tsx
if (loading) {
  return (
    <aside className="result-panel" aria-busy="true"
           aria-label={lang === 'es' ? 'Cargando datos de la comuna' : 'Loading commune data'}>
      <div className="skeleton" style={{ height: 28 }} />
      <div className="skeleton" style={{ height: 14, width: '60%' }} />
      <div className="skeleton" style={{ height: 44 }} />
    </aside>
  );
}
```

**stat-card pattern** (prototype lines 27–31):
```tsx
<div className="stat-card">
  <div className="stat-big">~{rate.toLocaleString('es-CL')}</div>
  <div className="stat-unit">
    {lang === 'es' ? `Tasa por 100.000 hab. (${year})` : `Rate per 100,000 inhab. (${year})`}
  </div>
</div>
```

**family bars section** (prototype lines 51–59 — adapted for 7 families using `by_family[]` from latest series entry):
```tsx
<div className="panel-section">
  <h4>{lang === 'es' ? `Incidencia por categoría (${year})` : `Incidence by category (${year})`}</h4>
  <PanelFamilyBars byFamily={latestEntry.by_family} locale={lang} level={level} />
</div>
```

**CTA button** (prototype line 95):
```tsx
<a href={`${lang === 'es' ? '/es/comuna/' : '/commune/'}${data.slug}/`}
   className="btn primary full">
  {lang === 'es' ? 'Ver ficha completa' : 'View full profile'}
</a>
```

---

### `site/src/components/map/PanelSparkline.tsx` (component, transform)

**Primary analog:** `site/src/components/Sparkline.astro` (full file, 60 lines) — direct React port

**Port pattern** (RESEARCH Pattern 6 — mirrors Sparkline.astro contract exactly):
```tsx
interface Props {
  series: Array<{ year: number; rate_per_100k: number; partial?: boolean }>;
  activeYear?: number;
  primaryColor?: string;
}

export function PanelSparkline({ series, activeYear, primaryColor = '#0f766e' }: Props) {
  const maxRate = Math.max(...series.map(s => s.rate_per_100k), 1);
  const width = 480;
  const height = 44;
  // Mirror Sparkline.astro WR-05: derive step from width so bars never overflow
  const step = series.length > 0 ? width / series.length : 8;
  const barW = Math.max(1, step - 1);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height}
         style={{ width: '100%', height: 'auto', overflow: 'visible' }}
         aria-hidden="true" className="sparkline">
      {series.map((s, i) => {
        const barH = Math.max(2, Math.round((s.rate_per_100k / maxRate) * height));
        return (
          <rect key={i}
                x={i * step} y={height - barH}
                width={barW} height={barH} rx="2"
                fill={s.year === activeYear ? primaryColor : 'var(--muted)'}
                opacity={s.partial ? 0.5 : 1} />
        );
      })}
    </svg>
  );
}
```

Key differences from Sparkline.astro: uses `primaryColor` prop instead of CSS `var(--primary)` (so the active bar color can be passed from React state); width/step logic mirrors Astro version exactly (WR-05 fix).

---

### `site/src/components/map/PanelFamilyBars.tsx` (component, transform)

**Primary analog:** `site/src/components/FamilyBreakdownBars.astro` (full file, 144 lines) — React port

**Family order and label constants** (port from FamilyBreakdownBars.astro lines 35–56):
```tsx
const FAMILY_ORDER = ['vida', 'propiedad', 'robos_violentos', 'incivilidades', 'vif', 'drogas', 'armas'] as const;
const FEATURED = new Set(['vida', 'propiedad']);
const FAMILY_LABELS: Record<string, { en: string; es: string }> = {
  vida:            { en: 'Life crimes',       es: 'Delitos contra la vida' },
  propiedad:       { en: 'Property crimes',   es: 'Delitos contra la propiedad' },
  robos_violentos: { en: 'Violent robbery',   es: 'Robos violentos' },
  incivilidades:   { en: 'Disorder',          es: 'Incivilidades' },
  vif:             { en: 'Domestic violence', es: 'Violencia intrafamiliar' },
  drogas:          { en: 'Drug crimes',       es: 'Drogas' },
  armas:           { en: 'Weapons',           es: 'Armas' },
};
```

**Props interface** (mirrors FamilyBreakdownBars.astro interface, lines 15–29):
```tsx
interface Props {
  byFamily: number[];          // 7-element array indexed per catalog.json family_keys order
  locale: 'en' | 'es';
  level: 1 | 2 | 3 | 4 | 5;
}
```

NOTE: Astro version takes `byFamily: ByFamily` (record by key). The React version receives `byFamily: number[]` from map-payload's `by_family` array and must map index → key using `catalog.json` `family_keys` order (0=vida, 1=robos_violentos, 2=vif, 3=drogas, 4=armas, 5=propiedad, 6=incivilidades). Reorder to FAMILY_ORDER after the index mapping.

**Bar width pattern** (FamilyBreakdownBars.astro line 64 — critical: always a CSS `%` string):
```tsx
const widthPct = Math.round((val / max) * 100) + '%';
// ...
<span className="family-bar-fill" style={{ width: widthPct, background: `var(--s${level})` }} />
```

**Accent dot for featured families** (FamilyBreakdownBars.astro lines 71–79):
```tsx
<span className={`family-bar-label${featured ? ' featured' : ''}`}>
  {featured && <span className="accent-dot" aria-hidden="true" />}
  {label}
</span>
```

---

### `site/src/components/map/Toast.tsx` (component, event-driven)

**Primary analog:** `ischilesafe.com/components.jsx` Toast (lines 152–155)

**Pattern** (extend with auto-dismiss and aria-live):
```tsx
export function Toast({ msg, onDismiss }: { msg: string; onDismiss: () => void }) {
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
```

---

### `site/src/components/map/ZoomControl.tsx` (component, event-driven)

**Primary analog:** `ischilesafe.com/map-view.jsx` `.zoom-ctl` block (lines 303–306)

**Pattern** (direct port with aria-labels):
```tsx
export function ZoomControl({ mapRef }: { mapRef: React.RefObject<L.Map | null> }) {
  return (
    <div className="zoom-ctl">
      <button onClick={() => mapRef.current?.zoomIn()} aria-label="Zoom in">+</button>
      <button onClick={() => mapRef.current?.zoomOut()} aria-label="Zoom out">−</button>
    </div>
  );
}
```

Hide on mobile via CSS: `.zoom-ctl { display: none; } @media (min-width: 640px) { .zoom-ctl { display: flex; } }`.

---

### `site/src/components/map/IncidentsList.tsx` (component, request-response)

**Primary analog:** `ischilesafe.com/map-view.jsx` events section in ResultPanel (lines 63–77)

**Pattern** (adapt from prototype; data now comes from commune JSON incidents field):
```tsx
export function IncidentsList({ incidents, lang }: IncidentsListProps) {
  if (!incidents || incidents.length === 0) {
    return <p className="panel-muted">—</p>;
  }
  return (
    <>
      {incidents.map(e => (
        <div className="event-row" key={e.id}>
          <div className="event-title">{lang === 'es' ? e.title_es : e.title_en}</div>
          <div className="event-meta">{e.date} · {e.outlet}</div>
          {/* SECURITY: external link must use rel="noopener noreferrer" */}
          <a href={e.url} target="_blank" rel="noopener noreferrer" className="event-source">
            {lang === 'es' ? 'Fuente' : 'Source'}: {e.outlet}
          </a>
        </div>
      ))}
    </>
  );
}
```

---

### `site/src/pages/map.astro` and `site/src/pages/es/mapa.astro` (routes, request-response)

**Primary analog:** `site/src/pages/commune/[slug].astro` (lines 1–60)

**Imports pattern** — no getStaticPaths needed (single static page); import layout + island:
```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import MapIsland from '../../components/map/MapIsland';
// Note: MapIsland imported WITHOUT .tsx extension; Astro resolves it
---
```

**Island mount pattern** (D-06 — client:only="react"):
```astro
<BaseLayout title="Chile Crime Map — Interactive" ...>
  <MapIsland client:only="react" lang="en" />
</BaseLayout>
```

**hreflang pattern** (matches `commune/[slug].astro` convention — inject in BaseLayout or page head):
```astro
<link rel="alternate" hreflang="en" href="https://ischilesafe.com/map/" />
<link rel="alternate" hreflang="es" href="https://ischilesafe.com/es/mapa/" />
<link rel="alternate" hreflang="x-default" href="https://ischilesafe.com/map/" />
```

Map pages do NOT use `getStaticPaths` — they are single static routes.

---

### `site/astro.config.mjs` (config — modify existing)

**Analog:** `site/astro.config.mjs` itself (lines 1–95) — extend, do not replace

**React integration addition** (RESEARCH Pattern 1):
```javascript
import react from '@astrojs/react';         // ADD at top

export default defineConfig({
  // ... site, i18n unchanged ...
  integrations: [
    react(),                                 // ADD — before sitemap
    sitemap({ /* existing config unchanged */ }),
  ],
  // ... vite unchanged ...
});
```

**Sitemap filter extension** — add map pages to the always-include list (alongside home, region, crime pages):
```javascript
// In sitemapFilter(), add before the "All other pages" fallback:
if (url === 'https://ischilesafe.com/map/' || url === 'https://ischilesafe.com/es/mapa/') {
  return true;
}
```

---

### `site/scripts/validate/map-pages.mjs` (validator, CRUD)

**Primary analog:** `site/scripts/validate/structure.mjs` (full file pattern)

**Imports and path setup pattern** (structure.mjs lines 1–17):
```javascript
import assert from 'node:assert/strict';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../..');
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');
```

**Early-exit pattern if dist/ absent** (structure.mjs lines 42–45):
```javascript
if (!existsSync(DIST_DIR)) {
  console.log('map-pages: dist/ not found — skipping HTML checks');
  process.exit(0);
}
```

**Assertions to implement** (from RESEARCH validation table):
```javascript
// MAP-01: /map/ and /es/mapa/ pages exist
assert.ok(existsSync(path.join(DIST_DIR, 'map', 'index.html')), 'dist/map/index.html missing');
assert.ok(existsSync(path.join(DIST_DIR, 'es', 'mapa', 'index.html')), 'dist/es/mapa/index.html missing');

// MAP-01: TopoJSON asset present and < 100 KB
const topoPath = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes.topo.json');
assert.ok(existsSync(topoPath), 'data/cead/geo/communes.topo.json missing');
const topoSize = statSync(topoPath).size;
assert.ok(topoSize < 102400, `communes.topo.json is ${topoSize} bytes — must be < 100 KB`);

// MAP-01: island script tag present in map page HTML
const mapHtml = readFileSync(path.join(DIST_DIR, 'map', 'index.html'), 'utf-8');
// client:only island emits a <script> or astro-island element
assert.ok(
  mapHtml.includes('astro-island') || mapHtml.includes('MapIsland'),
  'map page missing island mount'
);

// MAP-05: geolocation aria-label present in EN page
assert.ok(
  mapHtml.includes('Show my location') || mapHtml.includes('Mostrar mi ubicaci'),
  'map page missing locate button aria-label'
);
```

**Register in all.mjs** — add `'map-pages.mjs'` to the VALIDATORS array (structure.mjs pattern for registration).

---

### `data/cead/geo/communes.topo.json` (static asset, file-I/O)

**No code analog** — produced by the offline mapshaper pipeline (RESEARCH Pattern 4). This is a committed binary-ish JSON file, not a TypeScript file with patterns to copy.

**Pipeline command** (exact sequence from RESEARCH Pattern 4):
```bash
# Step 1: extract GeoJSON from JS wrapper
node -e "const s=require('fs').readFileSync('ischilesafe.com/geo-data.js','utf8'); \
  const m=s.match(/=\s*(\{[\s\S]+\})\s*;?\s*$/); \
  require('fs').writeFileSync('/tmp/communes-raw.geojson', m[1]);"

# Step 2: simplify + convert
mapshaper /tmp/communes-raw.geojson \
  -simplify visvalingam percentage=12% keep-shapes \
  -o format=topojson /tmp/communes.topo.json

# Step 3: verify size; adjust percentage if > 100 KB
# Step 4: commit to data/cead/geo/communes.topo.json
```

Join key: `feature.properties.id` = CUT string (verified from prototype `map-view.jsx` line 207).

---

## Shared Patterns

### 1. Incidence Color Constants

**Source:** `site/src/lib/colorScale.ts` (lines 10–13) — but do NOT import in island
**Apply to:** `ChoroplethLayer.ts`, `LowZoomDotLayer.ts`, `Legend.tsx`, `PanelSparkline.tsx`, `PanelFamilyBars.tsx`

```typescript
// Duplicate this constant directly in each island file that needs it
// Do NOT import from colorScale.ts — that module is Node-only
import chroma from 'chroma-js';
export const INCIDENCE_COLORS = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);
```

Alternatively, define once in a thin `site/src/components/map/colors.ts` (island-internal, no Node deps) and import from there. This avoids duplicating the constant across 5 files.

### 2. CSS Custom Properties (tokens)

**Source:** Phase 2 `global.css` (via existing pages)
**Apply to:** `map.css` (island-scoped) — reference via `var()`, do not redefine

```css
/* map.css — inherit Phase 2 tokens, extend only for map-specific elements */
.map-stage { height: calc(100vh - 64px); position: relative; }
.map-canvas { width: 100%; height: 100%; }
.map-topbar { background: var(--bg); border-bottom: 1px solid var(--line); /* ... */ }
.result-panel { background: var(--bg); border-left: 1px solid var(--line); /* ... */ }
.legend { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px; }
.chip { height: 44px; border-radius: 999px; padding: 0 16px; font-size: 14px; font-weight: 700; }
.chip.active { background: var(--primary); color: #ffffff; }
.chip:not(.active) { background: var(--card); color: var(--ink); border: 1px solid var(--line); }
.user-dot { width: 18px; height: 18px; border-radius: 50%; background: #0f766e; border: 2px solid #0f766e; box-shadow: 0 0 0 2px #ffffff; }
.ev-dot { width: 14px; height: 14px; border-radius: 50%; background: #e8a05c; border: 1px solid #ffffff; }
```

Family bar CSS mirrors `FamilyBreakdownBars.astro` lines 89–143 exactly (copy the `.family-bars`, `.family-bar-row`, `.family-bar-track`, `.family-bar-fill`, `.accent-dot` rules).

### 3. External Link Security

**Apply to:** `IncidentPinLayer.ts`, `IncidentsList.tsx`, `ResultPanel.tsx`

Always use `rel="noopener noreferrer"` on all incident source links and CTA external links. Never use `dangerouslySetInnerHTML` with incident data — React JSX escaping is the mitigation.

### 4. Leaflet CSS Import

**Apply to:** `MapIsland.tsx` only

```tsx
import 'leaflet/dist/leaflet.css';
// Must be inside the client:only island .tsx, not in any .astro file
// See RESEARCH Pitfall 1: importing in SSR context causes build error
```

### 5. Graceful Fetch Pattern

**Apply to:** `ResultPanel.tsx`, `IncidentPinLayer.ts`, year-payload fetch in `MapIsland.tsx`

```typescript
// Pattern: try/catch + response.ok guard; never throw to the top level
async function safeFetch<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.json() as T;
  } catch {
    return null;
  }
}
```

### 6. Validator Script Structure

**Source:** `site/scripts/validate/structure.mjs` + `site/scripts/validate/all.mjs`
**Apply to:** `site/scripts/validate/map-pages.mjs`

All validators follow the same pattern:
1. Resolve `REPO_ROOT`, `SITE_ROOT`, `DIST_DIR` via `fileURLToPath(import.meta.url)`
2. Early-exit `process.exit(0)` if `dist/` doesn't exist
3. Use `node:assert/strict` for assertions
4. Print `console.log('name: check passed')` per check
5. Zero external dependencies

Register the new validator in `site/scripts/validate/all.mjs` by adding `'map-pages.mjs'` to the VALIDATORS array.

---

## No Analog Found

All Phase 3 files have close analogs in the codebase. No files fall into this category.

---

## Metadata

**Analog search scope:** `ischilesafe.com/` (prototype), `site/src/components/`, `site/src/pages/`, `site/src/lib/`, `site/scripts/validate/`, `site/astro.config.mjs`
**Files scanned:** 10 source files read in full
**Pattern extraction date:** 2026-06-13
