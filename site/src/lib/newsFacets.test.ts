/**
 * newsFacets.test.ts — vitest spec for computeNewsFacets() (Phase 27 Task 1).
 * 8 behavior cases (7 numbered + 4b) per 27-01-PLAN.md, plus fix-cycle-1 cases:
 * Test 9/10 (H-1 byMonth union), Test 11 (M-1 7d boundary width), and an
 * escapeForInlineScript case (H-2 XSS-breakout escaping).
 */
import { describe, it, expect, afterEach } from 'vitest';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { computeNewsFacets, escapeForInlineScript, type IncidentLike } from './newsFacets';
import type { CommuneMeta } from './data';

function makeIndex(): CommuneMeta[] {
  return [
    { cut: '13101', name: 'Santiago', slug: 'santiago', region_id: '13', population: 100, low_population: false },
    { cut: '8106', name: 'Lota', slug: 'lota', region_id: '8', population: 50, low_population: false },
  ];
}

const tmpDirs: string[] = [];
afterEach(() => {
  while (tmpDirs.length) {
    const dir = tmpDirs.pop()!;
    rmSync(dir, { recursive: true, force: true });
  }
});

function makeTmpDir(): string {
  const dir = mkdtempSync(path.join(tmpdir(), 'newsfacets-test-'));
  tmpDirs.push(dir);
  return dir;
}

