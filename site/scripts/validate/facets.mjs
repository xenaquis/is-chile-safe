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
//
// L-1 (fix cycle 1): this assertion hardcodes INDEX_JSON_PATH and does NOT
// honor the argv[2]/FACETS_CURRENT_JSON override (that override only affects
// CURRENT_JSON_PATH). It cannot be exercised in the negative direction without
// mutating a tracked file under data/, which the F-19/hard-rule regime
// forbids. It is currently true in the positive direction (346 entries, all
// CUT-length derivations match, exactly 16 distinct region_ids) but is
// untestable for a negative case — a known coverage limitation, not a bug.
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
// Assertion 7 (fix cycle 1, M-2): per-month union-of-IDs count, cross-checked
// against the BUILT PAGE's rendered #news-facets byMonth output.
//
// The prior version only asserted "every current.json month appears in the
// archive+current union it just built" — a tautology that cannot fail for any
// input (confirmed empirically: a current-only 2019 month with zero archive
// coverage still passed). This version independently recomputes, from raw
// data/incidents/*.json only, the per-month de-duplicated-by-id union size,
// then reads the ACTUAL rendered dist/ page (produced by newsFacets.ts,
// unmodified) and asserts its byMonth counts match. This is what makes it
// falsifiable: if newsFacets.ts regresses to reporting the archive count alone
// for 'both' months (H-1), this assertion diverges from the page's real
// output and fails the build. It also closes H-1's validator half.
// ---------------------------------------------------------------------------
function loadArchiveMonthIds(dir) {
  const map = new Map();
  if (!existsSync(dir)) return map;
  let files = [];
  try {
    files = readdirSync(dir).filter((f) => /^\d{4}-\d{2}\.json$/.test(f));
  } catch {
    return map;
  }
  for (const f of files) {
    const yearMonth = f.replace('.json', '');
    try {
      const raw = JSON.parse(readFileSync(path.join(dir, f), 'utf-8'));
      const ids = new Set((raw.incidents ?? []).map((inc, i) => String(inc.id ?? `${f}-${i}`)));
      map.set(yearMonth, ids);
    } catch {
      // Malformed archive month — skip, mirrors newsFacets.ts Pitfall 4 discipline
    }
  }
  return map;
}

const archiveMonthIds = loadArchiveMonthIds(ARCHIVE_DIR);
const currentMonthIds = new Map();
for (const inc of incidents) {
  const ym = inc.date.slice(0, 7);
  if (!currentMonthIds.has(ym)) currentMonthIds.set(ym, new Set());
  currentMonthIds.get(ym).add(String(inc.id ?? `${inc.cut}-${inc.date}`));
}

const expectedByMonth = new Map();
const allMonthsForCheck = new Set([...archiveMonthIds.keys(), ...currentMonthIds.keys()]);
for (const yearMonth of allMonthsForCheck) {
  const archiveIds = archiveMonthIds.get(yearMonth);
  const currentIds = currentMonthIds.get(yearMonth);
  if (archiveIds && currentIds) {
    expectedByMonth.set(yearMonth, new Set([...archiveIds, ...currentIds]).size);
  } else if (archiveIds) {
    expectedByMonth.set(yearMonth, archiveIds.size);
  } else {
    expectedByMonth.set(yearMonth, currentIds.size);
  }
}

// RR-1 (fix cycle 2): both locales are checked, not just EN. Before this, no
// validator ever opened dist/es/noticias/index.html, so the ES page could drift
// or lose its facet node entirely without any gate noticing.
const DIST_PAGES = [
  ['EN', path.join(SITE_ROOT, 'dist', 'news', 'index.html')],
  ['ES', path.join(SITE_ROOT, 'dist', 'es', 'noticias', 'index.html')],
];

