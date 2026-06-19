# Phase 10: High-Resolution Commune Geometry — Human UAT Gate

**Plan:** 10-03 (Attribution + Visual/Perf Verification)
**Status:** ✅ APPROVED (human sign-off 2026-06-15)
**Gates:** 2 (visual recognizability + throttled-mobile perf)
**Requirements closed:** GEO-01 Success Criterion 2 (visual) + GEO-02 Success Criterion 3–4 (perf + console)

---

## Shipped Baseline

The Phase 10 pipeline (Plans 01–02) regenerated `communes.topo.json` from chilemapas
(GPL-3, INE/SUBDERE/BCN) at improved fidelity. Measured sizes:

| Asset | Raw | Gzip |
|-------|-----|------|
| `data/cead/geo/communes.topo.json` | 353,696 B (345.4 KB) | 87,672 B (85.6 KB) |

Previous asset (GADM, blocky): 227.5 KB raw / 61.2 KB gzip.
Fidelity settings: `visvalingam 10% keep-shapes`, `quantization=10000` (~0.4 km grid).
CUT join integrity: 346 features, 0 missing, 0 orphan, 0 dup.

---

## Gate 1 — Visual Recognizability (GEO-01 SC-2)

**What to verify:** The new chilemapas-sourced commune boundaries render as recognizable
real-world shapes in the browser — coastline detail, inter-commune borders, and island/oceanic
comunas are visually legible — contrasting with the prior blocky 8–10 km grid render.

### Steps

1. Start the dev server (or use the deployed site):
   ```
   cd site && npm run dev
   ```
2. Open both map pages in a real browser:
   - English: `http://localhost:4321/map/`
   - Spanish: `http://localhost:4321/es/mapa/`
3. At the default national zoom level, confirm:
   - Commune polygons have recognizable coastline detail (no straight-line "blocky" coastlines)
   - Internal commune borders are visible and follow expected shapes
4. Zoom in to the following spot-check areas and confirm individual comune shapes are legible:

   **Spot-check comunas:**
   | CUT | Name | Why |
   |-----|------|-----|
   | 5601 | Isla de Pascua | Tiny oceanic island — must be present and visually dot-sized |
   | 5602 | Juan Fernández | Tiny island group — must survive `keep-shapes` |
   | 12202 | Antártica Chilena | Placeholder polygon — must be present (CUT injected artificially) |
   | 5101 | Valparaíso | Coastal commune with recognizable irregular Pacific coastline |
   | 13101 | Santiago | Central metro commune — confirm crisp borders with neighbours |
   | 9101 | Temuco | River/interior commune — confirm border detail |

5. Compare the polygon fidelity to any screenshot of the prior GADM render (blocky straight
   coastlines). The new render should look materially smoother.

### Pass criteria
- [ ] Coastlines and commune borders have visible curve detail (not straight-line approximations)
- [ ] Isla de Pascua (CUT 5601) appears as a small polygon in the Pacific Ocean
- [ ] Juan Fernández (CUT 5602) appears as a tiny polygon offshore
- [ ] Antártica Chilena (CUT 12202) appears in southern Chile area (placeholder shape)
- [ ] Santiago metro cluster shows distinct commune boundaries
- [ ] Map renders completely — all 346 communes coloured by CEAD choropleth data
- [ ] Clicking a commune opens the commune detail panel (no regression)

### Fail criteria
- Any commune renders as a blank (no colour) — indicates a CEAD join regression
- Coastlines still appear as blocky straight-line polygons at moderate zoom
- Isla de Pascua or Juan Fernández are invisible (collapsed by simplification)
- Clicking a commune does not open the detail panel

---

## Gate 2 — Throttled-Mobile Pan/Zoom/Hover Performance (GEO-02 SC-3 / SC-4)

**What to verify:** With 7× more vertices than the prior asset (35,885 vs 5,085 arc points),
the map remains smooth during pan, zoom, and hover on a mid-range mobile profile — and the
browser console shows zero new errors.

### Setup

Use Chrome DevTools (or equivalent) to emulate a throttled mobile device:

