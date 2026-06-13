/**
 * structure.mjs — Validate Astro project structure and data loader.
 * Stub: exits 0. Full assertions added in plan 02-03.
 *
 * When complete this will assert:
 * - site/ directory exists with package.json, astro.config.mjs
 * - data/cead/meta/index.json is readable and has 346 entries
 * - loadIndex() parses 346 entries via fileURLToPath parent traversal
 * - All required lib/ and config/ files exist
 */
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../..');

// Minimal smoke check: critical files exist
const REQUIRED_FILES = [
  'site/package.json',
  'site/astro.config.mjs',
  'site/src/lib/data.ts',
  'site/src/lib/colorScale.ts',
  'site/src/lib/slugMaps.ts',
  'site/src/config/i18n.ts',
  'site/src/config/rollout.json',
  'data/cead/meta/index.json',
];

for (const file of REQUIRED_FILES) {
  const abs = path.join(REPO_ROOT, file);
  assert.ok(existsSync(abs), `Required file missing: ${file}`);
}

console.log('structure: smoke check passed (stub — full assertions added in plan 02-03)');
