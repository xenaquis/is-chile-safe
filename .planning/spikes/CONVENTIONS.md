# Spike Conventions

Patterns established across spike sessions. New spikes follow these unless the question requires otherwise.

## Stack
- **Static HTML + vanilla JS**, opened directly via `file://` — no build, no server, no framework. Mirrors the project's static-first philosophy and gets to a feelable result fastest.
- No npm installs for spikes; real project data is extracted offline into a JS data file.

## Structure
- `.planning/spikes/NNN-name/` per spike; comparison variants as `NNN-x-variant.html` + an `index.html` comparator (tabbed + desktop/375px-mobile toggle).
- `.planning/spikes/_shared/` holds cross-spike assets:
  - `spike.css` — design tokens lifted verbatim from `site/src/styles/global.css` (teal `--primary #0f766e`, Nunito Sans, the 5-level incidence scale). Keeps mockups feeling like the product.
  - `spike-data.js` — `window.SPIKE_DATA`, generated from real `data/cead/meta/index.json` + `site/public/data/cead/map-payload.json` (346 comunas, rate/100k, level, by_family, computed national rank).
  - `spike-ui.js` — `window.SPIKEUI` render helpers (header/nav, rank tables, search, level dots, comuna links).

## Patterns
- **Real data, site styling** for IA/product spikes — structure is judged against how the real thing would feel, not lo-fi wireframes.
- Region derived from CUT (`cut//1000` → region 1–16), not the CEAD provincial `region_id`.
- "Safest" = lowest reported rate/100k; rank computed over non-low-population comunas only (DATA-04).
- Verify mockups in-browser via BrowserOS `evaluate_script` (DOM assertions) when screenshots time out — assert data loaded + key elements rendered.

## Tools & Libraries
- BrowserOS MCP for headless verification (file:// URLs; `evaluate_script` for DOM checks).
- None added as project deps — spikes are throwaway.
