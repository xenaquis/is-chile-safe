/**
 * map.mjs — Validator for map integration: TopoJSON budget + map pages + zero-React regression guard.
 *
 * Assertions:
 *   1. TopoJSON budget — data/cead/geo/communes.topo.json exists within the dual budget
 *      (raw < 430080 bytes AND gzip <= 143360 bytes; Phase 10).
 *      (Runs even without dist/ — committed asset assertion.)
 *   2. [dist/ required] dist/map/index.html and dist/es/mapa/index.html exist.
 *   3. [dist/ required] Each map page contains an astro-island element or MapIsland reference.
 *   4. [dist/ required] EN map page HTML contains locate aria-label "Show my location".
 *   5. [dist/ required] ES map page HTML contains locate aria-label "Mostrar mi ubicaci".
 *   6. [dist/ required] Zero-React regression guard: a sample content page (e.g. commune/santiago/)
 *      does NOT contain "astro-island" and does NOT reference "leaflet" in its HTML —
 *      proving content pages stay React/Leaflet-free after adding react() to astro.config.mjs.
 *
 *  11. Own basemap (quick-261124-bmp) — data/cead/geo/basemap.topo.json exists, is a
 *      Topology with a "land" object, within budget (raw <= 150 KB, gzip <= 60 KB), was
 *      built against the CURRENT communes.topo.json (meta.communesSha256), does NOT
 *      contain Chile (geometric probes) and DOES contain the neighbours, covers the
 *      min-zoom viewport, and records border gaps (meta.gaps) within 0.5 km2 per piece /
 *      5 km2 total. Label anchors (site/src/data/commune-label-points.json) are current
 *      and every one lies inside its own commune. (Runs without dist/.)
 *  12. Map source has no third-party tile host: no tileLayer / gridLayer / imageOverlay
 *      API at all (any casing, incl. .wms), no tile URL template, no https:// or quoted
 *      protocol-relative host outside a short allow-list; zoom cap is on L.map and is
 *      numerically <= 13; the basemap fetch is not inside the Promise.all that gates the
 *      choropleth. (Runs without dist/.)
 *  13. [dist/ required] Built bundle guard: no dist/_astro/*.js|css references a tile /
 *      basemap host or URL template; every https?:// host in those files is allow-listed;
 *      the island chunk named by both map pages exists (anti-vacuous) and the bundle
 *      credits chilemapas + Natural Earth. The two map pages' own HTML may load
 *      resources (script/link/img/iframe/source) only from allow-listed hosts.
 *
 * This file also runs as the site's `postbuild` step (package.json), so the production
 * build itself fails on a regression. It depends only on dist/ and committed data, never
 * on data age.
 *
 * If dist/ does not exist, exits 0 (pre-build checks still run).
 * Modelled on structure.mjs pattern.
 *
 * Usage:
 *   node scripts/validate/map.mjs          # TopoJSON check only (pre-build)
 *   npm run build && node scripts/validate/map.mjs  # full suite
 */

import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../..');
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

let failures = 0;

function pass(label) {
  console.log(`PASS [${label}]`);
}

function fail(label, msg) {
  console.error(`FAIL [${label}]: ${msg}`);
  failures++;
}

// ---------------------------------------------------------------------------
// Check 1: TopoJSON budget (runs without dist/)
// ---------------------------------------------------------------------------
const TOPO_PATH = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes.topo.json');
const TOPO_MAX_BYTES  = 430080; // 420 KB raw ceiling (≤420 KB raw AND ≤140 KB gzip budget)
const TOPO_GZIP_MAX   = 143360; // 140 KB gzip ceiling

