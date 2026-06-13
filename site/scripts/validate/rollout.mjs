/**
 * rollout.mjs — Validate rollout gate behavior.
 * Stub: exits 0. Full assertions added in plan 02-03.
 *
 * When complete this will assert:
 * - Default build produces exactly 12 commune pages × 2 locales = 24
 * - ROLLOUT_ALL=true produces 346 × 2 = 692 commune pages
 * - rollout.json has exactly 12 CUT codes including 13101 and 13119
 * - Enabled CUT codes match D-25 priority list
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROLLOUT_PATH = path.resolve(__dirname, '../../src/config/rollout.json');

const rollout = JSON.parse(readFileSync(ROLLOUT_PATH, 'utf-8'));

assert.ok(Array.isArray(rollout.enabled), 'rollout.json must have an "enabled" array');
assert.strictEqual(rollout.enabled.length, 12, 'rollout.json must have exactly 12 CUT codes');
assert.ok(rollout.enabled.includes('13101'), 'rollout.json must include Santiago (13101)');
assert.ok(rollout.enabled.includes('13119'), 'rollout.json must include Maipú (13119)');

console.log('rollout: config validated (12 CUT codes, 13101 + 13119 present) — stub (build count assertions added in plan 02-03)');