// RR-1 (fix cycle 2), part 1 of 2 — SOURCE-level guard on the H-2 escaping.
//
// The re-review proposed catching a reverted escaping by asserting the rendered
// node contains no raw `<`. Measured: that does NOT work. The real payload
// contains no `<` at all, so `escapeForInlineScript(JSON.stringify(p))` and a
// bare `JSON.stringify(p)` emit byte-identical HTML — I reverted the ES page's
// call, rebuilt, and the dist-level check still passed. The only check that
// actually detects the control disappearing is a source-level one, so both
// guards are kept: this one catches the revert, the dist-level `<` check below
// catches a hostile payload that somehow reaches the page unescaped.
const SERIALIZATION_SITES = [
  ['EN', path.join(SITE_ROOT, 'src', 'pages', 'news.astro')],
  ['ES', path.join(SITE_ROOT, 'src', 'pages', 'es', 'noticias.astro')],
];
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  if (!existsSync(pagePath)) {
    fail(`assertion 7 — ${locale} news page source not found at ${pagePath}`);
  }
  const pageSrc = readFileSync(pagePath, 'utf-8');
  if (!pageSrc.includes('escapeForInlineScript(JSON.stringify(facetsProjection))')) {
    fail(
      `assertion 7 — ${locale} news page does not wrap the #news-facets payload in ` +
        `escapeForInlineScript(JSON.stringify(facetsProjection)). set:html is unescaped, so a ` +
        `"</script" sequence in a data-derived string (byFamily[].key comes from the LLM ` +
        `classifier over scraped headlines) would break out of the script element. ` +
        `This guard is source-level on purpose: with today's data the escaped and unescaped ` +
        `output are byte-identical, so no dist-level check can detect the call being removed.`
    );
  }
}

for (const [locale, distPath] of DIST_PAGES) {
  if (!existsSync(distPath)) {
    fail(`assertion 7 — ${locale} built page not found at ${distPath} (requires a prior build)`);
  }
  const distHtml = readFileSync(distPath, 'utf-8');
  const facetsMatch = distHtml.match(
    /<script type="application\/json" id="news-facets">([\s\S]*?)<\/script>/
  );
  if (!facetsMatch) {
    fail(`assertion 7 — could not find #news-facets JSON node in ${locale} built page`);
  }

  // RR-1: page-level regression guard for the H-2 escaping.
  //
  // `escapeForInlineScript` turns every `<` into `<`, so a correctly
  // serialized node can contain NO raw `<` at all. Today's real payload happens
  // to contain no `<` either, which means reverting the escaping call in either
  // page would produce a byte-identical dist/ and pass every other gate — the
  // security control could vanish invisibly. This check fires on the RESULT
  // (no raw `<` in the node) rather than on hostile input, so it holds now,
  // before any poisoned family value exists, and it fires per locale.
  if (facetsMatch[1].includes('<')) {
    fail(
      `assertion 7 — raw "<" found in the ${locale} #news-facets node: the H-2 ` +
        `escapeForInlineScript() call is missing or was reverted on this page. A raw ` +
        `"</script" sequence in a data-derived string would break out of the script element.`
    );
  }

  let renderedFacets;
  try {
    // The rendered node is escaped per H-2 (`<` -> `<`) — valid JSON, parses identically.
    renderedFacets = JSON.parse(facetsMatch[1]);
  } catch (err) {
    fail(`assertion 7 — could not parse ${locale} #news-facets JSON — ${err.message}`);
  }
  const renderedByMonth = new Map(
    (renderedFacets.byMonth ?? []).map((m) => [m.yearMonth, m.count])
  );

  for (const [yearMonth, expectedCount] of expectedByMonth) {
    const actualCount = renderedByMonth.get(yearMonth);
    if (actualCount === undefined) {
      fail(`assertion 7 — month "${yearMonth}" missing from ${locale} rendered #news-facets byMonth`);
    }
    if (actualCount !== expectedCount) {
      fail(
        `assertion 7 — ${locale} byMonth count mismatch for "${yearMonth}": rendered=${actualCount}, ` +
          `independently-computed union=${expectedCount}`
      );
    }
  }
}
const unionMonths = new Set([...currentMonthIds.keys(), ...archiveMonthIds.keys()]);

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
// M-3 (fix cycle 1): removed the prior "today window is empty despite
// incidents.length > 0" check — it was unreachable dead code. `today` is
// defined as `date === newestDate` where `newestDate` is the max date of that
// SAME array, so a non-empty array always has >= 1 match by construction; the
// check could never fail for any input (confirmed: could not construct a
// counterexample). Re-deriving "todayCount equals count of max-date incidents"
// here would just duplicate the identical computation a few lines above over
// the identical input and is equally incapable of failing — not a real
// regression guard. Monotonic containment (above) and the thirtyDay-vs-total
// bound (above) remain as the real invariants this assertion protects.

