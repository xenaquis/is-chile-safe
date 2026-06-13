/**
 * map.mjs — Validator for map integration: TopoJSON budget + map pages + zero-React regression guard.
 *
 * Assertions:
 *   1. TopoJSON budget — data/cead/geo/communes.topo.json exists and size < 102400 bytes.
 *      (Runs even without dist/ — committed asset assertion.)
 *   2. [dist/ required] dist/map/index.html and dist/es/mapa/index.html exist.
 *   3. [dist/ required] Each map page contains an astro-island element or MapIsland reference.
 *   4. [dist/ required] EN map page HTML contains locate aria-label "Show my location".
 *   5. [dist/ required] ES map page HTML contains locate aria-label "Mostrar mi ubicaci".
 *   6. [dist/ required] Zero-React regression guard: a sample content page (e.g. commune/santiago/)
 *      does NOT contain "astro-island" and does NOT reference "leaflet" in its HTML —
 *      proving content pages stay React/Leaflet-free after adding react() to astro.config.mjs.
 *
 * If dist/ does not exist, exits 0 (TopoJSON check still runs).
 * Modelled on structure.mjs pattern.
 *
 * Usage:
 *   node scripts/validate/map.mjs          # TopoJSON check only (pre-build)
 *   npm run build && node scripts/validate/map.mjs  # full suite
 */

import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
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
const TOPO_MAX_BYTES = 102400; // 100 KB

if (!existsSync(TOPO_PATH)) {
  fail('TopoJSON exists', `File not found: data/cead/geo/communes.topo.json`);
} else {
  const size = statSync(TOPO_PATH).size;
  if (size >= TOPO_MAX_BYTES) {
    fail('TopoJSON budget', `${size} bytes >= 100 KB (max ${TOPO_MAX_BYTES})`);
  } else {
    pass(`TopoJSON budget (${size} bytes < 100 KB)`);
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
// If dist/ does not exist, exit 0 — HTML checks require a build
// ---------------------------------------------------------------------------
if (!existsSync(DIST_DIR)) {
  console.log('\nmap: dist/ not found — skipping HTML checks (run npm run build first)');
  if (failures > 0) {
    console.error(`\nmap.mjs: FAILED (${failures} failure(s) — TopoJSON checks)`);
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
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nmap.mjs: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\nmap.mjs: PASSED — all map validator checks passed');
