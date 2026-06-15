/**
 * coverage.mjs — Coverage validator for the full 346×2 commune build.
 *
 * Assertions (run against an existing dist/ — does NOT rebuild):
 *
 *   A (route-count):           dist/commune/* dirs === dist/es/comuna/* dirs === index length
 *   B (no-orphan-link):        every /commune/{slug}/ and /es/comuna/{slug}/ href found in
 *                              any dist HTML has a corresponding generated page in dist/
 *   C (sitemap-coverage):      dist/sitemap-0.xml contains 346 .../commune/ <loc> entries
 *                              and 346 .../es/comuna/ <loc> entries, plus the directory URLs
 *   D (directory-completeness): dist/communes/index.html contains >=346 /commune/ hrefs;
 *                              dist/es/comunas/index.html contains >=346 /es/comuna/ hrefs
 *
 * Expected count is derived from data/cead/meta/index.json (NOT a hardcoded literal)
 * so this validator tracks the real index length automatically.
 *
 * NOTE: This scaffold is allowed to REPORT FAILURES at Wave 0 (directory pages and the
 * full 346 rollout do not exist yet). It is wired into all.mjs in Plan 04 after the
 * rollout flip and directory pages land.
 *
 * Usage:
 *   node scripts/validate/coverage.mjs
 *
 * Exit code: 0 if all assertions pass, 1 if any fail.
 */

import { readFileSync, existsSync, readdirSync, readdirSync as readDir } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// Load expected count from the canonical source — same path that rollout.mjs uses.
const INDEX_PATH = path.resolve(SITE_ROOT, '..', 'data', 'cead', 'meta', 'index.json');
if (!existsSync(INDEX_PATH)) {
  console.error(`FAIL: index.json not found at ${INDEX_PATH}`);
  process.exit(1);
}
const index = JSON.parse(readFileSync(INDEX_PATH, 'utf-8'));
const EXPECTED = index.length; // 346 (or whatever the real index length is)
console.log(`Expected commune count (from index.json): ${EXPECTED}`);

let failures = 0;

// ---------------------------------------------------------------------------
// ASSERTION A: route-count
// dist/commune/* dirs === dist/es/comuna/* dirs === EXPECTED
// ---------------------------------------------------------------------------
const enDir = path.join(DIST_DIR, 'commune');
const esDir = path.join(DIST_DIR, 'es', 'comuna');

let enSlugs = [];
let esSlugs = [];

if (!existsSync(enDir)) {
  console.error(`FAIL [A] dist/commune not found — run npm run build first`);
  failures++;
} else {
  enSlugs = readdirSync(enDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

if (!existsSync(esDir)) {
  console.error(`FAIL [A] dist/es/comuna not found — run npm run build first`);
  failures++;
} else {
  esSlugs = readdirSync(esDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

if (existsSync(enDir) && existsSync(esDir)) {
  const aEnPass = enSlugs.length === EXPECTED;
  const aEsPass = esSlugs.length === EXPECTED;
  const aParityPass = enSlugs.length === esSlugs.length;

  if (aEnPass && aEsPass && aParityPass) {
    console.log(`PASS [A] route-count: EN=${enSlugs.length} ES=${esSlugs.length} (both === ${EXPECTED})`);
  } else {
    if (!aEnPass) {
      console.error(`FAIL [A] route-count: dist/commune has ${enSlugs.length} dirs, expected ${EXPECTED}`);
      failures++;
    }
    if (!aEsPass) {
      console.error(`FAIL [A] route-count: dist/es/comuna has ${esSlugs.length} dirs, expected ${EXPECTED}`);
      failures++;
    }
    if (!aParityPass) {
      console.error(`FAIL [A] route-count: EN (${enSlugs.length}) and ES (${esSlugs.length}) counts differ`);
      failures++;
    }
  }
}

// ---------------------------------------------------------------------------
// ASSERTION B: no-orphan-link
// Scan all dist/**/*.html, extract commune hrefs, assert each has a page.
// ---------------------------------------------------------------------------
/**
 * Recursively collect all .html file paths under a directory.
 */
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

const allHtmlFiles = collectHtmlFiles(DIST_DIR);

const orphanEnSlugs = new Set();
const orphanEsSlugs = new Set();

// Regex patterns for commune hrefs
const EN_HREF_RE = /href="\/commune\/([^/"]+)\//g;
const ES_HREF_RE = /href="\/es\/comuna\/([^/"]+)\//g;

const enPageSet = new Set(enSlugs);
const esPageSet = new Set(esSlugs);

for (const htmlFile of allHtmlFiles) {
  const content = readFileSync(htmlFile, 'utf-8');

  let m;
  EN_HREF_RE.lastIndex = 0;
  while ((m = EN_HREF_RE.exec(content)) !== null) {
    const slug = m[1];
    if (!enPageSet.has(slug)) {
      orphanEnSlugs.add(slug);
    }
  }

  ES_HREF_RE.lastIndex = 0;
  while ((m = ES_HREF_RE.exec(content)) !== null) {
    const slug = m[1];
    if (!esPageSet.has(slug)) {
      orphanEsSlugs.add(slug);
    }
  }
}

