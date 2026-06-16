/**
 * seo.mjs — OG/Twitter meta + JSON-LD shape validator for Phase 13 SEO hardening.
 *
 * Assertions (run against an existing dist/ — does NOT rebuild):
 *
 *   M (OG asset existence):   dist/og/*.png exist (7 branded placeholder PNGs)
 *   N (OG meta presence):     sampled pages carry og:title/description/type/url/image/locale +
 *                             twitter:card=summary_large_image
 *   O (OG url locale):        EN pages' og:url has no /es/; ES pages' og:url contains /es/
 *   P (OG image absolute):    og:image matches https://ischilesafe.com/og/
 *   Q (JSON-LD parse):        every extracted ld+json block JSON.parses without error
 *   R (ItemList shape):       when present, itemListElement has numeric position + string url
 *   S (BreadcrumbList shape): when present, every element has position + name (+item on non-last)
 *
 * OG assertions (N/O/P) are GUARDED: they only fire on pages where the property is actually
 * present — so this validator passes on a pre-Plan-02 build where OG meta is not yet emitted.
 * JSON-LD parse (Q) and asset existence (M) are ALWAYS-ON.
 *
 * Usage:
 *   node scripts/validate/seo.mjs
 *
 * Exit code: 0 if all assertions pass, 1 if any fail.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

let failures = 0;

// ---------------------------------------------------------------------------
// Helper: recursively collect all .html file paths under a directory.
// ---------------------------------------------------------------------------
function collectHtmlFiles(dir) {
  if (!existsSync(dir)) return [];
  const result = [];
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...collectHtmlFiles(full));
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      result.push(full);
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Helper: extract ALL ld+json script blocks from HTML (g-flag loop).
// Returns array of parsed objects; parse failures push { _parseError, _raw }.
// ---------------------------------------------------------------------------
function extractAllJsonLd(html) {
  const re = /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi;
  const blocks = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    try {
      blocks.push(JSON.parse(m[1]));
    } catch (e) {
      blocks.push({ _parseError: e.message, _raw: m[1] });
    }
  }
  return blocks;
}

// ---------------------------------------------------------------------------
// Helper: get first subdirectory name deterministically (mirrors spine.mjs)
// ---------------------------------------------------------------------------
function firstSubdir(dir) {
  if (!existsSync(dir)) return null;
  const entry = readdirSync(dir, { withFileTypes: true }).find((d) => d.isDirectory());
  return entry ? entry.name : null;
}

// ---------------------------------------------------------------------------
// OG keys expected on every page (property= attribute form)
// ---------------------------------------------------------------------------
const OG_KEYS = ['og:title', 'og:description', 'og:type', 'og:url', 'og:image', 'og:locale'];

// ---------------------------------------------------------------------------
// checkOg: assert OG/Twitter meta presence + locale-correctness on a page.
// GUARDED: if the page lacks og:title entirely, skip OG checks (pre-Plan-02 build).
// ---------------------------------------------------------------------------
function checkOg(htmlPath, label, expectEsUrl) {
  if (!existsSync(htmlPath)) {
    // Missing sample page is reported but only warns — sampled editorial pages
    // may not exist in a partial build.
    console.log(`SKIP [OG] ${label}: file missing (sample page not in this build)`);
    return;
  }
  const html = readFileSync(htmlPath, 'utf-8');

  // Gate: if og:title is absent, OG meta is not yet emitted (pre-Plan-02). Skip.
  if (!html.includes('property="og:title"')) {
    console.log(`SKIP [OG] ${label}: og:title absent — OG not yet emitted (expected pre-Plan-02)`);
    return;
  }

  // All OG keys must be present
  for (const k of OG_KEYS) {
    if (!html.includes(`property="${k}"`)) {
      console.error(`FAIL [N] ${label}: missing ${k}`);
      failures++;
    }
  }

  // Twitter card
  if (!html.includes('name="twitter:card" content="summary_large_image"') &&
      !html.includes("name=\"twitter:card\" content='summary_large_image'")) {
    console.error(`FAIL [N] ${label}: twitter:card not summary_large_image`);
    failures++;
  }

  // og:url locale (O)
  const urlMatch = html.match(/property="og:url"\s+content="([^"]+)"/);
  if (urlMatch) {
    const isEs = /\/es\//.test(urlMatch[1]);
    if (expectEsUrl !== isEs) {
      console.error(`FAIL [O] ${label}: og:url locale mismatch (${urlMatch[1]})`);
      failures++;
    }
  }

  // og:image absolute under /og/ (P)
  const imgMatch = html.match(/property="og:image"\s+content="([^"]+)"/);
  if (imgMatch) {
    if (!imgMatch[1].includes('https://ischilesafe.com/og/')) {
      console.error(`FAIL [P] ${label}: og:image not absolute under /og/ (${imgMatch[1]})`);
      failures++;
    }
  }

  console.log(`PASS [OG] ${label}: OG/Twitter meta present and locale-correct`);
}

// ---------------------------------------------------------------------------
// ASSERTION M: OG PNG assets exist in dist/og/
// ---------------------------------------------------------------------------
const OG_TYPES = ['default', 'home', 'commune', 'region', 'crime', 'ranking', 'editorial'];

const distOgDir = path.join(DIST_DIR, 'og');
let allOgPresent = true;
for (const type of OG_TYPES) {
  const ogPath = path.join(distOgDir, `${type}.png`);
  if (!existsSync(ogPath)) {
    console.error(`FAIL [M] og-assets: dist/og/${type}.png not found`);
    failures++;
    allOgPresent = false;
  }
}
if (allOgPresent) {
  console.log(`PASS [M] og-assets: all 7 dist/og/*.png present`);
}

// ---------------------------------------------------------------------------
// Build sample page paths (one per template type × both locales)
// ---------------------------------------------------------------------------
const enCommuneDir = path.join(DIST_DIR, 'commune');
const esComunaDir = path.join(DIST_DIR, 'es', 'comuna');
const enRegionDir = path.join(DIST_DIR, 'region');
const esRegionDir = path.join(DIST_DIR, 'es', 'region');
const enCrimeDir = path.join(DIST_DIR, 'crime');
const esCrimeDir = path.join(DIST_DIR, 'es', 'delito');

const firstCommuneEn = firstSubdir(enCommuneDir);
const firstCommuneEs = firstSubdir(esComunaDir);
const firstRegionEn = firstSubdir(enRegionDir);
const firstRegionEs = firstSubdir(esRegionDir);
const firstCrimeEn = firstSubdir(enCrimeDir);
const firstCrimeEs = firstSubdir(esCrimeDir);

const SAMPLES = [
  // [htmlPath, label, expectEsUrl]
  [path.join(DIST_DIR, 'index.html'),                          'home (EN)',        false],
  [path.join(DIST_DIR, 'es', 'index.html'),                   'home (ES)',         true],
  ...(firstCommuneEn ? [[path.join(enCommuneDir, firstCommuneEn, 'index.html'), `commune/${firstCommuneEn} (EN)`, false]] : []),
  ...(firstCommuneEs ? [[path.join(esComunaDir,  firstCommuneEs, 'index.html'), `comune/${firstCommuneEs} (ES)`,  true]] : []),
  ...(firstRegionEn  ? [[path.join(enRegionDir,  firstRegionEn,  'index.html'), `region/${firstRegionEn} (EN)`,   false]] : []),
  ...(firstRegionEs  ? [[path.join(esRegionDir,  firstRegionEs,  'index.html'), `region/${firstRegionEs} (ES)`,   true]] : []),
  ...(firstCrimeEn   ? [[path.join(enCrimeDir,   firstCrimeEn,   'index.html'), `crime/${firstCrimeEn} (EN)`,    false]] : []),
  ...(firstCrimeEs   ? [[path.join(esCrimeDir,   firstCrimeEs,   'index.html'), `crime/${firstCrimeEs} (ES)`,    true]] : []),
  [path.join(DIST_DIR, 'rankings', 'index.html'),              'rankings (EN)',    false],
  [path.join(DIST_DIR, 'es', 'rankings', 'index.html'),        'rankings (ES)',     true],
  [path.join(DIST_DIR, 'is-chile-safe', 'index.html'),         'editorial (EN)',   false],
  [path.join(DIST_DIR, 'es', 'delitos-por-comuna', 'index.html'), 'editorial (ES)', true],
];

// ---------------------------------------------------------------------------
// ASSERTIONS N/O/P: OG meta presence + locale + image
// ---------------------------------------------------------------------------
for (const [htmlPath, label, expectEsUrl] of SAMPLES) {
  checkOg(htmlPath, label, expectEsUrl);
}

// ---------------------------------------------------------------------------
// ASSERTIONS Q/R/S: JSON-LD parse + shape checks on all sampled pages
// ---------------------------------------------------------------------------
for (const [htmlPath, label] of SAMPLES) {
  if (!existsSync(htmlPath)) continue;

  const html = readFileSync(htmlPath, 'utf-8');
  const blocks = extractAllJsonLd(html);

  // Q: every block must parse without error
  for (const block of blocks) {
    if (block._parseError) {
      console.error(`FAIL [Q] ${label}: JSON-LD parse error — ${block._parseError}`);
      failures++;
    }
  }

  const validBlocks = blocks.filter((b) => !b._parseError);

  // R: ItemList shape
  for (const block of validBlocks) {
    if (block['@type'] === 'ItemList') {
      const items = block.itemListElement;
      if (!Array.isArray(items) || items.length === 0) {
        console.error(`FAIL [R] ${label}: ItemList.itemListElement is missing or empty`);
        failures++;
        continue;
      }
      let itemOk = true;
      for (const item of items) {
        if (typeof item.position !== 'number') {
          console.error(`FAIL [R] ${label}: ListItem missing numeric position`);
          failures++;
          itemOk = false;
          break;
        }
        if (typeof item.url !== 'string') {
          console.error(`FAIL [R] ${label}: ListItem missing string url`);
          failures++;
          itemOk = false;
          break;
        }
      }
      if (itemOk) {
        console.log(`PASS [R] ${label}: ItemList shape valid`);
      }
    }
  }

  // S: BreadcrumbList shape
  for (const block of validBlocks) {
    if (block['@type'] === 'BreadcrumbList') {
      const items = block.itemListElement;
      if (!Array.isArray(items) || items.length === 0) {
        console.error(`FAIL [S] ${label}: BreadcrumbList.itemListElement is missing or empty`);
        failures++;
        continue;
      }
      let crumbOk = true;
      for (let i = 0; i < items.length; i++) {
        const crumb = items[i];
        if (typeof crumb.position !== 'number') {
          console.error(`FAIL [S] ${label}: BreadcrumbList ListItem[${i}] missing numeric position`);
          failures++;
          crumbOk = false;
          break;
        }
        if (typeof crumb.name !== 'string') {
          console.error(`FAIL [S] ${label}: BreadcrumbList ListItem[${i}] missing string name`);
          failures++;
          crumbOk = false;
          break;
        }
        // All but possibly the last should have item
        if (i < items.length - 1 && crumb.item === undefined) {
          console.error(`FAIL [S] ${label}: BreadcrumbList ListItem[${i}] (non-last) missing item`);
          failures++;
          crumbOk = false;
          break;
        }
      }
      if (crumbOk) {
        console.log(`PASS [S] ${label}: BreadcrumbList shape valid`);
      }
    }
  }

  // If no ld+json blocks at all, still counts as Q-pass (nothing to parse)
  if (blocks.length === 0) {
    console.log(`PASS [Q] ${label}: no ld+json blocks (pre-injection state)`);
  } else if (!blocks.some((b) => b._parseError)) {
    console.log(`PASS [Q] ${label}: all ${blocks.length} ld+json block(s) parse cleanly`);
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nseo.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}

console.log('\nseo.mjs: PASSED');
process.exit(0);
