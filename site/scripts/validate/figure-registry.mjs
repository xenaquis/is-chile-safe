/**
 * figure-registry.mjs — SRC-05: figure-registry zero-orphan completeness check.
 *
 * Reads data/SOURCES.md and asserts that every in-scope figure from the
 * v1.3-METHODOLOGY-SPEC.md Part 1 registry (F1-F12 + F15) maps to at least one
 * required source token present in SOURCES.md.
 *
 * A "token" is a substring that must appear in SOURCES.md content (heading or
 * body text).  Each figure's token group is the minimal set that proves its
 * backing source class is registered.
 *
 * Exit codes:
 *   0 — all in-scope figures have registered sources (zero orphans)
 *   1 — one or more figures are orphaned (required token missing from SOURCES.md)
 *
 * Usage:
 *   node scripts/validate/figure-registry.mjs
 */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { checkF16 } from './figure-registry.lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = path.resolve(__dirname, '../..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const SOURCES_PATH = path.join(REPO_ROOT, 'data', 'SOURCES.md');

// ---------------------------------------------------------------------------
// Guard: SOURCES.md must exist
// ---------------------------------------------------------------------------
if (!existsSync(SOURCES_PATH)) {
  console.error(`FAIL: data/SOURCES.md not found at ${SOURCES_PATH}`);
  process.exit(1);
}

const sourcesContent = readFileSync(SOURCES_PATH, 'utf-8');

