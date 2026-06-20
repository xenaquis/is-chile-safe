/**
 * generate-pairs.mjs — Generate same-region commune pair allowlist.
 *
 * Reads data/cead/meta/index.json, groups communes by region_id, and emits every
 * unordered pair C(n,2) within each region. Each pair is stored with sorted CUT
 * codes (cutA < cutB lexicographically) so there is exactly one canonical page per
 * pair — no A-vs-B / B-vs-A duplication (CMP-03).
 *
 * Output: data/comparator-pairs.json
 *   Array of { cutA, cutB, region_id, enabled }
 *   enabled: true for the first 20 pairs (Wave-1 staged batch per CMP-07), false otherwise.
 *
 * Hard assertion: total pair count must equal 5,031 (verified from real data in
 * 21-RESEARCH.md). Script exits 1 with a clear message if it diverges.
 *
 * Also prints projected total dist files (1,882 base + enabledPairs * 2) so the
 * operator can see budget headroom before any build.
 */

import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Script lives at scripts/ (repo root sibling), so reach data/ via __dirname
const SRC = path.resolve(__dirname, '..', 'data', 'cead', 'meta', 'index.json');
const OUT = path.resolve(__dirname, '..', 'data', 'comparator-pairs.json');

// ---------------------------------------------------------------------------
// Defensive exit if source is missing
// ---------------------------------------------------------------------------
if (!existsSync(SRC)) {
  console.error(`[generate-pairs] FATAL: index.json not found at ${SRC}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Read and group communes by region_id
// ---------------------------------------------------------------------------
const index = JSON.parse(readFileSync(SRC, 'utf-8'));

/** @type {Map<string, Array<{cut: string, name: string, region_id: string}>>} */
const byRegion = new Map();
for (const entry of index) {
  const { cut, region_id } = entry;
  if (!byRegion.has(region_id)) byRegion.set(region_id, []);
  byRegion.get(region_id).push({ cut, region_id });
}

// ---------------------------------------------------------------------------
// Generate all unordered same-region pairs
// ---------------------------------------------------------------------------
/** @type {Array<{cutA: string, cutB: string, region_id: string, enabled: boolean}>} */
const pairs = [];

for (const [region_id, communes] of byRegion.entries()) {
  for (let i = 0; i < communes.length; i++) {
    for (let j = i + 1; j < communes.length; j++) {
      // Sort CUT codes lexicographically — guarantees canonical cutA < cutB ordering
      const [cutA, cutB] = [communes[i].cut, communes[j].cut].sort();
      pairs.push({ cutA, cutB, region_id, enabled: false });
    }
  }
}

// ---------------------------------------------------------------------------
// Validate total pair count (hard assertion vs. 21-RESEARCH.md verified universe)
// ---------------------------------------------------------------------------
const EXPECTED_PAIRS = 5031;
if (pairs.length !== EXPECTED_PAIRS) {
  console.error(
    `[generate-pairs] FATAL: expected ${EXPECTED_PAIRS} same-region pairs but computed ${pairs.length}. ` +
    `Check that data/cead/meta/index.json has exactly 346 entries and the region_id distribution matches 21-RESEARCH.md.`
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Set enabled: true for the first WAVE_SIZE pairs (CMP-07 staged rollout)
// ---------------------------------------------------------------------------
const WAVE_SIZE = 20;
for (let i = 0; i < WAVE_SIZE && i < pairs.length; i++) {
  pairs[i].enabled = true;
}

// ---------------------------------------------------------------------------
// Write output
// ---------------------------------------------------------------------------
writeFileSync(OUT, JSON.stringify(pairs, null, 2), 'utf-8');

// ---------------------------------------------------------------------------
// Budget report
// ---------------------------------------------------------------------------
const BASE_FILES = 1882;   // baseline dist/ files without any A-vs-B pages (from 21-RESEARCH.md)
const SAFE_BOUND = 18000;
const enabledPairs = pairs.filter(p => p.enabled).length;
const projectedFiles = BASE_FILES + enabledPairs * 2;
const fullBuildFiles = BASE_FILES + pairs.length * 2;

console.log(`[generate-pairs] wrote ${pairs.length} pairs (${enabledPairs} enabled) → ${OUT}`);
console.log(`[generate-pairs] budget projection:`);
console.log(`  Base files:            ${BASE_FILES}`);
console.log(`  Enabled pairs × 2:    ${enabledPairs * 2}  (current batch)`);
console.log(`  Full universe × 2:    ${pairs.length * 2}  (all same-region pairs)`);
console.log(`  Projected (enabled):  ${projectedFiles} files  (limit ${SAFE_BOUND}, margin ${SAFE_BOUND - projectedFiles})`);
console.log(`  Projected (full):     ${fullBuildFiles} files  (limit ${SAFE_BOUND}, margin ${SAFE_BOUND - fullBuildFiles})`);
