/**
 * build-topojson.mjs — Offline pipeline to produce data/cead/geo/communes.topo.json
 *
 * Source dataset: chilemapas (GPL-3) — INE/SUBDERE/BCN-authoritative Chilean commune boundaries
 * GitHub: https://github.com/pachadotdev/chilemapas  (branch: master, data_geojson/comunas/)
 * Downloaded: 2026-06-15 — merged 16 regional GeoJSONs into communes-chilemapas.geojson
 * License: GPL-3. Attribution required. See site methodology/colophon for visible credit.
 * Saved as: data/cead/geo/communes-chilemapas.geojson (committed for offline reproducibility)
 *
 * Pipeline:
 *   1. Load chilemapas GeoJSON (345 features, codigo_comuna = 5-char zero-padded CUT)
 *   2. Load data/cead/meta/index.json (346-commune CUT source of truth)
 *   3. Re-key each chilemapas feature → CUT via srcCodeToCut(codigo_comuna) code-join
 *      (strips leading zeros: "02101" → "2101"; no-op for regions 10+)
 *      Drop all properties except id (CUT) and name (canonical from index.json)
 *   4. Add placeholder polygon for Antártica (CUT 12202) — absent from chilemapas;
 *      Chilean Antarctic Territory is not in standard boundary datasets;
 *      zero crime rates in CEAD data (population 151)
 *   5. Assert (pre-mapshaper): 346 features, 0 missing/orphan/dup, CUT 13101 present
 *   6. Write re-keyed GeoJSON to OS temp directory
 *   7. Simplify + convert to TopoJSON via mapshaper CLI
 *      Config: visvalingam percentage=10% keep-shapes, quantization=10000
 *      Measured (2026-06-15): ~367 KB raw / ~107 KB gzip, ~0.4 km grid, recognizable coastline
 *   8. Assert: 346 features, 0 missing/orphan/dup, CUT 13101 present,
 *      file ≤ 420 KB raw AND ≤ 140 KB gzip
 *   9. Copy to data/cead/geo/communes.topo.json
 *
 * Re-runnable: `node scripts/build-topojson.mjs`
 * Requires: mapshaper installed globally (`npm install -g mapshaper`)
 *
 * Note: Antártica (12202) uses a small placeholder polygon near Drake Passage;
 *   CEAD data shows population 151, zero crime rates — renders at incidence level 1.
 */

