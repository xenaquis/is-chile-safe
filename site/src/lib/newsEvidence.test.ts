// newsEvidence.test.ts — shared G-05 evidence-rule fixtures (JS side).
//
// This is the single JS definition of the G-05 rule (last_new_incident_at,
// else max(date)+1d; 48h stale; 24h future refusal). freshness.mjs consumes
// it directly; the Python twin (pipeline/news_evidence.py) is pinned by the
// shared fixtures A-G here and in freshness.test.ts / test_workflow_guards.py.

import { describe, it, expect } from 'vitest';
import {
  latestIncidentDate,
  computeEvidence,
  evidenceVerdict,
  MAX_AGE_HOURS,
  FUTURE_ALLOWANCE_HOURS,
  COMMUNE_NEWS_STALE_HOURS,
} from './newsEvidence.mjs';

describe('latestIncidentDate', () => {
  it('returns the max of valid canonical dates', () => {
    expect(
      latestIncidentDate({
        incidents: [{ date: '2026-09-03' }, { date: '2026-09-04' }, { date: 'bad' }, {}],
      })
    ).toBe('2026-09-04');
  });

  it('returns null when there are no valid dates', () => {
    expect(latestIncidentDate({ incidents: [] })).toBeNull();
    expect(latestIncidentDate({ incidents: [{ date: 'bad' }, {}] })).toBeNull();
  });

  it('returns null when incidents is not an array', () => {
    expect(latestIncidentDate({})).toBeNull();
    expect(latestIncidentDate({ incidents: null })).toBeNull();
  });
});

describe('computeEvidence', () => {
  it('prefers last_new_incident_at when present and parseable', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-05-29T12:00:00Z', incidents: [] });
    expect(ev?.source).toBe('last_new_incident_at');
    expect(ev?.label).toBe('2026-05-29T12:00:00Z');
  });

  it('falls through to the date fallback when last_new_incident_at is unparseable or blank', () => {
    const evUnparseable = computeEvidence({
      last_new_incident_at: 'not-a-date',
      incidents: [{ date: '2026-05-29' }],
    });
    expect(evUnparseable?.source).toBe('max(date)+1d');

    const evBlank = computeEvidence({
      last_new_incident_at: '  ',
      incidents: [{ date: '2026-05-29' }],
    });
    expect(evBlank?.source).toBe('max(date)+1d');
  });

  it('computes max(date)+1d fallback with the canonical label format', () => {
    const ev = computeEvidence({ incidents: [{ date: '2026-05-29' }] });
    expect(ev?.source).toBe('max(date)+1d');
    expect(ev?.label).toBe('2026-05-30T00:00:00Z');
  });

  it('returns null when there is no evidence at all', () => {
    expect(computeEvidence({ incidents: [] })).toBeNull();
  });
});

describe('evidenceVerdict', () => {
  const AS_OF = Date.parse('2026-06-01T12:00:00Z');

  it('returns none when evidence is null', () => {
    expect(evidenceVerdict(null, AS_OF)).toBe('none');
  });

  it('returns fresh at 47h old', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-05-30T13:00:00Z', incidents: [] });
    expect(evidenceVerdict(ev, AS_OF)).toBe('fresh');
  });

  it('returns fresh at exactly 48h old (inclusive boundary)', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-05-30T12:00:00Z', incidents: [] });
    expect(evidenceVerdict(ev, AS_OF)).toBe('fresh');
  });

  it('returns stale at 48h + 1s old', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-05-30T11:59:59Z', incidents: [] });
    expect(evidenceVerdict(ev, AS_OF)).toBe('stale');
  });

  it('returns future at 25h in the future', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-06-02T13:00:00Z', incidents: [] });
    expect(evidenceVerdict(ev, AS_OF)).toBe('future');
  });

  it('returns fresh at 23h in the future', () => {
    const ev = computeEvidence({ last_new_incident_at: '2026-06-02T11:00:00Z', incidents: [] });
    expect(evidenceVerdict(ev, AS_OF)).toBe('fresh');
  });

  it('applies a custom maxAgeHours for the commune-news caveat (168h)', () => {
    const ev = computeEvidence({ incidents: [{ date: '2026-09-15' }] }); // label 2026-09-16T00:00:00Z
    const now168 = Date.parse('2026-09-23T00:00:00Z'); // exactly 168h after evidence
    expect(evidenceVerdict(ev, now168, COMMUNE_NEWS_STALE_HOURS)).toBe('fresh');

    const now168plus1s = Date.parse('2026-09-23T00:00:01Z');
    expect(evidenceVerdict(ev, now168plus1s, COMMUNE_NEWS_STALE_HOURS)).toBe('stale');
  });

  it('Sep-4-frozen payload is stale at now 2026-09-23T12:00:00Z with no last_new_incident_at', () => {
    const payload = {
      generated: '2026-09-23T03:37:54.191098Z',
      incidents: [{ date: '2026-09-04' }],
    };
    const ev = computeEvidence(payload);
    const now = Date.parse('2026-09-23T12:00:00Z');
    expect(evidenceVerdict(ev, now)).toBe('stale');
  });

  it('the same frozen payload is fresh once last_new_incident_at is populated', () => {
    const payload = {
      generated: '2026-09-23T03:37:54.191098Z',
      incidents: [{ date: '2026-09-04' }],
      last_new_incident_at: '2026-09-23T11:00:00Z',
    };
    const ev = computeEvidence(payload);
    const now = Date.parse('2026-09-23T12:00:00Z');
    expect(evidenceVerdict(ev, now)).toBe('fresh');
  });
});

describe('constants', () => {
  it('exports the G-05 / FRESH-01 / FRESH-03 constants', () => {
    expect(MAX_AGE_HOURS).toBe(48);
    expect(FUTURE_ALLOWANCE_HOURS).toBe(24);
    expect(COMMUNE_NEWS_STALE_HOURS).toBe(168);
  });
});
