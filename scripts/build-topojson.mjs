/**
 * build-topojson.mjs — Offline pipeline to produce data/cead/geo/communes.topo.json
 *
 * Source dataset: GADM 4.1 Chile Level-3 (commune boundaries)
 * URL: https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_CHL_3.json
 * Saved as: data/cead/geo/communes-raw.geojson (do not re-fetch without reason)
 *
 * Pipeline:
 *   1. Load GADM GeoJSON (345 features with known quality issues — see MANUAL_FIXES)
 *   2. Load data/cead/meta/index.json (346-commune CUT source of truth)
 *   3. Match GADM features → CUT via normalized name matching + manual fixes
 *   4. Re-key each feature: properties.id = CUT (string), properties.name = canonical name
 *      Drop all other properties to minimise file size
 *   5. Add placeholder polygon for Antártica (CUT 12202) — absent from GADM;
 *      Chilean Antarctic Territory is not in standard boundary datasets;
 *      zero crime rates in CEAD data (population 151)
 *   6. Write re-keyed GeoJSON to OS temp directory
 *   7. Simplify + convert to TopoJSON via mapshaper CLI
 *      (visvalingam 0.05%, quantization=500 → ~89 KB)
 *   8. Assert: 346 features, CUT 13101 (Santiago) present, file < 100 KB
 *   9. Copy to data/cead/geo/communes.topo.json
 *
 * Re-runnable: `node scripts/build-topojson.mjs`
 * Requires: mapshaper installed globally (`npm install -g mapshaper`)
 *
 * Known deviations:
 *   - D-02 said use prototype geo-data.js — that file has only 56 slug-keyed features;
 *     provably unusable for 346-commune requirement. GADM sourced per D-02 escape hatch.
 *   - GADM has 4 naming/data issues fixed in MANUAL_FIXES below.
 *   - Antártica (12202) uses a small placeholder polygon near Drake Passage;
 *     CEAD data shows population 151, zero crime rates — renders at incidence level 1.
 */

import {
  readFileSync,
  writeFileSync,
  existsSync,
  mkdirSync,
  statSync,
} from 'node:fs';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------
const RAW_GEOJSON = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes-raw.geojson');
const INDEX_JSON = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
const OUTPUT_TOPO = path.join(REPO_ROOT, 'data', 'cead', 'geo', 'communes.topo.json');
const TMP_DIR = os.tmpdir();
const TMP_REKEYED = path.join(TMP_DIR, 'communes-rekeyed.geojson');
const TMP_TOPO = path.join(TMP_DIR, 'communes.topo.json');

// ---------------------------------------------------------------------------
// Manual name → CUT fixes for GADM data quality issues
// ---------------------------------------------------------------------------
// Key format: norm(NAME_3) + '_' + norm(NAME_2) + '_' + norm(NAME_1)
const MANUAL_FIXES = {
  // GADM uses "Calera" — CEAD is "La Calera" (CUT 5502, Quillota, Valparaíso)
  'calera_quillota_valparaiso': '5502',
  // GADM spells it "Paihuano" — CEAD index says "Paiguano" (CUT 4105, Elqui, Coquimbo)
  'paihuano_elqui_coquimbo': '4105',
  // GADM has duplicate "Tocopilla" in Tarapacá/Tamarugal — actually Pozo Almonte (CUT 1401)
  'tocopilla_tamarugal_tarapaca': '1401',
};

// ---------------------------------------------------------------------------
// Normalize names for matching
// ---------------------------------------------------------------------------
function norm(s) {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // strip diacritics
    .replace(/[^a-z0-9]/g, '');      // strip non-alphanumeric
}

// ---------------------------------------------------------------------------
// Step 1: Load inputs
// ---------------------------------------------------------------------------
if (!existsSync(RAW_GEOJSON)) {
  console.error('ERROR: communes-raw.geojson not found. Download from:');
  console.error('  https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_CHL_3.json');
  console.error('  Save as: data/cead/geo/communes-raw.geojson');
  process.exit(1);
}

console.log('Loading GADM GeoJSON...');
const rawGeo = JSON.parse(readFileSync(RAW_GEOJSON, 'utf8'));
const indexEntries = JSON.parse(readFileSync(INDEX_JSON, 'utf8'));

console.log(`GADM features: ${rawGeo.features.length}`);
console.log(`Index communes: ${indexEntries.length}`);

// ---------------------------------------------------------------------------
// Step 2: Build index lookup (normalized name → entry)
// ---------------------------------------------------------------------------
const indexByNorm = new Map();
indexEntries.forEach(c => {
  indexByNorm.set(norm(c.name), c);
});

// ---------------------------------------------------------------------------
// Step 3: Assign CUT to each GADM feature
// ---------------------------------------------------------------------------
const features = [];
let skipped = 0;

for (const f of rawGeo.features) {
  const n3 = f.properties.NAME_3;
  const n2 = f.properties.NAME_2;
  const n1 = f.properties.NAME_1;
  const manualKey = `${norm(n3)}_${norm(n2)}_${norm(n1)}`;

  let cut = MANUAL_FIXES[manualKey] ?? null;
  if (!cut) {
    const match = indexByNorm.get(norm(n3));
    if (match) cut = match.cut;
  }

  if (!cut) {
    console.warn(`  SKIP: no CUT for "${n3}" (${n2}, ${n1})`);
    skipped++;
    continue;
  }

  const ie = indexEntries.find(c => c.cut === cut);
  if (!ie) {
    console.warn(`  SKIP: CUT ${cut} not in index.json`);
    skipped++;
    continue;
  }

  features.push({
    type: 'Feature',
    geometry: f.geometry,
    properties: { id: cut, name: ie.name },
  });
}

console.log(`Matched: ${features.length}, Skipped: ${skipped}`);

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
// 0.05% visvalingam + quantization=500 → ~89 KB (under 100 KB target)
// Tune percentage downward if output grows above 100 KB
const SIMPLIFY_CONFIGS = [
  { pct: '0.05%', quant: 500 },
  { pct: '0.03%', quant: 300 },
  { pct: '0.02%', quant: 200 },
];

let finalSize = Infinity;

for (const { pct, quant } of SIMPLIFY_CONFIGS) {
  console.log(`\nMapshaper: visvalingam ${pct}, quantization=${quant}...`);
  const result = spawnSync('mapshaper', [
    TMP_REKEYED,
    '-simplify', 'visvalingam', `percentage=${pct}`, 'keep-shapes',
    '-o', `format=topojson`, `quantization=${quant}`, TMP_TOPO,
  ], { stdio: 'inherit', shell: true });

  if (result.status !== 0) {
    console.error('mapshaper failed — is it installed globally? npm install -g mapshaper');
    process.exit(1);
  }

  finalSize = statSync(TMP_TOPO).size;
  console.log(`  Size: ${finalSize} bytes (${(finalSize / 1024).toFixed(1)} KB)`);

  if (finalSize < 102400) {
    console.log(`  Under 100 KB — proceeding`);
    break;
  }
  console.log(`  Over 100 KB — trying more aggressive simplification`);
}

if (finalSize >= 102400) {
  console.error(`FATAL: Could not reduce TopoJSON below 100 KB (got ${finalSize} bytes)`);
  process.exit(1);
}

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
