# Phase 3: Leaflet Map Island - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss (4 grey areas, all accepted with recommended values)

<domain>
## Phase Boundary

An interactive Leaflet choropleth map of all 346 Chilean communes, shipped as a React island hydrated client-side only, letting users explore CEAD crime data on any device including mid-range mobile. Renders commune polygons colored by relative incidence; year and crime-type filters recolor without page reload; clicking a commune opens a panel (tasa per 100k, trend, national rank, sparkline 2005–present, crime-family breakdown); "mostrar mi ubicación" identifies and highlights the user's commune; an incident-pins layer (NEWS) shows recent incidents with source + date when `incidents/current.json` exists (graceful empty state until Phase 5).

Requirements: MAP-01, MAP-02, MAP-03, MAP-04, MAP-05, MAP-06.

**Out of this phase:**
- The RSS/news pipeline that produces `incidents/current.json` → Phase 5 (this phase only consumes it if present, else empty state).
- Editorial/legal pages + AdSense → Phase 4.
- Live deploy / cron / Cloudflare Deploy Hook → Phase 6.
- The static content pages (commune/region/crime-type) themselves → done in Phase 2; this phase mounts the interactive map into the Phase-2 map-placeholder slot and adds dedicated map pages.

</domain>

<decisions>
## Implementation Decisions

### GeoJSON delivery & size (SC3: boundary file <100 KB)
- **D-01:** Boundary geometry delivered as **TopoJSON**, decoded in the browser with `topojson-client` (already in the locked stack). Shared arcs + quantization bring 346 commune polygons well under the 100 KB budget.
- **D-02:** Source geometry = **simplify the prototype's `ischilesafe.com/geo-data.js` (~222 KB)** with mapshaper (Visvalingam, ~10–15% retention) down to the <100 KB target. Do NOT re-download a fresh dataset unless the prototype geometry proves unusable.
- **D-03:** Stored as a committed static asset under **`data/cead/geo/`** (consistent with the Phase-1 data contract), keyed so each feature carries the commune CUT for join with `map-payload`.
- **D-04:** **Fetched at runtime by the island** (not bundled) so the 346 content pages stay JS-free; the boundary file loads only on the map page / when the island mounts.

### Map island & placement
- **D-05:** Render with **native `L.geoJSON()` inside a `useEffect`** — NOT react-leaflet's `<GeoJSON>` component (CLAUDE.md "What NOT to Use": it re-renders on every hover and janks at 346 features). Leaflet 1.9.x; react-leaflet 4.x only if used for the container, otherwise pure Leaflet.
- **D-06:** Island hydration = **`client:only="react"`** (CLAUDE.md: never `client:load` on the map island — it would load Leaflet on every page). Mounts into the Phase-2 map-placeholder slot.
- **D-07:** Placement: **dedicated map pages `/map/` (EN) and `/es/mapa/` (ES)** are the primary interactive view. Commune pages keep their lightweight Phase-2 placeholder, linking to the map centered on that commune (no full island per commune page — protects content-page weight).
- **D-08:** Basemap = **CARTO Positron** (free, no API key, light palette that complements the teal incidence scale). No Mapbox (paid key).

### Filters & data loading (MAP-01, MAP-02)
- **D-09:** Year filter loads **`map-payload-{year}.json`** on change (pre-generated in Phase 1 — no recompute).
- **D-10:** Crime-type filter recolors from the payload's **`by_family[]`** (7 families) plus a "todos" option (total `rate`) — no extra fetch; the payload already carries per-family rates.
- **D-11:** Color scale = **chroma-js 5-level incidence scale** (teal→red, matching Phase 2 / prototype). Use the precomputed `level` (1–5) for the "todos" view; compute quantile breaks client-side for per-family coloring.
- **D-12:** Filter changes update the existing layer via **`setStyle` in place** (memoized) — never re-mount or re-create the L.geoJSON layer. No page reload (SC1).

### Commune panel, geolocation, incident pins, mobile
- **D-13:** Commune panel (MAP-03): on click, **fetch `data/cead/comunas/{cut}.json`** and render the panel (tasa per 100k, trend, national rank, sparkline 2005–present as inline SVG, crime-family breakdown) inside the React island, reusing the Phase-2 visual language. Inline SVG sparkline (no charting lib).
- **D-14:** Geolocation (MAP-05): browser **Geolocation API + point-in-polygon** against the loaded GeoJSON (Leaflet/turf-style hit test) → highlight the user's commune. No external reverse-geocode service. Handle permission-denied / no-fix gracefully.
- **D-15:** Incident pins (MAP-04): a NEWS layer **fetches `data/incidents/current.json`**; if the file is absent (Phase 5 not yet built) → render a graceful empty state, never an error. Each pin shows source outlet + date + link when present.
- **D-16:** Mobile performance (MAP-06): **`L.canvas()` renderer** for the 346 polygons + memoized styles + the <100 KB TopoJSON → target mid-range Android over 3G. Manual device/throttle check before phase sign-off (SC3).

