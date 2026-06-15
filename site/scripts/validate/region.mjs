/**
 * region.mjs — Validate region page HTML output.
 *
 * Asserts:
 * - dist/region has exactly 16 dirs
 * - dist/es/region has exactly 16 dirs
 * - Sample region pages (13 Metropolitana + 11 Aysen) have:
 *   - A ranking <table> whose row count == the region's ROLLOUT commune count
 *     (F-005: tables display only rollout communes, not the full region;
 *     respects ROLLOUT_ALL=true). Aysen has 0 rollout communes → 0 rows.
 *   - A "more coming" rollout-note affordance whenever rows are gated
 *   - hreflang alternates (en/es/x-default)
 *   - self-canonical
 *   - Dataset/Place JSON-LD block
 *   - A * marker present only if a DISPLAYED (rollout) commune is low_population
 *
 * Exit non-zero on any failure.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function countTableRows(html) {
  // Count <tr> elements inside <tbody>
  const tbodyMatch = html.match(/<tbody[^>]*>([\s\S]*?)<\/tbody>/i);
  if (!tbodyMatch) return 0;
  const trMatches = tbodyMatch[1].match(/<tr/gi);
  return trMatches ? trMatches.length : 0;
}

function getRegionCommuneCount(regionFileId) {
  const indexPath = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
  const index = JSON.parse(readFileSync(indexPath, 'utf-8'));
  return index.filter((c) => {
    const n = parseInt(c.region_id, 10);
    let fid;
    if (n >= 1 && n <= 16) fid = String(n);
    else fid = String(Math.floor(n / 10));
    return fid === String(regionFileId);
  }).length;
}

function hasLowPopCommune(regionFileId) {
  const indexPath = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
  const index = JSON.parse(readFileSync(indexPath, 'utf-8'));
  return index.some((c) => {
    const n = parseInt(c.region_id, 10);
    let fid;
    if (n >= 1 && n <= 16) fid = String(n);
    else fid = String(Math.floor(n / 10));
    return fid === String(regionFileId) && c.low_population;
  });
}

// Rollout-gated contract (F-005): region ranking tables display only communes
// whose cut is in the rollout set (or all communes when ROLLOUT_ALL=true).
// Mirrors loadRolloutCuts() in src/lib/data.ts so the validator asserts the
// same row set the page actually renders.
function getRolloutCuts() {
  const indexPath = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
  const index = JSON.parse(readFileSync(indexPath, 'utf-8'));
  if (process.env.ROLLOUT_ALL === 'true') {
    return new Set(index.map((c) => String(c.cut)));
  }
  const rolloutPath = path.join(SITE_ROOT, 'src', 'config', 'rollout.json');
  const rollout = JSON.parse(readFileSync(rolloutPath, 'utf-8'));
  return new Set((rollout.enabled || []).map((cut) => String(cut)));
}

function regionCommunes(regionFileId) {
  const indexPath = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
  const index = JSON.parse(readFileSync(indexPath, 'utf-8'));
  return index.filter((c) => {
    const n = parseInt(c.region_id, 10);
    let fid;
    if (n >= 1 && n <= 16) fid = String(n);
    else fid = String(Math.floor(n / 10));
    return fid === String(regionFileId);
  });
}

// Number of rows the gated table should display for a region = communes in the
// region whose cut is in the rollout set.
function getRegionRolloutCount(regionFileId) {
  const rolloutCuts = getRolloutCuts();
  return regionCommunes(regionFileId).filter((c) => rolloutCuts.has(String(c.cut))).length;
}

// Whether any DISPLAYED (rollout) commune in the region is low_population —
// the * marker is keyed to displayed rows, not the full region.
function hasRolloutLowPopCommune(regionFileId) {
  const rolloutCuts = getRolloutCuts();
  return regionCommunes(regionFileId).some(
    (c) => rolloutCuts.has(String(c.cut)) && c.low_population
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const enDir = path.join(DIST_DIR, 'region');
const esDir = path.join(DIST_DIR, 'es', 'region');

if (!existsSync(enDir)) {
  console.error('FAIL: dist/region directory not found — run npm run build first');
  process.exit(1);
}
if (!existsSync(esDir)) {
  console.error('FAIL: dist/es/region directory not found — run npm run build first');
  process.exit(1);
}

const enDirs = readdirSync(enDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

const esDirs = readdirSync(esDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

console.log(`Found ${enDirs.length} EN region dirs, ${esDirs.length} ES region dirs`);

let failures = 0;

// Assert counts
if (enDirs.length !== 16) {
  console.error(`FAIL: expected 16 EN region dirs, found ${enDirs.length}`);
  failures++;
} else {
  console.log('PASS: 16 EN region dirs');
}

if (esDirs.length !== 16) {
  console.error(`FAIL: expected 16 ES region dirs, found ${esDirs.length}`);
  failures++;
} else {
  console.log('PASS: 16 ES region dirs');
}

// Sample assertions: region 13 (Metropolitana) and 11 (Aysen)
const SAMPLES = [
  { regionFileId: 13, slug: 'metropolitana', locale: 'en' },
  { regionFileId: 13, slug: 'metropolitana', locale: 'es' },
  { regionFileId: 11, slug: 'aysen', locale: 'en' },
  { regionFileId: 11, slug: 'aysen', locale: 'es' },
];

for (const sample of SAMPLES) {
  const htmlPath =
    sample.locale === 'en'
      ? path.join(enDir, sample.slug, 'index.html')
      : path.join(esDir, sample.slug, 'index.html');

  if (!existsSync(htmlPath)) {
    console.error(`FAIL: missing HTML for ${sample.locale} region ${sample.slug}`);
    failures++;
    continue;
  }

  const html = readFileSync(htmlPath, 'utf-8');
  const lower = html.toLowerCase();
  const label = `${sample.locale.toUpperCase()} /region/${sample.slug}/`;

  // 1. Ranking table row count == rollout commune count (F-005 gating).
  //    The region table displays only communes in the rollout set, never the
  //    full region. Rank denominators stay national; only displayed rows gate.
  const communeCount = getRegionCommuneCount(sample.regionFileId);
  const expectedRows = getRegionRolloutCount(sample.regionFileId);
  const tableRows = countTableRows(html);
  if (tableRows !== expectedRows) {
    console.error(
      `FAIL: ${label} table has ${tableRows} rows, expected ${expectedRows} (rollout communes in region; ${communeCount} total)`
    );
    failures++;
  } else {
    console.log(
      `PASS: ${label} table rows (${tableRows}) == rollout communes (${expectedRows}) of ${communeCount} total`
    );
  }

  // 1b. When rows are gated (rollout < total), the "more coming" affordance must be present.
  if (expectedRows < communeCount) {
    if (!lower.includes('rollout-note')) {
      console.error(`FAIL: ${label} gated table missing rollout-note affordance`);
      failures++;
    } else {
      console.log(`PASS: ${label} rollout-note affordance present (gated ${expectedRows}/${communeCount})`);
    }
  }

  // 2. hreflang alternates
  if (!html.includes('hreflang="en"')) {
    console.error(`FAIL: ${label} missing hreflang="en"`);
    failures++;
  }
  if (!html.includes('hreflang="es"')) {
    console.error(`FAIL: ${label} missing hreflang="es"`);
    failures++;
  }
  if (!html.includes('hreflang="x-default"')) {
    console.error(`FAIL: ${label} missing hreflang="x-default"`);
    failures++;
  }
  console.log(`PASS: ${label} hreflang alternates present`);

  // 3. Self-canonical
  if (!lower.includes('rel="canonical"')) {
    console.error(`FAIL: ${label} missing canonical link`);
    failures++;
  } else {
    console.log(`PASS: ${label} canonical present`);
  }

  // 4. JSON-LD block with Dataset + Place
  if (!lower.includes('"dataset"') || !lower.includes('"administrativearea"')) {
    console.error(`FAIL: ${label} missing Dataset/Place JSON-LD`);
    failures++;
  } else {
    console.log(`PASS: ${label} JSON-LD Dataset+AdministrativeArea present`);
  }

  // 5. low-pop marker (* ) present only if a DISPLAYED (rollout) commune is low-pop.
  //    Keyed to displayed rows, not the full region — a region whose low-pop
  //    communes are all outside the rollout set must not assert a marker.
  const hasLowPop = hasRolloutLowPopCommune(sample.regionFileId);
  if (hasLowPop) {
    if (!html.includes('low-pop-marker')) {
      console.error(`FAIL: ${label} has displayed low-pop commune but no low-pop-marker in HTML`);
      failures++;
    } else {
      console.log(`PASS: ${label} low-pop * marker present`);
    }
  } else {
    console.log(`INFO: ${label} no displayed (rollout) low-pop communes in this region`);
  }
}

if (failures > 0) {
  console.error(`\nregion validation: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\nregion.mjs: PASSED — all region page assertions green');