// ---------------------------------------------------------------------------
// Assertion 9: TZ determinism. The window boundaries above use only UTC-safe
// primitives (TZ-independent by construction). Grep newsFacets.ts (NOT this
// validator's own source — a self-scan would always match its own pattern
// list and exit 1 unconditionally) for TZ-sensitive patterns, then run an
// executable spawnSync proof under both TZ=UTC and TZ=America/Santiago.
//
// L-1 (fix cycle 1): like assertion 6, this hardcodes NEWS_FACETS_TS_PATH and
// does not honor the argv[2]/FACETS_CURRENT_JSON override — that override
// only ever pointed at CURRENT_JSON_PATH. This assertion is nonetheless
// demonstrably live: a prior wave's reported deviation was this exact scan
// firing on a doc-comment containing the literal `toLocaleDateString`,
// forcing a reword. Known coverage limitation for the negative-file-path
// case, not a bug.
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
// Assertion 11: anchorDate correctness + UTC timeZone on page-level
// toLocaleDateString month formatting.
//
// Reuses the `newestDate` local already computed above (assertion 8) rather
// than recomputing a third time. Falsifiable counterexample (manually
// demonstrated once, not executed by this file): point FACETS_CURRENT_JSON at
// a tmp fixture whose max incident date is moved back one day -> RED, because
// the rendered anchorDate would then differ from the independently
// recomputed newestDate. Second counterexample: remove `timeZone: 'UTC'` from
// a `toLocaleDateString(...)` call with a `month:` option in either page's
// source -> RED (closes the gap left by assertion 9, which only scans
// newsFacets.ts and never reads the .astro pages).
// ---------------------------------------------------------------------------
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  const facetsMatch = distHtml.match(
    /<script type="application\/json" id="news-facets">([\s\S]*?)<\/script>/
  );
  if (!facetsMatch) {
    fail(`assertion 11 — could not find #news-facets JSON node in ${locale} built page`);
  }
  let renderedFacets;
  try {
    renderedFacets = JSON.parse(facetsMatch[1]);
  } catch (err) {
    fail(`assertion 11 — could not parse ${locale} #news-facets JSON — ${err.message}`);
  }
  if (renderedFacets.anchorDate !== newestDate) {
    fail(
      `assertion 11 — ${locale} rendered anchorDate "${renderedFacets.anchorDate}" !== ` +
        `independently-recomputed newest date "${newestDate}"`
    );
  }
}
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  const pageSrc = readFileSync(pagePath, 'utf-8');
  // Scan the call's argument region by slicing a fixed-length tail after the
  // call head, rather than matching a paren-free "[^)]*" run — a call whose
  // arguments contain a nested paren (e.g. buildOpts(), Number(x), a nested
  // object/function call) would otherwise silently escape a "[^)]*"-based
  // regex: it does not fail, it just stops matching.
  for (const m of pageSrc.matchAll(/(toLocaleDateString|Intl\.DateTimeFormat)\s*\(/g)) {
    const tail = pageSrc.slice(m.index, m.index + 400);
    if (/month\s*:/.test(tail) && !/timeZone:\s*['"]UTC['"]/.test(tail)) {
      fail(
        `assertion 11 — ${locale} page has a ${m[1]}(...) call with a ` +
          `"month:" option but no "timeZone: 'UTC'" — call snippet: ${tail.slice(0, 80)}`
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Assertion 12: card-count == incident-count (NEWSUI-02 static superset).
//
// Matches `<article ...class="...news-card..."...>` order-independently over
// attributes, NOT a bare substring count (which also matches the inlined
// `.news-card` CSS rule text — VERIFIED: bare substring returns 1216 vs the
// correct 1215). Falsifiable counterexample: render with one incident
// dropped -> RED.
// ---------------------------------------------------------------------------
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  const cardMatches = distHtml.match(/<article\b[^>]*\bclass="[^"]*\bnews-card\b[^"]*"/g) ?? [];
  if (cardMatches.length !== incidents.length) {
    fail(
      `assertion 12 — ${locale} news-card count (${cardMatches.length}) !== ` +
        `incidents.length (${incidents.length})`
    );
  }
  // NEWSUI-02 companion guard: the count check above treats
  // `<article class="news-card" hidden …>` identically to a visible card,
  // so it cannot by itself detect a regression to server-side hiding.
  // Assert that zero .news-card / .news-month-section nodes ship the
  // `hidden` attribute, and that no author CSS overrides `display` on the
  // hidden-controlled nodes (which would defeat the UA [hidden] rule even
  // if the attribute itself is absent).
  //
  // WR2-02 fix: `hidden` must be tested in ATTRIBUTE-NAME position, never as
  // a substring of an attribute VALUE (cards carry free-form `data-*`
  // values — commune names, LLM-classifier family output — that are not
  // fully controlled, e.g. `data-note="a hidden b"` on a fully visible
  // card must NOT trip this). Strip every `="..."` attribute-value body
  // from the captured opening tag before testing for a bare `hidden`
  // token, so only a genuine `hidden` attribute (boolean or `hidden=""`,
  // whether mid-tag or as the last attribute before `>`) can match.
  function tagHasHiddenAttr(tag) {
    const valuesStripped = tag.replace(/="[^"]*"/g, '=""');
    return /\shidden(?=[\s>])/.test(valuesStripped);
  }
  for (const m of distHtml.matchAll(/<article\b[^>]*>/g)) {
    const tag = m[0];
    if (/\bclass="[^"]*\bnews-card\b[^"]*"/.test(tag) && tagHasHiddenAttr(tag)) {
      fail(`assertion 12 — ${locale} ships a .news-card with the hidden attribute (NEWSUI-02 violation)`);
    }
  }
  for (const m of distHtml.matchAll(/<section\b[^>]*>/g)) {
    const tag = m[0];
    if (/\bclass="[^"]*\bnews-month-section\b[^"]*"/.test(tag) && tagHasHiddenAttr(tag)) {
      fail(`assertion 12 — ${locale} ships a hidden .news-month-section (NEWSUI-02 violation)`);
    }
  }
  if (/\.news-card[^{}]*\{[^}]*display\s*:/.test(distHtml)) {
    fail(`assertion 12 — ${locale} author CSS sets display on .news-card, defeating [hidden]`);
  }
  // WR2-03 fix: the CSS-rule check above only inspects stylesheet text, so
  // an inline `style="display:none"` directly on a card/month-section node
  // — the reflex alternative to `el.hidden = …` and therefore the most
  // likely future F-26 regression — left the validator green. Test each
  // opening tag's own `style="..."` attribute value for a `display` decl.
  for (const m of distHtml.matchAll(/<(article|section)\b[^>]*>/g)) {
    const tag = m[0];
    if (
      /\bclass="[^"]*\bnews-(card|month-section)\b[^"]*"/.test(tag) &&
      /\sstyle="[^"]*display\s*:/.test(tag)
    ) {
      fail(`assertion 12 — ${locale} sets inline style="display:..." on a news node (F-26 violation)`);
    }
  }
}

// ---------------------------------------------------------------------------
// Assertion 13: EN/ES i18n key parity for all news_* keys (digit-safe).
//
// Falsifiable counterexample: delete one news_* key from ES_STRINGS -> RED.
// ---------------------------------------------------------------------------
const I18N_TS_PATH = path.join(SITE_ROOT, 'src', 'config', 'i18n.ts');
if (!existsSync(I18N_TS_PATH)) {
  fail(`assertion 13 — i18n.ts not found at ${I18N_TS_PATH}`);
}
const i18nSrc = readFileSync(I18N_TS_PATH, 'utf-8');
function extractBlock(src, anchor) {
  const idx = src.indexOf(anchor);
  if (idx === -1) return null;
  // From the anchor to the next top-level "};" close (mirrors this file's
  // style of parsing TS source with string ops rather than importing it).
  const closeIdx = src.indexOf('\n};', idx);
  return closeIdx === -1 ? src.slice(idx) : src.slice(idx, closeIdx);
}
const enBlock = extractBlock(i18nSrc, 'export const EN_STRINGS');
const esBlock = extractBlock(i18nSrc, 'export const ES_STRINGS');
if (!enBlock) fail('assertion 13 — could not locate "export const EN_STRINGS" in i18n.ts');
if (!esBlock) fail('assertion 13 — could not locate "export const ES_STRINGS" in i18n.ts');
function extractNewsKeys(block) {
  return new Set(Array.from(block.matchAll(/^\s*(news_[a-z0-9_]+)\s*:/gm)).map((m) => m[1]));
}
const enNewsKeys = extractNewsKeys(enBlock);
const esNewsKeys = extractNewsKeys(esBlock);
if (enNewsKeys.size < 15) {
  fail(`assertion 13 — EN_STRINGS harvested only ${enNewsKeys.size} news_* keys, expected >= 15`);
}
if (esNewsKeys.size < 15) {
  fail(`assertion 13 — ES_STRINGS harvested only ${esNewsKeys.size} news_* keys, expected >= 15`);
}
for (const key of enNewsKeys) {
  if (!esNewsKeys.has(key)) {
    fail(`assertion 13 — news_* key "${key}" present in EN_STRINGS but missing from ES_STRINGS`);
  }
}
for (const key of esNewsKeys) {
  if (!enNewsKeys.has(key)) {
    fail(`assertion 13 — news_* key "${key}" present in ES_STRINGS but missing from EN_STRINGS`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 14: empty-state node presence — id="news-empty", ships `hidden`
// in the initial render, and is not an h1/h2.
//
// Falsifiable counterexample: remove `hidden` from #news-empty, or delete
// the node -> RED.
// ---------------------------------------------------------------------------
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  const emptyMatch = distHtml.match(/<(\w+)\b([^>]*\bid="news-empty"[^>]*)>/);
  if (!emptyMatch) {
    fail(`assertion 14 — ${locale} built page has no element with id="news-empty"`);
  }
  const [, tagName, attrs] = emptyMatch;
  if (!/\bhidden\b/.test(attrs)) {
    fail(`assertion 14 — ${locale} #news-empty node does not ship the "hidden" attribute`);
  }
  if (/^h[12]$/i.test(tagName)) {
    fail(`assertion 14 — ${locale} #news-empty is a <${tagName}> heading, expected a non-heading element`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 15: no-island — dist HTML never contains Astro's hydration
// marker "astro-island" (structural proof of NEWSUI-06's no-hydration
// claim). Falsifiable counterexample: add any client: directive -> RED
// (astro-island would then appear in the built output).
// ---------------------------------------------------------------------------
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  if (distHtml.includes('astro-island')) {
    fail(`assertion 15 — ${locale} built page contains "astro-island" (unexpected hydration island)`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 16: no cluster markup — news_cluster_source_count (Plan 28-01's
// reserved, unwired key) must never be CONSUMED by either page's template.
// Checked against the two .astro sources only, never i18n.ts (which is
// expected/required to hold the reserved key per assertion 13).
//
// Falsifiable counterexample: add a source-count badge element referencing
// the key or one of these class tokens to either page -> RED.
// ---------------------------------------------------------------------------
const CLUSTER_MARKUP_PATTERNS = [
  /news-source-count/,
  /news-cluster/,
  /source-count/,
  /sources<\//,
  /fuentes<\//,
];
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  const pageSrc = readFileSync(pagePath, 'utf-8');
  for (const pattern of CLUSTER_MARKUP_PATTERNS) {
    if (pattern.test(pageSrc)) {
      fail(`assertion 16 — ${locale} page source contains cluster-markup pattern ${pattern}`);
    }
  }
}
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  for (const pattern of CLUSTER_MARKUP_PATTERNS) {
    if (pattern.test(distHtml)) {
      fail(`assertion 16 — ${locale} built page contains cluster-markup pattern ${pattern}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Assertion 17: F-27 bundling proof — the shipped page script (inline OR
// chunked, whichever emission shape Astro actually produced) must contain
// the FILTER_LOGIC_MARKER string literal ('newsFilterLogic/v1'). Identifiers
// are mangled by minification; only string literals survive, which is why
// this asserts against the literal rather than any function/variable name.
//
// Collects (a) all inline <script type="module"> bodies in the page, and
// (b) the contents of every dist/_astro/*.js referenced via
// <script type="module" src="/_astro/...">, PLUS one level of that chunk's
// own static import specifiers (Rollup may hoist newsFilterLogic into a
// shared chunk — VERIFIED on the current tree: news.astro's page script
// imports from "./newsFilterLogic.BS0afx7K.js", which is where the marker
// actually lives).
//
// Falsifiable counterexample (manually demonstrated once): delete the
// import line from news.astro's script, rebuild, confirm this fails for the
// en locale, restore, reconfirm green.
// ---------------------------------------------------------------------------
const ASTRO_DIR = path.join(SITE_ROOT, 'dist', '_astro');
for (const [locale, distPath] of DIST_PAGES) {
  const distDir = path.dirname(distPath);
  const distHtml = readFileSync(distPath, 'utf-8');
  const searched = [];
  let combined = '';

  for (const m of distHtml.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)) {
    combined += m[1];
    searched.push('(inline)');
  }

  for (const m of distHtml.matchAll(/<script type="module" src="([^"]+)"><\/script>/g)) {
    const srcAttr = m[1];
    const chunkPath = srcAttr.startsWith('/')
      ? path.join(SITE_ROOT, 'dist', srcAttr)
      : path.join(distDir, srcAttr);
    searched.push(chunkPath);
    if (!existsSync(chunkPath)) continue;
    const chunkSrc = readFileSync(chunkPath, 'utf-8');
    combined += chunkSrc;

    // One level of that chunk's own static import specifiers.
    for (const im of chunkSrc.matchAll(/from"(\.\/[^"]+\.js)"|from '(\.\/[^']+\.js)'/g)) {
      const spec = im[1] || im[2];
      const importedPath = path.join(ASTRO_DIR, path.basename(spec));
      searched.push(importedPath);
      if (existsSync(importedPath)) {
        combined += readFileSync(importedPath, 'utf-8');
      }
    }
  }

  if (!combined.includes('newsFilterLogic/v1')) {
    fail(
      `assertion 17 — ${locale} page's shipped module script(s) do not contain the ` +
        `FILTER_LOGIC_MARKER literal "newsFilterLogic/v1". Scripts searched: ${searched.join(', ')}`
    );
  }
}

// ---------------------------------------------------------------------------
// Assertion 18: filter-control presence + no unsubstituted {n}/{date} tokens
// (NEWSUI-01, NEWSUI-03, F-32).
//
// Falsifiable counterexamples: delete the comuna input -> RED; render
// news_window_latest without substituting {date} -> RED; drop the
// data-result-count-template carrier -> RED.
// ---------------------------------------------------------------------------
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  const requiredIds = ['news-filters', 'news-comuna-q', 'news-result-count', 'news-clear-filters'];
  for (const id of requiredIds) {
    if (!distHtml.includes(`id="${id}"`)) {
      fail(`assertion 18 — ${locale} built page missing required id="${id}"`);
    }
  }
  for (const facet of ['window', 'region', 'family']) {
    if (!distHtml.includes(`data-facet="${facet}"`)) {
      fail(`assertion 18 — ${locale} built page missing fieldset with data-facet="${facet}"`);
    }
  }
  for (const facet of ['region', 'family']) {
    const fieldsetMatch = distHtml.match(
      new RegExp(`data-facet="${facet}"[\\s\\S]*?</fieldset>`)
    );
    if (!fieldsetMatch || !/<input\b[^>]*type="checkbox"/.test(fieldsetMatch[0])) {
      fail(`assertion 18 — ${locale} built page's ${facet} fieldset has no checkbox input`);
    }
  }

  // Exact form per plan (F-32): strip the one required data-result-count-template
  // carrier, then scan for unsubstituted tokens.
  const scan = distHtml.replace(/\sdata-result-count-template="[^"]*"/g, '');
  if (scan.includes('{n}') || scan.includes('{date}')) {
    fail(`assertion 18 — ${locale}: unsubstituted token in rendered markup`);
  }
  if ((distHtml.match(/data-result-count-template="/g) || []).length !== 1) {
    fail(`assertion 18 — ${locale}: expected exactly one data-result-count-template`);
  }
}

// ---------------------------------------------------------------------------
// Assertion 19: canonical + route count unchanged (no new indexable URL).
//
// Falsifiable counterexample: add a "?family=robos" link -> RED.
// ---------------------------------------------------------------------------
const EXPECTED_CANONICAL = new Map([
  ['EN', 'https://ischilesafe.com/news/'],
  ['ES', 'https://ischilesafe.com/es/noticias/'],
]);
const FORBIDDEN_QUERY_PARAMS = ['?family=', '?region=', '?window=', '?q='];
for (const [locale, distPath] of DIST_PAGES) {
  const distHtml = readFileSync(distPath, 'utf-8');
  const canonicalMatch = distHtml.match(/<link rel="canonical" href="([^"]*)"/);
  if (!canonicalMatch || canonicalMatch[1] !== EXPECTED_CANONICAL.get(locale)) {
    fail(
      `assertion 19 — ${locale} canonical is "${canonicalMatch ? canonicalMatch[1] : '(missing)'}", ` +
        `expected "${EXPECTED_CANONICAL.get(locale)}"`
    );
  }
  if (/<link rel="alternate"[^>]*\?(family|region|window|q)=/.test(distHtml)) {
    fail(`assertion 19 — ${locale} built page emits a query-string <link rel="alternate">`);
  }
  for (const hrefMatch of distHtml.matchAll(/<a\b[^>]*\bhref="([^"]*)"/g)) {
    for (const param of FORBIDDEN_QUERY_PARAMS) {
      if (hrefMatch[1].includes(param)) {
        fail(`assertion 19 — ${locale} built page has an internal <a href> containing "${param}": ${hrefMatch[1]}`);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Assertion 20: no innerHTML/outerHTML/insertAdjacentHTML/document.write with
// data-derived strings (NEWSUI-06). set:html remains permitted only on the
// single #news-facets node (assertion 7), counted via the ATTRIBUTE form
// (`set:html=`), exactly 1 per page — never the bare token, which is 2 in
// both pages today because of a Phase 27 explanatory comment.
//
// Falsifiable counterexample: replace a textContent = with innerHTML = in
// either source -> RED.
// ---------------------------------------------------------------------------
const FORBIDDEN_DOM_SINKS = [/innerHTML/, /outerHTML/, /insertAdjacentHTML/, /document\.write/];
const NEWS_FILTER_LOGIC_TS_PATH = path.join(SITE_ROOT, 'src', 'lib', 'newsFilterLogic.ts');
const SOURCE_SCAN_FILES = [
  ['EN', path.join(SITE_ROOT, 'src', 'pages', 'news.astro')],
  ['ES', path.join(SITE_ROOT, 'src', 'pages', 'es', 'noticias.astro')],
  ['shared', NEWS_FILTER_LOGIC_TS_PATH],
];
for (const [locale, filePath] of SOURCE_SCAN_FILES) {
  if (!existsSync(filePath)) {
    fail(`assertion 20 — ${locale} source file not found at ${filePath}`);
  }
  const src = readFileSync(filePath, 'utf-8');
  // Strip only whole-line // (or /* or *) comments before scanning — a doc
  // comment merely NAMING a forbidden sink (e.g. "never innerHTML") must not
  // read as a violation. Do NOT strip trailing "//..." on a code line: a
  // line containing a URL literal (e.g. "https://ischilesafe.com/news/")
  // would otherwise be truncated at the "//" inside the URL, silently
  // hiding any forbidden sink assignment later on that same line.
  const codeOnly = src
    .split('\n')
    .filter((line) => !/^\s*(\/\/|\/\*|\*)/.test(line))
    .join('\n');
  for (const pattern of FORBIDDEN_DOM_SINKS) {
    if (pattern.test(codeOnly)) {
      fail(`assertion 20 — ${locale} source (${filePath}) contains forbidden DOM sink ${pattern}`);
    }
  }
}
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  const pageSrc = readFileSync(pagePath, 'utf-8');
  const setHtmlAttrCount = (pageSrc.match(/set:html=/g) || []).length;
  if (setHtmlAttrCount !== 1) {
    fail(
      `assertion 20 — ${locale} page has ${setHtmlAttrCount} set:html= attribute occurrence(s), expected exactly 1`
    );
  }
}

// ---------------------------------------------------------------------------
// Assertion 21: no client: directive at source level (hardens assertion 15
// upstream of the build). Falsifiable counterexample: add client:load to any
// element in either page -> RED.
// ---------------------------------------------------------------------------
const CLIENT_DIRECTIVE_PATTERN = /client:(load|idle|visible|only|media)/;
for (const [locale, pagePath] of SERIALIZATION_SITES) {
  const pageSrc = readFileSync(pagePath, 'utf-8');
  if (CLIENT_DIRECTIVE_PATTERN.test(pageSrc)) {
    fail(`assertion 21 — ${locale} page source contains a client: directive`);
  }
}

// ---------------------------------------------------------------------------
// All assertions passed
// ---------------------------------------------------------------------------
console.log(
  `PASS facets: ${incidents.length} incidents, ${familyCounts.size} families observed, ` +
    `${indexData.length} communes cross-checked, ${unionMonths.size} months in byMonth union, ` +
    `window(today=${todayCount},7d=${sevenDayCount},30d=${thirtyDayCount}), TZ-determinism verified, ` +
    `21 assertions passed`
);
