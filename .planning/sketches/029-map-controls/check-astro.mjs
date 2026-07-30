/**
 * check-astro.mjs — asserts `astro check` is still at its known baseline.
 *
 * Why this file exists: the phase-close gate deliberately discards astro-check's exit
 * status with a single `;` (it exits non-zero at the expected 4-error baseline, F-34).
 * That discard is only safe because THIS assertion runs downstream. A gate that keeps
 * the `;` and drops the assertion cannot tell 4 errors from 400 — which is exactly what
 * the first draft of Plan 29-02 shipped.
 *
 * String scanning, never regex: this environment corrupts backslash escapes inside a
 * shell-quoted `node -e` (F-36), so rubric/gate logic lives in real .mjs files.
 *
 * Usage:  node check-astro.mjs <path-to-astro-check-log>
 *         node check-astro.mjs --selftest
 */
import { readFileSync } from 'node:fs';

const EXPECTED_ERRORS = 4;   // ComparatorPairsLinks.astro:28, ts(7031) x4 — pre-existing
const EXPECTED_WARNINGS = 0;

/** Strip ANSI colour codes without regex: drop ESC-[ ... m sequences. */
function stripAnsi(s) {
  let out = '';
  for (let i = 0; i < s.length; i++) {
    if (s.charCodeAt(i) === 27 && s[i + 1] === '[') {
      i += 2;
      while (i < s.length && s[i] !== 'm') i++;
      continue;
    }
    out += s[i];
  }
  return out;
}

/** Find "- N errors" / "- N warnings" summary lines by string parsing. */
export function parseSummary(raw) {
  const lines = stripAnsi(raw).split('\n').map((l) => l.trim());
  let errors = null;
  let warnings = null;
  for (const line of lines) {
    if (!line.startsWith('- ')) continue;
    const rest = line.slice(2).trim();
    const sp = rest.indexOf(' ');
    if (sp < 0) continue;
    const n = Number(rest.slice(0, sp));
    const word = rest.slice(sp + 1).trim();
    if (!Number.isInteger(n)) continue;
    if (word === 'error' || word === 'errors') errors = n;
    if (word === 'warning' || word === 'warnings') warnings = n;
  }
  return { errors, warnings };
}

function check(raw) {
  const { errors, warnings } = parseSummary(raw);
  if (errors === null || warnings === null) {
    return { ok: false, msg: 'astro check summary not found (errors=' + errors + ', warnings=' + warnings + ')' };
  }
  if (errors !== EXPECTED_ERRORS || warnings !== EXPECTED_WARNINGS) {
    return {
      ok: false,
      msg: 'astro check ' + errors + ' errors / ' + warnings + ' warnings, baseline ' +
           EXPECTED_ERRORS + '/' + EXPECTED_WARNINGS,
    };
  }
  return { ok: true, msg: 'astro check ' + errors + '/' + warnings + ' baseline confirmed' };
}

const arg = process.argv[2];

if (arg === '--selftest') {
  // Falsifiability proof, run as part of the plan's own gate (operating lesson 9).
  const cases = [
    ['Result (123 files):\n- 0 errors\n- 0 warnings\n', false, 'clean tree differs from the 4-error baseline'],
    ['Result (123 files):\n- 4 errors\n- 0 warnings\n', true, 'exact baseline'],
    ['Result (123 files):\n- 40 errors\n- 0 warnings\n', false, 'regression to 40 errors'],
    ['Result (123 files):\n- 4 errors\n- 3 warnings\n', false, 'new warnings'],
    ['no summary at all\n', false, 'unparseable log fails closed'],
    ['Result:\n[31m- 4 errors[0m\n- 0 warnings\n', true, 'ANSI-coloured baseline still parses'],
  ];
  let bad = 0;
  for (const [raw, want, label] of cases) {
    const got = check(raw).ok;
    if (got !== want) {
      console.error('SELFTEST FAIL [' + label + ']: expected ok=' + want + ', got ' + got);
      bad++;
    }
  }
  if (bad) process.exit(1);
  console.log('check-astro selftest: ' + cases.length + '/' + cases.length + ' cases correct');
  process.exit(0);
}

if (!arg) {
  console.error('usage: node check-astro.mjs <log-path> | --selftest');
  process.exit(1);
}

let raw;
try {
  raw = readFileSync(arg, 'utf8');
} catch (e) {
  console.error('FAIL: cannot read astro-check log at ' + arg + ' (' + e.message + ')');
  process.exit(1);
}

const res = check(raw);
console.log((res.ok ? '' : 'FAIL: ') + res.msg);
process.exit(res.ok ? 0 : 1);
