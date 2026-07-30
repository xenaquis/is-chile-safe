/**
 * check-spec.mjs — asserts 29-DESIGN-SPEC.md actually pins what Phase 30 needs.
 *
 * The first-draft gate for this artifact grepped for two tokens (`MAPSH-01`, `MAPSH-02`),
 * so a spec omitting MAPSH-03/05/07 would have passed. Worse, a spec with an EMPTY
 * z-index column would have passed — and an unpinned z-index column is precisely the
 * thing that sends Phase 30 back to designing.
 *
 * Real .mjs file, no regex inside a shell-quoted node -e (F-36).
 * Usage: node check-spec.mjs <spec-path> | --selftest
 */
import { readFileSync } from 'node:fs';

const REQUIRED_TOKENS = [
  'MAPSH-01', 'MAPSH-02', 'MAPSH-03', 'MAPSH-04', 'MAPSH-05', 'MAPSH-06', 'MAPSH-07',
  'iter-1', 'iter-2', '507', '991',
  'showModal', ':modal',
  'data-role="news-toggle"', 'data-role="entry-point"', 'data-role="filter-entry"',
  'aria-expanded', 'aria-live', 'aria-pressed',
  '480', '640',
  'parseFilterParams',   // the Phase 28 N1 trap must be named
  'F-43', 'F-40',        // full-bleed out of scope; the driving warning
];

const REQUIRED_SECTIONS = [
  'z-index',
  'breakpoint',
  'Element semantics',
  'Focus order',
  'Labels',
  'data-role',
  'decision table',
  'non-decisions',
  'reproduce',
];

/** The z-index table must carry NUMBERS, not prose. */
function zIndexTableHasNumbers(text) {
  const lines = text.split('\n');
  let hits = 0;
  for (const line of lines) {
    if (line.indexOf('|') === -1) continue;
    const l = line.toLowerCase();
    if (l.indexOf('news-toggle') === -1 && l.indexOf('map-topbar') === -1 && l.indexOf('fab') === -1) continue;
    // a bare "800" / "801" cell somewhere on the row
    for (const n of ['800', '801']) {
      if (line.indexOf(n) !== -1) { hits++; break; }
    }
  }
  return hits >= 3;
}

function check(text) {
  const problems = [];
  for (const t of REQUIRED_TOKENS) {
    if (text.indexOf(t) === -1) problems.push('missing required token: ' + t);
  }
  const lower = text.toLowerCase();
  for (const s of REQUIRED_SECTIONS) {
    if (lower.indexOf(s.toLowerCase()) === -1) problems.push('missing required section: ' + s);
  }
  if (!zIndexTableHasNumbers(text)) {
    problems.push('z-index table carries no numeric values for the named controls — Phase 30 would have to decide them');
  }
  return problems;
}

if (process.argv[2] === '--selftest') {
  const good = readFileSync(new URL('../../phases/29-map-ux-design-loop/29-DESIGN-SPEC.md', import.meta.url), 'utf8');
  const cases = [
    [good, 0, 'the real spec passes'],
    [good.split('\n').filter((l) => l.indexOf('MAPSH-07') === -1).join('\n'), 1, 'dropping MAPSH-07 fails'],
    // blank every z-index number -> the "cannot be empty" rule must fire
    [good.split('800').join('').split('801').join(''), 1, 'blanking the z-index column fails'],
    [good.split('parseFilterParams').join('xxx'), 1, 'dropping the ?region= trap fails'],
  ];
  let bad = 0;
  for (const [text, wantProblems, label] of cases) {
    const got = check(text).length;
    const ok = wantProblems === 0 ? got === 0 : got > 0;
    if (!ok) { console.error('SELFTEST FAIL [' + label + ']: got ' + got + ' problems'); bad++; }
  }
  if (bad) process.exit(1);
  console.log('check-spec selftest: ' + cases.length + '/' + cases.length + ' cases correct');
  process.exit(0);
}

const path = process.argv[2];
if (!path) { console.error('usage: node check-spec.mjs <spec-path> | --selftest'); process.exit(1); }

let text;
try { text = readFileSync(path, 'utf8'); }
catch (e) { console.error('FAIL: cannot read ' + path + ' (' + e.message + ')'); process.exit(1); }

const problems = check(text);
if (problems.length) {
  for (const p of problems) console.error('FAIL: ' + p);
  process.exit(1);
}
console.log('29-DESIGN-SPEC.md pins all required decisions');