### Claude's Discretion
- Exact mapshaper simplification percentage to hit <100 KB while keeping commune shapes recognizable (tune in execution).
- Panel open/close interaction details, mobile layout of the panel (bottom sheet vs side panel), zoom/pan defaults and initial map bounds (fit to Chile).
- Whether to use react-leaflet's `<MapContainer>` for the container or instantiate `L.map()` directly — both acceptable as long as the choropleth uses native `L.geoJSON()`.
- Quantile-break algorithm specifics for per-family color scaling.
- Highlight/selected-state styling for the clicked or geolocated commune.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `CLAUDE.md` — locked stack + "What NOT to Use": Leaflet 1.9.x, react-leaflet 4.x (pin for React 19), topojson-client 3.x, chroma-js 3.x; native `L.geoJSON()` inside useEffect (NOT `<GeoJSON>` component); `client:only="react"` on the map island (NOT `client:load`); GeoJSON performance section for 346 communes.
- `.planning/phases/02-astro-site-programmatic-pages/02-CONTEXT.md` + `02-UI-SPEC.md` — Phase-2 decisions: map-placeholder slot, teal palette (#0f766e) + 5-level incidence scale, component visual language to reuse in the panel.
- `.planning/phases/01-data-foundation/01-CONTEXT.md` — data contract (CUT codes, rate per 100k, low_population, trend, featured categories).
- `data/cead/map-payload.json` + `data/cead/map-payload-{year}.json` — per-commune `{id, rate, level 1-5, by_family[7]}` for the latest year and each year (drives choropleth + year filter). NOTE: feature key is `id` (the CUT), consistent with Phase-2 fix — join GeoJSON features on this.
- `data/cead/comunas/{cut}.json` — full per-commune data fetched on click for the panel.
- `data/cead/meta/catalog.json` — crime-family keys + order for the by_family[] index and the crime-type filter labels (ES/EN).
- `ischilesafe.com/geo-data.js` (~222 KB) — source commune/region geometry to simplify to <100 KB TopoJSON.
- `ischilesafe.com/map-view.jsx`, `components.jsx`, `tweaks-panel.jsx` — React+Leaflet prototype (map view, result panel with tasa/tendencia/ranking/sparkline/family bars, filter UX) to port into the island.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ischilesafe.com/map-view.jsx` + `components.jsx` — React+Leaflet prototype: choropleth, result panel, year/crime filters, teal 5-level scale. The structural reference to port into the Astro island.
- `ischilesafe.com/geo-data.js` — ~222 KB commune/region GeoJSON to simplify.
- Phase-2 `site/`: `src/lib/colorScale.ts` (chroma-js 5-level scale), `src/lib/data.ts` (data loaders + the `id`-as-CUT contract), `src/components/Sparkline.astro` / `FamilyBreakdownBars.astro` / `StatCard.astro` / `MapPlaceholderSlot.astro` (visual language + the slot the island mounts into).
- `data/cead/` — full Phase-1 output incl. map-payload(s).

### Established Patterns
- CUT code = commune identity; in per-commune JSON it is the `id` field (Phase-2 loadCommune populates `cut` from it — see Phase-2 fix). GeoJSON features must carry the CUT to join with payload/comuna JSON.
- Rate per 100k is the only metric; `level` (1–5) is the precomputed incidence quintile in map-payload.
- Zero React JS on content pages (Phase 2) — the map is the FIRST React island in the project; keep it `client:only` and isolated to the map page + slot.

### Integration Points
- Mounts into the Phase-2 `MapPlaceholderSlot` component / the `/map/` + `/es/mapa/` pages.
- Consumes `incidents/current.json` produced in Phase 5 (optional; empty state if absent).
- Reuses Phase-2 color scale + panel visual language for consistency.

</code_context>

<specifics>
## Specific Ideas

- The map is the product's hero feature ("un mapa nacional interactivo con datos CEAD reales") — visual consistency with the Phase-2 teal palette and the prototype's UX matters.
- Featured categories (homicidios, secuestros, propiedad) should be selectable/visible in the crime-type filter, prioritized per Phase-1 intent (homicidios = lowest cifra negra).
- Performance on mid-range Android over 3G is an explicit success criterion — favor canvas rendering, simplified geometry, and memoized styles over richer-but-heavier rendering.

</specifics>

<deferred>
## Deferred Ideas

- Incident pins with real data — Phase 5 (NEWS pipeline). This phase only renders the layer + empty state.
- Full interactive island embedded directly in every commune page — deferred; commune pages link to the centered map instead (content-page weight).
- Region-level choropleth toggle (region vs commune view) — not in MAP-01..06 scope; revisit post-MVP if desired.

</deferred>

---

*Phase: 3 - Leaflet Map Island*
*Context gathered: 2026-06-13 (autonomous smart-discuss)*
