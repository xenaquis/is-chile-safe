// freshness.test.ts — G-05 fixtures for freshness.mjs (newest-incident evidence, 48h).
//
// freshness.mjs performs file IO and process.exit() at module-load time, so it is
// never imported directly here (same constraint documented in
// figure-registry.test.ts). Each fixture writes a current.json to a tmp dir and
// spawns `process.execPath` on freshness.mjs with FRESHNESS_CURRENT_JSON /
// FRESHNESS_NOW env injections — never the wall clock.

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FRESHNESS_SCRIPT = path.join(__dirname, 'freshness.mjs');

let tmpDir: string;

beforeEach(() => {
  tmpDir = mkdtempSync(path.join(tmpdir(), 'freshness-test-'));
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

function runFreshness(payload: object, nowIso: string) {
  const currentJsonPath = path.join(tmpDir, 'current.json');
  writeFileSync(currentJsonPath, JSON.stringify(payload), 'utf-8');
  return spawnSync(process.execPath, [FRESHNESS_SCRIPT], {
    env: {
      ...process.env,
      FRESHNESS_CURRENT_JSON: currentJsonPath,
      FRESHNESS_NOW: nowIso,
    },
    encoding: 'utf-8',
  });
}

const AS_OF = '2026-06-01T12:00:00Z';

describe('freshness.mjs — G-05 fixtures', () => {
  it('Fixture A (G-05 fixture): last_new_incident_at = as_of - 3d -> FAIL', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-05-29T12:00:00Z',
      },
      AS_OF,
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
  });

  it('Fixture B (G-05 fallback fixture): no field, max(date)=2026-05-29 (60h) -> FAIL', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [{ date: '2026-05-29' }],
      },
      AS_OF,
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
    expect(result.stderr).toContain('max(date)+1d');
  });

  it('Fixture C: last_new_incident_at = as_of - 47h -> PASS', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-05-30T13:00:00Z', // 47h before AS_OF
      },
      AS_OF,
    );
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('PASS freshness');
  });

  it('Fixture D: exactly 48h -> PASS (inclusive boundary, F-96 semantics)', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-05-30T12:00:00Z', // exactly 48h before AS_OF
      },
      AS_OF,
    );
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('PASS freshness');
  });

  it('Fixture E: 48h + 1s -> FAIL', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-05-30T11:59:59Z', // 48h + 1s before AS_OF
      },
      AS_OF,
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
  });

  it('Fixture F: evidence 25h in the future -> FAIL (F-100 parity)', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-06-02T13:00:00Z', // 25h after AS_OF
      },
      AS_OF,
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
    expect(result.stderr.toLowerCase()).toContain('future');
  });

  it('Fixture G: no field, no incidents -> FAIL', () => {
    const result = runFreshness(
      { generated: AS_OF, window_days: 30, incidents: [] },
      AS_OF,
    );
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
  });

  it('names the evidence source and age in hours on PASS', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [],
        last_new_incident_at: '2026-05-30T13:00:00Z',
      },
      AS_OF,
    );
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('last_new_incident_at');
    expect(result.stdout).toMatch(/\d+(\.\d+)?h old/);
  });

  it('names the fallback evidence source on the max(date)+1d path', () => {
    const result = runFreshness(
      {
        generated: AS_OF,
        window_days: 30,
        incidents: [{ date: '2026-05-31' }], // 1 day before AS_OF + 1d fallback = 36h old
      },
      AS_OF,
    );
    expect(result.status).toBe(0);
    expect(result.stdout).toContain('max(date)+1d');
    expect(result.stdout).toMatch(/\d+(\.\d+)?h old/);
  });

  it('missing current.json -> FAIL', () => {
    const result = spawnSync(process.execPath, [FRESHNESS_SCRIPT], {
      env: {
        ...process.env,
        FRESHNESS_CURRENT_JSON: path.join(tmpDir, 'does-not-exist.json'),
        FRESHNESS_NOW: AS_OF,
      },
      encoding: 'utf-8',
    });
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
  });

  it('unparseable FRESHNESS_NOW -> FAIL', () => {
    const currentJsonPath = path.join(tmpDir, 'current.json');
    writeFileSync(
      currentJsonPath,
      JSON.stringify({ generated: AS_OF, window_days: 30, incidents: [] }),
      'utf-8',
    );
    const result = spawnSync(process.execPath, [FRESHNESS_SCRIPT], {
      env: {
        ...process.env,
        FRESHNESS_CURRENT_JSON: currentJsonPath,
        FRESHNESS_NOW: 'not-a-timestamp',
      },
      encoding: 'utf-8',
    });
    expect(result.status).toBe(1);
    expect(result.stderr).toContain('FAIL freshness');
  });
});