describe('computeNewsFacets', () => {
  it('Test 1: empty incidents array returns all-empty facets, no throw', () => {
    const result = computeNewsFacets([], makeIndex());
    expect(result).toEqual({
      byFamily: [],
      byRegion: [],
      byWindow: { today: [], sevenDay: [], thirtyDay: [] },
      byMonth: [],
      facetKeys: [],
    });
  });

  it('Test 2: byFamily uses real data keys (robos_violentos), homicidios never appears', () => {
    const incidents: IncidentLike[] = [
      { cut: '13101', date: '2026-07-20', family: 'robos_violentos' },
      { cut: '13101', date: '2026-07-19', family: 'robos_violentos' },
      { cut: '13101', date: '2026-07-18', family: 'vif' },
    ];
    const result = computeNewsFacets(incidents, makeIndex());
    expect(result.byFamily).toEqual([
      { key: 'robos_violentos', count: 2 },
      { key: 'vif', count: 1 },
    ]);
    expect(result.byFamily.some((f) => f.key === 'homicidios')).toBe(false);
  });

  it('Test 3: cut as number and cut as string resolve to same region_id bucket', () => {
    const incidents: IncidentLike[] = [
      { cut: 13101, date: '2026-07-20', family: 'vida' },
      { cut: '13101', date: '2026-07-19', family: 'vida' },
    ];
    const result = computeNewsFacets(incidents, makeIndex());
    expect(result.byRegion).toEqual([{ regionId: '13', count: 2 }]);
  });

  it('Test 4: window boundaries (today/7d/30d) — newest date 2026-07-28', () => {
    const incidents: IncidentLike[] = [
      { cut: '13101', date: '2026-07-28', family: 'vida' },
      { cut: '13101', date: '2026-07-25', family: 'vida' },
      { cut: '13101', date: '2026-06-29', family: 'vida' },
      { cut: '13101', date: '2026-06-28', family: 'vida' },
    ];
    const result = computeNewsFacets(incidents, makeIndex());
    expect(result.byWindow.today.length).toBe(1);
    expect(result.byWindow.sevenDay.length).toBe(2);
    expect(result.byWindow.thirtyDay.length).toBe(3);
  });

  it('Test 4b: thirtyDay window is a real boundary, not a pass-through of the full array', () => {
    const incidents: IncidentLike[] = [
      { cut: '13101', date: '2026-07-28', family: 'vida' },
      { cut: '13101', date: '2026-07-25', family: 'vida' },
      { cut: '13101', date: '2026-06-29', family: 'vida' },
      { cut: '13101', date: '2026-06-28', family: 'vida' },
    ];
    const result = computeNewsFacets(incidents, makeIndex());
    expect(result.byWindow.thirtyDay.length).toBeLessThan(incidents.length);
    expect(result.byWindow.thirtyDay.length).toBe(3);
  });

  it('Test 5: byRegion sorted ascending by numeric region_id, not string sort', () => {
    const index: CommuneMeta[] = [
      { cut: '1', name: 'A', slug: 'a', region_id: '1', population: 1, low_population: false },
      { cut: '2', name: 'B', slug: 'b', region_id: '2', population: 1, low_population: false },
      { cut: '10', name: 'C', slug: 'c', region_id: '10', population: 1, low_population: false },
      { cut: '16', name: 'D', slug: 'd', region_id: '16', population: 1, low_population: false },
    ];
    const incidents: IncidentLike[] = [
      { cut: '1', date: '2026-07-01', family: 'vida' },
      { cut: '2', date: '2026-07-01', family: 'vida' },
      { cut: '10', date: '2026-07-01', family: 'vida' },
      { cut: '16', date: '2026-07-01', family: 'vida' },
    ];
    const result = computeNewsFacets(incidents, index);
    expect(result.byRegion.map((r) => r.regionId)).toEqual(['1', '2', '10', '16']);
  });

  it('Test 6: missing archive month file does not throw, byMonth includes only existing/parseable files', () => {
    const archiveDir = makeTmpDir();
    writeFileSync(
      path.join(archiveDir, '2026-07.json'),
      JSON.stringify({ generated: '2026-07-30T00:00:00Z', window_days: 30, incidents: [{ id: 'a' }] })
    );
    // No 2026-06.json present — must not throw
    expect(() => computeNewsFacets([], makeIndex(), archiveDir)).not.toThrow();
    const result = computeNewsFacets([], makeIndex(), archiveDir);
    expect(result.byMonth).toEqual([{ yearMonth: '2026-07', count: 1, source: 'archive' }]);
  });

  it('Test 7: byMonth is the union of archive months and current incident months, tagged by source', () => {
    const archiveDir = makeTmpDir();
    writeFileSync(
      path.join(archiveDir, '2026-06.json'),
      JSON.stringify({
        generated: '2026-07-01T00:00:00Z',
        window_days: 30,
        incidents: [{ id: 'a' }, { id: 'b' }],
      })
    );
    const incidents: IncidentLike[] = [{ cut: '13101', date: '2026-07-15', family: 'vida' }];
    const result = computeNewsFacets(incidents, makeIndex(), archiveDir);
    expect(result.byMonth).toEqual(
      expect.arrayContaining([
        { yearMonth: '2026-07', count: 1, source: 'current' },
        { yearMonth: '2026-06', count: 2, source: 'archive' },
      ])
    );
  });

  it('Test 9 (H-1): byMonth union — disjoint IDs across archive and current sum, no undercount', () => {
    const archiveDir = makeTmpDir();
    writeFileSync(
      path.join(archiveDir, '2026-06.json'),
      JSON.stringify({
        generated: '2026-06-01T00:00:00Z',
        window_days: 30,
        incidents: Array.from({ length: 84 }, (_, i) => ({ id: `archive-${i}` })),
      })
    );
    // 17 current.json June incidents whose IDs are entirely disjoint from the archive's.
    const incidents: IncidentLike[] = Array.from({ length: 17 }, (_, i) => ({
      id: `current-${i}`,
      cut: '13101',
      date: '2026-06-15',
      family: 'vida',
    }));
    const result = computeNewsFacets(incidents, makeIndex(), archiveDir);
    const june = result.byMonth.find((m) => m.yearMonth === '2026-06');
    expect(june).toEqual({ yearMonth: '2026-06', count: 101, source: 'both', currentCount: 17 });
  });

  it('Test 10 (H-1): byMonth union — overlapping IDs are de-duplicated, not double-counted', () => {
    const archiveDir = makeTmpDir();
    writeFileSync(
      path.join(archiveDir, '2026-06.json'),
      JSON.stringify({
        generated: '2026-06-01T00:00:00Z',
        window_days: 30,
        incidents: [{ id: 'shared-1' }, { id: 'shared-2' }, { id: 'archive-only' }],
      })
    );
    // 2 of the 3 current.json incidents share an ID with the archive; 1 is new.
    const incidents: IncidentLike[] = [
      { id: 'shared-1', cut: '13101', date: '2026-06-10', family: 'vida' },
      { id: 'shared-2', cut: '13101', date: '2026-06-11', family: 'vida' },
      { id: 'current-only', cut: '13101', date: '2026-06-12', family: 'vida' },
    ];
    const result = computeNewsFacets(incidents, makeIndex(), archiveDir);
    const june = result.byMonth.find((m) => m.yearMonth === '2026-06');
    // Union = {shared-1, shared-2, archive-only, current-only} = 4, strictly less
    // than the naive sum (3 archive + 3 current = 6).
    expect(june).toEqual({ yearMonth: '2026-06', count: 4, source: 'both', currentCount: 3 });
    expect(june!.count).toBeLessThan(3 + 3);
  });

  it('Test 11 (M-1): 7d window spans exactly 7 distinct dates, boundary-exclusive on day 8', () => {
    // Newest date 2026-07-28. 7d window = [2026-07-22 .. 2026-07-28] inclusive = 7 dates.
    // One incident on 2026-07-21 (8 days back) must be excluded.
    const incidents: IncidentLike[] = [
      { cut: '13101', date: '2026-07-28', family: 'vida' },
      { cut: '13101', date: '2026-07-27', family: 'vida' },
      { cut: '13101', date: '2026-07-26', family: 'vida' },
      { cut: '13101', date: '2026-07-25', family: 'vida' },
      { cut: '13101', date: '2026-07-24', family: 'vida' },
      { cut: '13101', date: '2026-07-23', family: 'vida' },
      { cut: '13101', date: '2026-07-22', family: 'vida' },
      { cut: '13101', date: '2026-07-21', family: 'vida' }, // 8 days back — must be excluded
    ];
    const result = computeNewsFacets(incidents, makeIndex());
    const distinctDates = new Set(result.byWindow.sevenDay.map((i) => i.date));
    expect(distinctDates.size).toBe(7);
    expect(distinctDates.has('2026-07-21')).toBe(false);
    expect(result.byWindow.sevenDay.length).toBe(7);
  });

  it('H-2: escapeForInlineScript neutralizes </script> while staying valid, round-tripping JSON', () => {
    const poisoned = { byFamily: [{ key: 'x</script><script>alert(1)</script>', count: 1 }] };
    const raw = JSON.stringify(poisoned);
    expect(raw).toContain('</script');
    const escaped = escapeForInlineScript(raw);
    expect(escaped).not.toContain('</script');
    expect(escaped.toLowerCase()).not.toContain('</script');
    expect(JSON.parse(escaped)).toEqual(poisoned);
  });

  it('Test 8: window computation produces identical bucket sizes under TZ=UTC and TZ=America/Santiago', () => {
    const incidents: IncidentLike[] = [
      { cut: '13101', date: '2026-07-28', family: 'vida' },
      { cut: '13101', date: '2026-07-25', family: 'vida' },
      { cut: '13101', date: '2026-06-29', family: 'vida' },
      { cut: '13101', date: '2026-06-28', family: 'vida' },
    ];
    const originalTz = process.env.TZ;
    try {
      process.env.TZ = 'UTC';
      const utcResult = computeNewsFacets(incidents, makeIndex());
      process.env.TZ = 'America/Santiago';
      const clResult = computeNewsFacets(incidents, makeIndex());

      expect(utcResult.byWindow.today.length).toBe(clResult.byWindow.today.length);
      expect(utcResult.byWindow.sevenDay.length).toBe(clResult.byWindow.sevenDay.length);
      expect(utcResult.byWindow.thirtyDay.length).toBe(clResult.byWindow.thirtyDay.length);
    } finally {
      process.env.TZ = originalTz;
    }
  });
});
