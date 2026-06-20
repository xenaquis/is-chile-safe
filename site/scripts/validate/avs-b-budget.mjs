/**
 * avs-b-budget.mjs — Build-time file-budget + pair-symmetry assertion (CMP-05).
 *
 * Asserts:
 *   1. Total dist/ file count < 18,000 (Cloudflare Pages free-tier safe bound).
 *      Fails with "[CMP-05] File budget exceeded" if totalFiles >= SAFE_BOUND.
 *   2. EN compare-page count === ES comparar-page count (pair-symmetry — guards CMP-03
 *      reciprocity: every pair must be rendered in both locales).
 *
 * If dist/ does not exist, exits 0 with a note (safe to run before first build).
 */

import { existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// ---------------------------------------------------------------------------
// Graceful exit if dist/ is absent
// ---------------------------------------------------------------------------
if (!existsSync(DIST_DIR)) {
  console.log('avs-b-budget: dist/ not found — run npm run build first (exiting 0)');
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Recursive file counter
// ---------------------------------------------------------------------------
function countFiles(dir) {
  let count = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) count += countFiles(full);
    else count++;
  }
  return count;
}

// ---------------------------------------------------------------------------
// Recursive directory counter (counts direct subdirectory names only — each
// rendered A-vs-B page produces a {pair}/ dir with an index.html inside)
// ---------------------------------------------------------------------------
function countDirs(dir) {
  if (!existsSync(dir)) return 0;
  return readdirSync(dir, { withFileTypes: true }).filter(e => e.isDirectory()).length;
}

let failures = 0;

// ---------------------------------------------------------------------------
// Assertion 1: Total file budget
// ---------------------------------------------------------------------------
const SAFE_BOUND = 18000;
const totalFiles = countFiles(DIST_DIR);

if (totalFiles >= SAFE_BOUND) {
  console.error(
    `FAIL [CMP-05] File budget exceeded: ${totalFiles} files in dist/ (limit ${SAFE_BOUND}). ` +
    `Reduce the number of enabled pairs in data/comparator-pairs.json or check for asset bloat.`
  );
  failures++;
} else {
  console.log(
    `PASS [CMP-05] File budget: ${totalFiles} files in dist/ (limit ${SAFE_BOUND}, margin ${SAFE_BOUND - totalFiles})`
  );
}

// ---------------------------------------------------------------------------
// Assertion 2: EN/ES pair symmetry
// (dist/compare/ dirs vs dist/es/comparar/ dirs — excluding any non-pair dirs)
// ---------------------------------------------------------------------------
const compareEnDir = path.join(DIST_DIR, 'compare');
const compareEsDir = path.join(DIST_DIR, 'es', 'comparar');

// Count subdirs that look like a pair slug (contain "-vs-")
function countPairDirs(dir) {
  if (!existsSync(dir)) return 0;
  return readdirSync(dir, { withFileTypes: true })
    .filter(e => e.isDirectory() && e.name.includes('-vs-'))
    .length;
}

const enPairs = countPairDirs(compareEnDir);
const esPairs = countPairDirs(compareEsDir);

if (enPairs !== esPairs) {
  console.error(
    `FAIL [CMP-03] A-vs-B symmetry: EN compare pages (${enPairs}) !== ES comparar pages (${esPairs}). ` +
    `Both [pair].astro routes must generate the same set of pair slugs.`
  );
  failures++;
} else {
  if (enPairs === 0) {
    console.log('PASS [CMP-03] A-vs-B symmetry: no compare pages yet (no enabled pairs deployed)');
  } else {
    console.log(`PASS [CMP-03] A-vs-B symmetry: ${enPairs} EN pairs === ${esPairs} ES pairs`);
  }
}

// ---------------------------------------------------------------------------
// Exit
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\navs-b-budget.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}
console.log('\navs-b-budget.mjs: PASSED');
process.exit(0);
