/**
 * schema.mjs — Validate Schema.org JSON-LD in built HTML pages.
 *
 * Asserts:
 *   - Commune pages: JSON-LD with @type containing both "Dataset" and "Place",
 *     creator naming CEAD, spatialCoverage present
 *   - Region pages: same as commune
 *   - Crime pages: JSON-LD with "Dataset" @type, NO Place @type
 *   - temporalCoverage ends at a complete year (not 2026 partial)
 *   - JSON-LD parses as valid JSON (no syntax errors from template escaping)
 *
 * Exit non-zero naming failing pages.
 *
 * Usage:
 *   node scripts/validate/schema.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

let failures = 0;

function extractJsonLd(html) {
  // Find first <script type="application/ld+json">...</script>
  const m = html.match(/<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/i);
  if (!m) return null;
  try {
    return JSON.parse(m[1]);
  } catch (e) {
    return { _parseError: e.message, _raw: m[1] };
  }
}

function normalizeTypes(typeVal) {
  // @type can be a string or array
  if (!typeVal) return [];
  return Array.isArray(typeVal) ? typeVal.map(t => t.toLowerCase()) : [typeVal.toLowerCase()];
}

function checkPage(htmlPath, pageType) {
  // pageType: 'territorial' (commune/region) or 'crime'
  const html = readFileSync(htmlPath, 'utf-8');
  const label = htmlPath.replace(DIST_DIR, '').replace(/\\/g, '/');
  const ld = extractJsonLd(html);
  const pageFailures = [];

  if (!ld) {
    pageFailures.push('no application/ld+json script block found');
    failures++;
    console.error(`FAIL ${label}: ${pageFailures[0]}`);
    return;
  }

  if (ld._parseError) {
    failures++;
    console.error(`FAIL ${label}: JSON-LD parse error — ${ld._parseError}`);
    return;
  }

  const types = normalizeTypes(ld['@type']);

  if (pageType === 'territorial') {
    // Must have both Dataset and Place
    if (!types.includes('dataset')) {
      pageFailures.push('@type missing "Dataset"');
    }
    if (!types.includes('place') && !types.includes('administrativearea')) {
      // Also accept AdministrativeArea as Place equivalent
      pageFailures.push('@type missing "Place" (or AdministrativeArea)');
    }
    // spatialCoverage required
    if (!ld.spatialCoverage) {
      pageFailures.push('missing spatialCoverage');
    }
  } else if (pageType === 'crime') {
    // Must have Dataset, must NOT have Place as a top-level @type
    if (!types.includes('dataset')) {
      pageFailures.push('@type missing "Dataset"');
    }
    if (types.includes('place') || types.includes('administrativearea')) {
      pageFailures.push('crime page must NOT have Place/@type as top-level @type in JSON-LD');
    }
    // spatialCoverage with @type Country (national scope) is acceptable for crime pages
    // — what's prohibited is having Place as the page-level @type (UI-SPEC line 288)
  }

  // Creator naming CEAD (all page types)
  const creatorStr = JSON.stringify(ld.creator || '').toLowerCase();
  if (!creatorStr.includes('cead')) {
    pageFailures.push('creator does not reference CEAD');
  }

  // temporalCoverage ends at complete year (not 2026 partial)
  const tc = ld.temporalCoverage || '';
  if (tc) {
    const yearMatch = tc.match(/\/(\d{4})$/);
    if (!yearMatch) {
      pageFailures.push(`temporalCoverage "${tc}" does not end with a complete year`);
    } else {
      const year = parseInt(yearMatch[1], 10);
      if (year >= 2026) {
        pageFailures.push(`temporalCoverage ends at ${year} — must be a complete year (not current partial year)`);
      }
    }
  } else {
    pageFailures.push('temporalCoverage missing');
  }

  if (pageFailures.length > 0) {
    failures += pageFailures.length;
    console.error(`FAIL ${label}:\n  ${pageFailures.join('\n  ')}`);
  }
}

// ---------------------------------------------------------------------------
// Commune pages
// ---------------------------------------------------------------------------
const communeEnDir = path.join(DIST_DIR, 'commune');
const communeEsDir = path.join(DIST_DIR, 'es', 'comuna');
let communeCount = 0;

function checkDir(dir, pageType) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const htmlPath = path.join(dir, entry.name, 'index.html');
    if (existsSync(htmlPath)) {
      checkPage(htmlPath, pageType);
      communeCount++;
    }
  }
}

checkDir(communeEnDir, 'territorial');
checkDir(communeEsDir, 'territorial');

// ---------------------------------------------------------------------------
// Region pages
// ---------------------------------------------------------------------------
const regionEnDir = path.join(DIST_DIR, 'region');
const regionEsDir = path.join(DIST_DIR, 'es', 'region');
let regionCount = 0;

function checkRegionDir(dir) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const htmlPath = path.join(dir, entry.name, 'index.html');
    if (existsSync(htmlPath)) {
      checkPage(htmlPath, 'territorial');
      regionCount++;
    }
  }
}

checkRegionDir(regionEnDir);
checkRegionDir(regionEsDir);

// ---------------------------------------------------------------------------
// Crime pages
// ---------------------------------------------------------------------------
const crimeEnDir = path.join(DIST_DIR, 'crime');
const crimeEsDir = path.join(DIST_DIR, 'es', 'delito');
let crimeCount = 0;

function checkCrimeDir(dir) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const htmlPath = path.join(dir, entry.name, 'index.html');
    if (existsSync(htmlPath)) {
      checkPage(htmlPath, 'crime');
      crimeCount++;
    }
  }
}

checkCrimeDir(crimeEnDir);
checkCrimeDir(crimeEsDir);

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
const totalChecked = communeCount + regionCount + crimeCount;
console.log(`schema.mjs: checked ${communeCount} commune, ${regionCount} region, ${crimeCount} crime pages`);

if (failures > 0) {
  console.error(`\nschema.mjs: FAILED (${failures} issue(s) across ${totalChecked} pages)`);
  process.exit(1);
}

console.log(`schema.mjs: PASSED — ${totalChecked} pages validated`);
console.log(`  Commune/region: Dataset+Place JSON-LD with CEAD creator`);
console.log(`  Crime: Dataset-only (no Place) with CEAD creator`);
console.log(`  temporalCoverage: complete years only`);
