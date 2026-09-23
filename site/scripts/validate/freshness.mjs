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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const DEFAULT_CURRENT_JSON_PATH = path.join(REPO_ROOT, 'data', 'incidents', 'current.json');
const CURRENT_JSON_PATH = process.env.FRESHNESS_CURRENT_JSON || DEFAULT_CURRENT_JSON_PATH;

const MAX_AGE_HOURS = 48;
const FUTURE_ALLOWANCE_HOURS = 24;

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
// ---------------------------------------------------------------------------
function computeEvidence(payload) {
  const lastNew = payload.last_new_incident_at;
  if (typeof lastNew === 'string' && lastNew.trim() !== '') {
    const ms = Date.parse(lastNew);
    if (!isNaN(ms)) {
      return { ms, source: 'last_new_incident_at', label: lastNew };
    }
  }

  const incidents = Array.isArray(payload.incidents) ? payload.incidents : [];
  let maxMs = null;
  for (const inc of incidents) {
    if (!inc || typeof inc.date !== 'string') continue;
    const ms = Date.parse(`${inc.date}T00:00:00Z`);
    if (isNaN(ms)) continue;
    if (maxMs === null || ms > maxMs) maxMs = ms;
  }
  if (maxMs === null) return null;

  const fallbackMs = maxMs + 24 * 60 * 60 * 1000;
  const label = new Date(fallbackMs).toISOString().replace(/\.\d{3}Z$/, 'Z');
  return { ms: fallbackMs, source: 'max(date)+1d', label };
}

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
// Future-evidence refusal (F-100 parity with check-heartbeat.sh)
// ---------------------------------------------------------------------------
const futureAllowanceMs = FUTURE_ALLOWANCE_HOURS * 60 * 60 * 1000;
if (evidence.ms > nowMs + futureAllowanceMs) {
  console.error(
    `FAIL freshness: evidence (${evidence.source}: ${evidence.label}) is more than ${FUTURE_ALLOWANCE_HOURS}h in the future relative to the as-of clock — refusing to treat as healthy`
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Age check
// ---------------------------------------------------------------------------
const ageMs = nowMs - evidence.ms;
const ageHours = ageMs / (1000 * 60 * 60);

if (ageHours > MAX_AGE_HOURS) {
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
