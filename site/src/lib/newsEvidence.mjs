/**
 * newsEvidence.mjs — the single JS definition of the G-05 newest-incident
 * evidence rule (G-05, G-07(a)).
 *
 * Evidence is `last_new_incident_at` when present and parseable, else
 * `max(incident.date) + 1 day`. A build/page/validator is "fresh" when that
 * evidence is no more than `maxAgeHours` old (default 48h, MAX_AGE_HOURS),
 * "future" when it is more than 24h ahead of the as-of clock
 * (FUTURE_ALLOWANCE_HOURS), and "none" when there is no evidence at all.
 *
 * This module is pure ESM: no `fs`, no `process`, no wall-clock reads. Every
 * caller passes `nowMs` explicitly, so behaviour is fully deterministic and
 * testable without env injection.
 *
 * IMPORTANT: pipeline/news_evidence.py is a Python twin of this rule (used by
 * the stdlib-only heartbeat, heartbeat.yml). Any change to the G-05 semantics
 * here (the 48h/24h/168h thresholds, the fallback formula, the future-refusal
 * rule) MUST be mirrored in news_evidence.py, and the shared fixtures A-G
 * (freshness.test.ts here, TestNewsHeartbeatG05 in
 * pipeline/tests/test_workflow_guards.py) must stay green on both sides.
 */

/** @typedef {import('./newsEvidence.d.mts').Evidence} Evidence */
/** @typedef {import('./newsEvidence.d.mts').Verdict} Verdict */

export const MAX_AGE_HOURS = 48;
export const FUTURE_ALLOWANCE_HOURS = 24;
export const COMMUNE_NEWS_STALE_HOURS = 168;

const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;
const CANONICAL_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * latestIncidentDate — the max of `payload.incidents[].date`, counting only
 * strings that match the canonical YYYY-MM-DD shape and parse as a valid UTC
 * date. Returns null when `incidents` is missing, not an array, or has no
 * valid dates.
 *
 * @param {{ incidents?: unknown }} payload
 * @returns {string | null}
 */
export function latestIncidentDate(payload) {
  const incidents = Array.isArray(payload?.incidents) ? payload.incidents : [];
  let maxDate = null;
  for (const inc of incidents) {
    if (!inc || typeof inc.date !== 'string') continue;
    if (!CANONICAL_DATE_RE.test(inc.date)) continue;
    if (Number.isNaN(Date.parse(`${inc.date}T00:00:00Z`))) continue;
    if (maxDate === null || inc.date > maxDate) maxDate = inc.date;
  }
  return maxDate;
}

/**
 * computeEvidence — the G-05 rule. `last_new_incident_at` wins when it is a
 * non-blank, parseable string; otherwise falls back to
 * `latestIncidentDate(payload) + 1 day`. Returns null when there is no usable
 * evidence at all.
 *
 * @param {{ last_new_incident_at?: unknown, incidents?: unknown }} payload
 * @returns {Evidence | null}
 */
export function computeEvidence(payload) {
  const lastNew = payload?.last_new_incident_at;
  if (typeof lastNew === 'string' && lastNew.trim() !== '') {
    const ms = Date.parse(lastNew);
    if (!Number.isNaN(ms)) {
      return { ms, source: 'last_new_incident_at', label: lastNew };
    }
  }

  const maxDate = latestIncidentDate(payload);
  if (maxDate === null) return null;

  const maxMs = Date.parse(`${maxDate}T00:00:00Z`);
  const fallbackMs = maxMs + DAY_MS;
  const label = new Date(fallbackMs).toISOString().replace(/\.\d{3}Z$/, 'Z');
  return { ms: fallbackMs, source: 'max(date)+1d', label };
}

/**
 * evidenceVerdict — classify evidence relative to `nowMs`.
 * - 'none'   evidence is null
 * - 'future' evidence.ms is more than FUTURE_ALLOWANCE_HOURS ahead of nowMs
 * - 'stale'  evidence age exceeds maxAgeHours
 * - 'fresh'  otherwise (inclusive at the maxAgeHours boundary)
 *
 * @param {Evidence | null} evidence
 * @param {number} nowMs
 * @param {number} [maxAgeHours]
 * @returns {Verdict}
 */
export function evidenceVerdict(evidence, nowMs, maxAgeHours = MAX_AGE_HOURS) {
  if (evidence === null) return 'none';

  const futureAllowanceMs = FUTURE_ALLOWANCE_HOURS * HOUR_MS;
  if (evidence.ms > nowMs + futureAllowanceMs) return 'future';

  const ageHours = (nowMs - evidence.ms) / HOUR_MS;
  if (ageHours > maxAgeHours) return 'stale';

  return 'fresh';
}
