---
phase: 02-astro-site-programmatic-pages
plan: "03"
subsystem: commune-pages
tags: [astro, seo, prose-engine, i18n, commune-pages, rollout-gate, bilingual, json-ld]
dependency_graph:
  requires:
    - "02-01 (data.ts: loadRolloutCuts, loadNationalAverage, loadRegionalAverage, nearestComparable)"
    - "02-02 (all components: LevelChip, TrendChip, StatCard, Sparkline, FamilyBreakdownBars, ComparisonCallout, ComparableCommune, MapPlaceholderSlot, MethodologyCaveat)"
  provides:
    - "site/src/lib/proseEngine.ts — buildCommuneProse(commune, locale) 500+ word bilingual prose"
    - "site/src/pages/commune/[slug].astro — EN commune pages with full UI-SPEC layout"
    - "site/src/pages/es/comuna/[slug].astro — ES commune pages with same rollout gate"
    - "site/scripts/validate/commune.mjs — word count + 5-dimension + forbidden-term assertions"
    - "site/scripts/validate/rollout.mjs — batch count + EN/ES parity assertions"
  affects:
    - "02-04..02-06 — commune URLs referenced in region/crime-type pages; rollout gate canonical"
tech_stack:
  added: []
  patterns:
    - "process.cwd() anchor for data.ts DATA_ROOT and rollout.json — import.meta.url breaks in bundled prerender chunks (dist/.prerender/)"
    - "buildCommuneProse: 8 combinatorial branch dimensions (trend x rankTier x vsNational x vsRegional x family x comparable x timeSeries x lowPop)"
    - "vs-national/regional signed % computed against loadNationalAverage/loadRegionalAverage means, NOT loadNational/loadRegion SUM (Pitfall 1 guard)"
    - "Parallel hand-written EN + ES sentence banks — no translation API or runtime translation"
    - "Prose prose split on double-newline, each paragraph in <p set:html> — not raw dangerouslySetInnerHTML"
key_files:
  created:
    - "site/src/lib/proseEngine.ts"
    - "site/src/pages/commune/[slug].astro"
    - "site/src/pages/es/comuna/[slug].astro"
  modified:
    - "site/scripts/validate/commune.mjs (replaced stub)"
    - "site/scripts/validate/rollout.mjs (replaced stub)"
    - "site/src/lib/data.ts (process.cwd() path fix)"
decisions:
  - "process.cwd() replaces import.meta.url in data.ts DATA_ROOT and rollout.json loader — import.meta.url resolves to dist/.prerender/ during astro build prerender phase, breaking fs.readFileSync. process.cwd() is stable at site/ root during builds."
  - "8-paragraph prose structure (opening, regional context, vs-national, vs-regional, family, comparable, time-series, closing) consistently reaches 500+ words for all non-trivial communes"
  - "Santiago (13101) self-test: rate 9,309.4 vs national mean 5,807.8 = +60.3% above national (Pitfall 1 guard passes)"
metrics:
  duration: "~45min"
  completed: "2026-06-13"
  tasks_completed: 3
  files_created: 3
  files_modified: 3
---

# Phase 02 Plan 03: Commune Pages EN+ES + Prose Engine Summary

Bilingual commune page routes (/commune/{slug}/ and /es/comuna/{slug}/) with a deterministic combinatorial prose variation engine producing 500+ word sober bilingual prose from real Phase-1 CEAD data, gated by the 12-commune rollout batch, with machine-verified word count, forbidden-term, and EN/ES parity assertions.

## Outcome

All 3 tasks complete, all acceptance criteria verified:
- `npx astro check` exits 0 (0 errors, 0 warnings, 0 hints) after all tasks
- `npm run build` produces 12 EN + 12 ES commune pages (24 total) + index = 25 pages
- `node scripts/validate/commune.mjs --self-test` confirms:
  - Santiago (13101) EN prose: 509 words, no forbidden terms, all 5 dimensions present
  - Santiago (13101) ES prose: 632 words, no forbidden terms, all 5 dimensions present
  - vs-national: +60.3% (Santiago ABOVE national mean — Pitfall 1 guard passes, NOT ~-99%)
