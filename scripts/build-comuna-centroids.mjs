/**
 * build-comuna-centroids.mjs — emits site/src/data/comuna-centroids.json
 *
 * OPTIONAL. Only needed for the directory's "Near me / Cerca de mí" button.
 * Without this file the button is simply not rendered (see CommuneDirectory.astro).
 *
 * Source: data/cead/geo/communes-chilemapas.geojson — the same committed
 * boundary file scripts/build-topojson.mjs consumes. codigo_comuna is the
 * 5-char zero-padded INE CUT; index.json stores it unpadded, so the join uses
 * the same srcCodeToCut() normalization as build-topojson.mjs.
 *
 * Centroid = area-weighted mean of the ring vertices per polygon, which is
 * good enough for "which commune is nearest to me" (the map island keeps its
 * exact point-in-polygon path in UserLocationMarker.ts — this is not a
 * replacement for it).
 *
 * Antártica (12202) is absent from chilemapas, exactly as in build-topojson.mjs;
 * it is skipped here rather than given a placeholder — a placeholder centroid
 * would be a wrong answer to "nearest commune".
 *
 * Run: node scripts/build-comuna-centroids.mjs
 * Output: ~12 KB JSON, committed to the repo (no build-time dependency).
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');

const GEOJSON = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes-chilemapas.geojson');
const INDEX_JSON = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
const OUT = path.join(REPO_ROOT, 'site', 'src', 'data', 'comuna-centroids.json');

if (!existsSync(GEOJSON)) {
  console.error(`ERROR: ${GEOJSON} not found.`);
  process.exit(1);
}

const srcCodeToCut = (code) => String(parseInt(code, 10));

const geo = JSON.parse(readFileSync(GEOJSON, 'utf8'));
const index = JSON.parse(readFileSync(INDEX_JSON, 'utf8'));
const wantCuts = new Set(index.map((c) => c.cut));

function ringCentroid(ring) {
  // Shoelace centroid; falls back to vertex mean for degenerate rings.
  let a = 0, cx = 0, cy = 0;
  for (let i = 0, n = ring.length - 1; i < n; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[i + 1];
    const f = x0 * y1 - x1 * y0;
    a += f;
    cx += (x0 + x1) * f;
    cy += (y0 + y1) * f;
  }
  if (Math.abs(a) < 1e-12) {
    const n = ring.length;
    return { lng: ring.reduce((s, p) => s + p[0], 0) / n, lat: ring.reduce((s, p) => s + p[1], 0) / n, area: 0 };
  }
  a *= 0.5;
  return { lng: cx / (6 * a), lat: cy / (6 * a), area: Math.abs(a) };
}

function featureCentroid(geometry) {
  const polys = geometry.type === 'Polygon' ? [geometry.coordinates]
    : geometry.type === 'MultiPolygon' ? geometry.coordinates
    : null;
  if (!polys) return null;
  let tA = 0, tx = 0, ty = 0, fallback = null;
  for (const poly of polys) {
    const c = ringCentroid(poly[0]);
    if (!fallback) fallback = c;
    tA += c.area;
    tx += c.lng * c.area;
    ty += c.lat * c.area;
  }
  if (tA === 0) return fallback ? { lat: fallback.lat, lng: fallback.lng } : null;
  return { lat: ty / tA, lng: tx / tA };
}

const out = [];
const seen = new Set();
for (const f of geo.features) {
  const code = f.properties && f.properties.codigo_comuna;
  if (!code) continue;
  const cut = srcCodeToCut(code);
  if (!wantCuts.has(cut) || seen.has(cut)) continue;
  const c = featureCentroid(f.geometry);
  if (!c) continue;
  seen.add(cut);
  out.push({ cut, lat: Number(c.lat.toFixed(4)), lng: Number(c.lng.toFixed(4)) });
}

out.sort((a, b) => a.cut.localeCompare(b.cut));

const missing = [...wantCuts].filter((c) => !seen.has(c));
console.log(`Centroids: ${out.length} / ${wantCuts.size}`);
if (missing.length) console.log(`Not in chilemapas (expected: 12202 Antártica): ${missing.join(', ')}`);

if (out.length < 340) {
  console.error('FATAL: fewer than 340 centroids resolved — check the code-join.');
  process.exit(1);
}

mkdirSync(path.dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(out));
console.log(`SUCCESS: ${OUT} (${JSON.stringify(out).length} bytes)`);