if (!existsSync(TOPO_PATH)) {
  fail('TopoJSON exists', `File not found: data/cead/geo/communes.topo.json`);
} else {
  const topoBytes = readFileSync(TOPO_PATH);
  const size = topoBytes.length;
  if (size >= TOPO_MAX_BYTES) {
    fail('TopoJSON raw budget', `${size} bytes >= 420 KB (max ${TOPO_MAX_BYTES})`);
  } else {
    pass(`TopoJSON raw budget (${size} bytes < 420 KB)`);
  }

  const gz = gzipSync(topoBytes).length;
  if (gz > TOPO_GZIP_MAX) {
    fail('TopoJSON gzip budget', `${gz} B > 140 KB gzip (max ${TOPO_GZIP_MAX})`);
  } else {
    pass(`TopoJSON gzip budget (${gz} B < 140 KB)`);
  }

  // Also validate it's a proper TopoJSON with 346 features and Santiago CUT
  try {
    const topo = JSON.parse(readFileSync(TOPO_PATH, 'utf8'));
    if (topo.type !== 'Topology') {
      fail('TopoJSON type', 'Not a valid TopoJSON Topology');
    } else {
      const objKey = Object.keys(topo.objects)[0];
      const geoms = topo.objects[objKey].geometries;
      if (geoms.length !== 346) {
        fail('TopoJSON features', `Expected 346 features, got ${geoms.length}`);
      } else {
        pass('TopoJSON features (346)');
      }
      const sgo = geoms.find(g => g.properties && g.properties.id === '13101');
      if (!sgo) {
        fail('TopoJSON CUT join', 'Santiago (CUT 13101) not found — CUT join broken');
      } else {
        pass('TopoJSON CUT join (Santiago 13101 present)');
      }
    }
  } catch (e) {
    fail('TopoJSON parse', `JSON parse error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Check 11: own basemap asset (runs without dist/)
// The map draws its own basemap; a third-party tile service broke it once
// (API-key watermark on every tile, 2026-11-24) and must never come back.
// ---------------------------------------------------------------------------
const BASEMAP_PATH = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'basemap.topo.json');
const BASEMAP_MAX_BYTES = 153600; // 150 KB raw ceiling
const BASEMAP_GZIP_MAX = 61440;   // 60 KB gzip ceiling
const GAP_MAX_PIECE_KM2 = 0.5;    // same limits as scripts/build-basemap.mjs
const GAP_MAX_TOTAL_KM2 = 5;

function ringHas(ring, x, y) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

if (!existsSync(BASEMAP_PATH)) {
  fail('basemap exists', 'File not found: data/cead/geo/basemap.topo.json — run node scripts/build-basemap.mjs');
} else {
  try {
    const bytes = readFileSync(BASEMAP_PATH);
    const gz = gzipSync(bytes).length;
    if (bytes.length > BASEMAP_MAX_BYTES) fail('basemap raw budget', `${bytes.length} B > 150 KB (max ${BASEMAP_MAX_BYTES})`);
    else pass(`basemap raw budget (${bytes.length} bytes <= 150 KB)`);
    if (gz > BASEMAP_GZIP_MAX) fail('basemap gzip budget', `${gz} B > 60 KB gzip (max ${BASEMAP_GZIP_MAX})`);
    else pass(`basemap gzip budget (${gz} B <= 60 KB)`);

    const bm = JSON.parse(bytes.toString('utf8'));
    if (bm.type !== 'Topology' || !bm.objects || !bm.objects.land) {
      fail('basemap type', 'Not a TopoJSON Topology with a "land" object');
    } else {
      pass('basemap type (Topology, object "land")');

      // Staleness: the land was erased against a specific communes.topo.json.
      if (existsSync(TOPO_PATH)) {
        const cur = createHash('sha256').update(readFileSync(TOPO_PATH)).digest('hex');
        if (!bm.meta || bm.meta.communesSha256 !== cur) {
          fail(
            'basemap matches communes.topo.json',
            'meta.communesSha256 differs from the current communes.topo.json — re-run node scripts/build-basemap.mjs'
          );
        } else {
          pass('basemap matches communes.topo.json (sha256)');
        }
      }

      // No property may identify a country (single dissolved mass, no borders).
      const geoms = bm.objects.land.geometries ?? [bm.objects.land];
      const tagged = geoms.filter((g) => g.properties && Object.keys(g.properties).length > 0);
      if (tagged.length) fail('basemap has no country properties', `${tagged.length} geometry(ies) carry properties`);
      else pass('basemap has no country properties');

      // Geometric probes (a property check would pass vacuously on a dissolved mass).
      const require = createRequire(path.join(SITE_ROOT, 'package.json'));
      const { feature } = require('topojson-client');
      const fc = feature(bm, bm.objects.land);
      const polys = [];
      for (const f of fc.type === 'FeatureCollection' ? fc.features : [fc]) {
        if (!f.geometry) continue;
        if (f.geometry.type === 'Polygon') polys.push(f.geometry.coordinates);
        else if (f.geometry.type === 'MultiPolygon') polys.push(...f.geometry.coordinates);
      }
      const inLand = (lng, lat) =>
        polys.some((p) => ringHas(p[0], lng, lat) && !p.slice(1).some((h) => ringHas(h, lng, lat)));

      const chilePoints = { Santiago: [-70.65, -33.45], Calama: [-68.93, -22.46], Temuco: [-72.6, -38.74] };
      // + every commune centroid shipped with the site (345 points)
      const CENTROIDS = path.join(SITE_ROOT, 'src', 'data', 'comuna-centroids.json');
      if (existsSync(CENTROIDS)) {
        for (const c of JSON.parse(readFileSync(CENTROIDS, 'utf8'))) chilePoints[`cut ${c.cut}`] = [c.lng, c.lat];
      }
      const chileInside = Object.entries(chilePoints).filter(([, [x, y]]) => inLand(x, y)).map(([n]) => n);
      // Centroids are ring averages and can fall just outside a concave commune;
      // a real "Chile was not erased" regression puts hundreds inside, not a handful.
      if (chileInside.includes('Santiago') || chileInside.includes('Calama') || chileInside.includes('Temuco') || chileInside.length > 5) {
        fail('basemap excludes Chile', `${chileInside.length} Chilean point(s) inside neighbour land: ${chileInside.slice(0, 6).join(', ')}`);
      } else {
        pass(`basemap excludes Chile (${Object.keys(chilePoints).length} probes, ${chileInside.length} edge case(s))`);
      }

      const neighbours = { Mendoza: [-68.84, -32.89], 'La Paz': [-68.13, -16.5], Lima: [-76.9, -12.0], Tacna: [-70.25, -18.01], 'Buenos Aires (W)': [-59.0, -34.8] };
      const missing = Object.entries(neighbours).filter(([, [x, y]]) => !inLand(x, y)).map(([n]) => n);
      if (missing.length) fail('basemap contains neighbours', `not inside land: ${missing.join(', ')}`);
      else pass('basemap contains neighbours (Mendoza, La Paz, Lima, Tacna, Buenos Aires)');

      // Coverage: maxBounds only limits the map CENTRE. At min zoom 4 a 1440 px
      // viewport shows lng -134..-8 — land clipped tighter ends in a straight cut.
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const p of polys) for (const [x, y] of p[0]) {
        if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
      }
      if (minX > -134 || maxX < -8 || minY > -70 || maxY < 5) {
        fail('basemap covers min-zoom viewport', `bbox [${minX}, ${minY}, ${maxX}, ${maxY}] must cover lng -134..-8, lat -70..5`);
      } else {
        pass('basemap covers min-zoom viewport');
      }

      // Border gaps measured by build-basemap.mjs (enclosed sea-coloured pockets
      // between the neighbour land and the communes). Recomputing them needs
      // mapshaper, so the build script records them and this gate re-checks.
      const gaps = bm.meta && bm.meta.gaps;
      if (!gaps || !Number.isFinite(gaps.maxKm2) || !Number.isFinite(gaps.totalKm2)) {
        fail('basemap border gaps', 'meta.gaps missing — re-run node scripts/build-basemap.mjs');
      } else if (gaps.maxKm2 > GAP_MAX_PIECE_KM2 || gaps.totalKm2 > GAP_MAX_TOTAL_KM2) {
        fail('basemap border gaps', `largest ${gaps.maxKm2} km2 (max ${GAP_MAX_PIECE_KM2}), total ${gaps.totalKm2} km2 (max ${GAP_MAX_TOTAL_KM2})`);
      } else {
        pass(`basemap border gaps (${gaps.pieces} hairline(s), ${gaps.totalKm2} km2 total, largest ${gaps.maxKm2} km2)`);
      }
    }
  } catch (e) {
    fail('basemap parse', `error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Check 11b: label anchors. Place names are drawn at these points; a vertex
// average put 16 of 346 names on a neighbouring commune or in the sea.
// ---------------------------------------------------------------------------
const LABEL_POINTS_PATH = path.join(SITE_ROOT, 'src', 'data', 'commune-label-points.json');
if (!existsSync(LABEL_POINTS_PATH)) {
  fail('label anchors exist', 'site/src/data/commune-label-points.json not found — run node scripts/build-basemap.mjs');
} else if (existsSync(TOPO_PATH)) {
  try {
    const lp = JSON.parse(readFileSync(LABEL_POINTS_PATH, 'utf8'));
    const topoBuf = readFileSync(TOPO_PATH);
    if (lp.communesSha256 !== createHash('sha256').update(topoBuf).digest('hex')) {
      fail('label anchors match communes.topo.json', 'communesSha256 is stale — re-run node scripts/build-basemap.mjs');
    } else {
      pass('label anchors match communes.topo.json (sha256)');
    }
    const require = createRequire(path.join(SITE_ROOT, 'package.json'));
    const { feature } = require('topojson-client');
    const topo = JSON.parse(topoBuf.toString('utf8'));
    const fc = feature(topo, topo.objects[Object.keys(topo.objects)[0]]);
    const outside = [];
    let checked = 0;
    for (const f of fc.features) {
      const cut = f.properties && f.properties.id;
      const g = f.geometry;
      if (!cut || !g) continue;
      const pt = lp.points && lp.points[cut];
      if (!Array.isArray(pt)) { outside.push(`${cut} (missing)`); continue; }
      const [lat, lng] = pt;
      const polysOf = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
      const inside = polysOf.some((p) => ringHas(p[0], lng, lat) && !p.slice(1).some((h) => ringHas(h, lng, lat)));
      checked++;
      if (!inside) outside.push(String(cut));
    }
    if (outside.length || checked !== 346) {
      fail('label anchors inside own commune', `${outside.length} outside/missing of ${checked}: ${outside.slice(0, 8).join(', ')}`);
    } else {
      pass(`label anchors inside own commune (${checked}/346)`);
    }
  } catch (e) {
    fail('label anchors parse', `error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Check 12: map SOURCE has no third-party tile host (runs without dist/)
// ---------------------------------------------------------------------------
// Never ban bare {x} / {s} (minified template literals) or the word tileLayer
// in the BUILT bundle (Leaflet is bundled whole); the source may be stricter.
const TILE_HOST_RE =
  /cartocdn|basemaps\.|openstreetmap|carto\.com|\{z\}|\/\{x\}\/\{y\}|mapbox|maptiler|stadiamaps|arcgisonline|thunderforest|stamen|tiles?\.[a-z0-9-]+\.(?:com|org|net|io)\b/i;
const SOURCE_HOST_ALLOW = new Set(['github.com', 'www.naturalearthdata.com', 'www.w3.org']);
// Absolute hosts, plus protocol-relative ones when they open a string literal
// ("//host.tld/..."): Leaflet accepts those as layer URLs too.
const HOST_RE = /(?:https?:\/\/|["'`]\/\/)([a-z0-9.-]+\.[a-z]{2,})/gi;
// Any Leaflet API that fetches imagery from a URL — every casing, call or member
// access (L.tileLayer.wms, new L.TileLayer, L.GridLayer.extend, L.imageOverlay).
const TILE_API_RE = /\b(?:tileLayer|TileLayer|gridLayer|GridLayer|imageOverlay|ImageOverlay|videoOverlay|VideoOverlay)\b/;
const MAX_ZOOM_CEILING = 13;

const MAP_SRC_DIR = path.join(SITE_ROOT, 'src', 'components', 'map');
if (!existsSync(MAP_SRC_DIR)) {
  fail('map source dir', 'site/src/components/map not found');
} else {
  const srcFiles = readdirSync(MAP_SRC_DIR)
    .filter((f) => /\.(tsx?|css)$/.test(f))
    .map((f) => path.join(MAP_SRC_DIR, f))
    .concat([path.join(SITE_ROOT, 'src', 'lib', 'basemapLabels.ts'), path.join(SITE_ROOT, 'src', 'config', 'mapV2Strings.ts')])
    .filter((f) => existsSync(f));
  // The site-wide `svg { max-width: 100% }` reset collapses the basemap's SVG
  // renderer (custom pane) to zero width unless map.css exempts it — the land
  // is then in the DOM but invisible, and nothing else would notice.
  const mapCss = readFileSync(path.join(MAP_SRC_DIR, 'map.css'), 'utf8');
  if (!/\.leaflet-basemap-pane svg\s*\{[^}]*max-width:\s*none\s*!important/.test(mapCss)) {
    fail('basemap SVG visible', 'map.css must keep `.leaflet-container .leaflet-basemap-pane svg { max-width: none !important }`');
  } else {
    pass('basemap SVG visible (max-width reset exempted)');
  }

  const offenders = [];
  for (const f of srcFiles) {
    const text = readFileSync(f, 'utf8');
    const rel = path.relative(SITE_ROOT, f);
    const api = text.match(TILE_API_RE);
    if (api) offenders.push(`${rel}: ${api[0]} (imagery-from-URL Leaflet API)`);
    const m = text.match(TILE_HOST_RE);
    if (m) offenders.push(`${rel}: "${m[0]}"`);
    for (const h of text.matchAll(HOST_RE)) {
      if (!SOURCE_HOST_ALLOW.has(h[1].toLowerCase())) offenders.push(`${rel}: host ${h[1]}`);
    }
  }
  if (offenders.length) fail('map source: no third-party tile host', offenders.slice(0, 8).join(' | '));
  else pass(`map source: no third-party tile host (${srcFiles.length} files)`);

  const islandSrc = readFileSync(path.join(MAP_SRC_DIR, 'MapIsland.tsx'), 'utf8');
  if (!/maxZoom:\s*MAP_MAX_ZOOM/.test(islandSrc)) {
    fail('zoom cap on L.map', 'MapIsland.tsx must pass maxZoom: MAP_MAX_ZOOM to L.map() (no tile layer => Infinity otherwise)');
  } else {
    pass('zoom cap on L.map (MAP_MAX_ZOOM)');
  }
  // The numeric value too: vitest pins it, but vitest is not part of the build.
  const labelsSrc = readFileSync(path.join(SITE_ROOT, 'src', 'lib', 'basemapLabels.ts'), 'utf8');
  const capM = labelsSrc.match(/export const MAP_MAX_ZOOM\s*=\s*(\d+)\s*;/);
  if (!capM) fail('zoom cap value', 'could not read MAP_MAX_ZOOM from src/lib/basemapLabels.ts');
  else if (Number(capM[1]) > MAX_ZOOM_CEILING) fail('zoom cap value', `MAP_MAX_ZOOM is ${capM[1]} (> ${MAX_ZOOM_CEILING}): there is no street layer to show at deeper zoom`);
  else pass(`zoom cap value (MAP_MAX_ZOOM = ${capM[1]} <= ${MAX_ZOOM_CEILING})`);
  const literalZooms = [];
  for (const f of srcFiles) {
    const text = readFileSync(f, 'utf8');
    for (const m of text.matchAll(/(?:maxZoom|minZoom)\s*:\s*(\d+)|\.(?:flyTo|setView)\(\s*\[[^\]]*\]\s*,\s*(\d+)|\.setZoom\(\s*(\d+)/g)) {
      const z = Number(m[1] ?? m[2] ?? m[3]);
      if (z > MAX_ZOOM_CEILING) literalZooms.push(`${path.relative(SITE_ROOT, f)}: ${m[0]}`);
    }
  }
  if (literalZooms.length) fail('no zoom request above the cap', literalZooms.slice(0, 6).join(' | '));
  else pass('no zoom request above the cap');
  const pa = islandSrc.indexOf('Promise.all([');
  const paBlock = pa >= 0 ? islandSrc.slice(pa, islandSrc.indexOf(']);', pa)) : '';
  if (!paBlock) fail('basemap is progressive', 'could not locate the Promise.all block in MapIsland.tsx');
  else if (/basemap/i.test(paBlock)) fail('basemap is progressive', 'the basemap fetch is inside the Promise.all that gates the choropleth');
  else pass('basemap is progressive (not in the choropleth Promise.all)');
}

// ---------------------------------------------------------------------------
// If dist/ does not exist, exit 0 — HTML checks require a build
// ---------------------------------------------------------------------------
if (!existsSync(DIST_DIR)) {
  console.log('\nmap: dist/ not found — skipping HTML checks (run npm run build first)');
  if (failures > 0) {
    console.error(`\nmap.mjs: FAILED (${failures} failure(s) — pre-build checks)`);
    process.exit(1);
  }
  console.log('\nmap.mjs: PASSED (pre-build checks only)');
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Check 2: Map pages exist in dist/
// Wave 0 note: map pages (map.astro / mapa.astro) are created in Wave 1.
// If they are not present, warn but do not fail — Wave 0 validation skips map page checks.
// ---------------------------------------------------------------------------
const MAP_EN = path.join(DIST_DIR, 'map', 'index.html');
const MAP_ES = path.join(DIST_DIR, 'es', 'mapa', 'index.html');

const mapPagesExist = existsSync(MAP_EN) && existsSync(MAP_ES);

if (!existsSync(MAP_EN)) {
  console.log('map: dist/map/index.html not found — map pages not yet built (Wave 1)');
} else {
  pass('map EN page exists');
}

if (!existsSync(MAP_ES)) {
  console.log('map: dist/es/mapa/index.html not found — map pages not yet built (Wave 1)');
} else {
  pass('map ES page exists');
}

// ---------------------------------------------------------------------------
// Check 3-5: Map page content assertions (island + aria-labels)
// ---------------------------------------------------------------------------
function checkMapPage(htmlPath, lang, label) {
  if (!existsSync(htmlPath)) {
    // Not yet built — skip silently
    return;
  }
  const html = readFileSync(htmlPath, 'utf-8');

  // Check for island marker (astro-island element or MapIsland reference)
  const hasIsland = html.includes('astro-island') || html.includes('MapIsland');
  if (!hasIsland) {
    fail(`${label} island marker`, 'No astro-island element or MapIsland reference found');
  } else {
    pass(`${label} island marker`);
  }

  // Check aria-labels for locate button
  if (lang === 'en') {
    if (!html.includes('Show my location')) {
      fail(`${label} locate aria-label`, 'Missing aria-label "Show my location"');
    } else {
      pass(`${label} locate aria-label`);
    }
  } else {
    if (!html.includes('Mostrar mi ubicaci')) {
      fail(`${label} locate aria-label`, 'Missing aria-label containing "Mostrar mi ubicaci"');
    } else {
      pass(`${label} locate aria-label`);
    }
  }
}

checkMapPage(MAP_EN, 'en', 'EN map');
checkMapPage(MAP_ES, 'es', 'ES map');

// ---------------------------------------------------------------------------
// Check 6: Zero-React regression guard on content pages
// ---------------------------------------------------------------------------
// Verify that content pages (commune/region/crime) do NOT contain astro-island
// or leaflet references — adding react() to astro.config must not pollute them.
function findSampleContentPage() {
  // Try commune/santiago first (most reliable)
  const santiago = path.join(DIST_DIR, 'commune', 'santiago', 'index.html');
  if (existsSync(santiago)) return { path: santiago, label: 'commune/santiago' };

  // Fall back to first commune directory found
  const communeDir = path.join(DIST_DIR, 'commune');
  if (existsSync(communeDir)) {
    const first = readdirSync(communeDir, { withFileTypes: true })
      .find(d => d.isDirectory());
    if (first) {
      const p = path.join(communeDir, first.name, 'index.html');
      if (existsSync(p)) return { path: p, label: `commune/${first.name}` };
    }
  }

  // Fall back to region page
  const regionDir = path.join(DIST_DIR, 'region');
  if (existsSync(regionDir)) {
    const first = readdirSync(regionDir, { withFileTypes: true })
      .find(d => d.isDirectory());
    if (first) {
      const p = path.join(regionDir, first.name, 'index.html');
      if (existsSync(p)) return { path: p, label: `region/${first.name}` };
    }
  }

  return null;
}

const sample = findSampleContentPage();
if (!sample) {
  console.log('map: no content pages in dist/ — skipping zero-React regression guard');
} else {
  const html = readFileSync(sample.path, 'utf-8');

  // Content pages must NOT have astro-island (would mean a React island loaded here)
  if (html.includes('astro-island')) {
    fail(
      `zero-React guard [${sample.label}]`,
      'Content page contains "astro-island" — React island is leaking into content pages'
    );
  } else {
    pass(`zero-React guard [${sample.label}] — no astro-island`);
  }

  // Content pages must NOT reference leaflet (CSS or JS)
  if (html.toLowerCase().includes('leaflet')) {
    fail(
      `zero-Leaflet guard [${sample.label}]`,
      'Content page references "leaflet" — Leaflet is leaking into content pages'
    );
  } else {
    pass(`zero-Leaflet guard [${sample.label}] — no leaflet reference`);
  }
}

// ---------------------------------------------------------------------------
// Check 7: Runtime data is served from dist/data (the island fetches
// /data/cead/* in the browser; if these are not published the map loads empty).
// Regression guard for the prebuild sync-data step.
// ---------------------------------------------------------------------------
const RUNTIME_DATA_ASSETS = [
  'data/cead/geo/communes.topo.json',
  'data/cead/geo/basemap.topo.json',
  'data/cead/map-payload.json',
  'data/cead/meta/index.json',
  'data/cead/comunas/13101.json',
];
for (const rel of RUNTIME_DATA_ASSETS) {
  const p = path.join(DIST_DIR, rel);
  if (existsSync(p)) {
    pass(`runtime data served — dist/${rel}`);
  } else {
    fail(
      `runtime data served — dist/${rel}`,
      `Map island fetches /${rel} at runtime but it is missing from dist/. ` +
        `Ensure scripts/sync-data.mjs runs (predev/prebuild) so public/data is published.`
    );
  }
}

// ---------------------------------------------------------------------------
// Check 13: built bundle guard — no third-party tile / basemap host.
// Scans dist/_astro/*.js|css ONLY (dist/data holds press URLs that legitimately
// mention such hosts).
// ---------------------------------------------------------------------------
const ASTRO_DIR = path.join(DIST_DIR, '_astro');
const BUNDLE_HOST_ALLOW = new Set([
  'www.w3.org',               // SVG/XHTML namespaces
  'leafletjs.com',            // Leaflet's own attribution prefix constant
  'react.dev',                // React error-decoder links
  'fonts.googleapis.com',     // site font CSS (pre-existing, not the map)
  'fonts.gstatic.com',
  'ischilesafe.com',
  'www.ischilesafe.com',
  'github.com',               // chilemapas credit link
  'www.naturalearthdata.com', // Natural Earth credit link
]);
if (!existsSync(ASTRO_DIR)) {
  fail('bundle guard', 'dist/_astro not found');
} else {
  const assets = readdirSync(ASTRO_DIR).filter((f) => /\.(js|css)$/.test(f));
  const texts = new Map(assets.map((f) => [f, readFileSync(path.join(ASTRO_DIR, f), 'utf8')]));

  // Anti-vacuous: the island chunk both map pages point at must be among the scanned files.
  for (const [page, label] of [[MAP_EN, 'EN'], [MAP_ES, 'ES']]) {
    if (!existsSync(page)) continue;
    const m = readFileSync(page, 'utf-8').match(/component-url="\/_astro\/(MapIsland\.[^"]+\.js)"/);
    if (!m) fail(`bundle guard: ${label} island chunk`, 'no component-url="/_astro/MapIsland.*.js" in the map page');
    else if (!texts.has(m[1])) fail(`bundle guard: ${label} island chunk`, `${m[1]} not found in dist/_astro`);
    else pass(`bundle guard: ${label} island chunk scanned (${m[1]})`);
  }
  const all = [...texts.values()].join('\n');
  if (!all.includes('leaflet-container')) fail('bundle guard: Leaflet scanned', 'no scanned chunk contains "leaflet-container"');
  else pass('bundle guard: Leaflet scanned');

  const hits = [];
  const badHosts = new Set();
  for (const [f, text] of texts) {
    const m = text.match(TILE_HOST_RE);
    if (m) hits.push(`${f}: "${m[0]}"`);
    for (const h of text.matchAll(HOST_RE)) {
      if (!BUNDLE_HOST_ALLOW.has(h[1].toLowerCase())) badHosts.add(`${f}: ${h[1]}`);
    }
  }
  if (hits.length) fail('bundle guard: no tile host / URL template', hits.slice(0, 8).join(' | '));
  else pass(`bundle guard: no tile host / URL template (${assets.length} files)`);
  if (badHosts.size) {
    fail(
      'bundle guard: host allow-list',
      `${[...badHosts].slice(0, 8).join(' | ')} — the map must not depend on an external runtime host; ` +
        'if this is a plain credit link, add it to BUNDLE_HOST_ALLOW in validate/map.mjs'
    );
  } else {
    pass('bundle guard: host allow-list');
  }

  // The map pages' own HTML: resource-loading tags may only point at allow-listed
  // hosts (a <script src> / preconnect to a map CDN would bypass the chunk scan).
  // Anchors, canonical and hreflang links are navigation, not runtime dependencies.
  const HTML_HOST_ALLOW = new Set([
    'ischilesafe.com',
    'www.ischilesafe.com',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'pagead2.googlesyndication.com', // AdSense loader, only when the publisher id is configured
  ]);
  for (const [page, label] of [[MAP_EN, 'EN'], [MAP_ES, 'ES']]) {
    if (!existsSync(page)) continue;
    const html = readFileSync(page, 'utf-8');
    const bad = [];
    for (const tag of html.matchAll(/<(script|link|img|iframe|source|embed|object)\b[^>]*>/gi)) {
      const t = tag[0];
      if (/^<link\b/i.test(t) && /\brel\s*=\s*["']?(?:canonical|alternate)\b/i.test(t)) continue;
      for (const u of t.matchAll(/\b(?:src|href|data|srcset)\s*=\s*["']?\s*(?:https?:)?\/\/([a-z0-9.-]+\.[a-z]{2,})/gi)) {
        if (!HTML_HOST_ALLOW.has(u[1].toLowerCase())) bad.push(`<${tag[1]}> ${u[1]}`);
      }
      const th = t.match(TILE_HOST_RE);
      if (th) bad.push(`<${tag[1]}> "${th[0]}"`);
    }
    if (bad.length) fail(`bundle guard: ${label} map page HTML hosts`, [...new Set(bad)].slice(0, 8).join(' | '));
    else pass(`bundle guard: ${label} map page HTML loads no third-party map host`);
  }

  if (!all.includes('chilemapas') || !all.includes('Natural Earth')) {
    fail('bundle guard: attribution', 'built bundle must credit both "chilemapas" and "Natural Earth"');
  } else {
    pass('bundle guard: attribution (chilemapas + Natural Earth)');
  }
}

// ---------------------------------------------------------------------------
// Check 8: homicide rate field ('hr') present in map-payload
// (14-02 ships abbreviated key 'hr' instead of 'homicide_rate' — budget escape D-09)
// Runs without dist/ — committed data asset assertion.
// ---------------------------------------------------------------------------
const MAP_PAYLOAD_PATH = path.join(REPO_ROOT, 'data', 'cead', 'map-payload.json');
if (!existsSync(MAP_PAYLOAD_PATH)) {
  fail('homicide in payload', 'data/cead/map-payload.json not found — run scrape_cead.py');
} else {
  try {
    const payload = JSON.parse(readFileSync(MAP_PAYLOAD_PATH, 'utf8'));
    const sample = payload.comunas?.slice(0, 10) ?? [];
    const hasHomicide = sample.some(c => 'hr' in c);
    if (!hasHomicide) {
      fail('homicide in payload', 'map-payload.json comunas missing hr (homicide rate) — subgroup-101 scrape not run');
    } else {
      pass('homicide_rate in map-payload');
    }
  } catch (e) {
    fail('homicide in payload', `JSON parse error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Check 9: Santiago (13101) has non-empty homicidios in featured_rates
// Runs without dist/ — committed data asset assertion.
// ---------------------------------------------------------------------------
const SANTIAGO_PATH = path.join(REPO_ROOT, 'data', 'cead', 'comunas', '13101.json');
if (!existsSync(SANTIAGO_PATH)) {
  fail('homicide in 13101.json', 'data/cead/comunas/13101.json not found — run scrape_cead.py');
} else {
  try {
    const com = JSON.parse(readFileSync(SANTIAGO_PATH, 'utf8'));
    const hom = com.featured_rates?.homicidios ?? {};
    if (Object.keys(hom).length === 0) {
      fail('homicide in 13101.json', 'Santiago featured_rates.homicidios is empty — subgroup-101 scrape needed');
    } else {
      pass(`homicide in 13101.json (${Object.keys(hom).length} years)`);
    }
  } catch (e) {
    fail('homicide in 13101.json', `JSON parse error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Check 10 (MPX-A6): TopoJSON ids and map-payload.json comuna ids are the
// SAME set. bandStats.ts / applyBandDim key band isolation purely off CUT —
// a mismatch here would silently leave orphan polygons unstyled (never
// dimmed, never isolated) or orphan payload rows with no polygon to color.
// Runs without dist/ — committed data asset assertion.
// ---------------------------------------------------------------------------
if (existsSync(TOPO_PATH) && existsSync(MAP_PAYLOAD_PATH)) {
  try {
    const topo = JSON.parse(readFileSync(TOPO_PATH, 'utf8'));
    const payload = JSON.parse(readFileSync(MAP_PAYLOAD_PATH, 'utf8'));
    const objKey = Object.keys(topo.objects)[0];
    const topoIds = new Set(
      (topo.objects[objKey]?.geometries ?? [])
        .map((g) => g.properties && g.properties.id)
        .filter(Boolean)
    );
    const payloadIds = new Set((payload.comunas ?? []).map((c) => c.id));

    const missingFromPayload = [...topoIds].filter((id) => !payloadIds.has(id));
    const missingFromTopo = [...payloadIds].filter((id) => !topoIds.has(id));

    if (topoIds.size === payloadIds.size && missingFromPayload.length === 0 && missingFromTopo.length === 0) {
      pass(`TopoJSON <-> map-payload id sets match (${topoIds.size} ids)`);
    } else {
      fail(
        'TopoJSON <-> map-payload id sets',
        `topo=${topoIds.size} payload=${payloadIds.size}; ` +
          `missing from payload: ${missingFromPayload.slice(0, 5).join(',') || 'none'}` +
          (missingFromPayload.length > 5 ? `(+${missingFromPayload.length - 5} more)` : '') +
          `; missing from topo: ${missingFromTopo.slice(0, 5).join(',') || 'none'}` +
          (missingFromTopo.length > 5 ? `(+${missingFromTopo.length - 5} more)` : '')
      );
    }
  } catch (e) {
    fail('TopoJSON <-> map-payload id sets', `parse error: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nmap.mjs: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\nmap.mjs: PASSED — all map validator checks passed');