- `node scripts/validate/commune.mjs` (dist validation): PASSED
- `node scripts/validate/rollout.mjs`: PASSED (12 EN + 12 ES, all slugs reciprocal)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | d124c21 | proseEngine.ts + commune.mjs validator |
| Task 2 | f03735f | EN + ES commune page routes + data.ts process.cwd() fix |
| Task 3 | e23c806 | rollout gate validator |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] import.meta.url breaks in Astro prerender bundles**

- **Found during:** Task 2 — npm run build
- **Issue:** `data.ts` used `import.meta.url` to resolve `DATA_ROOT` (path to `data/cead/`) and `rollout.json`. During Astro build, code is bundled into `dist/.prerender/chunks/*.mjs` — `import.meta.url` then points to the prerender output directory, not the source tree. Result: `ENOENT: no such file or directory, open '...site/data/cead/meta/index.json'` and `...site/dist/.prerender/config/rollout.json'`
- **Fix:** Replaced `import.meta.url` anchor with `process.cwd()` in `data.ts`. During `astro build`, `process.cwd()` is stable at the `site/` directory root. DATA_ROOT becomes `path.resolve(process.cwd(), '..', 'data', 'cead')` and rollout.json is `path.resolve(process.cwd(), 'src', 'config', 'rollout.json')`.
- **Files modified:** `site/src/lib/data.ts`
- **Commit:** f03735f

**2. [Rule 1 - Bug] FamilyBreakdownBars requires `level` prop not initially passed**

- **Found during:** Task 2 — npx astro check after creating route files
- **Issue:** `FamilyBreakdownBars` component has `level: 1|2|3|4|5` as required prop; route templates omitted it
- **Fix:** Added `level={level}` to both EN and ES FamilyBreakdownBars calls (level already computed in page frontmatter)
- **Files modified:** `site/src/pages/commune/[slug].astro`, `site/src/pages/es/comuna/[slug].astro`

**3. [Rule 1 - Bug] EN prose only 418 words on first pass**

- **Found during:** Task 1 — commune.mjs --self-test run
- **Issue:** First prose implementation reached 418 words for Santiago (EN) — 82 words below the 500-word target
- **Fix:** Added a "trends over time" paragraph computing the rate change from the first year in the series to the latest complete year. This paragraph is substantive (names absolute rates, year range, notes partial-year opacity) and reliably adds 80–100 words. Final EN count: 509 words; ES: 632 words.

## Known Stubs

None — all prose is generated from real Phase-1 CEAD data. All 5 canonical dimensions present in every page. Comparable commune always resolves to a real commune with real data.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: content-injection | site/src/pages/commune/[slug].astro | Prose paragraphs use `set:html={para}` — however prose is generated by proseEngine.ts from numeric CEAD data only; no user input flows into prose. Low risk, consistent with Astro's trusted-source `set:html` usage. |

T-02-07 (JSON-LD tampering): `JSON.stringify(jsonLd)` + `is:inline` in BaseLayout — commune values are JSON-escaped, not string-concatenated. Mitigated.
T-02-08 (non-rollout commune disclosure): Non-rollout communes are NOT built (true 404). rollout.mjs verifies only 12 slugs emitted. Mitigated.
T-02-09 (forbidden language drift): commune.mjs --self-test asserts no forbidden term in generated prose. Mitigated.

## Self-Check

- site/src/lib/proseEngine.ts: FOUND
- site/src/pages/commune/[slug].astro: FOUND
- site/src/pages/es/comuna/[slug].astro: FOUND
- site/scripts/validate/commune.mjs: FOUND
- site/scripts/validate/rollout.mjs: FOUND
- Commits d124c21, f03735f, e23c806: FOUND

## Self-Check: PASSED
