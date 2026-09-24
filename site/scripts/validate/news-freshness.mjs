/**
 * news-freshness.mjs — Validator #18: news pages + commune sections are
 * consistent with the newest-incident evidence the build actually consumed
 * (FRESH-01/FRESH-02/FRESH-03).
 *
 * This validator is data-agnostic: it uses the shared G-05 rule
 * (site/src/lib/newsEvidence.mjs) to derive the expected verdict from
 * whatever payload the build read, and checks that the served HTML agrees
 * with that verdict — it PASSes whether the live news feed is fresh or
 * stale. It does not itself decide whether the feed being stale is
 * acceptable (that is freshness.mjs's job, validator #15).
 *
 * Checks:
 * 1. dist/news/index.html ('en') and dist/es/noticias/index.html ('es')
 *    against the payload — latest-incident stamp, stale-notice
 *    presence/absence, per-bar gap flags (R1/R-01), and gap-caption spans
 *    (R2/F35-R1-04).
 * 2. Every dist/commune/&lt;slug&gt;/index.html ('en') and
 *    dist/es/comuna/&lt;slug&gt;/index.html ('es') cnews-section — data-news-stale + heading consistency
 *    (FRESH-03, R1/R-08).
 * 3. FAILs if the EN and ES commune-section counts differ, or if
 *    payload.incidents is non-empty and the EN section count is 0.
 *
 * Env overrides (test-only / 35-07 prod-fetched-HTML reuse):
 *   NEWS_FRESHNESS_CURRENT_JSON — path to the payload file (else
 *     site/public/data/incidents/current.json — the exact file the build
 *     consumed)
 *   NEWS_FRESHNESS_DIST — dist root (else site/dist)
 *
 * Exit codes:
 *   0 — PASS
 *   1 — any check failed
 *
 * Usage:
 *   node scripts/validate/news-freshness.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { checkNewsPage, checkCommuneSection } from './news-freshness.lib.mjs';
import { evidenceVerdict, computeEvidence, MAX_AGE_HOURS } from '../../src/lib/newsEvidence.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');

const DEFAULT_CURRENT_JSON = path.join(SITE_ROOT, 'public', 'data', 'incidents', 'current.json');
const CURRENT_JSON_PATH = process.env.NEWS_FRESHNESS_CURRENT_JSON || DEFAULT_CURRENT_JSON;
const DIST_DIR = process.env.NEWS_FRESHNESS_DIST || path.join(SITE_ROOT, 'dist');

const errors = [];

function toLabel(p) {
  return path.relative(SITE_ROOT, p).split(path.sep).join('/');
}

let payload = {};
if (existsSync(CURRENT_JSON_PATH)) {
  try {
    payload = JSON.parse(readFileSync(CURRENT_JSON_PATH, 'utf-8')) ?? {};
  } catch {
    payload = {};
  }
}

// ---------------------------------------------------------------------------
// 1. News pages (EN/ES)
// ---------------------------------------------------------------------------
const newsPages = [
  { p: path.join(DIST_DIR, 'news', 'index.html'), locale: 'en' },
  { p: path.join(DIST_DIR, 'es', 'noticias', 'index.html'), locale: 'es' },
];
for (const { p, locale } of newsPages) {
  if (!existsSync(p)) {
    errors.push(`news page missing: ${toLabel(p)}`);
    continue;
  }
  const html = readFileSync(p, 'utf-8');
  const pageErrors = checkNewsPage(html, payload, locale);
  for (const e of pageErrors) errors.push(`${toLabel(p)}: ${e}`);
}

// ---------------------------------------------------------------------------
// 2. Commune sections (EN/ES)
// ---------------------------------------------------------------------------
function listCommuneSlugs(localeDir) {
  if (!existsSync(localeDir)) return [];
  return readdirSync(localeDir, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();
}

const enCommuneDir = path.join(DIST_DIR, 'commune');
const esCommuneDir = path.join(DIST_DIR, 'es', 'comuna');
const enSlugs = listCommuneSlugs(enCommuneDir);
const esSlugs = listCommuneSlugs(esCommuneDir);

let enSectionCount = 0;
let enCaveatedCount = 0;
for (const slug of enSlugs) {
  const p = path.join(enCommuneDir, slug, 'index.html');
  if (!existsSync(p)) continue;
  const html = readFileSync(p, 'utf-8');
  if (!html.includes('class="cnews-section"')) continue;
  enSectionCount++;
  if (html.includes('data-news-stale="true"')) enCaveatedCount++;
  const pageErrors = checkCommuneSection(html, 'en');
  for (const e of pageErrors) errors.push(`${toLabel(p)}: ${e}`);
}

let esSectionCount = 0;
let esCaveatedCount = 0;
for (const slug of esSlugs) {
  const p = path.join(esCommuneDir, slug, 'index.html');
  if (!existsSync(p)) continue;
  const html = readFileSync(p, 'utf-8');
  if (!html.includes('class="cnews-section"')) continue;
  esSectionCount++;
  if (html.includes('data-news-stale="true"')) esCaveatedCount++;
  const pageErrors = checkCommuneSection(html, 'es');
  for (const e of pageErrors) errors.push(`${toLabel(p)}: ${e}`);
}

if (enSectionCount !== esSectionCount) {
  errors.push(`commune cnews-section count mismatch: en=${enSectionCount} es=${esSectionCount}`);
}
const incidentsNonEmpty = Array.isArray(payload?.incidents) && payload.incidents.length > 0;
if (incidentsNonEmpty && enSectionCount === 0) {
  errors.push('payload has incidents but 0 EN commune cnews-sections were found');
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
const buildNowMs = Date.now();
const verdict = evidenceVerdict(computeEvidence(payload), buildNowMs, MAX_AGE_HOURS);
const newsStale = verdict === 'stale' || verdict === 'none';
const evidence = computeEvidence(payload);

if (errors.length > 0) {
  console.error(`FAIL news-freshness: ${errors.length} error(s)`);
  for (const e of errors.slice(0, 30)) {
    console.error(`  - ${e}`);
  }
  if (errors.length > 30) {
    console.error(`  ... and ${errors.length - 30} more`);
  }
  process.exit(1);
}

console.log(
  `PASS news-freshness: news stale=${newsStale} (evidence ${evidence ? evidence.label : 'none'}, build-now ${new Date(buildNowMs).toISOString()}); ` +
  `communes EN ${enSectionCount}/${enCaveatedCount} caveated, ES ${esSectionCount}/${esCaveatedCount}`
);
