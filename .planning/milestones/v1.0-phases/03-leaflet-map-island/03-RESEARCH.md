# Phase 3: Leaflet Map Island — Research

**Researched:** 2026-06-13
**Domain:** React island + Leaflet 1.9.x choropleth + TopoJSON pipeline + Astro 6 integration
**Confidence:** HIGH (all critical claims verified from codebase + npm registry + official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01** Boundary geometry delivered as TopoJSON; decoded in browser with `topojson-client`.
- **D-02** Source geometry = `ischilesafe.com/geo-data.js` (~222 KB); simplify with mapshaper (Visvalingam ~10–15% retention) to <100 KB. Do NOT re-download.
- **D-03** Stored as committed static asset under `data/cead/geo/`.
- **D-04** Fetched at runtime by the island (not bundled).
- **D-05** Native `L.geoJSON()` inside `useEffect` — NOT `<GeoJSON>` component from react-leaflet.
- **D-06** `client:only="react"` hydration. Never `client:load`.
- **D-07** Dedicated map pages `/map/` (EN) and `/es/mapa/` (ES); commune content pages keep placeholder, link to map centered on that commune.
- **D-08** Basemap = CARTO Positron (free, no API key).
- **D-09** Year filter loads `map-payload-{year}.json` on change.
- **D-10** Crime-type filter recolors from `by_family[]` (7 families) + "todos" (total rate). No extra fetch.
- **D-11** Color scale = chroma-js 5-level teal→red; `level` (1–5) for "todos"; client-side quantile breaks for per-family coloring.
- **D-12** Filter changes: `setStyle` in place — never re-mount the `L.geoJSON` layer.
- **D-13** Commune panel: fetch `data/cead/comunas/{cut}.json`; render tasa/trend/rank/sparkline/family breakdown inline; inline SVG sparkline; no charting lib.
- **D-14** Geolocation: browser Geolocation API + point-in-polygon against loaded GeoJSON; no external reverse-geocode.
- **D-15** Incident pins: fetch `data/incidents/current.json`; absent = graceful empty state.
- **D-16** Mobile perf: `L.canvas()` renderer + memoized styles + <100 KB TopoJSON; manual device check before sign-off.

### Claude's Discretion

- Exact mapshaper simplification % to hit <100 KB (tune in execution).
- Panel open/close interaction details, mobile layout (bottom sheet vs side panel), zoom/pan defaults and initial bounds.
- Whether to use `<MapContainer>` for container or `L.map()` directly.
- Quantile-break algorithm specifics for per-family color scaling.
- Highlight/selected-state styling for clicked or geolocated commune.

### Deferred Ideas (OUT OF SCOPE)

- Incident pins with real data (Phase 5). This phase renders layer + empty state only.
- Full interactive island embedded in every commune page.
- Region-level choropleth toggle.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAP-01 | User can explore choropleth national map with communes colored by relative incidence | D-05, D-11, D-12; native L.geoJSON + L.canvas + chroma-js 5-level scale |
| MAP-02 | User can filter map by year and crime type | D-09 (21 year payloads confirmed: 2005–2025); D-10 (by_family[7] in payload); D-12 (setStyle in place) |
| MAP-03 | User can open commune panel with tasa, trend, rank, sparkline, breakdown | D-13; fetch `comunas/{cut}.json`; PanelSparkline inline SVG ported from Sparkline.astro |
| MAP-04 | User can see incident-pin layer with source + date | D-15; `incidents/current.json`; empty state when absent |
| MAP-05 | "Mostrar mi ubicación" identifies and highlights commune | D-14; Geolocation API + point-in-polygon |
| MAP-06 | Map usable on mid-range mobile: <100 KB GeoJSON, memoized styles | D-16; L.canvas(); mapshaper TopoJSON pipeline |
</phase_requirements>

---

## Summary

Phase 3 installs the React+Leaflet ecosystem into the Phase-2 Astro project and builds the interactive choropleth island. The core work has four tracks: (1) install dependencies, (2) run the offline TopoJSON simplification pipeline, (3) build the React island with all UI components, and (4) wire the island into dedicated `/map/` + `/es/mapa/` pages.

The most important technical constraint is the `client:only="react"` hydration directive — this ensures Leaflet JS never loads on the 740 content pages. All choropleth state management uses native Leaflet APIs (L.geoJSON, setStyle, L.canvas) rather than react-leaflet components to avoid the documented per-hover re-render jank at 346 features.

The TopoJSON pipeline is a one-time offline step: extract the GeoJSON from the prototype's `geo-data.js` (a JS expression wrapping a raw GeoJSON object), simplify with mapshaper to <100 KB, convert to TopoJSON format, commit to `data/cead/geo/communes.topo.json`. The critical join key is `feature.properties.id` — verified from the prototype — which matches the `id` field in `map-payload.json` comunas.

**Primary recommendation:** Use `<MapContainer>` from react-leaflet@5 (React 19 compatible peer dep) for mount only; all choropleth via native `L.geoJSON()` inside `useEffect`. Do NOT use react-leaflet@4 — its peer dep is React ^18, incompatible with the installed React 19.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Choropleth rendering + filter | Browser / Client (React island) | — | Leaflet is a browser-only library; `client:only="react"` prevents SSR |
| TopoJSON → GeoJSON decode | Browser / Client | — | `topojson-client.feature()` runs in the island on mount |
| Year/crime-type payload fetch | Browser / Client | — | Runtime fetch from `/data/cead/map-payload-{year}.json`; island owns |
| Commune panel data fetch | Browser / Client | — | `fetch('/data/cead/comunas/{cut}.json')` on click |
| Incident pins fetch | Browser / Client | — | `fetch('/data/incidents/current.json')` on toggle; graceful 404 |
| Geolocation | Browser / Client | — | Geolocation API browser-only |
| Map page shell (SEO) | Frontend Server (Astro SSR/SSG) | — | `/map/` and `/es/mapa/` are static Astro pages; head/meta/hreflang pre-rendered |
| Basemap tiles | CDN (CARTO) | — | External tile CDN; no API key required |
| Boundary geometry | CDN / Static | — | `data/cead/geo/communes.topo.json` served as static asset by Cloudflare Pages |
| Payload files | CDN / Static | — | `data/cead/map-payload*.json` served as static assets |
| TopoJSON simplification pipeline | Build tooling (offline) | — | Runs once at data prep time, not at Astro build time |

---

## Standard Stack

### Core (new installs for Phase 3)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@astrojs/react` | 5.0.7 | React island integration in Astro 6 | Official integration; current [VERIFIED: npm registry] |
| `react` | 19.2.7 | React runtime for islands | Required peer dep of @astrojs/react@5 [VERIFIED: npm registry] |
| `react-dom` | 19.2.7 | React DOM renderer | Required peer dep of @astrojs/react@5 [VERIFIED: npm registry] |
| `leaflet` | 1.9.4 | Map rendering, choropleth, markers | Locked in CLAUDE.md; confirmed current [VERIFIED: npm registry] |
| `@types/leaflet` | 1.9.21 | TypeScript types for Leaflet | Current [VERIFIED: npm registry] |
| `@types/react` | 19.2.17 | TypeScript types for React | Required for .tsx [VERIFIED: npm registry] |
| `@types/react-dom` | 19.2.3 | TypeScript types for react-dom | Required for .tsx [VERIFIED: npm registry] |

### Critical Version Correction: react-leaflet

CLAUDE.md says "Pin to v4 for React 19 compat." **This is incorrect as of June 2026.** [VERIFIED: npm registry]

- `react-leaflet@4.2.1` peerDep: `"react": "^18.0.0"` — **incompatible with React 19**
- `react-leaflet@5.0.0` peerDep: `"react": "^19.0.0"` — **correct for React 19**

**Decision required:** Either use react-leaflet@5.0.0 (React 19 compatible), or skip react-leaflet entirely and use pure `L.map()` + `L.geoJSON()` for all rendering. Given that D-05 mandates native L.geoJSON anyway (not `<GeoJSON>` component), and the only react-leaflet benefit is `<MapContainer>`, it is viable to skip it entirely and instantiate `L.map(divRef.current, options)` directly. Recommend: **skip react-leaflet entirely** — zero risk of peer dep conflicts, one fewer dependency, and the pattern is already proven in the prototype's `map-view.jsx`.

If `<MapContainer>` is preferred for container management, use `react-leaflet@5.0.0` (React 19 compat confirmed [VERIFIED: npm registry]).

| Library | Version | Purpose | Note |
|---------|---------|---------|------|
| react-leaflet | 5.0.0 (if used) | `<MapContainer>` wrapper only | Optional; D-05 means choropleth bypasses it anyway |

### Already Installed (Phase 2)

| Library | Version | Status |
|---------|---------|--------|
| `chroma-js` | 3.2.0 | Installed — but currently build-time only in `colorScale.ts`; island needs its own client-side import |
| `topojson-client` | 3.1.0 | Installed — ready for browser use in island |
| `@types/chroma-js` | 2.4.4 | Installed |
| `@types/topojson-client` | 3.1.4 | Installed |

**chroma-js client-side usage:** `colorScale.ts` is documented as "build-time only." The React island cannot import it. The island must import `chroma-js` directly in the TSX file. This is fine — chroma-js is a universal module that runs in both Node and browser. The `package.json` lists it as a `dependency` (not devDependency), so it ships to the client bundle for the island.

### Offline Tooling (not in package.json)

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| mapshaper | 0.7.22 | Simplify + convert to TopoJSON | `npm install -g mapshaper` (global) [VERIFIED: npm registry] |

**Installation (new deps only):**
```bash
cd site
npm install @astrojs/react@5.0.7 react@19 react-dom@19 leaflet@1.9.4 @types/leaflet @types/react @types/react-dom
# Optional (only if using <MapContainer>):
npm install react-leaflet@5.0.0
```

**astro.config.mjs change:** Add `import react from '@astrojs/react'` and `react()` to integrations array. The existing sitemap integration is unaffected.

---

## Package Legitimacy Audit

> slopcheck was run but operates against PyPI by default; these are npm packages. Manual npm registry verification performed instead.

| Package | Registry | Confirmed via | Downloads (est.) | Source Repo | Disposition |
|---------|----------|---------------|-----------------|-------------|-------------|
| `@astrojs/react` | npm | `npm view` → 5.0.7 | Very high (Astro official) | github.com/withastro/astro | Approved [VERIFIED: npm registry] |
| `react` | npm | `npm view` → 19.2.7 | Billions/wk | github.com/facebook/react | Approved [VERIFIED: npm registry] |
| `react-dom` | npm | `npm view` → 19.2.7 | Billions/wk | github.com/facebook/react | Approved [VERIFIED: npm registry] |
| `leaflet` | npm | `npm view` → 1.9.4 | ~4M/wk | github.com/Leaflet/Leaflet | Approved [VERIFIED: npm registry] |
| `@types/leaflet` | npm | `npm view` → 1.9.21 | High | github.com/DefinitelyTyped | Approved [VERIFIED: npm registry] |
| `react-leaflet` | npm | `npm view` → 5.0.0 (latest) | ~600K/wk | github.com/PaulLeCam/react-leaflet | Approved if used [VERIFIED: npm registry] |
| `mapshaper` (global) | npm | `npm view` → 0.7.22 | High | github.com/mbloch/mapshaper | Approved [VERIFIED: npm registry] |

**Packages removed due to [SLOP]:** none
**Packages flagged [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (map page only)
│
├── Astro shell (/map/, /es/mapa/)
│   ├── <head> — SEO meta, hreflang, Leaflet CSS import
│   └── <MapIsland client:only="react" />
│
└── MapIsland (React, client-only)
    │
    ├── mount → L.map(divRef.current)
    │            └── CARTO Positron tile layer
    │
    ├── fetch data/cead/geo/communes.topo.json  ←── once on mount
    │   └── topojson.feature() → GeoJSON
    │       └── L.geoJSON(geo, { renderer: L.canvas() })
    │           ├── style fn: reads styleMap<cut, style> ref
    │           └── onEachFeature: tooltip + click + hover
    │
    ├── fetch data/cead/map-payload-{year}.json  ←── on year change
    │   └── build styleMap → layer.setStyle()
    │
    ├── Crime-type filter change
    │   └── compute quantile breaks from payload.by_family[i]
    │       └── build styleMap → layer.setStyle()
    │
    ├── Commune click
    │   └── fetch data/cead/comunas/{cut}.json
    │       └── ResultPanel (tasa / trend / rank / sparkline / family bars)
    │           └── "Ver ficha completa" → /commune/{slug}/
    │
    ├── "Mostrar mi ubicación" button
    │   └── navigator.geolocation.getCurrentPosition()
    │       ├── success: ray-cast PiP against loaded GeoJSON features
    │       │   └── highlight commune + fly to zoom 12 + user-dot marker
    │       └── denied/unavailable: Toast error
    │
    ├── Events toggle (active)
    │   └── fetch data/incidents/current.json
    │       ├── success: L.layerGroup of L.divIcon ev-dot markers
    │       └── 404/absent: Toast "Capa de noticias próximamente"
    │
    └── Low-zoom (< 8)
        └── L.layerGroup of L.circleMarker (one per commune centroid)
```

### Recommended Project Structure

```
site/src/
  components/
    map/
      MapIsland.tsx          — root island; client:only="react"; owns all state
      MapTopbar.tsx          — SearchBox + LocateButton + FiltersRow
      SearchBox.tsx          — commune name autocomplete
      FiltersRow.tsx         — year <select> + 8 crime-type chips + events toggle
      ZoomControl.tsx        — desktop +/− buttons (hidden on mobile)
      Legend.tsx             — 5 swatches + labels
      ResultPanel.tsx        — commune detail panel (fetches on open)
      PanelSparkline.tsx     — inline SVG; mirrors Sparkline.astro contract
      PanelFamilyBars.tsx    — 7-family horizontal bars
      IncidentsList.tsx      — incident rows inside ResultPanel
      Toast.tsx              — ephemeral notification, aria-live="polite"
    map.css                  — island-scoped CSS (no Tailwind; custom props from global.css)
  pages/
    map.astro                — EN map page
    es/
      mapa.astro             — ES map page
data/cead/
  geo/
    communes.topo.json       — <100 KB TopoJSON committed asset (offline pipeline output)
```

### Pattern 1: Astro Config — Adding React Integration

```typescript
// site/astro.config.mjs
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';         // ADD
// ... existing imports ...

export default defineConfig({
  site: 'https://ischilesafe.com',
  i18n: { /* unchanged */ },
  integrations: [
    react(),                                 // ADD — before sitemap
    sitemap({ /* unchanged */ }),
  ],
  vite: { /* unchanged */ },
});
```

`react()` integration with zero options is sufficient. It does not affect non-island pages — components without `client:*` directives are rendered to HTML only. [ASSUMED — based on Astro 6 docs pattern]

### Pattern 2: Map Island Mount — Pure Leaflet (no react-leaflet)

```typescript
// site/src/components/map/MapIsland.tsx
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import * as topojson from 'topojson-client';

export default function MapIsland({ lang }: { lang: 'en' | 'es' }) {
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.GeoJSON | null>(null);
  const styleMapRef = useRef<Map<string, L.PathOptions>>(new Map());

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    const map = L.map(divRef.current, { zoomControl: false, attributionControl: true });
    map.setView([-35.7, -71.8], 5);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  return <div ref={divRef} style={{ height: 'calc(100vh - 64px)' }} />;
}
```

[VERIFIED: pattern from prototype `map-view.jsx` + Leaflet 1.9.x docs]

### Pattern 3: Choropleth Layer — Native L.geoJSON + L.canvas + setStyle

```typescript
// Inside MapIsland or a useChoropleth hook
useEffect(() => {
  const map = mapRef.current;
  if (!map || !geoData) return;

  // Build style lookup once
  const styleMap = new Map<string, L.PathOptions>();
  payload.comunas.forEach(c => {
    styleMap.set(c.id, {
      fillColor: INCIDENCE_COLORS[c.level - 1]!,
      fillOpacity: 0.55,
      color: '#ffffff',
      weight: 1.2,
    });
  });
  styleMapRef.current = styleMap;

  const renderer = L.canvas();
  const layer = L.geoJSON(geoData, {
    renderer,
    style: (f) => styleMapRef.current.get(f!.properties.id) ?? defaultStyle,
    onEachFeature: (f, ly) => {
      ly.bindTooltip(f.properties.name, { sticky: true, direction: 'top' });
      ly.on('click', () => handleCommune(f.properties.id));
      ly.on('mouseover', () => {
        if (selectedCut !== f.properties.id)
          ly.setStyle({ fillOpacity: 0.74, weight: 1.8 });
      });
      ly.on('mouseout', () => layer.resetStyle(ly));
      polyIndexRef.current.set(f.properties.id, ly);
    },
  }).addTo(map);
  layerRef.current = layer;

  return () => { layer.remove(); layerRef.current = null; };
}, [geoData]);                         // Only on initial GeoJSON load

// On filter change: setStyle in place — NO re-mount
function applyFilter(newPayload: MapPayload, familyIndex: number | null) {
  const layer = layerRef.current;
  if (!layer) return;
  const rates = newPayload.comunas.map(c =>
    familyIndex !== null ? c.by_family[familyIndex]! : null
  ).filter(Boolean) as number[];
  const breaks = computeQuantileBreaks(rates, 5);

  const newStyleMap = new Map<string, L.PathOptions>();
  newPayload.comunas.forEach(c => {
    const rate = familyIndex !== null ? c.by_family[familyIndex]! : null;
    const level = rate !== null ? levelFromBreaks(rate, breaks) : c.level;
    newStyleMap.set(c.id, { fillColor: INCIDENCE_COLORS[level - 1]!, fillOpacity: 0.55, color: '#ffffff', weight: 1.2 });
  });
  styleMapRef.current = newStyleMap;
  layer.setStyle((f) => styleMapRef.current.get(f!.properties.id) ?? defaultStyle);
}
```

[VERIFIED: pattern from prototype map-view.jsx choropleth useEffect; CITED: Leaflet 1.9.x docs — setStyle applies style function to all layers without re-mount]

### Pattern 4: TopoJSON Offline Pipeline

```bash
# Step 1: Extract GeoJSON from JS wrapper
# geo-data.js is: window.CSM_GEO = { type: "FeatureCollection", ... }
# Extract with node:
node -e "const s=require('fs').readFileSync('ischilesafe.com/geo-data.js','utf8'); \
  const m=s.match(/=\s*(\{[\s\S]+\})\s*;?\s*$/); \
  require('fs').writeFileSync('/tmp/communes-raw.geojson', m[1]);"

# Step 2: Simplify + convert to TopoJSON with mapshaper
mapshaper /tmp/communes-raw.geojson \
  -simplify visvalingam percentage=12% keep-shapes \
  -o format=topojson /tmp/communes.topo.json

# Step 3: Check output size
du -k /tmp/communes.topo.json
# Target: < 100 KB. Adjust percentage if needed.

# Step 4: Commit
cp /tmp/communes.topo.json data/cead/geo/communes.topo.json
```

Key facts:
- `geo-data.js` features use `properties.id` as the CUT — confirmed in prototype code and grep. Matches `map-payload.json` `id` field. Join key is identical. [VERIFIED: codebase grep]
- Mapshaper@0.7.22 is the current version [VERIFIED: npm registry]. `visvalingam percentage=12%` is a starting point; tune to stay under 100 KB while keeping commune outlines recognizable.
- `--keep-shapes` preserves tiny communes (islands, Easter Island) that would otherwise disappear. [ASSUMED — mapshaper docs pattern]
- The `id` property on each feature must survive simplification. Mapshaper preserves all properties by default.

### Pattern 5: Point-in-Polygon for Geolocation

The prototype used `C.nearestComuna(lat, lng)` which was based on centroid distance — NOT true point-in-polygon. For correctness (urban communes with irregular shapes), use a ray-casting PiP against the loaded GeoJSON features.

```typescript
function pointInPolygon(lat: number, lng: number, features: GeoJSON.Feature[]): string | null {
  const pt: [number, number] = [lng, lat]; // GeoJSON is [lng, lat]
  for (const f of features) {
    if (containsPoint(f.geometry, pt)) return f.properties!.id as string;
  }
  return null;
}

// Ray-cast algorithm for Polygon/MultiPolygon
function containsPoint(geom: GeoJSON.Geometry, pt: [number, number]): boolean {
  if (geom.type === 'Polygon') return ringContains(geom.coordinates[0]!, pt);
  if (geom.type === 'MultiPolygon') return geom.coordinates.some(poly => ringContains(poly[0]!, pt));
  return false;
}

function ringContains(ring: number[][], [px, py]: [number, number]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]!;
    const [xj, yj] = ring[j]!;
    if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}
```

**Why not leaflet-pip or turf?** D-14 says "no external reverse-geocode service." A hand-rolled ray-cast is ~20 lines and avoids an additional dependency. 346 features × simple ring test is fast enough (< 2ms in browser). [ASSUMED — turf.js pointInPolygon could also be used but is an extra dependency]

### Pattern 6: Inline SVG Sparkline (React port of Sparkline.astro)

```tsx
// PanelSparkline.tsx — mirrors Sparkline.astro contract exactly
interface Props {
  series: Array<{ year: number; rate_per_100k: number; partial?: boolean }>;
  activeYear?: number;
  primaryColor?: string;
}

export function PanelSparkline({ series, activeYear, primaryColor = '#0f766e' }: Props) {
  const maxRate = Math.max(...series.map(s => s.rate_per_100k), 1);
  const barW = 18, gap = 8, height = 44;
  const totalW = series.length * (barW + gap) - gap;
  return (
    <svg viewBox={`0 0 ${totalW} ${height}`} width="100%" height={height}
         preserveAspectRatio="none" aria-hidden="true" className="sparkline">
      {series.map((s, i) => {
        const barH = Math.max(4, Math.round((s.rate_per_100k / maxRate) * (height - 4)));
        const active = s.year === activeYear;
        return <rect key={i} x={i * (barW + gap)} y={height - barH}
                     width={barW} height={barH} rx="3"
                     fill={active ? primaryColor : 'var(--muted)'}
                     opacity={s.partial ? 0.5 : 1} />;
      })}
    </svg>
  );
}
```

[VERIFIED: directly ported from `site/src/components/Sparkline.astro` and `ischilesafe.com/components.jsx` line 135-150]

### Pattern 7: Incident Layer — Schema Contract for Phase 5

Since `data/incidents/current.json` does not exist yet, Phase 3 must define the schema the layer reads so Phase 5 can produce it:

```typescript
// Expected schema: data/incidents/current.json
interface Incident {
  id: string;           // unique identifier
  cut: string;          // commune CUT (matches map-payload id)
  lat: number;          // approximate latitude
  lng: number;          // approximate longitude
  title_es: string;     // Spanish headline
  title_en: string;     // English headline
  date: string;         // ISO 8601 date "YYYY-MM-DD"
  outlet: string;       // news outlet name e.g. "BioBíoChile"
  url: string;          // source URL (external link)
  family: string;       // crime family key from catalog.json
}

interface IncidentsFile {
  generated: string;    // ISO timestamp
  window_days: number;  // e.g. 30
  incidents: Incident[];
}
```

The island fetches this with a try/catch + `response.ok` guard. If the fetch fails (404) or the file is empty, the events toggle renders disabled and a toast fires on tap. No error surfaces in the console.

### Pattern 8: chroma-js Client-Side Usage

```typescript
// In MapIsland.tsx — direct import, not via colorScale.ts (which is Node-only)
import chroma from 'chroma-js';

const INCIDENCE_COLORS = chroma
  .scale(['#dbeef0', '#9fd0cd', '#f4d58d', '#e8a05c', '#c96b5a'])
  .classes(5)
  .colors(5);

// Per-family quantile breaks
function computeQuantileBreaks(rates: number[], classes: number): number[] {
  const sorted = [...rates].filter(r => r > 0).sort((a, b) => a - b);
  return Array.from({ length: classes - 1 }, (_, i) =>
    sorted[Math.floor((sorted.length * (i + 1)) / classes)] ?? 0
  );
}

function levelFromBreaks(rate: number, breaks: number[]): 1 | 2 | 3 | 4 | 5 {
  const idx = breaks.findIndex(b => rate <= b);
  return (idx === -1 ? breaks.length : idx) + 1 as 1|2|3|4|5;
}
```

[VERIFIED: chroma-js is universal (browser + Node), confirmed from package.json dependencies]

### Anti-Patterns to Avoid

- **`<GeoJSON>` component from react-leaflet**: Triggers a full re-render on every hover event. With 346 features, this causes visible jank on mid-range devices. Use native `L.geoJSON()` inside `useEffect`. [CITED: CLAUDE.md "What NOT to Use"; tmsvr.com/react-leaflet-map-performance-issues/]
- **`client:load` on MapIsland**: Loads Leaflet JS on every page including the 740 content pages. Use `client:only="react"`. [CITED: CLAUDE.md]
- **Re-creating L.geoJSON layer on filter change**: Destroys and recreates all 346 layers; expensive. Use `layer.setStyle(fn)` in place with a pre-built styleMap ref.
- **Importing `colorScale.ts` in the island**: That module is marked "Node-only." Import chroma-js directly in the island.
- **Using `react-leaflet@4`**: Peer dep is React ^18. The project uses React 19. Will produce peer dep warnings and potential runtime issues. Use @5.0.0 or skip react-leaflet entirely.
- **SSR-ing the Leaflet island**: `client:only="react"` prevents SSR. Never remove this — Leaflet calls `window` and `document` on import, which crash Astro's SSR.
- **Loading Leaflet CSS via `<link>` in Astro head**: Import `leaflet/dist/leaflet.css` inside the island TSX instead; this ensures it only loads when the island is present.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TopoJSON decode | Custom parser | `topojson-client` (already installed) | `topojson.feature(topo, object)` → standard GeoJSON |
| Color scale computation | Manual lerp | `chroma-js` (already installed) | Correct perceptual color interpolation; scale/classes API |
| GeoJSON simplification | Custom vertex reduction | `mapshaper` CLI | Handles topology-preserving simplification; shared arcs |
| Basemap tiles | Self-hosted tiles | CARTO Positron (free CDN) | No API key, light palette, global CDN |
| Commune name search | Fuzzy search lib | Simple Array.filter on commune index | 346 communes fit in memory; no lib needed for exact prefix match |

---

## Data Contract Verification

### map-payload.json structure (confirmed from codebase)

```json
{
  "generated": "2026-06-13T01:58:59.563137Z",
  "year": 2025,
  "comunas": [
    { "id": "5602", "rate": 10567, "level": 5, "by_family": [1994, 295, 1043, 129, 221, 3301, 3584] }
  ]
}
```

- `id` = CUT code (string, no zero-padding for leading zeros) [VERIFIED: codebase]
- `by_family` = 7 integers, index order = catalog.json `family_keys` order [VERIFIED: codebase]
- `level` = precomputed 1–5 quintile; used directly for "todos" coloring
- Year payloads available: **2005 through 2025** (21 files) [VERIFIED: Glob output]

### catalog.json family_keys order (index → family name)

| Index | Key | Featured |
|-------|-----|---------|
| 0 | `vida` | yes |
| 1 | `robos_violentos` | no |
| 2 | `vif` | no |
| 3 | `drogas` | no |
| 4 | `armas` | no |
| 5 | `propiedad` | yes |
| 6 | `incivilidades` | no |

[VERIFIED: codebase — `data/cead/meta/catalog.json`]

**Note:** UI-SPEC chip order differs from catalog.json key order. The FiltersRow must map chip index → by_family array index via catalog family order, not chip order. Use catalog.json `family_keys` array as the authoritative index mapping.

### Geo-data feature join key

`feature.properties.id` matches commune CUT (string). [VERIFIED: prototype code `map-view.jsx` line 207]

---

## Common Pitfalls

### Pitfall 1: Leaflet CSS Import in SSR Context

**What goes wrong:** `import 'leaflet/dist/leaflet.css'` inside a component that Astro SSR's causes a build error — CSS is treated as a side effect in the server bundle.
**Why it happens:** `client:only="react"` prevents SSR, but if the import is at module level of a file that Astro ever attempts to analyze statically, it can fail.
**How to avoid:** Import inside the island's `.tsx` file (guaranteed `client:only`). Alternatively, add `<link rel="stylesheet" href="/node_modules/leaflet/dist/leaflet.css">` in the map page's `<head>` only on map pages.
**Warning signs:** Build error mentioning `leaflet/dist/leaflet.css` or `Cannot import CSS in server bundle`.

### Pitfall 2: react-leaflet@4 Peer Dep Conflict

**What goes wrong:** npm install completes with warnings; React 19 + react-leaflet@4 work but produce runtime issues or silent hook failures.
**Why it happens:** react-leaflet@4 declares `"react": "^18.0.0"` as peer dep. npm v7+ installs anyway with a warning but may install a duplicate React.
**How to avoid:** Use react-leaflet@5.0.0 or skip react-leaflet entirely (recommended given D-05 bypasses it for choropleth anyway).
**Warning signs:** `npm install` output showing "peer dep conflict for react-leaflet@4".

### Pitfall 3: chroma-js Imported as Node-Only

**What goes wrong:** `import { INCIDENCE_COLORS } from '../lib/colorScale.ts'` inside the island fails at runtime — colorScale.ts uses Node.js path/fs for imports not present in browser.
**Actually:** colorScale.ts itself only imports chroma-js which IS universal. BUT the file is documented as "MUST only be imported in build-time code." If it ever adds a Node-only dep, the island breaks silently.
**How to avoid:** Inline the `chroma-js` import and color constants directly in MapIsland.tsx. Do not re-export from colorScale.ts to the island.

### Pitfall 4: GeoJSON Feature CUT Mismatch

**What goes wrong:** Choropleth renders without fill color; communes appear white/transparent.
**Why it happens:** The join between `feature.properties.id` (from TopoJSON) and `map-payload.json` `id` fails if they don't match (e.g., leading zeros, string vs number).
**How to avoid:** After extracting GeoJSON from geo-data.js, verify a sample feature's `properties.id` matches a known CUT from map-payload (e.g., "13101" = Santiago). String comparison only — both are strings in the data contract.
**Warning signs:** All communes render in default Leaflet grey.

### Pitfall 5: Leaflet Map Double-Init

**What goes wrong:** React strict mode (development) double-invokes useEffect; `L.map()` called twice on same div → "Map container is already initialized" error.
**How to avoid:** Guard with `if (mapRef.current) return` at the top of the init useEffect. Return cleanup: `() => { map.remove(); mapRef.current = null; }`.
**Warning signs:** Console error "Map container is already initialized."

### Pitfall 6: L.canvas() + Non-Path Layers

**What goes wrong:** `L.canvas()` renderer only works with Path layers (Polygon, Polyline, CircleMarker). `L.marker()` (for user-dot and incident pins) uses SVG/DOM, not canvas — they are incompatible with the canvas renderer option.
**How to avoid:** Declare `renderer: L.canvas()` ONLY on the `L.geoJSON()` choropleth layer. Do NOT set it as the map's global default renderer. `L.circleMarker` (low-zoom dots) supports canvas; `L.marker` (user dot, ev-dot) uses DOM and is canvas-incompatible.
**Warning signs:** Markers disappear or produce console errors when a global canvas renderer is set.

### Pitfall 7: Mobile — Leaflet Default Marker Icon 404

**What goes wrong:** Default `L.marker()` tries to load `/images/marker-icon.png` from its CSS URL, resulting in 404.
**How to avoid:** Use `L.divIcon()` for all markers in this project (user-dot, ev-dot) — no image files needed. No need to fix the default icon path since no `L.marker` uses the default icon.

### Pitfall 8: OneDrive Build Artifacts Desync

**What goes wrong:** Astro build artifacts in `dist/` get synced by OneDrive mid-build on Windows; stale files cause false validate passes.
**How to avoid:** Chain build + validate in a single command: `npm run build && node scripts/validate/all.mjs`. Known env issue documented in STATE.md.

---

## Year Filter Data

Available year payloads (confirmed by file listing):

```
map-payload-2005.json through map-payload-2025.json (21 files)
map-payload.json (alias for latest = 2025)
```

Year selector default: **2025** (latestCompleteYear). 2026 would be partial-year if it existed; it does not currently. Year range: 2005–2025 inclusive. [VERIFIED: codebase]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (node) / existing `scripts/validate/all.mjs` pattern |
| Config file | none currently in site/ — Wave 0 gap |
| Quick run command | `node scripts/validate/all.mjs` (structural; already exists) |
| Full suite command | `npm run build && node scripts/validate/all.mjs` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command / Notes | Automatable? |
|--------|----------|-----------|--------------------------|-------------|
| MAP-01 | `/map/` and `/es/mapa/` pages exist in dist/ | structural | `ls dist/map/index.html && ls dist/es/mapa/index.html` | YES — add to validate/all.mjs |
| MAP-01 | Map island script present in map page HTML | structural | grep `data-island` or island script tag in dist/map/index.html | YES |
| MAP-01 | TopoJSON file is present and < 100 KB | structural | `stat -c%s data/cead/geo/communes.topo.json \| awk '{if($1<102400) print "OK"}'` | YES |
| MAP-01 | Choropleth renders 346 polygons | interaction | Manual — open /map/, check DevTools console for L.geoJSON layer count | MANUAL |
| MAP-02 | Year selector present in island HTML | structural | Not automatable without hydration | MANUAL |
| MAP-02 | setStyle recolors without reload | interaction | Manual — change year selector, observe map, verify no page reload | MANUAL |
| MAP-03 | Commune panel opens on click | interaction | Manual — click commune polygon, verify ResultPanel renders | MANUAL |
| MAP-03 | ResultPanel shows rate/trend/rank/sparkline/family bars | interaction | Manual — verify panel content sections | MANUAL |
| MAP-04 | Events toggle graceful when incidents/current.json absent | interaction | Manual — toggle events chip, verify toast "Capa de noticias próximamente" | MANUAL |
| MAP-05 | Geolocation button exists (aria-label present) | structural | grep `aria-label.*Show my location\|Mostrar mi ubicación` in island bundle | YES (partial) |
| MAP-05 | Geolocation flow works | interaction | Manual — trigger locate, verify toast + commune highlight | MANUAL |
| MAP-06 | TopoJSON < 100 KB | structural | File size check (see MAP-01 above) | YES |
| MAP-06 | Canvas renderer active | interaction | Manual — DevTools, verify `<canvas>` element in map container | MANUAL |
| MAP-06 | Mid-range mobile perf < 4s cold render | performance | Manual — Chrome DevTools Moto G4 + Fast 3G throttle | MANUAL (SC3) |

### Wave 0 Gaps (must be created in Wave 1)

- [ ] `data/cead/geo/communes.topo.json` — offline pipeline output (not a test file but a prerequisite)
- [ ] Validator: `scripts/validate/map-pages.mjs` — checks dist/ for `/map/`, `/es/mapa/`, TopoJSON size, island script tag
- [ ] `site/src/pages/map.astro` — EN map page stub
- [ ] `site/src/pages/es/mapa.astro` — ES map page stub
- [ ] Update `astro.config.mjs` with `react()` integration and sitemap filter extension for `/map/` + `/es/mapa/`

### Sampling Rate

- **Per task commit:** `npm run build && node scripts/validate/all.mjs` (existing validator gate)
- **Per wave merge:** Full build + new `scripts/validate/map-pages.mjs`
- **Phase gate:** Full build green + 6 manual interaction checks (MAP-01 choropleth, MAP-02 filter, MAP-03 panel, MAP-04 empty events, MAP-05 geolocation, MAP-06 mobile perf) before `/gsd:verify-work`

---

## Security Domain

> `security_enforcement: true` in config.json. ASVS level 1.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in this phase |
| V3 Session Management | no | No session |
| V4 Access Control | no | All data is public static files |
| V5 Input Validation | yes (partial) | Commune search input (client-side filter on known list — no server eval) |
| V6 Cryptography | no | No crypto |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via incident popup content | Tampering | Incident titles/outlets rendered via React (JSX escapes by default); never set `innerHTML` or `dangerouslySetInnerHTML` with incident data |
| External link abuse (ev-dot popup) | Tampering | Incident URLs: `target="_blank" rel="noopener noreferrer"` on all external links |
| CARTO tile request abuse | Information Disclosure | Tiles are public; no API key to leak |
| Geolocation data leakage | Information Disclosure | Browser Geolocation API — no lat/lng sent to any server; PiP computed client-side |
| CSP inline scripts | Security Misconfiguration | `client:only` islands are bundled modules, not inline scripts; no eval or inline handlers needed |

**Critical:** Never use `dangerouslySetInnerHTML` with any incident data fetched from `incidents/current.json`. React JSX escaping is the only mitigation needed for user-visible data. [ASSUMED — based on standard React security practice]

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Astro build | ✓ | 20+ (confirmed in project) | — |
| npm | package install | ✓ | current | — |
| mapshaper | TopoJSON pipeline (offline, once) | ✓ | 0.7.22 (npm view confirmed) | `npm install -g mapshaper` |
| Leaflet CSS | Island rendering | Will be available after install | via npm package | — |
| CARTO Positron tiles | Basemap | ✓ | external CDN | OpenStreetMap tiles (fallback, different URL) |

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| react-leaflet `<GeoJSON>` component | Native `L.geoJSON()` in useEffect | Avoids per-hover re-render; mandated by CLAUDE.md |
| react-leaflet@4 (React 18) | react-leaflet@5 (React 19) or skip | @4 peer dep is React ^18; project uses React 19 |
| SVG renderer (Leaflet default) | `L.canvas()` renderer | Canvas is significantly faster for 346 features on mobile |
| GeoJSON (~222 KB) | TopoJSON (<100 KB) | Shared arcs + quantization; `topojson-client` decodes in browser |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `react()` integration with zero options does not affect non-island Astro pages or the existing sitemap integration | Standard Stack / Pattern 1 | Low — worst case: rebuild issue; fixable |
| A2 | Hand-rolled ray-cast PiP is fast enough for 346 features on mid-range mobile (< 2ms) | Pattern 5 | Low — if slow, replace with turf.js `booleanPointInPolygon` |
| A3 | Never `dangerouslySetInnerHTML` is sufficient XSS mitigation for incident data | Security Domain | Medium — if incident data ever comes from user input (it doesn't in MVP), need sanitization |
| A4 | `keep-shapes` mapshaper flag preserves tiny commune polygons | Pattern 4 | Low — verifiable during execution |
| A5 | The prototype's geolocation used centroid distance (not PiP); replacing with ray-cast PiP is more accurate but may produce different commune assignments near borders | Pattern 5 | Low — accuracy improvement is desired |

---

## Open Questions

1. **react-leaflet: use or skip?**
   - What we know: D-05 mandates native `L.geoJSON()`; react-leaflet@4 incompatible with React 19; react-leaflet@5 adds `<MapContainer>` only
   - What's unclear: Whether the planner wants `<MapContainer>` for lifecycle convenience or prefers pure L.map()
   - Recommendation: Skip react-leaflet entirely; use `L.map(divRef.current)` directly. Saves a dependency and eliminates peer dep risk. This is what the prototype does.

2. **Sitemap: should `/map/` and `/es/mapa/` be in sitemap.xml?**
   - What we know: Sitemap filter currently passes "all other pages by default"
   - What's unclear: Map pages with `client:only` content may not be useful to index (no visible text content SSR'd)
   - Recommendation: Include in sitemap (they have meta descriptions and static headings); Google can crawl them as interactive pages. Low risk either way.

3. **commune content page: link-to-map vs. mini embedded island?**
   - What we know: D-07 says "commune pages link to the map centered on that commune"
   - What's unclear: Exact URL pattern for "centered on commune" link (e.g., `/map/?cut=13101`)
   - Recommendation: `/map/?cut={cut}` — island reads `URLSearchParams` on mount to set initial selected commune and fly to it.

---

## Sources

### Primary (HIGH confidence)
- `ischilesafe.com/map-view.jsx` — prototype choropleth pattern, geolocation logic, layer management
- `ischilesafe.com/components.jsx` — Sparkline component (lines 135–150)
- `site/src/components/Sparkline.astro` — Phase-2 sparkline contract to mirror
- `site/src/lib/colorScale.ts` — color scale and level computation
- `data/cead/map-payload.json` — confirmed payload schema; `id` field is CUT string
- `data/cead/meta/catalog.json` — confirmed family_keys order (7 families, indices 0–6)
- npm registry via `npm view` — all package versions confirmed

### Secondary (MEDIUM confidence)
- CLAUDE.md "What NOT to Use" section — Leaflet pitfalls documented
- Phase 3 CONTEXT.md D-01 through D-16 — locked decisions
- Phase 3 UI-SPEC.md — component inventory, interaction states, layout specs

### Tertiary (LOW confidence / ASSUMED)
- mapshaper `keep-shapes` flag behavior for tiny communes (A4)
- PiP ray-cast performance on mid-range Android (A2)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified via npm view
- react-leaflet version conflict: HIGH — peer deps confirmed from registry
- Architecture: HIGH — pattern directly derived from working prototype
- Pitfalls: HIGH — confirmed from prototype code + CLAUDE.md
- TopoJSON pipeline: MEDIUM — mapshaper command untested on this specific geo-data.js

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 (30 days — stable ecosystem)
