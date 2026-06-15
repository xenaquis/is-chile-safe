/**
 * rollout.mjs — Validate rollout gate output in dist/.
 *
 * Asserts:
 *   (a) dist/commune count === dist/es/comuna count === index length (346 by default)
 *   (b) Every EN commune slug has a matching ES slug and vice versa (reciprocity)
 *   (c) Presence of rollout.json enabled list (config sanity: Santiago + Maipú present,
 *       count is between 1 and 346 — rollout.json is vestigial when ROLLOUT_ALL=true)
 *
 * Expected count (defaultCount):
 *   Derived from data/cead/meta/index.json length (346). This is the committed default
 *   so that a standard `node scripts/validate/rollout.mjs` after a ROLLOUT_ALL build
 *   passes without needing EXPECT_ALL. The EXPECT_ALL env var is accepted as an alias
 *   (also resolves to index length) but is no longer required to assert 346.
 *
 * Does NOT rebuild — inspect existing dist/ output only.
 * Exit non-zero on any mismatch.
 *
 * Usage:
 *   node scripts/validate/rollout.mjs            # default: expects index.length (346) per locale
 *   EXPECT_ALL=true node scripts/validate/rollout.mjs  # alias — same expectation
 */

import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');
const ROLLOUT_PATH = path.join(SITE_ROOT, 'src', 'config', 'rollout.json');

// --- Load rollout config (config sanity only — not used for expectedCount) ---
assert.ok(existsSync(ROLLOUT_PATH), `rollout.json not found at ${ROLLOUT_PATH}`);
const rollout = JSON.parse(readFileSync(ROLLOUT_PATH, 'utf-8'));
assert.ok(Array.isArray(rollout.enabled), 'rollout.json must have an "enabled" array');
// Relaxed: rollout.json is vestigial under ROLLOUT_ALL; allow any count 1–346
assert.ok(
  rollout.enabled.length >= 1 && rollout.enabled.length <= 346,
  `rollout.json enabled count must be between 1 and 346 (got ${rollout.enabled.length})`
);
assert.ok(rollout.enabled.includes('13101'), 'rollout.json must include Santiago (13101)');
assert.ok(rollout.enabled.includes('13119'), 'rollout.json must include Maipú (13119)');
console.log(`rollout.json: ${rollout.enabled.length} enabled communes (config OK)`);

// --- Determine expected count from index.json (canonical source of truth) ---
const INDEX_PATH = path.resolve(SITE_ROOT, '..', 'data', 'cead', 'meta', 'index.json');
assert.ok(existsSync(INDEX_PATH), `index.json not found at ${INDEX_PATH}`);
const indexData = JSON.parse(readFileSync(INDEX_PATH, 'utf-8'));
// Both default and EXPECT_ALL=true resolve to index length (346).
// EXPECT_ALL is accepted as an alias but the committed default already expects 346.
const expectedCount = indexData.length;

// --- Check dist exists ---
const enDir = path.join(DIST_DIR, 'commune');
const esDir = path.join(DIST_DIR, 'es', 'comuna');

if (!existsSync(enDir)) {
  console.error(`FAIL: dist/commune not found — run npm run build first`);
  process.exit(1);
}
if (!existsSync(esDir)) {
  console.error(`FAIL: dist/es/comuna not found — run npm run build first`);
  process.exit(1);
}

// --- Count commune directories ---
const enSlugs = readdirSync(enDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

const esSlugs = readdirSync(esDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name);

console.log(`dist/commune:   ${enSlugs.length} dirs`);
console.log(`dist/es/comuna: ${esSlugs.length} dirs`);

let failures = 0;

// (a) Count assertions
if (enSlugs.length !== expectedCount) {
  console.error(`FAIL: dist/commune has ${enSlugs.length} dirs, expected ${expectedCount}`);
  failures++;
}

if (esSlugs.length !== expectedCount) {
  console.error(`FAIL: dist/es/comuna has ${esSlugs.length} dirs, expected ${expectedCount}`);
  failures++;
}

if (enSlugs.length !== esSlugs.length) {
  console.error(`FAIL: EN (${enSlugs.length}) and ES (${esSlugs.length}) commune counts do not match — hreflang parity broken`);
  failures++;
}

// (b) Reciprocity: every EN slug must have an ES counterpart and vice versa
const enSet = new Set(enSlugs);
const esSet = new Set(esSlugs);

for (const slug of enSlugs) {
  if (!esSet.has(slug)) {
    console.error(`FAIL: EN commune "${slug}" has no matching ES partner at dist/es/comuna/${slug}/`);
    failures++;
  }
}

for (const slug of esSlugs) {
  if (!enSet.has(slug)) {
    console.error(`FAIL: ES commune "${slug}" has no matching EN partner at dist/commune/${slug}/`);
    failures++;
  }
}

// --- Summary ---
if (failures > 0) {
  console.error(`\nrollout.mjs: FAILED (${failures} failure(s))`);
  process.exit(1);
}

console.log(`\nrollout.mjs: PASSED`);
console.log(`  ${enSlugs.length} EN commune pages + ${esSlugs.length} ES commune pages`);
console.log(`  EN/ES parity: OK (all slugs reciprocal)`);
console.log(`  Default rollout mode: ${expectedCount} communes per locale (index length)`);
