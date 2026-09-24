/**
 * newsEvidence.d.mts — strict TS types for newsEvidence.mjs.
 *
 * See newsEvidence.mjs for the G-05 rule documentation (evidence source,
 * 48h/24h/168h thresholds, and the Python twin pipeline/news_evidence.py).
 */

export interface Evidence {
  ms: number;
  source: 'last_new_incident_at' | 'max(date)+1d';
  label: string;
}

export type Verdict = 'none' | 'future' | 'stale' | 'fresh';

export interface EvidencePayload {
  last_new_incident_at?: unknown;
  incidents?: unknown;
}

export const MAX_AGE_HOURS: number;
export const FUTURE_ALLOWANCE_HOURS: number;
export const COMMUNE_NEWS_STALE_HOURS: number;

export function latestIncidentDate(payload: EvidencePayload): string | null;
export function computeEvidence(payload: EvidencePayload): Evidence | null;
export function evidenceVerdict(
  evidence: Evidence | null,
  nowMs: number,
  maxAgeHours?: number
): Verdict;