import {
  readFileSync,
  writeFileSync,
  existsSync,
  mkdirSync,
  statSync,
} from 'node:fs';
import { gzipSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------
const RAW_GEOJSON = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes-chilemapas.geojson');
const INDEX_JSON = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
const OUTPUT_TOPO = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes.topo.json');
const TMP_DIR = os.tmpdir();
const TMP_REKEYED = path.join(TMP_DIR, 'communes-rekeyed.geojson');
const TMP_TOPO = path.join(TMP_DIR, 'communes.topo.json');

// ---------------------------------------------------------------------------
// CUT zero-pad normalization helper (chilemapas source)
// ---------------------------------------------------------------------------
// chilemapas codigo_comuna is 5-char zero-padded INE CUT string (e.g. "02101").
// CEAD index.json stores CUT as unpadded raw digits (e.g. "2101").
// This is a no-op for regions 10+ (no leading zero).
function srcCodeToCut(code) {
  return String(parseInt(code, 10));
}

// ---------------------------------------------------------------------------
// Step 1: Load inputs
// ---------------------------------------------------------------------------
if (!existsSync(RAW_GEOJSON)) {
  console.error('ERROR: communes-chilemapas.geojson not found.');
  console.error('  This file is committed to the repo at data/cead/geo/communes-chilemapas.geojson.');
  console.error('  If missing, re-download from: https://github.com/pachadotdev/chilemapas');
  console.error('  Merge data_geojson/comunas/r01.geojson ... r16.geojson into one FeatureCollection.');
  process.exit(1);
}

console.log('Loading chilemapas GeoJSON...');
const rawGeo = JSON.parse(readFileSync(RAW_GEOJSON, 'utf8'));
const indexEntries = JSON.parse(readFileSync(INDEX_JSON, 'utf8'));

console.log(`chilemapas features: ${rawGeo.features.length}`);
console.log(`Index communes: ${indexEntries.length}`);

// ---------------------------------------------------------------------------
// Step 2: Build index lookup by CUT (unpadded)
// ---------------------------------------------------------------------------
const indexByCut = new Map();
indexEntries.forEach(c => {
  indexByCut.set(c.cut, c);
});

// ---------------------------------------------------------------------------
// Step 3: Re-key each chilemapas feature → CEAD CUT via code-join
// ---------------------------------------------------------------------------
// chilemapas ships a real INE codigo_comuna — prefer code-join over name-matching.
// Retired: MANUAL_FIXES, norm(), indexByNorm name-match machinery (GADM-specific).
const features = [];
let skipped = 0;

for (const f of rawGeo.features) {
  const rawCode = f.properties.codigo_comuna;
  if (!rawCode) {
    console.warn(`  SKIP: feature missing codigo_comuna`);
    skipped++;
    continue;
  }

  const cut = srcCodeToCut(rawCode);
  const ie = indexByCut.get(cut);

  if (!ie) {
    console.warn(`  SKIP: no index.json entry for CUT ${cut} (codigo_comuna=${rawCode})`);
    skipped++;
    continue;
  }

  features.push({
    type: 'Feature',
    geometry: f.geometry,
    properties: { id: cut, name: ie.name },
  });
}

console.log(`Joined: ${features.length}, Skipped: ${skipped}`);

// ---------------------------------------------------------------------------
// Step 4: Add placeholder for Antártica Chilena (CUT 12202)
// ---------------------------------------------------------------------------
// GADM does not include Chilean Antarctic Territory claim.
// CEAD data: population 151, all crime rates = 0 → renders at incidence level 1.
// Placeholder: tiny polygon near Drake Passage (south of Punta Arenas).
const coveredCuts = new Set(features.map(f => f.properties.id));
if (!coveredCuts.has('12202')) {
  const ie = indexEntries.find(c => c.cut === '12202');
  console.log('Adding Antártica (12202) placeholder polygon...');
  features.push({
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [[
        [-68.5, -63.5], [-68.0, -63.5], [-68.0, -63.0],
        [-68.5, -63.0], [-68.5, -63.5],
      ]],
    },
    properties: { id: '12202', name: ie ? ie.name : 'Antártica' },
  });
}

// ---------------------------------------------------------------------------
// Step 5: Pre-commit assertions — four-way integrity check against index.json
// ---------------------------------------------------------------------------
console.log(`\nTotal features after processing: ${features.length}`);

{
  const wantCuts = new Set(indexEntries.map(c => c.cut));
  const gotCuts  = features.map(f => f.properties.id);
  const missing  = [...wantCuts].filter(c => !gotCuts.includes(c));
  const orphan   = gotCuts.filter(c => !wantCuts.has(c));
  const dup      = gotCuts.filter((c, i) => gotCuts.indexOf(c) !== i);

  if (features.length !== 346 || missing.length || orphan.length || dup.length) {
    console.error('FATAL: Step-5 integrity check failed');
    console.error(JSON.stringify({ count: features.length, missing, orphan, dup }, null, 2));
    process.exit(1);
  }

  const santiagoPre = features.find(f => f.properties.id === '13101');
  if (!santiagoPre) {
    console.error('FATAL: Santiago (CUT 13101) not found before simplification');
    process.exit(1);
  }
  console.log(`Santiago (13101): "${santiagoPre.properties.name}" — present`);
  console.log(`346 features, 0 missing, 0 orphan, 0 dup`);
}

// ---------------------------------------------------------------------------
// Step 6: Write re-keyed GeoJSON to OS temp
// ---------------------------------------------------------------------------
writeFileSync(TMP_REKEYED, JSON.stringify({ type: 'FeatureCollection', features }));
console.log(`\nRe-keyed GeoJSON: ${TMP_REKEYED}`);

