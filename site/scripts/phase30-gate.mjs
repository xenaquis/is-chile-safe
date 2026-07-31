/**
 * phase30-gate.mjs — Phase 30 non-browser phase-close gate.
 *
 * Assertions (each independently reported PASS/FAIL):
 *   1. astro-check baseline: assert on the SET of file:line error locations
 *      (not the count). Baseline = all errors in ComparatorPairsLinks.astro:28.
 *   2. git diff --exit-code <PHASE30_BASE_SHA> -- the 3 protected Leaflet files
 *      + score.mjs (anchored to the pre-phase SHA, never the working tree).
 *   3. git diff --exit-code <PHASE30_BASE_SHA> -- package.json/package-lock.json
 *      (zero new dependencies), same pre-phase-SHA rule.
 *   4. dist/es/mapa/index.html, dist/map/index.html (if present) and every
 *      dist/_astro/* file must NOT contain "filters-row" or "ev-chip".
 *   5. At least one dist/_astro/*.js file must contain "showModal(".
 *   6. Every dist/_astro/*.css file, whitespace-stripped, must contain
 *      z-index:750, z-index:800 and z-index:801 at least once, and must NOT
 *      contain ".legend{...z-index:700".
 *   7. Every .tsx/.ts under site/src/components/map/ must be free of
 *      <GeoJSON, <Marker, from 'react-leaflet', from "react-leaflet".
 *
 * Does NOT invoke the build itself — run `npm run build` first.
 *
 * Usage:
 *   cd site && npm run build && node scripts/phase30-gate.mjs
 */

import { execSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');
const ASTRO_DIR = path.join(DIST_DIR, '_astro');
const BASELINE_MD = path.join(
  REPO_ROOT,
  '.planning',
  'phases',
  '30-map-control-shell-rework',
  '30-BASELINE.md'
);

let failures = 0;

function pass(label) {
  console.log(`PASS [${label}]`);
}

function fail(label, msg) {
  console.error(`FAIL [${label}]: ${msg}`);
  failures++;
}

// Strip ANSI color codes.
function stripAnsi(s) {
  // eslint-disable-next-line no-control-regex
  return s.replace(/\x1b\[[0-9;]*m/g, '');
}

function listFiles(dir, exts) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...listFiles(full, exts));
    } else if (exts.some((ext) => entry.name.endsWith(ext))) {
      out.push(full);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Assertion 1: astro-check baseline by error location
// ---------------------------------------------------------------------------
(function checkAstro() {
  const BASELINE_LOCATIONS = new Set(['ComparatorPairsLinks.astro:28']);

  let output = '';
  try {
    output = execSync('npx astro check', {
      cwd: SITE_ROOT,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (e) {
    // Non-zero exit is expected at the baseline error count — capture output.
    output = (e.stdout || '') + (e.stderr || '');
  }

  const clean = stripAnsi(output);
  const lines = clean.split('\n');

  const foundLocations = new Set();
  for (const line of lines) {
    // Astro-check error lines look like: "  File: .../ComparatorPairsLinks.astro:28:5"
    // or contain "error" with a "path:line:col" token. We match any token of the
    // form "<name>.astro:<line>" or "<name>.tsx:<line>" etc. that appears on a
    // line mentioning "error".
    if (line.toLowerCase().indexOf('error') === -1) continue;
    const idx = line.lastIndexOf('.astro:');
    const tsIdx = line.lastIndexOf('.ts:');
    const tsxIdx = line.lastIndexOf('.tsx:');
    for (const [ext, foundIdx] of [
      ['.astro:', idx],
      ['.ts:', tsIdx],
      ['.tsx:', tsxIdx],
    ]) {
      if (foundIdx === -1) continue;
      // Extract "<basename><ext><line>" starting from the nearest path separator.
      const sepIdx = Math.max(line.lastIndexOf('/', foundIdx), line.lastIndexOf('\\', foundIdx));
      const before = sepIdx === -1 ? line.slice(0, foundIdx) : line.slice(sepIdx + 1, foundIdx);
      // after ext, the rest of token up to next non-digit char (colon or space) is the line number
      const afterExt = line.slice(foundIdx + ext.length);
      let lineNum = '';
      for (const ch of afterExt) {
        if (ch >= '0' && ch <= '9') {
          lineNum += ch;
        } else {
          break;
        }
      }
      if (before && lineNum) {
        foundLocations.add(`${before}${ext.slice(0, -1)}:${lineNum}`);
      }
    }
  }

  const unexpected = [...foundLocations].filter((loc) => !BASELINE_LOCATIONS.has(loc));

  if (unexpected.length > 0) {
    fail(
      'astro-check baseline',
      `Unexpected error location(s) outside baseline set: ${unexpected.join(', ')}`
    );
  } else if (foundLocations.size === 0) {
    fail(
      'astro-check baseline',
      'No error locations parsed from astro check output — cannot confirm baseline (raw output may have changed format)'
    );
  } else {
    pass(
      `astro-check baseline (locations match: ${[...foundLocations].join(', ')})`
    );
  }
})();

// ---------------------------------------------------------------------------
// Assertion 2 + 3: git diff --exit-code against PHASE30_BASE_SHA
// ---------------------------------------------------------------------------
let PHASE30_BASE_SHA = null;
(function readBaseSha() {
  if (!existsSync(BASELINE_MD)) {
    fail('PHASE30_BASE_SHA read', `Baseline file not found: ${BASELINE_MD}`);
    return;
  }
  const text = readFileSync(BASELINE_MD, 'utf8');
  const match = text.match(/PHASE30_BASE_SHA:\s*([0-9a-fA-F]+)/);
  if (!match) {
    fail(
      'PHASE30_BASE_SHA read',
      `Line "PHASE30_BASE_SHA: <sha>" missing or malformed in ${BASELINE_MD}`
    );
    return;
  }
  PHASE30_BASE_SHA = match[1];
  pass(`PHASE30_BASE_SHA read (${PHASE30_BASE_SHA})`);
})();

function gitDiffExitCode(label, sha, files) {
  if (!sha) {
    fail(label, 'PHASE30_BASE_SHA not available — cannot run git diff check');
    return;
  }
  const fileArgs = files.map((f) => `"${f}"`).join(' ');
  try {
    execSync(`git diff --exit-code ${sha} -- ${fileArgs}`, {
      cwd: REPO_ROOT,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    pass(label);
  } catch (e) {
    fail(label, `git diff found changes since ${sha} in: ${files.join(', ')}`);
  }
}

gitDiffExitCode('protected Leaflet files + score.mjs unchanged', PHASE30_BASE_SHA, [
  'site/src/components/map/ChoroplethLayer.ts',
  'site/src/components/map/IncidentPinLayer.ts',
  'site/src/components/map/LowZoomDotLayer.ts',
  '.planning/sketches/029-map-controls/score.mjs',
]);

gitDiffExitCode('zero new dependencies (package.json/package-lock.json unchanged)', PHASE30_BASE_SHA, [
  'site/package.json',
  'site/package-lock.json',
]);

// ---------------------------------------------------------------------------
// Assertion 4: .filters-row / .ev-chip absence
// ---------------------------------------------------------------------------
(function checkAbsence() {
  if (!existsSync(DIST_DIR)) {
    fail('filters-row/ev-chip absence', `dist/ not found at ${DIST_DIR} — run npm run build first`);
    return;
  }

  const targets = [];
  const mapEs = path.join(DIST_DIR, 'es', 'mapa', 'index.html');
  const mapEn = path.join(DIST_DIR, 'map', 'index.html');
  if (existsSync(mapEs)) targets.push(mapEs);
  if (existsSync(mapEn)) targets.push(mapEn);
  targets.push(...listFiles(ASTRO_DIR, ['.js', '.css', '.html']));
  // Also include any other file types under _astro just in case
  const allAstroFiles = listFiles(ASTRO_DIR, ['']);
  for (const f of allAstroFiles) {
    if (!targets.includes(f)) targets.push(f);
  }

  let found = [];
  for (const f of targets) {
    let text;
    try {
      text = readFileSync(f, 'utf8');
    } catch {
      continue; // binary or unreadable, skip
    }
    if (text.includes('filters-row')) found.push(`${f}: filters-row`);
    if (text.includes('ev-chip')) found.push(`${f}: ev-chip`);
  }

  if (found.length > 0) {
    fail('filters-row/ev-chip absence', found.join('; '));
  } else {
    pass('filters-row/ev-chip absent from dist/ pages + _astro/*');
  }
})();

// ---------------------------------------------------------------------------
// Assertion 5: showModal( presence
//
// M-06 note: this is necessary-not-sufficient. A substring match cannot
// distinguish `showModal()` actually being called from a `<dialog open>`
// coexisting with a dead `showModal(` reference, or from a string literal.
// The real proof — `dialog.matches(':modal') === true` in a live browser —
// can only be observed at runtime; it lives in 30-06's browser pass
// (30-CLOSE.md §3), not in this static gate.
// ---------------------------------------------------------------------------
(function checkShowModal() {
  if (!existsSync(ASTRO_DIR)) {
    fail('showModal( presence', `dist/_astro/ not found — run npm run build first`);
    return;
  }
  const jsFiles = listFiles(ASTRO_DIR, ['.js']);
  const foundIn = jsFiles.find((f) => {
    try {
      return readFileSync(f, 'utf8').includes('showModal(');
    } catch {
      return false;
    }
  });
  if (foundIn) {
    pass(`showModal( present (${path.basename(foundIn)})`);
  } else {
    fail('showModal( presence', 'No dist/_astro/*.js file contains "showModal("');
  }
})();

// ---------------------------------------------------------------------------
// Assertion 6: z-index ladder in CSS, bound per-selector (whitespace-insensitive)
//
// M-05 fix: the previous version only asked whether the strings "z-index:750",
// "z-index:800", "z-index:801" appeared SOMEWHERE in the bundled CSS — it bound
// no value to a selector. That could not fail: z-index:800 is emitted by the
// pre-existing .map-topbar and .partial-year-badge rules even if .news-toggle
// and .filter-fab lost theirs entirely. This version extracts the declaration
// block for each pinned selector and asserts the value inside THAT block, plus
// asserts the sheet selector carries none at all (spec §3's "z-index: none").
// ---------------------------------------------------------------------------
(function checkZIndex() {
  if (!existsSync(ASTRO_DIR)) {
    fail('z-index ladder', `dist/_astro/ not found — run npm run build first`);
    return;
  }
  const cssFiles = listFiles(ASTRO_DIR, ['.css']);
  if (cssFiles.length === 0) {
    fail('z-index ladder', 'No dist/_astro/*.css files found');
    return;
  }

  // [selector-open-token, required "prop:value" inside that block]
  const rulesRequired = [
    ['.news-toggle{', 'z-index:800'],
    ['.filter-fab{', 'z-index:800'],
    ['.legend{', 'z-index:750'],
  ];
  // Selectors whose block must contain NO z-index declaration at all.
  const rulesForbidden = ['#filter-sheet{', '.filter-sheet{'];

  const foundRequired = new Set();
  const missingByFile = [];
  let forbiddenViolation = null;
  let legendZ700Violation = null;

  // Returns the declaration block body for the first occurrence of `openToken`
  // in `stripped`, starting the scan at `searchFrom`. Returns null if not found.
  function blockAfter(stripped, openToken, searchFrom) {
    const idx = stripped.indexOf(openToken, searchFrom);
    if (idx === -1) return null;
    const bodyStart = idx + openToken.length;
    const closeIdx = stripped.indexOf('}', bodyStart);
    const body = closeIdx === -1 ? stripped.slice(bodyStart) : stripped.slice(bodyStart, closeIdx);
    return { body, nextSearchFrom: idx + openToken.length };
  }

  for (const f of cssFiles) {
    let text;
    try {
      text = readFileSync(f, 'utf8');
    } catch {
      continue;
    }
    const stripped = text.replace(/\s+/g, '');

    for (const [selector, requiredValue] of rulesRequired) {
      let searchFrom = 0;
      while (true) {
        const found = blockAfter(stripped, selector, searchFrom);
        if (!found) break;
        if (found.body.includes(requiredValue)) {
          foundRequired.add(selector);
        }
        searchFrom = found.nextSearchFrom;
      }
    }

    for (const selector of rulesForbidden) {
      let searchFrom = 0;
      while (true) {
        const found = blockAfter(stripped, selector, searchFrom);
        if (!found) break;
        if (found.body.includes('z-index:')) {
          forbiddenViolation = `${f}: ${selector} contains a z-index declaration`;
        }
        searchFrom = found.nextSearchFrom;
      }
    }

    // .legend{...z-index:700 must be absent (the pre-Phase-30 popup-pane tie).
    let searchFrom = 0;
    while (true) {
      const found = blockAfter(stripped, '.legend{', searchFrom);
      if (!found) break;
      if (found.body.includes('z-index:700')) {
        legendZ700Violation = f;
      }
      searchFrom = found.nextSearchFrom;
    }
  }

  const missing = rulesRequired.filter(([selector]) => !foundRequired.has(selector));
  if (missing.length > 0) {
    fail(
      'z-index ladder present (value-per-selector)',
      `${missing.map(([s, v]) => `${s} missing ${v}`).join('; ')} in dist/_astro/*.css`
    );
  } else {
    pass('z-index ladder present, bound per selector (.news-toggle=800, .filter-fab=800, .legend=750)');
  }

  if (forbiddenViolation) {
    fail('filter sheet has no z-index', forbiddenViolation);
  } else {
    pass('filter sheet (#filter-sheet/.filter-sheet) carries no z-index');
  }

  if (legendZ700Violation) {
    fail('.legend z-index:700 absent', `Found ".legend{...z-index:700" in ${legendZ700Violation}`);
  } else {
    pass('.legend z-index:700 absent');
  }
})();

// ---------------------------------------------------------------------------
// Assertion 7: no react-leaflet declarative components anywhere in site/src,
// and no react-leaflet dependency in package.json
//
// M-06 fix: was scoped to site/src/components/map/**  and .tsx/.ts only. F-47
// bans a declarative react-leaflet layer "anywhere", and a <GeoJSON> in
// site/src/pages or site/src/lib, or in a .jsx/.js file, previously passed.
// ---------------------------------------------------------------------------
(function checkReactLeaflet() {
  const SRC_DIR = path.join(SITE_ROOT, 'src');
  if (!existsSync(SRC_DIR)) {
    fail('react-leaflet declarative usage absent', `Directory not found: ${SRC_DIR}`);
    return;
  }
  const srcFiles = listFiles(SRC_DIR, ['.tsx', '.ts', '.jsx', '.js']);
  // JSX-component patterns (<GeoJSON, <Marker) must not be followed by a "."
  // or word char — that would indicate a TS namespace/generic reference
  // (e.g. `useRef<GeoJSON.Feature[]>` or `L.Marker`) rather than an actual
  // JSX element `<GeoJSON ...>` / `<Marker ...>`.
  const jsxBanned = [
    { name: '<GeoJSON', re: /<GeoJSON(?![.\w])/ },
    { name: '<Marker', re: /<Marker(?![.\w])/ },
  ];
  const literalBanned = ["from 'react-leaflet'", 'from "react-leaflet"'];
  const violations = [];
  for (const f of srcFiles) {
    let text;
    try {
      text = readFileSync(f, 'utf8');
    } catch {
      continue;
    }
    for (const b of jsxBanned) {
      if (b.re.test(text)) violations.push(`${f}: ${b.name}`);
    }
    for (const b of literalBanned) {
      if (text.includes(b)) violations.push(`${f}: ${b}`);
    }
  }
  if (violations.length > 0) {
    fail('react-leaflet declarative usage absent', violations.join('; '));
  } else {
    pass('no react-leaflet declarative components (<GeoJSON, <Marker, react-leaflet import) anywhere in site/src');
  }

  const pkgPath = path.join(SITE_ROOT, 'package.json');
  if (!existsSync(pkgPath)) {
    fail('react-leaflet dependency absent', `package.json not found: ${pkgPath}`);
    return;
  }
  let pkg;
  try {
    pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
  } catch (e) {
    fail('react-leaflet dependency absent', `Could not parse package.json: ${e.message}`);
    return;
  }
  const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
  if (Object.prototype.hasOwnProperty.call(deps, 'react-leaflet')) {
    fail('react-leaflet dependency absent', `"react-leaflet" present in ${pkgPath}`);
  } else {
    pass('react-leaflet absent from site/package.json dependencies');
  }
})();


// ---------------------------------------------------------------------------
// Assertion 8: the ?cut= precedence rule is actually WIRED, not merely exported.
//
// N-2 (re-review): shouldApplyRegionFocus() is unit-tested and exported, but
// replacing its call site in MapIsland.tsx with `if (idx)` — i.e. deleting the
// whole "a valid ?cut= beats ?region=" rule — left the entire suite 51/51 green.
// The rule is only observable in a browser, so it is guarded here at source
// level (the F-24 precedent: when no runtime check can distinguish, assert the
// call exists rather than pretending the unit test covers it).
// ---------------------------------------------------------------------------
(function assertRegionPrecedenceWired() {
  const islandPath = path.join(SITE_ROOT, 'src/components/map/MapIsland.tsx');
  const src = readFileSync(islandPath, 'utf8');
  const importsIt = src.includes('shouldApplyRegionFocus');
  const callsIt = /if\s*\(\s*shouldApplyRegionFocus\(/.test(src);
  const stillResolves = src.includes('resolveRegionFocus(');
  if (importsIt && callsIt && stillResolves) {
    pass('?cut= precedence rule wired (shouldApplyRegionFocus guards the region block)');
  } else {
    fail(
      '?cut= precedence rule wired',
      'MapIsland.tsx must guard the ?region= block with if (shouldApplyRegionFocus(...)) — imports:' +
        importsIt + ' guardCall:' + callsIt + ' resolveCall:' + stillResolves
    );
  }
})();


// ---------------------------------------------------------------------------
// Assertion 9: the keyboard invariants F-58 rests on are encoded, not just walked.
//
// Verification finding: the "no focus trap" conclusion at 481/639/1296 rested
// SOLELY on a one-off Tab walk, with nothing to stop a later edit reintroducing
// a document-scoped key interceptor — the same durability hole N-2 found for the
// ?cut= precedence rule, which was closed with a source-level assertion. Same
// precedent applied here.
//
//  (a) No map component may register a document-scoped keyboard listener. This is
//      what keeps score.mjs's criterion 4 measurable at all (keyInterceptors: [])
//      and is why the rail's Escape handling is a container-scoped React onKeyDown.
//  (b) The roving tabindex must stay: exactly the WAI-ARIA radiogroup pattern that
//      F-58 records as the (benign) cause of c4's negativeTabindexCount.
// ---------------------------------------------------------------------------
(function assertKeyboardInvariants() {
  const mapDir = path.join(SITE_ROOT, 'src/components/map');
  const files = listFiles(mapDir, ['.ts', '.tsx']);
  const offenders = [];
  for (const f of files) {
    const src = readFileSync(f, 'utf8');
    if (/document\.addEventListener\([^)]*key/i.test(src)) {
      offenders.push(path.relative(SITE_ROOT, f));
    }
  }
  if (offenders.length > 0) {
    fail(
      'no document-scoped keyboard listener in map components',
      'found in: ' + offenders.join(', ') + ' — a global key interceptor makes score.mjs criterion 4 unmeasurable and can trap focus'
    );
  } else {
    pass('no document-scoped keyboard listener in map components (F-49/F-58 invariant)');
  }

  const ff = readFileSync(path.join(mapDir, 'FilterFields.tsx'), 'utf8');
  const hasRoving = /tabIndex=\{[^}]*\?\s*0\s*:\s*-1\s*\}/.test(ff) || (ff.includes('tabIndex={0}') && ff.includes('tabIndex={-1}'));
  const hasArrows = ff.includes('ArrowRight') && ff.includes('ArrowLeft') && ff.includes('Home') && ff.includes('End');
  if (hasRoving && hasArrows) {
    pass('radiogroups keep roving tabindex + arrow/Home/End navigation');
  } else {
    fail(
      'radiogroups keep roving tabindex + arrow key navigation',
      'FilterFields.tsx must keep the WAI-ARIA radiogroup pattern — roving:' + hasRoving + ' arrowKeys:' + hasArrows
    );
  }
})();

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nFAIL phase30-gate: ${failures} assertion(s) failed`);
  process.exit(1);
}

console.log('\nPASS phase30-gate: all assertions passed');
process.exit(0);