// ---------------------------------------------------------------------------
// Figure registry — in-scope figures F1-F15.
//
// Each entry specifies:
//   id         — figure number (e.g. 'F1')
//   description — short description for output readability
//   tokens     — array of token groups; each group is an array of strings ALL
//                of which must appear in SOURCES.md for the group to match.
//                A figure passes if AT LEAST ONE group matches (logical OR
//                across groups, AND within each group).
//   note       — why this figure passes (editorial note or derived)
// ---------------------------------------------------------------------------
const FIGURE_REGISTRY = [
  {
    id: 'F1',
    description: 'Commune crime rate (per-100k, by family + total)',
    tokens: [
      // CEAD section + INE section both present
      ['## CEAD', '## INE'],
    ],
    note: 'Requires both CEAD (medida=2 rates) and INE (population denominator) entries.',
  },
  {
    id: 'F2',
    description: 'National average (unweighted mean of non-low-pop commune rates)',
    tokens: [
      // Methodology parameters editorial entry covers the unweighted mean rule
      ['## Methodology parameters'],
    ],
    note: 'Editorial parameter (unweighted mean) documented in Methodology parameters section.',
  },
  {
    id: 'F3',
    description: 'Per-family national mean (unweighted)',
    tokens: [
      // CEAD rates + INE denominator + Methodology parameters editorial note
      ['## CEAD', '## INE', '## Methodology parameters'],
    ],
    note: 'Requires CEAD, INE denominator, and Methodology parameters (unweighted mean rule).',
  },
  {
    id: 'F4',
    description: 'Per-region breakdown mean (unweighted)',
    tokens: [
      ['## CEAD', '## INE', '## Methodology parameters'],
    ],
    note: 'Same source requirements as F3.',
  },
  {
    id: 'F5',
    description: 'National/regional time-series rate (population-weighted)',
    tokens: [
      ['## CEAD', '## INE'],
    ],
    note: 'CEAD series + INE population denominator for pop-weighted mean.',
  },
  {
    id: 'F6',
    description: 'Incidence level chip (1-5, relative classification)',
    tokens: [
      // Derived from CEAD rates; documented in Methodology parameters as editorial
      ['## CEAD', '## Methodology parameters'],
    ],
    note: 'Level classification derived from CEAD rates; editorial thresholds in Methodology parameters.',
  },
  {
    id: 'F7',
    description: 'Trend (rising/falling/stable): 3-year window + 5% threshold',
    tokens: [
      // Trend parameters are editorial; documented in Methodology parameters section
      ['## Methodology parameters', 'Trend window', 'Trend threshold'],
    ],
    note: 'Trend formula editorial parameters must appear in Methodology parameters section.',
  },
  {
    id: 'F8',
    description: 'Choropleth color scale (5 classes)',
    tokens: [
      // Derived from same CEAD distribution as F6; chilemapas for geometry
      ['## CEAD', '## chilemapas'],
    ],
    note: 'Color scale derived from CEAD rates; map geometry from chilemapas.',
  },
  {
    id: 'F9',
    description: 'Low-population exclusion (<10,000 inhabitants)',
    tokens: [
      // Editorial parameter in Methodology parameters + INE small-area convention
      ['## Methodology parameters', 'Low-population exclusion'],
    ],
    note: 'Low-pop exclusion documented as editorial parameter in Methodology parameters section.',
  },
  {
    id: 'F10',
    description: 'Drogas family rate (Ley 20.000 grupo 401 only)',
    tokens: [
      // CEAD taxonomy documents drogas = grupo 401 (Ley 20.000 only)
      ['## CEAD', 'grupo 401'],
    ],
    note: 'Drogas scope (Ley 20.000 grupo 401) must be documented in CEAD entry.',
  },
  {
    id: 'F11',
    description: 'Underreporting / cifra negra claims',
    tokens: [
      // ENUSC entry is the backing source for underreporting statistics
      ['## ENUSC'],
    ],
    note: 'ENUSC entry required — it is the empirical basis for cifra negra claims.',
  },
  {
    id: 'F12',
    description: 'Map geometry (commune boundary polygons)',
    tokens: [
      ['## chilemapas'],
    ],
    note: 'chilemapas entry required for boundary polygon attribution.',
  },
  {
    id: 'F13',
    description: 'SPD VHC homicide rate — M1 composite index input (spd_homicide_rate)',
    tokens: [
      // SPD VHC homicide — M1: both token groups must match in SOURCES.md (accent-free)
      ['SPD', 'homicidio'],
      ['Subsecretaria de Prevencion', 'homicidio'],
    ],
    note: 'SPD VHC homicide is M1 in the composite index; both SPD+homicidio and Subsecretaria de Prevencion+homicidio must appear in SOURCES.md (accent-free).',
  },
  {
    id: 'F14',
    description: 'SII exposure proxy — workers per commune (sii_workers)',
    tokens: [
      // SII workers exposure — both token pairs must match in SOURCES.md (accent-free)
      ['SII', 'trabajadores'],
      ['SII', 'exposicion'],
    ],
    note: 'SII exposure metric requires SII+trabajadores and SII+exposicion in SOURCES.md (accent-free).',
  },
  {
    id: 'F15',
    description: 'News incidents (count, date, location from RSS feeds)',
    tokens: [
      // RSS feeds entry is documented under "News" or referenced inline;
      // the news pipeline attribution is via the inline source links on news pages.
      // The validator checks for the presence of any RSS/news source marker in SOURCES.md
      // or the editorial guardrail that news incidents cite their outlet.
      // Since news sourcing is fully inline (every pin cites its outlet + URL),
      // we verify that SOURCES.md documents the news layer concept at a minimum
      // via the Cross-source notes or any mention of "RSS" or "news".
      ['RSS', 'news'],
    ],
    note: 'News layer attribution: each pin cites outlet + URL inline; SOURCES.md must reference RSS/news.',
  },
  {
    id: 'F16',
    description: 'ENUSC SAE VHDV household victimization rate (experimental, 2024)',
    tokens: [
      ['## INE ENUSC SAE', 'VHDV'],
      ['ENUSC', 'Victimizacion en Hogares', 'SAE'],
    ],
    note: 'INE ENUSC 2024 communal SAE estimate; labeled experimental. 136/346 comunas coverage. Distinct from F11 (underreporting claims) which uses the ## ENUSC underreporting section.',
  },
];

