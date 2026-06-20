/**
 * spine.mjs — IA spine validator for Phase 12 cross-link reciprocity.
 *
 * Assertions (run against an existing dist/ — does NOT rebuild):
 *
 *   F (map-spoke targets exist):    dist/map/index.html AND dist/es/mapa/index.html exist
 *   G (rankings pages exist):       dist/rankings/index.html AND dist/es/rankings/index.html exist
 *   H (rankings in sitemap):        dist/sitemap-0.xml includes /rankings/ AND /es/rankings/ <loc>
 *   I (breadcrumb reciprocity):     every dist/commune/{slug}/index.html contains href="/communes/"
 *                                   every dist/es/comuna/{slug}/index.html contains href="/es/comunas/"
 *   J (map-spoke on ficha):         every commune page HTML contains /map/?cut= (EN) or /es/mapa/?cut= (ES)
 *   K (home single H1):             dist/index.html and dist/es/index.html each have exactly one <h1
 *   L (rankings nav site-wide):     sample pages contain href="/rankings/" (EN) / href="/es/rankings/" (ES)
 *   M (comparator-spoke on ficha): every commune page HTML contains href="/compare/" (EN) or href="/es/comparar/" (ES)
 *
 * Usage:
 *   node scripts/validate/spine.mjs
 *
 * Exit code: 0 if all assertions pass, 1 if any fail.
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

let failures = 0;

// ---------------------------------------------------------------------------
// Helper: recursively collect all .html file paths under a directory.
// ---------------------------------------------------------------------------
function collectHtmlFiles(dir) {
  if (!existsSync(dir)) return [];
  const result = [];
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...collectHtmlFiles(full));
    } else if (entry.isFile() && entry.name.endsWith('.html')) {
      result.push(full);
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// ASSERTION F: map-spoke targets exist in dist
// dist/map/index.html AND dist/es/mapa/index.html must exist (the pages that
// commune map-spoke links point to).
// ---------------------------------------------------------------------------
const mapEnPage = path.join(DIST_DIR, 'map', 'index.html');
const mapEsPage = path.join(DIST_DIR, 'es', 'mapa', 'index.html');

if (!existsSync(mapEnPage)) {
  console.error(`FAIL [F] map-spoke: dist/map/index.html not found`);
  failures++;
} else {
  console.log(`PASS [F] map-spoke: dist/map/index.html exists`);
}

if (!existsSync(mapEsPage)) {
  console.error(`FAIL [F] map-spoke: dist/es/mapa/index.html not found`);
  failures++;
} else {
  console.log(`PASS [F] map-spoke: dist/es/mapa/index.html exists`);
}

// ---------------------------------------------------------------------------
// ASSERTION G: rankings pages exist in dist
// ---------------------------------------------------------------------------
const rankingsEnPage = path.join(DIST_DIR, 'rankings', 'index.html');
const rankingsEsPage = path.join(DIST_DIR, 'es', 'rankings', 'index.html');

if (!existsSync(rankingsEnPage)) {
  console.error(`FAIL [G] rankings: dist/rankings/index.html not found`);
  failures++;
} else {
  console.log(`PASS [G] rankings: dist/rankings/index.html exists`);
}

if (!existsSync(rankingsEsPage)) {
  console.error(`FAIL [G] rankings: dist/es/rankings/index.html not found`);
  failures++;
} else {
  console.log(`PASS [G] rankings: dist/es/rankings/index.html exists`);
}

// ---------------------------------------------------------------------------
// ASSERTION H: rankings in sitemap
// dist/sitemap-0.xml <loc> entries include /rankings/ AND /es/rankings/
// ---------------------------------------------------------------------------
const SITEMAP_PATH = path.join(DIST_DIR, 'sitemap-0.xml');

if (!existsSync(SITEMAP_PATH)) {
  console.error(`FAIL [H] rankings-sitemap: dist/sitemap-0.xml not found`);
  failures++;
} else {
  const sitemapContent = readFileSync(SITEMAP_PATH, 'utf-8');
  const LOC_RE = /<loc>([^<]+)<\/loc>/g;

  let hasEnRankings = false;
  let hasEsRankings = false;

  let lm;
  LOC_RE.lastIndex = 0;
  while ((lm = LOC_RE.exec(sitemapContent)) !== null) {
    const url = lm[1];
    if (/\/rankings\//.test(url) && !/\/es\//.test(url)) hasEnRankings = true;
    if (/\/es\/rankings\//.test(url)) hasEsRankings = true;
  }

  if (hasEnRankings) {
    console.log(`PASS [H] rankings-sitemap: /rankings/ found in sitemap`);
  } else {
    console.error(`FAIL [H] rankings-sitemap: /rankings/ not found in dist/sitemap-0.xml`);
    failures++;
  }

  if (hasEsRankings) {
    console.log(`PASS [H] rankings-sitemap: /es/rankings/ found in sitemap`);
  } else {
    console.error(`FAIL [H] rankings-sitemap: /es/rankings/ not found in dist/sitemap-0.xml`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// ASSERTION I: breadcrumb reciprocity
// Every dist/commune/*/index.html must contain href="/communes/"
// Every dist/es/comuna/*/index.html must contain href="/es/comunas/"
// ---------------------------------------------------------------------------
const enCommuneDir = path.join(DIST_DIR, 'commune');
const esComunaDir = path.join(DIST_DIR, 'es', 'comuna');

