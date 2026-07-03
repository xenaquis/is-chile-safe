/**
 * freshness.mjs — Validator #15: data/incidents/current.json freshness guard.
 *
 * Reads data/incidents/current.json and asserts that the `generated` timestamp
 * is no older than 3 days. A stale file indicates the news cron is probably down.
 *
 * Exit codes:
 *   0 — current.json exists, `generated` is parseable, and age <= 3 days (PASS)
 *   1 — file missing, `generated` absent/unparseable, or age > 3 days (FAIL)
 *
 * Usage:
 *   node scripts/validate/freshness.mjs
 *
 * Diagnosis reference (if this fails):
 *   .planning/NEWS-CRON-DIAGNOSIS-260703.md
 */

import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const CURRENT_JSON_PATH = path.join(REPO_ROOT, 'data', 'incidents', 'current.json');

const MAX_AGE_DAYS = 3;

// ---------------------------------------------------------------------------
// Guard: file must exist
// ---------------------------------------------------------------------------
if (!existsSync(CURRENT_JSON_PATH)) {
  console.error(
    `FAIL freshness: data/incidents/current.json not found at ${CURRENT_JSON_PATH}`
  );
  console.error(
    'The news cron is probably down. See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Parse and check `generated` field
// ---------------------------------------------------------------------------
let data;
try {
  data = JSON.parse(readFileSync(CURRENT_JSON_PATH, 'utf-8'));
} catch (err) {
  console.error(`FAIL freshness: could not parse current.json — ${err.message}`);
  console.error(
    'The news cron is probably down. See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

if (!data.generated || typeof data.generated !== 'string') {
  console.error(
    'FAIL freshness: current.json is missing the `generated` field or it is not a string'
  );
  console.error(
    'The news cron is probably down. See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

const generatedMs = Date.parse(data.generated);
if (isNaN(generatedMs)) {
  console.error(
    `FAIL freshness: current.json \`generated\` field is not a valid ISO timestamp: "${data.generated}"`
  );
  console.error(
    'The news cron is probably down. See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

const ageMs = Date.now() - generatedMs;
const ageDays = ageMs / (1000 * 60 * 60 * 24);

if (ageDays > MAX_AGE_DAYS) {
  console.error(
    `FAIL freshness: data/incidents/current.json is ${ageDays.toFixed(1)} days old (generated: ${data.generated})`
  );
  console.error(
    `Maximum allowed age is ${MAX_AGE_DAYS} days. The news cron is probably down.`
  );
  console.error(
    'See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

console.log(
  `PASS freshness: data/incidents/current.json is ${ageDays.toFixed(1)} days old (generated: ${data.generated})`
);
