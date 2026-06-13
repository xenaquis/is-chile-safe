/**
 * forbidden-language.mjs — EDIT-05: scan dist/ HTML for forbidden editorial terms.
 *
 * Strips script/style blocks + HTML tags from each page, normalises accents (NFD),
 * then matches a word-boundary-aware forbidden-term list against visible text.
 * A qualifying-phrase allow-list exempts CEAD-attributed superlatives.
 *
 * Fails non-zero naming the offending page + term on any match outside the allow-list.
 *
 * Usage:
 *   node scripts/validate/forbidden-language.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const DIST_DIR = path.join(SITE_ROOT, 'dist');

// ---------------------------------------------------------------------------
// Guard: dist/ must exist
// ---------------------------------------------------------------------------
if (!existsSync(DIST_DIR)) {
  console.error('FAIL: dist/ directory not found — run npm run build first');
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Forbidden terms (D-06). Terms are accent-stripped at match time so
// accented variants ('la más segura') match the normalised form ('la mas segura').
// Keep only in this JS array — never in an HTML/text context.
// ---------------------------------------------------------------------------
const FORBIDDEN_TERMS = [
  // Spanish
  'zona peligrosa',
  'area peligrosa',
  'comuna peligrosa',
  'barrio peligroso',
  'ranking definitivo',
  'zona segura garantizada',
  'zona segura',
  '100% seguro',
  'seguridad garantizada',
  'la mas segura',
  // English
  'dangerous zone',
  'dangerous area',
  'dangerous commune',
  'dangerous neighborhood',
  'definitive ranking',
  'guaranteed safe',
  '100% safe',
  'guaranteed safety',
  'the safest',
];

// ---------------------------------------------------------------------------
// Allow-list: qualifying phrases that make a superlative acceptable (D-06).
// Checked in a ~100-char context window after the match position.
// ---------------------------------------------------------------------------
const ALLOW_LIST = [
  /en este per[io]+do seg[u]+n datos cead/i,
  /according to cead data for \d{4}/i,
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Accent-strip via Unicode NFD decomposition. Apply to BOTH text and terms
 * so accented characters in HTML match their canonical term entries (Pitfall 2).
 */
function normalizeAccents(str) {
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '');
}

/**
 * Extract visible text from HTML.
 * ORDER MATTERS (Pitfall 3): remove script/style block content FIRST before
 * stripping tags, so JS identifiers cannot produce false positives.
 */
function extractVisibleText(html) {
  let text = html.replace(/<script[\s\S]*?<\/script>/gi, ' ');
  text = text.replace(/<style[\s\S]*?<\/style>/gi, ' ');
  text = text.replace(/<[^>]*>/g, ' ');
  text = text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

/**
 * Build a word-boundary-aware regex for a (already normalised) term.
 * Uses lookbehind/lookahead instead of \b — \b breaks on accented chars (D-08, Pattern 5).
 */
function buildTermPattern(normalizedTerm) {
  const escaped = normalizedTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?<![a-z0-9])${escaped}(?![a-z0-9])`, 'gi');
}

// Pre-build patterns for all terms (normalised lowercase).
const TERM_PATTERNS = FORBIDDEN_TERMS.map((term) => ({
  original: term,
  normalized: normalizeAccents(term.toLowerCase()),
  pattern: buildTermPattern(normalizeAccents(term.toLowerCase())),
}));

// ---------------------------------------------------------------------------
// Recursive index.html collector (verbatim from hreflang.mjs scaffold)
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

// ---------------------------------------------------------------------------
// Scan
// ---------------------------------------------------------------------------
const htmlFiles = findIndexFiles(DIST_DIR);
console.log(`forbidden-language: scanning ${htmlFiles.length} HTML files in dist/`);

let failures = 0;

for (const htmlPath of htmlFiles) {
  const html = readFileSync(htmlPath, 'utf-8');
  const pageLabel = htmlPath.replace(DIST_DIR, '').replace(/\\/g, '/');
  const visible = extractVisibleText(html);
  const normalizedVisible = normalizeAccents(visible.toLowerCase());

  for (const { original, normalized, pattern } of TERM_PATTERNS) {
    // Reset lastIndex between pages (global flag)
    pattern.lastIndex = 0;

    let match;
    while ((match = pattern.exec(normalizedVisible)) !== null) {
      const matchIndex = match.index;

      // Check allow-list in a ~100-char window after the match
      const window = normalizedVisible.slice(matchIndex, matchIndex + match[0].length + 100);
      const allowed = ALLOW_LIST.some((re) => re.test(window));
      if (allowed) continue;

      // Build a readable excerpt (50 chars before + 50 after)
      const excerptStart = Math.max(0, matchIndex - 50);
      const excerptEnd = Math.min(normalizedVisible.length, matchIndex + match[0].length + 50);
      const excerpt = normalizedVisible.slice(excerptStart, excerptEnd).replace(/\n/g, ' ');

      console.error(
        `[forbidden-language] FAIL: ${pageLabel}\n  Term: "${original}"\n  Context: "...${excerpt}..."`
      );
      failures++;
      // Report first match per term per page, then move to next term
      break;
    }

    // Reset for next page iteration
    pattern.lastIndex = 0;
  }
}

// ---------------------------------------------------------------------------
// Result
// ---------------------------------------------------------------------------
if (failures > 0) {
  console.error(`\nforbidden-language: FAILED (${failures} forbidden term(s) found across dist/ pages)`);
  process.exit(1);
}

console.log(`forbidden-language: PASS — ${htmlFiles.length} pages scanned, 0 forbidden terms found`);
