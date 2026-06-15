/**
 * all.mjs — Aggregate validator: run all 9 validation scripts in sequence.
 *
 * Validators:
 *   1.  structure.mjs         — required source files + sample page meta
 *   2.  commune.mjs           — commune page HTML assertions
 *   3.  rollout.mjs           — rollout gate: dist commune count matches rollout.json
 *   4.  region.mjs            — region page HTML assertions
 *   5.  crime.mjs             — crime-type page HTML assertions
 *   6.  hreflang.mjs          — hreflang reciprocity + canonical + PWA meta per page
 *   7.  schema.mjs            — Schema.org JSON-LD correctness per page type
 *   8.  map.mjs               — TopoJSON budget + map pages + zero-React content-page regression guard
 *   9.  forbidden-language.mjs — EDIT-05 forbidden editorial term gate over dist/ visible text
 *  10.  coverage.mjs          — route-count + no-orphan-link + sitemap-coverage + directory-completeness
 *
 * Any non-zero exit from a child script fails the suite.
 * Prints a per-check PASS/FAIL summary at the end.
 *
 * Usage:
 *   node scripts/validate/all.mjs            # default build
 *   EXPECT_ALL=true node scripts/validate/all.mjs  # full rollout (346 communes)
 */

import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const VALIDATORS = [
  'structure.mjs',
  'commune.mjs',
  'rollout.mjs',
  'region.mjs',
  'crime.mjs',
  'hreflang.mjs',
  'schema.mjs',
  'map.mjs',
  'forbidden-language.mjs',
  'coverage.mjs',
];

const results = [];

for (const script of VALIDATORS) {
  const scriptPath = path.join(__dirname, script);
  const label = script.replace('.mjs', '');

  console.log(`\n${'─'.repeat(60)}`);
  console.log(`▶ ${label}`);
  console.log(`${'─'.repeat(60)}`);

  const result = spawnSync(process.execPath, [scriptPath], {
    stdio: 'inherit',
    env: { ...process.env },
  });

  const passed = result.status === 0;
  results.push({ label, passed });

  if (!passed) {
    // Don't abort — run all validators to show the full picture
    console.error(`\n✗ ${label}: FAILED (exit code ${result.status})`);
  } else {
    console.log(`\n✓ ${label}: PASSED`);
  }
}

// ---------------------------------------------------------------------------
// Summary table
// ---------------------------------------------------------------------------
console.log('\n');
console.log('═'.repeat(60));
console.log('VALIDATION SUITE SUMMARY');
console.log('═'.repeat(60));

const passed = results.filter(r => r.passed);
const failed = results.filter(r => !r.passed);

for (const { label, passed: ok } of results) {
  const mark = ok ? 'PASS' : 'FAIL';
  console.log(`  ${mark}  ${label}`);
}

console.log('─'.repeat(60));
console.log(`  ${passed.length}/${results.length} validators passed`);

if (failed.length > 0) {
  console.error(`\nFAILED: ${failed.map(r => r.label).join(', ')}`);
  process.exit(1);
}

console.log('\nAll validators passed.');
