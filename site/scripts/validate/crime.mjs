/**
 * crime.mjs — Validate crime-type page HTML output.
 *
 * Asserts:
 * - dist/crime has exactly 7 dirs
 * - dist/es/delito has exactly 7 dirs
 * - EN dir names exactly match the 7 FAMILY_SLUGS .en values (slug drift guard)
 * - ES dir names exactly match the 7 FAMILY_SLUGS .es values (slug drift guard)
 * - Sample page (crime/property) has:
 *   - A ranking <table> with multiple data rows
 *   - Dataset JSON-LD block
 *   - NO Place @type in JSON-LD (crime pages are Dataset-only per UI-SPEC line 288)
 *   - Reciprocal hreflang (en / es / x-default)
 *   - Self-canonical
 *
 * Exit non-zero on any failure.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// ---------------------------------------------------------------------------
// FAMILY_SLUGS (must stay in sync with site/src/config/i18n.ts FAMILY_SLUGS)
// ---------------------------------------------------------------------------
const FAMILY_SLUGS = {
  vida:            { en: 'homicide',         es: 'homicidios' },
  robos_violentos: { en: 'violent-robbery',  es: 'robos-violentos' },
  vif:             { en: 'domestic-violence', es: 'violencia-intrafamiliar' },
  drogas:          { en: 'drug-crimes',      es: 'drogas' },
  armas:           { en: 'weapons',          es: 'armas' },
  propiedad:       { en: 'property',         es: 'propiedad' },
  incivilidades:   { en: 'disorder',         es: 'incivilidades' },
};

const EXPECTED_EN_SLUGS = new Set(Object.values(FAMILY_SLUGS).map((s) => s.en));
const EXPECTED_ES_SLUGS = new Set(Object.values(FAMILY_SLUGS).map((s) => s.es));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function countTableRows(html) {
  const tbodyMatch = html.match(/<tbody[^>]*>([\s\S]*?)<\/tbody>/i);
  if (!tbodyMatch) return 0;
  const trMatches = tbodyMatch[1].match(/<tr/gi);
  return trMatches ? trMatches.length : 0;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const enCrimeDir = path.join(DIST_DIR, 'crime');
const esCrimeDir = path.join(DIST_DIR, 'es', 'delito');

if (!existsSync(enCrimeDir)) {
  console.error('FAIL: dist/crime directory not found — run npm run build first');
  process.exit(1);
}
if (!existsSync(esCrimeDir)) {
  console.error('FAIL: dist/es/delito directory not found — run npm run build first');
  process.exit(1);
}

const enDirs = readdirSync(enCrimeDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

const esDirs = readdirSync(esCrimeDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

console.log(`Found ${enDirs.length} EN crime dirs, ${esDirs.length} ES crime dirs`);

let failures = 0;

// 1. Count: exactly 7 EN + 7 ES
if (enDirs.length !== 7) {
  console.error(`FAIL: expected 7 EN crime dirs, found ${enDirs.length}: [${enDirs.join(', ')}]`);
  failures++;
} else {
  console.log('PASS: 7 EN crime dirs found');
}

if (esDirs.length !== 7) {
  console.error(`FAIL: expected 7 ES crime dirs, found ${esDirs.length}: [${esDirs.join(', ')}]`);
  failures++;
} else {
  console.log('PASS: 7 ES crime dirs found');
}

// 2. Slug correctness — EN dirs must exactly match FAMILY_SLUGS .en values
const enDirSet = new Set(enDirs);
for (const slug of EXPECTED_EN_SLUGS) {
  if (!enDirSet.has(slug)) {
    console.error(`FAIL: EN crime dir missing expected slug "${slug}"`);
    failures++;
  }
}
for (const slug of enDirs) {
  if (!EXPECTED_EN_SLUGS.has(slug)) {
    console.error(`FAIL: EN crime dir "${slug}" is not in FAMILY_SLUGS EN values (slug drift)`);
    failures++;
  }
}
if (failures === 0) {
  console.log('PASS: EN crime dir names match FAMILY_SLUGS.en values exactly');
}

const esDirSet = new Set(esDirs);
const failsBefore = failures;
for (const slug of EXPECTED_ES_SLUGS) {
  if (!esDirSet.has(slug)) {
    console.error(`FAIL: ES crime dir missing expected slug "${slug}"`);
    failures++;
  }
}
for (const slug of esDirs) {
  if (!EXPECTED_ES_SLUGS.has(slug)) {
    console.error(`FAIL: ES crime dir "${slug}" is not in FAMILY_SLUGS ES values (slug drift)`);
    failures++;
  }
}
if (failures === failsBefore) {
  console.log('PASS: ES crime dir names match FAMILY_SLUGS.es values exactly');
}

// 3. Sample page assertions: EN crime/property and ES delito/propiedad
const SAMPLES = [
  {
    label: 'EN /crime/property/',
    htmlPath: path.join(enCrimeDir, 'property', 'index.html'),
    locale: 'en',
  },
  {
    label: 'ES /es/delito/propiedad/',
    htmlPath: path.join(esCrimeDir, 'propiedad', 'index.html'),
    locale: 'es',
  },
];

for (const sample of SAMPLES) {
  if (!existsSync(sample.htmlPath)) {
    console.error(`FAIL: ${sample.label} — index.html not found at ${sample.htmlPath}`);
    failures++;
    continue;
  }

  const html = readFileSync(sample.htmlPath, 'utf-8');
  const lower = html.toLowerCase();

  // 3a. Ranking table has multiple data rows (>= 10 expected, all non-low-pop communes)
  const tableRows = countTableRows(html);
  if (tableRows < 10) {
    console.error(`FAIL: ${sample.label} ranking table has only ${tableRows} rows (expected >= 10)`);
    failures++;
  } else {
    console.log(`PASS: ${sample.label} ranking table rows (${tableRows})`);
  }

  // 3b. Dataset JSON-LD present
  if (!lower.includes('"dataset"')) {
    console.error(`FAIL: ${sample.label} missing Dataset JSON-LD`);
    failures++;
  } else {
    console.log(`PASS: ${sample.label} Dataset JSON-LD present`);
  }

  // 3c. No Place @type in JSON-LD (crime pages must NOT emit Place — UI-SPEC line 288)
  // Extract JSON-LD script content and check for "place" type
  const jsonLdMatch = html.match(/<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/i);
  if (jsonLdMatch) {
    const jsonLdContent = jsonLdMatch[1].toLowerCase();
    if (jsonLdContent.includes('"place"') || jsonLdContent.includes('"administrativearea"')) {
      console.error(`FAIL: ${sample.label} JSON-LD contains Place/@type — crime pages must emit Dataset only`);
      failures++;
    } else {
      console.log(`PASS: ${sample.label} JSON-LD is Dataset-only (no Place type)`);
    }
  } else {
    console.error(`FAIL: ${sample.label} no JSON-LD script block found`);
    failures++;
  }

  // 3d. Reciprocal hreflang
  if (!html.includes('hreflang="en"')) {
    console.error(`FAIL: ${sample.label} missing hreflang="en"`);
    failures++;
  }
  if (!html.includes('hreflang="es"')) {
    console.error(`FAIL: ${sample.label} missing hreflang="es"`);
    failures++;
  }
  if (!html.includes('hreflang="x-default"')) {
    console.error(`FAIL: ${sample.label} missing hreflang="x-default"`);
    failures++;
  }
  console.log(`PASS: ${sample.label} hreflang alternates present`);

  // 3e. Self-canonical
  if (!lower.includes('rel="canonical"')) {
    console.error(`FAIL: ${sample.label} missing canonical link`);
    failures++;
  } else {
    console.log(`PASS: ${sample.label} canonical present`);
  }
}

// ---------------------------------------------------------------------------
// Check 4: homicide redirect stubs never become orphans (V-03, recalibrated).
// /crime/homicide/ and /es/delito/homicidios/ are TD-04 redirect stubs to the
// homicide ranking pages. F-01 proposed a >=2 inbound floor via a hub link,
// but that link sat on the VIDA card and landed users on the homicide ranking
// (wrong category) — reverted. The honest invariant is: the glossary keeps at
// least one inbound link so the legacy URLs stay discoverable and the 301
// keeps serving old external links.
// ---------------------------------------------------------------------------
function countInboundLinks(href, ownDir) {
  let count = 0;
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(p);
      else if (entry.name.endsWith('.html') && !p.includes(ownDir)) {
        const html = readFileSync(p, 'utf8');
        if (html.includes(`href="${href}"`)) count++;
      }
    }
  };
  walk(DIST_DIR);
  return count;
}

for (const [href, ownDir] of [
  ['/crime/homicide/', path.join('crime', 'homicide')],
  ['/es/delito/homicidios/', path.join('delito', 'homicidios')],
]) {
  const inbound = countInboundLinks(href, ownDir);
  if (inbound < 1) {
    console.error(`FAIL: ${href} has 0 inbound links site-wide — legacy redirect stub orphaned (V-03 guard)`);
    failures++;
  } else {
    console.log(`PASS: ${href} inbound link floor met (${inbound} page(s) link to it)`);
  }
}

if (failures > 0) {
  console.error(`\ncrime.mjs: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log('\ncrime.mjs: PASSED — all crime-type page assertions green');
