/**
 * cead-vintage.mjs — Validator #17: FRESH-05 CEAD as-of + partial-year label
 * on methodology, region and commune pages (EN/ES), plus a banned invented-
 * cutoff-phrasing scan over the whole dist tree (R-02).
 *
 * Checks:
 * 1. dist/methodology/index.html + dist/es/metodologia/index.html against
 *    data/cead/national.json, in methodology mode (asserts the narrative
 *    "(currently N)" / "(actualmente N)" sentence too).
 * 1b. Every data/cead/regions/*.json against dist/region/<slug> and
 *     dist/es/region/<slug> (16 files). FAIL if either locale count is 0 or
 *     EN != ES. In the default dist, a missing region page FAILs by name;
 *     in subset mode (CEAD_VINTAGE_DIST set — used by 35-07 against fetched
 *     prod pages) a missing page is skipped, but each locale count must
 *     still be >= 1 and EN == ES.
 * 2. Every data/cead/meta/index.json entry against dist/commune/<slug> and
 *    dist/es/comuna/<slug>, when present (skip if absent — same subset
 *    logic as region pages, harmless in the default dist where all 346
 *    exist).
 * 3. FAIL if either locale's commune count is 0 or EN != ES.
 * 3b. Scan dist/**\/*.html plus site/src/components/map/ResultPanel.tsx for
 *     the banned invented partial-year phrasing (R-02). Any hit is an error
 *     naming the file. FAIL if 0 HTML files were scanned (R2/F35-R1-02).
 *
 * Dist root: env CEAD_VINTAGE_DIST, else site/dist. This injection point is
 * what 35-07 uses to run this validator against HTML fetched from prod.
 *
 * Exit codes:
 *   0 — PASS
 *   1 — any check failed
 *
 * Usage:
 *   node scripts/validate/cead-vintage.mjs
 *   CEAD_VINTAGE_DIST=<path> node scripts/validate/cead-vintage.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { expectedFromJson, checkCeadVintagePage, findBannedPartialLabels } from './cead-vintage.lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');

const SUBSET_MODE = process.env.CEAD_VINTAGE_DIST !== undefined;
const DIST_DIR = SUBSET_MODE ? process.env.CEAD_VINTAGE_DIST : path.join(SITE_ROOT, 'dist');

const errors = [];

function readJson(p) {
  return JSON.parse(readFileSync(p, 'utf-8'));
}

function readHtml(p) {
  return readFileSync(p, 'utf-8');
}

// Posix-relative label for error messages (Windows path.join uses '\\',
// which breaks any consumer that greps for a forward-slash substring —
// see figure-registry.mjs:356 for the same normalization).
function toLabel(p) {
  return path.relative(SITE_ROOT, p).split(path.sep).join('/');
}

function collectHtmlFiles(dir) {
  if (!existsSync(dir)) return [];
  const result = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
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
// 1. Methodology pages
// ---------------------------------------------------------------------------
const nationalPath = path.join(REPO_ROOT, 'data', 'cead', 'national.json');
const national = readJson(nationalPath);
const nationalExpected = expectedFromJson(national);

let methodologyCount = 0;
const methodologyPages = [
  { p: path.join(DIST_DIR, 'methodology', 'index.html'), locale: 'en' },
  { p: path.join(DIST_DIR, 'es', 'metodologia', 'index.html'), locale: 'es' },
];
for (const { p, locale } of methodologyPages) {
  if (!existsSync(p)) {
    if (SUBSET_MODE) continue;
    errors.push(`methodology page missing: ${p}`);
    continue;
  }
  const html = readHtml(p);
  const pageErrors = checkCeadVintagePage(html, nationalExpected, locale, { methodology: true });
  for (const e of pageErrors) errors.push(`${toLabel(p)}: ${e}`);
  methodologyCount++;
}
if (!SUBSET_MODE && methodologyCount !== 2) {
  errors.push(`expected 2 methodology pages checked, got ${methodologyCount}`);
}

// ---------------------------------------------------------------------------
// 1b. Region pages (R-02, 16 per locale)
// ---------------------------------------------------------------------------
const regionsDir = path.join(REPO_ROOT, 'data', 'cead', 'regions');
const regionFiles = readdirSync(regionsDir).filter((f) => f.endsWith('.json'));

let regionEnCount = 0;
let regionEsCount = 0;
for (const file of regionFiles) {
  const region = readJson(path.join(regionsDir, file));
  const slug = region.slug;
  const expected = expectedFromJson({
    series: region.series,
    last_updated: region.last_updated ?? national.last_updated,
  });

  const enPath = path.join(DIST_DIR, 'region', slug, 'index.html');
  const esPath = path.join(DIST_DIR, 'es', 'region', slug, 'index.html');

  if (existsSync(enPath)) {
    const pageErrors = checkCeadVintagePage(readHtml(enPath), expected, 'en');
    for (const e of pageErrors) errors.push(`${toLabel(enPath)}: ${e}`);
    regionEnCount++;
  } else if (!SUBSET_MODE) {
    errors.push(`region page missing (en): ${slug}`);
  }

  if (existsSync(esPath)) {
    const pageErrors = checkCeadVintagePage(readHtml(esPath), expected, 'es');
    for (const e of pageErrors) errors.push(`${toLabel(esPath)}: ${e}`);
    regionEsCount++;
  } else if (!SUBSET_MODE) {
    errors.push(`region page missing (es): ${slug}`);
  }
}

if (regionEnCount === 0) errors.push('region pages (en): 0 checked');
if (regionEsCount === 0) errors.push('region pages (es): 0 checked');
if (regionEnCount !== regionEsCount) {
  errors.push(`region page count mismatch: en=${regionEnCount} es=${regionEsCount}`);
}
if (!SUBSET_MODE && (regionEnCount !== 16 || regionEsCount !== 16)) {
  errors.push(`expected 16/16 region pages, got ${regionEnCount}/${regionEsCount}`);
}

// ---------------------------------------------------------------------------
// 2/3. Commune pages
// ---------------------------------------------------------------------------
const meta = readJson(path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json'));

let communeEnCount = 0;
let communeEsCount = 0;
for (const entry of meta) {
  const cut = entry.cut;
  const slug = entry.slug;
  const communePath = path.join(REPO_ROOT, 'data', 'cead', 'comunas', `${cut}.json`);
  let commune = null;
  if (existsSync(communePath)) {
    commune = readJson(communePath);
  }
  const expected = expectedFromJson({
    series: commune?.series ?? [],
    last_updated: commune?.last_updated ?? national.last_updated,
  });

  const enPath = path.join(DIST_DIR, 'commune', slug, 'index.html');
  const esPath = path.join(DIST_DIR, 'es', 'comuna', slug, 'index.html');

  if (existsSync(enPath)) {
    const pageErrors = checkCeadVintagePage(readHtml(enPath), expected, 'en');
    for (const e of pageErrors) errors.push(`${toLabel(enPath)}: ${e}`);
    communeEnCount++;
  }
  if (existsSync(esPath)) {
    const pageErrors = checkCeadVintagePage(readHtml(esPath), expected, 'es');
    for (const e of pageErrors) errors.push(`${toLabel(esPath)}: ${e}`);
    communeEsCount++;
  }
}

if (communeEnCount === 0) errors.push('commune pages (en): 0 checked');
if (communeEsCount === 0) errors.push('commune pages (es): 0 checked');
if (communeEnCount !== communeEsCount) {
  errors.push(`commune page count mismatch: en=${communeEnCount} es=${communeEsCount}`);
}

// ---------------------------------------------------------------------------
// 3b. Banned invented partial-year phrasing scan (R-02)
// ---------------------------------------------------------------------------
const htmlFiles = collectHtmlFiles(DIST_DIR);
const resultPanelPath = path.join(SITE_ROOT, 'src', 'components', 'map', 'ResultPanel.tsx');
const scannedFiles = [...htmlFiles];
if (existsSync(resultPanelPath)) scannedFiles.push(resultPanelPath);

let bannedHits = 0;
for (const file of scannedFiles) {
  const content = readFileSync(file, 'utf-8');
  const hits = findBannedPartialLabels(content);
  if (hits.length > 0) {
    bannedHits += hits.length;
    errors.push(`${toLabel(file)}: banned partial-year phrasing found: ${hits.join(', ')}`);
  }
}

if (htmlFiles.length === 0) {
  errors.push('R2/F35-R1-02: 0 HTML files scanned for banned partial labels');
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
if (errors.length > 0) {
  console.error(`FAIL cead-vintage: ${errors.length} error(s)`);
  for (const e of errors.slice(0, 20)) {
    console.error(`  - ${e}`);
  }
  if (errors.length > 20) {
    console.error(`  ... and ${errors.length - 20} more`);
  }
  process.exit(1);
}

console.log(
  `PASS cead-vintage: ${methodologyCount} methodology + ${regionEnCount}/${regionEsCount} region + ` +
  `${communeEnCount}/${communeEsCount} commune pages (EN/ES), 0 banned partial labels in ${htmlFiles.length} html files, ` +
  `CEAD as of ${national.last_updated}`
);
