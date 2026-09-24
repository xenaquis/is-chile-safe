/**
 * freshness.mjs — Validator #15: newest-incident evidence ≤ 48h (G-05).
 *
 * Reads data/incidents/current.json and asserts that the newest-incident
 * evidence — `last_new_incident_at` when present, else max(incident.date) + 1
 * day — is no older than 48h. This measures real news classification, not
 * file rewrites: a no-op cron run that only rewrites `generated` no longer
 * passes this check (G-05, NREC-08).
 *
 * Exit codes:
 *   0 — current.json exists, evidence is parseable, and age <= 48h (PASS)
 *   1 — file missing, evidence absent/unparseable, evidence >24h in the
 *       future, or age > 48h (FAIL)
 *
 * Test-only env injections (never used in production):
 *   FRESHNESS_CURRENT_JSON — override the current.json path
 *   FRESHNESS_NOW          — override "now" (ISO 8601); if set but
 *                            unparseable, FAIL
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
import { computeEvidence, evidenceVerdict, MAX_AGE_HOURS, FUTURE_ALLOWANCE_HOURS } from '../../src/lib/newsEvidence.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const DEFAULT_CURRENT_JSON_PATH = path.join(REPO_ROOT, 'data', 'incidents', 'current.json');
const CURRENT_JSON_PATH = process.env.FRESHNESS_CURRENT_JSON || DEFAULT_CURRENT_JSON_PATH;

// ---------------------------------------------------------------------------
// Resolve "now" (G-05: fixed, injectable as-of for tests; never the wall
// clock in the test path)
// ---------------------------------------------------------------------------
let nowMs;
if (process.env.FRESHNESS_NOW !== undefined) {
  nowMs = Date.parse(process.env.FRESHNESS_NOW);
  if (isNaN(nowMs)) {
    console.error(
      `FAIL freshness: FRESHNESS_NOW is not a valid ISO timestamp: "${process.env.FRESHNESS_NOW}"`
    );
    process.exit(1);
  }
} else {
  nowMs = Date.now();
}

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
// Parse current.json
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

// ---------------------------------------------------------------------------
// G-05 evidence: last_new_incident_at (preferred), else max(date)+1 day
// (single JS definition lives in src/lib/newsEvidence.mjs)
// ---------------------------------------------------------------------------
const evidence = computeEvidence(data);

if (evidence === null) {
  console.error(
    'FAIL freshness: current.json has no last_new_incident_at and no incidents with a parseable date'
  );
  console.error(
    'The news cron is probably down. See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Verdict (none/future/stale/fresh)
// ---------------------------------------------------------------------------
const verdict = evidenceVerdict(evidence, nowMs, MAX_AGE_HOURS);
const ageHours = (nowMs - evidence.ms) / (1000 * 60 * 60);

// ---------------------------------------------------------------------------
// Future-evidence refusal (F-100 parity with check-heartbeat.sh)
// ---------------------------------------------------------------------------
if (verdict === 'future') {
  console.error(
    `FAIL freshness: evidence (${evidence.source}: ${evidence.label}) is more than ${FUTURE_ALLOWANCE_HOURS}h in the future relative to the as-of clock — refusing to treat as healthy`
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Age check
// ---------------------------------------------------------------------------
if (verdict === 'stale') {
  console.error(
    `FAIL freshness: newest-incident evidence (${evidence.source}: ${evidence.label}) is ${ageHours.toFixed(1)}h old`
  );
  console.error(
    `Maximum allowed age is ${MAX_AGE_HOURS}h. The news cron is probably down.`
  );
  console.error(
    'See .planning/NEWS-CRON-DIAGNOSIS-260703.md'
  );
  process.exit(1);
}

console.log(
  `PASS freshness: newest-incident evidence (${evidence.source}: ${evidence.label}) is ${ageHours.toFixed(1)}h old`
);