if (!existsSync(enCommuneDir)) {
  console.error(`FAIL [I] breadcrumb: dist/commune/ not found`);
  failures++;
} else {
  const enCommuneDirs = readdirSync(enCommuneDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const enOffenders = [];
  for (const slug of enCommuneDirs) {
    const htmlPath = path.join(enCommuneDir, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!content.includes('href="/communes/"')) {
        enOffenders.push(slug);
        if (enOffenders.length >= 5) break;
      }
    }
  }

  if (enOffenders.length === 0) {
    console.log(`PASS [I] breadcrumb: all EN commune pages contain href="/communes/"`);
  } else {
    console.error(`FAIL [I] breadcrumb: ${enOffenders.length}+ EN commune pages missing href="/communes/": ${enOffenders.join(', ')}`);
    failures++;
  }
}

if (!existsSync(esComunaDir)) {
  console.error(`FAIL [I] breadcrumb: dist/es/comuna/ not found`);
  failures++;
} else {
  const esComunaDirs = readdirSync(esComunaDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const esOffenders = [];
  for (const slug of esComunaDirs) {
    const htmlPath = path.join(esComunaDir, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!content.includes('href="/es/comunas/"')) {
        esOffenders.push(slug);
        if (esOffenders.length >= 5) break;
      }
    }
  }

  if (esOffenders.length === 0) {
    console.log(`PASS [I] breadcrumb: all ES comuna pages contain href="/es/comunas/"`);
  } else {
    console.error(`FAIL [I] breadcrumb: ${esOffenders.length}+ ES comuna pages missing href="/es/comunas/": ${esOffenders.join(', ')}`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// ASSERTION J: map-spoke present on commune ficha pages
// Every EN commune page must contain the substring /map/?cut=
// Every ES commune page must contain the substring /es/mapa/?cut=
// ---------------------------------------------------------------------------
if (existsSync(enCommuneDir)) {
  const enCommuneDirs = readdirSync(enCommuneDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const enMapOffenders = [];
  for (const slug of enCommuneDirs) {
    const htmlPath = path.join(enCommuneDir, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!content.includes('/map/?cut=')) {
        enMapOffenders.push(slug);
        if (enMapOffenders.length >= 5) break;
      }
    }
  }

  if (enMapOffenders.length === 0) {
    console.log(`PASS [J] map-spoke: all EN commune pages contain /map/?cut=`);
  } else {
    console.error(`FAIL [J] map-spoke: ${enMapOffenders.length}+ EN commune pages missing /map/?cut=: ${enMapOffenders.join(', ')}`);
    failures++;
  }
}

if (existsSync(esComunaDir)) {
  const esComunaDirs = readdirSync(esComunaDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const esMapOffenders = [];
  for (const slug of esComunaDirs) {
    const htmlPath = path.join(esComunaDir, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!content.includes('/es/mapa/?cut=')) {
        esMapOffenders.push(slug);
        if (esMapOffenders.length >= 5) break;
      }
    }
  }

  if (esMapOffenders.length === 0) {
    console.log(`PASS [J] map-spoke: all ES comuna pages contain /es/mapa/?cut=`);
  } else {
    console.error(`FAIL [J] map-spoke: ${esMapOffenders.length}+ ES comuna pages missing /es/mapa/?cut=: ${esMapOffenders.join(', ')}`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// ASSERTION K: home single H1
// dist/index.html and dist/es/index.html must each contain exactly one <h1
// ---------------------------------------------------------------------------
const H1_RE = /<h1[\s>]/g;

const homeEnPath = path.join(DIST_DIR, 'index.html');
const homeEsPath = path.join(DIST_DIR, 'es', 'index.html');

if (!existsSync(homeEnPath)) {
  console.error(`FAIL [K] home-h1: dist/index.html not found`);
  failures++;
} else {
  const content = readFileSync(homeEnPath, 'utf-8');
  H1_RE.lastIndex = 0;
  const matches = content.match(H1_RE) ?? [];
  if (matches.length === 1) {
    console.log(`PASS [K] home-h1: dist/index.html has exactly 1 <h1>`);
  } else {
    console.error(`FAIL [K] home-h1: dist/index.html has ${matches.length} <h1> occurrences (expected 1)`);
    failures++;
  }
}

if (!existsSync(homeEsPath)) {
  console.error(`FAIL [K] home-h1: dist/es/index.html not found`);
  failures++;
} else {
  const content = readFileSync(homeEsPath, 'utf-8');
  H1_RE.lastIndex = 0;
  const matches = content.match(H1_RE) ?? [];
  if (matches.length === 1) {
    console.log(`PASS [K] home-h1: dist/es/index.html has exactly 1 <h1>`);
  } else {
    console.error(`FAIL [K] home-h1: dist/es/index.html has ${matches.length} <h1> occurrences (expected 1)`);
    failures++;
  }
}

// ---------------------------------------------------------------------------
// ASSERTION L: rankings nav site-wide
// Sample representative pages must contain href="/rankings/" (EN) or
// href="/es/rankings/" (ES) — verifies the nav link is present.
//
// Sample: home (EN+ES), map page (EN+ES), one commune page (EN+ES)
// ---------------------------------------------------------------------------
const sampleEnPages = [
  path.join(DIST_DIR, 'index.html'),
  path.join(DIST_DIR, 'map', 'index.html'),
];
const sampleEsPages = [
  path.join(DIST_DIR, 'es', 'index.html'),
  path.join(DIST_DIR, 'es', 'mapa', 'index.html'),
];

// Add one commune page to each sample set if available
if (existsSync(enCommuneDir)) {
  const firstSlug = readdirSync(enCommuneDir, { withFileTypes: true })
    .find((d) => d.isDirectory())?.name;
  if (firstSlug) {
    sampleEnPages.push(path.join(enCommuneDir, firstSlug, 'index.html'));
  }
}
if (existsSync(esComunaDir)) {
  const firstSlug = readdirSync(esComunaDir, { withFileTypes: true })
    .find((d) => d.isDirectory())?.name;
  if (firstSlug) {
    sampleEsPages.push(path.join(esComunaDir, firstSlug, 'index.html'));
  }
}

const enNavOffenders = [];
for (const p of sampleEnPages) {
  if (existsSync(p)) {
    const content = readFileSync(p, 'utf-8');
    if (!content.includes('href="/rankings/"')) {
      enNavOffenders.push(path.relative(DIST_DIR, p));
    }
  }
}

if (enNavOffenders.length === 0) {
  console.log(`PASS [L] rankings-nav: all sampled EN pages contain href="/rankings/"`);
} else {
  console.error(`FAIL [L] rankings-nav: missing href="/rankings/" in: ${enNavOffenders.join(', ')}`);
  failures++;
}

const esNavOffenders = [];
for (const p of sampleEsPages) {
  if (existsSync(p)) {
    const content = readFileSync(p, 'utf-8');
    if (!content.includes('href="/es/rankings/"')) {
      esNavOffenders.push(path.relative(DIST_DIR, p));
    }
  }
}

if (esNavOffenders.length === 0) {
  console.log(`PASS [L] rankings-nav: all sampled ES pages contain href="/es/rankings/"`);
} else {
  console.error(`FAIL [L] rankings-nav: missing href="/es/rankings/" in: ${esNavOffenders.join(', ')}`);
  failures++;
}

// ---------------------------------------------------------------------------
// ASSERTION M: comparator cross-link on commune ficha pages (CMP-06)
// Every EN commune page must embed the ComparatorPairsLinks spoke, and every
// ES comuna page likewise. We must NOT match the site-wide PageHeader nav link
// (bare href="/compare/" / href="/es/comparar/"), which is present on EVERY
// page regardless of the spoke — matching it would make this a false-pass
// (WR-03). Instead assert on the spoke's distinctive pair-slug link
// href="/compare/<cutA>-vs-<cutB>/" (a "-vs-" link the nav never emits).
// ---------------------------------------------------------------------------
const enCommuneDir2 = path.join(DIST_DIR, 'commune');
const esComunaDir2 = path.join(DIST_DIR, 'es', 'comuna');

// Distinctive markers only the ComparatorPairsLinks spoke produces.
const EN_SPOKE_RE = /href="\/compare\/\d+-vs-\d+\//;
const ES_SPOKE_RE = /href="\/es\/comparar\/\d+-vs-\d+\//;

if (existsSync(enCommuneDir2)) {
  const enCommuneDirs2 = readdirSync(enCommuneDir2, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const enCmpOffenders = [];
  for (const slug of enCommuneDirs2) {
    const htmlPath = path.join(enCommuneDir2, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!EN_SPOKE_RE.test(content)) {
        enCmpOffenders.push(slug);
        if (enCmpOffenders.length >= 5) break;
      }
    }
  }

  if (enCmpOffenders.length === 0) {
    console.log(`PASS [M] comparator-spoke: all EN commune pages contain a /compare/<a>-vs-<b>/ pair link`);
  } else {
    console.error(
      `FAIL [M] comparator-spoke: ${enCmpOffenders.length}+ EN commune pages missing a /compare/<a>-vs-<b>/ pair link: ${enCmpOffenders.join(', ')}`
    );
    failures++;
  }
}

if (existsSync(esComunaDir2)) {
  const esComunaDirs2 = readdirSync(esComunaDir2, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  const esCmpOffenders = [];
  for (const slug of esComunaDirs2) {
    const htmlPath = path.join(esComunaDir2, slug, 'index.html');
    if (existsSync(htmlPath)) {
      const content = readFileSync(htmlPath, 'utf-8');
      if (!ES_SPOKE_RE.test(content)) {
        esCmpOffenders.push(slug);
        if (esCmpOffenders.length >= 5) break;
      }
    }
  }

  if (esCmpOffenders.length === 0) {
    console.log(`PASS [M] comparator-spoke: all ES comuna pages contain a /es/comparar/<a>-vs-<b>/ pair link`);
  } else {
    console.error(
      `FAIL [M] comparator-spoke: ${esCmpOffenders.length}+ ES comuna pages missing a /es/comparar/<a>-vs-<b>/ pair link: ${esCmpOffenders.join(', ')}`
    );
    failures++;
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nspine.mjs: FAILED (${failures} assertion(s) failed)`);
  process.exit(1);
}

console.log('\nspine.mjs: PASSED');
process.exit(0);