1. Open DevTools → `More tools` → `Sensors` (for geolocation, if needed)
2. Open DevTools → `Network` tab → set throttling to **Fast 3G**
3. Open DevTools → `Performance` (or use the `Rendering` panel toggle for paint flashing)
4. Device emulation: select **Moto G4** preset (or set viewport to 375 × 667 px, mobile UA)
   - In Chrome: DevTools → Toggle device toolbar → select `Moto G4` from the device list
   - Alternatively: set viewport width to 375 px (the BrowserOS review equivalent per MEMORY)

Note: BrowserOS browser-review agents can emulate mobile via a 375 px iframe width.

### Steps

1. With the throttled-mobile profile active, open:
   - `http://localhost:4321/map/`
   - `http://localhost:4321/es/mapa/`
2. Open the browser **Console** tab — note any pre-existing warnings (baseline).
3. On each page, perform the following interactions and rate smoothness:
   - **Pan:** Click-drag the map across Chile (north to south, east to west). No visible stutter.
   - **Zoom in:** Pinch-zoom (or scroll) from national level to a city-level zoom (e.g. Santiago area). No freeze.
   - **Zoom out:** Return to national zoom. No jank.
   - **Hover:** Move the mouse/pointer slowly over several communes. Tooltip appears without lag.
   - **Click:** Click a commune. The detail panel opens within ~1 second.
4. After all interactions, inspect the **Console** for any new errors (red entries) that were not
   present before the interaction.

### Pass criteria
- [ ] Pan is smooth — no visible freeze or frame drop perceived as a stutter
- [ ] Zoom in/out completes without freezing the page
- [ ] Hover tooltips appear without perceptible delay (sub-500 ms feel)
- [ ] Commune detail panel opens on click (regression check)
- [ ] Console shows zero new **error**-level entries (red) after interactions
- [ ] Both `/map/` and `/es/mapa/` pass the above checks

### Fail criteria
- Pan or zoom freezes for more than ~2 seconds on Moto G4 + Fast 3G profile
- Hover tooltip lags significantly (>1 s delay) or causes visible flicker
- New console errors (red) appear after pan/zoom/hover that were not present on page load
- Detail panel does not open on click

---

## Additional Regression Checks (both gates)

These confirm no regressions to the choropleth or routing from Phase 3:

- [ ] All 346 communes display a choropleth colour (no grey "no data" communes visible at national zoom — unless the commune genuinely has no CEAD data, which should be noted)
- [ ] The `/methodology/` page (EN) displays the chilemapas attribution credit
- [ ] The `/es/metodologia/` page (ES) displays the chilemapas attribution credit (parity)
- [ ] No 404 errors on map page navigation links (e.g. `/map/` ↔ `/es/mapa/` toggle works)

---

## Sign-Off

After completing both gates, record the result here and resume the plan:

| Gate | Status | Tester | Date | Notes |
|------|--------|--------|------|-------|
| Gate 1 — Visual Recognizability | ✅ PASS | xenaquis | 2026-06-15 | Approved after local review on dev server (:4324) |
| Gate 2 — Throttled-Mobile Perf | ✅ PASS | xenaquis | 2026-06-15 | Approved; no perf/console issues reported |
| Regression checks | ✅ PASS | xenaquis | 2026-06-15 | Choropleth + attribution + nav confirmed |

**Resume signal:** Reply "approved" if all gates pass, or describe any visual/perf/console
issues found so they can be investigated and resolved before closing Phase 10.

---

## Context

- **Source:** chilemapas (GPL-3), github.com/pachadotdev/chilemapas, INE/SUBDERE/BCN-derived
- **Prior source:** GADM 4.1 L3 (retired — license-incompatible with AdSense + public repo)
- **Render path:** unchanged from Phase 3 — native `L.geoJSON()` + `L.canvas()` in `ChoroplethLayer.ts`
- **Phase-3 mobile gate device:** Moto G4 + Fast 3G (reused here for continuity)
- **Attribution pages:** `site/src/pages/methodology.astro` + `site/src/pages/es/metodologia.astro`
