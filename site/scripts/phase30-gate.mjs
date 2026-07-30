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
// Assertion 6: z-index ladder in CSS (whitespace-insensitive)
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

  const required = ['z-index:750', 'z-index:800', 'z-index:801'];
  const foundRequired = new Set();
  let legendViolation = null;

  for (const f of cssFiles) {
    let text;
    try {
      text = readFileSync(f, 'utf8');
    } catch {
      continue;
    }
    const stripped = text.replace(/\s+/g, '');

    for (const req of required) {
      if (stripped.includes(req)) foundRequired.add(req);
    }

    // .legend{...z-index:700 must be absent. Look for ".legend{" followed
    // (without another "}" in between) by "z-index:700".
    let searchFrom = 0;
    while (true) {
      const legendIdx = stripped.indexOf('.legend{', searchFrom);
      if (legendIdx === -1) break;
      const closeIdx = stripped.indexOf('}', legendIdx);
      const block = closeIdx === -1 ? stripped.slice(legendIdx) : stripped.slice(legendIdx, closeIdx);
      if (block.includes('z-index:700')) {
        legendViolation = f;
        break;
      }
      searchFrom = legendIdx + 8;
    }
    if (legendViolation) break;
  }

  const missing = required.filter((r) => !foundRequired.has(r));
  if (missing.length > 0) {
    fail('z-index ladder present', `Missing required value(s) in dist/_astro/*.css: ${missing.join(', ')}`);
  } else {
    pass('z-index ladder present (750, 800, 801)');
  }

  if (legendViolation) {
    fail('.legend z-index:700 absent', `Found ".legend{...z-index:700" in ${legendViolation}`);
  } else {
    pass('.legend z-index:700 absent');
  }
})();

// ---------------------------------------------------------------------------
// Assertion 7: no react-leaflet declarative components in map source
// ---------------------------------------------------------------------------
(function checkReactLeaflet() {
  const MAP_SRC_DIR = path.join(SITE_ROOT, 'src', 'components', 'map');
  if (!existsSync(MAP_SRC_DIR)) {
    fail('react-leaflet declarative usage absent', `Directory not found: ${MAP_SRC_DIR}`);
    return;
  }
  const srcFiles = listFiles(MAP_SRC_DIR, ['.tsx', '.ts']);
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
    pass('no react-leaflet declarative components (<GeoJSON, <Marker, react-leaflet import) in map source');
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
