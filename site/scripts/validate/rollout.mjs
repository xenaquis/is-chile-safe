/**
 * rollout.mjs — Validate rollout gate output in dist/.
 *
 * Asserts:
 *   (a) dist/commune count === dist/es/comuna count === rollout.json enabled length
 *   (b) Every EN commune slug has a matching ES slug and vice versa (reciprocity)
 *   (c) Presence of rollout.json enabled list (config validation)
 *   (d) In EXPECT_ALL=true mode, asserts 346 per locale
 *
 * Does NOT rebuild — inspect existing dist/ output only.
 * Exit non-zero on any mismatch.
 *
 * Usage:
 *   node scripts/validate/rollout.mjs            # default build (12 communes)
 *   EXPECT_ALL=true node scripts/validate/rollout.mjs  # full rollout (346)
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

// --- Load rollout config ---
assert.ok(existsSync(ROLLOUT_PATH), `rollout.json not found at ${ROLLOUT_PATH}`);
const rollout = JSON.parse(readFileSync(ROLLOUT_PATH, 'utf-8'));
assert.ok(Array.isArray(rollout.enabled), 'rollout.json must have an "enabled" array');
assert.strictEqual(rollout.enabled.length, 12, `rollout.json must have exactly 12 CUT codes (got ${rollout.enabled.length})`);
assert.ok(rollout.enabled.includes('13101'), 'rollout.json must include Santiago (13101)');
assert.ok(rollout.enabled.includes('13119'), 'rollout.json must include Maipú (13119)');
console.log(`rollout.json: ${rollout.enabled.length} enabled communes (config OK)`);

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

// Determine expected count
const expectAll = process.env.EXPECT_ALL === 'true';
const expectedCount = expectAll ? 346 : rollout.enabled.length;

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
if (expectAll) {
  console.log(`  EXPECT_ALL mode: 346 communes per locale asserted`);
} else {
  console.log(`  Default rollout mode: ${rollout.enabled.length} communes per locale`);
}