// ---------------------------------------------------------------------------
// Step 7: Simplify + convert to TopoJSON
// ---------------------------------------------------------------------------
// Budget: ≤ 420 KB raw AND ≤ 140 KB gzip (Cloudflare serves gzip/brotli).
// Config: visvalingam 10%, quantization=10000 → ~367 KB raw / ~107 KB gzip,
//   ~0.4 km grid (sub-km, recognizable coastline). Measured 2026-06-15.
// Do NOT add fallback configs — silent re-over-simplification is forbidden.
// If budget is exceeded, fix the source or knobs explicitly.
const RAW_MAX_BYTES  = 430080; // 420 KB raw ceiling
const GZIP_MAX_BYTES = 143360; // 140 KB gzip ceiling

console.log(`\nMapshaper: visvalingam 10%, quantization=10000...`);
const mapshaperResult = spawnSync('mapshaper', [
  TMP_REKEYED,
  '-clean',
  '-simplify', 'visvalingam', 'percentage=10%', 'keep-shapes',
  '-o', 'format=topojson', 'quantization=10000', TMP_TOPO,
], { stdio: 'inherit', shell: true });

if (mapshaperResult.status !== 0) {
  console.error('mapshaper failed — is it installed globally? npm install -g mapshaper');
  process.exit(1);
}

const finalSize = statSync(TMP_TOPO).size;
const gzipSize  = gzipSync(readFileSync(TMP_TOPO)).length;
console.log(`  Raw:  ${finalSize} bytes (${(finalSize / 1024).toFixed(1)} KB)`);
console.log(`  Gzip: ${gzipSize} bytes (${(gzipSize / 1024).toFixed(1)} KB)`);

if (finalSize >= RAW_MAX_BYTES || gzipSize >= GZIP_MAX_BYTES) {
  console.error(`FATAL: TopoJSON exceeds budget (raw: ${finalSize}/${RAW_MAX_BYTES}, gzip: ${gzipSize}/${GZIP_MAX_BYTES})`);
  process.exit(1);
}
console.log(`  Budget OK: ≤ 420 KB raw AND ≤ 140 KB gzip`);

// ---------------------------------------------------------------------------
// Step 8: Validate TopoJSON output
// ---------------------------------------------------------------------------
const topo = JSON.parse(readFileSync(TMP_TOPO, 'utf8'));
if (topo.type !== 'Topology') {
  console.error('FATAL: output is not valid TopoJSON');
  process.exit(1);
}

const objKey = Object.keys(topo.objects)[0];
const geometries = topo.objects[objKey].geometries;
const geomCount = geometries.length;

{
  const wantCuts = new Set(indexEntries.map(c => c.cut));
  const gotCuts  = geometries.map(g => g.properties && g.properties.id);
  const missing  = [...wantCuts].filter(c => !gotCuts.includes(c));
  const orphan   = gotCuts.filter(c => !wantCuts.has(c));
  const dup      = gotCuts.filter((c, i) => gotCuts.indexOf(c) !== i);

  if (geomCount !== 346 || missing.length || orphan.length || dup.length) {
    console.error('FATAL: Step-8 TopoJSON integrity check failed');
    console.error(JSON.stringify({ count: geomCount, missing, orphan, dup }, null, 2));
    process.exit(1);
  }

  const sgoFeature = geometries.find(g => g.properties && g.properties.id === '13101');
  if (!sgoFeature) {
    console.error('FATAL: CUT 13101 (Santiago) not found in TopoJSON output');
    process.exit(1);
  }
  console.log(`Step-8: 346 geometries, 0 missing, 0 orphan, 0 dup — TopoJSON integrity OK`);
  console.log(`Santiago (13101): "${sgoFeature.properties.name}" — join verified`);
}

// ---------------------------------------------------------------------------
// Step 9: Copy to final destination
// ---------------------------------------------------------------------------
const outputDir = path.dirname(OUTPUT_TOPO);
if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

writeFileSync(OUTPUT_TOPO, readFileSync(TMP_TOPO));
console.log(`\nSUCCESS: ${OUTPUT_TOPO}`);
console.log(`  ${finalSize} bytes (${(finalSize / 1024).toFixed(1)} KB), ${geomCount} communes`);
