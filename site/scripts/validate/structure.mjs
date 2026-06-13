/**
 * structure.mjs — Fast sampler: assert that, IF dist/ exists, a sample page from each
 * built type (one commune, one region) has a <head> with <title>, <link rel=canonical>,
 * and the three hreflang alternates, and that <body> is non-empty.
 *
 * If dist/ does not yet exist, exits 0 with a note (safe to run before the first build).
 * Target: <60s quick-check from the VALIDATION sampling contract.
 */
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../..');
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// ---------------------------------------------------------------------------
// Smoke check: critical files exist
// ---------------------------------------------------------------------------
const REQUIRED_FILES = [
  'site/package.json',
  'site/astro.config.mjs',
  'site/src/lib/data.ts',
  'site/src/lib/colorScale.ts',
  'site/src/lib/slugMaps.ts',
  'site/src/config/i18n.ts',
  'site/src/config/rollout.json',
  'data/cead/meta/index.json',
];

for (const file of REQUIRED_FILES) {
  const abs = path.join(REPO_ROOT, file);
  assert.ok(existsSync(abs), `Required file missing: ${file}`);
}
console.log('structure: smoke check passed (all required source files found)');

// ---------------------------------------------------------------------------
// If dist/ does not exist, exit 0 — safe before first build
// ---------------------------------------------------------------------------
if (!existsSync(DIST_DIR)) {
  console.log('structure: dist/ not found — skipping HTML checks (run npm run build first)');
  process.exit(0);
}

// ---------------------------------------------------------------------------
// HTML head meta sampler
// ---------------------------------------------------------------------------
function checkPage(htmlPath, label) {
  if (!existsSync(htmlPath)) {
    console.error(`FAIL [${label}]: HTML not found at ${htmlPath}`);
    return false;
  }

  const html = readFileSync(htmlPath, 'utf-8');
  let ok = true;

  // <title> present
  if (!/<title>[^<]+<\/title>/i.test(html)) {
    console.error(`FAIL [${label}]: missing or empty <title>`);
    ok = false;
  }

  // <link rel="canonical"> present
  if (!html.includes('rel="canonical"')) {
    console.error(`FAIL [${label}]: missing <link rel="canonical">`);
    ok = false;
  }

  // Three hreflang alternates
  if (!html.includes('hreflang="en"')) {
    console.error(`FAIL [${label}]: missing hreflang="en"`);
    ok = false;
  }
  if (!html.includes('hreflang="es"')) {
    console.error(`FAIL [${label}]: missing hreflang="es"`);
    ok = false;
  }
  if (!html.includes('hreflang="x-default"')) {
    console.error(`FAIL [${label}]: missing hreflang="x-default"`);
    ok = false;
  }

  // <body> is non-empty
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  if (!bodyMatch || bodyMatch[1].trim().length < 10) {
    console.error(`FAIL [${label}]: <body> is empty or near-empty`);
    ok = false;
  }

  if (ok) console.log(`PASS [${label}]`);
  return ok;
}

let failures = 0;

// Sample one EN commune page
const communeEnDir = path.join(DIST_DIR, 'commune');
if (existsSync(communeEnDir)) {
  const firstSlug = readdirSync(communeEnDir, { withFileTypes: true })
    .find((d) => d.isDirectory())?.name;
  if (firstSlug) {
    if (!checkPage(path.join(communeEnDir, firstSlug, 'index.html'), `EN commune/${firstSlug}`)) {
      failures++;
    }
  }
} else {
  console.log('structure: no commune pages built yet — skipping commune sample');
}

// Sample one ES commune page
const communeEsDir = path.join(DIST_DIR, 'es', 'comuna');
if (existsSync(communeEsDir)) {
  const firstSlug = readdirSync(communeEsDir, { withFileTypes: true })
    .find((d) => d.isDirectory())?.name;
  if (firstSlug) {
    if (!checkPage(path.join(communeEsDir, firstSlug, 'index.html'), `ES es/comuna/${firstSlug}`)) {
      failures++;
    }
  }
} else {
  console.log('structure: no ES commune pages built yet — skipping');
}

// Sample one EN region page (Metropolitana)
const regionEnPath = path.join(DIST_DIR, 'region', 'metropolitana', 'index.html');
if (existsSync(path.join(DIST_DIR, 'region'))) {
  if (!checkPage(regionEnPath, 'EN region/metropolitana')) failures++;
} else {
  console.log('structure: no region pages built yet — skipping region sample');
}

// Sample one ES region page
const regionEsPath = path.join(DIST_DIR, 'es', 'region', 'metropolitana', 'index.html');
if (existsSync(path.join(DIST_DIR, 'es', 'region'))) {
  if (!checkPage(regionEsPath, 'ES es/region/metropolitana')) failures++;
}

// ---------------------------------------------------------------------------
// Phase-4 editorial and legal page assertions (EDIT-01 / EDIT-02 / EDIT-04)
// Guard: only assert if the sentinel page (methodology/index.html) exists.
// Before the editorial pages are built this block is a no-op.
// Slug list is taken verbatim from REQUIREMENTS.md EDIT-01/EDIT-02/EDIT-04.
// ---------------------------------------------------------------------------
const PHASE4_DIST_PAGES = [
  // EDIT-01 EN editorial (10 pages — root assertd as dist/index.html)
  'index.html',               // /  (root)
  'chile-crime-map/index.html',
  'is-chile-safe/index.html',
  'santiago-safety-map/index.html',
  'is-santiago-safe/index.html',
  'valparaiso-safety/index.html',
  'vina-del-mar-safety/index.html',
  'concepcion-safety/index.html',
  'safest-cities-in-chile/index.html',
  'methodology/index.html',
  // EDIT-02 ES editorial (10 pages — /es/ root as dist/es/index.html)
  'es/index.html',            // /es/
  'es/mapa-delito-chile/index.html',
  'es/delitos-por-comuna/index.html',
  'es/delitos-por-region/index.html',
  'es/comunas-mas-seguras-chile/index.html',
  'es/mapa-seguridad-santiago/index.html',
  'es/seguridad-valparaiso/index.html',
  'es/seguridad-vina-del-mar/index.html',
  'es/seguridad-concepcion/index.html',
  'es/metodologia/index.html',
  // EDIT-04 legal (EN + ES)
  'privacy-policy/index.html',
  'terms/index.html',
  'about/index.html',
  'contact/index.html',
  'es/politica-privacidad/index.html',
  'es/terminos/index.html',
  'es/acerca-de/index.html',
  'es/contacto/index.html',
];

const phase4Sentinel = path.join(DIST_DIR, 'methodology', 'index.html');
if (!existsSync(phase4Sentinel)) {
  console.log('structure: Phase-4 editorial pages not built yet — skipping');
} else {
  console.log('structure: Phase-4 sentinel found — asserting all EDIT-01/02/04 pages');
  let phase4Failures = 0;
  for (const rel of PHASE4_DIST_PAGES) {
    const abs = path.join(DIST_DIR, rel);
    if (!existsSync(abs)) {
      console.error(`FAIL [phase4]: HTML not found at ${abs}`);
      phase4Failures++;
      failures++;
    }
  }
  if (phase4Failures === 0) {
    console.log(`structure: Phase-4 PASS — all ${PHASE4_DIST_PAGES.length} editorial/legal pages present`);
  }
}

if (failures > 0) {
  console.error(`\nstructure.mjs: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\nstructure.mjs: PASSED — sampled page head meta validated');