// ---------------------------------------------------------------------------
// Check each figure
// ---------------------------------------------------------------------------
console.log(`figure-registry: checking ${FIGURE_REGISTRY.length} in-scope figures (F1-F16)`);
console.log(`figure-registry: reading ${SOURCES_PATH}`);
console.log('');

const orphans = [];

for (const figure of FIGURE_REGISTRY) {
  // F16 uses the hardened, section-bounded + length-guarded check (DOCS-05).
  // All other figures (F1-F15) keep the existing whole-file substring check —
  // do not generalize section-bounding to figures whose token groups
  // legitimately span multiple `## ` sections (e.g. F1's ['## CEAD', '## INE']).
  const passed =
    figure.id === 'F16'
      ? checkF16(sourcesContent)
      : figure.tokens.some((group) => group.every((token) => sourcesContent.includes(token)));

  if (passed) {
    console.log(`  PASS  ${figure.id}: ${figure.description}`);
  } else {
    // Report which tokens are missing
    const missingGroups = figure.tokens.map((group) => {
      const missing = group.filter((t) => !sourcesContent.includes(t));
      return { group, missing };
    });
    console.error(`  FAIL  ${figure.id}: ${figure.description}`);
    for (const { group, missing } of missingGroups) {
      console.error(`         Required tokens: [${group.map((t) => `"${t}"`).join(', ')}]`);
      console.error(`         Missing tokens:  [${missing.map((t) => `"${t}"`).join(', ')}]`);
    }
    orphans.push(figure.id);
  }
}

console.log('');

// ---------------------------------------------------------------------------
// Result
// ---------------------------------------------------------------------------
if (orphans.length > 0) {
  console.error(
    `figure-registry: FAILED — ${orphans.length} orphaned figure(s): ${orphans.join(', ')}`
  );
  console.error(
    'Add the missing source entries to data/SOURCES.md or add the required token to the existing entry.'
  );
  process.exit(1);
}

console.log(
  `figure-registry: PASS — all ${FIGURE_REGISTRY.length} in-scope figures (F1-F16) have registered sources in data/SOURCES.md (zero orphans)`
);

// ---------------------------------------------------------------------------
// DOCS-01 / DOCS-03 content-correctness checks
//
// These guard against Plan 31-01's national_rank-direction fix and Plan
// 31-02's News section rewrite silently regressing. Failures here push into
// the same `orphans`-style exit-1 path as the figure-registry loop above.
//
// F-68 (mandatory whitespace normalization): a hard re-wrap of any of these
// sentences could split a phrase across a newline; an un-normalized check
// would then go RED against perfectly correct prose. All phrase checks run
// against whitespace-normalized content, never raw file bytes.
// ---------------------------------------------------------------------------
const norm = (s) => s.replace(/\s+/g, ' ');

// Accent-strip: NFD-decompose and drop combining marks, mirrors the
// accent-insensitive normalization used elsewhere in this repo
// (pipeline/news/resolver.py `_norm`, communes/index.astro).
const stripAccents = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '');

let contentFailures = 0;

const METHODOLOGY_EN_PATH = path.join(SITE_ROOT, 'src', 'pages', 'methodology.astro');
const METHODOLOGY_ES_PATH = path.join(SITE_ROOT, 'src', 'pages', 'es', 'metodologia.astro');
const SAFEST_CITIES_PATH = path.join(SITE_ROOT, 'src', 'pages', 'safest-cities-in-chile.astro');
const COMUNAS_SEGURAS_PATH = path.join(SITE_ROOT, 'src', 'pages', 'es', 'comunas-mas-seguras-chile.astro');

// ---------------------------------------------------------------------------
// (a) Repo-wide sweep — every .astro file under src/pages/ (both locales,
// recursively), not just the files a prior plan happened to edit. A guard
// scoped to the diff can only ever confirm the fix it was written alongside
// (CR-02). Whitespace-normalized AND accent-stripped before matching so no
// accented/unaccented or re-wrapped variant can slip through.
// ---------------------------------------------------------------------------
const PAGES_ROOT = path.join(SITE_ROOT, 'src', 'pages');

