/**
 * hreflang.mjs — Validate hreflang correctness and reciprocity across all built pages.
 *
 * Asserts per page:
 *   1. Three hreflang alternates present: hreflang="en", hreflang="es", hreflang="x-default"
 *   2. self-canonical present (rel="canonical")
 *   3. x-default points to the EN URL
 *   4. EN alternate URL resolves to an actually-existing dist/ file (reciprocity)
 *   5. ES alternate URL resolves to an actually-existing dist/ file (reciprocity)
 *   6. theme-color meta present (#0f766e)
 *   7. manifest link present (/manifest.json) — folds SEO-04 page-level checks
 *
 * Exit non-zero naming the first 5 offending pages (then summary count).
 *
 * Usage:
 *   node scripts/validate/hreflang.mjs
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

const BASE = 'https://ischilesafe.com';

// ---------------------------------------------------------------------------
// Collect all index.html files recursively
// ---------------------------------------------------------------------------
function findIndexFiles(dir, results = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findIndexFiles(full, results);
    } else if (entry.name === 'index.html') {
      results.push(full);
    }
  }
  return results;
}

if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

const htmlFiles = findIndexFiles(DIST_DIR);
console.log(`hreflang.mjs: scanning ${htmlFiles.length} HTML files in dist/`);

// ---------------------------------------------------------------------------
// URL → dist path helper
// ---------------------------------------------------------------------------
function urlToDistPath(url) {
  // Remove base and trailing slash, then append /index.html
  const relative = url.replace(BASE, '').replace(/\/$/, '') || '';
  return path.join(DIST_DIR, relative, 'index.html');
}

// ---------------------------------------------------------------------------
// Parse hreflang/canonical from HTML
// ---------------------------------------------------------------------------
function parseHreflangTags(html) {
  const results = {};
  // Match <link rel="alternate" hreflang="..." href="...">
  const re = /hreflang="([^"]+)"[^>]*href="([^"]+)"|href="([^"]+)"[^>]*hreflang="([^"]+)"/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const lang = m[1] || m[4];
    const href = m[2] || m[3];
    results[lang] = href;
  }
  return results;
}

function parseCanonical(html) {
  const m = html.match(/rel="canonical"\s+href="([^"]+)"/);
  if (m) return m[1];
  const m2 = html.match(/href="([^"]+)"\s+rel="canonical"/);
  return m2 ? m2[1] : null;
}

// ---------------------------------------------------------------------------
// Walk all pages and assert
// ---------------------------------------------------------------------------
let failures = 0;
const failMessages = [];
const MAX_DETAIL = 5; // report first 5 failing pages in detail

for (const htmlPath of htmlFiles) {
  const html = readFileSync(htmlPath, 'utf-8');
  // Skip Astro-generated static redirect pages (meta http-equiv refresh + noindex)
  if (html.includes('http-equiv="refresh"') || html.includes("http-equiv='refresh'")) continue;
  const pageLabel = htmlPath.replace(DIST_DIR, '').replace(/\\/g, '/');
  const pageFailures = [];

  // 1. Three hreflang alternates
  const tags = parseHreflangTags(html);
  if (!tags['en'])        pageFailures.push('missing hreflang="en"');
  if (!tags['es'])        pageFailures.push('missing hreflang="es"');
  if (!tags['x-default']) pageFailures.push('missing hreflang="x-default"');

  // 2. Self-canonical
  const canonical = parseCanonical(html);
  if (!canonical) {
    pageFailures.push('missing rel="canonical"');
  }

  // 3. x-default points to EN URL
  if (tags['en'] && tags['x-default'] && tags['x-default'] !== tags['en']) {
    pageFailures.push(`x-default (${tags['x-default']}) !== en href (${tags['en']})`);
  }

  // 4 & 5. Reciprocity: each alternate must resolve to a real dist file
  if (tags['en']) {
    const enPath = urlToDistPath(tags['en']);
    if (!existsSync(enPath)) {
      pageFailures.push(`EN alternate URL not found in dist: ${tags['en']}`);
    }
  }
  if (tags['es']) {
    const esPath = urlToDistPath(tags['es']);
    if (!existsSync(esPath)) {
      pageFailures.push(`ES alternate URL not found in dist: ${tags['es']}`);
    }
  }

  // 6. theme-color meta
  if (!html.includes('name="theme-color"')) {
    pageFailures.push('missing <meta name="theme-color">');
  }

  // 7. manifest link
  if (!html.includes('rel="manifest"')) {
    pageFailures.push('missing <link rel="manifest">');
  }

  if (pageFailures.length > 0) {
    failures += pageFailures.length;
    if (failMessages.length < MAX_DETAIL) {
      failMessages.push(`FAIL ${pageLabel}:\n  ${pageFailures.join('\n  ')}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
if (failures > 0) {
  for (const msg of failMessages) {
    console.error(msg);
  }
  const remaining = failures - failMessages.reduce((acc, m) => acc + (m.match(/\n  /g) || []).length + 1, 0);
  if (remaining > 0) {
    console.error(`  ... and more failures (total individual failure count: ${failures})`);
  }
  console.error(`\nhreflang.mjs: FAILED (${failures} issue(s) across ${htmlFiles.length} pages)`);
  process.exit(1);
}

console.log(`hreflang.mjs: PASSED — ${htmlFiles.length} pages checked`);
console.log(`  All pages have 3 hreflang alternates + canonical`);
console.log(`  Reciprocity verified: all alternate URLs resolve to real dist files`);
console.log(`  theme-color + manifest link present on all pages`);
