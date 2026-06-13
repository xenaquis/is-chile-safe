/**
 * region.mjs — Validate region page HTML output.
 *
 * Asserts:
 * - dist/region has exactly 16 dirs
 * - dist/es/region has exactly 16 dirs
 * - Sample region pages (13 Metropolitana + 11 Aysen) have:
 *   - A populated <table> with at least as many rows as the region's commune count
 *   - hreflang alternates (en/es/x-default)
 *   - self-canonical
 *   - Dataset/Place JSON-LD block
 *   - A * marker present if any commune in region is low_population
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

  // 1. Ranking table row count >= commune count
  const communeCount = getRegionCommuneCount(sample.regionFileId);
  const tableRows = countTableRows(html);
  if (tableRows < communeCount) {
    console.error(
      `FAIL: ${label} table has ${tableRows} rows, expected >= ${communeCount} (commune count)`
    );
    failures++;
  } else {
    console.log(`PASS: ${label} table rows (${tableRows}) >= commune count (${communeCount})`);
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

  // 5. low-pop marker (* ) present if region has low-pop communes
  const hasLowPop = hasLowPopCommune(sample.regionFileId);
  if (hasLowPop) {
    if (!html.includes('low-pop-marker') && !html.includes('*')) {
      console.error(`FAIL: ${label} has low-pop communes but no * marker in HTML`);
      failures++;
    } else {
      console.log(`PASS: ${label} low-pop * marker present`);
    }
  } else {
    console.log(`INFO: ${label} no low-pop communes in this region`);
  }
}

if (failures > 0) {
  console.error(`\nregion validation: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\nregion.mjs: PASSED — all region page assertions green');
