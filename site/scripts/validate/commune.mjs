/**
 * commune.mjs — Validate commune page HTML output + prose self-test.
 *
 * Modes:
 *   --self-test : Run pure TypeScript engine checks (no dist/ needed).
 *                 Asserts proseEngine produces 500+ words, no forbidden terms,
 *                 and Santiago (13101) reads ABOVE national average.
 *   (default)   : Inspect dist/ HTML files and assert 500+ words + 5 dimensions.
 *
 * Exit non-zero on first failure.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// Forbidden terms per D-05 Sober Language Contract
const FORBIDDEN_TERMS = [
  'zona peligrosa',
  'comuna peligrosa',
  'ranking definitivo',
  'zona segura garantizada',
  'la más segura',
  'the safest',
  'dangerous zone',
  'dangerous commune',
  'definitive ranking',
  'guaranteed safe',
];

// ---------------------------------------------------------------------------
// Strip HTML tags
// ---------------------------------------------------------------------------
function stripTags(html) {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function wordCount(text) {
  return text.split(/\s+/).filter(Boolean).length;
}

// ---------------------------------------------------------------------------
// Self-test mode: run proseEngine directly (no dist needed)
// ---------------------------------------------------------------------------
async function runSelfTest() {
  console.log('commune: --self-test mode\n');

  // We need to run TS via tsx/ts-node or use the compiled output.
  // Since the Astro project has tsx available via npx, we spawn a small
  // inline script via tsx to access the TypeScript modules.
  const { spawnSync } = await import('node:child_process');

  const selfTestScript = `
import { buildCommuneProse } from './src/lib/proseEngine.ts';
import { loadCommune, loadNationalAverage } from './src/lib/data.ts';

const FORBIDDEN = ${JSON.stringify(FORBIDDEN_TERMS)};

function wordCount(s) {
  return s.split(/\\s+/).filter(Boolean).length;
}

const commune = loadCommune('13101');
const nationalAvg = loadNationalAverage();
const rate = commune.series.find(s => s.year === commune.latestCompleteYear && !s.partial)?.rate_per_100k ?? 0;

console.log('Santiago rate:', rate);
console.log('National avg:', nationalAvg);

const vsNationalPct = nationalAvg > 0 ? ((rate - nationalAvg) / nationalAvg) * 100 : 0;
console.log('vs-national %:', vsNationalPct.toFixed(2));

// PITFALL 1 guard: Santiago must be ABOVE national (positive %), not ~-99%
if (vsNationalPct <= 0) {
  console.error('FAIL: Santiago vs-national is', vsNationalPct.toFixed(2) + '% — expected positive (above national mean). Pitfall 1 not fixed.');
  process.exit(1);
}
console.log('PASS: Santiago is', vsNationalPct.toFixed(2) + '% above national mean (Pitfall 1 guard passed)');

// EN prose
const enProse = buildCommuneProse(commune, 'en');
const enWords = wordCount(enProse);
console.log('EN word count:', enWords);
if (enWords < 500) {
  console.error('FAIL: EN prose has', enWords, 'words (need 500+)');
  process.exit(1);
}
console.log('PASS: EN prose has 500+ words');

for (const term of FORBIDDEN) {
  if (enProse.toLowerCase().includes(term.toLowerCase())) {
    console.error('FAIL: EN prose contains forbidden term:', term);
    process.exit(1);
  }
}
console.log('PASS: EN prose contains no forbidden terms');

// ES prose
const esProse = buildCommuneProse(commune, 'es');
const esWords = wordCount(esProse);
console.log('ES word count:', esWords);
if (esWords < 500) {
  console.error('FAIL: ES prose has', esWords, 'words (need 500+)');
  process.exit(1);
}
console.log('PASS: ES prose has 500+ words');

for (const term of FORBIDDEN) {
  if (esProse.toLowerCase().includes(term.toLowerCase())) {
    console.error('FAIL: ES prose contains forbidden term:', term);
    process.exit(1);
  }
}
console.log('PASS: ES prose contains no forbidden terms');

// Check both prose contain all 5 dimension markers
function checkDimensions(prose, locale) {
  const lower = prose.toLowerCase();
  const checks = [
    { name: 'vs-national', patterns: ['national average', 'promedio nacional', 'national mean', 'media nacional'] },
    { name: 'vs-regional', patterns: ['regional average', 'promedio regional', 'regional mean', 'media per cápita regional', 'media regional', 'regional per-capita'] },
    { name: 'trend', patterns: ['rising', 'declining', 'stable', 'al alza', 'a la baja', 'estable', 'tendencia'] },
    { name: 'family', patterns: ['crime', 'incidence', 'category', 'categoría', 'familia', 'propiedad', 'property'] },
    { name: 'comparable', patterns: ['comparable', 'comparable commune', 'comuna comparable'] },
  ];
  for (const check of checks) {
    if (!check.patterns.some(p => lower.includes(p))) {
      console.error('FAIL: ' + locale + ' prose missing dimension:', check.name);
      process.exit(1);
    }
  }
  console.log('PASS: ' + locale + ' prose contains all 5 dimensions');
}

checkDimensions(enProse, 'EN');
checkDimensions(esProse, 'ES');

console.log('\\nAll self-tests passed.');
`;

  const result = spawnSync(
    'node',
    ['--input-type=module', '--experimental-strip-types'],
    {
      input: selfTestScript,
      cwd: SITE_ROOT,
      stdio: ['pipe', 'inherit', 'inherit'],
      env: { ...process.env, NODE_NO_WARNINGS: '1' },
    }
  );

  if (result.status !== 0) {
    // Try with tsx fallback
    console.log('Node strip-types failed, trying tsx...');
    const tsxResult = spawnSync(
      'npx',
      ['--yes=false', 'tsx', '--eval', selfTestScript.replace(/import\s+/g, 'const ')],
      {
        cwd: SITE_ROOT,
        stdio: 'inherit',
        env: { ...process.env },
      }
    );

    // If both fail, try via a temp file with tsx
    if (tsxResult.status !== 0) {
      const { writeFileSync, unlinkSync } = await import('node:fs');
      const tmpFile = path.join(SITE_ROOT, '__prose_selftest_tmp.mts');
      writeFileSync(tmpFile, selfTestScript, 'utf-8');
      try {
        const tsxFileResult = spawnSync(
          'npx',
          ['--yes=false', 'tsx', tmpFile],
          {
            cwd: SITE_ROOT,
            stdio: 'inherit',
            env: { ...process.env },
          }
        );
        if (tsxFileResult.status !== 0) {
          process.exit(1);
        }
      } finally {
        try { unlinkSync(tmpFile); } catch {}
      }
    }
  }

  console.log('\ncommune.mjs --self-test: PASSED');
}

// ---------------------------------------------------------------------------
// Default mode: validate dist/ HTML output
// ---------------------------------------------------------------------------
async function runDistValidation() {
  const enDir = path.join(DIST_DIR, 'commune');
  const esDir = path.join(DIST_DIR, 'es', 'comuna');

  if (!existsSync(enDir)) {
    console.error('FAIL: dist/commune directory not found — run npm run build first');
    process.exit(1);
  }
  if (!existsSync(esDir)) {
    console.error('FAIL: dist/es/comuna directory not found — run npm run build first');
    process.exit(1);
  }

  const enSlugs = readdirSync(enDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const esSlugs = readdirSync(esDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  console.log(`Found ${enSlugs.length} EN commune dirs, ${esSlugs.length} ES commune dirs`);

  let failures = 0;

  // Validate each EN page
  for (const slug of enSlugs) {
    const htmlPath = path.join(enDir, slug, 'index.html');
    if (!existsSync(htmlPath)) {
      console.error(`FAIL: missing index.html for EN commune ${slug}`);
      failures++;
      continue;
    }

    const html = readFileSync(htmlPath, 'utf-8');
    const text = stripTags(html);
    const words = wordCount(text);

    if (words < 500) {
      console.error(`FAIL: EN commune ${slug} has ${words} words (need 500+)`);
      failures++;
    }

    // Check 5 dimension markers in HTML
    const lower = html.toLowerCase();
    const dimensionChecks = [
      { name: 'vs-national callout', patterns: ['national average', 'vs-national', 'above national', 'below national', 'national average'] },
      { name: 'vs-regional callout', patterns: ['regional average', 'vs-regional', 'above regional', 'below regional'] },
      { name: 'trend chip', patterns: ['trend', 'rising', 'declining', 'stable'] },
      { name: 'family breakdown heading', patterns: ['incidence by', 'crime category', 'family breakdown'] },
      { name: 'comparable commune', patterns: ['comparable commune', 'comparable-commune'] },
    ];

    for (const check of dimensionChecks) {
      if (!check.patterns.some((p) => lower.includes(p))) {
        console.error(`FAIL: EN commune ${slug} missing dimension: ${check.name}`);
        failures++;
      }
    }

    // Check for forbidden terms
    for (const term of FORBIDDEN_TERMS) {
      if (lower.includes(term.toLowerCase())) {
        console.error(`FAIL: EN commune ${slug} contains forbidden term: "${term}"`);
        failures++;
      }
    }

    // Assert ENUSC VHDV module presence (Phase 23 VL-03 / VL-04)
    // Every commune page must have EITHER enusc-vhdv-section OR enusc-no-estimate
    const hasVhdvSection = html.includes('enusc-vhdv-section');
    const hasNoEstimate = html.includes('enusc-no-estimate');
    if (!hasVhdvSection && !hasNoEstimate) {
      console.error(`FAIL: ${htmlPath} — missing both enusc-vhdv-section and enusc-no-estimate`);
      failures++;
    }
  }

  // Validate each ES page
  for (const slug of esSlugs) {
    const htmlPath = path.join(esDir, slug, 'index.html');
    if (!existsSync(htmlPath)) {
      console.error(`FAIL: missing index.html for ES commune ${slug}`);
      failures++;
      continue;
    }

    const html = readFileSync(htmlPath, 'utf-8');
    const text = stripTags(html);
    const words = wordCount(text);

    if (words < 500) {
      console.error(`FAIL: ES commune ${slug} has ${words} words (need 500+)`);
      failures++;
    }

    // Forbidden term check on ES pages
    const lower = html.toLowerCase();
    for (const term of FORBIDDEN_TERMS) {
      if (lower.includes(term.toLowerCase())) {
        console.error(`FAIL: ES commune ${slug} contains forbidden term: "${term}"`);
        failures++;
      }
    }

    // Assert ENUSC VHDV module presence (Phase 23 VL-03 / VL-04)
    const hasVhdvSection = html.includes('enusc-vhdv-section');
    const hasNoEstimate = html.includes('enusc-no-estimate');
    if (!hasVhdvSection && !hasNoEstimate) {
      console.error(`FAIL: ${htmlPath} — missing both enusc-vhdv-section and enusc-no-estimate`);
      failures++;
    }
  }

  if (failures > 0) {
    console.error(`\ncommune validation: FAILED (${failures} failure(s))`);
    process.exit(1);
  }

  console.log('\ncommune.mjs: PASSED — all commune pages validated');
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
if (args.includes('--self-test')) {
  await runSelfTest();
} else {
  await runDistValidation();
}
