/**
 * check-iteration.mjs — the gate that makes Phase 29 capable of failing.
 *
 * The problem it solves (premortem F4): iteration 1's build instructions ARE the rubric
 * criteria, so it scores well by construction; iteration 2 then has no failing target,
 * and a cosmetic recolour with the word "CrimeMapping" typed into the delta note would
 * pass every other gate in the phase. MAPUX-02 makes the LOOP the deliverable, so the
 * loop needs an instrument that can tell a real second iteration from a restyle.
 *
 * Exits non-zero unless, for iteration N:
 *   1. every JSON blob in iter-N/SCORE.md parses and carries its provenance fields
 *   2. no blob reads NOT_MEASURED_FAIL, and every frozen STRESS.md condition appears
 *   3. (N >= 2) iter-N is structurally distinct from iter-(N-1), OR moved a cell FAIL->PASS
 *   4. (N >= 2) the delta note cites at least one literal number from iter-(N-1)'s JSON
 *
 * Real .mjs file, no regex inside a shell-quoted node -e (F-36).
 *
 * Usage: node check-iteration.mjs <N>
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const REQUIRED_FIELDS = [
  'newsToggleDiscoverable',
  'filterOverflowsContainer',
  'touchTargetViolations',
  'criterion5',
  'capturedAt',
  'pageUrl',
  'viewportWidthPx',
  'stressCondition',
];

const fail = (msg) => { console.error('FAIL: ' + msg); process.exit(1); };

/** Extract ```json fenced blocks without regex. */
export function extractJsonBlocks(md) {
  const blocks = [];
  const lines = md.split('\n');
  let inBlock = false;
  let buf = [];
  for (const line of lines) {
    const t = line.trim();
    if (!inBlock && (t === '```json' || t === '``` json')) { inBlock = true; buf = []; continue; }
    if (inBlock && t === '```') { blocks.push(buf.join('\n')); inBlock = false; continue; }
    if (inBlock) buf.push(line);
  }
  return blocks;
}

/** Every integer/float literal appearing in a string, as strings. */
function numericLiterals(s) {
  const out = new Set();
  let cur = '';
  for (let i = 0; i <= s.length; i++) {
    const c = s[i];
    if (c >= '0' && c <= '9') { cur += c; continue; }
    if (c === '.' && cur.length) { cur += c; continue; }
    if (cur.length) { if (cur.length >= 2) out.add(cur.replace(/\.$/, '')); cur = ''; }
  }
  return out;
}

const n = Number(process.argv[2]);
if (!Number.isInteger(n) || n < 1) fail('usage: node check-iteration.mjs <iteration-number>');

const dir = join(ROOT, 'iter-' + n);
const scorePath = join(dir, 'SCORE.md');
if (!existsSync(scorePath)) fail('missing ' + scorePath);
const md = readFileSync(scorePath, 'utf8');

// --- 1. blobs parse and carry provenance ------------------------------------------
const blocks = extractJsonBlocks(md);
if (blocks.length === 0) fail('iter-' + n + '/SCORE.md contains no ```json blocks — scores must be raw evaluate_script output, not prose');

const blobs = [];
blocks.forEach((b, i) => {
  let parsed;
  try { parsed = JSON.parse(b); } catch (e) { fail('JSON block #' + (i + 1) + ' does not parse: ' + e.message); }
  for (const f of REQUIRED_FIELDS) {
    if (!(f in parsed)) fail('JSON block #' + (i + 1) + ' (' + (parsed.stressCondition || '?') + ') missing required field: ' + f);
  }
  blobs.push(parsed);
});

// --- 2. nothing unmeasured, every frozen condition present -------------------------
const unmeasured = blobs.filter((b) => b.criterion5 === 'NOT_MEASURED_FAIL');
if (unmeasured.length) {
  fail(unmeasured.length + ' blob(s) report criterion5=NOT_MEASURED_FAIL (conditions: ' +
       unmeasured.map((b) => b.stressCondition).join(', ') +
       '). A sketch with no Leaflet stand-in is not a scored iteration.');
}

const stressPath = join(ROOT, 'STRESS.md');
if (!existsSync(stressPath)) fail('missing STRESS.md — the frozen conditions must exist before any iteration is scored');
const stress = readFileSync(stressPath, 'utf8');
const declared = [];
for (const line of stress.split('\n')) {
  const t = line.trim();
  if (t.startsWith('- id:')) declared.push(t.slice(5).trim());
}
if (declared.length === 0) fail('STRESS.md declares no `- id:` conditions');
const seen = new Set(blobs.map((b) => b.stressCondition));
const missing = declared.filter((d) => !seen.has(d));
if (missing.length) fail('iteration ' + n + ' was not scored under: ' + missing.join(', '));

// --- 3 & 4. distinctness from the previous iteration -------------------------------
if (n >= 2) {
  const prevDir = join(ROOT, 'iter-' + (n - 1));
  const prevScorePath = join(prevDir, 'SCORE.md');
  if (!existsSync(prevScorePath)) fail('missing ' + prevScorePath + ' — cannot prove iteration ' + n + ' is distinct');
  const prevMd = readFileSync(prevScorePath, 'utf8');
  const prevBlobs = extractJsonBlocks(prevMd).map((b) => JSON.parse(b));

  const countEntryPoints = (p) => {
    if (!existsSync(p)) fail('missing ' + p);
    const html = readFileSync(p, 'utf8');
    return html.split('data-role="entry-point"').length - 1;
  };
  const curEP = countEntryPoints(join(dir, 'desktop.html'));
  const prevEP = countEntryPoints(join(prevDir, 'desktop.html'));

  const cellKey = (b) => b.stressCondition + '@' + b.viewportWidthPx;
  const prevCells = new Map(prevBlobs.map((b) => [cellKey(b), b]));
  let improved = false;
  for (const b of blobs) {
    const p = prevCells.get(cellKey(b));
    if (!p) continue;
    for (const c of ['criterion1', 'criterion2', 'criterion3', 'criterion4', 'criterion5']) {
      if (p[c] === 'FAIL' && b[c] === 'PASS') improved = true;
    }
  }

  if (curEP === prevEP && !improved) {
    fail('ITERATION ' + n + ' IS NOT A DISTINCT ITERATION — same entry-point count (' + curEP +
         ') as iteration ' + (n - 1) + ' and no criterion moved FAIL->PASS. ' +
         'A restyle is not an iteration (MAPUX-02).');
  }

  const prevNums = numericLiterals(JSON.stringify(prevBlobs));
  const curText = numericLiterals(md);
  let cited = false;
  for (const v of curText) { if (prevNums.has(v)) { cited = true; break; } }
  if (!cited) {
    fail('iter-' + n + '/SCORE.md cites no literal numeric value from iteration ' + (n - 1) +
         ' — the delta note must compare against the prior scores, not paraphrase them.');
  }
}

console.log('iteration ' + n + ' OK: ' + blobs.length + ' scored cells across ' + seen.size +
            ' condition(s)' + (n >= 2 ? ', proven distinct from iteration ' + (n - 1) : ''));
