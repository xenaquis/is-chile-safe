/**
 * news-freshness-fixtures.mjs — Sep-4-frozen vs fresh real-build harness
 * (FRESH-01/FRESH-03 close-gate proof).
 *
 * NOT registered in all.mjs — it costs two full `astro build`s. Run by
 * 35-07's close gate.
 *
 * Deliberately independent of news-freshness.lib.mjs (T-35-13): every
 * assertion here is a hardcoded absolute outcome read directly off the
 * built HTML with plain string search, not the shared helper's verdict —
 * so a bug shared between the page code and the lib cannot make this
 * harness lie.
 *
 * Steps:
 * 1. `node scripts/sync-data.mjs` restores the baseline public/data copy.
 * 2. Build two fixtures in memory: FROZEN (the committed Sep-4 fixture) and
 *    FRESH (a deep copy shifted so its max date is today UTC, with a
 *    recent last_new_incident_at).
 * 3. For each fixture, in order [frozen, fresh]: overwrite
 *    site/public/data/incidents/current.json, run a real `astro build`
 *    into an OS-temp outDir (never OneDrive — see the project memory
 *    "OneDrive build artifacts desync"), and assert hardcoded outcomes.
 * 4. Restore the public copy and clean up temp dirs in `finally`.
 *
 * Env overrides: none (this harness owns its own paths).
 *
 * Exit codes:
 *   0 — both fixtures satisfy every assertion
 *   1 — any assertion failed, or a build/sync step failed
 *
 * Usage:
 *   node scripts/validate/news-freshness-fixtures.mjs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');

const SYNC_DATA_SCRIPT = path.join(SITE_ROOT, 'scripts', 'sync-data.mjs');
const ASTRO_BIN = path.join(SITE_ROOT, 'node_modules', 'astro', 'bin', 'astro.mjs');
const NEWS_FRESHNESS_SCRIPT = path.join(__dirname, 'news-freshness.mjs');
const PUBLIC_CURRENT_JSON = path.join(SITE_ROOT, 'public', 'data', 'incidents', 'current.json');
const FROZEN_FIXTURE_PATH = path.join(__dirname, 'fixtures', 'news-current-frozen-2026-09-04.json');
const META_INDEX_PATH = path.join(REPO_ROOT, 'data', 'cead', 'meta', 'index.json');

const errors = [];
const outDirs = [];
const tmpFiles = [];

function runSyncData() {
  const result = spawnSync(process.execPath, [SYNC_DATA_SCRIPT], { cwd: SITE_ROOT, stdio: 'inherit' });
  if (result.status !== 0) {
    console.error('FAIL news-freshness-fixtures: sync-data.mjs exited non-zero');
    process.exit(1);
  }
}

function addDaysStr(dateStr, days) {
  const ms = Date.parse(dateStr + 'T00:00:00Z') + days * 86400000;
  return new Date(ms).toISOString().slice(0, 10);
}

function todayUtc() {
  return new Date().toISOString().slice(0, 10);
}

// Independent of news-freshness.lib.mjs on purpose (T-35-13): plain string
// search, no regex, no shared parsing code.
function extractCnewsSection(html) {
  const classIdx = html.indexOf('class="cnews-section"');
  if (classIdx === -1) return null;
  const tagStart = html.lastIndexOf('<section', classIdx);
  const closeIdx = html.indexOf('</section>', classIdx);
  if (tagStart === -1 || closeIdx === -1) return null;
  return html.slice(tagStart, closeIdx + '</section>'.length);
}

function countOccurrences(haystack, needle) {
  let count = 0;
  let idx = 0;
  while ((idx = haystack.indexOf(needle, idx)) !== -1) {
    count++;
    idx += needle.length;
  }
  return count;
}

function readOrNull(p) {
  return existsSync(p) ? readFileSync(p, 'utf-8') : null;
}

// ---------------------------------------------------------------------------
// Step 1: restore baseline
// ---------------------------------------------------------------------------
runSyncData();

// ---------------------------------------------------------------------------
// Step 2: build fixtures
// ---------------------------------------------------------------------------
const frozen = JSON.parse(readFileSync(FROZEN_FIXTURE_PATH, 'utf-8'));

const today = todayUtc();
const k = Math.round(
  (Date.parse(today + 'T00:00:00Z') - Date.parse('2026-09-04T00:00:00Z')) / 86400000
);

const fresh = {
  generated: new Date().toISOString(),
  window_days: frozen.window_days,
  last_new_incident_at: new Date(Date.now() - 3600000).toISOString(),
  incidents: frozen.incidents.map((inc) => ({ ...inc, date: addDaysStr(inc.date, k) })),
};

const meta = JSON.parse(readFileSync(META_INDEX_PATH, 'utf-8'));
const cutToSlug = new Map(meta.map((m) => [String(m.cut), m.slug]));
const fixtureCuts = [...new Set(frozen.incidents.map((inc) => String(inc.cut)))];
const fixtureSlugs = fixtureCuts.map((cut) => cutToSlug.get(cut)).filter((s) => s !== undefined);

const FIXTURES = [
  { name: 'frozen', data: frozen },
  { name: 'fresh', data: fresh },
];

try {
  for (const fixture of FIXTURES) {
    const { name, data } = fixture;
    console.log(`\n=== Building fixture: ${name} ===`);

    writeFileSync(PUBLIC_CURRENT_JSON, JSON.stringify(data, null, 2), 'utf-8');

    const fixturePayloadTmp = path.join(os.tmpdir(), `ics-fresh35-${name}-current.json`);
    writeFileSync(fixturePayloadTmp, JSON.stringify(data), 'utf-8');
    tmpFiles.push(fixturePayloadTmp);

    const outDir = path.join(os.tmpdir(), `ics-fresh35-${name}`);
    rmSync(outDir, { recursive: true, force: true });
    outDirs.push(outDir);

    const buildResult = spawnSync(process.execPath, [ASTRO_BIN, 'build', '--outDir', outDir], {
      cwd: SITE_ROOT,
      env: { ...process.env, ROLLOUT_ALL: 'true' },
      stdio: 'inherit',
      timeout: 900000,
    });
    if (buildResult.status !== 0) {
      errors.push(`${name}: astro build exited non-zero (status ${buildResult.status})`);
      continue;
    }

    // -------------------------------------------------------------------
    // Read pages
    // -------------------------------------------------------------------
    const homeEn = readOrNull(path.join(outDir, 'index.html'));
    const homeEs = readOrNull(path.join(outDir, 'es', 'index.html'));
    const newsEn = readOrNull(path.join(outDir, 'news', 'index.html'));
    const newsEs = readOrNull(path.join(outDir, 'es', 'noticias', 'index.html'));

    if (!homeEn) errors.push(`${name}: dist/index.html missing`);
    if (!homeEs) errors.push(`${name}: dist/es/index.html missing`);
    if (!newsEn) errors.push(`${name}: dist/news/index.html missing`);
    if (!newsEs) errors.push(`${name}: dist/es/noticias/index.html missing`);

    const pulseStaleEn = homeEn ? countOccurrences(homeEn, 'class="pulse-stale"') : -1;
    const pulseStaleEs = homeEs ? countOccurrences(homeEs, 'class="pulse-stale"') : -1;
    const noticeEn = newsEn ? countOccurrences(newsEn, 'class="news-stale-notice"') : -1;
    const noticeEs = newsEs ? countOccurrences(newsEs, 'class="news-stale-notice"') : -1;

    let caveatedCount = 0;
    let checkedEn = 0;
    let checkedEs = 0;

    if (name === 'frozen') {
      if (pulseStaleEn !== 1) errors.push(`frozen: expected exactly 1 pulse-stale on EN home, got ${pulseStaleEn}`);
      if (pulseStaleEs !== 1) errors.push(`frozen: expected exactly 1 pulse-stale on ES home, got ${pulseStaleEs}`);
      if (noticeEn !== 1) errors.push(`frozen: expected exactly 1 news-stale-notice on EN news, got ${noticeEn}`);
      if (noticeEs !== 1) errors.push(`frozen: expected exactly 1 news-stale-notice on ES news, got ${noticeEs}`);

      if (newsEn && !newsEn.includes('data-latest-incident="2026-09-04"')) {
        errors.push('frozen: EN news page missing data-latest-incident="2026-09-04"');
      }
      if (newsEs && !newsEs.includes('data-latest-incident="2026-09-04"')) {
        errors.push('frozen: ES news page missing data-latest-incident="2026-09-04"');
      }
      if (newsEn && !newsEn.includes('Latest incident: September 4, 2026')) {
        errors.push('frozen: EN news page missing "Latest incident: September 4, 2026"');
      }
      if (newsEs && !newsEs.includes('Último incidente: 4 de septiembre de 2026')) {
        errors.push('frozen: ES news page missing "Último incidente: 4 de septiembre de 2026"');
      }

      for (const slug of fixtureSlugs) {
        const enPath = path.join(outDir, 'commune', slug, 'index.html');
        const esPath = path.join(outDir, 'es', 'comuna', slug, 'index.html');
        const enHtml = readOrNull(enPath);
        const esHtml = readOrNull(esPath);

        if (enHtml) {
          const section = extractCnewsSection(enHtml);
          if (section) {
            checkedEn++;
            if (!section.includes('data-news-stale="true"')) {
              errors.push(`frozen: ${slug} (en) cnews-section is not data-news-stale="true"`);
            }
            if (!section.includes('Earlier Incidents in the News')) {
              errors.push(`frozen: ${slug} (en) cnews-section missing the stale heading`);
            } else {
              caveatedCount++;
            }
          }
        }
        if (esHtml) {
          const section = extractCnewsSection(esHtml);
          if (section) {
            checkedEs++;
            if (!section.includes('data-news-stale="true"')) {
              errors.push(`frozen: ${slug} (es) cnews-section is not data-news-stale="true"`);
            }
            if (!section.includes('Incidentes Anteriores en la Prensa')) {
              errors.push(`frozen: ${slug} (es) cnews-section missing the stale heading`);
            }
          }
        }
      }
      if (checkedEn === 0) errors.push('frozen: 0 fixture-commune EN cnews-sections found — nothing was checked');
      if (checkedEs === 0) errors.push('frozen: 0 fixture-commune ES cnews-sections found — nothing was checked');
    } else {
      if (pulseStaleEn !== 0) errors.push(`fresh: expected 0 pulse-stale on EN home, got ${pulseStaleEn}`);
      if (pulseStaleEs !== 0) errors.push(`fresh: expected 0 pulse-stale on ES home, got ${pulseStaleEs}`);
      if (noticeEn !== 0) errors.push(`fresh: expected 0 news-stale-notice on EN news, got ${noticeEn}`);
      if (noticeEs !== 0) errors.push(`fresh: expected 0 news-stale-notice on ES news, got ${noticeEs}`);

      if (newsEn && !newsEn.includes(`data-latest-incident="${today}"`)) {
        errors.push(`fresh: EN news page missing data-latest-incident="${today}"`);
      }
      if (newsEs && !newsEs.includes(`data-latest-incident="${today}"`)) {
        errors.push(`fresh: ES news page missing data-latest-incident="${today}"`);
      }

      for (const slug of fixtureSlugs) {
        const enPath = path.join(outDir, 'commune', slug, 'index.html');
        const esPath = path.join(outDir, 'es', 'comuna', slug, 'index.html');
        const enHtml = readOrNull(enPath);
        const esHtml = readOrNull(esPath);

        if (enHtml) {
          const section = extractCnewsSection(enHtml);
          if (section) {
            checkedEn++;
            if (!section.includes('data-news-stale="false"')) {
              errors.push(`fresh: ${slug} (en) cnews-section is not data-news-stale="false"`);
            }
            if (!section.includes('Recent Incidents in the News')) {
              errors.push(`fresh: ${slug} (en) cnews-section missing the normal heading`);
            }
          }
        }
        if (esHtml) {
          const section = extractCnewsSection(esHtml);
          if (section) {
            checkedEs++;
            if (!section.includes('data-news-stale="false"')) {
              errors.push(`fresh: ${slug} (es) cnews-section is not data-news-stale="false"`);
            }
            if (!section.includes('Incidentes Recientes en la Prensa')) {
              errors.push(`fresh: ${slug} (es) cnews-section missing the normal heading`);
            }
          }
        }
      }
      if (checkedEn === 0) errors.push('fresh: 0 fixture-commune EN cnews-sections found — nothing was checked');
      if (checkedEs === 0) errors.push('fresh: 0 fixture-commune ES cnews-sections found — nothing was checked');
      caveatedCount = 0;
    }

    // -------------------------------------------------------------------
    // Cross-check: validator #18 must exit 0 against this exact fixture/dist pair
    // -------------------------------------------------------------------
    const validatorResult = spawnSync(
      process.execPath,
      [NEWS_FRESHNESS_SCRIPT],
      {
        cwd: SITE_ROOT,
        env: { ...process.env, NEWS_FRESHNESS_DIST: outDir, NEWS_FRESHNESS_CURRENT_JSON: fixturePayloadTmp },
        stdio: 'inherit',
      }
    );
    if (validatorResult.status !== 0) {
      errors.push(`${name}: news-freshness.mjs exited non-zero against this fixture/dist pair`);
    }

    fixture._caveatedCount = caveatedCount;
    fixture._checkedEn = checkedEn;
  }
} finally {
  // Step 5: restore + cleanup, unconditionally.
  runSyncData();
  for (const dir of outDirs) rmSync(dir, { recursive: true, force: true });
  for (const f of tmpFiles) rmSync(f, { force: true });
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
if (errors.length > 0) {
  console.error(`\nFAIL news-freshness-fixtures: ${errors.length} error(s)`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

const frozenFx = FIXTURES[0];
const freshFx = FIXTURES[1];
console.log(
  `\nPASS news-freshness-fixtures: frozen → notice EN/ES present, ${frozenFx._caveatedCount} communes caveated; ` +
  `fresh → notice absent, ${freshFx._checkedEn} communes normal`
);