if (orphanEnSlugs.size === 0 && orphanEsSlugs.size === 0) {
  console.log(`PASS [B] no-orphan-link: 0 dead commune links across ${allHtmlFiles.length} HTML files`);
} else {
  if (orphanEnSlugs.size > 0) {
    console.error(`FAIL [B] no-orphan-link: ${orphanEnSlugs.size} orphan EN slugs: ${[...orphanEnSlugs].slice(0, 5).join(', ')}${orphanEnSlugs.size > 5 ? ' …' : ''}`);
    failures++;
  }
  if (orphanEsSlugs.size > 0) {
    console.error(`FAIL [B] no-orphan-link: ${orphanEsSlugs.size} orphan ES slugs: ${[...orphanEsSlugs].slice(0, 5).join(', ')}${orphanEsSlugs.size > 5 ? ' …' : ''}`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// ASSERTION C: sitemap-coverage
// dist/sitemap-0.xml contains EXPECTED .../commune/ <loc> entries and
// EXPECTED .../es/comuna/ <loc> entries, plus the directory URLs.
// ---------------------------------------------------------------------------
const SITEMAP_PATH = path.join(DIST_DIR, 'sitemap-0.xml');

if (!existsSync(SITEMAP_PATH)) {
  console.error(`FAIL [C] sitemap-coverage: dist/sitemap-0.xml not found`);
  failures++;
} else {
  const sitemapContent = readFileSync(SITEMAP_PATH, 'utf-8');
  const LOC_RE = /<loc>([^<]+)<\/loc>/g;

  const enCommuneLocs = new Set();
  const esComunaLocs = new Set();
  let hasEnDirectory = false;
  let hasEsDirectory = false;

  let lm;
  LOC_RE.lastIndex = 0;
  while ((lm = LOC_RE.exec(sitemapContent)) !== null) {
    const url = lm[1];
    if (/\/commune\/[^/]+\/$/.test(url)) {
      enCommuneLocs.add(url);
    } else if (/\/es\/comuna\/[^/]+\/$/.test(url)) {
      esComunaLocs.add(url);
    }
    if (/\/communes\//.test(url)) hasEnDirectory = true;
    if (/\/es\/comunas\//.test(url)) hasEsDirectory = true;
  }

  const cEnPass = enCommuneLocs.size === EXPECTED;
  const cEsPass = esComunaLocs.size === EXPECTED;

  if (cEnPass && cEsPass && hasEnDirectory && hasEsDirectory) {
    console.log(`PASS [C] sitemap-coverage: ${enCommuneLocs.size} EN + ${esComunaLocs.size} ES commune locs; directory URLs present`);
  } else {
    if (!cEnPass) {
      console.error(`FAIL [C] sitemap-coverage: ${enCommuneLocs.size} EN commune <loc> entries, expected ${EXPECTED}`);
      failures++;
    }
    if (!cEsPass) {
      console.error(`FAIL [C] sitemap-coverage: ${esComunaLocs.size} ES comuna <loc> entries, expected ${EXPECTED}`);
      failures++;
    }
    if (!hasEnDirectory) {
      console.error(`FAIL [C] sitemap-coverage: /communes/ directory URL not found in sitemap`);
      failures++;
    }
    if (!hasEsDirectory) {
      console.error(`FAIL [C] sitemap-coverage: /es/comunas/ directory URL not found in sitemap`);
      failures++;
    }
  }
}

// ---------------------------------------------------------------------------
// ASSERTION D: directory-completeness
// dist/communes/index.html contains >=EXPECTED /commune/ hrefs
// dist/es/comunas/index.html contains >=EXPECTED /es/comuna/ hrefs
// ---------------------------------------------------------------------------
const EN_DIR_PAGE = path.join(DIST_DIR, 'communes', 'index.html');
const ES_DIR_PAGE = path.join(DIST_DIR, 'es', 'comunas', 'index.html');

function countDistinctMatches(htmlContent, re) {
  const found = new Set();
  let m;
  re.lastIndex = 0;
  while ((m = re.exec(htmlContent)) !== null) {
    found.add(m[1]);
  }
  return found.size;
}

if (!existsSync(EN_DIR_PAGE)) {
  console.error(`FAIL [D] directory-completeness: dist/communes/index.html not found`);
  failures++;
} else {
  const content = readFileSync(EN_DIR_PAGE, 'utf-8');
  const count = countDistinctMatches(content, /href="\/commune\/([^/"]+)\//g);
  if (count >= EXPECTED) {
    console.log(`PASS [D] directory-completeness: ${count} distinct /commune/ hrefs in EN directory`);
  } else {
    console.error(`FAIL [D] directory-completeness: EN directory has ${count} distinct /commune/ hrefs, expected >=${EXPECTED}`);
    failures++;
  }
}

if (!existsSync(ES_DIR_PAGE)) {
  console.error(`FAIL [D] directory-completeness: dist/es/comunas/index.html not found`);
  failures++;
} else {
  const content = readFileSync(ES_DIR_PAGE, 'utf-8');
  const count = countDistinctMatches(content, /href="\/es\/comuna\/([^/"]+)\//g);
  if (count >= EXPECTED) {
    console.log(`PASS [D] directory-completeness: ${count} distinct /es/comuna/ hrefs in ES directory`);
  } else {
    console.error(`FAIL [D] directory-completeness: ES directory has ${count} distinct /es/comuna/ hrefs, expected >=${EXPECTED}`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\ncoverage.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}

console.log(`\ncoverage.mjs: PASSED`);
