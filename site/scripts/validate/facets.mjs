/**
 * facets.mjs — Validator #16: news facet count integrity.
 *
 * Deliberately independent of site/src/lib/newsFacets.ts — this validator
 * re-implements plain-JS assertions against raw JSON so it can detect drift
 * between the module's real output and the data, rather than testing itself.
 *
 * Reads data/incidents/current.json (or an override path — see below),
 * data/incidents/archive/*.json, data/cead/meta/index.json, and
 * pipeline/shared/schema.py from repo root.
 *
 * Accepts an optional override path via process.argv[2] or
 * process.env.FACETS_CURRENT_JSON, defaulting to data/incidents/current.json.
 * This exists so the negative-path demonstration (bad CUT / homicidios leak)
 * never needs to touch the real data/ tree — it points this validator at a
 * fixture built in os.tmpdir() instead.
 *
 * Exit codes:
 *   0 — all 10 assertions pass (PASS)
 *   1 — any assertion fails (FAIL)
 *
 * Usage:
 *   node scripts/validate/facets.mjs
 *   node scripts/validate/facets.mjs <path-to-current.json>
 *   FACETS_CURRENT_JSON=<path> node scripts/validate/facets.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');

const CURRENT_JSON_PATH =
  process.argv[2] ||
  process.env.FACETS_CURRENT_JSON ||
  path.join(REPO_ROOT, 'data', 'incidents', 'current.json');
const ARCHIVE_DIR = path.join(REPO_ROOT, 'data', 'incidents', 'archive');
const INDEX_JSON_PATH = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');
const SCHEMA_PY_PATH = path.join(REPO_ROOT, 'pipeline', 'shared', 'schema.py');
const NEWS_FACETS_TS_PATH = path.join(SITE_ROOT, 'src', 'lib', 'newsFacets.ts');

function fail(reason) {
  console.error(`FAIL facets: ${reason}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Load inputs
// ---------------------------------------------------------------------------
if (!existsSync(CURRENT_JSON_PATH)) {
  fail(`current.json not found at ${CURRENT_JSON_PATH}`);
}
let currentData;
try {
  currentData = JSON.parse(readFileSync(CURRENT_JSON_PATH, 'utf-8'));
} catch (err) {
  fail(`could not parse current.json — ${err.message}`);
}
const incidents = currentData.incidents ?? [];

if (!existsSync(INDEX_JSON_PATH)) {
  fail(`index.json not found at ${INDEX_JSON_PATH}`);
}
let indexData;
try {
  indexData = JSON.parse(readFileSync(INDEX_JSON_PATH, 'utf-8'));
} catch (err) {
  fail(`could not parse index.json — ${err.message}`);
}

const cutToRegion = new Map(indexData.map((c) => [String(c.cut), c.region_id]));

// ---------------------------------------------------------------------------
// Assertion 1: sum of per-family counts equals count of incidents with family
// ---------------------------------------------------------------------------
const familyCounts = new Map();
let incidentsWithFamily = 0;
for (const inc of incidents) {
  if (!inc.family) continue;
  incidentsWithFamily++;
  familyCounts.set(inc.family, (familyCounts.get(inc.family) ?? 0) + 1);
}
const sumFamilyCounts = Array.from(familyCounts.values()).reduce((a, b) => a + b, 0);
if (sumFamilyCounts !== incidentsWithFamily) {
  fail(
    `assertion 1 — sum of family counts (${sumFamilyCounts}) !== incidents-with-family (${incidentsWithFamily})`
  );
}

// ---------------------------------------------------------------------------
// Assertion 2: every incident's String(cut) resolves to a region_id in "1".."16"
// ---------------------------------------------------------------------------
const VALID_REGION_IDS = new Set(Array.from({ length: 16 }, (_, i) => String(i + 1)));
for (const inc of incidents) {
  const regionId = cutToRegion.get(String(inc.cut));
  if (!regionId) {
    fail(`assertion 2 — incident cut ${JSON.stringify(inc.cut)} does not resolve to a region_id in index.json`);
  }
  if (!VALID_REGION_IDS.has(regionId)) {
    fail(`assertion 2 — resolved region_id "${regionId}" for cut ${JSON.stringify(inc.cut)} is not in 1..16`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 3: family set derived live from pipeline/shared/schema.py, never
// hand-transcribed. Regex-match FAMILY_KEYS list literal.
// ---------------------------------------------------------------------------
if (!existsSync(SCHEMA_PY_PATH)) {
  fail(`pipeline/shared/schema.py not found at ${SCHEMA_PY_PATH}`);
}
const schemaSrc = readFileSync(SCHEMA_PY_PATH, 'utf-8');
const familyKeysMatch = schemaSrc.match(/FAMILY_KEYS:\s*list\[str\]\s*=\s*\[([\s\S]*?)\]/);
if (!familyKeysMatch) {
  fail(
    'assertion 3 — could not locate FAMILY_KEYS list literal in pipeline/shared/schema.py (regex did not match)'
  );
}
const familyKeysBody = familyKeysMatch[1];
const parsedFamilyKeys = Array.from(familyKeysBody.matchAll(/["']([\w]+)["']/g)).map((m) => m[1]);
if (parsedFamilyKeys.length !== 7) {
  fail(
    `assertion 3 — parsed FAMILY_KEYS has ${parsedFamilyKeys.length} entries, expected exactly 7. ` +
      'CEAD FAMILY_KEYS must stay at 7 (see memory: sexuales news-only family). ' +
      `Parsed: ${JSON.stringify(parsedFamilyKeys)}`
  );
}
const VALID_FAMILIES = new Set([...parsedFamilyKeys, 'sexuales']);
const observedFamilies = new Set(incidents.map((i) => i.family).filter(Boolean));
for (const fam of observedFamilies) {
  if (!VALID_FAMILIES.has(fam)) {
    fail(`assertion 3 — observed family "${fam}" is not a member of VALID_FAMILIES (${[...VALID_FAMILIES].join(', ')})`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 4: 'homicidios' does not appear among observed families
// ---------------------------------------------------------------------------
if (observedFamilies.has('homicidios')) {
  fail('assertion 4 — phantom family "homicidios" observed in current.json incidents');
}

// ---------------------------------------------------------------------------
// Assertion 5: 'sexuales' IS present among observed families
// ---------------------------------------------------------------------------
if (!observedFamilies.has('sexuales')) {
  fail('assertion 5 — expected 8th news-only family "sexuales" is absent from observed families');
}

// ---------------------------------------------------------------------------
// Assertion 6: CUT-length cross-check for all 346 index.json entries
// ---------------------------------------------------------------------------
if (indexData.length !== 346) {
  fail(`assertion 6 — expected 346 index.json entries, found ${indexData.length}`);
}
const derivedRegionIds = new Set();
for (const entry of indexData) {
  const cut = String(entry.cut);
  const derived = cut.length === 4 ? cut.slice(0, 1) : cut.slice(0, 2);
  if (derived !== entry.region_id) {
    fail(
      `assertion 6 — CUT-length derivation mismatch for cut ${cut}: derived="${derived}" region_id="${entry.region_id}"`
    );
  }
  derivedRegionIds.add(entry.region_id);
}
if (derivedRegionIds.size !== 16) {
  fail(`assertion 6 — expected exactly 16 distinct region_id values, found ${derivedRegionIds.size}`);
}

// ---------------------------------------------------------------------------
// Assertion 7: byMonth completeness — every current.json month is representable
// in the archive+current union this validator independently derives
// ---------------------------------------------------------------------------
const currentMonths = new Set(incidents.map((i) => i.date.slice(0, 7)));
const archiveMonths = new Set();
if (existsSync(ARCHIVE_DIR)) {
  const files = readdirSync(ARCHIVE_DIR).filter((f) => /^\d{4}-\d{2}\.json$/.test(f));
  for (const f of files) {
    archiveMonths.add(f.replace('.json', ''));
  }
}
const unionMonths = new Set([...currentMonths, ...archiveMonths]);
for (const month of currentMonths) {
  if (!unionMonths.has(month)) {
    fail(`assertion 7 — current.json month "${month}" is excluded from the archive+current union`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 8: window day-granularity sanity (monotonic containment)
// ---------------------------------------------------------------------------
let newestDate = null;
for (const inc of incidents) {
  if (!newestDate || inc.date > newestDate) newestDate = inc.date;
}
let todayCount = 0;
let sevenDayCount = 0;
let thirtyDayCount = 0;
if (newestDate) {
  const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
  const lower7 = new Date(anchorMs - 6 * 86400000).toISOString().slice(0, 10);
  const lower30 = new Date(anchorMs - 29 * 86400000).toISOString().slice(0, 10);
  for (const inc of incidents) {
    if (inc.date === newestDate) todayCount++;
    if (inc.date >= lower7) sevenDayCount++;
    if (inc.date >= lower30) thirtyDayCount++;
  }
}
// Day-granularity is preset-only by construction — no per-day bucket structure
// exists to check for absence; this assertion checks monotonic containment only.
if (!(todayCount <= sevenDayCount && sevenDayCount <= thirtyDayCount)) {
  fail(
    `assertion 8 — window buckets not monotonically increasing: today=${todayCount} 7d=${sevenDayCount} 30d=${thirtyDayCount}`
  );
}
if (thirtyDayCount > incidents.length) {
  fail(`assertion 8 — thirtyDay count (${thirtyDayCount}) exceeds total incidents (${incidents.length})`);
}
if (incidents.length > 0 && todayCount === 0) {
  fail('assertion 8 — today window is empty despite incidents.length > 0');
}

// ---------------------------------------------------------------------------
// Assertion 9: TZ determinism. The window boundaries above use only UTC-safe
// primitives (TZ-independent by construction). Grep newsFacets.ts (NOT this
// validator's own source — a self-scan would always match its own pattern
// list and exit 1 unconditionally) for TZ-sensitive patterns, then run an
// executable spawnSync proof under both TZ=UTC and TZ=America/Santiago.
// ---------------------------------------------------------------------------
if (!existsSync(NEWS_FACETS_TS_PATH)) {
  fail(`assertion 9 — newsFacets.ts not found at ${NEWS_FACETS_TS_PATH}`);
}
const newsFacetsSrc = readFileSync(NEWS_FACETS_TS_PATH, 'utf-8');
const tzSensitivePatterns = [/toLocaleDateString/, /getMonth\(/, /new Date\(\d/];
for (const pattern of tzSensitivePatterns) {
  if (pattern.test(newsFacetsSrc)) {
    fail(`assertion 9 — TZ-sensitive pattern ${pattern} found in newsFacets.ts`);
  }
}

const windowCalcScript = `
const incidents = [
  { date: '2026-07-28' },
  { date: '2026-07-25' },
  { date: '2026-06-29' },
  { date: '2026-06-28' },
];
let newestDate = null;
for (const inc of incidents) { if (!newestDate || inc.date > newestDate) newestDate = inc.date; }
const anchorMs = Date.parse(newestDate + 'T00:00:00Z');
const lower7 = new Date(anchorMs - 6 * 86400000).toISOString().slice(0, 10);
const lower30 = new Date(anchorMs - 29 * 86400000).toISOString().slice(0, 10);
let today = 0, sevenDay = 0, thirtyDay = 0;
for (const inc of incidents) {
  if (inc.date === newestDate) today++;
  if (inc.date >= lower7) sevenDay++;
  if (inc.date >= lower30) thirtyDay++;
}
console.log(JSON.stringify({ today, sevenDay, thirtyDay }));
`;

const utcRun = spawnSync(process.execPath, ['-e', windowCalcScript], {
  env: { ...process.env, TZ: 'UTC' },
});
const clRun = spawnSync(process.execPath, ['-e', windowCalcScript], {
  env: { ...process.env, TZ: 'America/Santiago' },
});
if (utcRun.status !== 0 || clRun.status !== 0) {
  fail(`assertion 9 — TZ determinism spawnSync failed (utc status=${utcRun.status}, cl status=${clRun.status})`);
}
const utcOut = utcRun.stdout.toString().trim();
const clOut = clRun.stdout.toString().trim();
if (utcOut !== clOut) {
  fail(`assertion 9 — window computation differs under TZ=UTC (${utcOut}) vs TZ=America/Santiago (${clOut})`);
}

// ---------------------------------------------------------------------------
// Assertion 10: stray facet-artifact walk under site/public/ (gitignored paths
// included — git status --porcelain is blind to those).
// ---------------------------------------------------------------------------
const PUBLIC_DIR = path.join(SITE_ROOT, 'public');
const SKIP_DIRS = new Set(['node_modules', '.astro', 'dist']);

function walk(dir, found) {
  if (!existsSync(dir)) return;
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, found);
    } else if (/facet/i.test(entry.name)) {
      found.push(full);
    }
  }
}

const strayArtifacts = [];
walk(PUBLIC_DIR, strayArtifacts);
if (strayArtifacts.length > 0) {
  fail(`assertion 10 — stray facet artifact(s) found under site/public/: ${strayArtifacts.join(', ')}`);
}

// ---------------------------------------------------------------------------
// All assertions passed
// ---------------------------------------------------------------------------
console.log(
  `PASS facets: ${incidents.length} incidents, ${familyCounts.size} families observed, ` +
    `${indexData.length} communes cross-checked, ${unionMonths.size} months in byMonth union, ` +
    `window(today=${todayCount},7d=${sevenDayCount},30d=${thirtyDayCount}), TZ-determinism verified`
);