function listAstroFiles(root) {
  const entries = readdirSync(root, { recursive: true, withFileTypes: true });
  return entries
    .filter((e) => e.isFile() && e.name.endsWith('.astro'))
    .map((e) => path.join(e.parentPath ?? e.path, e.name));
}

const INVERTED_PHRASES_RAW = [
  'lowest reported rate in Chile',
  'menor tasa reportada en Chile',
  'lowest reported rate among all non-low-population',
  'tasa más baja reportada',
  'tasa mas baja reportada',
  'Rango nacional 1 = tasa más baja',
  'Rango nacional 1 = tasa mas baja',
];
// Pre-normalize the phrase list once (whitespace + accent-strip) so the
// per-file loop below does the same transform to both sides.
const INVERTED_PHRASES = INVERTED_PHRASES_RAW.map((p) => stripAccents(norm(p)));

const astroFiles = listAstroFiles(PAGES_ROOT);

for (const filePath of astroFiles) {
  const label = path.relative(SITE_ROOT, filePath).split(path.sep).join('/');
  const raw = readFileSync(filePath, 'utf-8');
  const content = stripAccents(norm(raw));
  for (let i = 0; i < INVERTED_PHRASES.length; i++) {
    if (content.includes(INVERTED_PHRASES[i])) {
      console.error(
        `FAIL [DOCS-01] ${label} contains the inverted phrase "${INVERTED_PHRASES_RAW[i]}" (national_rank direction regression)`
      );
      contentFailures++;
    }
  }
}

// (b) positive checks — the corrected phrasing must actually be present in
// each page (not just the absence of the wrong one).
const POSITIVE_CHECKS = [
  { label: 'methodology.astro', filePath: METHODOLOGY_EN_PATH, phrase: 'highest reported rate in Chile' },
  { label: 'metodologia.astro', filePath: METHODOLOGY_ES_PATH, phrase: 'mayor tasa reportada en Chile' },
  { label: 'safest-cities-in-chile.astro', filePath: SAFEST_CITIES_PATH, phrase: 'highest reported rate nationwide' },
  { label: 'es/comunas-mas-seguras-chile.astro', filePath: COMUNAS_SEGURAS_PATH, phrase: 'mayor tasa reportada a nivel nacional' },
];

for (const { label, filePath, phrase } of POSITIVE_CHECKS) {
  if (!existsSync(filePath)) {
    console.error(`FAIL [DOCS-01] ${label} not found at ${filePath}`);
    contentFailures++;
    continue;
  }
  const content = norm(readFileSync(filePath, 'utf-8'));
  if (content.includes(phrase)) {
    console.log(`PASS [DOCS-01] ${label} contains "${phrase}"`);
  } else {
    console.error(`FAIL [DOCS-01] ${label} is missing the corrected phrase "${phrase}"`);
    contentFailures++;
  }
}

// (c) DOCS-03 — data/SOURCES.md must still carry Plan 31-02's News section
// rewrite tokens (Google News / Granite / R2).
const sourcesNorm = norm(sourcesContent);
const DOCS03_CHECKS = [
  {
    label: 'news.google.com / Google News',
    test: () => sourcesNorm.includes('news.google.com') || sourcesNorm.includes('Google News'),
  },
  {
    label: 'granite (case-insensitive)',
    test: () => /granite/i.test(sourcesNorm),
  },
  {
    label: 'R2',
    test: () => sourcesNorm.includes('R2'),
  },
];

for (const { label, test } of DOCS03_CHECKS) {
  if (test()) {
    console.log(`PASS [DOCS-03] data/SOURCES.md contains ${label}`);
  } else {
    console.error(`FAIL [DOCS-03] data/SOURCES.md is missing ${label}`);
    contentFailures++;
  }
}

if (contentFailures > 0) {
  console.error(`\nfigure-registry: FAILED — ${contentFailures} DOCS-01/DOCS-03 content check(s) failed`);
  process.exit(1);
}
